#!/usr/bin/env python3
"""
run_agent.py — Loop agêntico noturno (agêntico DENTRO de um checklist fixo).

Roteador = Claude (ROUTER_MODEL) com tool-use; ferramentas chamam pandas / scraping /
Gemini Flash / Opus. Guardrails: teto USD, max iterações, wall-clock, detector de
repetição, checkpoint por passo. finalize() SEMPRE garante o dashboard (caminho
determinístico), mesmo que o LLM esteja indisponível.

Retomável: se houver checkpoints/state.json, retoma de onde parou.
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone

# stdout/stderr robustos a UTF-8 (Windows cp1252 quebraria com emojis/acentos)
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from . import config
from . import checkpoint
from . import progress
from . import tools as T
from .budget import Budget
from .llm import Claude

KICKOFF = (
    "Inicie a missão de análise de CUSTO da folha da Saúde de Sete Lagoas. "
    "Trabalhe pelas tarefas do plano (compute_tables → discover_laws → fetch_laws → "
    "classify_rubricas → synthesize_narrative → build_dashboard → self_check → finish). "
    "Decida a ordem e use as ferramentas. Ao concluir sem lacunas no self_check, chame finish."
)


def _system() -> str:
    if config.MISSION_FILE.exists():
        return config.MISSION_FILE.read_text(encoding="utf-8")
    return ("Você é um agente autônomo que produz um dashboard de custo da folha da Saúde "
            "de Sete Lagoas. Use as ferramentas; nunca invente dados; análise gerencial, não forense.")


def _content_to_dicts(content) -> list:
    out = []
    for b in content:
        t = getattr(b, "type", "")
        if t == "text":
            out.append({"type": "text", "text": b.text})
        elif t == "tool_use":
            out.append({"type": "tool_use", "id": b.id, "name": b.name, "input": b.input})
    return out


def ensure_deliverable(ctx: dict) -> dict:
    """Garante todos os artefatos por caminho determinístico (rede de segurança)."""
    import sys
    sys.path.insert(0, str(config.BASE / "analysis"))
    import folha_tables, build_html  # noqa: E402
    from . import legislacao, synth, sapl, analise_leis   # noqa: E402

    steps = []
    if not (config.TABELAS_DIR / "dados_consolidados.json").exists():
        folha_tables.gerar_tudo(config.DATA_DIR, config.TABELAS_DIR); steps.append("compute_tables")
    dados = json.loads((config.TABELAS_DIR / "dados_consolidados.json").read_text(encoding="utf-8"))
    if not (config.TABELAS_DIR / "rubricas_legislacao.json").exists():
        legislacao.discover_laws()
        try:
            sapl.enrich_laws()  # baixa ementas/leis do SAPL (best-effort, pure-requests)
            steps.append("sapl_enrich")
        except Exception as e:
            print(f"[ensure] sapl_enrich falhou (segue sem texto de lei): {e}")
        legislacao.classify_rubricas(use_flash=True); steps.append("classify_rubricas")
    if not (config.TABELAS_DIR / "analise_legislacao.json").exists():
        try:
            analise_leis.analisar()  # lê o texto das leis e cruza com a folha (DeepSeek/Gemini)
            steps.append("analise_leis")
        except Exception as e:
            print(f"[ensure] analise_leis falhou (segue sem análise textual): {e}")
    leg = json.loads((config.TABELAS_DIR / "rubricas_legislacao.json").read_text(encoding="utf-8"))
    if not (config.TABELAS_DIR / "insights.json").exists():
        synth.synthesize(dados, leg, ctx.get("claude")); steps.append("synthesize")
    build_html.build(config.TABELAS_DIR, config.OUTPUT_HTML); steps.append("build_dashboard")
    return {"steps_deterministicos": steps}


def finalize(ctx: dict, budget: Budget, motivo: str):
    progress.log("finalize_inicio", motivo=motivo, usd=round(budget.usd_spent, 4))
    try:
        safety = ensure_deliverable(ctx)
    except Exception as e:
        safety = {"erro": str(e)}
    check = T.t_self_check({}, ctx)
    leg = T._load_json(config.TABELAS_DIR / "rubricas_legislacao.json") or {}
    dados = T._load_json(config.TABELAS_DIR / "dados_consolidados.json") or {}
    kpis = dados.get("kpis", {})
    html_kb = (config.OUTPUT_HTML.stat().st_size / 1024) if config.OUTPUT_HTML.exists() else 0

    status = "SUCESSO" if check.get("ok") else "PARCIAL"
    rel = [
        f"# Relatório de Execução — Auditoria Folha Saúde / Sete Lagoas",
        f"\n**Status:** {status}  ",
        f"**Motivo de encerramento:** {motivo}  ",
        f"**Gerado em:** {datetime.now(timezone.utc).isoformat(timespec='seconds')}  ",
        f"\n## Resultado",
        f"- Servidores ativos: {kpis.get('n_ativos','?')}",
        f"- Custo bruto: R$ {kpis.get('proventos_total','?'):,}" if kpis else "- Custo bruto: ?",
        f"- Gini: {kpis.get('gini_proventos','?')}",
        f"- Elite > R$20k: {kpis.get('elite_acima_20k',{}).get('n','?')}",
        f"- Cobertura legal (por valor): {leg.get('cobertura_valor_pct','?')}% ({leg.get('metodo','?')})",
        f"- Dashboard: {config.OUTPUT_HTML.name} ({html_kb:.0f} KB)",
        f"\n## Custo de API",
        f"```json\n{json.dumps(budget.to_dict(), ensure_ascii=False, indent=2)}\n```",
        f"\n## Lacunas (self_check)",
        ("- nenhuma" if check.get("ok") else "\n".join(f"- {g}" for g in check.get("gaps", []))),
        f"\n## Rede de segurança determinística\n```json\n{json.dumps(safety, ensure_ascii=False)}\n```",
    ]
    config.RELATORIO_EXEC.write_text("\n".join(rel), encoding="utf-8")

    msg = (f"✅ Auditoria folha Saúde/Sete Lagoas — {status}\n"
           f"Ativos: {kpis.get('n_ativos','?')} | Bruto: R$ {kpis.get('proventos_total',0):,.0f}\n"
           f"Gini: {kpis.get('gini_proventos','?')} | Elite>20k: {kpis.get('elite_acima_20k',{}).get('n','?')}\n"
           f"Cobertura legal: {leg.get('cobertura_valor_pct','?')}%\n"
           f"Custo API: US$ {budget.usd_spent:.3f} | HTML: {html_kb:.0f}KB\n"
           f"Arquivo: {config.OUTPUT_HTML}")
    notif = T.t_notify_telegram({"message": msg}, ctx)
    progress.log("finalize_fim", status=status, telegram_ok=notif.get("ok"),
                 usd=round(budget.usd_spent, 4), html_kb=round(html_kb, 1))
    checkpoint.clear()
    print("\n" + "=" * 60 + f"\n{status} — {motivo}\n" + msg + "\n" + "=" * 60)


def run():
    start = time.time()
    ckpt = checkpoint.load()
    if ckpt:
        budget = Budget.from_dict(ckpt.get("budget", {}))
        history = ckpt.get("history", [])
        it = ckpt.get("iter", 0)
        progress.log("retomada", iter=it, usd=round(budget.usd_spent, 4))
    else:
        budget = Budget()
        history = [{"role": "user", "content": KICKOFF}]
        it = 0
        progress.log("inicio", router=config.ROUTER_MODEL, synth=config.SYNTH_MODEL,
                     usd_budget=config.USD_BUDGET, max_iter=config.MAX_ITERATIONS)

    claude = Claude(budget)
    ctx = {"claude": claude, "budget": budget}

    # Sem Anthropic → caminho 100% determinístico
    if not claude.available():
        progress.log("sem_anthropic", info="executando pipeline determinístico")
        finalize(ctx, budget, motivo="anthropic_indisponivel_pipeline_deterministico")
        return

    repeticoes = Counter()
    sem_tool = 0
    system = _system()

    while True:
        # ---- Guardrails ----
        if budget.exceeded():
            return finalize(ctx, budget, "budget_usd_excedido")
        if it >= config.MAX_ITERATIONS:
            return finalize(ctx, budget, "max_iteracoes")
        if time.time() - start > config.MAX_WALL_SECONDS:
            return finalize(ctx, budget, "wall_clock")

        it += 1
        resp = claude.create(config.ROUTER_MODEL, system, history, tools=T.TOOLS, max_tokens=1500)
        if resp is None:
            return finalize(ctx, budget, "claude_indisponivel_durante_loop")

        history.append({"role": "assistant", "content": _content_to_dicts(resp.content)})
        tool_uses = [b for b in resp.content if getattr(b, "type", "") == "tool_use"]

        if resp.stop_reason != "tool_use" or not tool_uses:
            sem_tool += 1
            if sem_tool >= 2:
                return finalize(ctx, budget, "sem_chamadas_de_ferramenta")
            history.append({"role": "user", "content":
                            "Use as ferramentas para avançar a missão ou chame finish quando concluir."})
            checkpoint.save({"history": history, "budget": budget.to_dict(), "iter": it})
            continue
        sem_tool = 0

        results = []
        done = False
        for tu in tool_uses:
            key = f"{tu.name}:{json.dumps(tu.input, sort_keys=True, default=str)}"
            repeticoes[key] += 1
            if tu.name == "finish":
                done = True
                results.append({"type": "tool_result", "tool_use_id": tu.id,
                                "content": "Missão encerrada pelo agente."})
                continue
            if repeticoes[key] > 3:
                results.append({"type": "tool_result", "tool_use_id": tu.id,
                                "content": json.dumps({"skip": "chamada repetida demais; avance para a próxima etapa ou finish"})})
                progress.log("repeticao_bloqueada", tool=tu.name)
                continue

            t0 = time.time()
            out = T.dispatch(tu.name, tu.input, ctx)
            progress.log("tool", tool=tu.name, ms=int((time.time() - t0) * 1000),
                         usd=round(budget.usd_spent, 4), ok=("error" not in out))
            results.append({"type": "tool_result", "tool_use_id": tu.id,
                            "content": json.dumps(out, ensure_ascii=False, default=str)[:4000]})

        history.append({"role": "user", "content": results})
        checkpoint.save({"history": history, "budget": budget.to_dict(), "iter": it})

        if done:
            return finalize(ctx, budget, "concluido_pelo_agente")


if __name__ == "__main__":
    run()
