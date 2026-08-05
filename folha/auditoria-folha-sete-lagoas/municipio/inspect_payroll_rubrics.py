# -*- coding: utf-8 -*-
from pathlib import Path
import csv

# __file__ is in folha/auditoria-folha-sete-lagoas/municipio/
# We want folha/01_folha_limpa/dicionario_rubricas.csv
BASE = Path(__file__).resolve().parent.parent.parent
FOLHA_LIMPA = BASE / "01_folha_limpa"
dict_file = FOLHA_LIMPA / "dicionario_rubricas.csv"

if not dict_file.exists():
    print(f"Rubrics dictionary not found at: {dict_file}")
    exit(1)

KEYWORDS = ["dobra", "exten", "carga", "jornada", "regencia", "regência", "prof", "docen", "peb", "educ"]

print("--- PAYROLL RUBRICS MATCHING EDUCATION OR EXTENSIONS ---")
with open(dict_file, mode="r", encoding="utf-8", errors="ignore") as f:
    reader = csv.reader(f)
    # Check headers
    headers = next(reader)
    print(f"Headers: {headers}")
    
    matches = []
    for row in reader:
        row_str = " | ".join(row).lower()
        if any(kw in row_str for kw in KEYWORDS):
            matches.append(row)

for m in matches:
    print(" | ".join(m))
