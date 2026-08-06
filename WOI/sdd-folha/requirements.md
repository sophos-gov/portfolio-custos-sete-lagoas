# Requirements — Integração da Folha de Pagamento nos Dashboards de Custos

## 1. Visão Geral

Estender os dois relatórios HTML de custos (Saúde e Educação) com uma seção robusta de **Análise de Folha de Pagamento**, incluindo:

1. **Saúde:** processar `2026-02.csv` (Fev/2026, ~950 servidores) e incorporar no dashboard WOI
2. **Educação:** aprimorar a seção de pessoal existente (hoje usa `educ-10-2025.xlsx`) e deixar gancho para incorporar folha 2026 quando disponível
3. **Análise via API Claude Opus:** gerar narrativa analítica cruzando dados da folha com custos orçamentários
4. **Gancho Educação:** script Python + prompt para Claude Code processar folha nova de 2026

> **Abordagem SDD:** este documento é a spec; `design.md` detalha arquitetura e código; `tasks.md` detalha implementação para o Claude Code.

---

## 2. Fontes de Dados

### 2.1 Folha da Saúde — `2026-02.csv`

**Caminho relativo (de `output/`):** `../../../saude7l/Folha 11-2025 e exporta arquivo/2026-02.csv`
**Caminho absoluto no projeto:** `projetos/saude7l/Folha 11-2025 e exporta arquivo/2026-02.csv`
**Formato:** CSV, separador `;`, encoding `latin-1`
**Registros:** ~950 servidores
**Colunas-chave:**

| Coluna | Descrição |
|--------|-----------|
| `Matrícula` | Identificador único do servidor |
| `Nome` | Nome completo |
| `Lotação` | Unidade + tipo de vínculo (ex: `"49 - 050000 - HOSPITAL MUNICIPAL - CONTRATO"`) |
| `Cargo` | Código + nome do cargo (ex: `"127 - ENFERMEIRO"`) |
| `Função` | Função exercida (pode ser vazia) |
| `Cód. Padrão` | Grade salarial (S1-S9 para comissionados, 141-162 para efetivos) |
| `Descrição Padrão` | Nome da grade |
| `Valor_XXXX` | Rubricas de proventos (ex: `Valor_0001`, `Valor_0051`) |
| `Valor_RYYY` | Rubricas de descontos (ex: `Valor_R007`, `Valor_R997`) |
| `Proventos` | Total bruto |
| `Descontos` | Total descontos |
| `Liquido` | Salário líquido |
| `Tipo Contrato` | `"SERV.PUBL. EFETIVO"`, `"SERV.PUBL. CARGO TEMPORARIO"`, `"APOSENTADO"`, etc. |
| `Admissao` | Data de admissão (YYYY-MM-DD) |

**Classificação de vínculos (via campo `Lotação`):**
```
EFETIVO:      Lotação contém 'EFETIV'
COMISSIONADO: Lotação contém 'COMISSION'
APOSENTADO:   Lotação contém 'APOSENTAD' ou 'PENSIONIST'
CONTRATO:     Lotação contém 'CONTRATO'
OUTROS:       demais
```

### 2.2 Folha da Educação — `educ-10-2025.xlsx`

**Caminho:** `../educ-10-2025.xlsx`
**Formato:** Excel, aba `Total`, 4.021 linhas × 109 colunas
**Colunas relevantes:** `Local de trabalho` (escola real), `Cargo`, `Tipo Contrato`, `Proventos`, `Líquido`
**Período:** 10 meses de 2025 (Jan–Out)

### 2.3 Folha futura da Educação (gancho)

**Formato esperado:** CSV com separador `;`, encoding `latin-1` — mesmo layout da folha da Saúde
**Quando chegar:** o script `processa_folha_educacao.py` deve processá-la e atualizar o dashboard

### 2.4 Dados de custo já existentes (WOI)

Os dashboards já possuem análises orçamentárias completas. A integração da folha deve **cruzar** com:

| Dado WOI | Cruzamento |
|----------|-----------|
| `composicao_categorias.csv` → categoria "Pessoal" | Comparar vlr_empenhado com total da folha |
| `composicao_natureza.csv` → "Pessoal e Encargos" | Validar % de pessoal nos custos |
| `serie_mensal.csv` | Contextualizar custo mensal da folha vs. despesa total |
| `kpis.json` → `total_pago` | Calcular % da folha sobre o gasto total |

---

## 3. Análises Requeridas — Folha da Saúde

### 3.1 Indicadores-chave (KPIs de folha)

