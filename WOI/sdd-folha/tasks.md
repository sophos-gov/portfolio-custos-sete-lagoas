# Tasks — Integração da Folha de Pagamento nos Dashboards de Custos

## Contexto para o Claude Code

Estender os dois relatórios HTML de custos (Saúde e Educação) com análise de folha de pagamento.
O pipeline WOI já existe e funciona. Esta integração **adiciona** a seção de pessoal sem quebrar o que já existe.

**LEIA ANTES DE COMEÇAR:**
- `requirements.md` — requisitos, fontes de dados, análises requeridas, spec do HTML
- `design.md` — arquitetura, código de referência, funções prontas, edge cases

**Caminhos ABSOLUTOS (para evitar ambiguidade):**
```
projetos/saude7l/Folha 11-2025 e exporta arquivo/2026-02.csv  → Folha Saúde Fev/2026
projetos/custos/WOI/educ-10-2025.xlsx                          → Folha Educação 2025
projetos/custos/WOI/output/                                    → Scripts e outputs
projetos/custos/WOI/output/tabelas/saude/                      → Tabelas WOI saúde
projetos/custos/WOI/output/tabelas/educacao/                   → Tabelas WOI educação
projetos/custos/WOI/output/tabelas/saude/folha/                → NOVO: tabelas folha saúde
projetos/custos/WOI/output/tabelas/educacao/folha/             → NOVO: tabelas folha educação
```

**Caminhos relativos (a partir de `output/`, onde os scripts rodam):**
```
../../../saude7l/Folha 11-2025 e exporta arquivo/2026-02.csv  → Folha Saúde Fev/2026
../educ-10-2025.xlsx                                            → Folha Educação 2025
tabelas/saude/                                                  → Tabelas WOI saúde
tabelas/educacao/                                               → Tabelas WOI educação
tabelas/saude/folha/                                            → NOVO: folha saúde
tabelas/educacao/folha/                                         → NOVO: folha educação
```

**ATENÇÃO:** O `build_html_saude.py` e `build_html_educacao.py` já existem e funcionam. As modificações devem ser **incrementais** — não reescrever do zero.

---

## TASK 1 — generate_folha.py (Saúde)

**Objetivo:** Processar `2026-02.csv` da Saúde e gerar tabelas analíticas da folha.

### 1.1 Setup
- [ ] Criar pasta `../output/tabelas/saude/folha/`
- [ ] Instalar: `pip install numpy --break-system-packages` (se não instalado)
- [ ] Criar o script em `../output/generate_folha.py`

### 1.2 Ler e normalizar CSV da Saúde
- [ ] Ler `../../../saude7l/Folha 11-2025 e exporta arquivo/2026-02.csv` usando `ler_folha_csv()` do design.md §2.1
  - **Caminho absoluto:** `projetos/saude7l/Folha 11-2025 e exporta arquivo/2026-02.csv`
- [ ] Aplicar `detectar_colunas()` do design.md §2.2 para mapear colunas automaticamente
- [ ] Converter todos os campos `Valor_*` com `to_num()`
- [ ] Verificar colunas mapeadas (printar: `matricula=X, lotacao=Y, proventos=Z`)
- [ ] Aplicar `calcular_campos()` do design.md §2.4
- [ ] Classificar vínculos com `classificar_vinculo()` do design.md §2.3
- [ ] Printar: `Shape: (N, M), Vínculos: {contagem por tipo}`

### 1.3 Carregar KPIs WOI existentes
- [ ] Ler `../output/tabelas/saude/kpis.json` para dados de cruzamento
- [ ] Se não existir: logar aviso e prosseguir sem cruzamento

### 1.4 Gerar tabelas analíticas
Usar as funções do design.md §3:
- [ ] `kpis_folha.json` — KPIs da folha + cruzamento WOI (§3.1)
- [ ] `por_vinculo.csv` — Distribuição por tipo de vínculo (§3.2)
- [ ] `distribuicao_faixas.csv` — Faixas salariais (§3.3)
- [ ] `top_locais.csv` — Top 15 locais de lotação (§3.4)
- [ ] `top_cargos.csv` — Top 15 cargos (mesma lógica, agrupado por Cargo)
- [ ] `alertas_folha.csv` — Anomalias detectadas (§3.5)
- [ ] `rubricas_top.csv` — Top 20 rubricas (§3.6)
- [ ] `cruzamento_woi.json` — Cruzamento folha vs. orçamento (§3.7)

