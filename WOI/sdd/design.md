# Design — Relatório de Custos Municipais 2025 (Saúde e Educação)

## 1. Arquitetura Geral

```
┌──────────────────────────────────────────────────────────┐
│                       run_all.sh                         │
│      Orquestra execução sequencial dos scripts           │
└──────────────┬───────────────────────────────────────────┘
               │
    ┌──────────▼──────────┐
    │   extract_data.py   │  Etapa 1 — Extração
    │                     │
    │  • Descompacta ZIPs │
    │  • Lê CSVs (latin-1)│
    │  • Filtra por unid. │
    │  • Salva Parquets   │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────────┐
    │  classify_empenhos.py   │  Etapa 2 — Classificação
    │                         │
    │  • Regras dsc_natureza  │
    │  • Regras dsc_acao      │
    │  • API Claude (ambíguos)│
    │  • Cache incremental    │
    └──────────┬──────────────┘
               │
    ┌──────────▼──────────────┐
    │   generate_tables.py    │  Etapa 3 — Tabelas
    │                         │
    │  • Composição programas │
    │  • Ranking fornecedores │
    │  • Série mensal         │
    │  • Fontes de recurso    │
    │  • KPIs JSON            │
    └──────────┬──────────────┘
               │
    ┌──────────▼──────────────┐
    │  build_html_saude.py    │  Etapa 4 — HTMLs
    │  build_html_educacao.py │
    │                         │
    │  • Lê tabelas/          │
    │  • Gera action titles   │
    │  • Monta HTML + Charts  │
    │  • Embute dados JSON    │
    └─────────────────────────┘
```

---

## 2. Modelo de Dados

### 2.1 Tabelas e seus papéis

```
despesa.despesa      → visão ORÇAMENTÁRIA por dotação (sem seq_empenho)
empenho.empenho      → detalhe de CADA COMPROMISSO (tem seq_empenho + dsc_empenho)
despesa.pagamento    → PAGAMENTOS EFETIVOS (tem seq_empenho + nom_credor + vlr_pag_fonte)
empenho.credorEmpenho → CNPJ/CPF do credor por empenho (complementar)
```

### 2.2 Fluxos de join

```python
# FLUXO 1 — Composição orçamentária (zero join)
# despesa.despesa já está no nível certo de agregação
df_despesa = despesa_df.groupby(['dsc_programa', 'dsc_acao', 'dsc_naturezadespesa',
                                  'dsc_fonterecurso', 'num_mesexercicio'])['vlr_pago'].sum()

# FLUXO 2 — Classificação (zero join)
# empenho.empenho usado diretamente
df_empenho_class = empenho_df[['seq_empenho', 'dsc_empenho',
                                 'dsc_naturezadespesa', 'dsc_acao',
                                 'vlr_empenhado', 'num_mesexercicio']]

# FLUXO 3 — Fornecedores (join opcional para CNPJ)
df_fornecedores = pagamento_df.groupby('nom_credor').agg(
    total_pago=('vlr_pag_fonte', 'sum'),
    qtd_pagamentos=('seq_pagamento', 'count'),
    qtd_empenhos=('seq_empenho', 'nunique')
).sort_values('total_pago', ascending=False)

# Para enriquecer com CNPJ quando nom_credor vem vazio:
df_credor = credorEmpenho_df[['seq_empenho', 'num_doc_credor', 'nom_credor']]
df_pagamento_enrich = pagamento_df.merge(df_credor, on='seq_empenho', how='left',
                                          suffixes=('_pag', '_emp'))
df_pagamento_enrich['nom_credor_final'] = (
    df_pagamento_enrich['nom_credor_pag']
    .where(df_pagamento_enrich['nom_credor_pag'].notna(), df_pagamento_enrich['nom_credor_emp'])
)
```

### 2.3 Normalização de valores monetários

CSVs do SICOM usam formato BR: `"1.234.567,89"` → `1234567.89`