| KPI | Cálculo |
|-----|---------|
| Total de servidores ativos | Excluir aposentados/pensionistas |
| Total da folha bruta mensal | Soma de `Proventos` dos ativos |
| Total da folha líquida | Soma de `Liquido` dos ativos |
| Média salarial bruta | `total_bruto / qtd_ativos` |
| Mediana salarial bruta | `mediana(Proventos)` dos ativos |
| Índice de Gini | Curva de Lorenz sobre proventos |
| Taxa média de desconto | `total_descontos / total_bruto * 100` |
| Custo mensal da folha / despesa total | `total_bruto / kpis.total_pago * 12` (anualizado) |

### 3.2 Distribuição por tipo de vínculo

**Tabela:** `por_vinculo.csv`

| Coluna | Descrição |
|--------|-----------|
| `vinculo` | EFETIVO, COMISSIONADO, CONTRATO, APOSENTADO, OUTROS |
| `qtd_servidores` | Contagem |
| `total_bruto` | Soma de Proventos |
| `media_bruto` | Média |
| `mediana_bruto` | Mediana |
| `pct_folha` | % do total da folha |

### 3.3 Distribuição por faixa salarial

**Tabela:** `distribuicao_faixas.csv`

| Faixa | Descrição |
|-------|-----------|
| Até R$ 2.000 | Contratos iniciais |
| R$ 2.001–3.500 | Base |
| R$ 3.501–5.500 | Intermediário |
| R$ 5.501–8.000 | Sênior |
| R$ 8.001–12.000 | Especialista |
| R$ 12.001–20.000 | Chefia/Médico |
| Acima de R$ 20.000 | Elite |

### 3.4 Top locais de lotação por custo

**Tabela:** `top_locais.csv` — Top 15 unidades por custo total de pessoal

| Coluna | Descrição |
|--------|-----------|
| `local` | Nome da unidade (extraído de `Lotação`) |
| `qtd_servidores` | Contagem |
| `total_bruto` | Soma de Proventos |
| `media_bruto` | Média por servidor |
| `pct_folha` | % do total |

### 3.5 Top cargos por custo

**Tabela:** `top_cargos.csv` — Top 15 cargos

Mesma estrutura da 3.4, agrupado por `Cargo`.

### 3.6 Zona de elite e alertas

**Tabela:** `alertas_folha.csv`

| Alerta | Regra |
|--------|-------|
| `elite_acima_20k` | Proventos > R$ 20.000 |
| `desconto_acima_50pct` | Taxa desconto > 50% |
| `outlier_cargo` | Provento > Q3 + 1.5×IQR para o cargo |
| `efetivo_com_funcao_comissionada` | Efetivo exercendo função de comissionado |

### 3.7 Análise de rubricas dominantes

**Tabela:** `rubricas_top.csv` — Top 20 rubricas por valor total

| Coluna | Descrição |
|--------|-----------|
| `rubrica` | Código (ex: 0001) |
| `tipo` | provento ou desconto |
| `total` | Soma de todos os servidores |
| `pct_folha` | % sobre total da folha |
| `qtd_servidores` | Quantos recebem esta rubrica |

### 3.8 Cruzamento com dados WOI (CRÍTICO)

Análise que conecta folha de pagamento com dados orçamentários:

| Cruzamento | Descrição |
|------------|-----------|
| **Folha vs. Categoria "Pessoal"** | Total bruto mensal × 12 vs. `composicao_categorias['Pessoal']` — são compatíveis? |
| **Folha vs. Natureza "3.1"** | Total bruto anualizado vs. natureza "Pessoal e Encargos" |
| **% da folha no gasto total** | Total bruto anualizado / `kpis.total_pago` — meta: ~55-65% para saúde |
| **Custo médio × nº servidores** | Projetar impacto de cada nova contratação |
| **Concentração salarial vs. concentração de fornecedores** | Comparar Gini da folha com Pareto de fornecedores |

---

## 4. Análises Requeridas — Folha da Educação

Mesmas análises da Saúde (§3.1 a §3.8) adaptadas, **com adições específicas**:

### 4.1 Análise por escola

Referência: Relatório de Custos da Educação (Dez/2025), Tabelas 15 e 16.

**Tabela:** `custo_por_escola.csv`

| Coluna | Descrição |
|--------|-----------|
| `escola` | Nome da escola (campo `Local de trabalho`) |
| `qtd_servidores` | Total de servidores lotados |
| `total_bruto` | Soma de proventos |
| `media_bruto` | Média salarial |
| `custo_por_aluno` | `total_bruto / matriculas` (se matrícula disponível) |

### 4.2 Distribuição por tempo de serviço

Referência: Relatório de Custos da Educação, Tabela 18.

**Tabela:** `distribuicao_tempo_servico.csv`

| Faixa | Descrição |
|-------|-----------|
| < 5 anos | Recém-contratados |
| 5–10 anos | Inicial |
| 10–20 anos | Intermediário |
| 20–30 anos | Sênior |
| > 30 anos | Próximo à aposentadoria |

