# Tasks — Relatório de Custos Municipais 2025 (Saúde e Educação)

## Contexto para o Claude Code

Pipeline Python que processa dados SICOM/TCE-MG de 2025 do município de Sete Lagoas (3167202)
e gera dois relatórios HTML interativos no estilo McKinsey — um para Saúde, um para Educação.
**Escopo exclusivo: 2025 standalone. Nenhum comparativo com anos anteriores.**

**LEIA ANTES DE COMEÇAR:**
- `requirements.md` — requisitos, filtros, análises, spec do HTML
- `design.md` — arquitetura, código de referência, CSS/JS, edge cases

**Caminhos (relativos ao diretório `sdd/`):**
```
../../2025/          → ZIPs com CSVs de 2025
../educ-10-2025.xlsx → Folha de pagamento Educação
../output/           → Todos os scripts e outputs gerados
../output/tabelas/   → Parquets e CSVs intermediários
```

---

## TASK 1 — extract_data.py

**Objetivo:** Descompactar ZIPs, ler CSVs, filtrar por secretaria, salvar Parquets.

### 1.1 Setup
- [ ] Criar pastas: `../output/`, `../output/tabelas/saude/`, `../output/tabelas/educacao/`
- [ ] Instalar: `pip install pandas openpyxl pyarrow anthropic --break-system-packages`
- [ ] Criar o script em `../output/extract_data.py`

### 1.2 Descompactar ZIPs
- [ ] Descompactar os 4 ZIPs de `../../2025/` para `/tmp/sicom_2025/`
- [ ] Verificar existência dos 4 CSVs principais:
  - `2025.3167202.despesa.despesa.csv`
  - `2025.3167202.empenho.empenho.csv`
  - `2025.3167202.despesa.pagamento.csv`
  - `2025.3167202.empenho.credorEmpenho.csv`

### 1.3 Ler e normalizar CSVs
- [ ] `pd.read_csv(path, sep=';', encoding='latin-1', errors='replace')`
- [ ] Converter todos os campos `vlr_*` com a função `parse_valor_br()` do design.md §2.3
- [ ] Converter `cod_unidade` para string: `.astype(str).str.strip()`
- [ ] Converter `num_mesexercicio` para int
- [ ] Printar: shape e colunas de cada DataFrame lido

### 1.4 Filtrar por secretaria
Aplicar em `despesa.despesa`, `empenho.empenho`, `pagamento` e `credorEmpenho`:
- [ ] **SAÚDE:** `df[df['cod_unidade'] == '13001']`
- [ ] **EDUCAÇÃO:** `df[df['cod_unidade'].isin(['11001', '22001'])]`
- [ ] Incluir previdência (funcao 09) quando cod_unidade pertencer à secretaria (já incluído no filtro)
- [ ] NÃO filtrar por programa — programas são consequência do filtro por unidade
- [ ] Printar contagem: esperado ~3.430 despesas para Saúde, ~1.848 para Educação

### 1.5 Salvar intermediários
- [ ] Parquets em `../output/tabelas/{saude|educacao}/`:
  - `despesa_2025.parquet`
  - `empenho_2025.parquet`
  - `pagamento_2025.parquet`
  - `credorEmpenho_2025.parquet`
- [ ] Gerar `../output/tabelas/extraction_log.txt` com: contagem de linhas, meses cobertos, programas encontrados

### ✅ Critérios de aceite:
- Todos os Parquets existem e carregam sem erro
- Saúde: ~3.430 linhas em despesa; Educação: ~1.848
- Nenhum campo `vlr_*` contém strings
- Log gerado

---

## TASK 2 — classify_empenhos.py

**Objetivo:** Classificar cada empenho em uma das 14 categorias de custo.

### 2.1 Carregar empenhos
- [ ] Ler `empenho_2025.parquet` de Saúde e Educação
- [ ] Adicionar coluna `secretaria` ('saude' ou 'educacao')
- [ ] Concatenar em DataFrame único

