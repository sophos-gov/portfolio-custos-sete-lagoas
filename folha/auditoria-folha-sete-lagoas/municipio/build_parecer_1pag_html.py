# -*- coding: utf-8 -*-
"""Gera o parecer de UMA PAGINA em HTML compacto (print A4) a partir do .md."""
from pathlib import Path
import markdown

BASE = Path(__file__).resolve().parent.parent / "output" / "municipio"
SRC = BASE / "PARECER_APOSTILADO_1PAGINA.md"
OUT = BASE / "PARECER_APOSTILADO_1PAGINA.html"

body = markdown.markdown(SRC.read_text(encoding="utf-8"), extensions=["tables", "sane_lists"])

CSS = """
@page { size: A4; margin: 10mm 12mm; }
*{box-sizing:border-box;}
body{margin:0;background:#e9edf0;font-family:'Segoe UI',Arial,Helvetica,sans-serif;color:#1c2630;}
.page{max-width:200mm;margin:0 auto;background:#fff;padding:11mm 13mm;}
h1{font-family:Georgia,serif;color:#051C2C;font-size:13.5px;line-height:1.18;margin:0 0 3px;border-bottom:2px solid #051C2C;padding-bottom:4px;text-align:center;}
h2{font-family:Georgia,serif;color:#051C2C;font-size:10.4px;margin:7px 0 2px;padding-bottom:1px;border-bottom:1px solid #cfd6db;}
p,li,td,th{font-size:9.4px;line-height:1.32;margin:3px 0;color:#22303a;text-align:justify;}
strong{color:#0c1620;}
em{font-style:italic;color:#22303a;}
table{width:100%;border-collapse:collapse;margin:5px 0;}
th{font-size:8.4px;text-transform:uppercase;letter-spacing:.03em;color:#5b6770;text-align:left;border-bottom:1.5px solid #051C2C;padding:3px 5px;}
td{padding:2.5px 5px;border-bottom:1px solid #eceff1;vertical-align:top;}
ul{margin:4px 0;padding-left:16px;}
li{margin:2px 0;}
a{color:#2251FF;}
em{color:#5b6770;}
@media print{body{background:#fff;}.page{box-shadow:none;padding:0;}}
"""

html = (
    '<!doctype html><html lang="pt-br"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width, initial-scale=1">'
    "<title>Parecer (1 página) — Salário Apostilado · Sete Lagoas/MG</title>"
    f"<style>{CSS}</style></head><body><div class='page'>{body}</div></body></html>"
)
OUT.write_text(html, encoding="utf-8")
print(f">> 1-pagina salvo: {OUT} ({len(html):,} bytes)")
