# Auditoria de Custo da Folha — Saúde / Sete Lagoas (MG)

Agente autônomo que produz uma **análise gerencial de custo** (não-forense) da folha da
Secretaria de Saúde de Sete Lagoas (Fev/2026) como **dashboard HTML interativo** + narrativa.
Projetado para rodar **a noite inteira, sem supervisão**, na VPS Hermes.

## TL;DR

```bash
# Local — caminho determinístico (SEM nenhuma API), gera o dashboard:
python run_analysis.py
#   -> output/relatorio_custos_folha_saude_setelagoas.html

# Local — agente completo (usa Claude/Gemini se houver chave; senão degrada):
python -m agent.run_agent

# Deploy na Hermes + agendamento 01:00:
.\deploy\deploy.ps1            # (PowerShell, na pasta do projeto)
.\deploy\deploy.ps1 -RunNow    # roda já e acompanha os logs
.\deploy\monitor.ps1 -Pull     # de manhã: baixa e abre o dashboard
```

## Como funciona (resumo)

- **Núcleo determinístico** (`run_analysis.py` → `analysis/folha_tables.py` + `build_html.py`)
  calcula tudo e monta o dashboard **sem IA**. É o fallback garantido.
- **Agente noturno** (`agent/run_agent.py`) é um loop *tool-calling* sobre a API da Anthropic
  (roteador Claude), com ferramentas que chamam pandas, scraping de leis e **Gemini Flash**
  (classificação de rubricas) + **Opus** (1 síntese). Guardrails: teto de custo, máximo de
  iterações, wall-clock, checkpoint retomável, detector de repetição, degradação graciosa.
- **`finalize()`** sempre garante o entregável: se o LLM falhar, roda o caminho determinístico,
  escreve `RELATORIO_EXECUCAO.md` e notifica o Telegram.

## Modelos (híbrido)

| Etapa | Modelo | Observação |
|-------|--------|-----------|
| Roteador do loop | `claude-sonnet-4-6` | precisa de crédito Anthropic |
| Síntese narrativa | `claude-opus-4-8` → Gemini → fallback | 1 chamada |
| Classificar 151 rubricas | `gemini-2.5-flash` | barato, em lotes |
| Tudo o mais | determinístico (pandas) | ~80% do trabalho |

> Sem crédito na Anthropic, o agente **degrada automaticamente** para Gemini Flash +
> pipeline determinístico — e ainda entrega o dashboard com narrativa (fonte: gemini).

## Configuração

Copie `.env.example` para `.env` e preencha as chaves (no deploy, `remote_setup.sh` tenta
herdar `ANTHROPIC_API_KEY`/`GEMINI_API_KEY`/`TELEGRAM_BOT_TOKEN` de `/root/.hermes/.env`).

## Estrutura

```
auditoria-folha-sete-lagoas/
├── MISSION.md  requirements.md  design.md  tasks.md  plan.json   # documentos-base
├── run_analysis.py            # pipeline determinístico (fallback)
├── data/                      # folha limpa + agregados + dicionário
├── analysis/folha_tables.py   # tabelas (KPIs, Gini, vínculo, faixas, top, alertas, rubricas)
├── analysis/build_html.py     # dashboard (#pessoal + #legislacao)
├── agent/                     # run_agent, llm, gemini_client, tools, legislacao, synth, budget, checkpoint, progress
├── deploy/                    # systemd unit+timer, deploy.ps1, monitor.ps1, remote_setup.sh
└── output/                    # relatorio_custos_folha_saude_setelagoas.html
```

## Verificação matinal

`RELATORIO_EXECUCAO.md` → status SUCESSO/PARCIAL, custo de API, cobertura legal, lacunas.
`progress.jsonl` → uma linha por passo. Dashboard em `output/`.
