# PRD — Auditoria Automatizada de Folha de Pagamento Municipal

> **Template replicável** baseado no projeto Santa Luzia/MG (2026).  
> Adaptável a qualquer município brasileiro com acesso a folhas de pagamento + legislação local.

---

## 1. Contexto e Objetivo

### O que é este projeto

Pipeline automatizado de auditoria forense de folha de pagamento municipal, que transforma planilhas XLS brutas em um relatório Word fundamentado legalmente, identificando irregularidades com quantificação financeira precisa.

### Por que automatizar

| Abordagem | Tempo | Qualidade |
|-----------|-------|-----------|
| Manual tradicional | 3–6 meses, 1 auditor | Parcial, sem cruzamento sistemático |
| Este pipeline | 2–4 semanas | 100% das rubricas, cruzamento com legislação, quantificação automática |

### Resultado esperado

- **Irregularidades identificadas** com base legal citada (artigo, lei, data)
- **Quantificação financeira** por irregularidade e total
- **Relatório Word** (`relatorio_vX.docx`) pronto para entrega ao TCE/TCU ou cliente
- **Trilha de auditoria** completa (scripts, dados, logs, versões)

---

## 2. Contexto de Domínio

### Base legal mínima a levantar antes de iniciar

```
CF/88
├── Art. 37, XI      → Teto constitucional (salário do Governador do Estado)
├── Art. 37, XIV     → Vinculação/equiparação de vencimentos (proibida)
├── Art. 40 / 201    → RPPS vs RGPS (regimes previdenciários)
└── Art. 212 / 212-A → FUNDEB (vinculação de receita de educação)

LRF (LC 101/2000)
├── Art. 18–20       → Gastos com pessoal (limite de 60% da RCL)
├── Art. 21 §único   → Vantagens pessoais após último ano de mandato
└── Art. 22          → Vedações (contratação, progressão) quando acima do limite

LC 173/2020          → Proibições emergenciais COVID (ainda relevante para contratos vigentes)

Lei Orgânica Municipal + Estatuto dos Servidores Municipal
Plano de Carreira, Cargos e Vencimentos (PCCV) vigente
Leis específicas de gratificações (lei por lei para cada rubrica)
```

### Irregularidades mais comuns a procurar

| Código | Tipo | Base Legal |
|--------|------|-----------|
| I.TETO | Teto constitucional ultrapassado | CF art. 37 XI |
| I.PSS | Vantagem PSS sem previsão no edital | Edital PSS + Lei Orgânica |
| I.LRF | Concessão pós-vedação LRF | LRF art. 21 §único |
| I.QUINQ | Quinquênio concedido a temporários | Estatuto (aplicação indevida) |
| I.INSALUB | Insalubridade sem laudo vigente | CLT art. 190 + LC municipal |
| I.FUNDEB | Distribuição FUNDEB fora do prazo/proporcionalidade | LC 14.113/2020 |
| I.INSS | Retenção INSS sobre vantagens não salariáveis | Lei 8.212/1991 |
| I.FGC | Headcount FGC acima do cap legal | PCCV Anexo de cargos em comissão |

---

## 3. Dados de Entrada Necessários

### 3.1 Folhas de Pagamento (OBRIGATÓRIO)

```
dados-brutos/folhas-pagamento/
├── YYYY MM SalarioDetalhado MM YYYY.xlsx   ← padrão de nome
├── ...
└── (mínimo: 3 competências/ano × anos auditados)
```

**Formato esperado (wide):**

| MATRICULA | NOME | CARGO | RUBRICA_001 | RUBRICA_002 | ... | TOTAL |
|-----------|------|-------|-------------|-------------|-----|-------|
| 1234 | JOAO SILVA | FISCAL | 3500.00 | 500.00 | ... | 4800.00 |

> Cada rubrica é uma coluna. O pipeline converte para formato longo.

**Competências recomendadas:** Janeiro, Julho e Dezembro de cada ano (captura reajustes + 13º).

