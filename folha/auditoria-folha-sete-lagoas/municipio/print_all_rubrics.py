# -*- coding: utf-8 -*-
from pathlib import Path
import csv
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).resolve().parent.parent.parent
FOLHA_LIMPA = BASE / "01_folha_limpa"
dict_file = FOLHA_LIMPA / "dicionario_rubricas.csv"

if not dict_file.exists():
    print(f"Rubrics dictionary not found.")
    exit(1)

print("--- ALL RUBRICS IN DICTIONARY ---")
with open(dict_file, mode="r", encoding="utf-8-sig", errors="ignore") as f:
    reader = csv.reader(f, delimiter=';')
    for row in reader:
        # Filter empty rows
        if not row:
            continue
        print(" | ".join(row))
