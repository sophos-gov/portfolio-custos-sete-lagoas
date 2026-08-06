# Tasks — Checklist do Agente (espelha plan.json)

O agente é autônomo na *ordem* e no *como*, mas a *fronteira* é esta lista fechada.

| ID  | Tarefa | Ferramenta | Critério de pronto |
|-----|--------|-----------|--------------------|
| T01 | Carregar e validar dados | `compute_tables` | dados_consolidados.json; n_ativos>2000; reconciliação <3% |
| T02 | KPIs + Gini | `compute_tables` | kpis_folha.json; Gini∈[0,3;0,8] |
| T03 | Custo por vínculo | `compute_tables` | por_vinculo.csv (TEMPORARIO×EFETIVO) |
| T04 | Distribuição por faixas | `compute_tables` | distribuicao_faixas.csv |
| T05 | Top unidades | `compute_tables` | top_unidades.csv |
| T06 | Top cargos | `compute_tables` | top_cargos.csv |
| T07 | Alertas / outliers | `compute_tables` | alertas_folha.csv; elite>20k≥1 |
| T08 | Concentração de rubricas + Pareto | `compute_tables` | rubricas_top.csv; rubricas_pareto.json |
| T09 | Descobrir leis citadas | `discover_laws` | leis_alvo.json |
| T10 | Baixar texto das leis (best-effort) | `fetch_laws` | cache parcial OK |
| T11 | Classificar rubricas → lei/grupo/propósito | `classify_rubricas` (Flash) | rubricas_legislacao.json; cobertura≥70% |
| T12 | Síntese narrativa | `synthesize_narrative` (Opus→Gemini→fallback) | insights.json |
| T13 | Montar dashboard HTML | `build_dashboard` | HTML<2,5MB; #pessoal+#legislacao |
| T14 | Autoverificação | `self_check` | sem lacunas críticas |
| T15 | Notificar conclusão | `notify_telegram` | mensagem enviada |

> `compute_tables` cumpre T01–T08 de uma vez (é idempotente). O agente pode marcá-las juntas.
