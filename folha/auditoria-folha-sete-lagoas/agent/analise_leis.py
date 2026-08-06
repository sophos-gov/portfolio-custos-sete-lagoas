"""
Análise do TEXTO das leis cruzado com a folha.

Lê o texto integral de cada lei baixada (PDF via PyMuPDF; .doc/.bin via texto extraído
salvo em <slug>.txt — gerado por WebFetch nesta máquina), agrupa as rubricas de cada
lei com seu custo real, e usa um LLM barato (DeepSeek→Gemini) para produzir uma análise
objetiva: o que a lei institui e como isso aparece no custo da folha.

Gera: analysis/tabelas/analise_legislacao.json + analise_legislacao.md
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from . import config
from . import deepseek_client, gemini_client


def _slug(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFKD", str(s)) if not unicodedata.combining(c))
    return re.sub(r"[^\w]+", "_", s).strip("_").lower()


def _texto_pdf(path: Path) -> str:
    try:
        import fitz
        doc = fitz.open(path)
        t = "\n".join(p.get_text() for p in doc)
        doc.close()
        return re.sub(r"\n{3,}", "\n\n", t).strip()
    except Exception:
        return ""


def _texto_docx(path: Path) -> str:
    try:
        import docx
        d = docx.Document(str(path))
        return "\n".join(p.text for p in d.paragraphs).strip()
    except Exception:
        return ""


def _texto_lei(lei_id: str, arquivo_local: str | None) -> tuple[str, str]:
    """Retorna (texto, fonte). Prioriza .txt (WebFetch) > PDF (fitz) > DOCX (python-docx) > vazio."""
    slug = _slug(lei_id)
    for base in (config.CACHE_DIR, config.SEED_DIR):
        txt_file = base / f"{slug}.txt"
        if txt_file.exists() and txt_file.stat().st_size > 200:
            return txt_file.read_text(encoding="utf-8", errors="replace"), "texto_extraido"
    if arquivo_local:
        p = Path(arquivo_local)
        if p.exists():
            if p.suffix.lower() == ".pdf":
                t = _texto_pdf(p)
                if len(t) > 200:
                    return t, "pdf"
            # .docx (às vezes salvo como .bin); .doc binário antigo não é parseável aqui
            t = _texto_docx(p)
            if len(t) > 200:
                return t, "docx"
    return "", "ementa"


def _gen(prompt: str) -> str | None:
    # DeepSeek primeiro (estável, sem rate limit); depois Gemini
    r = deepseek_client.gen_text(prompt, temperature=0.2, max_tokens=400)
    if r:
        return r
    return gemini_client.gen_text(prompt, max_retries=2, generation_config={"temperature": 0.2})


def analisar() -> dict:
    leg_path = config.TABELAS_DIR / "rubricas_legislacao.json"
    resumo_path = config.TABELAS_DIR / "leis_resumo.json"
    if not leg_path.exists():
        raise FileNotFoundError("rubricas_legislacao.json ausente (rode classify_rubricas)")
    leg = json.loads(leg_path.read_text(encoding="utf-8"))
    resumo = json.loads(resumo_path.read_text(encoding="utf-8")).get("leis", {}) if resumo_path.exists() else {}

    # agrupar rubricas por lei
    by_lei: dict[str, list] = {}
    for r in leg["rubricas"]:
        by_lei.setdefault(r["lei_criadora"], []).append(r)

    analises = []
    for lei in leg["por_lei"]:
        lid = lei["lei_id"]
        sapl = resumo.get(lid, {})
        ementa = sapl.get("ementa", "")
        texto, fonte = _texto_lei(lid, sapl.get("arquivo_local"))
        rubricas = sorted(by_lei.get(lid, []), key=lambda x: -x["valor_total"])[:12]
        rub_txt = "\n".join(
            f'- {x["codigo"]} {x["descricao"]}: R$ {x["valor_total"]:,.0f} ({x["n_servidores"]} serv.)'
            for x in rubricas)

        prompt = (
            "Você é analista de custos da folha pública (Secretaria de Saúde de Sete Lagoas). "
            "Análise GERENCIAL, não forense — nunca diga 'ilegal'.\n\n"
            f"LEI: {lid}\nEMENTA OFICIAL: {ementa}\n\n"
            f"TEXTO DA LEI (trecho):\n{texto[:6000] if texto else '(texto integral não disponível em formato legível; baseie-se na ementa e nas rubricas)'}\n\n"
            f"RUBRICAS DESTA LEI NA FOLHA (Fev/2026) E CUSTO:\n{rub_txt or '(sem rubricas mapeadas)'}\n"
            f"Custo total desta lei na folha: R$ {lei['valor_total']:,.0f} em {lei['n_rubricas']} rubrica(s).\n\n"
            "Escreva 2 a 3 frases objetivas em PT-BR: (1) o que a lei institui; "
            "(2) como isso aparece no custo da folha (cite percentuais/artigos do texto se houver). "
            "Responda apenas o texto da análise."
        )
        analise = _gen(prompt) or ementa or lei.get("proposito", "")
        analises.append({
            "lei_id": lid, "valor_total": lei["valor_total"], "n_rubricas": lei["n_rubricas"],
            "fonte_texto": fonte, "ementa": ementa, "analise": analise.strip(),
        })

    metodo = "deepseek/gemini" if (deepseek_client.deepseek_available() or gemini_client.gemini_available()) else "sem_llm"
    out = {"metodo": metodo, "n_leis": len(analises), "analises": analises}
    (config.TABELAS_DIR / "analise_legislacao.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    md = ["# Análise da Legislação × Custo da Folha (Saúde / Sete Lagoas)\n"]
    for a in analises:
        md.append(f"## {a['lei_id']} — R$ {a['valor_total']:,.0f} ({a['n_rubricas']} rubricas) "
                  f"[fonte: {a['fonte_texto']}]\n")
        if a["ementa"]:
            md.append(f"*Ementa:* {a['ementa']}\n")
        md.append(f"{a['analise']}\n")
    config.RELATORIO_EXEC.parent.joinpath("analise_legislacao.md").write_text(
        "\n".join(md), encoding="utf-8")
    return out


if __name__ == "__main__":
    res = analisar()
    print(f"Análise legislativa: {res['n_leis']} leis ({res['metodo']})")
    for a in res["analises"][:6]:
        print(f"\n[{a['lei_id']}] (fonte: {a['fonte_texto']}, R$ {a['valor_total']:,.0f})")
        print("  " + (a["analise"][:240].replace("\n", " ")))
