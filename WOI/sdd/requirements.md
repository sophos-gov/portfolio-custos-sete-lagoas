# Requirements — Relatório de Custos Municipais 2025 (Saúde e Educação)

## 1. Visão Geral do Projeto

Construir um pipeline automatizado em Python que:
1. Extrai e processa dados orçamentários do SICOM/TCE-MG de 2025 do município de Sete Lagoas (código 3167202)
2. Gera tabelas analíticas de composição, ranking e evolução **somente para o ano de 2025**
3. Classifica empenhos por categoria de custo usando a API do Claude
4. Produz dois relatórios HTML interativos no estilo McKinsey — um para Saúde, um para Educação

> **Escopo:** Apenas dados de 2025. Nenhum comparativo com anos anteriores é necessário.

---

## 2. Fonte dos Dados

### 2.1 Dados 2025 (CSVs dentro de ZIPs)
Pasta: `../../2025/` (relativo ao diretório `sdd/`)

| Arquivo ZIP | CSVs principais usados | Encoding |
|---|---|---|
| `SICOM.2025.3167202.despesa (2).zip` | `despesa.despesa.csv` (4.2 MB), `despesa.pagamento.csv` (28 MB), `despesa.liquidacao.csv` | latin-1 |
| `SICOM.2025.3167202.empenho (2).zip` | `empenho.empenho.csv` (11 MB), `empenho.credorEmpenho.csv` (1.5 MB) | latin-1 |
| `SICOM.2025.3167202.desp_pessoal.zip` | `desp_pessoal.despPessoal.csv` | latin-1 |
| `SICOM.2025.3167202.contrato.zip` | `contrato.contratos.csv` | latin-1 |

**Delimitador:** `;` (ponto-e-vírgula)
**Encoding:** `latin-1` (ISO-8859-1) — usar `errors='replace'` se houver caracteres problemáticos

### 2.2 Arquivo de Folha de Pagamento (Educação)
`../educ-10-2025.xlsx` — Folha de 10 meses de 2025, 4.021 servidores, 109 colunas.
Usado exclusivamente no relatório de Educação para análise de pessoal por escola e tipo de contrato.

### 2.3 Relatório de referência (leitura opcional)
`../../Relatório_Custos_educação_20251229.docx` — Relatório anterior que serve como referência de
estrutura analítica e contexto do município. **Não usar seus dados; apenas a estrutura narrativa.**

---

## 3. Filtros de Unidade Organizacional

### 3.1 SAÚDE
| Campo | Valor |
|---|---|
| `cod_unidade` | **13001** |
| `dsc_funcao` | `10 - SAÚDE` (consequência natural do filtro por unidade) |
| Programas esperados | 2076 (MAC), 2073 (Atenção Básica), 2077 (Vigilância), 2072 (Assist. Farmacêutica), 2074 (Gestão SUS), 2075 (Investimento SUS), 2051 (Gestão Adm.) |
| Registros despesa 2025 | ~3.430 |

### 3.2 EDUCAÇÃO
| Campo | Valor |
|---|---|
| `cod_unidade` | **11001** (Secretaria) + **22001** (Autarquia/FUNDEB, `seq_orgao` diferente) |
| `dsc_funcao` | `12 - EDUCAÇÃO` (consequência natural do filtro por unidade) |
| Programas esperados | 2084 (Universalização), 2085 (Educação), 2050 (Operações Especiais), 2051 (Gestão Adm.) |
| Registros despesa 2025 | ~1.848 (soma das duas unidades) |

**Nota:** Registros com `dsc_funcao = 09 - PREVIDÊNCIA SOCIAL` devem ser **incluídos** quando `cod_unidade` pertencer à secretaria — correspondem aos inativos e pensionistas de cada secretaria.

**Normalização obrigatória:** `cod_unidade` pode ser `int` ou `str` nos CSVs → converter com `.astype(str).str.strip()` antes de filtrar.

---

## 4. Estrutura dos CSVs Principais

