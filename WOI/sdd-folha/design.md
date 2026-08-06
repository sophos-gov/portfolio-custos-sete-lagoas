# Design — Integração da Folha de Pagamento nos Dashboards de Custos

## 1. Arquitetura Geral

```
┌───────────────────────────────────────────────────────────────────┐
│                        Pipeline Existente                        │
│  extract_data → classify_empenhos → generate_tables → build_html │
└──────────────────────────────┬────────────────────────────────────┘
                               │
          ┌────────────────────▼────────────────────────┐
          │          NOVA INTEGRAÇÃO — FOLHA             │
          │                                              │
          │  ┌─────────────────────┐                     │
          │  │ generate_folha.py   │  Etapa A — Tabelas  │
          │  │                     │                      │
          │  │ • Lê CSV folha      │                      │
          │  │ • Normaliza valores │                      │
          │  │ • Classifica vínculo│                      │
          │  │ • Gera tabelas CSV  │                      │
          │  │ • Calcula KPIs JSON │                      │
          │  └────────┬────────────┘                      │
          │           │                                   │
          │  ┌────────▼─────────────┐                     │
          │  │ build_html_saude.py  │ Etapa B — HTML      │
          │  │ build_html_educacao.py│ (MODIFICADOS)      │
          │  │                      │                     │
          │  │ • Carrega tabelas    │                     │
          │  │ • Chama API Opus     │                     │
          │  │ • Cruza com WOI      │                     │
          │  │ • Gera seção HTML    │                     │
          │  └──────────────────────┘                     │
          │                                              │
          │  ┌──────────────────────────┐                │
          │  │ processa_folha_educacao.py│ GANCHO futuro  │
          │  │ (standalone para 2026)    │                │
          │  └──────────────────────────┘                │
          └──────────────────────────────────────────────┘
```

### 1.1 Novos arquivos

| Arquivo | Localização | Papel |
|---------|------------|-------|
| `generate_folha.py` | `../output/` | Processa CSV da folha → gera tabelas + KPIs |
| `build_html_saude.py` | `../output/` | **MODIFICAR** — adicionar seção `#pessoal` |
| `build_html_educacao.py` | `../output/` | **MODIFICAR** — aprimorar seção `#pessoal` |
| `processa_folha_educacao.py` | `../output/` | Script standalone para folha futura da educação |
| `PROMPT_INCORPORAR_FOLHA_EDUCACAO.md` | `../sdd-folha/` | Prompt para Claude Code |

### 1.2 Armazenamento intermediário

```
../output/tabelas/
├── saude/
│   ├── (existentes: composicao_programa.csv, kpis.json, etc.)
│   └── folha/                    ← NOVO
│       ├── kpis_folha.json
│       ├── por_vinculo.csv
│       ├── distribuicao_faixas.csv
│       ├── top_locais.csv
│       ├── top_cargos.csv
│       ├── alertas_folha.csv
│       ├── rubricas_top.csv
│       └── cruzamento_woi.json
│
└── educacao/
    ├── (existentes)
    └── folha/                    ← NOVO
        ├── kpis_folha.json
        ├── por_vinculo.csv
        ├── distribuicao_faixas.csv
        ├── top_locais.csv
        ├── top_cargos.csv
        ├── alertas_folha.csv
        ├── rubricas_top.csv
        ├── cruzamento_woi.json
        ├── custo_por_escola.csv  ← específico educação
        └── tempo_servico.csv     ← específico educação
```

---

## 2. Modelo de Dados da Folha

### 2.1 Leitura e normalização do CSV

```python
import pandas as pd
import numpy as np
import re
import os

def ler_folha_csv(csv_path, encoding='latin-1', sep=';'):
    """Lê CSV da folha de pagamento e normaliza."""
    df = pd.read_csv(csv_path, encoding=encoding, sep=sep, dtype=str)

    # Normalizar nomes de colunas (remover acentos problemáticos de encoding)
    df.rename(columns=lambda c: (
        c.replace('\xed', 'i').replace('\xe7', 'c').replace('\xe3', 'a')
         .replace('\xe9', 'e').replace('\xea', 'e').replace('\xf3', 'o')
         .replace('\xf5', 'o').replace('\xfa', 'u').replace('\xe2', 'a')
         .replace('\xf4', 'o').replace('\xc3', 'A').strip()
    ), inplace=True)

    return df


def to_num(s):
    """Converte série de strings BR para float."""
    return (
        s.astype(str).str.strip()
         .str.replace(r'\s', '', regex=True)
         .str.replace(',', '.', regex=False)
         .replace({'': '0', 'nan': '0', 'None': '0'})
         .astype(float)
    )
```

