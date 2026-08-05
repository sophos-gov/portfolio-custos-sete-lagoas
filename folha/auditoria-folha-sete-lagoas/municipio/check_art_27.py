# -*- coding: utf-8 -*-
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
FULL = BASE / "legislacao_full"
path = FULL / "lc_80_03.txt"

content = path.read_text(encoding="utf-8", errors="ignore")
lines = content.splitlines()

# Search for "Art. 27" and print surrounding lines
for i, line in enumerate(lines):
    if "Art. 27" in line:
        print(f"--- Article 27 in lc_80_03.txt (Line {i+1}) ---")
        for j in range(max(0, i-5), min(len(lines), i+30)):
            print(f"{j+1}: {lines[j]}")
        break
