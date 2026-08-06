#!/usr/bin/env python3
"""
build_html_educacao.py — Task 5
Gera relatorio_custos_educacao_2025.html no estilo McKinsey com Chart.js.
Inclui seção extra de análise de pessoal via educ-10-2025.xlsx.
"""
import os, sys, json
import pandas as pd
from pathlib import Path

# Importar utilitários compartilhados de build_html_saude
sys.path.insert(0, str(Path(__file__).parent))
from build_html_saude import (
    CSS, JS_UTILS, fmt_brl, fmt_m, pct,
    carregar_dados,
    gerar_analise_opus, gerar_action_titles_fallback,
    gerar_recomendacoes_fallback,
    tabela_programas_html, tabela_fornecedores_html, heatmap_categorias_html,
)

SCRIPT_DIR  = Path(__file__).resolve().parent
TABELAS_DIR = SCRIPT_DIR / "tabelas"
EDUC_DIR    = TABELAS_DIR / "educacao"
OUTPUT_HTML = SCRIPT_DIR / "relatorio_custos_educacao_2025.html"
EDUC_XLSX   = SCRIPT_DIR.parent / "educ-10-2025.xlsx"

SECRETARIA     = "Educação"
SECRETARIA_KEY = "educacao"


# ---------------------------------------------------------------------------
# Análise de Pessoal (xlsx)
# ---------------------------------------------------------------------------
def analisar_pessoal(xlsx_path: Path) -> dict:
    """Lê educ-10-2025.xlsx e extrai análises de pessoal."""
    print(f"\n  Lendo planilha de pessoal: {xlsx_path.name}")

    if not xlsx_path.exists():
        print("  [AVISO] Arquivo não encontrado — seção de pessoal será omitida")
        return {}

    try:
        df = pd.read_excel(xlsx_path, sheet_name="Total", engine="openpyxl")
    except Exception as e:
        try:
            df = pd.read_excel(xlsx_path, engine="openpyxl")
        except Exception as e2:
            print(f"  [ERRO] Não foi possível ler xlsx: {e2}")
            return {}

    print(f"  Shape: {df.shape} ({len(df)} servidores, {len(df.columns)} colunas)")
    print(f"  Colunas: {list(df.columns[:15])}…")

    resultado = {}

    # Tentar identificar colunas relevantes
    cols_lower = {c.lower().strip(): c for c in df.columns}

    def find_col(*candidates):
        for c in candidates:
            if c in cols_lower:
                return cols_lower[c]
            # busca parcial
            for k in cols_lower:
                if c in k:
                    return cols_lower[k]
        return None

    col_liquido    = find_col("liquido", "líquido", "liq", "salario liquido", "vencimento liquido")
    col_bruto      = find_col("proventos", "bruto", "total bruto", "vencimento bruto", "total proventos")
    # "Local de trabalho" contém os nomes reais das escolas/unidades;
    # "Escola" é apenas uma flag categórica ("Escola" / "Outros")
    col_escola     = find_col("local de trabalho", "lotacao", "lotação", "unidade")
    col_cargo      = find_col("cargo", "funcao", "função")
    col_tipo       = find_col("tipo contrato", "tipo_contrato", "vinculo", "vínculo", "tipo aposentadoria")
    col_nome       = find_col("nome", "servidor")

    print(f"  Colunas mapeadas: liquido={col_liquido}, bruto={col_bruto}, escola={col_escola}, tipo={col_tipo}")

    # Usar a melhor coluna de valor disponível
    col_valor = col_bruto or col_liquido
    if col_valor:
        if df[col_valor].dtype == object:
            df[col_valor] = pd.to_numeric(
                df[col_valor].astype(str).str.replace(r"[^0-9,.]", "", regex=True).str.replace(",", "."),
                errors="coerce"
            ).fillna(0)
        else:
            df[col_valor] = pd.to_numeric(df[col_valor], errors="coerce").fillna(0)

    resultado["total_servidores"] = len(df)

    # Por tipo de contrato
    if col_tipo and col_valor:
        tipo_agg = df.groupby(col_tipo)[col_valor].agg(["sum", "count"]).reset_index()
        tipo_agg.columns = ["tipo", "total", "qtd"]
        tipo_agg = tipo_agg.sort_values("total", ascending=False)
        resultado["por_tipo"] = tipo_agg.to_dict("records")
    else:
        resultado["por_tipo"] = []

    # Top 10 escolas por custo
    if col_escola and col_valor:
        escola_agg = df.groupby(col_escola)[col_valor].agg(["sum", "count"]).reset_index()
        escola_agg.columns = ["escola", "total", "servidores"]
        escola_agg = escola_agg.sort_values("total", ascending=False).head(10)
        resultado["top_escolas"] = escola_agg.to_dict("records")
    else:
        resultado["top_escolas"] = []

    # Distribuição de proventos (histograma por faixas)
    if col_valor:
        vals = df[col_valor].dropna()
        vals = vals[vals > 0]
        faixas = [0, 3000, 5000, 8000, 10000, float("inf")]
        labels = ["Até R$ 3k", "R$ 3–5k", "R$ 5–8k", "R$ 8–10k", "Acima R$ 10k"]
        counts = []
        for i in range(len(faixas) - 1):
            n = ((vals > faixas[i]) & (vals <= faixas[i+1])).sum()
            counts.append(int(n))
        resultado["hist_faixas"] = {"labels": labels, "values": counts}

        # Servidores acima de R$ 10k
        acima_10k = df[df[col_valor] > 10000]
        resultado["acima_10k"] = {
            "qtd": int(len(acima_10k)),
            "total": float(acima_10k[col_valor].sum()),
            "pct_servidores": float(len(acima_10k) / len(df) * 100) if len(df) else 0,
        }
        resultado["total_folha"] = float(vals.sum())
        resultado["media_provento"] = float(vals.mean())
    else:
        resultado["hist_faixas"] = {"labels": [], "values": []}
        resultado["acima_10k"] = {"qtd": 0, "total": 0, "pct_servidores": 0}
        resultado["total_folha"] = 0
        resultado["media_provento"] = 0

    print(f"  Análise de pessoal: {resultado['total_servidores']} servidores, "
          f"folha total R$ {resultado.get('total_folha', 0):,.0f}")

    return resultado