### 3.2 Legislação Municipal (OBRIGATÓRIO)

```
legislacao/
├── estatuto_servidores.pdf
├── pccv_vigente.pdf
├── lei_XXXX_YYYY_gratificacao_X.pdf
└── ...
```

Fontes:
- Site oficial da Câmara Municipal
- leismunicipais.com.br
- SAPL (Sistema de Apoio ao Processo Legislativo)
- Portal da Transparência municipal

### 3.3 Editais de PSS/Concurso (se aplicável)

```
editais/
├── edital_pss_001_YYYY.pdf
├── edital_pss_002_YYYY.pdf
└── ...
```

### 3.4 Certidões e Comprovantes (opcional)

```
certidoes/
├── cnd_fgts.pdf
├── cnd_receita_federal.pdf
└── ...
```

---

## 4. Estrutura de Diretórios do Projeto

```
nome-municipio/
├── dados-brutos/
│   └── folhas-pagamento/          ← XLS originais (nunca modificar)
├── legislacao/                    ← PDFs das leis (referência)
├── editais/                       ← Editais PSS/concurso
├── certidoes/                     ← CNDs, regularidade
├── auditoria/
│   ├── scripts/                   ← Todos os scripts Python
│   │   ├── 01_consolidar_folhas.py
│   │   ├── 02_catalogo_gratificacoes.py
│   │   ├── 03_indicadores.py
│   │   ├── 04_grat_por_cargo.py
│   │   ├── T5XX_*.py              ← Análises de domínio
│   │   └── T6XX_*.py              ← Análises de domínio
│   ├── data/
│   │   ├── folha_consolidada.parquet   ← Gerado pelo 01_
│   │   ├── leis_txt/                   ← Textos extraídos das leis
│   │   └── catalogo_gratificacoes.json ← Gerado pelo 02_
│   └── outputs/                   ← Análises individuais (.md, .xlsx)
├── relatorios/
│   ├── relatorio_v1.docx
│   └── versoes/
├── specs/
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
├── logs/
├── .env                           ← API keys (NUNCA versionar)
├── SPEC.md                        ← Log de sessão (diário de bordo)
├── PENDENCIAS.md                  ← Tarefas abertas
└── plan.json                      ← Orquestração SDD
```

---

## 5. Pipeline de Execução

### Fase 1 — Ingestão e Consolidação

**Objetivo:** Transformar N planilhas XLS (wide, rubricas como colunas) em um único arquivo Parquet (long, uma linha por rubrica por servidor por competência).

**Script:** `01_consolidar_folhas.py`

```python
# Saída esperada:
# folha_consolidada.parquet
# Colunas: matricula | nome | cargo | competencia | rubrica_codigo | rubrica_desc | valor
# Linhas: ~200k–500k dependendo do município

# Pontos de adaptação:
# - regex para detectar nome da competência no nome do arquivo
# - lista de colunas a ignorar (totais, subtotais)
# - encoding do arquivo (UTF-8, latin-1, cp1252)
```

**Validação de qualidade:**
- [ ] Nenhuma matricula vazia
- [ ] Soma das rubricas bate com total da planilha (tolerância: R$ 0,01)
- [ ] Todas as competências esperadas presentes

---

### Fase 2 — Catalogação e Perfilamento Estatístico

**Objetivo:** Construir o catálogo de rubricas com estatísticas (média, max, presença, servidores).

**Scripts:** `02_catalogo_gratificacoes.py`, `03_indicadores.py`, `04_grat_por_cargo.py`

```python
# Saída esperada:
# catalogo_gratificacoes.json  ← 1 entrada por rubrica
# {
#   "codigo_rubrica": "63",
#   "descricao": "PRODUT-GIP-1835/96",
#   "classe": "produtividade",  ← classificar manualmente depois
#   "n_servidores": 12,
#   "n_pagamentos": 3847,
#   "valor_acumulado": 3207876.85,
#   "valor_medio": 833.87,
#   "vigente_em_YYYY_MM": true,
#   "valor_dez_YYYY": 255234.66
# }
```

