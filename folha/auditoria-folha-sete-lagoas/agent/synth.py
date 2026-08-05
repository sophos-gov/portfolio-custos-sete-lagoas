"""Síntese narrativa (Opus → Gemini → fallback determinístico). Gera insights.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import config
from . import cheap
from .llm import Claude

sys.path.insert(0, str(config.BASE / "analysis"))
import build_html  # noqa: E402

_SYSTEM = (
    "Você é um consultor sênior de gestão pública analisando o CUSTO da folha da "
    "Secretaria de Saúde de Sete Lagoas (MG). Faça análise gerencial (NÃO forense): "
    "nunca use a palavra 'ilegal'. Seja específico com números. Responda só JSON."
)


def _prompt(dados: dict, leg: dict | None) -> str:
    payload = {
        "kpis": dados.get("kpis", {}),
        "por_vinculo": dados.get("por_vinculo", []),
        "faixas": dados.get("faixas", []),
        "top_unidades": dados.get("top_unidades", [])[:10],
        "top_cargos": dados.get("top_cargos", [])[:10],
        "rubricas_top": dados.get("rubricas_top", [])[:12],
        "rubricas_pareto": dados.get("rubricas_pareto", {}),
        "n_alertas": len(dados.get("alertas", [])),
        "legislacao_por_grupo": (leg or {}).get("por_grupo", [])[:8],
        "legislacao_por_lei": (leg or {}).get("por_lei", [])[:8],
        "legislacao_cobertura_pct": (leg or {}).get("cobertura_valor_pct"),
    }
    return (
        "DADOS:\n" + json.dumps(payload, ensure_ascii=False, indent=2) +
        "\n\nRetorne EXATAMENTE este JSON (sem markdown):\n"
        "{\n"
        '  "action_title": "frase executiva de até 24 palavras com o número mais relevante",\n'
        '  "analise_folha": "2-3 frases sobre distribuição, média/mediana, Gini, taxa de desconto",\n'
        '  "cruzamento": "2-3 frases cruzando temporário vs efetivo E folha vs legislação (custo por lei/grupo)",\n'
        '  "alertas": ["3 a 5 pontos de atenção factuais, com números"],\n'
        '  "recomendacoes": ["3 a 5 recomendações de gestão acionáveis"]\n'
        "}"
    )


def _via_cheap(dados: dict, leg: dict | None) -> dict | None:
    if not cheap.cheap_available():
        return None
    txt = cheap.gen_text(_SYSTEM + "\n\n" + _prompt(dados, leg), temperature=0.3)
    if not txt:
        return None
    import re
    txt = re.sub(r"^```(?:json)?|```$", "", txt.strip(), flags=re.MULTILINE).strip()
    try:
        d = json.loads(txt)
        d["_fonte"] = "llm_barato"
        return d
    except Exception:
        return None


def synthesize(dados: dict, leg: dict | None, claude: Claude | None,
               out: Path | None = None) -> dict:
    """Tenta Opus → Gemini → fallback determinístico. Sempre retorna um dict válido."""
    insights = None
    if claude and claude.available():
        d = claude.complete_json(config.SYNTH_MODEL, _SYSTEM, _prompt(dados, leg), max_tokens=2000)
        if d and d.get("action_title"):
            d["_fonte"] = "opus"
            insights = d
    if insights is None:
        insights = _via_cheap(dados, leg)
    if insights is None:
        insights = build_html.narrativa_fallback(dados)

    # validação mínima de schema
    for k in ("action_title", "analise_folha", "cruzamento"):
        insights.setdefault(k, "")
    insights.setdefault("alertas", [])
    insights.setdefault("recomendacoes", [])

    out = out or (config.TABELAS_DIR / "insights.json")
    Path(out).write_text(json.dumps(insights, ensure_ascii=False, indent=2), encoding="utf-8")
    return insights