# ---------------------------------------------------------------------------
# Construir HTML da Educação
# ---------------------------------------------------------------------------
def build_html_educacao(dados: dict, titles: dict, recs: list,
                         pessoal: dict, secretaria: str,
                         analise_cruzada: str = "", alertas: list = None) -> str:
    kpis   = dados["kpis"]
    prog   = dados["programas"]
    nat    = dados["natureza"]
    acoes  = dados["acoes"]
    forn   = dados["fornecedores"]
    cat    = dados["categorias"]
    cat_m  = dados["cat_mensal"]
    serie  = dados["serie"]
    fontes = dados["fontes"]
    conc   = dados["concentracao"]

    def to_js(df, cols):
        if df.empty:
            return "[]", "[]"
        labels = [str(r[cols[0]])[:55] for _, r in df.iterrows()]
        values = [float(r[cols[1]]) for _, r in df.iterrows()]
        return json.dumps(labels), json.dumps(values)

    prog_labels,  prog_values  = to_js(prog,  ["dsc_programa", "vlr_pago"])
    nat_col = "macro_natureza" if "macro_natureza" in nat.columns else nat.columns[0]
    nat_labels,   nat_values   = to_js(nat,   [nat_col, "vlr_pago"])
    acao_labels,  acao_values  = to_js(acoes, ["dsc_acao", "vlr_pago"])
    forn_labels,  forn_values  = to_js(forn,  ["nom_credor", "total_pago"])
    cat_col = "categoria_nome" if "categoria_nome" in cat.columns else cat.columns[0]
    cat_labels,   cat_values   = to_js(cat,   [cat_col, "vlr_empenhado"])
    fonte_col = "fonte" if "fonte" in fontes.columns else fontes.columns[0]
    fonte_labels, fonte_values = to_js(fontes, [fonte_col, "vlr_pago"])
    pareto_labels = json.dumps(list(forn["nom_credor"].str[:30]) if not forn.empty else [])
    pareto_values = json.dumps([float(v) for v in forn["pct_acumulado"]] if not forn.empty else [])

    if not serie.empty:
        serie_labels = json.dumps(list(serie["mes_nome"]))
        serie_values = json.dumps([float(v) for v in serie["vlr_pago"]])
        serie_media  = float(serie["vlr_pago"].mean())
    else:
        serie_labels = "[]"; serie_values = "[]"; serie_media = 0

    # Dados pessoal
    hist_labels = json.dumps(pessoal.get("hist_faixas", {}).get("labels", []))
    hist_values = json.dumps(pessoal.get("hist_faixas", {}).get("values", []))

    tipos_p = pessoal.get("por_tipo", [])
    tipo_labels = json.dumps([str(r.get("tipo", ""))[:30] for r in tipos_p])
    tipo_values = json.dumps([float(r.get("total", 0)) for r in tipos_p])

    escolas_p = pessoal.get("top_escolas", [])
    escola_labels = json.dumps([str(r.get("escola", ""))[:40] for r in escolas_p])
    escola_values = json.dumps([float(r.get("total", 0)) for r in escolas_p])

    # Tabelas HTML
    tab_prog  = tabela_programas_html(prog)
    tab_forn  = tabela_fornecedores_html(forn)
    tab_heat  = heatmap_categorias_html(cat_m)

    # Tabela de tipos de contrato
    tab_tipos = ""
    if tipos_p:
        total_folha = pessoal.get("total_folha", 1) or 1
        rows = ""
        for r in tipos_p:
            pct_v = r.get("total", 0) / total_folha * 100
            rows += f"<tr><td>{r.get('tipo','')}</td><td class='num-col'>{int(r.get('qtd',0))}</td><td class='num-col'>{fmt_brl(r.get('total',0))}</td><td class='num-col'>{pct_v:.1f}%</td></tr>"
        tab_tipos = f"""<table class='data-table' style='margin-top:1rem'>
            <thead><tr><th>Tipo de Contrato</th><th class='num-col'>Servidores</th><th class='num-col'>Total Proventos</th><th class='num-col'>% Folha</th></tr></thead>
            <tbody>{rows}</tbody></table>"""

    # Tabela top escolas
    tab_escolas = ""
    if escolas_p:
        rows = ""
        for i, r in enumerate(escolas_p):
            rows += f"<tr><td>{i+1}</td><td>{r.get('escola','')[:50]}</td><td class='num-col'>{int(r.get('servidores',0))}</td><td class='num-col'>{fmt_brl(r.get('total',0))}</td></tr>"
        tab_escolas = f"""<table class='data-table' style='margin-top:1rem'>
            <thead><tr><th>#</th><th>Escola/Unidade</th><th class='num-col'>Servidores</th><th class='num-col'>Custo Total</th></tr></thead>
            <tbody>{rows}</tbody></table>"""

    if alertas is None:
        alertas = []

    t = titles
    acima = pessoal.get("acima_10k", {})
    total_serv = pessoal.get("total_servidores", 0)
    total_folha = pessoal.get("total_folha", 0)
    media_prov  = pessoal.get("media_provento", 0)

    pessoal_title = (
        f"{acima.get('qtd', 0)} servidores ({acima.get('pct_servidores', 0):.1f}%) "
        f"recebem acima de R$ 10 mil; folha total de {fmt_brl(total_folha)}"
        if total_serv > 0 else
        "Análise de pessoal da Educação — folha de 10 meses de 2025"
    )

    kpi_total   = kpis.get("total_pago", 0)
    kpi_emp     = kpis.get("total_empenhado", 0)
    kpi_forn    = kpis.get("num_fornecedores", 0)
    kpi_empenho = kpis.get("num_empenhos", 0)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Custos da {secretaria} — Sete Lagoas 2025</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>{CSS}</style>
