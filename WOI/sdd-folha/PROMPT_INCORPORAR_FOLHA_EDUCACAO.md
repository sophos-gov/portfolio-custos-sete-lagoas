# Prompt — Incorporar Nova Folha de Pagamento da Educação ao Dashboard

## Para o Claude Code: leia este documento inteiro antes de executar qualquer comando.

---

## Contexto

O dashboard de custos da Educação (`relatorio_custos_educacao_2025.html`) já existe e está funcional com dados orçamentários SICOM 2025 e análise básica de pessoal via `educ-10-2025.xlsx` (jan–out/2025, 4.021 servidores).

Chegou uma **nova folha de pagamento da Educação (2026)** e precisa ser incorporada ao dashboard. Este documento contém todas as instruções para executar isso sem ambiguidade.

**Caminhos absolutos base (Windows):**
```
C:\Users\victo\OneDrive\Documentos\Python\projetos\custos\WOI\output\
C:\Users\victo\OneDrive\Documentos\Python\projetos\custos\WOI\output\tabelas\educacao\
C:\Users\victo\OneDrive\Documentos\Python\projetos\custos\WOI\output\tabelas\educacao\folha\
```

**Documentação de referência (ler se precisar de detalhes de implementação):**
- `sdd-folha/requirements.md` — requisitos e análises requeridas
- `sdd-folha/design.md` — arquitetura e código de referência
- `sdd-folha/tasks.md` — tasks de implementação (Tasks 2 e 5 são as relevantes para educação)

---

## Passo 1 — Identificar o arquivo da folha

### 1.1 Verificar os scripts necessários existem

Antes de qualquer coisa, confirme que os scripts foram implementados:

```bash
ls C:/Users/victo/OneDrive/Documentos/Python/projetos/custos/WOI/output/processa_folha_educacao.py
ls C:/Users/victo/OneDrive/Documentos/Python/projetos/custos/WOI/output/generate_folha.py
```

**Se os scripts NÃO existirem:** precisam ser implementados primeiro. Consultar `sdd-folha/tasks.md` Tasks 1, 2 e 5 para criá-los, depois retornar a este passo.

### 1.2 Localizar o arquivo da folha

O usuário deve indicar onde está o arquivo. Se não indicou, procurar nos locais prováveis:

```bash
# Procurar CSVs e XLSXs recentes no projeto
ls -lt C:/Users/victo/OneDrive/Documentos/Python/projetos/custos/WOI/*.csv 2>/dev/null
ls -lt C:/Users/victo/OneDrive/Documentos/Python/projetos/custos/WOI/*.xlsx 2>/dev/null
ls -lt C:/Users/victo/OneDrive/Documentos/Python/projetos/custos/WOI/output/*.csv 2>/dev/null
ls -lt C:/Users/victo/Downloads/*.csv 2>/dev/null | head -5
```

### 1.3 Inspecionar o arquivo encontrado

Verificar formato e integridade antes de processar:

```bash
# Para CSV — verificar header e contagem de linhas
head -2 /caminho/para/folha_educacao_2026.csv
wc -l /caminho/para/folha_educacao_2026.csv

# Para XLSX — verificar com Python
python3 -c "
import pandas as pd
xl = pd.ExcelFile('/caminho/para/folha_educacao_2026.xlsx')
print('Abas disponíveis:', xl.sheet_names)
df = xl.parse(xl.sheet_names[0], nrows=3)
print('Colunas:', list(df.columns))
print('Shape (3 linhas amostra):', df.shape)
"
```

**Formato esperado:**

| Atributo | Valor esperado |
|----------|----------------|
| Formato | CSV (`;` separador, `latin-1`) ou XLSX |
| Colunas obrigatórias | Matrícula, Nome, Lotação / Local de trabalho, Cargo, Proventos, Descontos, Líquido, Tipo Contrato |
| Rubricas de proventos | `Valor_XXXX` (ex: `Valor_0001`, `Valor_0011`) |
| Rubricas de descontos | `Valor_RYYY` (ex: `Valor_R001`) |
| Linhas esperadas | > 3.000 (a folha out/2025 tinha 4.021 servidores) |

**Se as colunas tiverem nomes diferentes** (ex: `Vl_Liquido` em vez de `Liquido`): o script `detectar_colunas()` tenta mapear automaticamente por similaridade. Se falhar, ver Troubleshooting § encoding/colunas.

---

## Passo 2 — Processar a folha

```bash
cd C:/Users/victo/OneDrive/Documentos/Python/projetos/custos/WOI/output

# CSV padrão
python3 processa_folha_educacao.py /caminho/para/folha_educacao_2026.csv \
    --competencia "Fev/2026"

# XLSX (ajustar --aba conforme nome real da aba)
python3 processa_folha_educacao.py /caminho/para/folha_educacao_2026.xlsx \
    --formato xlsx \
    --aba "Total" \
    --competencia "Fev/2026"

# Sem chave de API (usa fallback por template)
python3 processa_folha_educacao.py /caminho/para/folha_educacao_2026.csv \
    --competencia "Fev/2026" \
    --sem-api
```