```python
def parse_valor_br(s):
    """Converte string formato BR para float. Retorna 0.0 para nulos/vazios."""
    if pd.isna(s):
        return 0.0
    s = str(s).strip()
    if s in ('', '-', '0'):
        return 0.0
    try:
        return float(s.replace('.', '').replace(',', '.'))
    except ValueError:
        return 0.0

# Aplicar em todos os campos vlr_*
vlr_cols = [c for c in df.columns if c.startswith('vlr_')]
for col in vlr_cols:
    df[col] = df[col].apply(parse_valor_br)
```

### 2.4 Armazenamento intermediário

```
../output/tabelas/
├── classificacao_cache.csv          ← cache global de classificações
├── classificacao_erros.log          ← empenhos não classificados pela API
├── saude/
│   ├── despesa_2025.parquet
│   ├── empenho_2025.parquet
│   ├── empenho_classificado.parquet
│   ├── pagamento_2025.parquet
│   ├── composicao_programa.csv
│   ├── composicao_natureza.csv
│   ├── composicao_acao.csv
│   ├── ranking_fornecedores.csv
│   ├── pareto.csv
│   ├── composicao_categorias.csv
│   ├── composicao_categorias_mensal.csv
│   ├── serie_mensal.csv
│   ├── fontes_recurso.csv
│   └── kpis.json
└── educacao/
    └── (mesma estrutura)
```

---

## 3. Classificação de Empenhos (classify_empenhos.py)

### 3.1 Camada 1 — Regras determinísticas

```python
# Prioridade: dsc_naturezadespesa > dsc_acao
# Match por prefixo do código de natureza (começando pelos mais específicos)

REGRAS_NATUREZA = {
    # Pessoal
    '3.1.90.11': 'Pessoal',           # Vencimentos e salários
    '3.1.90.04': 'Pessoal',           # Contratos temporários
    '3.1.90.13': 'Pessoal',           # Contribuição INSS patronal
    '3.1.90.16': 'Pessoal',           # Outras despesas pessoal civil
    '3.1.91.13': 'Pessoal',           # RPPS – contribuição patronal
    '3.1.90.01': 'Pessoal',           # Aposentadorias RPPS
    '3.1.90.03': 'Pessoal',           # Pensões RPPS
    '3.1.90.94': 'Previdência',       # Indenizações inativos
    # Materiais
    '3.3.90.30.09': 'Medicamentos',
    '3.3.90.30.35': 'Material hospitalar',
    '3.3.90.30.07': 'Alimentação',
    '3.3.90.30.22': 'Limpeza',
    '3.3.90.30.16': 'Material expediente/pedagógico',
    '3.3.90.30.25': 'Manutenção',     # Material manutenção bens móveis
    '3.3.90.30.37': 'Manutenção',     # Material manutenção veículos
    '3.3.90.30.17': 'Material hospitalar',  # Material farmacológico
    # Serviços
    '3.3.90.36': 'Serviços terceirizados',  # Pessoa física
    '3.3.90.39': 'Serviços terceirizados',  # Pessoa jurídica
    '3.3.90.37': 'Transporte',         # Locação de meios de transporte
    '3.3.90.40': 'TI',                 # Serviços de TI
    # Investimentos
    '4.4.90.51': 'Investimentos',      # Obras e instalações
    '4.4.90.52': 'Investimentos',      # Equipamentos e material permanente
    # Transferências
    '3.3.50':    'Transferências',     # Instituições privadas
    '3.3.90.48': 'Transferências',     # Auxílios financeiros PF
    '3.2.90.49': 'Transferências',     # Auxílios PJ
}

REGRAS_ACAO = {
    '2551': 'Pessoal',                 # Remuneração servidores ativos
    '2550': 'Pessoal',                 # Remuneração agentes políticos
    '2552': 'Previdência',             # Proventos inativos/pensionistas
    '2718': 'Previdência',             # Pensões e proventos aposentadoria
    '2653': 'Transporte',              # Transporte escolar
    '2647': 'Alimentação',             # Segurança alimentar e nutricional
    '2607': 'Medicamentos',            # Assistência farmacêutica
    '2637': 'TI',                      # Gestão TI e rede integrada
}

def classificar_por_regras(row):
    natureza = str(row.get('dsc_naturezadespesa', '') or '').strip()
    acao = str(row.get('dsc_acao', '') or '').strip()[:4]  # primeiros 4 dígitos

    # Natureza tem prioridade (match por prefixo, do mais específico ao menos)
    for prefixo in sorted(REGRAS_NATUREZA, key=len, reverse=True):
        if natureza.startswith(prefixo):
            return REGRAS_NATUREZA[prefixo]

    # Fallback: ação
    if acao in REGRAS_ACAO:
        return REGRAS_ACAO[acao]

    return None  # ambíguo → vai para API
```