</head>
<body>

<nav class="nav-sidebar">
    <div class="nav-logo">🎓 Custos {secretaria}<small>Sete Lagoas · 2025</small></div>
    <a href="#hero">Resumo Executivo</a>
    <a href="#programas">Composição por Programa</a>
    <a href="#natureza">Natureza de Despesa</a>
    <a href="#acoes">Por Ação</a>
    <a href="#fornecedores">Fornecedores</a>
    <a href="#categorias">Categorias de Custo</a>
    <a href="#mensal">Evolução Mensal</a>
    <a href="#fontes">Fontes de Recurso</a>
    <a href="#pessoal">Análise de Pessoal</a>
    <a href="#sintese">Síntese Analítica</a>
    <a href="#recomendacoes">Recomendações</a>
</nav>

<div class="main-content">

<!-- HERO -->
<section class="hero" id="hero">
    <h1>Custos da {secretaria} — Sete Lagoas 2025</h1>
    <div class="periodo">🎓 {kpis.get('periodo', '2025')} · Sete Lagoas (MG) · SICOM/TCE-MG + Folha de Pessoal</div>
    <p class="action-title-hero">{t.get('hero', '')}</p>
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">Total Pago</div>
            <div class="kpi-value">{fmt_m(kpi_total)}</div>
            <div class="kpi-sub">{fmt_brl(kpi_total)}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Total Empenhado</div>
            <div class="kpi-value">{fmt_m(kpi_emp)}</div>
            <div class="kpi-sub">{fmt_brl(kpi_emp)}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Servidores</div>
            <div class="kpi-value">{total_serv:,}</div>
            <div class="kpi-sub">folha 10 meses 2025</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Fornecedores</div>
            <div class="kpi-value">{kpi_forn:,}</div>
            <div class="kpi-sub">{kpi_empenho:,} empenhos</div>
        </div>
    </div>