### 2.2 Detecção automática de colunas

```python
def detectar_colunas(df):
    """Detecta colunas-chave independente de encoding."""
    cols = {}
    for c in df.columns:
        cl = c.lower().strip()
        if 'matr' in cl:                          cols['matricula'] = c
        elif cl in ('nome', 'servidor'):           cols['nome'] = c
        elif 'lota' in cl:                         cols['lotacao'] = c
        elif cl == 'cargo':                        cols['cargo'] = c
        elif cl.startswith('fun') and 'fonte' not in cl: cols['funcao'] = c
        elif 'cod' in cl and 'padr' in cl:         cols['cod_padrao'] = c
        elif 'descri' in cl and 'padr' in cl:      cols['desc_padrao'] = c
        elif cl == 'proventos':                     cols['proventos'] = c
        elif cl in ('descontos', 'desconto'):       cols['descontos'] = c
        elif cl in ('liquido', 'líquido'):          cols['liquido'] = c
        elif 'tipo contrato' in cl or 'tipo_contrato' in cl: cols['tipo_contrato'] = c
        elif cl in ('admissao', 'admissão'):        cols['admissao'] = c
        elif 'local de trabalho' in cl:             cols['local_trabalho'] = c
    return cols
```

### 2.3 Classificação de vínculos

```python
def classificar_vinculo(lotacao_str):
    """Classifica tipo de vínculo a partir do campo Lotação."""
    lot = str(lotacao_str).upper()
    if 'EFETIV' in lot:
        return 'EFETIVO'
    elif 'COMISSION' in lot:
        return 'COMISSIONADO'
    elif 'APOSENTAD' in lot or 'PENSIONIST' in lot:
        return 'APOSENTADO'
    elif 'CONTRATO' in lot:
        return 'CONTRATO'
    else:
        return 'OUTROS'

# Aplicação:
# df['VINCULO'] = df[cols['lotacao']].apply(classificar_vinculo)
```

**Nota para Educação (xlsx):** O campo `Tipo Contrato` já traz a classificação diretamente:
- `Efetivo` → EFETIVO
- `Temporário` / `Contrato Temporário` → CONTRATO
- `Aposentado` → APOSENTADO

### 2.4 Cálculos derivados

```python
def calcular_campos(df, cols):
    """Calcula campos derivados para análise."""
    # Converter valores monetários
    for c in [cols.get('proventos'), cols.get('descontos'), cols.get('liquido')]:
        if c and c in df.columns:
            df[c] = to_num(df[c])

    # Detectar e converter rubricas
    valor_cols = [c for c in df.columns if c.startswith('Valor_')]
    prov_cols = [c for c in valor_cols if re.match(r'Valor_\d', c)]
    desc_cols = [c for c in valor_cols if re.match(r'Valor_R', c)]

    for c in valor_cols:
        df[c] = to_num(df[c])

    # Campos calculados
    df['BRUTO'] = df[cols.get('proventos', 'Proventos')]
    df['DESCONTOS'] = df[cols.get('descontos', 'Descontos')]
    df['LIQUIDO'] = df[cols.get('liquido', 'Liquido')]
    df['TAXA_DESCONTO'] = df['DESCONTOS'] / df['BRUTO'].replace(0, np.nan)

    # Classificar vínculo
    col_lot = cols.get('lotacao')
    if col_lot:
        df['VINCULO'] = df[col_lot].apply(classificar_vinculo)

    # Extrair local limpo da lotação
    if col_lot:
        df['LOCAL'] = df[col_lot].str.extract(r'\d+\s*-\s*\d+\s*-\s*(.+?)(?:\s*-\s*(?:EFETIV|COMISSION|CONTRATO|APOSENTAD).*)?\s*$')[0].str.strip()
        df['LOCAL'] = df['LOCAL'].fillna(df[col_lot])

    return df, prov_cols, desc_cols
```

### 2.5 Índice de Gini

```python
def gini(array):
    """Calcula o coeficiente de Gini para uma distribuição."""
    array = np.sort(np.array(array, dtype=float))
    array = array[array > 0]
    if len(array) == 0:
        return 0.0
    n = len(array)
    index = np.arange(1, n + 1)
    return float((2 * np.sum(index * array) - (n + 1) * np.sum(array)) / (n * np.sum(array)))
```

---

## 3. Geração de Tabelas Analíticas (generate_folha.py)

