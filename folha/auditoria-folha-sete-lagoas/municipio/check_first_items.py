# -*- coding: utf-8 -*-
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CACHE = BASE / "legislacao_cache"
raw_file = CACHE / "decretos_list_raw.json"

raw_list = json.loads(raw_file.read_text(encoding="utf-8"))

print("--- FIRST 20 DECREES FROM API LIST ---")
for i, x in enumerate(raw_list[:20]):
    print(f"{i+1}: ID {x.get('id')} | Decreto {x.get('numero')}/{x.get('ano')} | Data: {x.get('data')} | {x.get('__str__')}")

print("\n--- LAST 20 DECREES FROM API LIST ---")
for i, x in enumerate(raw_list[-20:]):
    idx = len(raw_list) - 20 + i + 1
    print(idx, f"ID {x.get('id')} | Decreto {x.get('numero')}/{x.get('ano')} | Data: {x.get('data')} | {x.get('__str__')}")
