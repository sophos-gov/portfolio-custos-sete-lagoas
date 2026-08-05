#!/usr/bin/env python3
"""
build_html_saude.py — Task 4
Gera relatorio_custos_saude_2025.html no estilo McKinsey com Chart.js.
"""
import os, sys, json, re
import pandas as pd
from pathlib import Path

SCRIPT_DIR  = Path(__file__).resolve().parent
TABELAS_DIR = SCRIPT_DIR / "tabelas"
SAUDE_DIR   = TABELAS_DIR / "saude"
OUTPUT_HTML = SCRIPT_DIR / "relatorio_custos_saude_2025.html"

SECRETARIA  = "Saúde"
SECRETARIA_KEY = "saude"


# ---------------------------------------------------------------------------
# Helpers de formatação
# ---------------------------------------------------------------------------
def fmt_brl(v: float) -> str:
    """R$ 1.234.567"""
    try:
        return f"R$ {v:_.0f}".replace("_", ".")
    except:
        return "R$ 0"


def fmt_m(v: float) -> str:
    """R$ 1,2M"""
    if v >= 1e9:
        return f"R$ {v/1e9:.1f}B".replace(".", ",")
    elif v >= 1e6:
        return f"R$ {v/1e6:.1f}M".replace(".", ",")
    elif v >= 1e3:
        return f"R$ {v/1e3:.0f} mil"
    return fmt_brl(v)


def pct(v: float) -> str:
    return f"{v:.1f}%"


# ---------------------------------------------------------------------------
# Carregar dados
# ---------------------------------------------------------------------------
def carregar_dados(dir_: Path) -> dict:
    dados = {}

    def ler_csv(nome):
        p = dir_ / nome
        if p.exists():
            return pd.read_csv(p)
        return pd.DataFrame()

    def ler_json(nome):
        p = dir_ / nome
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        return {}

    dados["kpis"]          = ler_json("kpis.json")
    dados["concentracao"]  = ler_json("concentracao.json")
    dados["programas"]     = ler_csv("composicao_programa.csv")
    dados["natureza"]      = ler_csv("composicao_natureza.csv")
    dados["acoes"]         = ler_csv("composicao_acao.csv")
    dados["fornecedores"]  = ler_csv("ranking_fornecedores.csv")
    dados["categorias"]    = ler_csv("composicao_categorias.csv")
    dados["cat_mensal"]    = ler_csv("composicao_categorias_mensal.csv")
    dados["serie"]         = ler_csv("serie_mensal.csv")
    dados["fontes"]        = ler_csv("fontes_recurso.csv")
    return dados


# ---------------------------------------------------------------------------
# Action Titles
# ---------------------------------------------------------------------------
def gerar_analise_opus(client, dados: dict, secretaria: str) -> dict:
    """Uma chamada Opus com todos os dados → action titles, análise cruzada, alertas e recomendações."""
    kpis   = dados["kpis"]
    prog   = dados["programas"].to_dict("records") if not dados["programas"].empty else []
    nat    = dados["natureza"].to_dict("records") if not dados["natureza"].empty else []
    acoes  = dados["acoes"].head(15).to_dict("records") if not dados["acoes"].empty else []
    forn   = dados["fornecedores"].head(20).to_dict("records") if not dados["fornecedores"].empty else []
    cat    = dados["categorias"].to_dict("records") if not dados["categorias"].empty else []
    serie  = dados["serie"].to_dict("records") if not dados["serie"].empty else []
    fontes = dados["fontes"].to_dict("records") if not dados["fontes"].empty else []
    conc   = dados["concentracao"]

    payload = {
        "secretaria": secretaria,
        "municipio": "Sete Lagoas (MG)",
        "exercicio": "2025",
        "kpis": kpis,
        "por_programa": prog,
        "por_natureza_macro": nat,
        "por_acao": acoes,
        "top_fornecedores": forn,
        "por_categoria": cat,
        "serie_mensal": serie,
        "fontes_recurso": fontes,
        "concentracao": conc,
    }

    prompt = f"""Você é um consultor sênior de gestão pública analisando os custos da Secretaria de {secretaria} de Sete Lagoas (MG) no exercício de 2025.

DADOS COMPLETOS:
{json.dumps(payload, ensure_ascii=False, indent=2)}

Analise esses dados com profundidade — procure padrões, anomalias, riscos e oportunidades que não são óbvios ao olhar uma seção isolada.

Retorne EXATAMENTE este JSON (sem markdown, sem texto fora do JSON):

{{
  "action_titles": {{
    "hero": "frase executiva de até 22 palavras com o número mais relevante e a implicação para o secretário",
    "programas": "insight sobre concentração ou distribuição entre programas — o que isso revela para o gestor",
    "natureza": "insight sobre a composição da natureza de despesa — o que a estrutura de gastos diz sobre a secretaria",
    "acoes": "insight sobre as ações líderes — o que o padrão de execução revela",
    "fornecedores": "insight sobre concentração e dependência de fornecedores — qual o risco embutido",
    "categorias": "insight sobre as categorias dominantes — o que revelam sobre a gestão",
    "mensal": "insight sobre sazonalidade e variação — o que o perfil mensal indica",
    "fontes": "insight sobre dependência de fontes — qual o grau de autonomia fiscal"
  }},
  "analise_cruzada": "Parágrafo de 4-5 frases conectando os achados de múltiplas seções. Identifique: tensões entre execução e planejamento, correlações entre fornecedores e programas, riscos sistêmicos que surgem apenas com visão holística, e o que esses padrões revelam sobre a maturidade de gestão da secretaria.",
  "alertas": [
    "Alerta 1 (mais severo): descreva o risco específico com número concreto e consequência potencial",
    "Alerta 2: segundo risco mais relevante com dados",
    "Alerta 3: terceiro risco ou oportunidade perdida com dados"
  ],
  "recomendacoes": [
    {{
      "insight": "dado específico que fundamenta — inclua valor ou percentual exato dos dados",
      "implicacao": "o que isso significa para a gestão da secretaria em termos de risco, eficiência ou governança",
      "acao": "ação concreta, mensurável e com prazo implícito — começar com verbo no infinitivo"
    }},
    {{
      "insight": "...",
      "implicacao": "...",
      "acao": "..."
    }},
    {{
      "insight": "...",
      "implicacao": "...",
      "acao": "..."
    }},
    {{
      "insight": "...",
      "implicacao": "...",
      "acao": "..."
    }}
  ]
}}

REGRAS:
- Action titles: afirmação com ≥1 número; evite rótulos genéricos como "análise de" ou "composição de"
- Análise cruzada: conecte seções — não repita o que já está nos action titles
- Alertas: ordenados por severidade; cada um com dado concreto + risco implícito
- Recomendações: 4 exatas; baseadas nos dados, não em boas práticas genéricas; ações concretas e mensuráveis"""

    resp = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4000,
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}]
    )

    texto = resp.content[0].text.strip()
    texto = re.sub(r"^```[a-z]*\n?", "", texto)
    texto = re.sub(r"\n?```$", "", texto)
    return json.loads(texto)