### 3.1 KPIs da Folha

```python
def gerar_kpis_folha(df, kpis_woi, secretaria, competencia):
    """Gera JSON com KPIs da folha + cruzamento com WOI."""
    ativos = df[df['VINCULO'] != 'APOSENTADO']

    total_bruto = float(ativos['BRUTO'].sum())
    total_liq = float(ativos['LIQUIDO'].sum())
    total_desc = float(ativos['DESCONTOS'].sum())
    qtd = int(len(ativos))
    g = gini(ativos['BRUTO'].values)

    # Cruzamento WOI
    total_pago_woi = kpis_woi.get('total_pago', 0)
    meses_cobertos = kpis_woi.get('meses_cobertos', 12)
    folha_anualizada = total_bruto * 12
    pct_folha_orcamento = (folha_anualizada / total_pago_woi * 100) if total_pago_woi else 0

    return {
        'secretaria': secretaria,
        'competencia': competencia,
        'total_servidores_ativos': qtd,
        'total_aposentados': int(len(df[df['VINCULO'] == 'APOSENTADO'])),
        'total_bruto': total_bruto,
        'total_liquido': total_liq,
        'total_descontos': total_desc,
        'media_bruto': float(ativos['BRUTO'].mean()) if qtd else 0,
        'mediana_bruto': float(ativos['BRUTO'].median()) if qtd else 0,
        'gini': g,
        'taxa_desconto_media': float(total_desc / total_bruto * 100) if total_bruto else 0,
        'folha_anualizada': folha_anualizada,
        'pct_folha_orcamento': pct_folha_orcamento,
        'total_pago_woi': total_pago_woi,
        'meses_cobertos_woi': meses_cobertos,
        'elite_acima_20k': {
            'qtd': int((ativos['BRUTO'] > 20000).sum()),
            'total': float(ativos[ativos['BRUTO'] > 20000]['BRUTO'].sum()),
            'pct_folha': float(ativos[ativos['BRUTO'] > 20000]['BRUTO'].sum() / total_bruto * 100) if total_bruto else 0
        }
    }
```

### 3.2 Distribuição por vínculo

```python
def gerar_por_vinculo(df):
    """Agrupa por tipo de vínculo."""
    total = df['BRUTO'].sum()
    t = df.groupby('VINCULO').agg(
        qtd_servidores=('BRUTO', 'count'),
        total_bruto=('BRUTO', 'sum'),
        media_bruto=('BRUTO', 'mean'),
        mediana_bruto=('BRUTO', 'median')
    ).reset_index()
    t.columns = ['vinculo', 'qtd_servidores', 'total_bruto', 'media_bruto', 'mediana_bruto']
    t['pct_folha'] = t['total_bruto'] / total * 100
    t = t.sort_values('total_bruto', ascending=False)
    return t
```

### 3.3 Distribuição por faixa salarial

```python
FAIXAS_SAUDE = [
    (0,     2000,  'Até R$ 2 mil'),
    (2000,  3500,  'R$ 2–3,5 mil'),
    (3500,  5500,  'R$ 3,5–5,5 mil'),
    (5500,  8000,  'R$ 5,5–8 mil'),
    (8000,  12000, 'R$ 8–12 mil'),
    (12000, 20000, 'R$ 12–20 mil'),
    (20000, 1e9,   'Acima R$ 20 mil'),
]

def gerar_faixas(df, faixas=FAIXAS_SAUDE):
    """Distribui servidores ativos por faixa salarial."""
    ativos = df[df['VINCULO'] != 'APOSENTADO']
    total = len(ativos)
    rows = []
    for inf, sup, label in faixas:
        mask = (ativos['BRUTO'] > inf) & (ativos['BRUTO'] <= sup)
        n = int(mask.sum())
        soma = float(ativos.loc[mask, 'BRUTO'].sum())
        rows.append({
            'faixa': label,
            'qtd': n,
            'pct_servidores': n / total * 100 if total else 0,
            'total_bruto': soma
        })
    return pd.DataFrame(rows)
```

### 3.4 Top locais

```python
def gerar_top_locais(df, top_n=15):
    """Top locais de lotação por custo total."""
    ativos = df[df['VINCULO'] != 'APOSENTADO']
    total = ativos['BRUTO'].sum()
    t = ativos.groupby('LOCAL').agg(
        qtd_servidores=('BRUTO', 'count'),
        total_bruto=('BRUTO', 'sum'),
        media_bruto=('BRUTO', 'mean')
    ).reset_index()
    t['pct_folha'] = t['total_bruto'] / total * 100
    t = t.sort_values('total_bruto', ascending=False).head(top_n)
    return t
```

