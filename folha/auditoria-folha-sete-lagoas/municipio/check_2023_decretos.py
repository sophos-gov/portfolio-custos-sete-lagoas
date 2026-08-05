# -*- coding: utf-8 -*-
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CACHE = BASE / "legislacao_cache"
raw_file = CACHE / "decretos_list_raw.json"

raw_list = json.loads(raw_file.read_text(encoding="utf-8"))

print("--- 2023 DECREES IN SAPL ---")
for x in raw_list:
    if x.get("ano") == "2023" or x.get("ano") == 2023:
        print(f"ID: {x.get('id')} | Num: {x.get('numero')} | Date: {x.get('data')}")
        print(f"Ementa: {x.get('ementa')}")
        print(f"Text URL: {x.get('texto_integral')}")
        print("-" * 50)
