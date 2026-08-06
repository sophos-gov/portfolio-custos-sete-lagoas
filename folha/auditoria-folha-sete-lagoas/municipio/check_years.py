# -*- coding: utf-8 -*-
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CACHE = BASE / "legislacao_cache"
raw_file = CACHE / "decretos_list_raw.json"

raw_list = json.loads(raw_file.read_text(encoding="utf-8"))
years = {}
for x in raw_list:
    y = x.get("ano")
    years[y] = years.get(y, 0) + 1

print("--- DECREES PER YEAR ---")
for y in sorted(years.keys(), key=lambda val: int(val) if val and str(val).isdigit() else 0, reverse=True):
    print(f"  Year {y}: {years[y]} decrees")