### 4.1 `despesa.despesa.csv` — visão orçamentária agregada
```
seq_orgao; cod_municipio; cod_orgao; seq_unidade; cod_unidade; cod_subunidade;
num_anoexercicio; num_mesexercicio; dsc_funcao; dsc_subfuncao; dsc_programa;
dsc_acao; dsc_subacao; dsc_naturezadespesa; dsc_fonterecurso; dsc_cod_orcamentario;
vlr_previsto; vlr_acrescimo; vlr_deducao; vlr_empenhado; vlr_liquidado; vlr_pago;
vlr_rspprocessado; vlr_rspnprocessado
```
**Uso:** Análises de composição por programa, ação, natureza, fonte e evolução mensal.
**Importante:** Esta tabela **não tem `seq_empenho`** — é uma visão agregada por dotação.

### 4.2 `empenho.empenho.csv` — detalhe de cada compromisso
```
seq_empenho; cod_municipio; seq_orgao; cod_orgao; seq_unidade; cod_unidade;
cod_subunidade; num_anoexercicio; num_mesexercicio; num_empenho; dat_empenho;
dsc_modalidade; dsc_tipo_empenho; dsc_empenho; ...;
dsc_funcao; dsc_subfuncao; dsc_programa; dsc_acao; dsc_subacao;
dsc_naturezadespesa; vlr_empenhado; vlr_reforco; vlr_anulempenho
```
**Uso:** Classificação por categoria via `dsc_empenho` (texto livre). O `seq_empenho` é a FK para pagamento e credorEmpenho.

### 4.3 `despesa.pagamento.csv` — pagamentos efetivos
```
seq_pagamento; seq_orgao; cod_orgao; seq_unidade; seq_empenho; ...;
nom_credor; dat_pagamento; dsc_pagamento; dsc_tipo_pagamento; dsc_fonte_recurso;
vlr_pag_fonte; vlr_ret_fonte; vlr_ant_fonte; vlr_anu_fonte
```
**Uso:** Ranking de fornecedores e curva de concentração. O `vlr_pag_fonte` é o valor efetivamente pago.

### 4.4 `empenho.credorEmpenho.csv` — credor por empenho
```
seq_emp_credor; seq_empenho; seq_orgao; cod_orgao; seq_unidade;
num_ano_referencia; num_mes_referencia; num_doc_credor; nom_credor
```
**Uso:** Complementa `nom_credor` quando ausente no pagamento; traz `num_doc_credor` (CNPJ/CPF).

---

## 5. Fluxos de Dados (Joins)

As tabelas têm propósitos distintos e **não se cruzam todas entre si**:

```
FLUXO 1 — Composição orçamentária (sem join):
  despesa.despesa → filtrar por cod_unidade → agrupar por programa / natureza / ação / fonte / mês

FLUXO 2 — Classificação de empenhos (sem join com despesa):
  empenho.empenho → filtrar por cod_unidade → classificar dsc_empenho → agrupar por categoria

FLUXO 3 — Ranking de fornecedores:
  despesa.pagamento → filtrar por cod_unidade → agrupar por nom_credor → top 20 + Pareto
  (join opcional com credorEmpenho para obter CNPJ quando nom_credor vier vazio)
```

**Chave de ligação empenho ↔ pagamento:** `seq_empenho`
**Chave de filtro por secretaria:** `cod_unidade` (presente em todas as tabelas)

---

## 6. Análises Requeridas (2025 Standalone)

| # | Análise | Fonte | Granularidade | Output |
|---|---|---|---|---|
| A1 | **Composição por programa** — quanto cada programa representa do total | despesa.despesa | programa × vlr_pago | ranking + % do total |
| A2 | **Composição por natureza de despesa** — pessoal, material, serviços etc. | despesa.despesa | natureza × vlr_pago | ranking + % |
| A3 | **Composição por ação** — cada atividade/serviço | despesa.despesa | ação × vlr_pago | ranking + % |
| A4 | **Top 20 fornecedores** — por valor pago | pagamento | credor × total_pago × nº empenhos | ranking |
| A5 | **Concentração de fornecedores** — Pareto | pagamento | % acumulado | curva Pareto |
| A6 | **Classificação por categoria de custo** — via regras + API Claude | empenho | categoria × vlr_empenhado | composição |
| A7 | **Evolução mensal** — gastos mês a mês em 2025 | despesa.despesa | mês × vlr_pago | série temporal |
| A8 | **Fontes de recurso** — recursos próprios vs. SUS / FUNDEB | despesa.despesa | fonte × vlr_pago | composição |