</section>

<!-- PROGRAMAS -->
<section class="section" id="programas">
    <div class="section-id">Seção 2 — Composição por Programa</div>
    <div class="action-title">{t.get('programas', 'Composição por programa orçamentário')}</div>
    <div class="chart-container"><canvas id="chartProg"></canvas></div>
    {tab_prog}
</section>

<!-- NATUREZA -->
<section class="section" id="natureza">
    <div class="section-id">Seção 3 — Natureza de Despesa</div>
    <div class="action-title">{t.get('natureza', 'Composição por natureza de despesa')}</div>
    <div class="chart-container short"><canvas id="chartNat"></canvas></div>
</section>

<!-- AÇÕES -->
<section class="section" id="acoes">
    <div class="section-id">Seção 4 — Composição por Ação</div>
    <div class="action-title">{t.get('acoes', 'Top ações por valor pago')}</div>
    <div class="chart-container tall"><canvas id="chartAcoes"></canvas></div>
</section>

<!-- FORNECEDORES -->
<section class="section" id="fornecedores">
    <div class="section-id">Seção 5 — Top Fornecedores</div>
    <div class="action-title">{t.get('fornecedores', 'Ranking de fornecedores por valor pago')}</div>
    <div class="chart-container"><canvas id="chartForn"></canvas></div>
    <div class="chart-container short" style="margin-top:1.5rem">
        <canvas id="chartPareto"></canvas>
    </div>
    {tab_forn}
</section>

<!-- CATEGORIAS -->
<section class="section" id="categorias">
    <div class="section-id">Seção 6 — Categorias de Custo</div>
    <div class="action-title">{t.get('categorias', 'Composição por categoria de custo')}</div>
    <div class="chart-container short"><canvas id="chartCat"></canvas></div>
    {tab_heat}
</section>

<!-- MENSAL -->
<section class="section" id="mensal">
    <div class="section-id">Seção 7 — Evolução Mensal</div>
    <div class="action-title">{t.get('mensal', 'Evolução mensal de gastos em 2025')}</div>
    <div class="chart-container"><canvas id="chartMensal"></canvas></div>
</section>

<!-- FONTES -->
<section class="section" id="fontes">
    <div class="section-id">Seção 8 — Fontes de Recurso</div>
    <div class="action-title">{t.get('fontes', 'Composição por fonte de recurso')}</div>
    <div class="chart-container short"><canvas id="chartFontes"></canvas></div>
</section>