### 3.5 Alertas

```python
def gerar_alertas(df):
    """Detecta anomalias e gera tabela de alertas."""
    alertas = []

    # Elite > R$ 20k
    elite = df[(df['VINCULO'] != 'APOSENTADO') & (df['BRUTO'] > 20000)]
    for _, r in elite.iterrows():
        alertas.append({
            'tipo': 'elite_acima_20k',
            'matricula': r.get('matricula', ''),
            'nome': r.get('nome', ''),
            'cargo': r.get('cargo', ''),
            'valor': r['BRUTO'],
            'detalhe': f'Provento bruto de R$ {r["BRUTO"]:,.2f}'
        })

    # Desconto > 50%
    desc_alto = df[(df['TAXA_DESCONTO'] > 0.5) & (df['VINCULO'] != 'APOSENTADO')]
    for _, r in desc_alto.iterrows():
        alertas.append({
            'tipo': 'desconto_acima_50pct',
            'matricula': r.get('matricula', ''),
            'nome': r.get('nome', ''),
            'cargo': r.get('cargo', ''),
            'valor': r['TAXA_DESCONTO'] * 100,
            'detalhe': f'Taxa de desconto de {r["TAXA_DESCONTO"]*100:.1f}%'
        })

    # Outlier por cargo (> Q3 + 1.5*IQR)
    ativos = df[df['VINCULO'] != 'APOSENTADO']
    col_cargo = 'cargo' if 'cargo' in df.columns else None
    if col_cargo:
        for cargo, grupo in ativos.groupby(col_cargo):
            if len(grupo) >= 5:
                q1, q3 = grupo['BRUTO'].quantile([0.25, 0.75])
                iqr = q3 - q1
                limite = q3 + 1.5 * iqr
                outliers = grupo[grupo['BRUTO'] > limite]
                for _, r in outliers.iterrows():
                    alertas.append({
                        'tipo': 'outlier_cargo',
                        'matricula': r.get('matricula', ''),
                        'nome': r.get('nome', ''),
                        'cargo': cargo,
                        'valor': r['BRUTO'],
                        'detalhe': f'Acima do limite de R$ {limite:,.2f} para {cargo}'
                    })

    return pd.DataFrame(alertas) if alertas else pd.DataFrame(
        columns=['tipo', 'matricula', 'nome', 'cargo', 'valor', 'detalhe']
    )
```

### 3.6 Top rubricas

```python
def gerar_rubricas_top(df, prov_cols, desc_cols, top_n=20):
    """Identifica as rubricas mais representativas."""
    ativos = df[df['VINCULO'] != 'APOSENTADO']
    total_folha = ativos['BRUTO'].sum()
    rows = []

    for c in prov_cols:
        total = ativos[c].sum()
        if total > 0:
            codigo = c.replace('Valor_', '')
            qtd = int((ativos[c] > 0).sum())
            rows.append({
                'rubrica': codigo,
                'tipo': 'provento',
                'total': total,
                'pct_folha': total / total_folha * 100 if total_folha else 0,
                'qtd_servidores': qtd
            })

    for c in desc_cols:
        total = ativos[c].sum()
        if total > 0:
            codigo = c.replace('Valor_', '')
            qtd = int((ativos[c] > 0).sum())
            rows.append({
                'rubrica': codigo,
                'tipo': 'desconto',
                'total': total,
                'pct_folha': total / total_folha * 100 if total_folha else 0,
                'qtd_servidores': qtd
            })

    result = pd.DataFrame(rows).sort_values('total', ascending=False).head(top_n)
    return result
```

### 3.7 Cruzamento com WOI

