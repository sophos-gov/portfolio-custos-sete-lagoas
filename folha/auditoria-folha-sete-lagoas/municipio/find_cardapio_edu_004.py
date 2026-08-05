# -*- coding: utf-8 -*-
from pathlib import Path

# __file__ is at folha/auditoria-folha-sete-lagoas/municipio/
# cardapio_unificado.html is at root (4 levels up)
BASE = Path(__file__).resolve().parent.parent.parent.parent
cardapio_file = BASE / "cardapio_unificado.html"

if not cardapio_file.exists():
    print(f"Cardapio file not found at: {cardapio_file}")
    exit(1)

content = cardapio_file.read_text(encoding="utf-8", errors="ignore")
lines = content.splitlines()

print("--- EDU-004 IN CARDAPIO ---")
found = False
for i, line in enumerate(lines):
    if "EDU-004" in line or "edu-004" in line:
        found = True
        print(f"Line {i+1}:")
        for j in range(max(0, i-5), min(len(lines), i+15)):
            print(f"  {j+1}: {lines[j]}")
        print("-" * 50)

if not found:
    print("No EDU-004 found in cardapio_unificado.html.")
