# -*- coding: utf-8 -*-
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent.parent
cardapio_file = BASE / "cardapio_unificado.html"

content = cardapio_file.read_text(encoding="utf-8", errors="ignore")
lines = content.splitlines()

print("--- SELO BADGES IN CARDAPIO ---")
for i, line in enumerate(lines):
    if 'class="selo' in line:
        print(f"Line {i+1}: {line.strip()}")