<!-- PESSOAL -->
<section class="section" id="pessoal">
    <div class="section-id">Seção 9 — Análise de Pessoal (Folha 2025)</div>
    <div class="action-title">{pessoal_title}</div>
    {"<p style='color:var(--cinza-medio);font-size:0.9rem'>Dados de pessoal não disponíveis.</p>" if not total_serv else f'''
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:1rem;margin-bottom:1.5rem">
        <div class="kpi-card" style="background:var(--azul-escuro);color:white">
            <div class="kpi-label">Total Servidores</div>
            <div class="kpi-value">{total_serv:,}</div>
        </div>
        <div class="kpi-card" style="background:var(--azul-escuro);color:white">
            <div class="kpi-label">Total Folha</div>
            <div class="kpi-value">{fmt_m(total_folha)}</div>
            <div class="kpi-sub">{fmt_brl(total_folha)}</div>
        </div>
        <div class="kpi-card" style="background:var(--azul-escuro);color:white">
            <div class="kpi-label">Média por Servidor</div>
            <div class="kpi-value">{fmt_brl(media_prov)}</div>
        </div>
        <div class="kpi-card" style="background:var(--vermelho);color:white">
            <div class="kpi-label">Acima R$ 10 mil</div>
            <div class="kpi-value">{acima.get('qtd',0):,}</div>
            <div class="kpi-sub">{acima.get('pct_servidores',0):.1f}% dos servidores</div>
        </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem">
        <div>
            <h4 style="color:var(--azul-escuro);margin-bottom:0.5rem;font-size:0.95rem">Distribuição de Proventos</h4>
            <div class="chart-container short"><canvas id="chartHist"></canvas></div>
        </div>
        <div>
            <h4 style="color:var(--azul-escuro);margin-bottom:0.5rem;font-size:0.95rem">Custo por Tipo de Contrato</h4>
            <div class="chart-container short"><canvas id="chartTipos"></canvas></div>
        </div>
    </div>
    {tab_tipos}
    <h4 style="color:var(--azul-escuro);margin:1.5rem 0 0.5rem;font-size:0.95rem">Top 10 Escolas por Custo de Pessoal</h4>
    <div class="chart-container" style="height:320px"><canvas id="chartEscolas"></canvas></div>
    {tab_escolas}
    '''}
</section>

<!-- SÍNTESE ANALÍTICA -->
<section class="section" id="sintese">
    <div class="section-id">Síntese — Análise Consolidada</div>
    <div class="action-title">Padrões cruzados que revelam o perfil de gestão da Secretaria de {secretaria}</div>
    {f'<div class="analise-cruzada">{analise_cruzada}</div>' if analise_cruzada else ''}
    {f'''<p class="alertas-titulo">⚠ Alertas Prioritários</p>
    <div class="alerta-grid">{"".join(f'<div class="alerta-card">{a}</div>' for a in alertas)}</div>''' if alertas else ''}
</section>

<!-- RECOMENDAÇÕES -->
<section class="section" id="recomendacoes">
    <div class="section-id">Seção 10 — Recomendações de Gestão</div>
    <div class="action-title">Quatro ações prioritárias para melhorar a gestão de custos de {secretaria}</div>
    <div class="rec-grid">
        {"".join(f'''<div class="rec-card">
            <div class="rec-label">Recomendação {i+1}</div>
            <p class="rec-insight">{r.get('insight','')}</p>
            <p class="rec-implicacao">{r.get('implicacao','')}</p>
            <p class="rec-acao">{r.get('acao','')}</p>
        </div>''' for i, r in enumerate(recs))}
    </div>
</section>

</div><!-- main-content -->

<script>
{JS_UTILS}