def gerar_action_titles_fallback(dados: dict, secretaria: str) -> dict:
    """Gera action titles com f-strings + dados reais."""
    kpis   = dados["kpis"]
    prog   = dados["programas"]
    nat    = dados["natureza"]
    serie  = dados["serie"]
    forn   = dados["fornecedores"]
    cat    = dados["categorias"]
    conc   = dados["concentracao"]
    fontes = dados["fontes"]

    titles = {}

    # Hero
    total = kpis.get("total_pago", 0)
    periodo = kpis.get("periodo", "2025")
    prog_top_nome = prog.iloc[0]["dsc_programa"] if not prog.empty else "N/A"
    prog_top_pct  = float(prog.iloc[0]["pct_total"]) if not prog.empty else 0
    titles["hero"] = (
        f"{secretaria} de Sete Lagoas gastou {fmt_brl(total)} em {periodo}: "
        f"{prog_top_nome.split(' - ')[-1].strip()[:40]} concentra {prog_top_pct:.0f}% do orçamento"
    )

    # Programas
    if not prog.empty and len(prog) >= 2:
        p1 = prog.iloc[0]
        p2 = prog.iloc[1]
        n1 = p1["dsc_programa"].split(" - ")[-1].strip()[:35]
        n2 = p2["dsc_programa"].split(" - ")[-1].strip()[:30]
        titles["programas"] = (
            f"{n1} domina {p1['pct_total']:.0f}% dos gastos de {secretaria}, "
            f"seguido por {n2} com {p2['pct_total']:.0f}%"
        )
    else:
        titles["programas"] = f"Programa principal concentra mais de 50% dos gastos de {secretaria}"

    # Natureza
    if not nat.empty:
        n1 = nat.iloc[0]
        titles["natureza"] = (
            f"{n1['macro_natureza'] if 'macro_natureza' in n1 else n1.index[0]} responde por "
            f"{n1['pct_total']:.0f}% dos custos de {secretaria} ({fmt_brl(n1['vlr_pago'])})"
        )
    else:
        titles["natureza"] = f"Pessoal e encargos respondem pela maior parcela dos custos de {secretaria}"

    # Ações
    if not dados["acoes"].empty:
        a1 = dados["acoes"].iloc[0]
        acao_nome = str(a1["dsc_acao"]).split(" - ")[-1].strip()[:40]
        titles["acoes"] = (
            f"Ação '{acao_nome[:35]}' lidera com {fmt_brl(a1['vlr_pago'])} "
            f"({a1['pct_total']:.0f}% do total)"
        )
    else:
        titles["acoes"] = f"Atividade-fim concentra a maior parte dos gastos de {secretaria}"

    # Fornecedores
    if not forn.empty:
        f1 = forn.iloc[0]
        pct_top10 = conc.get("pct_top10", 0)
        titles["fornecedores"] = (
            f"Os 10 maiores fornecedores absorvem {pct_top10:.0f}% do orçamento; "
            f"{f1['nom_credor'][:30]} lidera com {fmt_brl(f1['total_pago'])}"
        )
    else:
        titles["fornecedores"] = "Concentração de fornecedores requer atenção de governança"

    # Categorias
    if not cat.empty:
        c1 = cat.iloc[0]
        c2 = cat.iloc[1] if len(cat) > 1 else None
        nome_col = "categoria_nome" if "categoria_nome" in cat.columns else cat.columns[0]
        if c2 is not None:
            titles["categorias"] = (
                f"{c1[nome_col]} ({c1['pct_total']:.0f}%) e {c2[nome_col]} ({c2['pct_total']:.0f}%) "
                f"somam {c1['pct_total']+c2['pct_total']:.0f}% dos custos classificados"
            )
        else:
            titles["categorias"] = f"{c1[nome_col]} domina os custos com {c1['pct_total']:.0f}%"
    else:
        titles["categorias"] = f"Pessoal é a categoria dominante de custo em {secretaria}"

    # Mensal
    if not serie.empty:
        idx_pico = serie["vlr_pago"].idxmax()
        pico = serie.loc[idx_pico]
        media = float(serie["vlr_pago"].mean())
        pct_acima = (pico["vlr_pago"] / media - 1) * 100 if media else 0
        mes_nome = pico.get("mes_nome", "pico")
        titles["mensal"] = (
            f"Pico de {fmt_brl(pico['vlr_pago'])} em {mes_nome} — "
            f"{pct_acima:.0f}% acima da média mensal de {fmt_brl(media)}"
        )
    else:
        titles["mensal"] = f"Gastos mensais de {secretaria} apresentam variação ao longo de 2025"

    # Fontes
    if not fontes.empty:
        f1 = fontes.iloc[0]
        col_fonte = "fonte" if "fonte" in fontes.columns else fontes.columns[0]
        titles["fontes"] = (
            f"{f1[col_fonte]} financia {f1['pct_total']:.0f}% dos gastos "
            f"({fmt_brl(f1['vlr_pago'])}); demais fontes complementam os {100-f1['pct_total']:.0f}% restantes"
        )
    else:
        titles["fontes"] = f"Recursos próprios e transferências federais financiam os gastos de {secretaria}"

    return titles