**Ajuste `--competencia`** para o mês real da folha (ex: `"Mar/2026"`, `"Jan/2026"`).

### 2.1 Output esperado no console

```
📂 Lendo CSV...
  Shape: (N, M)
  Colunas mapeadas: matricula=Matrícula, lotacao=Local de trabalho, proventos=Proventos, ...
  Vínculos: EFETIVO=X, CONTRATO=Y, APOSENTADO=Z, COMISSIONADO=W

📊 Gerando tabelas...
  kpis_folha.json ✓
  por_vinculo.csv ✓ (N tipos)
  distribuicao_faixas.csv ✓ (7 faixas)
  top_locais.csv ✓ (15 locais)
  top_cargos.csv ✓ (15 cargos)
  alertas_folha.csv ✓ (N alertas)
  rubricas_top.csv ✓ (20 rubricas)
  cruzamento_woi.json ✓
  custo_por_escola.csv ✓ (15 escolas)
  tempo_servico.csv ✓ (5 faixas)

📈 Resumo — Educação Fev/2026:
  Servidores ativos: X
  Folha bruta: R$ Y
  Média salarial: R$ Z
  Gini: W
  % folha/orçamento: V%
```

Se aparecer erro antes do resumo, ir direto ao Troubleshooting.

---

## Passo 3 — Verificar tabelas geradas

```bash
ls -la C:/Users/victo/OneDrive/Documentos/Python/projetos/custos/WOI/output/tabelas/educacao/folha/
```

Deve conter **exatamente 10 arquivos**:

| # | Arquivo | Tamanho mínimo |
|---|---------|----------------|
| 1 | `kpis_folha.json` | > 200 bytes |
| 2 | `por_vinculo.csv` | > 100 bytes |
| 3 | `distribuicao_faixas.csv` | > 200 bytes |
| 4 | `top_locais.csv` | > 300 bytes |
| 5 | `top_cargos.csv` | > 300 bytes |
| 6 | `alertas_folha.csv` | qualquer tamanho (pode estar vazio se nenhum alerta) |
| 7 | `rubricas_top.csv` | > 300 bytes |
| 8 | `cruzamento_woi.json` | > 100 bytes |
| 9 | `custo_por_escola.csv` | > 300 bytes |
| 10 | `tempo_servico.csv` | > 150 bytes |

### 3.1 Validação rápida dos KPIs

```bash
cd C:/Users/victo/OneDrive/Documentos/Python/projetos/custos/WOI/output

python3 -c "
import json, csv

# KPIs principais
kpis = json.load(open('tabelas/educacao/folha/kpis_folha.json'))
print('=== KPIs da Folha ===')
print(f'Servidores ativos : {kpis[\"total_servidores_ativos\"]:,}')
print(f'Folha bruta       : R\$ {kpis[\"total_bruto\"]:,.2f}')
print(f'Média salarial    : R\$ {kpis[\"media_salario\"]:,.2f}')
print(f'Gini              : {kpis[\"gini\"]:.3f}')
print(f'% do orçamento    : {kpis[\"pct_folha_orcamento\"]:.1f}%')

# Validação de sanidade
assert kpis['total_servidores_ativos'] > 2000, 'ALERTA: menos de 2.000 servidores — verificar filtro'
assert 0.2 < kpis['gini'] < 0.8, f'ALERTA: Gini suspeito = {kpis[\"gini\"]}'
assert kpis['total_bruto'] > 1_000_000, 'ALERTA: folha bruta abaixo de R\$ 1M — verificar valores'
print()
print('✅ Sanidade OK')
"
```

**Valores de referência (folha out/2025 — educ-10-2025.xlsx):**
- Servidores ativos: ~4.021
- Folha bruta: verificar na execução anterior
- Gini: tipicamente entre 0.30 e 0.50 em educação municipal
- % orçamento: esperar entre 40% e 75% (educação é pessoal-intensiva)

### 3.2 Verificar distribuição de vínculos

```bash
python3 -c "
import pandas as pd
df = pd.read_csv('tabelas/educacao/folha/por_vinculo.csv')
print(df.to_string(index=False))
total = df['total_bruto'].sum()
kpis_total = __import__('json').load(open('tabelas/educacao/folha/kpis_folha.json'))['total_bruto']
print(f'\nSoma por vínculo: R\$ {total:,.2f}')
print(f'KPI total_bruto : R\$ {kpis_total:,.2f}')
diff_pct = abs(total - kpis_total) / kpis_total * 100
print(f'Diferença       : {diff_pct:.2f}% (deve ser < 1%)')
"
```