Salvar tudo em `../output/tabelas/saude/folha/`

### 1.5 Printar resumo
- [ ] Total servidores ativos, aposentados
- [ ] Folha bruta total, média, mediana
- [ ] Gini
- [ ] Top 3 locais e top 3 cargos por custo
- [ ] Quantos alertas gerados por tipo
- [ ] % da folha sobre gasto total WOI

### ✅ Critérios de aceite:
- 8 arquivos gerados em `tabelas/saude/folha/`
- Nenhum CSV vazio
- `kpis_folha.json` contém `pct_folha_orcamento` > 0
- Gini entre 0.2 e 0.8 (sanidade)
- Pelo menos 800 servidores ativos processados

---

## TASK 2 — generate_folha.py (Educação)

**Objetivo:** Processar `educ-10-2025.xlsx` da Educação e gerar tabelas analíticas — incluindo análises específicas (escola, tempo de serviço).

### 2.1 Ler e normalizar Excel da Educação
- [ ] Ler `../educ-10-2025.xlsx`, aba `Total`
- [ ] Usar `detectar_colunas()` — atenção: campo escola é `Local de trabalho`, não `Escola`
- [ ] O campo `Tipo Contrato` já classifica vínculos (Efetivo/Temporário/Aposentado) — mapear para EFETIVO/CONTRATO/APOSENTADO
- [ ] Converter valores monetários com `to_num()`
- [ ] Printar: `Shape: (N, M), Vínculos: {contagem}`

### 2.2 Gerar tabelas padrão (mesmas da Saúde)
- [ ] `kpis_folha.json`
- [ ] `por_vinculo.csv`
- [ ] `distribuicao_faixas.csv`
- [ ] `top_locais.csv` (usando `Local de trabalho` como local)
- [ ] `top_cargos.csv`
- [ ] `alertas_folha.csv`
- [ ] `rubricas_top.csv`
- [ ] `cruzamento_woi.json`

### 2.3 Gerar tabelas específicas da Educação
- [ ] `custo_por_escola.csv` — Top 15 escolas por custo (design.md §6.1)
- [ ] `tempo_servico.csv` — Distribuição por faixa de tempo de serviço (design.md §6.2)
  - Data de referência: `2025-11-01` (competência da folha)
  - Se campo `Admissao` não existir: omitir esta tabela

Salvar em `../output/tabelas/educacao/folha/`

### 2.4 Printar resumo
- [ ] Mesmo do Task 1 + top 3 escolas + distribuição tempo de serviço

### ✅ Critérios de aceite:
- 10 arquivos gerados em `tabelas/educacao/folha/`
- ~4.021 servidores processados
- `custo_por_escola.csv` com pelo menos 10 escolas
- `tempo_servico.csv` com 5 faixas

---

## TASK 3 — Modificar build_html_saude.py

**Objetivo:** Adicionar seção `#pessoal` ao dashboard de Saúde.

### 3.1 Carregar dados da folha
- [ ] Adicionar função `carregar_dados_folha(dir_)` que lê os CSVs/JSONs de `tabelas/saude/folha/`
- [ ] Se a pasta não existir: retornar dict vazio (seção omitida)
- [ ] Integrar no fluxo existente de `carregar_dados()`

### 3.2 Expandir prompt Opus
- [ ] No `gerar_analise_opus()` existente, adicionar ao `payload`:
  ```python
  'folha_kpis': kpis_folha,
  'folha_por_vinculo': por_vinculo[:5],
  'folha_top_locais': top_locais[:5],
  'folha_cruzamento': cruzamento_woi,
  ```
- [ ] Atualizar o JSON esperado para incluir:
  ```json
  "action_title_pessoal": "...",
  "analise_folha": "...",
  "cruzamento_custos": "...",
  "alertas_folha": ["..."],
  "recomendacoes_folha": [{"insight":"...", "implicacao":"...", "acao":"..."}]
  ```
- [ ] No fallback, usar `gerar_analise_folha_fallback()` do design.md §4.2

### 3.3 Adicionar link na nav sidebar
- [ ] Inserir `<a href="#pessoal">Análise de Pessoal</a>` entre `#fontes` e `#sintese` (ou `#recomendacoes`)