def gerar_recomendacoes_fallback(dados: dict, secretaria: str) -> list:
    kpis   = dados["kpis"]
    prog   = dados["programas"]
    forn   = dados["fornecedores"]
    conc   = dados["concentracao"]
    cat    = dados["categorias"]

    total  = kpis.get("total_pago", 0)
    pct_top10 = conc.get("pct_top10", 0)

    recs = []

    # 1 — Concentração de fornecedores
    if not forn.empty:
        f1 = forn.iloc[0]
        recs.append({
            "insight": f"Os 10 maiores fornecedores concentram {pct_top10:.1f}% do total pago "
                       f"({fmt_brl(total * pct_top10/100)}). {f1['nom_credor'][:30]} é o maior, "
                       f"com {fmt_brl(f1['total_pago'])}.",
            "implicacao": "Alta concentração cria risco de dependência e reduz poder de negociação.",
            "acao": "Diversificar fornecedores-chave e revisar condições contratuais dos top 5."
        })

    # 2 — Programa dominante
    if not prog.empty:
        p1 = prog.iloc[0]
        nome_prog = p1["dsc_programa"].split(" - ")[-1].strip()[:40]
        recs.append({
            "insight": f"{nome_prog} concentra {p1['pct_total']:.1f}% do orçamento "
                       f"({fmt_brl(p1['vlr_pago'])}).",
            "implicacao": "Programa dominante merece monitoramento intensivo de execução.",
            "acao": "Implantar painel de indicadores mensais para acompanhar execução do programa principal."
        })

    # 3 — Categoria de custo
    if not cat.empty:
        nome_col = "categoria_nome" if "categoria_nome" in cat.columns else cat.columns[0]
        c1 = cat.iloc[0]
        recs.append({
            "insight": f"A categoria '{c1[nome_col]}' representa {c1['pct_total']:.1f}% dos empenhos classificados.",
            "implicacao": "Categoria dominante requer controle orçamentário e análise de tendência.",
            "acao": "Revisar política de contratação e comparar custo unitário com benchmarks regionais."
        })

    # 4 — Execução orçamentária
    total_prev = kpis.get("total_previsto", 0)
    if total_prev > 0:
        exec_pct = total / total_prev * 100
        recs.append({
            "insight": f"Execução orçamentária de {exec_pct:.1f}%: {fmt_brl(total)} pagos de "
                       f"{fmt_brl(total_prev)} previstos até {kpis.get('periodo', '2025')}.",
            "implicacao": "Taxa de execução indica capacidade de absorção do orçamento disponível.",
            "acao": "Antecipar planejamento de contratações para melhorar execução nos meses finais."
        })
    else:
        recs.append({
            "insight": f"Total pago de {fmt_brl(total)} no período {kpis.get('periodo', '2025')}.",
            "implicacao": "Monitorar execução mensal para identificar gargalos orçamentários.",
            "acao": "Estabelecer metas mensais de execução e revisar cronograma de desembolsos."
        })

    return recs[:4]