---

## 7. Classificação de Empenhos (Análise A6)

O campo `dsc_empenho` é texto livre descrevendo o objeto do gasto. Exemplos reais:
- `"AQUISIÇÃO DE MEDICAMENTOS PARA ATENÇÃO BÁSICA"`
- `"PRESTAÇÃO DE SERVIÇOS DE LIMPEZA E CONSERVAÇÃO"`
- `"PAGAMENTO DE FOLHA COMPLEMENTAR COMPETÊNCIA 03/2025"`

**14 categorias de destino:**

| # | Categoria |
|---|---|
| 1 | Pessoal (salários, encargos, gratificações) |
| 2 | Medicamentos e insumos de saúde |
| 3 | Material hospitalar e equipamentos |
| 4 | Alimentação e nutrição |
| 5 | Limpeza e conservação |
| 6 | Manutenção predial e de equipamentos |
| 7 | Transporte (escolar, ambulâncias, frota) |
| 8 | Tecnologia e informática |
| 9 | Serviços terceirizados (assessoria, consultoria) |
| 10 | Material de expediente e pedagógico |
| 11 | Investimentos (obras, aquisição bens permanentes) |
| 12 | Previdência e aposentadoria |
| 13 | Transferências e subvenções |
| 14 | Outros |

**Estratégia em duas camadas:**
1. **Regras determinísticas** (~70%): `dsc_naturezadespesa` e `dsc_acao` já classificam a maioria
2. **API Claude** (~30%): apenas para empenhos ambíguos não cobertos pelas regras

### Prompt de classificação (API Claude)
```
Você é um classificador de empenhos públicos municipais brasileiros.

Classifique cada empenho abaixo em UMA das categorias:
1. Pessoal  2. Medicamentos  3. Material hospitalar  4. Alimentação
5. Limpeza  6. Manutenção  7. Transporte  8. TI  9. Serviços terceirizados
10. Material expediente/pedagógico  11. Investimentos  12. Previdência
13. Transferências  14. Outros

Use os campos dsc_empenho, dsc_naturezadespesa e dsc_acao como contexto.

Responda APENAS com um JSON array no formato:
[{"seq_empenho": "X", "categoria": N}, ...]

Empenhos:
{batch_json}
```

**Configuração da API:**
- Modelo: `claude-sonnet-4-20250514`
- Temperatura: `0` (determinístico)
- Max tokens: `4096`
- Lote: 50 empenhos por chamada
- Custo estimado: ~$0.12 para todo o projeto

---

## 8. Requisitos do Output HTML

### 8.1 Princípios McKinsey (obrigatórios)

1. **Action title em todo gráfico** — afirmação com número + "so what". Nunca rótulo genérico.
   - ❌ Ruim: "Despesas por programa"
   - ✅ Bom: "MAC concentra 68% do orçamento da Saúde, respondendo por R$ X em 2025"
2. **Horizontal flow** — ler só os action titles em sequência conta a história completa
3. **Vertical flow** — cada gráfico prova exatamente o que o action title afirma
4. **Anotações contextuais** nos gráficos: labels de pico, destaque do maior item, % do total
5. **Headlines** seguem a fórmula: `[Número específico] + [Impacto/Contexto] + [Ação implícita]`

### 8.2 Seções de cada relatório HTML

