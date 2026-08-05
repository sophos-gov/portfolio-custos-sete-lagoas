# -*- coding: utf-8 -*-
import os
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
FULL = BASE / "legislacao_full"

print(f"Scanning files in {FULL}...")
matches = []

ref_patterns = [
    re.compile(r"lei\s+complementar\s+(?:nº\s+)?80", re.IGNORECASE),
    re.compile(r"lc\s+(?:nº\s+)?80", re.IGNORECASE)
]

for file in os.listdir(FULL):
    if not file.endswith(".txt") or file.startswith("_"):
        continue
    path = FULL / file
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        found = False
        for pattern in ref_patterns:
            if pattern.search(content):
                found = True
                break
        if found:
            # Extract the first matching line for context
            lines = content.splitlines()
            ctx = ""
            for line in lines:
                if any(p.search(line) for p in ref_patterns):
                    ctx = line.strip()
                    break
            matches.append((file, ctx))
    except Exception as e:
        print(f"Error reading {file}: {e}")

print(f"\nFound {len(matches)} files referencing LC 80/2003:")
for file, ctx in sorted(matches):
    print(f"File: {file}")
    print(f"  Context: {ctx[:150]}")
    print("-" * 50)