**Entregável visual:** `grat_x_cargo.xlsx` — pivot rubrica × cargo com frequências. Use para identificar rubricas concentradas em cargos específicos (sinal de irregularidade).

---

### Fase 3 — Extração e Tratamento da Legislação

**Objetivo:** Converter PDFs de leis em texto pesquisável.

**Scripts:** `07b_buscar_leis_html.py` (download), `07d_ocr_leis.py` (OCR)

```bash
# Instalação necessária:
pip install pymupdf pytesseract
# + Tesseract-OCR no sistema: https://github.com/UB-Mannheim/tesseract/wiki

# Para PDFs digitais (não escaneados):
python -c "import fitz; doc=fitz.open('lei.pdf'); print(doc[0].get_text())"

# Para PDFs escaneados:
tesseract lei_scan.pdf lei_scan_ocr txt -l por
```

**Saída:** `auditoria/data/leis_txt/Lei_XXXX_YYYY.txt`

---

### Fase 4 — Análises de Domínio (T5XX / T6XX)

**Objetivo:** Auditar rubricas específicas contra a legislação. Um script por "família" de irregularidade.

**Padrão de script T5XX/T6XX:**

```python
"""
T5XX_analise_NOME.py
Audita a rubrica/gratificação NOME contra a lei YYYY/XXXX.
"""
import pandas as pd
import json

# 1. Carregar dados
df = pd.read_parquet("../data/folha_consolidada.parquet")
with open("../data/catalogo_gratificacoes.json") as f:
    catalogo = {str(i["codigo_rubrica"]): i for i in json.load(f)}

# 2. Filtrar rubrica-alvo
rubrica_alvo = "63"  # ← adaptar
df_alvo = df[df["rubrica_codigo"] == rubrica_alvo]

# 3. Cruzar com regra legal
# Ex: verificar se servidor está em cargo autorizado
# Ex: verificar se valor ultrapassa teto da lei
# Ex: verificar se contrato PSS permite o benefício

# 4. Quantificar impacto
impacto_total = df_alvo["valor"].sum()
servidores_afetados = df_alvo["matricula"].nunique()

# 5. Gerar evidência
df_alvo.to_excel("../outputs/T5XX_evidencia.xlsx", index=False)

# 6. Gerar análise markdown
with open("../outputs/T5XX_analise.md", "w", encoding="utf-8") as f:
    f.write(f"## Irregularidade I.XX — NOME DA RUBRICA\n\n")
    f.write(f"**Base legal:** Lei XXXX/YYYY, Art. Y\n")
    f.write(f"**Servidores afetados:** {servidores_afetados}\n")
    f.write(f"**Valor total:** R$ {impacto_total:,.2f}\n")
    f.write(f"**Período:** {df_alvo['competencia'].min()} a {df_alvo['competencia'].max()}\n\n")
    f.write("### Fundamentação\n\n[texto legal aqui]\n")
```

**Análises prioritárias para qualquer município:**

| Script | Alvo | Verificar |
|--------|------|-----------|
| `T501_teto_constitucional.py` | Todos servidores | Total mensal > teto do Estado |
| `T502_temporarios.py` | Servidores temporários (PSS) | Rubricas exclusivas de estatutários |
| `T503_quinquenio.py` | Quinquênio | Aplicação a não-efetivos |
| `T504_insalubridade.py` | Insalubridade/periculosidade | Laudo vigente; base legal |
| `T505_lrf_vedacoes.py` | Novos FGCs, progressões | Datas vs janelas LRF |
| `T506_fundeb.py` | Rubricas com fonte FUNDEB | Proporcionalidade mínimo 70% |

---

### Fase 5 — Pesquisa de Jurisprudência (opcional, recomendado)

**Objetivo:** Fortalecer cada achado com decisões do TCU, TCE, STJ, STF.

**Scripts:** `12_buscar_jurisprudencia.py`, `gip_multiagente.py`

