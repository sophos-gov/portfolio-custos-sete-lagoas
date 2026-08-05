"""Ferramentas do agente (tool-use). Cada tool é idempotente e degrada graciosamente."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import config
from . import legislacao
from . import sapl
from . import synth

sys.path.insert(0, str(config.BASE / "analysis"))
import folha_tables  # noqa: E402
import build_html    # noqa: E402


# ---------------------------------------------------------------------------
# Schemas (formato Anthropic tool-use)
# ---------------------------------------------------------------------------
TOOLS = [
    {"name": "read_data",
     "description": "Inspeciona os dados disponíveis (arquivos em data/ e KPIs já calculados, se houver). Use para se orientar.",
     "input_schema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "compute_tables",
     "description": "Executa toda a análise determinística da folha (KPIs, Gini, vínculo, faixas, top unidades/cargos, alertas, concentração de rubricas) e grava as tabelas. Idempotente.",
     "input_schema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "discover_laws",
     "description": "Descobre, a partir das descrições das rubricas, quais leis municipais (LC/Lei) precisam ser consultadas. Determinístico.",
     "input_schema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "fetch_laws",
     "description": "Tenta baixar (best-effort, cacheado) o texto das leis. O texto é enriquecimento OPCIONAL; a identificação da lei já vem das descrições.",
     "input_schema": {"type": "object", "properties": {
         "lei_ids": {"type": "array", "items": {"type": "string"},
                     "description": "IDs de lei (ex.: 'LC 190/16'). Vazio = todas as descobertas."}},
         "additionalProperties": False}},
    {"name": "classify_rubricas",
     "description": "Classifica cada rubrica em grupo + lei criadora + propósito e agrega o custo por lei e por grupo (usa modelo barato se disponível). Gera rubricas_legislacao.json.",
     "input_schema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "synthesize_narrative",
     "description": "Gera a narrativa executiva (action title, análise, cruzamento, alertas, recomendações) com o modelo de síntese. Gera insights.json.",
     "input_schema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "build_dashboard",
     "description": "Monta o dashboard HTML final a partir de todas as tabelas e da narrativa. Idempotente.",
     "input_schema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "mark_task_done",
     "description": "Marca uma tarefa do plano (plan.json) como concluída, registrando a evidência.",
     "input_schema": {"type": "object", "properties": {
         "task_id": {"type": "string"}, "evidence": {"type": "string"}},
         "required": ["task_id"], "additionalProperties": False}},
    {"name": "self_check",
     "description": "Confere os artefatos contra os critérios de pronto (done-criteria) e retorna as lacunas pendentes.",
     "input_schema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "notify_telegram",
     "description": "Envia uma mensagem de status/conclusão ao Telegram (best-effort).",
     "input_schema": {"type": "object", "properties": {"message": {"type": "string"}},
                      "required": ["message"], "additionalProperties": False}},
    {"name": "finish",
     "description": "Encerra a missão. Use somente após self_check sem lacunas críticas e o dashboard construído.",
     "input_schema": {"type": "object", "properties": {"summary": {"type": "string"}},
                      "required": ["summary"], "additionalProperties": False}},
]


# ---------------------------------------------------------------------------
# Implementações
# ---------------------------------------------------------------------------
def _load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _ensure_tables() -> dict:
    p = config.TABELAS_DIR / "dados_consolidados.json"
    if not p.exists():
        return folha_tables.gerar_tudo(config.DATA_DIR, config.TABELAS_DIR)
    return _load_json(p)


def t_read_data(_inp, ctx) -> dict:
    files = sorted(f.name for f in config.DATA_DIR.glob("*") if f.is_file())
    dados = _load_json(config.TABELAS_DIR / "dados_consolidados.json")
    return {"data_files": files,
            "tables_computed": dados is not None,
            "kpis": dados.get("kpis") if dados else None}


def t_compute_tables(_inp, ctx) -> dict:
    dados = folha_tables.gerar_tudo(config.DATA_DIR, config.TABELAS_DIR)
    ctx["dados"] = dados
    k = dados["kpis"]
    return {"ok": True, "n_ativos": k["n_ativos"], "proventos_total": k["proventos_total"],
            "gini": k["gini_proventos"], "elite_20k": k["elite_acima_20k"]["n"],
            "n_alertas": len(dados["alertas"]), "reconciliacao": dados["reconciliacao"]}


def t_discover_laws(_inp, ctx) -> dict:
    leis = legislacao.discover_laws()
    return {"n_leis": len(leis), "lei_ids": [l["lei_id"] for l in leis]}


def t_fetch_laws(inp, ctx) -> dict:
    legislacao.discover_laws()
    res = sapl.enrich_laws()  # SAPL API (pure-requests): ementa + download do texto integral
    return {"n_leis": res["n_leis"], "n_localizadas": res["n_localizadas"], "fonte": res["fonte"]}


def t_classify_rubricas(_inp, ctx) -> dict:
    res = legislacao.classify_rubricas(use_flash=True)
    return {"metodo": res["metodo"], "cobertura_valor_pct": res["cobertura_valor_pct"],
            "n_leis": len(res["por_lei"]), "n_grupos": len(res["por_grupo"]),
            "top_grupos": [(g["grupo"], g["valor_total"]) for g in res["por_grupo"][:5]]}


def t_synthesize(_inp, ctx) -> dict:
    dados = _ensure_tables()
    leg = _load_json(config.TABELAS_DIR / "rubricas_legislacao.json")
    insights = synth.synthesize(dados, leg, ctx.get("claude"))
    return {"fonte": insights.get("_fonte"), "action_title": insights.get("action_title", "")[:160]}


def t_build_dashboard(_inp, ctx) -> dict:
    _ensure_tables()
    html = build_html.build(config.TABELAS_DIR, config.OUTPUT_HTML)
    kb = html.stat().st_size / 1024
    return {"ok": True, "path": str(html), "size_kb": round(kb, 1)}


def t_mark_task_done(inp, ctx) -> dict:
    plan = _load_json(config.PLAN_FILE) or {"tasks": []}
    tid = inp.get("task_id")
    found = False
    for tarefa in plan.get("tasks", []):
        if tarefa.get("id") == tid:
            tarefa["status"] = "done"
            tarefa["evidence"] = inp.get("evidence", "")
            found = True
    config.PLAN_FILE.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": found, "task_id": tid}


def t_self_check(_inp, ctx) -> dict:
    gaps = []
    dados = _load_json(config.TABELAS_DIR / "dados_consolidados.json")
    if not dados:
        gaps.append("dados_consolidados.json ausente (rodar compute_tables)")
    else:
        g = dados["kpis"]["gini_proventos"]
        if not (0.3 <= g <= 0.8):
            gaps.append(f"Gini {g} fora de [0.3, 0.8]")
        if dados["kpis"]["elite_acima_20k"]["n"] < 1:
            gaps.append("nenhum alerta de elite > 20k")
    leg = _load_json(config.TABELAS_DIR / "rubricas_legislacao.json")
    if not leg:
        gaps.append("rubricas_legislacao.json ausente (rodar classify_rubricas)")
    elif leg.get("cobertura_valor_pct", 0) < 70:
        gaps.append(f"cobertura legal {leg.get('cobertura_valor_pct')}% < 70%")
    if not (config.TABELAS_DIR / "insights.json").exists():
        gaps.append("insights.json ausente (rodar synthesize_narrative)")
    if not config.OUTPUT_HTML.exists():
        gaps.append("dashboard HTML não construído (rodar build_dashboard)")
    else:
        kb = config.OUTPUT_HTML.stat().st_size / 1024
        if kb >= 2560:
            gaps.append(f"HTML {kb:.0f} KB acima de 2,5 MB")
    return {"ok": len(gaps) == 0, "gaps": gaps}


def t_notify_telegram(inp, ctx) -> dict:
    msg = inp.get("message", "Auditoria da folha concluída.")
    if not config.TELEGRAM_BOT_TOKEN:
        return {"ok": False, "reason": "TELEGRAM_BOT_TOKEN ausente"}
    try:
        import requests
        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
        r = requests.post(url, json={"chat_id": config.TELEGRAM_CHAT_ID, "text": msg[:4000]}, timeout=15)
        return {"ok": r.status_code == 200, "status_code": r.status_code}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


DISPATCH = {
    "read_data": t_read_data,
    "compute_tables": t_compute_tables,
    "discover_laws": t_discover_laws,
    "fetch_laws": t_fetch_laws,
    "classify_rubricas": t_classify_rubricas,
    "synthesize_narrative": t_synthesize,
    "build_dashboard": t_build_dashboard,
    "mark_task_done": t_mark_task_done,
    "self_check": t_self_check,
    "notify_telegram": t_notify_telegram,
}


def dispatch(name: str, inp: dict, ctx: dict) -> dict:
    fn = DISPATCH.get(name)
    if not fn:
        return {"error": f"ferramenta desconhecida: {name}"}
    try:
        return fn(inp or {}, ctx)
    except Exception as e:
        import traceback
        return {"error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-800:]}
