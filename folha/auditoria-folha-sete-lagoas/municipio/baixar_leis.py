# -*- coding: utf-8 -*-
"""
baixar_leis.py — ADAPTAÇÃO do agente SAPL para baixar TODAS as leis do município
(antes só as 10 da Saúde). Pipeline:

  1. listar_lcs()      -> catálogo de TODAS as Leis Complementares (tipo=14) via API SAPL
  2. refs_rubricas()   -> leis ordinárias citadas nas rubricas da folha (município)
  3. baixar()          -> baixa texto_integral de cada lei p/ legislacao_cache/ (resumível)
  4. extrair()         -> converte pdf/doc/docx -> legislacao_full/<slug>.txt (resumível)
  5. catálogo final    -> legislacao_full/_catalogo_leis.json (numero, ano, ementa, arquivo)

Fonte: API SAPL da Câmara de Sete Lagoas (sapl.setelagoas.mg.leg.br) — oficial e automatável.
Resumível: pula o que já está em cache/extraído. Seguro p/ rodar em background.
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent.parent
CACHE = BASE / "legislacao_cache"
FULL = BASE / "legislacao_full"
CACHE.mkdir(parents=True, exist_ok=True)
FULL.mkdir(parents=True, exist_ok=True)

API = "https://sapl.setelagoas.mg.leg.br/api/norma/normajuridica/"
HEAD = {"Accept": "application/json", "User-Agent": "AuditoriaFolhaBot/1.0 (auditoria folha municipal)"}
CATALOGO = FULL / "_catalogo_leis.json"
LISTA = CACHE / "_sapl_lista.json"

# Leis ordinárias citadas nas rubricas do município (parsing corrigido p/ pontos de milhar)
LEIS_ORDINARIAS_EXTRA = [
    (1031, 1964), (3663, 1986), (9613, 2023),  # 9.613/23 = Guarda Civil Municipal
    (6544, 2001), (7757, 2009), (9526, 2023),  # já existentes (Saúde) — confirmadas
]


def _slug_lei(tipo_sigla: str, numero, ano) -> str:
    t = "lc" if "complementar" in tipo_sigla.lower() or tipo_sigla.upper() == "LC" else "lei"
    a = str(ano)[-2:] if ano else "xx"
    return f"{t}_{numero}_{a}"


def _get(params: dict, max_retries: int = 4):
    for tent in range(max_retries):
        try:
            r = requests.get(API, params=params, headers=HEAD, timeout=40)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503):
                time.sleep(2 ** tent)
                continue
            return None
        except Exception:
            time.sleep(2 ** tent)
    return None


# --------------------------------------------------------------------------- 1) listar LCs
def listar_lcs(tipo: int = 14) -> list[dict]:
    if LISTA.exists():
        try:
            return json.loads(LISTA.read_text(encoding="utf-8"))
        except Exception:
            pass
    out, pg = [], 1
    while True:
        d = _get({"tipo": tipo, "page": pg})
        res = (d or {}).get("results", [])
        if not res:
            break
        for x in res:
            out.append({
                "id": x.get("id"), "numero": x.get("numero"), "ano": x.get("ano"),
                "tipo": str(x.get("__str__", "")),
                "ementa": (x.get("ementa") or "").strip(),
                "data": x.get("data"),
                "texto_integral": x.get("texto_integral") or "",
            })
        print(f"  [SAPL] LC página {pg}: +{len(res)} (total {len(out)})", file=sys.stderr)
        pg += 1
        time.sleep(0.2)
    LISTA.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


# --------------------------------------------------------------------------- 2) refs ordinárias
def buscar_ordinarias() -> list[dict]:
    out = []
    for numero, ano in LEIS_ORDINARIAS_EXTRA:
        d = _get({"tipo": 13, "numero": numero, "ano": ano})
        res = (d or {}).get("results", [])
        if res:
            x = res[0]
            out.append({
                "id": x.get("id"), "numero": x.get("numero"), "ano": x.get("ano"),
                "tipo": str(x.get("__str__", "")),
                "ementa": (x.get("ementa") or "").strip(),
                "data": x.get("data"),
                "texto_integral": x.get("texto_integral") or "",
            })
            print(f"  [SAPL] Lei {numero}/{ano}: OK", file=sys.stderr)
        else:
            print(f"  [SAPL] Lei {numero}/{ano}: não encontrada", file=sys.stderr)
        time.sleep(0.2)
    return out


# --------------------------------------------------------------------------- 3) baixar arquivos
def _ext_from_url(url: str) -> str:
    u = url.lower().split("?")[0]
    for e in (".pdf", ".docx", ".doc", ".odt", ".rtf", ".txt"):
        if u.endswith(e):
            return e
    return ".bin"


def baixar(leis: list[dict]) -> list[dict]:
    for lei in leis:
        slug = _slug_lei(lei["tipo"], lei["numero"], lei["ano"])
        lei["slug"] = slug
        # já extraído?
        if (FULL / f"{slug}.txt").exists() and (FULL / f"{slug}.txt").stat().st_size > 200:
            lei["arquivo_cache"] = None
            lei["baixado"] = "ja_extraido"
            continue
        url = lei.get("texto_integral")
        if not url:
            lei["baixado"] = "sem_url"
            continue
        if url.startswith("/"):
            url = "https://sapl.setelagoas.mg.leg.br" + url
        ext = _ext_from_url(url)
        dst = CACHE / f"{slug}{ext}"
        if dst.exists() and dst.stat().st_size > 200:
            lei["arquivo_cache"] = str(dst)
            lei["baixado"] = "cache"
            continue
        try:
            r = requests.get(url, headers={"User-Agent": HEAD["User-Agent"]}, timeout=60)
            if r.status_code == 200 and len(r.content) > 200:
                dst.write_bytes(r.content)
                lei["arquivo_cache"] = str(dst)
                lei["baixado"] = "ok"
            else:
                lei["baixado"] = f"http_{r.status_code}"
        except Exception as e:  # noqa
            lei["baixado"] = f"erro:{type(e).__name__}"
        time.sleep(0.15)
    return leis


# --------------------------------------------------------------------------- 4) extrair texto
def extrair(leis: list[dict]):
    # PDFs
    try:
        import pdfplumber
    except Exception:
        pdfplumber = None
    # Word COM (uma instância)
    word = None
    try:
        import win32com.client.dynamic as dynamic
        word = dynamic.Dispatch("Word.Application")
        word.Visible = False
        try:
            word.DisplayAlerts = 0
        except Exception:
            pass
    except Exception as e:  # noqa
        print(f"  [extrair] Word COM indisponível: {e}", file=sys.stderr)

    def extrai_pdf(path, dst):
        parts = []
        with pdfplumber.open(path) as pdf:
            for pg in pdf.pages:
                parts.append(pg.extract_text() or "")
        txt = "\n".join(parts)
        dst.write_text(txt, encoding="utf-8")
        return len(txt)

    def extrai_word(path, dst):
        import shutil
        tmp = None
        src = path
        if path.lower().endswith(".bin"):
            tmp = path[:-4] + ".docx"
            shutil.copyfile(path, tmp)
            src = tmp
        doc = word.Documents.Open(src, ConfirmConversions=False, ReadOnly=True, AddToRecentFiles=False)
        try:
            txt = (doc.Content.Text or "").replace("\r\n", "\n").replace("\r", "\n")
            dst.write_text(txt, encoding="utf-8")
            return len(txt)
        finally:
            doc.Close(SaveChanges=0)
            if tmp and os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except Exception:
                    pass

    n_ok = 0
    for lei in leis:
        slug = lei.get("slug")
        if not slug:
            continue
        dst = FULL / f"{slug}.txt"
        if dst.exists() and dst.stat().st_size > 200:
            lei["chars"] = dst.stat().st_size
            lei["extraido"] = "ja"
            n_ok += 1
            continue
        cache = lei.get("arquivo_cache")
        if not cache or not os.path.exists(cache):
            lei["extraido"] = "sem_arquivo"
            continue
        low = cache.lower()
        try:
            if low.endswith(".pdf") and pdfplumber:
                c = extrai_pdf(cache, dst)
            elif low.endswith((".doc", ".docx", ".bin")) and word is not None:
                c = extrai_word(cache, dst)
            elif low.endswith((".txt", ".rtf")):
                c = len(Path(cache).read_text(encoding="latin-1", errors="replace"))
                dst.write_text(Path(cache).read_text(encoding="latin-1", errors="replace"), encoding="utf-8")
            else:
                lei["extraido"] = f"ext_nao_suportada:{low[-5:]}"
                continue
            lei["chars"] = c
            lei["extraido"] = "ok" if c > 0 else "vazio"
            if c > 0:
                n_ok += 1
        except Exception as e:  # noqa
            lei["extraido"] = f"erro:{type(e).__name__}:{str(e)[:60]}"
        if (n_ok % 20) == 0 and n_ok:
            print(f"  [extrair] {n_ok} leis extraídas...", file=sys.stderr)

    if word is not None:
        try:
            word.Quit()
        except Exception:
            pass
    return n_ok


# --------------------------------------------------------------------------- main
def main():
    print(">> 1. Listando Leis Complementares no SAPL...", file=sys.stderr)
    lcs = listar_lcs()
    print(f"   {len(lcs)} LCs catalogadas", file=sys.stderr)
    print(">> 2. Buscando leis ordinárias citadas em rubricas...", file=sys.stderr)
    ord_ = buscar_ordinarias()
    # dedup por slug
    todas = {}
    for lei in lcs + ord_:
        s = _slug_lei(lei["tipo"], lei["numero"], lei["ano"])
        lei["slug"] = s
        todas[s] = lei
    leis = list(todas.values())
    print(f">> 3. Baixando texto integral de {len(leis)} leis...", file=sys.stderr)
    leis = baixar(leis)
    print(">> 4. Extraindo texto (pdfplumber/Word COM)...", file=sys.stderr)
    n_ok = extrair(leis)

    # catálogo final (só o essencial p/ os agentes)
    catalogo = [{
        "slug": l["slug"], "numero": l["numero"], "ano": l["ano"],
        "tipo": l["tipo"], "data": l.get("data"),
        "ementa": l["ementa"], "chars": l.get("chars", 0),
        "extraido": l.get("extraido"), "baixado": l.get("baixado"),
    } for l in leis]
    catalogo.sort(key=lambda x: (-(x["ano"] or 0), -(int(re.sub(r"\D", "", str(x["numero"])) or 0))))
    CATALOGO.write_text(json.dumps(catalogo, ensure_ascii=False, indent=2), encoding="utf-8")

    # resumo
    extr = sum(1 for l in leis if l.get("extraido") in ("ok", "ja"))
    print("\n" + "=" * 60, file=sys.stderr)
    print(f"DOWNLOAD DE LEIS — RESUMO", file=sys.stderr)
    print(f"  Catalogadas: {len(leis)} | extraídas (texto): {extr}", file=sys.stderr)
    falhas = [l for l in leis if l.get("extraido") not in ("ok", "ja")]
    print(f"  Sem texto: {len(falhas)}", file=sys.stderr)
    for l in falhas[:20]:
        print(f"    {l['slug']}: baixado={l.get('baixado')} extraido={l.get('extraido')}", file=sys.stderr)
    print(f"  Catálogo: {CATALOGO}", file=sys.stderr)
    print(f"  Textos em: {FULL}", file=sys.stderr)


if __name__ == "__main__":
    main()