```python
# APIs disponíveis:
# TCU:    https://contas.tcu.gov.br/juris/SvlHighLight
# DataJud: https://api-publica.datajud.cnj.jus.br  (requer API key gratuita)
# STF:    https://jurisprudencia.stf.jus.br/pages/search

# Termos de busca por irregularidade:
TERMOS = {
    "teto": ["teto constitucional", "art 37 XI", "acórdão 2.884/2022 TCU"],
    "insalubridade": ["insalubridade CLT servidor estatutário", "ausência laudo"],
    "pss": ["contratação temporária vantagem", "regime especial benefício"],
    "lrf": ["art 21 LC 101", "vedação concessão vantagem último ano"],
}
```

---

### Fase 6 — Geração do Relatório Word

**Objetivo:** Compilar todas as análises `.md` em um relatório `.docx` estruturado.

**Scripts:** `14_preencher_template_docx.py`, `16b_gerar_relatorio_humanizado.py`

```python
# Usando python-docx:
from docx import Document

doc = Document("template_relatorio.docx")

for irregularidade in irregularidades_confirmadas:
    # Adicionar seção
    doc.add_heading(f"Irregularidade {irregularidade['codigo']}", level=2)
    doc.add_paragraph(irregularidade['fundamentacao'])
    
    # Adicionar tabela de evidência
    table = doc.add_table(rows=1, cols=4)
    # ... preencher tabela

doc.save(f"relatorios/relatorio_v1.docx")

# OU usar SuperDoc MCP (mais robusto para formatação complexa):
# superdoc_open → superdoc_edit → superdoc_save
```

**Revisão de linguagem:** Usar Claude para suavizar afirmações (de "ilegal" para "em desconformidade com") antes da entrega final.

---

## 6. Orquestração SDD (plan.json)

### Estrutura do plan.json

```json
{
  "project": "auditoria-[municipio]",
  "version": "1.0",
  "token_budget": 86000,
  "tasks": [
    {
      "id": "T001",
      "title": "Consolidação da Folha",
      "script": "scripts/01_consolidar_folhas.py",
      "model": "haiku",
      "surface": "claude-code",
      "depends_on": [],
      "status": "pending",
      "acceptance_criteria": [
        "folha_consolidada.parquet criado",
        "zero linhas com matricula vazia",
        "soma bate com total XLS (tolerância R$ 0,01)"
      ]
    },
    {
      "id": "T002",
      "title": "Catálogo de Gratificações",
      "script": "scripts/02_catalogo_gratificacoes.py",
      "model": "haiku",
      "surface": "claude-code",
      "depends_on": ["T001"],
      "status": "pending"
    },
    {
      "id": "T003",
      "title": "Extração de Leis (OCR)",
      "script": "scripts/07d_ocr_leis.py",
      "model": "haiku",
      "surface": "claude-code",
      "depends_on": [],
      "status": "pending"
    },
    {
      "id": "T004",
      "title": "Análise Teto Constitucional",
      "script": "scripts/T501_teto_constitucional.py",
      "model": "sonnet",
      "surface": "claude-code",
      "depends_on": ["T001", "T002"],
      "status": "pending"
    },
    {
      "id": "T005",
      "title": "Análises de Domínio (T5XX/T6XX)",
      "script": "scripts/T502_*.py ... T5XX_*.py",
      "model": "sonnet",
      "surface": "claude-code",
      "depends_on": ["T001", "T002", "T003"],
      "status": "pending"
    },
    {
      "id": "T006",
      "title": "Pesquisa de Jurisprudência",
      "script": "scripts/12_buscar_jurisprudencia.py",
      "model": "sonnet",
      "surface": "claude-code",
      "depends_on": ["T005"],
      "status": "pending"
    },
    {
      "id": "T007",
      "title": "Geração do Relatório Word",
      "script": "scripts/16b_gerar_relatorio_humanizado.py",
      "model": "sonnet",
      "surface": "claude-code",
      "depends_on": ["T005", "T006"],
      "status": "pending"
    },
    {
      "id": "T008",
      "title": "Revisão e Validação do Relatório",
      "script": "manual",
      "model": "opus",
      "surface": "cowork",
      "depends_on": ["T007"],
      "status": "pending",
      "notes": "Revisor independente valida achados críticos"
    },
    {
      "id": "T009",
      "title": "Entrega Final",
      "script": "manual",
      "surface": "human",
      "depends_on": ["T008"],
      "status": "pending"
    }
  ]
}
```