```python
def gerar_cruzamento_woi(kpis_folha, kpis_woi, categorias_csv_path, serie_csv_path):
    """Cruza dados da folha com dados orçamentários do WOI."""
    result = {
        'folha_mensal': kpis_folha['total_bruto'],
        'folha_anualizada': kpis_folha['folha_anualizada'],
        'gasto_total_woi': kpis_woi.get('total_pago', 0),
        'pct_folha_orcamento': kpis_folha['pct_folha_orcamento'],
    }

    # Comparar com categoria "Pessoal" nos empenhos classificados
    if os.path.exists(categorias_csv_path):
        cat = pd.read_csv(categorias_csv_path)
        nome_col = 'categoria_nome' if 'categoria_nome' in cat.columns else cat.columns[0]
        pessoal_row = cat[cat[nome_col].str.contains('Pessoal', case=False, na=False)]
        if not pessoal_row.empty:
            vlr_col = 'vlr_empenhado' if 'vlr_empenhado' in cat.columns else 'total'
            result['pessoal_empenho'] = float(pessoal_row[vlr_col].sum())
            result['diferenca_folha_vs_empenho'] = result['folha_anualizada'] - result['pessoal_empenho']

    # Série mensal para contexto
    if os.path.exists(serie_csv_path):
        serie = pd.read_csv(serie_csv_path)
        if not serie.empty:
            result['media_mensal_woi'] = float(serie['vlr_pago'].mean())
            result['pct_folha_media_mensal'] = (
                kpis_folha['total_bruto'] / result['media_mensal_woi'] * 100
            ) if result['media_mensal_woi'] else 0

    return result
```

---

## 4. Análise via API Claude Opus

### 4.1 Prompt consolidado (uma chamada para tudo)

```python
import anthropic, json, re

def gerar_analise_folha_opus(client, kpis_folha, dados_folha, cruzamento, secretaria):
    """
    Uma chamada Opus com dados consolidados da folha + cruzamento WOI.
    Retorna: action_title, análise narrativa, alertas e recomendações.
    """
    payload = {
        'secretaria': secretaria,
        'municipio': 'Sete Lagoas (MG)',
        'kpis_folha': kpis_folha,
        'por_vinculo': dados_folha.get('por_vinculo', []),
        'faixas_salariais': dados_folha.get('faixas', []),
        'top_locais': dados_folha.get('top_locais', []),
        'top_cargos': dados_folha.get('top_cargos', []),
        'rubricas_top': dados_folha.get('rubricas', []),
        'alertas_detectados': dados_folha.get('alertas', []),
        'cruzamento_woi': cruzamento,
    }

    prompt = f"""Você é um consultor sênior de gestão pública analisando a folha de pagamento da Secretaria de {secretaria} de Sete Lagoas (MG).

DADOS DA FOLHA E CRUZAMENTO COM ORÇAMENTO:
{json.dumps(payload, ensure_ascii=False, indent=2)}

Analise com profundidade — procure padrões, anomalias, riscos e oportunidades. CRUZE os dados da folha com os dados orçamentários para insights que não seriam possíveis olhando cada fonte isolada.

Retorne EXATAMENTE este JSON (sem markdown, sem texto fora do JSON):

{{
  "action_title_pessoal": "Frase executiva de até 22 palavras com número + implicação. Ex: 'Folha de R$ 6,4M absorve 63% do orçamento; 42 médicos acima de R$ 20k representam 18% do custo'",
  "analise_folha": "Parágrafo de 4-5 frases analisando a estrutura da folha: composição por vínculo, concentração salarial, relação entre cargos e custo. Linguagem executiva, dados concretos.",
  "cruzamento_custos": "Parágrafo de 3-4 frases conectando a folha com os dados orçamentários: % da folha no gasto total, coerência entre empenhos de pessoal e folha real, sazonalidade. Insight que só emerge com visão cruzada.",
  "alertas_folha": [
    "Alerta 1 (mais severo): dado concreto + risco + consequência",
    "Alerta 2: segundo risco com números",
    "Alerta 3: terceiro achado relevante"
  ],
  "recomendacoes_folha": [
    {{
      "insight": "dado específico com valor ou %",
      "implicacao": "o que significa para a gestão",
      "acao": "ação concreta — verbo no infinitivo"
    }},
    {{
      "insight": "...",
      "implicacao": "...",
      "acao": "..."
    }}
  ]
}}

REGRAS:
- Action title: afirmação com ≥2 números; evite rótulos genéricos
- Cruzamento: obrigatório conectar folha com dados WOI
- Alertas: ordenados por severidade; baseados nos dados fornecidos
- Recomendações: 2 exatas; concretas e mensuráveis; baseadas nos dados"""

    resp = client.messages.create(
        model='claude-opus-4-6',
        max_tokens=3000,
        temperature=0.2,
        messages=[{'role': 'user', 'content': prompt}]
    )

    texto = resp.content[0].text.strip()
    texto = re.sub(r'^```[a-z]*\n?', '', texto)
    texto = re.sub(r'\n?```$', '', texto)
    return json.loads(texto)
