#!/usr/bin/env python3
"""
build_html.py — Dashboard HTML standalone (estilo McKinsey, Chart.js v4).

Consome:
  tabelas/dados_consolidados.json   (obrigatório — gerado por folha_tables.gerar_tudo)
  tabelas/rubricas_legislacao.json  (opcional — enriquecimento legal; seção #legislacao)
  tabelas/insights.json             (opcional — narrativa do agente; senão usa fallback)

Produz:
  output/relatorio_custos_folha_saude_setelagoas.html

Roda sem API. Se a narrativa do agente não existir, gera narrativa determinística.
"""
from __future__ import annotations

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Formatação
# ---------------------------------------------------------------------------
def fmt_brl(v) -> str:
    try:
        return f"R$ {float(v):_.0f}".replace("_", ".")
    except Exception:
        return "R$ 0"


def fmt_m(v) -> str:
    try:
        v = float(v)
    except Exception:
        return "R$ 0"
    if v >= 1e9:
        return f"R$ {v/1e9:.1f}B".replace(".", ",")
    if v >= 1e6:
        return f"R$ {v/1e6:.1f}M".replace(".", ",")
    if v >= 1e3:
        return f"R$ {v/1e3:.0f} mil"
    return fmt_brl(v)


def pct(v) -> str:
    try:
        return f"{float(v):.1f}%".replace(".", ",")
    except Exception:
        return "0,0%"


def _esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# ---------------------------------------------------------------------------
# Narrativa fallback (determinística — usada quando não há insights do agente)
# ---------------------------------------------------------------------------
def narrativa_fallback(dados: dict) -> dict:
    k = dados["kpis"]
    pv = {r["categoria_vinculo"]: r for r in dados.get("por_vinculo", [])}
    temp = pv.get("CONTRATADO_TEMPORARIO", {})
    efet = pv.get("EFETIVO", {})
    par = dados.get("rubricas_pareto", {})
    top_unid = dados.get("top_unidades", [])
    top_cargo = dados.get("top_cargos", [])
    elite = k.get("elite_acima_20k", {})

    action = (f"A folha da Saúde de Sete Lagoas custa {fmt_m(k['proventos_total'])} "
              f"em {k['competencia']} para {k['n_ativos']:,} servidores ativos, com "
              f"{pct(temp.get('pct_folha', 0))} do gasto concentrado em vínculos temporários.").replace(",", ".")

    analise = (
        f"A remuneração bruta soma {fmt_brl(k['proventos_total'])} entre {k['n_ativos']} servidores ativos "
        f"(média {fmt_brl(k['proventos_medio'])}, mediana {fmt_brl(k['proventos_mediana'])}). "
        f"O coeficiente de Gini de {str(k['gini_proventos']).replace('.', ',')} indica desigualdade "
        f"{'moderada' if k['gini_proventos'] < 0.5 else 'alta'} na distribuição salarial. "
        f"A taxa de desconto média é de {pct(k['taxa_desconto_pct'])} dos proventos."
    )

    cruzamento = (
        f"O contraste entre vínculos é o achado central: CONTRATADO_TEMPORARIO responde por "
        f"{temp.get('n', 0)} servidores e {fmt_brl(temp.get('proventos_total', 0))} "
        f"({pct(temp.get('pct_folha', 0))} da folha, média {fmt_brl(temp.get('proventos_medio', 0))}), "
        f"enquanto EFETIVO soma {efet.get('n', 0)} servidores e {fmt_brl(efet.get('proventos_total', 0))} "
        f"({pct(efet.get('pct_folha', 0))}, média {fmt_brl(efet.get('proventos_medio', 0))}). "
        f"Em concentração de rubricas, as 10 maiores explicam {pct(par.get('top10_pct', 0))} dos proventos."
    )

    alertas = []
    if elite.get("n"):
        alertas.append(f"{elite['n']} servidores recebem acima de R$ 20 mil "
                       f"({pct(elite.get('pct_folha', 0))} da folha em {pct(elite.get('pct_servidores', 0))} do efetivo).")
    if top_unid:
        u = top_unid[0]
        alertas.append(f"A unidade {u.get('nome_unidade','')} concentra {fmt_brl(u.get('proventos_total',0))} "
                       f"({pct(u.get('pct_folha',0))} da folha).")
    if top_cargo:
        c = top_cargo[0]
        alertas.append(f"O cargo {c.get('cargo','')} lidera com {fmt_brl(c.get('proventos_total',0))} "
                       f"em {int(c.get('n',0))} servidores (média {fmt_brl(c.get('proventos_medio',0))}).")
    n_alertas = len(dados.get("alertas", []))
    if n_alertas:
        alertas.append(f"{n_alertas} ocorrências sinalizadas (elite, desconto>50%, outliers por cargo) — ver tabela.")

    recomendacoes = [
        "Avaliar a sustentabilidade da dependência de vínculos temporários (≈2/3 do custo) frente à LRF.",
        "Revisar as unidades e cargos de maior concentração de custo para oportunidades de eficiência.",
        "Mapear as gratificações por lei criadora (seção Legislação) para entender os direcionadores do gasto.",
    ]
    return {
        "action_title": action,
        "analise_folha": analise,
        "cruzamento": cruzamento,
        "alertas": alertas,
        "recomendacoes": recomendacoes,
        "_fonte": "fallback_deterministico",
    }