---

## 7. Documentação de Sessão (SPEC.md)

Manter `SPEC.md` como diário de bordo do projeto. Atualizar a cada sessão.

```markdown
# SPEC.md — Auditoria [Município]/[Estado]

## Sessão 1 — [Data]
### Objetivos
- [ ] Consolidar folhas XLS
- [ ] Gerar catálogo inicial

### Resultados
- folha_consolidada.parquet: 218.256 linhas, 88 competências
- 238 rubricas identificadas
- Top 5 rubricas por valor: ...

### Decisões Tomadas
- Usar competências Jan/Jul/Dez (vs todas): reduz volume 4×, mantém sazonal
- Ignorar rubrica 999 (ajuste contábil interno, não remuneratório)

### Pendências para próxima sessão
- [ ] Baixar texto da Lei 1.835 do site da Câmara
- [ ] Confirmar teto constitucional do Estado para o período
```

---

## 8. PENDENCIAS.md

```markdown
# PENDENCIAS.md — [Município]

## Abertas

### [DATA] — [Descrição]
- **Prioridade:** Alta / Média / Baixa
- **Bloqueador:** [o que impede a conclusão]
- **Próxima ação:** [ação específica]

## Fechadas
- [x] [DATA] — [Descrição] — Resolvido por [solução]
```

---

## 9. Dependências e Ambiente

### Instalação

```bash
# Ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Dependências core
pip install pandas openpyxl pyarrow python-docx pymupdf pytesseract requests anthropic

# Dependências opcionais
pip install google-generativeai  # Gemini (análise com contexto grande)
pip install python-dotenv        # Carregar .env automaticamente
pip install beautifulsoup4       # Scraping de leis

# Sistema (Windows)
# Tesseract-OCR: https://github.com/UB-Mannheim/tesseract/wiki
```

### .env (não versionar)

```bash
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...         # Opcional: análise de contexto grande
DATAJUD_API_KEY=...            # Opcional: pesquisa de jurisprudência
```

### requirements.txt

```
pandas>=2.0.0
openpyxl>=3.1.0
pyarrow>=14.0.0
python-docx>=1.1.0
pymupdf>=1.24.0
pytesseract>=0.3.10
requests>=2.31.0
anthropic>=0.28.0
python-dotenv>=1.0.0
beautifulsoup4>=4.12.0
```

---

## 10. Checklist de Replicação

### Pré-projeto

- [ ] Dados de folha coletados (XLS, mínimo 3 competências/ano)
- [ ] Legislação municipal baixada (estatuto, PCCV, leis de gratificações)
- [ ] Editais PSS/concurso coletados (se aplicável)
- [ ] API keys configuradas (Anthropic obrigatório; Gemini e DataJud opcionais)
- [ ] Teto constitucional do Estado confirmado para o período auditado
- [ ] CNPJ do município para consultas de certidões

### Fase de Consolidação (1–2 dias)

- [ ] `01_consolidar_folhas.py` adaptado ao formato do município
- [ ] `folha_consolidada.parquet` gerado e validado
- [ ] `02_catalogo_gratificacoes.py` executado
- [ ] `catalogo_gratificacoes.json` revisado manualmente (classificar rubricas)
- [ ] `grat_x_cargo.xlsx` analisado para identificar anomalias óbvias

### Fase de Análise (3–7 dias)