### 3.2 Camada 2 — API Claude (ambíguos)

```python
import anthropic, os, json, time

client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

PROMPT_TEMPLATE = """Você é um classificador de empenhos públicos municipais brasileiros.

Classifique cada empenho abaixo em UMA das categorias:
1. Pessoal  2. Medicamentos  3. Material hospitalar  4. Alimentação
5. Limpeza  6. Manutenção  7. Transporte  8. TI  9. Serviços terceirizados
10. Material expediente/pedagógico  11. Investimentos  12. Previdência
13. Transferências  14. Outros

Use dsc_empenho, dsc_naturezadespesa e dsc_acao como contexto.
Responda APENAS com JSON: [{{"seq_empenho": "X", "categoria": N}}, ...]

Empenhos:
{batch_json}"""

def classificar_lote_api(batch_df, max_retries=3):
    items = batch_df[['seq_empenho', 'dsc_empenho',
                       'dsc_naturezadespesa', 'dsc_acao']].to_dict('records')
    prompt = PROMPT_TEMPLATE.format(batch_json=json.dumps(items, ensure_ascii=False))

    for tentativa in range(max_retries):
        try:
            resp = client.messages.create(
                model='claude-sonnet-4-20250514',
                max_tokens=4096,
                temperature=0,
                messages=[{'role': 'user', 'content': prompt}]
            )
            return json.loads(resp.content[0].text)
        except Exception as e:
            if tentativa == max_retries - 1:
                # Após 3 tentativas, retornar "Outros" para todos
                return [{'seq_empenho': str(r['seq_empenho']), 'categoria': 14}
                        for r in items]
            time.sleep(2 ** tentativa)  # backoff exponencial

def classificar_com_cache(empenhos_df, cache_path):
    if os.path.exists(cache_path):
        cache = pd.read_csv(cache_path, dtype={'seq_empenho': str})
        ja_feitos = set(cache['seq_empenho'].astype(str))
    else:
        cache = pd.DataFrame(columns=['seq_empenho', 'categoria', 'origem'])
        ja_feitos = set()

    pendentes = empenhos_df[~empenhos_df['seq_empenho'].astype(str).isin(ja_feitos)]

    if len(pendentes) == 0:
        return cache

    novos = []
    for i in range(0, len(pendentes), 50):
        batch = pendentes.iloc[i:i+50]
        resultado = classificar_lote_api(batch)
        for r in resultado:
            novos.append({'seq_empenho': str(r['seq_empenho']),
                          'categoria': r['categoria'], 'origem': 'api'})

    cache = pd.concat([cache, pd.DataFrame(novos)], ignore_index=True)
    cache.to_csv(cache_path, index=False)
    return cache
```

---

## 4. Tabelas Analíticas (generate_tables.py)

### 4.1 Composição por programa