# ---------------------------------------------------------------------------
# Blocos HTML
# ---------------------------------------------------------------------------
def _kpi_cards(k: dict) -> str:
    cards = [
        ("Custo bruto mensal", fmt_m(k["proventos_total"]), f"{k['n_ativos']:,} servidores ativos".replace(",", ".")),
        ("Remuneração média", fmt_brl(k["proventos_medio"]), f"mediana {fmt_brl(k['proventos_mediana'])}"),
        ("Gini (proventos)", str(k["gini_proventos"]).replace(".", ","), "desigualdade salarial"),
        ("Elite > R$ 20k", str(k["elite_acima_20k"]["n"]), f"{pct(k['elite_acima_20k']['pct_folha'])} da folha"),
        ("Taxa de desconto", pct(k["taxa_desconto_pct"]), f"líquido {fmt_m(k['liquido_total'])}"),
    ]
    out = []
    for titulo, valor, sub in cards:
        out.append(f"""<div class="kpi">
          <div class="kpi-label">{_esc(titulo)}</div>
          <div class="kpi-value">{_esc(valor)}</div>
          <div class="kpi-sub">{_esc(sub)}</div>
        </div>""")
    return "\n".join(out)


def _tabela(headers: list[str], rows: list[list[str]], cls: str = "") -> str:
    th = "".join(f"<th>{_esc(h)}</th>" for h in headers)
    trs = []
    for r in rows:
        tds = "".join(f"<td>{c}</td>" for c in r)
        trs.append(f"<tr>{tds}</tr>")
    return f'<table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{"".join(trs)}</tbody></table>'


def _bloco_analise_leis(analise: dict | None) -> str:
    """Subseção 'Análise legislativa × custo' (leitura do texto das leis cruzada com a folha)."""
    if not analise or not analise.get("analises"):
        return ""
    fonte_tag = {"pdf": "texto integral (PDF)", "texto_extraido": "texto integral",
                 "docx": "texto integral (DOCX)", "ementa": "ementa"}
    itens = []
    for a in sorted(analise["analises"], key=lambda x: -x.get("valor_total", 0)):
        if not a.get("analise"):
            continue
        tag = fonte_tag.get(a.get("fonte_texto", ""), a.get("fonte_texto", ""))
        itens.append(
            f'<div style="margin:12px 0;padding:12px 14px;background:#f8fafb;border-left:3px solid #16557a;border-radius:4px">'
            f'<div style="font-weight:600">{_esc(a["lei_id"])} '
            f'<span class="muted">— {fmt_brl(a.get("valor_total",0))} · {a.get("n_rubricas",0)} rubrica(s) · '
            f'<span class="badge">{_esc(tag)}</span></span></div>'
            f'<div style="margin-top:6px">{_esc(a["analise"])}</div></div>')
    if not itens:
        return ""
    return ("<h3>Análise legislativa × custo</h3>"
            '<p class="muted">Leitura do texto de cada lei cruzada com as rubricas e o custo real da folha.</p>'
            + "".join(itens))


