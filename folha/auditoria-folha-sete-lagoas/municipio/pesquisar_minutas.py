# -*- coding: utf-8 -*-
import os
import re
from pathlib import Path

ONEDRIVE_PATH = Path(r"C:\Users\victo\OneDrive - Valor Público LTDA\SAAE\Produtos\Entrega Finalíssima - Minutas")
KEYWORDS = [re.compile(r"sapl", re.IGNORECASE), re.compile(r"educa", re.IGNORECASE), re.compile(r"dobra", re.IGNORECASE), re.compile(r"professor", re.IGNORECASE)]

def search_files():
    print(f"Scanning directory: {ONEDRIVE_PATH}")
    if not ONEDRIVE_PATH.exists():
        print("OneDrive directory does not exist.")
        return
    
    found_any = False
    for root, dirs, files in os.walk(ONEDRIVE_PATH):
        # Skip some dirs
        if any(p in root for p in [".git", "__pycache__", ".docx-backups", "old", "backup"]):
            continue
        for file in files:
            if file.startswith("~$") or not file.endswith((".md", ".txt", ".py", ".bas", ".json", ".csv")):
                continue
            path = Path(root) / file
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                matches = []
                for kw in KEYWORDS:
                    if kw.search(content):
                        matches.append(kw.pattern)
                if matches:
                    print(f"Match found in: {path.relative_to(ONEDRIVE_PATH)} | Keywords: {', '.join(matches)}")
                    found_any = True
            except Exception as e:
                print(f"Error reading {file}: {e}")
    if not found_any:
        print("No matching files found.")

if __name__ == "__main__":
    search_files()
