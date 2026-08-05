# Design — Harness Agêntico + Pipeline de Análise

## Camadas
```
run_analysis.py            # caminho 100% determinístico (sem IA) — fallback obrigatório
  └─ analysis/folha_tables.py   # tabelas (KPIs, Gini, vínculo, faixas, top, alertas, rubricas)
  └─ analysis/build_html.py     # dashboard HTML (#pessoal + #legislacao) + narrativa fallback

agent/run_agent.py         # loop agêntico (agêntico DENTRO do checklist do plan.json)
  ├─ llm.py                # Claude (Anthropic) com retry + budget
  ├─ gemini_client.py      # Gemini Flash (retry + fallback), init lazy/graceful
  ├─ tools.py              # ferramentas tool-use (idempotentes, com prereqs)
  ├─ legislacao.py         # discover_laws / fetch_law / classify_rubricas
  ├─ synth.py              # narrativa: Opus → Gemini → fallback determinístico
  ├─ budget.py             # acumulador USD/tokens + teto rígido
  ├─ checkpoint.py         # estado retomável (atômico, com .bak)
  └─ progress.py           # progress.jsonl append-only
```

## Loop (run_agent.run)
1. Retoma de `checkpoints/state.json` se existir.
2. Se Anthropic indisponível → vai direto para `finalize` (pipeline determinístico + Gemini).
3. A cada iteração: guardrails (budget/iterações/wall-clock) → `claude.create(ROUTER, tools)` →
   despacha tool_use → `tool_result` → **checkpoint**. Detector de repetição (mesma tool+args 3×).
4. `finish` ou limite → `finalize`.

## finalize (rede de segurança)
`ensure_deliverable()` roda deterministicamente qualquer artefato faltante (tabelas → legislação →
síntese → HTML), depois `self_check`, escreve `RELATORIO_EXECUCAO.md` e notifica o Telegram.
**Garante o dashboard mesmo se o LLM nunca rodar.**

## Roteamento de modelo (fixo no dispatch)
- Determinístico (pandas/I/O): ~80% das ferramentas, sem modelo.
- **Gemini Flash**: `classify_rubricas` (lotes) + narrativa de fallback.
- **Claude Sonnet**: roteador do loop + `self_check` (quando há crédito).
- **Claude Opus**: só `synthesize_narrative` (1 chamada).

## Decisões-chave
- Dados já vêm classificados (`categoria_vinculo`, `nome_unidade`) → consumir o LONG, não reconstruir.
- Identificação da lei vem das **descrições** das rubricas (confiável); o **texto** scrapeado é opcional.
- Rubricas de provento = código não-`R` e fora de `{0500,1952,1959,1960}`; reconciliação validada (~1%).
- Checkpoints idempotentes; `compute_tables`/`build_dashboard` podem rodar quantas vezes for preciso.

## Contratos de I/O
- `analysis/tabelas/dados_consolidados.json` — payload central (KPIs, tabelas, alertas, reconciliação).
- `analysis/tabelas/rubricas_legislacao.json` — cobertura, por_lei, por_grupo, rubricas[].
- `analysis/tabelas/insights.json` — action_title, analise_folha, cruzamento, alertas[], recomendacoes[], _fonte.
- `output/relatorio_custos_folha_saude_setelagoas.html` — entregável final.