```

### 4.2 Fallback sem API

```python
def gerar_analise_folha_fallback(kpis_folha, cruzamento, secretaria):
    """Gera análise da folha sem API, usando templates + dados reais."""
    total = kpis_folha['total_bruto']
    qtd = kpis_folha['total_servidores_ativos']
    media = kpis_folha['media_bruto']
    g = kpis_folha['gini']
    pct_orc = kpis_folha['pct_folha_orcamento']
    elite = kpis_folha['elite_acima_20k']

    def brl(v):
        try: return f"R$ {v:_.0f}".replace("_", ".")
        except: return "R$ 0"

    def m(v):
        if v >= 1e6: return f"R$ {v/1e6:.1f}M".replace('.', ',')
        if v >= 1e3: return f"R$ {v/1e3:.0f} mil"
        return brl(v)

    return {
        'action_title_pessoal': (
            f"Folha de {m(total)} para {qtd} servidores absorve {pct_orc:.0f}% do orçamento; "
            f"{elite['qtd']} acima de R$ 20 mil representam {elite['pct_folha']:.0f}% do custo"
        ),
        'analise_folha': (
            f"A folha bruta mensal de {secretaria} é de {m(total)} para {qtd} servidores ativos, "
            f"com média de {brl(media)} e Gini de {g:.2f}. "
            f"Os {elite['qtd']} servidores com remuneração acima de R$ 20 mil concentram "
            f"{brl(elite['total'])} ({elite['pct_folha']:.1f}% da folha)."
        ),
        'cruzamento_custos': (
            f"A folha anualizada de {m(kpis_folha['folha_anualizada'])} representa "
            f"{pct_orc:.1f}% do gasto total de {m(cruzamento.get('gasto_total_woi', 0))} da secretaria."
        ),
        'alertas_folha': [
            f"{elite['qtd']} servidores ({elite['pct_folha']:.1f}%) concentram "
            f"{brl(elite['total'])} em proventos acima de R$ 20 mil",
        ],
        'recomendacoes_folha': [
            {
                'insight': f"Folha de {m(total)}/mês representa {pct_orc:.0f}% do gasto total.",
                'implicacao': 'Comprometimento alto com pessoal limita margem para investimentos.',
                'acao': 'Mapear posições a vagar nos próximos 24 meses e avaliar se reposição é necessária.'
            },
            {
                'insight': f"Índice de Gini de {g:.2f} indica concentração salarial moderada a alta.",
                'implicacao': 'Poucos servidores consomem parcela desproporcional do orçamento.',
                'acao': 'Revisar política de gratificações e funções comissionadas para os top 50 servidores.'
            }
        ]
    }
```

---

## 5. HTML — Seção de Pessoal

### 5.1 Estrutura HTML da seção

```html
<!-- PESSOAL -->
<section class="section" id="pessoal">
    <div class="section-id">Seção 9 — Análise de Pessoal (Folha {COMPETENCIA})</div>
    <div class="action-title">{action_title_pessoal}</div>

    <!-- KPI Cards -->
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:1rem;margin-bottom:1.5rem">
        <div class="kpi-card" style="background:var(--azul-escuro);color:white">
            <div class="kpi-label">Servidores Ativos</div>
            <div class="kpi-value">{qtd}</div>
        </div>
        <div class="kpi-card" style="background:var(--azul-escuro);color:white">
            <div class="kpi-label">Folha Bruta Mensal</div>
            <div class="kpi-value">{total_m}</div>
            <div class="kpi-sub">{total_brl}</div>
        </div>
        <div class="kpi-card" style="background:var(--azul-escuro);color:white">
            <div class="kpi-label">Média Salarial</div>
            <div class="kpi-value">{media_brl}</div>
        </div>
        <div class="kpi-card" style="background:var(--vermelho);color:white">
            <div class="kpi-label">Índice de Gini</div>
            <div class="kpi-value">{gini:.2f}</div>
            <div class="kpi-sub">concentração salarial</div>
        </div>
    </div>

    <!-- Charts: Vínculo + Faixas -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem">
        <div>
            <h4 style="...">Por Tipo de Vínculo</h4>
            <div class="chart-container short"><canvas id="chartVinculo"></canvas></div>
        </div>
        <div>
            <h4 style="...">Distribuição por Faixa Salarial</h4>
            <div class="chart-container short"><canvas id="chartFaixas"></canvas></div>
        </div>
    </div>

    <!-- Tabela de Vínculos -->
    {tabela_vinculos_html}

    <!-- Top Locais -->
    <h4>Top 10 Unidades por Custo de Pessoal</h4>
    <div class="chart-container"><canvas id="chartLocais"></canvas></div>
    {tabela_locais_html}

    <!-- Top Rubricas -->
    <h4>Rubricas de Maior Impacto</h4>
    <div class="chart-container short"><canvas id="chartRubricas"></canvas></div>

    <!-- Cruzamento com Custos WOI -->
    <h4>Folha vs. Orçamento — Visão Integrada</h4>
    <div class="analise-cruzada">{cruzamento_custos}</div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:1rem;margin:1rem 0">
        <div class="kpi-card" style="background:#EBF4FF">
            <div class="kpi-label">Folha Anualizada</div>
            <div class="kpi-value">{folha_anual_m}</div>
        </div>
        <div class="kpi-card" style="background:#EBF4FF">
            <div class="kpi-label">Gasto Total WOI</div>
            <div class="kpi-value">{total_woi_m}</div>
        </div>
        <div class="kpi-card" style="background:{cor_pct}">
            <div class="kpi-label">% Folha / Orçamento</div>
            <div class="kpi-value">{pct_folha}%</div>
        </div>
    </div>

    <!-- Alertas -->
    {alertas_html if alertas else ''}