---

## Passo 4 — Regenerar o dashboard

```bash
cd C:/Users/victo/OneDrive/Documentos/Python/projetos/custos/WOI/output
python3 build_html_educacao.py
```

O script automaticamente:
1. Detecta que `tabelas/educacao/folha/` existe com dados
2. Carrega as novas tabelas (substituindo a análise básica anterior)
3. Chama API Claude Opus para action titles e análise narrativa (se `ANTHROPIC_API_KEY` estiver configurada)
4. Gera `relatorio_custos_educacao_2025.html` com seção de pessoal atualizada

**Verificar tamanho do HTML gerado:**
```bash
ls -lh relatorio_custos_educacao_2025.html
# Deve ficar entre 50 KB e 2.5 MB
```

Se exceder 2.5 MB, ver Troubleshooting § HTML muito grande.

---

## Passo 5 — Validar

### 5.1 Abrir no browser

```bash
# Windows — abrir o arquivo diretamente
start relatorio_custos_educacao_2025.html
```

Ou navegar até `C:\Users\victo\OneDrive\Documentos\Python\projetos\custos\WOI\output\relatorio_custos_educacao_2025.html` e abrir com Chrome/Edge.

### 5.2 Checklist visual — seção "Análise de Pessoal"

- [ ] Seção "#pessoal" presente na navegação lateral (sidebar)
- [ ] KPI cards com 4 valores: Servidores, Folha Bruta, Média, Gini
- [ ] **6 charts renderizando** (sem área cinza vazia):
  - [ ] `chartF_Vinculo` — doughnut de vínculos (EFETIVO, CONTRATO, APOSENTADO, ...)
  - [ ] `chartF_Faixas` — barras de faixas salariais (< 2k até > 20k)
  - [ ] `chartF_Locais` — barras horizontais top locais de lotação
  - [ ] `chartF_Rubricas` — barras horizontais top rubricas
  - [ ] `chartF_Escolas` — barras horizontais top escolas por custo
  - [ ] `chartF_TempoServ` — barras de tempo de serviço (5 faixas)
- [ ] Tabela de vínculos com colunas: Tipo, Servidores, Custo Total, %, Média
- [ ] Tabela de escolas com pelo menos 10 linhas
- [ ] Mini-seção "Folha vs. Orçamento" com cards comparativos
- [ ] Action title da seção contém pelo menos 2 números concretos (ex: "R$ X M" e "Y%")
- [ ] Números correspondem à nova folha 2026 (não à folha out/2025)

### 5.3 Checklist técnico (console do browser)

Abrir DevTools (F12) → aba Console:
- [ ] Zero erros vermelhos de JavaScript
- [ ] Zero erros "Cannot read properties of undefined" nos charts
- [ ] Verificar que os dados dos charts não são `[]` ou `[0, 0, 0]`

### 5.4 Verificar que a seção antiga foi substituída

A seção anterior usava dados de `educ-10-2025.xlsx` (out/2025). Confirme que:
- Os números de servidores e folha refletem a nova competência
- O título da seção menciona a competência correta (ex: "Fev/2026")

### 5.5 Se action titles estiverem com dados antigos

O cache Opus pode ter ficado desatualizado:
```bash
rm tabelas/educacao/folha/analise_opus_cache.json 2>/dev/null
python3 build_html_educacao.py
```

---

## Troubleshooting

### `UnicodeDecodeError` ao ler o CSV

```bash
# Tentar encodings alternativos
python3 processa_folha_educacao.py arquivo.csv --encoding utf-8
python3 processa_folha_educacao.py arquivo.csv --encoding cp1252
python3 processa_folha_educacao.py arquivo.csv --encoding utf-8-sig

# Detectar encoding automaticamente
python3 -c "
import chardet
raw = open('arquivo.csv', 'rb').read(10000)
print(chardet.detect(raw))
"
```

### Colunas não detectadas / `KeyError` em coluna

Verificar o header real do arquivo:
```bash
python3 -c "
import pandas as pd
# Para CSV
df = pd.read_csv('arquivo.csv', sep=';', encoding='latin-1', nrows=0)
print(list(df.columns))

# Para XLSX
xl = pd.ExcelFile('arquivo.xlsx')
print('Abas:', xl.sheet_names)
df = xl.parse(xl.sheet_names[0], nrows=0)
print(list(df.columns))
"
```

Ajustar o mapeamento de colunas em `generate_folha.py` função `detectar_colunas()` conforme os nomes reais.

### Poucos servidores (< 2.000) ou folha bruta suspeita

O arquivo pode estar incompleto ou filtrado incorretamente:
```bash
python3 -c "
import pandas as pd
df = pd.read_csv('arquivo.csv', sep=';', encoding='latin-1')
print('Total linhas:', len(df))
print('Tipo Contrato únicos:', df['Tipo Contrato'].value_counts().to_dict() if 'Tipo Contrato' in df.columns else 'coluna não encontrada')
print('Primeiras 3 linhas:\n', df.head(3))
"
```

