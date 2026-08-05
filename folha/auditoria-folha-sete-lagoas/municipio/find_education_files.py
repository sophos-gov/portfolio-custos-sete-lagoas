# -*- coding: utf-8 -*-
import os
from pathlib import Path

# Scan c:\Users\victo\OneDrive\Documentos\Python and projects folders
SEARCH_DIRS = [
    Path(r"c:\Users\victo\OneDrive\Documentos\Python\projetos\custos"),
    Path(r"c:\Users\victo\OneDrive\Documentos\Python\projetos"),
    Path(r"c:\Users\victo\OneDrive\Documentos\Python"),
]

print("--- SEARCHING FOR EDUCATION STUDY FILES ---")
for s_dir in SEARCH_DIRS:
    if not s_dir.exists():
        continue
    print(f"Searching in: {s_dir}")
    for root, dirs, files in os.walk(s_dir):
        if any(p in root for p in [".git", "__pycache__", ".venv", "node_modules", "legislacao_cache"]):
            continue
        for file in files:
            file_lower = file.lower()
            if "educ" in file_lower or "estudo" in file_lower or "dobra" in file_lower:
                path = Path(root) / file
                print(f"Found: {path}")