</section>
```

### 5.2 Charts JavaScript (adicionar ao script inline)

```javascript
// Vínculo (doughnut)
new Chart(document.getElementById('chartVinculo'), {
    type: 'doughnut',
    data: { labels: VINC_LABELS, datasets: [{
        data: VINC_VALUES, backgroundColor: CORES.palette, borderWidth: 2, borderColor: '#fff'
    }]},
    options: { cutout: '55%', plugins: {
        legend: { position: 'right' },
        tooltip: { callbacks: { label: ctx => ctx.label + ': ' + formatBRL(ctx.raw) } }
    }}
});

// Faixas salariais (bar horizontal)
new Chart(document.getElementById('chartFaixas'), {
    type: 'bar',
    data: { labels: FAIXA_LABELS, datasets: [{
        data: FAIXA_VALUES, backgroundColor: CORES.principal, borderRadius: 4, barPercentage: 0.7
    }]},
    options: {
        indexAxis: 'y',
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ctx.raw + ' servidores' }}},
        scales: { x: { grid: { display: false }}, y: { grid: { display: false }}}
    }
});

// Top locais (bar horizontal)
new Chart(document.getElementById('chartLocais'), {
    type: 'bar',
    data: { labels: LOCAL_LABELS, datasets: [{
        data: LOCAL_VALUES, backgroundColor: CORES.principal, borderRadius: 4, barPercentage: 0.65
    }]},
    options: {
        indexAxis: 'y',
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => formatBRL(ctx.raw) }}},
        scales: { x: { ticks: { callback: v => formatM(v) }, grid: { display: false }}, y: { grid: { display: false }}}
    }
});
```

---

## 6. Educação — Análises Específicas

### 6.1 Custo por escola

```python
def gerar_custo_por_escola(df, cols, top_n=15):
    """Top escolas por custo — usa 'Local de trabalho' para nome real."""
    col_escola = cols.get('local_trabalho') or cols.get('lotacao')
    if not col_escola:
        return pd.DataFrame()

    ativos = df[df['VINCULO'] != 'APOSENTADO']
    t = ativos.groupby(col_escola).agg(
        qtd_servidores=('BRUTO', 'count'),
        total_bruto=('BRUTO', 'sum'),
        media_bruto=('BRUTO', 'mean')
    ).reset_index()
    t.columns = ['escola', 'qtd_servidores', 'total_bruto', 'media_bruto']
    t = t.sort_values('total_bruto', ascending=False).head(top_n)
    return t
```

### 6.2 Distribuição por tempo de serviço

```python
def gerar_tempo_servico(df, cols, data_ref=None):
    """Distribui servidores por faixa de tempo de serviço."""
    col_adm = cols.get('admissao')
    if not col_adm:
        return pd.DataFrame()

    if data_ref is None:
        data_ref = pd.Timestamp.now()

    ativos = df[df['VINCULO'] != 'APOSENTADO'].copy()
    ativos['dt_admissao'] = pd.to_datetime(ativos[col_adm], errors='coerce')
    ativos['anos_servico'] = (data_ref - ativos['dt_admissao']).dt.days / 365.25

    faixas = [
        (0, 5, '< 5 anos'),
        (5, 10, '5–10 anos'),
        (10, 20, '10–20 anos'),
        (20, 30, '20–30 anos'),
        (30, 99, '> 30 anos'),
    ]

    rows = []
    for inf, sup, label in faixas:
        mask = (ativos['anos_servico'] >= inf) & (ativos['anos_servico'] < sup)
        n = int(mask.sum())
        soma = float(ativos.loc[mask, 'BRUTO'].sum())
        media = float(ativos.loc[mask, 'BRUTO'].mean()) if n > 0 else 0
        rows.append({'faixa': label, 'qtd': n, 'total_bruto': soma, 'media_bruto': media})

    return pd.DataFrame(rows)