```python
def composicao_programa(despesa_df):
    t = despesa_df.groupby('dsc_programa').agg(
        vlr_pago=('vlr_pago', 'sum'),
        vlr_empenhado=('vlr_empenhado', 'sum'),
        vlr_previsto=('vlr_previsto', 'sum')
    ).reset_index().sort_values('vlr_pago', ascending=False)
    t['pct_total'] = t['vlr_pago'] / t['vlr_pago'].sum() * 100
    return t
```

### 4.2 Composição por natureza (agrupada)

```python
# Agrupar naturezas no 2º nível do código (ex: "3.1.90" → "Pessoal")
MACRO_NATUREZA = {
    '3.1': 'Pessoal e Encargos',
    '3.3.90.30': 'Materiais de Consumo',
    '3.3.90.36': 'Serviços PF',
    '3.3.90.37': 'Locações',
    '3.3.90.39': 'Serviços PJ',
    '3.3.90.40': 'TI e Serv. Tecnológicos',
    '3.3.90.48': 'Auxílios e Transferências',
    '3.3.50':    'Transf. Instituições Privadas',
    '4.4.90':    'Investimentos',
}

def categorizar_natureza(nat_code):
    nat = str(nat_code).strip()
    for prefixo in sorted(MACRO_NATUREZA, key=len, reverse=True):
        if nat.startswith(prefixo):
            return MACRO_NATUREZA[prefixo]
    return 'Outros'
```

### 4.3 Ranking de fornecedores + Pareto

```python
def ranking_fornecedores(pagamento_df, top_n=20):
    r = pagamento_df.groupby('nom_credor').agg(
        total_pago=('vlr_pag_fonte', 'sum'),
        qtd_pagamentos=('seq_pagamento', 'count'),
        qtd_empenhos=('seq_empenho', 'nunique')
    ).sort_values('total_pago', ascending=False).reset_index()

    total_geral = r['total_pago'].sum()
    r['pct_total']    = r['total_pago'] / total_geral * 100
    r['pct_acumulado'] = r['pct_total'].cumsum()
    return r.head(top_n)
```

### 4.4 Série temporal mensal

```python
def serie_mensal(despesa_df):
    MESES = {1:'Jan',2:'Fev',3:'Mar',4:'Abr',5:'Mai',6:'Jun',
             7:'Jul',8:'Ago',9:'Set',10:'Out',11:'Nov',12:'Dez'}
    s = despesa_df.groupby('num_mesexercicio')['vlr_pago'].sum().reset_index()
    s.columns = ['mes', 'vlr_pago']
    s['mes_nome'] = s['mes'].map(MESES)
    s['media']    = s['vlr_pago'].mean()
    return s.sort_values('mes')
```

### 4.5 KPIs JSON

```python
def gerar_kpis(despesa_df, pagamento_df, empenho_df, secretaria):
    mes_max = int(despesa_df['num_mesexercicio'].max())
    serie   = serie_mensal(despesa_df)

    return {
        'secretaria':        secretaria,
        'total_pago':        float(despesa_df['vlr_pago'].sum()),
        'total_empenhado':   float(despesa_df['vlr_empenhado'].sum()),
        'total_previsto':    float(despesa_df['vlr_previsto'].sum()),
        'num_fornecedores':  int(pagamento_df['nom_credor'].nunique()),
        'num_empenhos':      int(empenho_df['seq_empenho'].nunique()),
        'meses_cobertos':    mes_max,
        'periodo':           f'Jan–{["","Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"][mes_max]} 2025',
        'mes_pico':          int(serie.loc[serie['vlr_pago'].idxmax(), 'mes']),
        'valor_pico':        float(serie['vlr_pago'].max()),
        'media_mensal':      float(serie['vlr_pago'].mean()),
        'programa_top':      str(despesa_df.groupby('dsc_programa')['vlr_pago'].sum().idxmax()),
    }
```

---

## 5. HTML McKinsey (build_html_*.py)

### 5.1 Geração de Action Titles via API Claude