# ---------------------------------------------------------------------------
# CSS e JavaScript compartilhados
# ---------------------------------------------------------------------------
CSS = """
:root {
    --azul-escuro:  #1B3A5C;
    --azul-medio:   #2E86AB;
    --azul-claro:   #A3CEF1;
    --verde:        #28A745;
    --vermelho:     #E63946;
    --amarelo:      #F4A261;
    --cinza-escuro: #343A40;
    --cinza-medio:  #6C757D;
    --fundo:        #F8F9FA;
    --branco:       #FFFFFF;
    --fonte: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: var(--fonte); background: var(--fundo); color: var(--cinza-escuro); line-height: 1.6; }

.nav-sidebar {
    position: fixed; left: 0; top: 0;
    width: 220px; height: 100vh;
    background: var(--azul-escuro);
    padding: 1.5rem 1rem; overflow-y: auto; z-index: 100;
}
.nav-logo { color: white; font-weight: 700; margin-bottom: 1.5rem; font-size: 0.9rem; line-height: 1.4; }
.nav-logo small { opacity: 0.6; display: block; font-size: 0.75rem; margin-top: 0.25rem; }
.nav-sidebar a {
    display: block; color: rgba(255,255,255,0.7); text-decoration: none;
    padding: 0.45rem 0.75rem; border-radius: 4px; font-size: 0.82rem;
    margin-bottom: 0.2rem; transition: all 0.2s;
}
.nav-sidebar a:hover, .nav-sidebar a.active { background: var(--azul-medio); color: var(--branco); }

.main-content { margin-left: 220px; padding: 2rem 2.5rem; max-width: 1100px; }

.hero {
    background: linear-gradient(135deg, var(--azul-escuro), var(--azul-medio));
    color: white; padding: 2.5rem; border-radius: 16px; margin-bottom: 2rem;
}
.hero h1 { font-size: 1.9rem; margin-bottom: 0.5rem; }
.hero .periodo { font-size: 0.85rem; opacity: 0.7; margin-bottom: 1rem; }
.action-title-hero { font-size: 1.1rem; opacity: 0.92; font-weight: 400; max-width: 750px; line-height: 1.5; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 1rem; margin-top: 2rem; }
.kpi-card { background: rgba(255,255,255,0.15); border-radius: 10px; padding: 1.1rem; text-align: center; }
.kpi-label { font-size: 0.72rem; opacity: 0.8; text-transform: uppercase; letter-spacing: 0.06em; }
.kpi-value { font-size: 1.5rem; font-weight: 700; margin: 0.2rem 0; }
.kpi-sub   { font-size: 0.78rem; opacity: 0.7; }

.section {
    background: var(--branco); border-radius: 12px; padding: 2rem 2.5rem;
    margin-bottom: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.section-id { font-size: 0.68rem; color: var(--azul-medio); text-transform: uppercase;
              letter-spacing: 0.09em; font-weight: 600; margin-bottom: 0.4rem; }
.action-title {
    font-size: 1.15rem; font-weight: 600; color: var(--azul-escuro);
    border-left: 4px solid var(--azul-medio); padding-left: 1rem;
    margin-bottom: 1.5rem; line-height: 1.45;
}
.chart-container { position: relative; height: 380px; margin: 1rem 0 1.5rem; }
.chart-container.tall { height: 460px; }
.chart-container.short { height: 280px; }

.data-table { width: 100%; border-collapse: collapse; font-size: 0.86rem; margin-top: 1rem; }
.data-table th { background: var(--azul-escuro); color: white; padding: 0.55rem 0.8rem;
                 text-align: left; font-weight: 500; }
.data-table td { padding: 0.45rem 0.8rem; border-bottom: 1px solid var(--fundo); }
.data-table tr:hover td { background: var(--fundo); }
.heat-high { background: #FDECEA; color: var(--vermelho); font-weight: 600; }
.heat-med  { background: #FFF8E1; color: #856404; }
.heat-low  { background: #E8F5E9; color: #2E7D32; }
.num-col { text-align: right; font-variant-numeric: tabular-nums; }
.pct-bar { display: inline-block; height: 8px; background: var(--azul-claro); border-radius: 4px; margin-left: 6px; vertical-align: middle; }

.rec-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; }
.rec-card { border-left: 4px solid var(--verde); padding: 1.2rem;
            background: #F0FFF4; border-radius: 0 10px 10px 0; }
.rec-label { font-size: 0.68rem; font-weight: 700; color: var(--azul-medio);
             text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.3rem; }
.rec-insight    { font-size: 0.92rem; color: var(--cinza-escuro); margin-bottom: 0.5rem; }
.rec-implicacao { font-size: 0.85rem; color: var(--cinza-medio); margin-bottom: 0.7rem; }
.rec-acao { font-size: 0.85rem; font-weight: 600; color: var(--azul-escuro); }
.rec-acao::before { content: "→ "; color: var(--verde); }

.analise-cruzada {
    background: #EBF4FF; border-left: 4px solid var(--azul-medio);
    padding: 1.2rem 1.5rem; border-radius: 0 10px 10px 0;
    font-size: 0.95rem; line-height: 1.7; color: var(--cinza-escuro);
    margin-bottom: 1.5rem;
}
.alertas-titulo { font-size: 0.72rem; font-weight: 700; color: var(--vermelho);
                  text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.75rem; }
.alerta-grid { display: flex; flex-direction: column; gap: 0.6rem; margin-bottom: 1.75rem; }
.alerta-card { border-left: 4px solid var(--vermelho); background: #FFF5F5;
               padding: 0.85rem 1.2rem; border-radius: 0 8px 8px 0;
               font-size: 0.875rem; line-height: 1.55; color: var(--cinza-escuro); }
.alerta-card strong { color: var(--vermelho); }

@media (max-width: 768px) {
    .nav-sidebar  { display: none; }
    .main-content { margin-left: 0; padding: 1rem; }
    .hero         { padding: 1.5rem; }
    .hero h1      { font-size: 1.35rem; }
    .chart-container { height: 260px; }
}
"""

