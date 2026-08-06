"""
Cliente do SAPL (Sistema de Apoio ao Processo Legislativo) da Câmara de Sete Lagoas.

Fonte confiável e automatável (API REST JSON, pure-requests — funciona na VPS):
  GET /api/norma/normajuridica/?ano=YYYY&numero=NNN
Retorna ementa (= propósito oficial), data (corrige o ano inferido), texto_integral (URL).

Usado tanto no download manual (aqui) quanto no fluxo determinístico noturno (VPS).
"""
from __future__ import annotations

import json
import re
import time
import unicodedata
from pathlib import Path
from typing import Optional

from . import config

API = "https://sapl.setelagoas.mg.leg.br/api/norma/normajuridica/"


def _slug(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFKD", str(s)) if not unicodedata.combining(c))
    return re.sub(r"[^\w]+", "_", s).strip("_").lower()


def parse_lei_id(lei_id: str) -> Optional[dict]:
    """'LC 190/16' -> {tipo:'LC', numero:190, ano:2016}; 'Lei 13708' -> ano None (federal)."""
    m = re.match(r"\s*(LC|Lei)\s+(\d+)(?:/(\d{2,4}))?", lei_id, re.IGNORECASE)
    if not m:
        return None
    tipo = "LC" if m.group(1).upper() == "LC" else "Lei"
    numero = int(m.group(2))
    ano = m.group(3)
    if ano:
        ano = int(ano)
        if ano < 100:
            ano = 1900 + ano if ano > 40 else 2000 + ano
    return {"tipo": tipo, "numero": numero, "ano": ano}


def fetch_norma(numero: int, ano: int, is_lc: bool, timeout: int = 25,
                max_retries: int = 3) -> Optional[dict]:
    """Consulta a API do SAPL por (numero, ano). Retorna o registro mais adequado ou None."""
    try:
        import requests
    except Exception:
        return None
    for tent in range(max_retries):
        try:
            r = requests.get(API, params={"ano": ano, "numero": numero},
                             headers={"Accept": "application/json"}, timeout=timeout)
            if r.status_code != 200:
                if r.status_code in (429, 500, 502, 503):
                    time.sleep(2 ** tent); continue
                return None
            data = r.json()
            results = data.get("results", data if isinstance(data, list) else [])
            if not results:
                return None
            # desambiguar LC vs Lei ordinária quando há mais de um registro
            def is_complementar(rec):
                t = json.dumps(rec.get("tipo", ""), ensure_ascii=False).lower() + str(rec.get("__str__", "")).lower()
                return "complementar" in t
            chosen = None
            for rec in results:
                if is_complementar(rec) == is_lc:
                    chosen = rec; break
            chosen = chosen or results[0]
            return {
                "numero": chosen.get("numero"), "ano": chosen.get("ano"),
                "data": chosen.get("data"),
                "ementa": (chosen.get("ementa") or "").strip(),
                "texto_integral": chosen.get("texto_integral") or "",
                "tipo": str(chosen.get("__str__", "")),
            }
        except Exception:
            time.sleep(2 ** tent)
    return None


def _baixar_arquivo(url: str, destino_sem_ext: Path, timeout: int = 40) -> Optional[str]:
    """Baixa o texto_integral (pdf/doc) para cache. Retorna o caminho ou None."""
    if not url:
        return None
    try:
        import requests
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "AuditoriaFolhaBot/1.0"})
        if r.status_code != 200 or len(r.content) < 200:
            return None
        ext = ".pdf" if url.lower().endswith(".pdf") else (".doc" if url.lower().endswith(".doc") else ".bin")
        destino = destino_sem_ext.with_suffix(ext)
        destino.write_bytes(r.content)
        return str(destino)
    except Exception:
        return None


def enrich_laws(baixar_arquivos: bool = True) -> dict:
    """
    Lê leis_alvo.json, consulta o SAPL para cada lei, baixa o texto integral e
    grava leis_resumo.json (+ arquivos em legislacao_cache/). Retorna um sumário.
    """
    alvo_path = config.TABELAS_DIR / "leis_alvo.json"
    if not alvo_path.exists():
        from . import legislacao
        legislacao.discover_laws()
    leis = json.loads(alvo_path.read_text(encoding="utf-8"))

    resumo = {}
    ok = 0
    for lei in leis:
        lei_id = lei["lei_id"]
        p = parse_lei_id(lei_id)
        entry = {"lei_id": lei_id, "ementa": "", "data": None, "ano": p["ano"] if p else None,
                 "texto_integral_url": "", "arquivo_local": None, "fonte": None,
                 "status": "nao_localizada", "n_rubricas": lei.get("n_rubricas", 0)}
        if not p:
            resumo[lei_id] = entry; continue
        if p["ano"] is None:
            entry["status"] = "federal_ou_sem_ano"  # ex.: Lei Federal 13708
            entry["fonte"] = "fora do SAPL municipal"
            resumo[lei_id] = entry; continue

        rec = fetch_norma(p["numero"], p["ano"], is_lc=(p["tipo"] == "LC"))
        if rec:
            entry["ementa"] = rec["ementa"]
            entry["data"] = rec["data"]
            entry["ano"] = rec["ano"] or p["ano"]
            entry["texto_integral_url"] = rec["texto_integral"]
            entry["fonte"] = "SAPL Sete Lagoas (API)"
            entry["status"] = "localizada"
            ok += 1
            if baixar_arquivos and rec["texto_integral"]:
                caminho = _baixar_arquivo(rec["texto_integral"], config.CACHE_DIR / _slug(lei_id))
                entry["arquivo_local"] = caminho
            # cache de texto/metadados sempre
            (config.CACHE_DIR / f"{_slug(lei_id)}.json").write_text(
                json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
        resumo[lei_id] = entry

    out = {"fonte": "SAPL Sete Lagoas", "n_leis": len(leis), "n_localizadas": ok, "leis": resumo}
    (config.TABELAS_DIR / "leis_resumo.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


if __name__ == "__main__":
    res = enrich_laws()
    print(f"SAPL: {res['n_localizadas']}/{res['n_leis']} leis localizadas")
    for lid, e in res["leis"].items():
        flag = "OK " if e["status"] == "localizada" else "-- "
        arq = " [arquivo baixado]" if e.get("arquivo_local") else ""
        print(f"  {flag}{lid:14} ({e.get('data') or e['status']}): {e['ementa'][:70]}{arq}")
