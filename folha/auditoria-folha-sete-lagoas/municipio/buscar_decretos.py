# -*- coding: utf-8 -*-
"""
buscar_decretos.py — Scrapes decrees (tipo=12) from Sete Lagoas SAPL API,
filtering for education/teacher workload ("dobras") regulation terms.
"""
from __future__ import annotations
import json
import os
import re
import sys
import time
from pathlib import Path
import requests

BASE = Path(__file__).resolve().parent.parent
CACHE = BASE / "legislacao_cache"
FULL = BASE / "legislacao_full"
CACHE.mkdir(parents=True, exist_ok=True)
FULL.mkdir(parents=True, exist_ok=True)

API = "https://sapl.setelagoas.mg.leg.br/api/norma/normajuridica/"
HEAD = {"Accept": "application/json", "User-Agent": "AuditoriaFolhaBot/1.0 (auditoria folha municipal)"}

KEYWORDS = [
    "professor", "docente", "jornada", "hora-atividade", "hora/atividade",
    "itinerante", "polo", "peb", "magistério", "magisterio", "regulamenta",
    "dobra", "extensão", "extensao", "carga", "educação", "educacao", "ensino"
]

def check_ementa(ementa: str) -> list[str]:
    if not ementa:
        return []
    found = []
    text_lower = ementa.lower()
    for kw in KEYWORDS:
        if kw in text_lower:
            found.append(kw)
    return found

def get_page(page: int, max_retries: int = 4):
    params = {"tipo": 12, "page": page}
    for tent in range(max_retries):
        try:
            r = requests.get(API, params=params, headers=HEAD, timeout=40)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503):
                time.sleep(2 ** tent)
                continue
            return None
        except Exception as e:
            print(f"Error fetching page {page} on attempt {tent+1}: {e}", file=sys.stderr)
            time.sleep(2 ** tent)
    return None

def main():
    print("Starting search for Sete Lagoas Education Decrees (tipo=12)...", file=sys.stderr)
    page = 1
    matches = []
    total_scanned = 0
    
    # We can check if we have a cache of the list to avoid redownloading
    list_cache_file = CACHE / "decretos_list_raw.json"
    raw_list = []
    
    if list_cache_file.exists():
        print(f"Loading raw decrees list from cache: {list_cache_file}", file=sys.stderr)
        raw_list = json.loads(list_cache_file.read_text(encoding="utf-8"))
    else:
        print("Querying SAPL API (tipo=12)... This may take a minute.", file=sys.stderr)
        while True:
            data = get_page(page)
            if not data:
                print(f"Finished or error on page {page}.", file=sys.stderr)
                break
            results = data.get("results", [])
            if not results:
                print(f"No results on page {page}. Stopping.", file=sys.stderr)
                break
            raw_list.extend(results)
            print(f"Fetched page {page} | Total items: {len(raw_list)}", file=sys.stderr)
            page += 1
            time.sleep(0.1)
        # Save to cache
        list_cache_file.write_text(json.dumps(raw_list, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved raw list to cache: {list_cache_file}", file=sys.stderr)

    # Process list
    print(f"Filtering {len(raw_list)} decrees for education keywords and year >= 2020...", file=sys.stderr)
    for x in raw_list:
        ano = x.get("ano")
        # Try to parse year, default to 0 if missing
        try:
            year_val = int(ano) if ano else 0
        except ValueError:
            year_val = 0
            
        ementa = x.get("ementa") or ""
        matched_kws = check_ementa(ementa)
        
        # We can also check type or __str__ to make sure it's a decree
        if matched_kws and year_val >= 2020:
            item = {
                "id": x.get("id"),
                "numero": x.get("numero"),
                "ano": x.get("ano"),
                "tipo": str(x.get("__str__", "")),
                "ementa": ementa.strip(),
                "data": x.get("data"),
                "texto_integral": x.get("texto_integral") or "",
                "matched_keywords": matched_kws
            }
            matches.append(item)
            
    print(f"Found {len(matches)} potential matching decrees.", file=sys.stderr)
    
    # Save matches
    output_file = CACHE / "decretos_educacao_matches.json"
    output_file.write_text(json.dumps(matches, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved matches to {output_file}", file=sys.stderr)
    
    # Print matches summary
    for m in matches:
        print(f"Decreto {m['numero']}/{m['ano']} - Data: {m['data']}")
        print(f"Keywords: {m['matched_keywords']}")
        print(f"Ementa: {m['ementa']}")
        print(f"URL: {m['texto_integral']}")
        print("-" * 50)

if __name__ == "__main__":
    main()
