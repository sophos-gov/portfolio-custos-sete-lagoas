# -*- coding: utf-8 -*-
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CACHE = BASE / "legislacao_cache"
raw_file = CACHE / "decretos_list_raw.json"

if not raw_file.exists():
    print("Raw list cache not found.")
    exit(1)

raw_list = json.loads(raw_file.read_text(encoding="utf-8"))
print(f"Total decrees loaded: {len(raw_list)}")

# Print first 5 items to inspect fields
print("\n--- FIRST 5 ITEMS ---")
for i, x in enumerate(raw_list[:5]):
    print(f"Item {i+1}:")
    print(f"  __str__: {x.get('__str__')}")
    print(f"  ano: {x.get('ano')} (type: {type(x.get('ano'))})")
    print(f"  ementa: {x.get('ementa')}")
    print(f"  data: {x.get('data')}")
    print(f"  texto_integral: {x.get('texto_integral')}")
    print()

# Count by year
years = {}
for x in raw_list:
    y = x.get("ano")
    years[y] = years.get(y, 0) + 1

print("\n--- DECREES PER YEAR ---")
for y in sorted(years.keys(), key=lambda val: int(val) if val and str(val).isdigit() else 0, reverse=True):
    print(f"  Year {y}: {years[y]} decrees")

# Let's search with a broader set of keywords or no year filter to see if we get anything
print("\n--- SEARCH WITH NO YEAR FILTER (ALL YEARS) FOR KEYWORDS ---")
KEYWORDS = ["professor", "docente", "jornada", "itinerante", "polo", "peb", "magistério", "magisterio", "dobra", "educação", "educacao", "ensino"]
matches = []
for x in raw_list:
    ementa = (x.get("ementa") or "").lower()
    found = [kw for kw in KEYWORDS if kw in ementa]
    if found:
        matches.append((x.get("numero"), x.get("ano"), x.get("ementa"), found))

print(f"Found {len(matches)} matches across all years (no year limit):")
for num, ano, em, kws in matches[:30]:
    print(f"  Decreto {num}/{ano} (Kws: {kws}): {em.strip()}")