JS_UTILS = """
const CORES = {
    principal: '#2E86AB', secundaria: '#A3CEF1',
    verde: '#28A745', vermelho: '#E63946', amarelo: '#F4A261', cinza: '#6C757D',
    palette: ['#1B3A5C','#2E86AB','#A3CEF1','#28A745','#F4A261','#E63946',
              '#6C757D','#17BECF','#8C564B','#E377C2','#BCBD22','#9467BD',
              '#D62728','#FF7F0E']
};

const formatBRL = v => {
    if (v == null || isNaN(v)) return 'R$ 0';
    return 'R$ ' + Math.round(v).toLocaleString('pt-BR');
};
const formatM = v => {
    if (v == null || isNaN(v)) return 'R$ 0';
    if (Math.abs(v) >= 1e9) return 'R$ ' + (v/1e9).toFixed(1).replace('.',',') + 'B';
    if (Math.abs(v) >= 1e6) return 'R$ ' + (v/1e6).toFixed(1).replace('.',',') + 'M';
    if (Math.abs(v) >= 1e3) return 'R$ ' + (v/1e3).toFixed(0) + ' mil';
    return formatBRL(v);
};

Chart.defaults.font.family = 'system-ui, -apple-system, "Segoe UI", sans-serif';
Chart.defaults.font.size   = 12;
Chart.defaults.color       = '#343A40';

// Nav scroll highlight
window.addEventListener('scroll', () => {
    const sections = document.querySelectorAll('.section[id], .hero[id]');
    const navLinks = document.querySelectorAll('.nav-sidebar a');
    let current = '';
    sections.forEach(s => {
        if (window.scrollY >= s.offsetTop - 120) current = s.id;
    });
    navLinks.forEach(a => {
        a.classList.remove('active');
        if (a.getAttribute('href') === '#' + current) a.classList.add('active');
    });
});
"""


# ---------------------------------------------------------------------------
# Gerador de seções HTML
# ---------------------------------------------------------------------------
def tabela_programas_html(prog: pd.DataFrame) -> str:
    if prog.empty:
        return "<p>Dados não disponíveis.</p>"
    rows = ""
    max_pag = float(prog["vlr_pago"].max()) if not prog.empty else 1
    for _, r in prog.iterrows():
        pct_v = float(r["pct_total"])
        bar_w = int(pct_v * 1.5)
        heat = "heat-high" if pct_v > 40 else ("heat-med" if pct_v > 15 else "heat-low")
        rows += f"""<tr>
            <td>{str(r['dsc_programa'])[:70]}</td>
            <td class="num-col">{fmt_brl(r['vlr_pago'])}</td>
            <td class="num-col {heat}">{pct_v:.1f}%<span class="pct-bar" style="width:{bar_w}px"></span></td>
            <td class="num-col">{fmt_brl(r.get('vlr_empenhado', 0))}</td>
        </tr>"""
    return f"""<table class="data-table">
        <thead><tr><th>Programa</th><th class="num-col">Valor Pago</th>
        <th class="num-col">% Total</th><th class="num-col">Empenhado</th></tr></thead>
        <tbody>{rows}</tbody></table>"""


def tabela_fornecedores_html(forn: pd.DataFrame) -> str:
    if forn.empty:
        return "<p>Dados não disponíveis.</p>"
    rows = ""
    for i, (_, r) in enumerate(forn.iterrows()):
        pct_v = float(r["pct_total"])
        heat = "heat-high" if pct_v > 10 else ("heat-med" if pct_v > 5 else "")
        rows += f"""<tr>
            <td>{i+1}</td>
            <td>{str(r['nom_credor'])[:50]}</td>
            <td class="num-col">{fmt_brl(r['total_pago'])}</td>
            <td class="num-col {heat}">{pct_v:.1f}%</td>
            <td class="num-col">{pct(float(r['pct_acumulado']))}</td>
        </tr>"""
    return f"""<table class="data-table">
        <thead><tr><th>#</th><th>Fornecedor</th><th class="num-col">Total Pago</th>
        <th class="num-col">% Total</th><th class="num-col">% Acumulado</th></tr></thead>
        <tbody>{rows}</tbody></table>"""