def _secao_legislacao(leg: dict | None, analise: dict | None = None) -> tuple[str, str]:
    """Retorna (html, chart_js). Degrada graciosamente se leg ausente/parcial."""
    if not leg or not leg.get("rubricas"):
        html = """<section id="legislacao">
          <h2>Legislação das gratificações</h2>
          <p class="muted">Enriquecimento legal pendente — execute o agente com acesso à internet
          para mapear cada rubrica à lei que a criou. A análise de custo acima independe desta seção.</p>
        </section>"""
        return html, ""

    cob = leg.get("cobertura_valor_pct", 0)
    por_lei = sorted(leg.get("por_lei", []), key=lambda x: x.get("valor_total", 0), reverse=True)
    rubricas = sorted(leg.get("rubricas", []), key=lambda x: x.get("valor_total", 0), reverse=True)[:30]

    rows_lei = [[_esc(l.get("lei_id", "")), _esc(l.get("proposito", "") or l.get("grupo", "")),
                 str(l.get("n_rubricas", "")), fmt_brl(l.get("valor_total", 0))] for l in por_lei]
    tab_lei = _tabela(["Diploma legal", "Propósito", "Rubricas", "Custo"], rows_lei, "tbl")

    rows_rub = []
    for r in rubricas:
        status = r.get("lei_status", "")
        badge = "" if status == "localizada" else f' <span class="badge">{_esc(status)}</span>'
        rows_rub.append([
            _esc(r.get("codigo", "")), _esc(r.get("descricao", "")),
            _esc(r.get("grupo", "")), _esc(r.get("lei_criadora", "—")) + badge,
            _esc(r.get("proposito_1linha", "")), fmt_brl(r.get("valor_total", 0)),
        ])
    tab_rub = _tabela(["Cód.", "Rubrica", "Grupo", "Lei criadora", "Propósito", "Custo"], rows_rub, "tbl")

    labels = json.dumps([l.get("lei_id", "") for l in por_lei], ensure_ascii=False)
    valores = json.dumps([round(l.get("valor_total", 0), 2) for l in por_lei])
    chart = f"""
    new Chart(document.getElementById('chartF_Leis'), {{
      type: 'bar',
      data: {{ labels: {labels}, datasets: [{{ label: 'Custo por diploma legal',
        data: {valores}, backgroundColor: '#0b6e4f' }}] }},
      options: {{ indexAxis: 'y', plugins: {{ legend: {{ display: false }} }},
        scales: {{ x: {{ ticks: {{ callback: v => 'R$ ' + (v/1e6).toFixed(1) + 'M' }} }} }} }}
    }});"""

    html = f"""<section id="legislacao">
      <h2>Legislação das gratificações <span class="muted">— cobertura {pct(cob)} do valor</span></h2>
      <p class="muted">Cada rubrica de gratificação foi associada à lei municipal que a criou,
      para revelar os direcionadores legais do custo. Rubricas sem lei localizada recebem grupo inferido.</p>
      <div class="chart-box"><canvas id="chartF_Leis" height="160"></canvas></div>
      <h3>Custo por diploma legal</h3>
      {tab_lei}
      <h3>Rubricas mapeadas</h3>
      {tab_rub}
      {_bloco_analise_leis(analise)}
    </section>"""
    return html, chart


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def build(tabelas_dir: Path, output_html: Path) -> Path:
    tabelas_dir = Path(tabelas_dir)
    dados = json.loads((tabelas_dir / "dados_consolidados.json").read_text(encoding="utf-8"))
    leg = None
    if (tabelas_dir / "rubricas_legislacao.json").exists():
        leg = json.loads((tabelas_dir / "rubricas_legislacao.json").read_text(encoding="utf-8"))
    analise_leg = None
    if (tabelas_dir / "analise_legislacao.json").exists():
        analise_leg = json.loads((tabelas_dir / "analise_legislacao.json").read_text(encoding="utf-8"))
    if (tabelas_dir / "insights.json").exists():
        insights = json.loads((tabelas_dir / "insights.json").read_text(encoding="utf-8"))
    else:
        insights = narrativa_fallback(dados)

    k = dados["kpis"]

    # ----- dados para charts -----
    vinc = dados.get("por_vinculo", [])
    vinc_labels = json.dumps([v["categoria_vinculo"] for v in vinc], ensure_ascii=False)
    vinc_vals = json.dumps([round(v["proventos_total"], 2) for v in vinc])

    faixas = dados.get("faixas", [])
    fx_labels = json.dumps([f["faixa"] for f in faixas], ensure_ascii=False)
    fx_vals = json.dumps([f["n"] for f in faixas])

    unid = dados.get("top_unidades", [])[:12]
    un_labels = json.dumps([u.get("nome_unidade", "") for u in unid], ensure_ascii=False)
    un_vals = json.dumps([round(u.get("proventos_total", 0), 2) for u in unid])

    cargos = dados.get("top_cargos", [])[:12]
    cg_labels = json.dumps([c.get("cargo", "") for c in cargos], ensure_ascii=False)
    cg_vals = json.dumps([round(c.get("proventos_total", 0), 2) for c in cargos])

    rub = dados.get("rubricas_top", [])[:15]
    rb_labels = json.dumps([r.get("descricao_rubrica", "")[:32] for r in rub], ensure_ascii=False)
    rb_vals = json.dumps([round(r.get("valor_total", 0), 2) for r in rub])

    # ----- tabelas HTML -----
    rows_vinc = [[_esc(v["categoria_vinculo"]), str(int(v["n"])), fmt_brl(v["proventos_total"]),
                  pct(v["pct_folha"]), fmt_brl(v["proventos_medio"])] for v in vinc]
    tab_vinc = _tabela(["Vínculo", "Servidores", "Custo total", "% folha", "Média"], rows_vinc, "tbl")

    rows_unid = [[_esc(u.get("nome_unidade", "")), str(int(u.get("n", 0))),
                  fmt_brl(u.get("proventos_total", 0)), pct(u.get("pct_folha", 0))] for u in dados.get("top_unidades", [])]
    tab_unid = _tabela(["Unidade", "Servidores", "Custo", "% folha"], rows_unid, "tbl")

    rows_cargo = [[_esc(c.get("cargo", "")), str(int(c.get("n", 0))),
                   fmt_brl(c.get("proventos_total", 0)), fmt_brl(c.get("proventos_medio", 0))] for c in dados.get("top_cargos", [])]
    tab_cargo = _tabela(["Cargo", "Servidores", "Custo", "Média"], rows_cargo, "tbl")

    rows_rub = [[_esc(r.get("codigo", "")), _esc(r.get("descricao_rubrica", "")), str(int(r.get("n_servidores", 0))),
                 fmt_brl(r.get("valor_total", 0)), pct(r.get("pct_folha", 0)), pct(r.get("pct_acum", 0))]
                for r in dados.get("rubricas_top", [])]
    tab_rub = _tabela(["Cód.", "Rubrica", "Serv.", "Custo", "% folha", "% acum."], rows_rub, "tbl")

    # Alertas (até 60 linhas para manter HTML leve)
    al = dados.get("alertas", [])[:60]
    rows_al = [[_esc(a.get("tipo", "")), _esc(a.get("matricula", "")), _esc(a.get("cargo", "")),
                _esc(a.get("categoria_vinculo", "")), fmt_brl(a.get("proventos", 0)), _esc(a.get("detalhe", ""))] for a in al]
    tab_al = _tabela(["Tipo", "Matrícula", "Cargo", "Vínculo", "Proventos", "Detalhe"], rows_al, "tbl")
    nota_al = "" if len(dados.get("alertas", [])) <= 60 else f'<p class="muted">Exibindo 60 de {len(dados.get("alertas", []))} ocorrências.</p>'

    leg_html, leg_chart = _secao_legislacao(leg, analise_leg)

    alertas_li = "".join(f"<li>{_esc(a)}</li>" for a in insights.get("alertas", []))
    recs_li = "".join(f"<li>{_esc(r)}</li>" for r in insights.get("recomendacoes", []))
    fonte_narr = "IA (síntese)" if insights.get("_fonte") != "fallback_deterministico" else "síntese determinística (sem IA)"

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Custo da Folha — Saúde / Sete Lagoas (Fev/2026)</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  :root {{ --ink:#1a1a2e; --accent:#0b6e4f; --accent2:#16557a; --muted:#6b7280; --bg:#f7f8fa; --card:#fff; --line:#e5e7eb; }}
  * {{ box-sizing:border-box; }}
  body {{ font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; margin:0; background:var(--bg); color:var(--ink); }}
  header {{ background:linear-gradient(120deg,#0b6e4f,#16557a); color:#fff; padding:36px 40px; }}
  header h1 {{ margin:0 0 6px; font-size:26px; }}
  header p {{ margin:0; opacity:.9; }}
  .wrap {{ max-width:1180px; margin:0 auto; padding:24px 40px 60px; }}
  .hero {{ background:var(--card); border-left:5px solid var(--accent); border-radius:8px; padding:20px 24px; margin:24px 0;
           font-size:18px; font-weight:600; box-shadow:0 1px 3px rgba(0,0,0,.06); }}
  .kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:16px; margin:8px 0 28px; }}
  .kpi {{ background:var(--card); border:1px solid var(--line); border-radius:8px; padding:16px 18px; }}
  .kpi-label {{ font-size:12px; color:var(--muted); text-transform:uppercase; letter-spacing:.04em; }}
  .kpi-value {{ font-size:26px; font-weight:700; margin:6px 0 2px; color:var(--accent2); }}
  .kpi-sub {{ font-size:12px; color:var(--muted); }}
  section {{ background:var(--card); border:1px solid var(--line); border-radius:8px; padding:22px 26px; margin:18px 0; }}
  h2 {{ margin:0 0 4px; font-size:20px; }}
  h3 {{ margin:22px 0 8px; font-size:15px; color:var(--accent2); }}
  .muted {{ color:var(--muted); font-weight:400; font-size:13px; }}
  .grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:24px; }}
  .chart-box {{ position:relative; margin:10px 0; }}
  table.tbl {{ width:100%; border-collapse:collapse; font-size:13px; margin-top:8px; }}
  table.tbl th {{ text-align:left; background:#f1f3f5; padding:8px 10px; border-bottom:2px solid var(--line); }}
  table.tbl td {{ padding:7px 10px; border-bottom:1px solid var(--line); }}
  table.tbl tr:hover td {{ background:#fafbfc; }}
  .badge {{ background:#fde68a; color:#92400e; border-radius:4px; padding:1px 6px; font-size:11px; }}
  ul.insights li {{ margin:6px 0; }}
  footer {{ color:var(--muted); font-size:12px; text-align:center; padding:30px; }}
  @media(max-width:820px){{ .grid2{{grid-template-columns:1fr;}} .wrap{{padding:16px;}} header{{padding:24px;}} }}
</style>
</head>
<body>
<header>
  <h1>Custo da Folha — Secretaria de Saúde de Sete Lagoas (MG)</h1>
  <p>Competência {k['competencia']} · {k['n_ativos']:,} servidores ativos · bruto {fmt_brl(k['proventos_total'])} · narrativa: {fonte_narr}</p>
</header>
<div class="wrap">

  <div class="hero">{_esc(insights.get('action_title',''))}</div>

  <div class="kpis">{_kpi_cards(k)}</div>

  <section id="pessoal">
    <h2>Composição do custo de pessoal</h2>
    <div class="grid2">
      <div>
        <h3>Custo por vínculo</h3>
        <div class="chart-box"><canvas id="chartF_Vinculo" height="220"></canvas></div>
      </div>
      <div>
        <h3>Distribuição por faixa de remuneração</h3>
        <div class="chart-box"><canvas id="chartF_Faixas" height="220"></canvas></div>
      </div>
    </div>
    {tab_vinc}
    <p class="muted" style="margin-top:14px">{_esc(insights.get('cruzamento',''))}</p>
  </section>

  <section>
    <h2>Onde o dinheiro está</h2>
    <div class="grid2">
      <div>
        <h3>Top unidades por custo</h3>
        <div class="chart-box"><canvas id="chartF_Unidades" height="260"></canvas></div>
      </div>
      <div>
        <h3>Top cargos por custo</h3>
        <div class="chart-box"><canvas id="chartF_Cargos" height="260"></canvas></div>
      </div>
    </div>
    <h3>Unidades</h3>{tab_unid}
    <h3>Cargos</h3>{tab_cargo}
  </section>

  <section>
    <h2>Concentração de rubricas</h2>
    <p class="muted">As 10 maiores rubricas explicam {pct(dados.get('rubricas_pareto',{}).get('top10_pct',0))}
       dos proventos; as 20 maiores, {pct(dados.get('rubricas_pareto',{}).get('top20_pct',0))}.</p>
    <div class="chart-box"><canvas id="chartF_Rubricas" height="200"></canvas></div>
    {tab_rub}
  </section>

  {leg_html}

  <section>
    <h2>Análise e recomendações <span class="muted">— {fonte_narr}</span></h2>
    <p>{_esc(insights.get('analise_folha',''))}</p>
    <h3>Pontos de atenção</h3><ul class="insights">{alertas_li}</ul>
    <h3>Recomendações</h3><ul class="insights">{recs_li}</ul>
  </section>

  <section>
    <h2>Ocorrências sinalizadas</h2>
    <p class="muted">Elite &gt; R$ 20k, descontos &gt; 50% dos proventos e outliers por cargo (IQR).</p>
    {nota_al}{tab_al}
  </section>

</div>
<footer>Gerado automaticamente · dados de competência {k['competencia']} · análise gerencial (não-forense) · Sete Lagoas (MG)</footer>

<script>
Chart.defaults.font.family = "-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif";
const BRL = v => 'R$ ' + (v>=1e6 ? (v/1e6).toFixed(1)+'M' : (v/1e3).toFixed(0)+'k');
new Chart(document.getElementById('chartF_Vinculo'), {{
  type:'doughnut',
  data:{{ labels:{vinc_labels}, datasets:[{{ data:{vinc_vals},
    backgroundColor:['#0b6e4f','#16557a','#d97706','#9333ea','#dc2626','#0891b2'] }}] }},
  options:{{ plugins:{{ legend:{{ position:'bottom' }}, tooltip:{{ callbacks:{{ label:c=>c.label+': '+BRL(c.parsed) }} }} }} }}
}});
new Chart(document.getElementById('chartF_Faixas'), {{
  type:'bar',
  data:{{ labels:{fx_labels}, datasets:[{{ label:'Servidores', data:{fx_vals}, backgroundColor:'#16557a' }}] }},
  options:{{ plugins:{{ legend:{{ display:false }} }} }}
}});
new Chart(document.getElementById('chartF_Unidades'), {{
  type:'bar',
  data:{{ labels:{un_labels}, datasets:[{{ label:'Custo', data:{un_vals}, backgroundColor:'#0b6e4f' }}] }},
  options:{{ indexAxis:'y', plugins:{{ legend:{{ display:false }} }},
    scales:{{ x:{{ ticks:{{ callback:BRL }} }} }} }}
}});
new Chart(document.getElementById('chartF_Cargos'), {{
  type:'bar',
  data:{{ labels:{cg_labels}, datasets:[{{ label:'Custo', data:{cg_vals}, backgroundColor:'#16557a' }}] }},
  options:{{ indexAxis:'y', plugins:{{ legend:{{ display:false }} }},
    scales:{{ x:{{ ticks:{{ callback:BRL }} }} }} }}
}});
new Chart(document.getElementById('chartF_Rubricas'), {{
  type:'bar',
  data:{{ labels:{rb_labels}, datasets:[{{ label:'Custo', data:{rb_vals}, backgroundColor:'#d97706' }}] }},
  options:{{ indexAxis:'y', plugins:{{ legend:{{ display:false }} }},
    scales:{{ x:{{ ticks:{{ callback:BRL }} }} }} }}
}});
{leg_chart}
</script>
</body>
</html>"""

    output_html = Path(output_html)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(html, encoding="utf-8")
    return output_html


if __name__ == "__main__":
    import sys
    base = Path(__file__).resolve().parent.parent
    tdir = Path(sys.argv[1]) if len(sys.argv) > 1 else base / "analysis" / "tabelas"
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else base / "output" / "relatorio_custos_folha_saude_setelagoas.html"
    p = build(tdir, out)
    kb = p.stat().st_size / 1024
    print(f"OK — {p} ({kb:.0f} KB)")