```python
def gerar_action_title(secao, dados_resumo, secretaria):
    prompt = f"""Você é um consultor McKinsey escrevendo um relatório de custos
para o secretário de {secretaria} de Sete Lagoas (MG).

Seção: {secao}
Dados resumidos: {json.dumps(dados_resumo, ensure_ascii=False)}

Escreva UM action title em português (máximo 18 palavras) seguindo estas regras:
- AFIRMAÇÃO, não rótulo (evite "análise de", "composição de")
- Contém pelo menos UM número ou percentual específico
- Comunica o "so what" — a implicação para o gestor
- Estilo direto e executivo

Exemplos de bons action titles:
- "MAC concentra 68% dos gastos da Saúde, exigindo governança rigorosa sobre contratos hospitalares"
- "Três fornecedores de limpeza respondem por 41% do custo operacional não-pessoal"
- "Pico de R$ 4,2M em março coincide com renovação de contratos anuais"

Responda APENAS com o action title, sem aspas nem explicações."""

    resp = client.messages.create(
        model='claude-sonnet-4-20250514', max_tokens=150, temperature=0.3,
        messages=[{'role': 'user', 'content': prompt}]
    )
    return resp.content[0].text.strip()
```

### 5.2 Geração de Recomendações via API Claude

```python
def gerar_recomendacoes(kpis, composicao, fornecedores, secretaria, n=4):
    prompt = f"""Você é um consultor McKinsey analisando os custos da secretaria de {secretaria}
do município de Sete Lagoas (MG) em 2025.

Dados principais:
{json.dumps({'kpis': kpis, 'top_programas': composicao[:5], 'top_fornecedores': fornecedores[:5]}, ensure_ascii=False, indent=2)}

Gere exatamente {n} recomendações de gestão baseadas nos dados.
Cada recomendação deve ter:
- "insight": o dado que fundamenta (1-2 frases com número)
- "implicacao": o que isso significa para a gestão (1 frase)
- "acao": a ação concreta sugerida (1 frase, começar com verbo no infinitivo)

Responda APENAS com JSON:
[{{"insight": "...", "implicacao": "...", "acao": "..."}}, ...]"""

    resp = client.messages.create(
        model='claude-sonnet-4-20250514', max_tokens=1500, temperature=0.5,
        messages=[{'role': 'user', 'content': prompt}]
    )
    return json.loads(resp.content[0].text)
```

### 5.3 Template CSS (McKinsey style)

