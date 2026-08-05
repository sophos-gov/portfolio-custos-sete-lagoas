# -*- coding: utf-8 -*-
"""
brief_juridico.py — BRIEF JURÍDICO por tese (A1–A5) usando DeepSeek.

Agora que o acervo tem ~299 leis (todas as LCs do município + ordinárias citadas),
não cabe tudo num contexto. Estratégia (DeepSeek, 64K):
  1. Lê o catálogo (_catalogo_leis.json) e seleciona as leis RELEVANTES a servidores
     por palavras-chave na ementa + leis-núcleo conhecidas (Estatuto, PCCV, gratificações).
  2. Para cada lei selecionada, 1 chamada DeepSeek extrai dispositivos relevantes às
     teses A1–A5 (cita artigos; "nada relevante" se for o caso).
  3. Chamada final sintetiza as notas por lei no brief estruturado A1–A5 + lacunas.

Saídas: municipio/data/brief_juridico.md, municipio/data/leis_relevantes.json,
        municipio/data/notas_por_lei.json
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent import deepseek_client  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
FULL = BASE / "legislacao_full"
CATALOGO = FULL / "_catalogo_leis.json"
DATA = BASE / "municipio" / "data"
OUT = DATA / "brief_juridico.md"

MAX_CHARS_LEI = 90_000  # ~22K tokens por lei (folga p/ os 64K do DeepSeek)
MAX_LEIS = 30           # teto de leis lidas a fundo (controle de custo/tempo)

# Palavras-chave de relevância (servidores / remuneração / carreira)
KW = ["SERVIDOR", "PESSOAL", "VENCIMENT", "REMUNERA", "SUBSIDIO", "SUBSÍDIO",
      "CARREIRA", "CARGO", "PCCV", "PLANO DE CARGOS", "ESTATUTO", "GRATIFIC",
      "ADICIONAL", "INSALUBR", "PERICULOS", "TEMPORARI", "CONTRATA", "PSS",
      "QUADRO DE PESSOAL", "FUNCAO", "FUNÇÃO", "PROFESSOR", "MAGISTERIO",
      "MAGISTÉRIO", "GUARDA", "SAUDE", "SAÚDE", "PROVENTO", "APOSENT",
      "TETO", "JORNADA", "PRODUTIVIDADE", "DESEMPENHO", "ABONO"]

# Leis-núcleo (sempre incluir se existirem) — Estatuto e PCCV/gratificações já conhecidas
NUCLEO = ["lc_192_16", "lc_183_15", "lc_190_16", "lc_235_20", "lc_263_22",
          "lc_285_23", "lc_174_14", "lei_9613_23", "lei_7757_09", "lei_9526_23"]


def _up(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", str(s)) if not unicodedata.combining(c)).upper()


def selecionar() -> list[dict]:
    cat = json.loads(CATALOGO.read_text(encoding="utf-8")) if CATALOGO.exists() else []
    # mapear por slug
    by_slug = {c["slug"]: c for c in cat}
    sel, vistos = [], set()
    # núcleo primeiro
    for s in NUCLEO:
        if s in by_slug and (FULL / f"{s}.txt").exists():
            sel.append(by_slug[s]); vistos.add(s)
    # por palavra-chave na ementa
    cand = []
    for c in cat:
        if c["slug"] in vistos:
            continue
        if not (FULL / f"{c['slug']}.txt").exists():
            continue
        em = _up(c.get("ementa", ""))
        score = sum(1 for k in KW if k in em)
        if score > 0:
            cand.append((score, c))
    cand.sort(key=lambda x: (-x[0], -(x[1].get("ano") or 0)))
    for _, c in cand:
        if len(sel) >= MAX_LEIS:
            break
        sel.append(c); vistos.add(c["slug"])
    (DATA / "leis_relevantes.json").write_text(
        json.dumps(sel, ensure_ascii=False, indent=2), encoding="utf-8")
    return sel


def nota_por_lei(lei: dict) -> str:
    txt = (FULL / f"{lei['slug']}.txt").read_text(encoding="utf-8", errors="replace")[:MAX_CHARS_LEI]
    cab = f"{lei['tipo']} (nº {lei['numero']}/{lei['ano']}) — {lei.get('ementa','')[:160]}"
    prompt = (
        "Você é procurador municipal (Direito Administrativo, CF/88 arts. 37–41, LRF, STF/STJ).\n"
        f"Analise a norma abaixo e extraia SOMENTE dispositivos relevantes a estas teses de "
        "auditoria da folha:\n"
        "A1 contratação temporária em atividade permanente (CF 37 IX);\n"
        "A2 teto remuneratório (CF 37 XI) / subsídio do Prefeito;\n"
        "A3 gratificações e adicionais (base de cálculo, condições);\n"
        "A4 insalubridade/periculosidade (SV 4/STF, laudo);\n"
        "A5 apostilamento/incorporação de funções.\n\n"
        "Para cada dispositivo relevante: cite **artigo/§/inciso** e transcreva o trecho-chave "
        "entre aspas (curto). Se a norma NÃO tratar de nada disso, responda apenas 'NADA RELEVANTE'.\n"
        "Seja conciso. Em PT-BR.\n\n"
        f"=== NORMA: {cab} ===\n{txt}\n=== FIM ==="
    )
    out = deepseek_client.gen_text(prompt, temperature=0.1, max_tokens=2500)
    return out or ""


def sintetizar(notas: list[dict]) -> str:
    blob = "\n\n".join(
        f"### {n['cab']}\n{n['nota']}" for n in notas
        if n["nota"] and "NADA RELEVANTE" not in n["nota"].upper()[:30])
    prompt = (
        "Você é procurador-chefe. A seguir, notas jurídicas extraídas de várias leis municipais "
        "de Sete Lagoas/MG (folha de pagamento). Consolide um BRIEF em Markdown estruturado por "
        "tese (## A1 ... ## A5), reunindo os dispositivos pertinentes COM citação (lei, artigo) e "
        "trecho entre aspas. Ao final, '## Lacunas do acervo' com o que ainda falta (ex.: subsídio "
        "do Prefeito, laudos de insalubridade, lei de PSS se ausente). NÃO invente artigos; use só "
        "o que está nas notas. Conciso e citável.\n\n=== NOTAS POR LEI ===\n" + blob[:90000]
    )
    out = deepseek_client.gen_text(prompt, temperature=0.1, max_tokens=8000)
    return out or blob


def main():
    sel = selecionar()
    print(f">> {len(sel)} leis selecionadas p/ leitura profunda", file=sys.stderr)
    notas = []
    for i, lei in enumerate(sel, 1):
        cab = f"{lei['tipo']} (nº {lei['numero']}/{lei['ano']}) — {lei.get('ementa','')[:120]}"
        print(f"   [{i}/{len(sel)}] {lei['slug']}...", file=sys.stderr)
        nota = nota_por_lei(lei)
        notas.append({"slug": lei["slug"], "cab": cab, "nota": nota})
    (DATA / "notas_por_lei.json").write_text(
        json.dumps(notas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(">> sintetizando brief final...", file=sys.stderr)
    brief = sintetizar(notas)
    rel = sum(1 for n in notas if n["nota"] and "NADA RELEVANTE" not in n["nota"].upper()[:30])
    OUT.write_text(
        "# Brief Jurídico (DeepSeek) — Teses A1–A5 · Município de Sete Lagoas\n\n"
        f"> Gerado a partir de {len(sel)} leis lidas a fundo ({rel} com conteúdo relevante), "
        f"selecionadas de {len(json.loads(CATALOGO.read_text(encoding='utf-8'))) if CATALOGO.exists() else '?'} "
        "normas do acervo (todas as LCs do município + leis ordinárias citadas em rubricas).\n\n"
        + brief, encoding="utf-8")
    print(f">> brief salvo: {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