```
1. HERO SECTION
   - Título: "Custos da [Saúde / Educação] — Sete Lagoas 2025"
   - Action title geral: frase-síntese com o principal insight
   - 4 cards KPI: Total Pago, Total Empenhado, Nº Fornecedores, Nº Empenhos
   - Indicador de período coberto (ex: "Jan–Out 2025 · 10 meses")

2. COMPOSIÇÃO POR PROGRAMA
   - Action title: ex. "MAC domina 68% dos gastos da Saúde, seguido por Atenção Básica com 21%"
   - Bar chart horizontal ordenado por valor
   - Tabela: programa | valor pago | % do total | nº empenhos

3. DESPESA POR NATUREZA
   - Action title: ex. "Pessoal responde por 55% dos custos; materiais e serviços dividem os 45% restantes"
   - Doughnut chart com as naturezas agrupadas em categorias macro
   - Tabela detalhada com heatmap de participação

4. DESPESA POR AÇÃO/ATIVIDADE
   - Action title: variável conforme os dados
   - Lollipop chart horizontal (top 15 ações por valor)
   - Percentual de cada ação sobre o total

5. TOP FORNECEDORES
   - Action title: ex. "Os 10 maiores fornecedores absorvem X% do orçamento total"
   - Lollipop chart dos top 20 por valor pago
   - Curva de Pareto (% acumulado)

6. CLASSIFICAÇÃO POR CATEGORIA DE CUSTO
   - Action title: ex. "Medicamentos e limpeza somam X% dos custos não-pessoais da Saúde"
   - Doughnut chart por categoria
   - Tabela heatmap: categoria × mês (qual mês cada categoria pesou mais)

7. EVOLUÇÃO MENSAL
   - Action title: ex. "Pico de gastos em [mês] com R$ X — Y% acima da média mensal de R$ Z"
   - Line chart mês a mês (Jan–mês mais recente disponível)
   - Anotação no pico e no vale
   - Linha de média com label

8. FONTES DE RECURSO
   - Action title: ex. "Recursos próprios financiam X%; SUS/FUNDEB complementam com Y%"
   - Stacked bar ou treemap por fonte

9. RECOMENDAÇÕES
   - 3 a 5 cards gerados via API Claude
   - Estrutura de cada card: Insight (dado) → Implicação → Ação sugerida
```

### 8.3 Stack técnica

| Componente | Solução |
|---|---|
| Charts | Chart.js v4 via CDN `cdn.jsdelivr.net/npm/chart.js` |
| Layout | CSS Grid + variáveis CSS nativas (sem frameworks externos) |
| Tipografia | `system-ui, -apple-system, "Segoe UI"` (funciona offline) |
| Dados | JSON inline no `<script>` do HTML |
| Interatividade | Tooltips nativos do Chart.js, scroll suave entre seções |

**Paleta institucional:**
```css
--azul-escuro:  #1B3A5C;   /* títulos, destaques */
--azul-medio:   #2E86AB;   /* ação principal, links */
--azul-claro:   #A3CEF1;   /* barras secundárias */
--verde:        #28A745;   /* positivo, crescimento */
--vermelho:     #E63946;   /* alerta, concentração */
--amarelo:      #F4A261;   /* anotações contextuais */
--cinza-escuro: #343A40;
--fundo:        #F8F9FA;
```

### 8.4 Requisitos não-funcionais

- HTML **standalone** — funciona sem servidor, abre direto no browser
- Tamanho final **< 2 MB** por arquivo
- Compatível com **Chrome, Edge, Firefox** (últimas 2 versões)
- **Responsivo** — cards empilham e charts redimensionam em mobile (breakpoints: 768px, 1200px)

---

## 9. Entregáveis Finais

| # | Arquivo | Localização |
|---|---|---|
| 1 | `extract_data.py` | `../output/` |
| 2 | `classify_empenhos.py` | `../output/` |
| 3 | `generate_tables.py` | `../output/` |
| 4 | `build_html_saude.py` | `../output/` |
| 5 | `build_html_educacao.py` | `../output/` |
| 6 | `relatorio_custos_saude_2025.html` | `../output/` |
| 7 | `relatorio_custos_educacao_2025.html` | `../output/` |
| 8 | `tabelas/saude/` e `tabelas/educacao/` | `../output/tabelas/` |
| 9 | `run_all.sh` | `../output/` |