### 2.2 Classificação por regras (Camada 1)
- [ ] Implementar `REGRAS_NATUREZA` e `REGRAS_ACAO` conforme design.md §3.1
- [ ] Aplicar `classificar_por_regras(row)` — match por prefixo, natureza tem prioridade
- [ ] Marcar classificados como `origem='regra'`
- [ ] Printar: total classificados por regra (meta: ≥ 65%)

### 2.3 Classificação via API Claude (Camada 2)
- [ ] Verificar `ANTHROPIC_API_KEY` no environment:
  - Se não existir: classificar restantes como categoria 14 (Outros), logar aviso
  - Se existir: executar classificação em lotes de 50 conforme design.md §3.2
- [ ] Usar cache incremental em `../output/tabelas/classificacao_cache.csv`
- [ ] Retry com backoff exponencial (3 tentativas por lote)
- [ ] Logar erros em `../output/tabelas/classificacao_erros.log`
- [ ] Marcar como `origem='api'`

### 2.4 Consolidar e salvar
- [ ] Garantir 100% dos empenhos com categoria atribuída (fallback: 14)
- [ ] Salvar `empenho_classificado.parquet` em cada pasta de secretaria
- [ ] Printar distribuição: contagem e % por categoria × secretaria

### ✅ Critérios de aceite:
- Zero empenhos sem categoria
- Cache funciona: rodar 2× não dispara chamadas duplicadas à API
- Pessoal é a categoria dominante em ambas as secretarias

---

## TASK 3 — generate_tables.py

**Objetivo:** Gerar todas as tabelas analíticas em CSV/JSON para uso nos HTMLs.

### 3.1 Composição por programa (A1)
- [ ] `despesa_2025` agrupada por `dsc_programa`: somar `vlr_pago`, `vlr_empenhado`, `vlr_previsto`
- [ ] Calcular `pct_total` e ordenar decrescente
- [ ] Salvar: `composicao_programa.csv`

### 3.2 Composição por natureza macro (A2)
- [ ] Aplicar `categorizar_natureza()` do design.md §4.2 em `dsc_naturezadespesa`
- [ ] Agrupar por macro-categoria, somar `vlr_pago`, calcular `pct_total`
- [ ] Salvar: `composicao_natureza.csv`

### 3.3 Composição por ação (A3)
- [ ] Agrupar por `dsc_acao`, somar `vlr_pago`, calcular `pct_total`
- [ ] Ordenar decrescente, manter top 20
- [ ] Salvar: `composicao_acao.csv`

### 3.4 Ranking de fornecedores + Pareto (A4 e A5)
- [ ] Usar `pagamento_2025`: agrupar por `nom_credor` → `total_pago`, `qtd_pagamentos`, `qtd_empenhos`
- [ ] Calcular `pct_total` e `pct_acumulado` (Pareto)
- [ ] Salvar: `ranking_fornecedores.csv` (top 20)
- [ ] Salvar: `concentracao.json` com `{'pct_top5': X, 'pct_top10': Y, 'pct_top20': Z}`

### 3.5 Composição por categoria (A6)
- [ ] Usar `empenho_classificado`: agrupar por `categoria_custo`, somar `vlr_empenhado`
- [ ] Calcular `pct_total`
- [ ] Variante mensal: `categoria × num_mesexercicio` → `composicao_categorias_mensal.csv`
- [ ] Salvar: `composicao_categorias.csv`

### 3.6 Série temporal mensal (A7)
- [ ] Agrupar `despesa_2025` por `num_mesexercicio`, somar `vlr_pago`
- [ ] Adicionar `media_mensal`, identificar `mes_pico` e `mes_vale`
- [ ] Salvar: `serie_mensal.csv`

### 3.7 Fontes de recurso (A8)
- [ ] Agrupar por `dsc_fonterecurso`, somar `vlr_pago`, calcular `pct_total`
- [ ] Simplificar nomes longos (ex: `"1.500.000 - RECURSOS NÃO VINCULADOS..."` → `"Recursos Próprios"`)
- [ ] Salvar: `fontes_recurso.csv`