```css
:root {
    --azul-escuro:  #1B3A5C;
    --azul-medio:   #2E86AB;
    --azul-claro:   #A3CEF1;
    --verde:        #28A745;
    --vermelho:     #E63946;
    --amarelo:      #F4A261;
    --cinza-escuro: #343A40;
    --cinza-medio:  #6C757D;
    --fundo:        #F8F9FA;
    --branco:       #FFFFFF;
    --fonte:        system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}

body {
    font-family: var(--fonte);
    background: var(--fundo);
    color: var(--cinza-escuro);
    line-height: 1.6;
    margin: 0;
    padding: 0;
}

/* Barra de navegação lateral */
.nav-sidebar {
    position: fixed;
    left: 0; top: 0;
    width: 220px; height: 100vh;
    background: var(--azul-escuro);
    padding: 2rem 1rem;
    overflow-y: auto;
    z-index: 100;
}
.nav-sidebar a {
    display: block;
    color: rgba(255,255,255,0.7);
    text-decoration: none;
    padding: 0.5rem 0.75rem;
    border-radius: 4px;
    font-size: 0.85rem;
    margin-bottom: 0.25rem;
    transition: all 0.2s;
}
.nav-sidebar a:hover, .nav-sidebar a.active {
    background: var(--azul-medio);
    color: var(--branco);
}

.main-content {
    margin-left: 220px;
    padding: 2rem 2.5rem;
    max-width: 1100px;
}

/* Hero */
.hero {
    background: linear-gradient(135deg, var(--azul-escuro), var(--azul-medio));
    color: white;
    padding: 3rem;
    border-radius: 16px;
    margin-bottom: 2rem;
}
.hero h1 { font-size: 2rem; margin: 0 0 0.5rem; }
.hero .action-title-hero {
    font-size: 1.15rem;
    opacity: 0.9;
    font-weight: 400;
    max-width: 700px;
}
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
    margin-top: 2rem;
}
.kpi-card {
    background: rgba(255,255,255,0.15);
    border-radius: 10px;
    padding: 1.25rem;
    text-align: center;
    backdrop-filter: blur(4px);
}
.kpi-label  { font-size: 0.75rem; opacity: 0.8; text-transform: uppercase; letter-spacing: 0.05em; }
.kpi-value  { font-size: 1.6rem; font-weight: 700; margin: 0.25rem 0; }
.kpi-sub    { font-size: 0.8rem; opacity: 0.7; }

/* Seções */
.section {
    background: var(--branco);
    border-radius: 12px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.section-id {
    font-size: 0.7rem;
    color: var(--azul-medio);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
    margin-bottom: 0.5rem;
}
.action-title {
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--azul-escuro);
    border-left: 4px solid var(--azul-medio);
    padding-left: 1rem;
    margin-bottom: 1.5rem;
    line-height: 1.4;
}
.chart-container { position: relative; height: 380px; margin: 1rem 0 1.5rem; }

/* Tabelas */
.data-table { width: 100%; border-collapse: collapse; font-size: 0.88rem; margin-top: 1rem; }
.data-table th {
    background: var(--azul-escuro); color: white;
    padding: 0.6rem 0.8rem; text-align: left; font-weight: 500;
}
.data-table td { padding: 0.5rem 0.8rem; border-bottom: 1px solid var(--fundo); }
.data-table tr:hover td { background: var(--fundo); }
.heat-high  { background: #FDECEA; color: var(--vermelho); font-weight: 600; }
.heat-med   { background: #FFF8E1; color: #856404; }
.heat-low   { background: #E8F5E9; color: #2E7D32; }

/* Recomendações */
.rec-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; }
.rec-card { border-left: 4px solid var(--verde); padding: 1.25rem; background: #F0FFF4; border-radius: 0 10px 10px 0; }
.rec-insight    { font-size: 0.95rem; color: var(--cinza-escuro); margin-bottom: 0.5rem; }
.rec-implicacao { font-size: 0.88rem; color: var(--cinza-medio); margin-bottom: 0.75rem; }
.rec-acao       { font-size: 0.88rem; font-weight: 600; color: var(--azul-escuro); }
.rec-acao::before { content: "→ "; color: var(--verde); }

/* Responsivo */
@media (max-width: 768px) {
    .nav-sidebar  { display: none; }
    .main-content { margin-left: 0; padding: 1rem; }
    .hero         { padding: 1.5rem; }
    .hero h1      { font-size: 1.4rem; }
    .chart-container { height: 280px; }
}
```

### 5.4 Configurações Chart.js por tipo