// ---- DATA ----
const PROG_LABELS   = {prog_labels};
const PROG_VALUES   = {prog_values};
const NAT_LABELS    = {nat_labels};
const NAT_VALUES    = {nat_values};
const ACAO_LABELS   = {acao_labels};
const ACAO_VALUES   = {acao_values};
const FORN_LABELS   = {forn_labels};
const FORN_VALUES   = {forn_values};
const CAT_LABELS    = {cat_labels};
const CAT_VALUES    = {cat_values};
const SERIE_LABELS  = {serie_labels};
const SERIE_VALUES  = {serie_values};
const SERIE_MEDIA   = {serie_media};
const FONTE_LABELS  = {fonte_labels};
const FONTE_VALUES  = {fonte_values};
const PARETO_LABELS = {pareto_labels};
const PARETO_VALUES = {pareto_values};
const KPI_TOTAL     = {kpi_total};
const HIST_LABELS   = {hist_labels};
const HIST_VALUES   = {hist_values};
const TIPO_LABELS   = {tipo_labels};
const TIPO_VALUES   = {tipo_values};
const ESCOLA_LABELS = {escola_labels};
const ESCOLA_VALUES = {escola_values};

// ---- CHARTS ----
// 1. Programas
new Chart(document.getElementById('chartProg'), {{
    type: 'bar',
    data: {{ labels: PROG_LABELS,
        datasets: [{{ data: PROG_VALUES, backgroundColor: '#2E86AB', borderRadius:4, barPercentage:0.7 }}] }},
    options: {{
        indexAxis: 'y',
        plugins: {{ legend:{{display:false}}, tooltip:{{callbacks:{{label: ctx=>formatBRL(ctx.raw)}}}} }},
        scales: {{ x:{{ticks:{{callback:v=>formatM(v)}},grid:{{display:false}}}}, y:{{grid:{{display:false}}}} }}
    }}
}});

// 2. Natureza
new Chart(document.getElementById('chartNat'), {{
    type: 'doughnut',
    data: {{ labels: NAT_LABELS,
        datasets: [{{ data: NAT_VALUES, backgroundColor: CORES.palette, borderWidth:2, borderColor:'#fff' }}] }},
    options: {{
        cutout: '58%',
        plugins: {{
            legend:{{position:'right',labels:{{font:{{size:11}}}}}},
            tooltip:{{callbacks:{{label:ctx=>{{
                const tot=ctx.dataset.data.reduce((a,b)=>a+b,0);
                return ctx.label+': '+formatBRL(ctx.raw)+' ('+(ctx.raw/tot*100).toFixed(1)+'%)';
            }}}}}}
        }}
    }}
}});

// 3. Ações
new Chart(document.getElementById('chartAcoes'), {{
    type:'bar',
    data:{{ labels:ACAO_LABELS,
        datasets:[{{ data:ACAO_VALUES,
            backgroundColor:ACAO_VALUES.map((_,i)=>i===0?CORES.vermelho:CORES.principal),
            borderRadius:4, barPercentage:0.65 }}] }},
    options:{{
        indexAxis:'y',
        plugins:{{legend:{{display:false}},
            tooltip:{{callbacks:{{label:ctx=>formatBRL(ctx.raw)+' ('+(ctx.raw/KPI_TOTAL*100).toFixed(1)+'%)'}}}}
        }},
        scales:{{x:{{ticks:{{callback:v=>formatM(v)}},grid:{{display:false}}}},
                 y:{{grid:{{display:false}},ticks:{{font:{{size:10}}}}}}
        }}
    }}
}});

// 4. Fornecedores
new Chart(document.getElementById('chartForn'), {{
    type:'bar',
    data:{{ labels:FORN_LABELS,
        datasets:[{{ data:FORN_VALUES,
            backgroundColor:FORN_VALUES.map((_,i)=>i<3?CORES.vermelho:CORES.principal),
            borderRadius:4, barPercentage:0.65 }}] }},
    options:{{
        indexAxis:'y',
        plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:ctx=>formatBRL(ctx.raw)}}}}}},
        scales:{{x:{{ticks:{{callback:v=>formatM(v)}},grid:{{display:false}}}},y:{{grid:{{display:false}},ticks:{{font:{{size:10}}}}}}}}
    }}
}});

