# -*- coding: utf-8 -*-
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
FULL = BASE / "legislacao_full"
catalogo_file = FULL / "_catalogo_leis.json"

if not catalogo_file.exists():
    print("Catalog file not found.")
    exit(1)

catalogo = json.loads(catalogo_file.read_text(encoding="utf-8"))
print(f"Total laws in catalog: {len(catalogo)}")

KEYWORDS = ["educação", "educacao", "ensino", "pccv", "magistério", "magisterio", "professor", "docente", "escola"]
matches = []

for x in catalogo:
    ementa = (x.get("ementa") or "").lower()
    tipo = (x.get("tipo") or "").lower()
    slug = (x.get("slug") or "").lower()
    
    found_kws = [kw for kw in KEYWORDS if kw in ementa or kw in slug]
    # Also check if it explicitly references LC 80 or 80/2003
    has_80 = "80" in ementa or "80" in slug
    
    if found_kws or has_80:
        matches.append((x.get("slug"), x.get("tipo"), x.get("numero"), x.get("ano"), x.get("ementa"), found_kws, has_80))

print(f"\nFound {len(matches)} matching laws in the catalog:")
for slug, tipo, num, ano, em, kws, has_80 in matches:
    print(f"Slug: {slug} | Tipo: {tipo} | Num: {num}/{ano} | References LC 80: {has_80}")
    print(f"Ementa: {em.strip()}")
    print("-" * 50)
