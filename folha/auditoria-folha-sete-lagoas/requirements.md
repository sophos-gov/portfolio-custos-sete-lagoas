# Requirements — Análise de Custo da Folha (Saúde / Sete Lagoas)

## Objetivo
Análise **gerencial** (não-forense) do custo da folha da Secretaria de Saúde de Sete Lagoas (MG),
competência Fev/2026, entregue como **dashboard HTML interativo** + narrativa executiva,
produzida por um **agente autônomo** rodando à noite na VPS Hermes.

## Escopo (in)
- Perfil de custo: KPIs, média/mediana, **Gini**, taxa de desconto.
- **Vínculo**: contraste temporário (≈2/3 do custo) × efetivo.
- Distribuição por **faixas** de remuneração; **outliers** (elite > R$ 20k, desconto > 50%, IQR por cargo).
- **Top unidades** e **top cargos** por custo.
- **Concentração de rubricas** (Pareto) + **classificação legal** (rubrica → lei criadora → propósito → custo por lei/grupo).
- Narrativa executiva (Opus → Gemini → fallback determinístico).

## Fora de escopo (out)
- **Não é auditoria forense.** Nada de "ilegal", teto constitucional, jurisprudência, relatório para TCE.
- A legislação serve **apenas** para explicar/classificar o custo das rubricas.

## Fontes de dados (`data/`)
- `folha_2026_02_rubricas_long.csv` (primário; 35.435 linhas, 3.260 servidores).
- `agg_por_unidade.csv`, `agg_por_cargo.csv`, `agg_por_categoria.csv` (atalhos agregados).
- `dicionario_rubricas.csv` (151 rubricas → descoberta de leis).

## Requisitos não-funcionais
- HTML **standalone < 2,5 MB**, Chart.js v4 (CDN), valores em padrão BR.
- **Fallback sem API obrigatório**: `run_analysis.py` produz dashboard válido sem nenhuma chamada de IA.
- Custo de API alvo **< US$ 3**; execução **< 4 h**.
- Robustez overnight: retry/fallback, checkpoint retomável, degradação graciosa, log estruturado.

## Critérios de aceitação
- 3.215 ± servidores ativos; bruto ≈ R$ 20,4 mi; Gini ∈ [0,3; 0,8]; ≥ 1 elite > R$ 20k.
- Cobertura legal ≥ 70% do **valor** da folha.
- `RELATORIO_EXECUCAO.md` com status; notificação Telegram enviada.