### 3.8 KPIs JSON
- [ ] Gerar `kpis.json` para cada secretaria conforme design.md §4.5:
  - `total_pago`, `total_empenhado`, `total_previsto`
  - `num_fornecedores`, `num_empenhos`
  - `meses_cobertos`, `periodo`
  - `mes_pico`, `valor_pico`, `media_mensal`
  - `programa_top`

### ✅ Critérios de aceite:
- Todos os 8 CSVs + 2 JSONs gerados para cada secretaria (16 + 4 arquivos no total)
- Total por programa = total geral (soma bate)
- Nenhum CSV vazio

---

## TASK 4 — build_html_saude.py

**Objetivo:** Montar o relatório HTML da Saúde com charts, action titles e recomendações.

### 4.1 Carregar dados
- [ ] Ler todos os CSVs e JSONs de `../output/tabelas/saude/`
- [ ] Serializar para dicts Python (para embutir como JSON inline no HTML)
- [ ] Formatar valores: `R$ X,XM` para labels; `float` puro para chart data

### 4.2 Gerar action titles via API Claude
- [ ] Usar `gerar_action_title()` do design.md §5.1 para cada seção
- [ ] Passar dados resumidos (top 3 programas, total, etc.) como contexto
- [ ] Se API indisponível: usar templates com f-strings interpolando os dados reais
- [ ] Gerar 8 action titles (um por seção)

### 4.3 Gerar recomendações via API Claude
- [ ] Usar `gerar_recomendacoes()` do design.md §5.2
- [ ] Passar kpis, top programas e top fornecedores como contexto
- [ ] Gerar 4 cards (insight + implicação + ação)
- [ ] Se API indisponível: gerar recomendações genéricas baseadas nos dados (hardcoded com f-strings)

### 4.4 Montar HTML
Usar template do design.md §5.5. Incluir estas seções na ordem:

- [ ] **`#hero`** — título, action title geral, 4 cards KPI, indicador de período
- [ ] **`#programas`** — action title + bar horizontal + tabela (programa | R$ | % | nº empenhos)
- [ ] **`#natureza`** — action title + doughnut macro-categorias + tabela detalhada
- [ ] **`#acoes`** — action title + lollipop top 15 ações
- [ ] **`#fornecedores`** — action title + lollipop top 20 + curva Pareto (Chart.js line com eixo Y secundário %)
- [ ] **`#categorias`** — action title + doughnut categorias + tabela heatmap (categoria × mês)
- [ ] **`#mensal`** — action title + line chart + anotação do pico + linha de média (dataset separado)
- [ ] **`#fontes`** — action title + bar horizontal ou doughnut
- [ ] **`#recomendacoes`** — grid de cards (rec-grid / rec-card conforme CSS)

### 4.5 CSS e JavaScript inline
- [ ] Embutir CSS completo do design.md §5.3
- [ ] CDN Chart.js: `<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>`
- [ ] Embutir dados: `<script>const DATA = {json_inline};</script>`
- [ ] Inicializar todos os charts com configurações do design.md §5.4
- [ ] Adicionar listener para highlight de nav item ativo no scroll
- [ ] Formatação de tooltip em BRL em todos os charts

### 4.6 Salvar e validar
- [ ] Salvar: `../output/relatorio_custos_saude_2025.html`
- [ ] Verificar tamanho < 2MB
- [ ] Abrir com `python3 -m http.server` e checar console do browser (zero erros JS)

### ✅ Critérios de aceite:
- Todos os charts renderizam sem erro no console
- Action titles contêm números e "so what"
- Cards KPI mostram valores corretos e formatados em BRL
- Nav lateral funciona
- Responsivo em 375px (mobile)

---

## TASK 5 — build_html_educacao.py

**Objetivo:** Relatório HTML da Educação — mesmo padrão da Task 4, com seção adicional de pessoal.

### 5.1 Base idêntica à Task 4
- [ ] Reaproveitar classe ou funções de `build_html_saude.py`
- [ ] Carregar dados de `../output/tabelas/educacao/`
- [ ] Ajustar contexto dos prompts: "secretário de Educação"
- [ ] Títulos e labels específicos de Educação (ex: "FUNDEB" em vez de "SUS")