Calcular a partir de `Admissao`: `anos_servico = (data_ref - Admissao).days / 365.25`

### 4.3 Análise de gratificações

Referência: Relatório de Custos da Educação, seção sobre gratificações.

Identificar rubricas que representam gratificações (códigos 0051, 0053, 0054, 0057, etc.) e quantificar:
- Total gasto em gratificações
- % da folha representado por gratificações
- Distribuição por tipo de gratificação

---

## 5. Seção HTML — "Análise de Pessoal"

### 5.1 Posição no dashboard

Inserir entre "Fontes de Recurso" e "Síntese Analítica":
```
...
#fontes     → Seção 8 — Fontes de Recurso
#pessoal    → Seção 9 — Análise de Pessoal (NOVA para Saúde / APRIMORADA para Educação)
#sintese    → Síntese Analítica
#recomendacoes → Recomendações
```

### 5.2 Conteúdo da seção (ambas secretarias)

```
1. Action title gerado via API Opus (ex: "Folha de R$ 6,4M concentra 63% do orçamento;
   42 servidores acima de R$ 20k representam 18% do custo total")

2. KPI cards (4):
   - Total Servidores | Total Folha | Média Salarial | Gini

3. Chart: Distribuição por vínculo (doughnut)
4. Chart: Distribuição por faixa salarial (bar horizontal)
5. Tabela: Tipos de vínculo (servidores, custo, %, média)

6. Chart: Top 10 locais por custo (bar horizontal)
7. Tabela: Top 10 locais

8. Chart: Top rubricas (bar horizontal)

9. Mini-seção "Cruzamento com Custos":
   - Cards comparando folha vs. categorias WOI
   - Gráfico: folha mensal vs. despesa total mensal (dual axis)

10. Alertas (cards vermelhos): elite, outliers, anomalias
```

### 5.3 Educação — adições específicas

```
11. Chart: Top 10 escolas por custo de pessoal (bar horizontal)
12. Chart: Distribuição por tempo de serviço (bar)
13. Tabela: Gratificações por tipo
```

---

## 6. Análise via API Claude Opus

### 6.1 Prompt para folha

Uma chamada Opus com dados consolidados da folha + dados WOI, retornando:

```json
{
  "action_title_pessoal": "...",
  "analise_folha": "Parágrafo 4-5 frases...",
  "cruzamento_custos": "Parágrafo 3-4 frases conectando folha com dados orçamentários...",
  "alertas_folha": ["alerta 1", "alerta 2", "alerta 3"],
  "recomendacoes_folha": [
    {"insight": "...", "implicacao": "...", "acao": "..."},
    {"insight": "...", "implicacao": "...", "acao": "..."}
  ]
}
```

### 6.2 Integração com recomendações gerais

As `recomendacoes_folha` devem ser **mescladas** com as recomendações gerais do dashboard, mantendo 4 recomendações no total (priorizando as baseadas em dados mais concretos).

### 6.3 Fallback sem API

Se `ANTHROPIC_API_KEY` não estiver definida:
- Action title: f-string com dados reais interpolados
- Análise: template padrão com métricas calculadas
- Alertas: gerados por regras simples (thresholds)
- Recomendações: baseadas em padrões detectados nos dados

---

## 7. Gancho — Educação 2026

### 7.1 Script: `processa_folha_educacao.py`

```bash
python3 processa_folha_educacao.py folha_educacao_2026.csv
```

O script deve:
1. Ler o CSV no formato padrão de folha (`;`, `latin-1`)
2. Gerar todas as tabelas da seção 4 (§3.1 a §3.8 + §4.1 a §4.3)
3. Salvar em `tabelas/educacao/folha/`
4. Opcionalmente chamar API Opus para narrativa
5. Printar resumo no console

### 7.2 Prompt para Claude Code

Documento `PROMPT_INCORPORAR_FOLHA_EDUCACAO.md` com instruções completas para o Claude Code:
1. Rodar o script de processamento
2. Atualizar `build_html_educacao.py` se necessário
3. Regenerar o HTML
4. Validar visualmente

---

## 8. Requisitos Não-Funcionais

| Requisito | Especificação |
|-----------|--------------|
| HTML standalone | Funciona sem servidor; abre direto no browser |
| Tamanho | < 2.5 MB por arquivo (tolerância extra pela seção de folha) |
| Dados inline | JSON embutido no `<script>` |
| Charts | Chart.js v4 via CDN |
| Estilo | McKinsey — action titles, cores institucionais, paleta existente |
| API Claude | Opus para análise narrativa; fallback sem API |
| Encoding CSV | `latin-1` com `errors='replace'` |
| Valores BR | `"1.234,56"` → `1234.56` antes de qualquer cálculo |
