# -*- coding: utf-8 -*-
"""
build_html_teto.py — Relatório AUTÔNOMO sobre o teto remuneratório (CF art. 37, XI e §11)
do município de Sete Lagoas/MG. Documento dedicado, autocontido, no mesmo estilo McKinsey
do sumário executivo, focado exclusivamente no teto.

Fontes (não recalcula nada — single source of truth):
  - output/municipio/teto_aprofundamento.json   (dados: listas, cenários, brechas)
  - output/municipio/auditoria_municipio.json   (tese A6: prosa + fundamentos verbatim)

Reaproveita helpers e exhibits de build_html_municipio.py (brl, num, esc, md_to_html,
exhibit_teto_servidores, exhibit_delta_511, exhibit_brechas).

Uso:  python municipio/build_html_teto.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_html_municipio as B  # noqa: E402  (reusa helpers/exhibits/estilo)

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "output" / "municipio"

CSS = """
:root{--navy:#051C2C;--blue:#2251FF;--ink:#1a1a1a;--mut:#5b6770;--line:#d8dde1;--bg:#fff;--soft:#f4f6f8;}
*{box-sizing:border-box;}
body{margin:0;background:#e9edf0;color:var(--ink);font-family:Georgia,'Times New Roman',serif;}
.page{max-width:980px;margin:0 auto;background:var(--bg);}
p,li,td,th{font-family:'Segoe UI',Arial,Helvetica,sans-serif;font-size:14.5px;line-height:1.62;color:#23323c;}
h1,h2,h3,h4{font-family:Georgia,'Times New Roman',serif;color:var(--navy);}
.cover{background:var(--navy);color:#fff;padding:56px 60px 48px;}
.cover .kicker{font-family:'Segoe UI',sans-serif;letter-spacing:.22em;font-size:12px;color:#8fb0ff;text-transform:uppercase;}
.cover h1{color:#fff;font-size:32px;line-height:1.18;margin:14px 0 8px;font-weight:700;}
.cover .sub{font-family:'Segoe UI',sans-serif;color:#c7d4e0;font-size:15px;}
.cover .rule{height:3px;width:80px;background:var(--blue);margin:22px 0;}
.cover .gov{font-size:18px;line-height:1.6;color:#eaf0f7;max-width:780px;}
.kpibar{display:flex;flex-wrap:wrap;gap:0;border-top:1px solid rgba(255,255,255,.15);margin-top:30px;}
.kpibar .k{flex:1 1 22%;padding:18px 14px 6px;border-right:1px solid rgba(255,255,255,.12);}
.kpibar .k:last-child{border-right:none;}
.kpibar .v{font-family:Georgia,serif;font-size:25px;color:#fff;}
.kpibar .l{font-family:'Segoe UI',sans-serif;font-size:11.5px;color:#9fb3c8;text-transform:uppercase;letter-spacing:.08em;}
.body{padding:42px 60px 60px;}
h2.sec{font-size:22px;border-bottom:2px solid var(--navy);padding-bottom:7px;margin:42px 0 16px;}
.lead{font-weight:600;color:var(--navy);}
.exhibit{border:1px solid var(--line);border-radius:3px;margin:24px 0;padding:20px 22px 14px;background:#fff;box-shadow:0 1px 0 rgba(0,0,0,.03);}
.ex-num{font-family:'Segoe UI',sans-serif;font-size:11px;font-weight:700;letter-spacing:.14em;color:var(--blue);text-transform:uppercase;}
.exhibit h3{font-size:17px;margin:4px 0 14px;}
table{width:100%;border-collapse:collapse;margin:6px 0;}
th{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--mut);text-align:left;border-bottom:2px solid var(--navy);padding:7px 8px;}
td{padding:6px 8px;border-bottom:1px solid #eceff1;}
td.r,th.r{text-align:right;}
tfoot td{border-top:2px solid var(--navy);border-bottom:none;}
.src{font-size:11.5px;color:var(--mut);font-style:italic;margin:8px 0 2px;}
.fund-label{font-size:12.5px;color:var(--mut);margin:8px 0 2px;font-weight:600;}
ul.fund{margin:0 0 8px;padding-left:18px;}ul.fund li{font-size:13px;color:#3a4750;margin-bottom:4px;}
.rec{background:#eef3ff;border:1px solid #cfdcff;padding:14px 16px;border-radius:3px;}
.verif{font-size:13px;color:#5b6770;background:var(--soft);border-left:3px solid #c8d0d6;padding:10px 14px;margin-top:14px;}
.cav{color:var(--mut);font-style:italic;}
.callout{background:var(--navy);color:#eaf0f7;padding:22px 26px;border-radius:4px;margin:24px 0;}
.callout p{color:#eaf0f7;}
.note{font-size:12.5px;color:var(--mut);border-top:1px solid var(--line);margin-top:40px;padding-top:14px;}
@media print{body{background:#fff;}.page{max-width:none;}.exhibit{break-inside:avoid;}}
"""


def _renum(html_exhibit, de, para):
    return html_exhibit.replace(f"Exhibit {de}", f"Exhibit {para}")


def main():
    tap = json.loads((OUT / "teto_aprofundamento.json").read_text(encoding="utf-8"))
    aud = json.loads((OUT / "auditoria_municipio.json").read_text(encoding="utf-8"))
    a6 = next((t for t in aud.get("teses", []) if t.get("id") == "A6"), {})

    proxy = tap["teto_proxy"]["valor"]
    cen = tap["cenarios"]
    ag = tap["agregados"]
    r216 = tap.get("abate_teto_r216", {})
    nbru = cen["bruto"]["n"]; n511 = cen["base_511"]["n"]
    red = cen["reducao_pct"]

    brl = B.brl; num = B.num; md = B.md_to_html; esc = B.esc

    gov = (
        f"Aplicado corretamente o art. 37, §11 da Constituição — que exclui do teto as verbas "
        f"indenizatórias —, <strong>{n511} servidores</strong> (não {nbru}) excedem o subsídio "
        f"do Prefeito de forma estrutural. A exposição recua de R$ 5,78 mi para "
        f"<strong>{brl(cen['base_511']['exc_ano'])}/ano</strong> (−{red:.0f}%). O alvo real é a "
        f"Procuradoria; os médicos têm o escudo da acumulação lícita. E o município já possui o "
        f"mecanismo de abate-teto (rubrica R216), mas o aplica a apenas "
        f"{r216.get('n_servidores','—')} servidores.")

    kpibar = f"""
    <div class="kpibar">
      <div class="k"><div class="v">{brl(proxy)}</div><div class="l">Teto-proxy · subsídio do Prefeito</div></div>
      <div class="k"><div class="v">{n511}</div><div class="l">Acima do teto no líquido §11</div></div>
      <div class="k"><div class="v">{brl(cen['base_511']['exc_ano'])}</div><div class="l">Exposição §11 / ano</div></div>
      <div class="k"><div class="v">{r216.get('n_servidores','—')}</div><div class="l">Servidores com abate-teto aplicado</div></div>
    </div>"""

    # síntese executiva (escrita aqui, números do JSON)
    sintese = (
        f"**O problema de método.** O achado de teto da auditoria comparava *proventos brutos* "
        f"contra o subsídio do Prefeito. Isso ignora o art. 37, §11, que manda excluir as parcelas "
        f"indenizatórias (férias, 1/3, 13º, rescisões). A base de folha do município permite essa "
        f"separação — e, feita a exclusão, o quadro muda de tamanho e de foco.\n\n"
        f"**O resultado.** No bruto, {nbru} servidores superam o teto; no líquido §11, "
        f"**{n511}** — e os {nbru - n511} que saem o faziam por verbas indenizatórias, não por "
        f"remuneração contínua. O excedente real é **{brl(cen['base_511']['exc_mes'])}/mês = "
        f"{brl(cen['base_511']['exc_ano'])}/ano**. Destes {n511}: **{ag['nao_medico']['n']} "
        f"não-médicos** ({brl(ag['nao_medico']['exc_ano'])}/ano), núcleo na Procuradoria; "
        f"**{ag['medico']['n']} médicos** ({brl(ag['medico']['exc_ano'])}/ano), em sua maioria "
        f"estouros pequenos com plantão limitado ao subsídio. **{ag['estrutural_3de3']['n']} dos "
        f"{n511}** violam o teto nos 3 meses (estrutural).\n\n"
        f"**A oportunidade.** O abate-teto não depende de lei nova: a rubrica **R216 DESC.LIMITE "
        f"CONSTITUCIONAL** já existe na folha — mas é acionada para pouquíssimos. Ligá-la, "
        f"computando todas as parcelas remuneratórias (inclusive produtividade fiscal e "
        f"gratificações), é a medida de maior alavancagem.")

    ex61 = _renum(B.exhibit_teto_servidores(tap), "6.1", "1")
    ex62 = _renum(B.exhibit_delta_511(tap), "6.2", "2")
    ex63 = _renum(B.exhibit_brechas(tap), "6.3", "3")

    fund = a6.get("fundamento", [])
    fund_html = "".join(f"<li>{B._inline(f)}</li>" for f in fund)

    # corpo analítico: usa a prosa da tese A6 (já validada verbatim), sem o 1º parágrafo
    # de escopo (que duplica a síntese) — começa no item "2)".
    achado = a6.get("achado", "")
    corte = achado.find("**2)")
    analise = achado[corte:] if corte > 0 else achado

    html_doc = f"""<!doctype html><html lang="pt-br"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Teto Remuneratório — Auditoria da Folha · Sete Lagoas/MG</title>
<style>{CSS}</style></head>
<body><div class="page">
  <header class="cover">
    <div class="kicker">Teto remuneratório constitucional · CF art. 37, XI e §11</div>
    <h1>Teto Remuneratório — Prefeitura de Sete Lagoas / MG</h1>
    <div class="sub">Relatório dedicado · competência mai/2026 · 100% da folha · proventos brutos</div>
    <div class="rule"></div>
    <p class="gov">{B._inline(gov)}</p>
    {kpibar}
  </header>
  <main class="body">
    <h2 class="sec">Síntese</h2>
    {md(sintese)}

    <h2 class="sec">Quem está acima do teto</h2>
    {ex61}
    {ex62}

    <h2 class="sec">Por que o abate-teto não opera — e as brechas</h2>
    {md(analise)}
    {ex63}

    <h2 class="sec">Recomendações</h2>
    <div class="rec">{B._inline(a6.get('recomendacao',''))}</div>

    <h2 class="sec">Fundamento legal (conferido verbatim no acervo)</h2>
    <ul class="fund">{fund_html}</ul>

    <div class="verif"><strong>Verificação adversarial.</strong> {B._inline(a6.get('critica_revisor',''))}</div>

    <div class="note">
      <strong>Nota metodológica.</strong> Base de teto (art. 37, §11) = proventos totais − rubricas
      de natureza indenizatória (tipo_rubrica EVENTUAL_INDENIZATORIA); reconciliação folha-longa ↔
      servidor-mês fecha ao centavo. Teto-proxy = maior provento do Prefeito ({brl(proxy)}) —
      o <em>valor nominal</em> do subsídio (lei de fixação da legislatura) segue pendente e, obtido,
      pode reduzir o teto e o nº de violações. Líquido real (pós-INSS/IRRF) só existe na base
      Saúde/fev (14 de {nbru}), competência distinta — usado apenas como referência.
      Fontes: base pessoal.xlsx × cadastro(32).csv; acervo legal municipal (SAPL).
      Anualização: fator 13,3× (12 + 13º + ⅓ de férias).
    </div>
  </main>
</div></body></html>"""

    out = OUT / "TETO_REMUNERATORIO.html"
    out.write_text(html_doc, encoding="utf-8")
    print(f"HTML do teto gravado: {out} ({out.stat().st_size/1024:.0f} KB)")
    return out


if __name__ == "__main__":
    main()