```javascript
// Paleta global
const CORES = {
    principal: '#2E86AB', secundaria: '#A3CEF1',
    verde: '#28A745', vermelho: '#E63946',
    amarelo: '#F4A261', cinza: '#6C757D',
    palette: ['#1B3A5C','#2E86AB','#A3CEF1','#28A745','#F4A261','#E63946','#6C757D','#17BECF','#8C564B','#E377C2']
};

// Formatação monetária BR
const formatBRL = v => 'R$ ' + v.toLocaleString('pt-BR', {minimumFractionDigits: 0, maximumFractionDigits: 0});
const formatM   = v => 'R$ ' + (v/1e6).toFixed(1).replace('.',',') + 'M';

// Bar horizontal (composição por programa, ação)
const configBarH = (labels, values, title) => ({
    type: 'bar',
    data: {
        labels,
        datasets: [{ data: values, backgroundColor: CORES.principal,
                     borderRadius: 4, barPercentage: 0.7 }]
    },
    options: {
        indexAxis: 'y',
        plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: ctx => formatBRL(ctx.raw) } }
        },
        scales: {
            x: { ticks: { callback: v => formatM(v) }, grid: { display: false } },
            y: { grid: { display: false } }
        }
    }
});

// Doughnut (categorias, natureza macro)
const configDoughnut = (labels, values) => ({
    type: 'doughnut',
    data: {
        labels,
        datasets: [{ data: values, backgroundColor: CORES.palette,
                     borderWidth: 2, borderColor: '#fff' }]
    },
    options: {
        cutout: '60%',
        plugins: {
            legend: { position: 'right' },
            tooltip: { callbacks: {
                label: ctx => `${ctx.label}: ${formatBRL(ctx.raw)} (${(ctx.raw/ctx.dataset.data.reduce((a,b)=>a+b)*100).toFixed(1)}%)`
            }}
        }
    }
});

// Line (série mensal)
const configLine = (meses, valores) => ({
    type: 'line',
    data: {
        labels: meses,
        datasets: [{
            label: '2025',
            data: valores,
            borderColor: CORES.principal,
            backgroundColor: CORES.principal + '20',
            tension: 0.3, fill: true, pointRadius: 5,
            pointBackgroundColor: CORES.principal
        }]
    },
    options: {
        plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: ctx => formatBRL(ctx.raw) } }
        },
        scales: {
            x: { grid: { display: false } },
            y: { ticks: { callback: v => formatM(v) } }
        }
    }
});
```

### 5.5 Estrutura HTML base

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Custos da {SECRETARIA} — Sete Lagoas 2025</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>/* CSS inline aqui */</style>
</head>
<body>

<nav class="nav-sidebar">
    <div style="color:white;font-weight:700;margin-bottom:1.5rem;font-size:0.9rem">
        📊 Custos {SECRETARIA}<br>
        <small style="opacity:0.6">Sete Lagoas · 2025</small>
    </div>
    <a href="#hero">Resumo Executivo</a>
    <a href="#programas">Composição por Programa</a>
    <a href="#natureza">Natureza de Despesa</a>
    <a href="#acoes">Por Ação</a>
    <a href="#fornecedores">Fornecedores</a>
    <a href="#categorias">Categorias de Custo</a>
    <a href="#mensal">Evolução Mensal</a>
    <a href="#fontes">Fontes de Recurso</a>
    <a href="#recomendacoes">Recomendações</a>
</nav>

<div class="main-content">
    <!-- seções geradas dinamicamente -->
</div>

<script>
const DATA = /* JSON inline */;
/* JavaScript de inicialização de charts */
</script>
</body>
</html>
```

---

## 6. Tratamento de Edge Cases

| Situação | Tratamento |
|---|---|
| `vlr_pago` zerado em meses iniciais | Incluir na série — é informação válida (gasto zero) |
| `nom_credor` vazio no pagamento | Buscar em `credorEmpenho` via `seq_empenho`; fallback: "NÃO IDENTIFICADO" |
| Empenhos com `vlr_empenhado` negativo | São anulações — manter; ao somar, resultado líquido será correto |
| Encoding misto no CSV | `encoding='latin-1', errors='replace'` — nunca gera exceção |
| `cod_unidade` como int64 no CSV | `.astype(str).str.strip()` antes de qualquer filtro |
| Meses faltantes (dado parcial) | Só exibir meses que existem; anotar "Jan–[último mês] 2025" no relatório |
| API Claude indisponível | Classificar ambíguos como categoria 14 (Outros); logar em `classificacao_erros.log` |
| HTML > 2MB | Truncar ranking de fornecedores em top 30; simplificar heatmap mensal |

---

## 7. Dependências

```
pandas>=2.0
openpyxl>=3.1
pyarrow>=14.0
anthropic>=0.39
```

```bash
pip install pandas openpyxl pyarrow anthropic --break-system-packages
```