### 3.4 Construir HTML da seção
- [ ] Usar template do design.md §5.1
- [ ] KPI cards: Servidores, Folha Bruta, Média, Gini
- [ ] Charts:
  - `chartVinculo` (doughnut) — por tipo de vínculo
  - `chartFaixas` (bar horizontal) — por faixa salarial
  - `chartLocais` (bar horizontal) — top 10 locais
  - `chartRubricas` (bar horizontal) — top 10 rubricas
- [ ] Tabela de vínculos com: tipo, servidores, custo, %, média
- [ ] Tabela top locais com: local, servidores, custo, %
- [ ] Mini-seção "Cruzamento com Custos": cards + texto analítico
- [ ] Alertas em cards vermelhos (se houver)

### 3.5 Adicionar variáveis JavaScript
- [ ] Serializar dados da folha como JSON inline:
  ```javascript
  const VINC_LABELS = [...];
  const VINC_VALUES = [...];
  const FAIXA_LABELS = [...];
  const FAIXA_VALUES = [...];
  const LOCAL_LABELS = [...];
  const LOCAL_VALUES = [...];
  const RUBRIC_LABELS = [...];
  const RUBRIC_VALUES = [...];
  ```
- [ ] Adicionar inicialização dos 4 charts (design.md §5.2)

### 3.6 Mesclar recomendações
- [ ] Se houver `recomendacoes_folha`, substituir 2 das 4 recomendações gerais pelas da folha
- [ ] Priorizar recomendações com dados mais concretos

### 3.7 Regenerar HTML
- [ ] Salvar `relatorio_custos_saude_2025.html` com seção nova
- [ ] Verificar: tamanho < 2.5 MB

### ✅ Critérios de aceite:
- Seção `#pessoal` visível no HTML entre `#fontes` e `#sintese`
- 4 charts renderizam sem erro no console
- KPIs formatados corretamente (R$, separadores BR)
- Nav lateral inclui link "Análise de Pessoal"
- Cards de cruzamento WOI presentes
- Se pasta `folha/` não existe: seção graciosamente omitida

---

## TASK 4 — Modificar build_html_educacao.py

**Objetivo:** Aprimorar seção `#pessoal` existente da Educação com análises mais profundas.

### 4.1 Substituir `analisar_pessoal()` básica
- [ ] Em vez de processar xlsx inline, carregar tabelas pré-geradas de `tabelas/educacao/folha/`
- [ ] Manter fallback: se `folha/` não existir, usar `analisar_pessoal()` atual com xlsx
- [ ] Isso garante compatibilidade: se rodar sem Task 2, ainda funciona

### 4.2 Expandir seção `#pessoal` com novos charts
- [ ] Adicionar chart `chartEscolas` (bar horizontal) — top 10 escolas por custo
- [ ] Adicionar chart `chartTempoServico` (bar) — distribuição por faixa de tempo
- [ ] Adicionar tabela de escolas expandida (mais colunas que a atual)
- [ ] Adicionar tabela de tempo de serviço

### 4.3 Adicionar cruzamento WOI
- [ ] Mini-seção "Folha vs. Orçamento" com cards comparativos (mesmo padrão da Saúde)
- [ ] Texto analítico cruzando folha com dados orçamentários

### 4.4 Expandir prompt Opus (mesma lógica da Task 3)
- [ ] Incluir dados da folha no payload do `gerar_analise_opus()`
- [ ] Incluir `action_title_pessoal` e `cruzamento_custos` no retorno
- [ ] Fallback sem API

### 4.5 Regenerar HTML
- [ ] Salvar `relatorio_custos_educacao_2025.html` com seção aprimorada
- [ ] Verificar < 2.5 MB

### ✅ Critérios de aceite:
- Seção `#pessoal` com 6+ charts (vs. 3 atuais)
- Charts de escola e tempo de serviço presentes
- Cruzamento WOI com cards
- Fallback para xlsx funciona se `folha/` não existir
- Tabelas expandidas com mais dados

---

## TASK 5 — processa_folha_educacao.py (Gancho)

**Objetivo:** Script standalone que processa folha nova da Educação quando ela chegar.

### 5.1 Criar script com argparse
- [ ] Criar `../output/processa_folha_educacao.py`
- [ ] Argumentos: `arquivo`, `--competencia`, `--formato`, `--aba`, `--sem-api`
- [ ] Usar o layout do design.md §7.1