```

---

## 7. Gancho — Script Standalone para Educação

### 7.1 Argparse + fluxo principal

```python
#!/usr/bin/env python3
"""
processa_folha_educacao.py — Processa nova folha da Educação e atualiza dashboard.

Uso:
    python3 processa_folha_educacao.py folha_educacao_2026.csv [--competencia "Fev/2026"]
    python3 processa_folha_educacao.py folha.xlsx --formato xlsx [--aba Total]
"""
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Processa folha de educação')
    parser.add_argument('arquivo', help='CSV ou XLSX da folha')
    parser.add_argument('--competencia', default='2026', help='Competência (ex: Fev/2026)')
    parser.add_argument('--formato', choices=['csv', 'xlsx'], default='csv')
    parser.add_argument('--aba', default='Total', help='Aba do Excel (se xlsx)')
    parser.add_argument('--sem-api', action='store_true', help='Não chamar API Claude')
    args = parser.parse_args()

    # 1. Ler arquivo
    if args.formato == 'xlsx':
        df = pd.read_excel(args.arquivo, sheet_name=args.aba, engine='openpyxl')
    else:
        df = ler_folha_csv(args.arquivo)

    # 2. Processar (mesmas funções de generate_folha.py)
    # 3. Salvar tabelas em tabelas/educacao/folha/
    # 4. Chamar API Opus se --sem-api não for passado
    # 5. Printar resumo

if __name__ == '__main__':
    main()
```

---

## 8. Integração com build_html — Modificações

### 8.1 build_html_saude.py — Mudanças

1. **Importar** função `carregar_dados_folha()` de `generate_folha.py` (ou inline)
2. **Carregar** tabelas de `tabelas/saude/folha/`
3. **Adicionar** seção `#pessoal` ao HTML (entre `#fontes` e `#sintese`)
4. **Adicionar** link na nav sidebar: `<a href="#pessoal">Análise de Pessoal</a>`
5. **Adicionar** variáveis JS: `VINC_LABELS`, `FAIXA_LABELS`, `LOCAL_LABELS`, etc.
6. **Adicionar** charts: `chartVinculo`, `chartFaixas`, `chartLocais`, `chartRubricas`
7. **Mesclar** recomendações da folha com recomendações gerais (total: 4)
8. **Atualizar** prompt Opus da análise geral para incluir dados da folha no payload

### 8.2 build_html_educacao.py — Mudanças

1. **Substituir** a função `analisar_pessoal()` atual (básica) por carregamento das tabelas geradas
2. **Adicionar** charts específicos: `chartEscolas`, `chartTempoServico`
3. **Expandir** seção `#pessoal` com mais gráficos e tabelas
4. **Manter compatibilidade**: se `tabelas/educacao/folha/` não existir, usar fallback `educ-10-2025.xlsx` como hoje

### 8.3 Adição à nav sidebar

```html
<a href="#pessoal">Análise de Pessoal</a>  <!-- já existe no educação, ADICIONAR no saúde -->
```

---

## 9. Tratamento de Edge Cases

| Situação | Tratamento |
|----------|-----------|
| Folha não encontrada | Omitir seção `#pessoal` do HTML; logar aviso |
| API indisponível | Usar fallback com f-strings (§4.2) |
| Colunas com encoding corrompido | `norm_col()` normaliza acentos |
| Valores monetários em formato BR | `to_num()` converte antes de calcular |
| Educação sem folha 2026 | Manter `educ-10-2025.xlsx` como fallback |
| CSV com encoding misto | `encoding='latin-1', errors='replace'` |
| Campo Lotação com formatos variados | Regex flexível para extrair local |
| Divisão por zero em Gini/taxas | `replace(0, np.nan)` + fallback 0.0 |

---

## 10. Dependências

```
# Já instalados (do pipeline WOI):
pandas>=2.0
openpyxl>=3.1
pyarrow>=14.0
anthropic>=0.39

# Adicionais:
numpy>=1.24       # para Gini e outlier detection
matplotlib>=3.7   # para gráficos estáticos (opcional, só para debug)
```

```bash
pip install numpy --break-system-packages
```