- [ ] Leis extraídas em texto (`leis_txt/*.txt`)
- [ ] Teto constitucional calculado para cada competência (variação anual)
- [ ] `T501_teto_constitucional.py` executado → servidores acima do teto identificados
- [ ] Rubricas de PSS cruzadas com editais → vantagens sem previsão identificadas
- [ ] Insalubridade/periculosidade verificada (laudo + base legal)
- [ ] FGC verificado (headcount vs cap do PCCV; datas vs LRF)
- [ ] FUNDEB verificado (proporção mínima 70% para magistério)
- [ ] Demais análises de domínio executadas conforme rubricas do município

### Fase de Relatório (2–3 dias)

- [ ] Todas as irregularidades documentadas em `.md` individuais
- [ ] Quantificação financeira por irregularidade revisada
- [ ] Jurisprudência pesquisada para achados críticos
- [ ] Relatório Word v1 gerado
- [ ] Revisão de linguagem aplicada (assertivo mas não peremptório)
- [ ] Revisão independente por auditor humano
- [ ] Versão final entregue

---

## 11. Métricas de Sucesso

| Métrica | Meta |
|---------|------|
| Cobertura de rubricas analisadas | > 80% do valor total da folha |
| Irregularidades com base legal citada | 100% |
| Quantificação financeira | 100% das irregularidades confirmadas |
| Tempo total do projeto | < 4 semanas |
| Custo de API | < USD $5 para municípios médios |
| Relatório Word entregável | Sim, sem revisão manual massiva |

---

## 12. Riscos e Mitigações

| Risco | Probabilidade | Mitigação |
|-------|--------------|-----------|
| Planilhas XLS com formato diferente | Alta | Inspecionar 2–3 arquivos antes de escrever o parser |
| Leis escaneadas ilegíveis (OCR ruim) | Média | Buscar versão digital no site da Câmara; fallback para transcrição manual da lei |
| Teto constitucional variável por período | Média | Calcular teto para cada ano (tabela de referência do STF) |
| Rubricas sem lei identificada | Alta | Usar orquestrador para gerar lista de leis a pesquisar |
| API Gemini instável (503) | Alta | Usar retry exponencial + fallback Flash (ver CLAUDE.md global) |
| Município usa sistema diferente de lotação | Média | Adaptar agrupamento por `cargo` ou `lotacao` conforme disponível |

---

## 13. Scripts a Copiar do Projeto Santa Luzia

```
santa-luzia/auditoria/scripts/
├── 01_consolidar_folhas.py       ← copiar e adaptar (regex competência, colunas)
├── 02_catalogo_gratificacoes.py  ← copiar sem alteração
├── 03_indicadores.py             ← copiar sem alteração
├── 04_grat_por_cargo.py          ← copiar sem alteração
├── 07b_buscar_leis_html.py       ← adaptar URL do site da Câmara municipal
├── 07d_ocr_leis.py               ← copiar sem alteração
├── 12_buscar_jurisprudencia.py   ← copiar e adaptar termos de busca
├── 14_preencher_template_docx.py ← adaptar template do relatório
├── 16b_gerar_relatorio_humanizado.py ← adaptar prompt de revisão
├── orquestrador_instrumentacao.py    ← copiar, adaptar gap detection
├── T501_teto_constitucional.py   ← adaptar valor do teto por Estado/período
└── T502–T505_*.py                ← adaptar rubrica-alvo para o novo município
```

---

## Referências

- **Projeto base:** `santa-luzia/` (auditoria validada, v15 entregue ao TCE)
- **CLAUDE.md global:** Regras de automação, Gemini CLI, retry pattern
- **SPEC.md do santa-luzia:** Diário de bordo com decisões e lições aprendidas
- **marco_normativo_completo.md:** Base legal completa reutilizável
- **TCU Jurisprudência:** https://contas.tcu.gov.br/juris
- **DataJud (CNJ):** https://datajud-wiki.cnj.jus.br
- **Tesseract OCR:** https://github.com/UB-Mannheim/tesseract/wiki

---

*Criado em 2026-06-14. Baseado no projeto Santa Luzia/MG (maio 2026).*