### 5.2 Implementar pipeline completo
- [ ] Ler CSV (formato padrão de folha: `;`, `latin-1`) ou XLSX
- [ ] Aplicar todas as funções de `generate_folha.py`:
  - `ler_folha_csv()` ou `pd.read_excel()`
  - `detectar_colunas()`
  - `calcular_campos()`
  - `gerar_kpis_folha()`
  - `gerar_por_vinculo()`
  - `gerar_faixas()`
  - `gerar_top_locais()`
  - `gerar_alertas()`
  - `gerar_rubricas_top()`
  - `gerar_cruzamento_woi()`
  - `gerar_custo_por_escola()` (educação)
  - `gerar_tempo_servico()` (educação)
- [ ] Salvar em `tabelas/educacao/folha/`
- [ ] Chamar API Opus se `--sem-api` não for passado
- [ ] Printar resumo completo

### 5.3 Opção de regenerar HTML
- [ ] Flag `--rebuild-html`: após gerar tabelas, rodar `build_html_educacao.py`
- [ ] Implementar como subprocess: `subprocess.run(['python3', 'build_html_educacao.py'])`

### 5.4 Testar com dados da educação existentes
- [ ] Rodar: `python3 processa_folha_educacao.py ../educ-10-2025.xlsx --formato xlsx --competencia "Out/2025"`
- [ ] Verificar que gera as mesmas tabelas que Task 2

### ✅ Critérios de aceite:
- Script roda com `python3 processa_folha_educacao.py arquivo.csv`
- Aceita CSV e XLSX
- Gera 10 tabelas em `tabelas/educacao/folha/`
- `--rebuild-html` regenera o relatório
- `--sem-api` funciona sem key

---

## TASK 6 — PROMPT_INCORPORAR_FOLHA_EDUCACAO.md

**Objetivo:** Documento-prompt para o Claude Code quando a folha de 2026 chegar.

### 6.1 Criar documento
- [ ] Criar `../sdd-folha/PROMPT_INCORPORAR_FOLHA_EDUCACAO.md`
- [ ] Conteúdo: instruções completas, passo a passo, para o Claude Code:

```markdown
# Prompt — Incorporar Nova Folha de Educação ao Dashboard

## Contexto
O dashboard de custos da Educação (`relatorio_custos_educacao_2025.html`) já existe e funciona.
Chegou uma nova folha de pagamento da Educação (2026).

## Passos

### 1. Identificar o arquivo
O arquivo da folha de educação 2026 deve estar na pasta do projeto.
Formato esperado: CSV com separador `;`, encoding `latin-1`.
Se for XLSX, usar flag `--formato xlsx`.

### 2. Processar a folha
```bash
cd projetos/custos/WOI/output
python3 processa_folha_educacao.py /caminho/para/folha_educ_2026.csv --competencia "Mês/2026"
```

### 3. Verificar tabelas geradas
```bash
ls -la tabelas/educacao/folha/
```
Deve conter: kpis_folha.json, por_vinculo.csv, distribuicao_faixas.csv, top_locais.csv,
top_cargos.csv, alertas_folha.csv, rubricas_top.csv, cruzamento_woi.json,
custo_por_escola.csv, tempo_servico.csv

### 4. Regenerar dashboard
```bash
python3 build_html_educacao.py
```

### 5. Validar
- Abrir `relatorio_custos_educacao_2025.html` no browser
- Verificar seção "Análise de Pessoal"
- Confirmar que action titles contêm números da nova folha
- Console do browser sem erros JS

### Troubleshooting
- Se CSV com encoding errado: tentar `--encoding utf-8` ou `--encoding cp1252`
- Se colunas não detectadas: verificar nomes no header do CSV
- Se API falhar: usar `--sem-api` e action titles serão gerados por template
```

### ✅ Critério: documento claro e autossuficiente para o Claude Code executar sem ambiguidade.

---

## TASK 7 — Atualizar run_all.sh

**Objetivo:** Incluir geração de tabelas da folha no pipeline completo.

### 7.1 Modificar `../output/run_all.sh`
- [ ] Adicionar etapa entre generate_tables e build_html:

```bash
#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "=== [1/6] Extração dos dados 2025 ==="
python3 extract_data.py

echo "=== [2/6] Classificação de empenhos ==="
python3 classify_empenhos.py

echo "=== [3/6] Geração de tabelas analíticas ==="
python3 generate_tables.py

echo "=== [4/6] Processamento da folha de pagamento ==="
python3 generate_folha.py

echo "=== [5/6] Relatório HTML — Saúde ==="
python3 build_html_saude.py

echo "=== [6/6] Relatório HTML — Educação ==="
python3 build_html_educacao.py

echo ""
echo "✅ CONCLUÍDO. Relatórios gerados:"
echo "   → relatorio_custos_saude_2025.html"
echo "   → relatorio_custos_educacao_2025.html"
```

### ✅ Critério: `bash run_all.sh` executa sem erros e gera ambos os HTMLs com seção de pessoal.

---

## TASK 8 — Verificação Final

### 8.1 Integridade dos dados
- [ ] `kpis_folha.json` da Saúde: ~950 servidores, Gini entre 0.3-0.7
- [ ] `kpis_folha.json` da Educação: ~4.021 servidores
- [ ] `cruzamento_woi.json`: `pct_folha_orcamento` entre 15% e 80% (sanidade)
- [ ] `por_vinculo.csv`: soma de `total_bruto` = `kpis_folha.total_bruto`
- [ ] `alertas_folha.csv`: pelo menos 1 alerta do tipo `elite_acima_20k` na Saúde

### 8.2 Validação visual dos HTMLs
- [ ] Abrir `relatorio_custos_saude_2025.html`:
  - Seção `#pessoal` presente e visível
  - 4 charts renderizam com dados
  - KPIs formatados corretamente
  - Cruzamento WOI com cards
  - Nav sidebar atualizada
- [ ] Abrir `relatorio_custos_educacao_2025.html`:
  - Seção `#pessoal` aprimorada
  - Charts de escola e tempo de serviço
  - Cruzamento WOI
  - Mais dados que a versão anterior

### 8.3 Validação do gancho
- [ ] `python3 processa_folha_educacao.py ../educ-10-2025.xlsx --formato xlsx --sem-api` funciona
- [ ] Tabelas geradas em `tabelas/educacao/folha/`
- [ ] `PROMPT_INCORPORAR_FOLHA_EDUCACAO.md` é autoexplicativo

### 8.4 Zero erros no console
- [ ] Abrir ambos HTMLs no Chrome/Edge
- [ ] Console do DevTools: zero erros JS
- [ ] Todos os charts com dados (nenhum vazio)

### 8.5 Validação narrativa
- [ ] Copiar todos os action titles (incluindo pessoal) em sequência
- [ ] Verificar: contam uma história coerente do macro ao micro
- [ ] Action title de pessoal contém pelo menos 2 números concretos

---

## Notas para o Claude Code

1. **NÃO REESCREVER** `build_html_saude.py` nem `build_html_educacao.py` do zero — fazer modificações incrementais
2. **Reutilizar** código: `generate_folha.py` deve ser importável por ambos os build_html e por `processa_folha_educacao.py`
3. **Encoding:** SEMPRE `encoding='latin-1', errors='replace'` nos CSVs de folha
4. **Valores BR:** Converter ANTES de qualquer cálculo — `"1.234,56"` → `1234.56`
5. **API Claude:** `ANTHROPIC_API_KEY` do env. Sem a key → fallback com f-strings (nunca falhar)
6. **Folha Saúde:** `2026-02.csv` é Fev/2026 — competência mais recente
7. **Folha Educação:** `educ-10-2025.xlsx` é 10 meses de 2025 — dados acumulados
8. **Compatibilidade:** Se pasta `folha/` não existir, dashboards devem funcionar sem a seção de pessoal
9. **Cruzamento WOI:** é o diferencial — conectar folha com dados orçamentários em toda narrativa
10. **Chart IDs:** O `build_html_educacao.py` já usa: `chartProg`, `chartNat`, `chartAcoes`, `chartForn`, `chartPareto`, `chartCat`, `chartMensal`, `chartFontes`, `chartHist`, `chartTipos`, `chartEscolas`. Para a seção de folha, usar IDs com prefixo `chartF_`: `chartF_Vinculo`, `chartF_Faixas`, `chartF_Locais`, `chartF_Rubricas`, `chartF_TempoServ`. O `build_html_saude.py` usa os mesmos IDs base (sem `chartHist`, `chartTipos`, `chartEscolas`) — usar mesmo prefixo `chartF_`.
