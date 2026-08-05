# -*- coding: utf-8 -*-
"""Converte PARECER_APOSTILADO.md em HTML autônomo estilizado (estilo do SUMARIO_EXECUTIVO)."""
from pathlib import Path
import markdown

BASE = Path(__file__).resolve().parent.parent / "output" / "municipio"
SRC = BASE / "PARECER_APOSTILADO.md"
OUT = BASE / "PARECER_APOSTILADO.html"

md_text = SRC.read_text(encoding="utf-8")
body = markdown.markdown(
    md_text,
    extensions=["tables", "fenced_code", "sane_lists", "attr_list", "nl2br"],
)

CSS = """
:root{--navy:#051C2C;--blue:#2251FF;--ink:#1a1a1a;--mut:#5b6770;--line:#d8dde1;--bg:#fff;--soft:#f4f6f8;}
*{box-sizing:border-box;}
body{margin:0;background:#e9edf0;color:var(--ink);font-family:Georgia,'Times New Roman',serif;}
.page{max-width:980px;margin:0 auto;background:var(--bg);}
p,li,td,th{font-family:'Segoe UI',Arial,Helvetica,sans-serif;font-size:14.5px;line-height:1.62;color:#23323c;}
h1,h2,h3,h4{font-family:Georgia,'Times New Roman',serif;color:var(--navy);}
.cover{background:var(--navy);color:#fff;padding:52px 60px 40px;}
.cover .kicker{font-family:'Segoe UI',sans-serif;letter-spacing:.22em;font-size:12px;color:#8fb0ff;text-transform:uppercase;}
.cover h1{color:#fff;font-size:30px;line-height:1.18;margin:14px 0 8px;font-weight:700;}
.cover .sub{font-family:'Segoe UI',sans-serif;color:#c7d4e0;font-size:14.5px;}
.cover .rule{height:3px;width:80px;background:var(--blue);margin:20px 0;}
.kpibar{display:flex;flex-wrap:wrap;gap:0;border-top:1px solid rgba(255,255,255,.15);margin-top:26px;}
.kpibar .k{flex:1 1 22%;padding:16px 14px 6px;border-right:1px solid rgba(255,255,255,.12);}
.kpibar .k:last-child{border-right:none;}
.kpibar .v{font-family:Georgia,serif;font-size:23px;color:#fff;}
.kpibar .l{font-family:'Segoe UI',sans-serif;font-size:11px;color:#9fb3c8;text-transform:uppercase;letter-spacing:.08em;}
.body{padding:38px 60px 60px;}
.body>h2{font-size:22px;border-bottom:2px solid var(--navy);padding-bottom:7px;margin:42px 0 16px;}
.body>h3{font-size:18px;margin:30px 0 10px;border-left:4px solid var(--blue);padding-left:10px;}
.body>h4{font-size:15px;margin:18px 0 6px;color:#2a3b47;}
.body>blockquote{border-left:4px solid var(--blue);background:var(--soft);padding:12px 18px;margin:16px 0;border-radius:0 3px 3px 0;color:#2a3b47;}
.body>blockquote p{font-size:13.5px;margin:6px 0;}
table{width:100%;border-collapse:collapse;margin:12px 0;}
th{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--mut);text-align:left;border-bottom:2px solid var(--navy);padding:7px 8px;}
td{padding:6px 8px;border-bottom:1px solid #eceff1;vertical-align:top;}
table tr td:last-child, table tr th:last-child{text-align:right;}
table tr td:first-child{text-align:left;}
code{background:#eef1f4;padding:1px 5px;border-radius:3px;font-size:12.5px;}
hr{border:none;border-top:1px solid var(--line);margin:30px 0;}
a{color:var(--blue);word-break:break-all;}
ul,ol{padding-left:20px;}
strong{color:#16222b;}
@media print{body{background:#fff;}.page{max-width:none;}table,blockquote{break-inside:avoid;}}
"""

HEADER = """
<header class="cover">
  <div class="kicker">Auditoria de custo da folha · Parecer técnico-jurídico</div>
  <h1>Salário Apostilado (Achado A5)</h1>
  <div class="sub">Prefeitura de Sete Lagoas / MG · rubrica 36 · mai/2026 · escopo: cessação prospectiva</div>
  <div class="rule"></div>
  <div class="kpibar">
    <div class="k"><div class="v">109</div><div class="l">servidores apostilados</div></div>
    <div class="k"><div class="v">R$ 676 mil/ano</div><div class="l">glosa limpa (teto §2)</div></div>
    <div class="k"><div class="v">6</div><div class="l">acima do teto RGPS</div></div>
    <div class="k"><div class="v">15</div><div class="l">fora da janela 89-B (verificar)</div></div>
  </div>
</header>
"""

html = (
    '<!doctype html><html lang="pt-br"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width, initial-scale=1">'
    "<title>Parecer — Salário Apostilado · Sete Lagoas/MG</title>"
    f"<style>{CSS}</style></head><body><div class='page'>"
    f"{HEADER}<main class='body'>{body}</main></div></body></html>"
)
OUT.write_text(html, encoding="utf-8")
print(f">> HTML salvo: {OUT} ({len(html):,} bytes)")