### `Gini = 0` ou `NaN`

Indica que a coluna de proventos/líquido não foi convertida corretamente (valores como string `"1.234,56"` não foram parseados):
```bash
python3 -c "
import pandas as pd
df = pd.read_csv('arquivo.csv', sep=';', encoding='latin-1')
col = 'Proventos'  # ou o nome real da coluna
print('Tipo:', df[col].dtype)
print('Amostra:', df[col].head(10).tolist())
# Espera ver: strings tipo '1.234,56' ou floats
"
```

Se forem strings, o `to_num()` do `generate_folha.py` deve convertê-las. Verificar se a função está sendo chamada.

### `cruzamento_woi.json` vazio ou `pct_folha_orcamento = 0`

O cruzamento depende de `tabelas/educacao/kpis.json` (gerado pelo pipeline WOI principal):
```bash
ls tabelas/educacao/kpis.json
python3 -c "import json; print(json.load(open('tabelas/educacao/kpis.json')))"
```

Se `kpis.json` não existir, rodar o pipeline principal primeiro:
```bash
python3 generate_tables.py
```

### API Claude falha (`AuthenticationError` ou `RateLimitError`)

```bash
# Verificar se a chave está configurada
echo $ANTHROPIC_API_KEY

# Rodar sem API (usa fallback por template — relatório gerado normalmente)
python3 processa_folha_educacao.py arquivo.csv --competencia "Fev/2026" --sem-api
python3 build_html_educacao.py  # script detecta ausência de cache e usa fallback
```

### HTML muito grande (> 2.5 MB)

```bash
# Reduzir número de entradas nas tabelas
# Editar processa_folha_educacao.py: top_n=10 em vez de 15 para locais, cargos e escolas
# Ou rodar com flag se disponível:
python3 processa_folha_educacao.py arquivo.csv --top-n 10
```

### `processa_folha_educacao.py` não existe

O script ainda não foi implementado. Verificar tasks.md Task 5 e implementar antes de continuar.

Como alternativa temporária para gerar as tabelas manualmente:
```bash
python3 generate_folha.py  # se existir — gera tabelas de educação com dados padrão
```

### Charts renderizam vazios (sem dados)

Abrir o HTML em editor de texto e procurar por `chartF_Vinculo`:
```bash
grep -n "chartF_Vinculo\|VINC_LABELS\|VINC_VALUES" relatorio_custos_educacao_2025.html | head -10
```

Se as variáveis JavaScript estiverem como `[]` ou ausentes, o `build_html_educacao.py` não carregou as tabelas da folha. Verificar função `carregar_dados_folha()` no script.

---

## Referência rápida de comandos

```bash
# Caminho base
cd C:/Users/victo/OneDrive/Documentos/Python/projetos/custos/WOI/output

# Pipeline completo (processar folha + regenerar HTML em um comando)
python3 processa_folha_educacao.py /caminho/folha_2026.csv \
    --competencia "Fev/2026" \
    --rebuild-html

# Só processar folha (sem regenerar HTML)
python3 processa_folha_educacao.py /caminho/folha_2026.csv \
    --competencia "Fev/2026"

# Processar XLSX
python3 processa_folha_educacao.py /caminho/folha_2026.xlsx \
    --formato xlsx \
    --aba "Total" \
    --competencia "Fev/2026"

# Sem API (fallback por template)
python3 processa_folha_educacao.py /caminho/folha_2026.csv \
    --competencia "Fev/2026" \
    --sem-api

# Só regenerar HTML (tabelas já existem)
python3 build_html_educacao.py

# Validar KPIs em uma linha
python3 -c "import json; k=json.load(open('tabelas/educacao/folha/kpis_folha.json')); print(f'{k[\"total_servidores_ativos\"]} servidores | R\$ {k[\"total_bruto\"]:,.0f} | Gini {k[\"gini\"]:.3f} | {k[\"pct_folha_orcamento\"]:.1f}% do orçamento')"

# Pipeline completo desde o início (se SICOM também mudou)
bash run_all.sh
```

---

## Valores de sanidade para aceite

| Métrica | Mínimo | Máximo | Referência out/2025 |
|---------|--------|--------|---------------------|
| Servidores ativos | 2.000 | 6.000 | 4.021 |
| Gini | 0.20 | 0.80 | ~0.35–0.45 |
| Folha bruta | R$ 1 M | R$ 50 M | verificar histórico |
| % folha/orçamento | 15% | 85% | tipicamente 50–70% |
| Arquivos gerados | 10 | 10 | — |
| Tamanho HTML | 50 KB | 2.500 KB | ~100–300 KB |
