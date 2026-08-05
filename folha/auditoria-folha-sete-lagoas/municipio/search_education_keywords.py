# -*- coding: utf-8 -*-
import os
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
FULL = BASE / "legislacao_full"

FILES = [
    "lc_80_03.txt", "lc_95_04.txt", "lc_98_04.txt", "lc_108_06.txt",
    "lc_120_07.txt", "lc_127_08.txt", "lc_133_10.txt", "lc_135_10.txt",
    "lc_138_10.txt", "lc_147_11.txt", "lc_149_11.txt", "lc_152_12.txt",
    "lc_159_12.txt", "lc_163_12.txt", "lc_172_13.txt", "lc_189_16.txt",
    "lc_229_19.txt", "lc_233_20.txt", "lc_236_20.txt", "lc_248_21.txt",
    "lc_253_21.txt", "lc_266_22.txt", "lc_281_23.txt", "lc_287_23.txt"
]

KEYWORDS = [
    re.compile(r"dobra", re.IGNORECASE),
    re.compile(r"itinerant", re.IGNORECASE), # itinerante, itinerância
    re.compile(r"polo", re.IGNORECASE),
    re.compile(r"extens[ão]", re.IGNORECASE), # extensão, extensao
    re.compile(r"carga\s+hor[áa]ria", re.IGNORECASE),
    re.compile(r"jornada", re.IGNORECASE),
    re.compile(r"reg[êe]ncia", re.IGNORECASE)
]

print("--- KEYWORD MATCHES IN EDUCATION LEGISLATION ---")
for file in FILES:
    path = FULL / file
    if not path.exists():
        continue
    content = path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()
    
    file_printed = False
    for i, line in enumerate(lines):
        matches = []
        for kw in KEYWORDS:
            if kw.search(line):
                matches.append(kw.pattern)
        if matches:
            if not file_printed:
                print(f"\n==================== File: {file} ====================")
                file_printed = True
            print(f"Line {i+1} | Kws: {matches} | Content: {line.strip()}")