// 5. Pareto
new Chart(document.getElementById('chartPareto'), {{
    type:'line',
    data:{{ labels:PARETO_LABELS,
        datasets:[{{label:'% Acumulado',data:PARETO_VALUES,
            borderColor:CORES.vermelho,backgroundColor:CORES.vermelho+'20',
            tension:0.2,fill:true,pointRadius:4}}] }},
    options:{{
        plugins:{{legend:{{display:true}},tooltip:{{callbacks:{{label:ctx=>ctx.raw.toFixed(1)+'%'}}}}}},
        scales:{{x:{{grid:{{display:false}},ticks:{{font:{{size:9}},maxRotation:45}}}},y:{{min:0,max:100,ticks:{{callback:v=>v+'%'}}}}}}
    }}
}});

// 6. Categorias
new Chart(document.getElementById('chartCat'), {{
    type:'doughnut',
    data:{{ labels:CAT_LABELS,
        datasets:[{{ data:CAT_VALUES, backgroundColor:CORES.palette, borderWidth:2, borderColor:'#fff' }}] }},
    options:{{
        cutout:'55%',
        plugins:{{
            legend:{{position:'right',labels:{{font:{{size:11}}}}}},
            tooltip:{{callbacks:{{label:ctx=>{{
                const tot=ctx.dataset.data.reduce((a,b)=>a+b,0);
                return ctx.label+': '+formatBRL(ctx.raw)+' ('+(ctx.raw/tot*100).toFixed(1)+'%)';
            }}}}}}
        }}
    }}
}});

// 7. Evolução mensal
new Chart(document.getElementById('chartMensal'), {{
    type:'line',
    data:{{ labels:SERIE_LABELS,
        datasets:[
            {{ label:'Valor Pago', data:SERIE_VALUES,
               borderColor:CORES.principal, backgroundColor:CORES.principal+'25',
               tension:0.3, fill:true,
               pointBackgroundColor: SERIE_VALUES.map(v=>v===Math.max(...SERIE_VALUES)?CORES.vermelho:CORES.principal),
               pointRadius: SERIE_VALUES.map(v=>v===Math.max(...SERIE_VALUES)?8:5) }},
            {{ label:'Média', data:SERIE_LABELS.map(()=>SERIE_MEDIA),
               borderColor:CORES.amarelo, borderDash:[6,4], borderWidth:2, pointRadius:0, fill:false }}
        ] }},
    options:{{
        plugins:{{legend:{{display:true}},tooltip:{{callbacks:{{label:ctx=>ctx.dataset.label+': '+formatBRL(ctx.raw)}}}}}},
        scales:{{x:{{grid:{{display:false}}}},y:{{ticks:{{callback:v=>formatM(v)}}}}}}
    }}
}});

// 8. Fontes
new Chart(document.getElementById('chartFontes'), {{
    type:'bar',
    data:{{ labels:FONTE_LABELS,
        datasets:[{{ data:FONTE_VALUES, backgroundColor:CORES.palette, borderRadius:4, barPercentage:0.65 }}] }},
    options:{{
        indexAxis:'y',
        plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:ctx=>formatBRL(ctx.raw)}}}}}},
        scales:{{x:{{ticks:{{callback:v=>formatM(v)}},grid:{{display:false}}}},y:{{grid:{{display:false}}}}}}
    }}
}});

// 9. Pessoal — histograma de proventos
if (document.getElementById('chartHist') && HIST_LABELS.length > 0) {{
    new Chart(document.getElementById('chartHist'), {{
        type:'bar',
        data:{{ labels:HIST_LABELS,
            datasets:[{{ data:HIST_VALUES,
                backgroundColor:['#28A745','#2E86AB','#F4A261','#E63946','#1B3A5C'],
                borderRadius:4, barPercentage:0.7 }}] }},
        options:{{
            plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:ctx=>ctx.raw+' servidores'}}}}}},
            scales:{{x:{{grid:{{display:false}}}},y:{{ticks:{{callback:v=>v+' serv.'}}}}}}
        }}
    }});
}}