def heatmap_categorias_html(cat_mensal: pd.DataFrame) -> str:
    if cat_mensal.empty:
        return ""
    from io import StringIO
    try:
        pivot = cat_mensal.pivot_table(
            index="categoria_nome", columns="mes_nome", values="vlr_empenhado", aggfunc="sum", fill_value=0
        )
        MESES_ORD = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
        cols = [c for c in MESES_ORD if c in pivot.columns]
        pivot = pivot[cols]

        header = "<tr><th>Categoria</th>" + "".join(f"<th class='num-col'>{c}</th>" for c in cols) + "</tr>"
        rows = ""
        for cat in pivot.index:
            row_vals = pivot.loc[cat]
            row_max  = row_vals.max()
            cells = ""
            for v in row_vals:
                if row_max > 0:
                    ratio = v / row_max
                    cls = "heat-high" if ratio > 0.7 else ("heat-med" if ratio > 0.3 else "")
                else:
                    cls = ""
                cells += f"<td class='num-col {cls}'>{fmt_m(v) if v > 0 else '—'}</td>"
            rows += f"<tr><td>{cat}</td>{cells}</tr>"

        return f"<table class='data-table' style='font-size:0.78rem;margin-top:1rem'><thead>{header}</thead><tbody>{rows}</tbody></table>"
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Construir HTML completo
# ---------------------------------------------------------------------------
def build_html(dados: dict, titles: dict, recs: list, secretaria: str,
               analise_cruzada: str = "", alertas: list = None,
               cor_acento: str = "#2E86AB") -> str:
    kpis  = dados["kpis"]
    prog  = dados["programas"]
    nat   = dados["natureza"]
    acoes = dados["acoes"]
    forn  = dados["fornecedores"]
    cat   = dados["categorias"]
    cat_m = dados["cat_mensal"]
    serie = dados["serie"]
    fontes = dados["fontes"]
    conc  = dados["concentracao"]

    # Serializar para JS
    def to_js(df, cols):
        if df.empty:
            return "[]", "[]"
        labels = [str(r[cols[0]])[:55] for _, r in df.iterrows()]
        values = [float(r[cols[1]]) for _, r in df.iterrows()]
        return json.dumps(labels), json.dumps(values)

    prog_labels, prog_values = to_js(prog, ["dsc_programa", "vlr_pago"])
    nat_col = "macro_natureza" if "macro_natureza" in nat.columns else nat.columns[0]
    nat_labels,  nat_values  = to_js(nat,  [nat_col, "vlr_pago"])
    acao_labels, acao_values = to_js(acoes, ["dsc_acao", "vlr_pago"])
    forn_labels, forn_values = to_js(forn,  ["nom_credor", "total_pago"])
    cat_col = "categoria_nome" if "categoria_nome" in cat.columns else cat.columns[0]
    cat_labels,  cat_values  = to_js(cat,  [cat_col, "vlr_empenhado"])
    fonte_col = "fonte" if "fonte" in fontes.columns else fontes.columns[0]
    fonte_labels, fonte_values = to_js(fontes, [fonte_col, "vlr_pago"])

    if not serie.empty:
        serie_labels = json.dumps(list(serie["mes_nome"]))
        serie_values = json.dumps([float(v) for v in serie["vlr_pago"]])
        serie_media  = float(serie["vlr_pago"].mean())
    else:
        serie_labels = "[]"; serie_values = "[]"; serie_media = 0

    pareto_labels = json.dumps(list(forn["nom_credor"].str[:30]) if not forn.empty else [])
    pareto_values = json.dumps([float(v) for v in forn["pct_acumulado"]] if not forn.empty else [])

    # Tabelas HTML
    tab_prog  = tabela_programas_html(prog)
    tab_forn  = tabela_fornecedores_html(forn)
    tab_heat  = heatmap_categorias_html(cat_m)

    if alertas is None:
        alertas = []

    t = titles
    icone = "🏥" if secretaria.lower() == "saúde" else "🎓"

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
    <div class="nav-logo">{icone} Custos {secretaria}<small>Sete Lagoas · 2025</small></div>
    <a href="#hero">Resumo Executivo</a>
    <a href="#programas">Composição por Programa</a>
    <a href="#natureza">Natureza de Despesa</a>
    <a href="#acoes">Por Ação</a>
    <a href="#fornecedores">Fornecedores</a>
    <a href="#categorias">Categorias de Custo</a>
    <a href="#mensal">Evolução Mensal</a>
    <a href="#fontes">Fontes de Recurso</a>
    <a href="#sintese">Síntese Analítica</a>
    <a href="#recomendacoes">Recomendações</a>
</nav>

<div class="main-content">