### 5.2 Seção adicional — Análise de Pessoal
- [ ] Ler `../educ-10-2025.xlsx` (aba `Total`, 4.021 linhas × 109 colunas)
- [ ] Extrair colunas: `Escola`, `Cargo`, `Função`, `Tipo Contrato` (ou `Lotação`), `Líquido` (salário líquido), `Proventos` (bruto)
- [ ] Gerar:
  - Contagem e custo total por tipo de contrato (Efetivo / Temporário / Aposentado)
  - Top 10 escolas por custo total de pessoal
  - Distribuição de proventos (histogram: faixas 0-3k, 3-5k, 5-8k, 8-10k, >10k)
  - Contar servidores com provento > R$ 10.000 e soma total
- [ ] Adicionar seção `#pessoal` ao HTML com action title + charts + tabela

### 5.3 Salvar e validar
- [ ] Salvar: `../output/relatorio_custos_educacao_2025.html`
- [ ] Mesmos critérios de aceite da Task 4

### ✅ Critérios adicionais:
- Seção de pessoal presente e com dados corretos
- Folha de 4.021 servidores lida sem erro

---

## TASK 6 — run_all.sh

- [ ] Criar `../output/run_all.sh`:

```bash
#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "=== [1/5] Extração dos dados 2025 ==="
python3 extract_data.py

echo "=== [2/5] Classificação de empenhos ==="
python3 classify_empenhos.py

echo "=== [3/5] Geração de tabelas analíticas ==="
python3 generate_tables.py

echo "=== [4/5] Relatório HTML — Saúde ==="
python3 build_html_saude.py

echo "=== [5/5] Relatório HTML — Educação ==="
python3 build_html_educacao.py

echo ""
echo "✅ CONCLUÍDO. Relatórios gerados:"
echo "   → relatorio_custos_saude_2025.html"
echo "   → relatorio_custos_educacao_2025.html"
```

- [ ] `chmod +x ../output/run_all.sh`

### ✅ Critério: `bash run_all.sh` executa sem erros e gera ambos os HTMLs.

---

## TASK 7 — Verificação Final

### 7.1 Integridade dos dados
- [ ] Soma de programas = total_pago do KPI (tolerância: ±0.01%)
- [ ] Ranking de fornecedores: pct_acumulado do último chega a ~100%
- [ ] Série mensal: número de meses bate com `meses_cobertos` do KPI

### 7.2 Validação visual (abrir HTMLs)
- [ ] Zero erros no console do browser
- [ ] Todos os charts renderizam com dados (nenhum vazio)
- [ ] Action titles contêm números específicos e não são genéricos
- [ ] Cards KPI formatados corretamente (R$ com separadores brasileiros)
- [ ] Nav lateral destaca seção ativa no scroll
- [ ] Layout em 375px (mobile): sem overflow horizontal

### 7.3 Validação narrativa
- [ ] Copiar todos os action titles em sequência
- [ ] Verificar: contam uma história coerente sem precisar ver os gráficos

---

## Notas para o Claude Code

1. **Encoding:** SEMPRE `encoding='latin-1', errors='replace'` nos CSVs do SICOM
2. **Valores BR:** Converter ANTES de qualquer cálculo — `"1.234,56"` → `1234.56`
3. **cod_unidade:** `.astype(str).str.strip()` obrigatório — pode ser int ou str
4. **pagamento.csv (28MB):** Se travar: `pd.read_csv(..., chunksize=50000)` e concatenar
5. **API Claude:** `ANTHROPIC_API_KEY` do env. Sem a key → apenas regras + fallback "Outros"
6. **Action titles:** Nunca genéricos. Sempre com número real interpolado dos dados
7. **HTML standalone:** Sem arquivos externos além do CDN do Chart.js. Dados como JSON inline
8. **Valor monetário display:** `R$ 1.234.567` (sem centavos em macronúmeros) — usar `toLocaleString('pt-BR')`