// 10. Pessoal — por tipo de contrato
if (document.getElementById('chartTipos') && TIPO_LABELS.length > 0) {{
    new Chart(document.getElementById('chartTipos'), {{
        type:'doughnut',
        data:{{ labels:TIPO_LABELS,
            datasets:[{{ data:TIPO_VALUES, backgroundColor:CORES.palette, borderWidth:2, borderColor:'#fff' }}] }},
        options:{{
            cutout:'55%',
            plugins:{{
                legend:{{position:'bottom',labels:{{font:{{size:10}}}}}},
                tooltip:{{callbacks:{{label:ctx=>ctx.label+': '+formatBRL(ctx.raw)}}}}
            }}
        }}
    }});
}}

// 11. Pessoal — top escolas
if (document.getElementById('chartEscolas') && ESCOLA_LABELS.length > 0) {{
    new Chart(document.getElementById('chartEscolas'), {{
        type:'bar',
        data:{{ labels:ESCOLA_LABELS,
            datasets:[{{ data:ESCOLA_VALUES, backgroundColor:'#2E86AB', borderRadius:4, barPercentage:0.7 }}] }},
        options:{{
            indexAxis:'y',
            plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:ctx=>formatBRL(ctx.raw)}}}}}},
            scales:{{x:{{ticks:{{callback:v=>formatM(v)}},grid:{{display:false}}}},y:{{grid:{{display:false}},ticks:{{font:{{size:10}}}}}}}}
        }}
    }});
}}
</script>
</body>
</html>"""

    return html


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("TASK 5 — build_html_educacao.py")
    print("=" * 60)

    if not EDUC_DIR.exists():
        print(f"[ERRO] {EDUC_DIR} não existe — execute tasks anteriores primeiro")
        sys.exit(1)

    # Carregar dados orçamentários
    print("\nCarregando dados de Educação…")
    dados = carregar_dados(EDUC_DIR)
    kpis = dados["kpis"]
    print(f"  Total pago: {fmt_brl(kpis.get('total_pago', 0))}")
    print(f"  Período: {kpis.get('periodo', 'N/A')}")

    # Análise de pessoal
    pessoal = analisar_pessoal(EDUC_XLSX)

    # API Claude
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    client  = None
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            print("[OK] API Claude disponível")
        except Exception as e:
            print(f"[AVISO] Falha ao conectar API: {e}")

    # Gerar análise via Opus (uma chamada completa) ou fallback
    analise_cruzada = ""
    alertas = []

    print("\nGerando análise com Opus (chamada única)…")
    if client:
        try:
            analise = gerar_analise_opus(client, dados, SECRETARIA)
            titles  = analise.get("action_titles", {})
            recs    = analise.get("recomendacoes", [])
            analise_cruzada = analise.get("analise_cruzada", "")
            alertas = analise.get("alertas", [])
            fallback = gerar_action_titles_fallback(dados, SECRETARIA)
            for k in fallback:
                if not titles.get(k):
                    titles[k] = fallback[k]
            print(f"  [OK] Opus retornou {len(titles)} títulos, {len(recs)} recomendações, {len(alertas)} alertas")
        except Exception as e:
            print(f"  [AVISO] Opus falhou ({e}) — usando fallback")
            titles = gerar_action_titles_fallback(dados, SECRETARIA)
            recs   = gerar_recomendacoes_fallback(dados, SECRETARIA)
    else:
        titles = gerar_action_titles_fallback(dados, SECRETARIA)
        recs   = gerar_recomendacoes_fallback(dados, SECRETARIA)

    for k, v in titles.items():
        print(f"  [{k}] {v[:80]}…" if len(str(v)) > 80 else f"  [{k}] {v}")
    print(f"  {len(recs)} recomendações | analise_cruzada: {'sim' if analise_cruzada else 'não'}")

    # Montar HTML
    print("\nMontando HTML…")
    html = build_html_educacao(dados, titles, recs, pessoal, SECRETARIA,
                               analise_cruzada=analise_cruzada, alertas=alertas)

    # Salvar
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    size_kb = OUTPUT_HTML.stat().st_size / 1024
    print(f"\n[OK] Salvo: {OUTPUT_HTML}")
    print(f"     Tamanho: {size_kb:.0f} KB ({'OK' if size_kb < 2048 else 'AVISO: > 2MB'})")

    print("\n[CONCLUÍDO] Task 5 — build_html_educacao.py")


if __name__ == "__main__":
    main()