<!-- HERO -->
<section class="hero" id="hero">
    <h1>Custos da {secretaria} — Sete Lagoas 2025</h1>
    <div class="periodo">{icone} {kpis.get('periodo', '2025')} · Sete Lagoas (MG) · SICOM/TCE-MG</div>
    <p class="action-title-hero">{t.get('hero', '')}</p>
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">Total Pago</div>
            <div class="kpi-value">{fmt_m(kpis.get('total_pago', 0))}</div>
            <div class="kpi-sub">{fmt_brl(kpis.get('total_pago', 0))}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Total Empenhado</div>
            <div class="kpi-value">{fmt_m(kpis.get('total_empenhado', 0))}</div>
            <div class="kpi-sub">{fmt_brl(kpis.get('total_empenhado', 0))}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Fornecedores</div>
            <div class="kpi-value">{kpis.get('num_fornecedores', 0):,}</div>
            <div class="kpi-sub">únicos no período</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Empenhos</div>
            <div class="kpi-value">{kpis.get('num_empenhos', 0):,}</div>
            <div class="kpi-sub">compromissos em 2025</div>
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
    <div class="section-id">Seção 9 — Recomendações de Gestão</div>
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
const PROG_LABELS  = {prog_labels};
const PROG_VALUES  = {prog_values};
const NAT_LABELS   = {nat_labels};
const NAT_VALUES   = {nat_values};
const ACAO_LABELS  = {acao_labels};
const ACAO_VALUES  = {acao_values};
const FORN_LABELS  = {forn_labels};
const FORN_VALUES  = {forn_values};
const CAT_LABELS   = {cat_labels};
const CAT_VALUES   = {cat_values};
const SERIE_LABELS = {serie_labels};
const SERIE_VALUES = {serie_values};
const SERIE_MEDIA  = {serie_media};
const FONTE_LABELS = {fonte_labels};
const FONTE_VALUES = {fonte_values};
const PARETO_LABELS= {pareto_labels};
const PARETO_VALUES= {pareto_values};
const KPI_TOTAL    = {kpis.get('total_pago', 0)};

// ---- CHARTS ----

// 1. Programas — bar horizontal
new Chart(document.getElementById('chartProg'), {{
    type: 'bar',
    data: {{
        labels: PROG_LABELS,
        datasets: [{{ data: PROG_VALUES, backgroundColor: CORES.principal,
                     borderRadius: 4, barPercentage: 0.7 }}]
    }},
    options: {{
        indexAxis: 'y',
        plugins: {{
            legend: {{ display: false }},
            tooltip: {{ callbacks: {{ label: ctx => formatBRL(ctx.raw) }} }}
        }},
        scales: {{
            x: {{ ticks: {{ callback: v => formatM(v) }}, grid: {{ display: false }} }},
            y: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 11 }} }} }}
        }}
    }}
}});

// 2. Natureza — doughnut
new Chart(document.getElementById('chartNat'), {{
    type: 'doughnut',
    data: {{
        labels: NAT_LABELS,
        datasets: [{{ data: NAT_VALUES, backgroundColor: CORES.palette,
                     borderWidth: 2, borderColor: '#fff' }}]
    }},
    options: {{
        cutout: '58%',
        plugins: {{
            legend: {{ position: 'right', labels: {{ font: {{ size: 11 }} }} }},
            tooltip: {{ callbacks: {{ label: ctx => {{
                const tot = ctx.dataset.data.reduce((a,b)=>a+b,0);
                return ctx.label + ': ' + formatBRL(ctx.raw) + ' (' + (ctx.raw/tot*100).toFixed(1) + '%)';
            }}}}}}
        }}
    }}
}});

// 3. Ações — bar horizontal
new Chart(document.getElementById('chartAcoes'), {{
    type: 'bar',
    data: {{
        labels: ACAO_LABELS,
        datasets: [{{ data: ACAO_VALUES,
                     backgroundColor: ACAO_VALUES.map((v,i) => i===0 ? CORES.vermelho : CORES.principal),
                     borderRadius: 4, barPercentage: 0.65 }}]
    }},
    options: {{
        indexAxis: 'y',
        plugins: {{
            legend: {{ display: false }},
            tooltip: {{ callbacks: {{ label: ctx => formatBRL(ctx.raw) + ' (' + (ctx.raw/KPI_TOTAL*100).toFixed(1) + '%)' }} }}
        }},
        scales: {{
            x: {{ ticks: {{ callback: v => formatM(v) }}, grid: {{ display: false }} }},
            y: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }}
        }}
    }}
}});

// 4. Fornecedores — bar horizontal
new Chart(document.getElementById('chartForn'), {{
    type: 'bar',
    data: {{
        labels: FORN_LABELS,
        datasets: [{{ data: FORN_VALUES,
                     backgroundColor: FORN_VALUES.map((v,i) => i < 3 ? CORES.vermelho : CORES.principal),
                     borderRadius: 4, barPercentage: 0.65 }}]
    }},
    options: {{
        indexAxis: 'y',
        plugins: {{
            legend: {{ display: false }},
            tooltip: {{ callbacks: {{ label: ctx => formatBRL(ctx.raw) }} }}
        }},
        scales: {{
            x: {{ ticks: {{ callback: v => formatM(v) }}, grid: {{ display: false }} }},
            y: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }}
        }}
    }}
}});

// 5. Pareto — linha de % acumulado
new Chart(document.getElementById('chartPareto'), {{
    type: 'line',
    data: {{
        labels: PARETO_LABELS,
        datasets: [{{
            label: '% Acumulado',
            data: PARETO_VALUES,
            borderColor: CORES.vermelho,
            backgroundColor: CORES.vermelho + '20',
            tension: 0.2, fill: true, pointRadius: 4
        }}]
    }},
    options: {{
        plugins: {{
            legend: {{ display: true }},
            tooltip: {{ callbacks: {{ label: ctx => ctx.raw.toFixed(1) + '%' }} }}
        }},
        scales: {{
            x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 9 }}, maxRotation: 45 }} }},
            y: {{ min: 0, max: 100, ticks: {{ callback: v => v + '%' }} }}
        }}
    }}
}});

// 6. Categorias — doughnut
new Chart(document.getElementById('chartCat'), {{
    type: 'doughnut',
    data: {{
        labels: CAT_LABELS,
        datasets: [{{ data: CAT_VALUES, backgroundColor: CORES.palette,
                     borderWidth: 2, borderColor: '#fff' }}]
    }},
    options: {{
        cutout: '55%',
        plugins: {{
            legend: {{ position: 'right', labels: {{ font: {{ size: 11 }} }} }},
            tooltip: {{ callbacks: {{ label: ctx => {{
                const tot = ctx.dataset.data.reduce((a,b)=>a+b,0);
                return ctx.label + ': ' + formatBRL(ctx.raw) + ' (' + (ctx.raw/tot*100).toFixed(1) + '%)';
            }}}}}}
        }}
    }}
}});

// 7. Evolução mensal — line + média
new Chart(document.getElementById('chartMensal'), {{
    type: 'line',
    data: {{
        labels: SERIE_LABELS,
        datasets: [
            {{
                label: 'Valor Pago',
                data: SERIE_VALUES,
                borderColor: CORES.principal,
                backgroundColor: CORES.principal + '25',
                tension: 0.3, fill: true, pointRadius: 5,
                pointBackgroundColor: SERIE_VALUES.map(v => v === Math.max(...SERIE_VALUES) ? CORES.vermelho : CORES.principal),
                pointRadius: SERIE_VALUES.map(v => v === Math.max(...SERIE_VALUES) ? 8 : 5)
            }},
            {{
                label: 'Média mensal',
                data: SERIE_LABELS.map(() => SERIE_MEDIA),
                borderColor: CORES.amarelo,
                borderDash: [6, 4],
                borderWidth: 2,
                pointRadius: 0,
                fill: false
            }}
        ]
    }},
    options: {{
        plugins: {{
            legend: {{ display: true }},
            tooltip: {{ callbacks: {{ label: ctx => ctx.dataset.label + ': ' + formatBRL(ctx.raw) }} }}
        }},
        scales: {{
            x: {{ grid: {{ display: false }} }},
            y: {{ ticks: {{ callback: v => formatM(v) }} }}
        }}
    }}
}});

// 8. Fontes — bar horizontal
new Chart(document.getElementById('chartFontes'), {{
    type: 'bar',
    data: {{
        labels: FONTE_LABELS,
        datasets: [{{ data: FONTE_VALUES, backgroundColor: CORES.palette,
                     borderRadius: 4, barPercentage: 0.65 }}]
    }},
    options: {{
        indexAxis: 'y',
        plugins: {{
            legend: {{ display: false }},
            tooltip: {{ callbacks: {{ label: ctx => formatBRL(ctx.raw) }} }}
        }},
        scales: {{
            x: {{ ticks: {{ callback: v => formatM(v) }}, grid: {{ display: false }} }},
            y: {{ grid: {{ display: false }} }}
        }}
    }}
}});

</script>
</body>
</html>"""

    return html


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print(f"TASK 4 — build_html_saude.py")
    print("=" * 60)

    # Verificar dados
    if not SAUDE_DIR.exists():
        print(f"[ERRO] {SAUDE_DIR} não existe — execute tasks anteriores primeiro")
        sys.exit(1)

    # Carregar dados
    print("\nCarregando dados de Saúde…")
    dados = carregar_dados(SAUDE_DIR)
    kpis = dados["kpis"]
    print(f"  Total pago: {fmt_brl(kpis.get('total_pago', 0))}")
    print(f"  Período: {kpis.get('periodo', 'N/A')}")

    # API Claude para action titles + recomendações
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    client  = None
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            print("[OK] API Claude disponível para action titles e recomendações")
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
            # Fallback para seções de action_title que vieram vazias
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
    html = build_html(dados, titles, recs, SECRETARIA,
                      analise_cruzada=analise_cruzada, alertas=alertas)

    # Salvar
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    size_kb = OUTPUT_HTML.stat().st_size / 1024
    print(f"\n[OK] Salvo: {OUTPUT_HTML}")
    print(f"     Tamanho: {size_kb:.0f} KB ({'OK' if size_kb < 2048 else 'AVISO: > 2MB'})")

    print("\n[CONCLUÍDO] Task 4 — build_html_saude.py")


if __name__ == "__main__":
    main()
