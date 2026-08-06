# -*- coding: utf-8 -*-
"""
build_html_municipio.py — monta o SUMÁRIO EXECUTIVO (HTML estilo McKinsey) e o
RELATORIO_AUDITORIA_MUNICIPIO.md a partir de:
  - municipio/data/dados_consolidados.json          (exhibits determinísticos)
  - output/municipio/trilha_b_resultado.json
  - output/municipio/trilha_c_resumo.json
  - output/municipio/auditoria_municipio.json        (prosa + teses do workflow Opus)

HTML autocontido (CSS inline), navy #051C2C + azul #2251FF, serif p/ títulos,
exhibits numerados, imprime em PDF. NÃO é dashboard (sem JS/gráficos interativos).
"""
from __future__ import annotations

import html
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "municipio" / "data"
OUT = BASE / "output" / "municipio"
OUT.mkdir(parents=True, exist_ok=True)


def _load(p, default=None):
    p = Path(p)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return default if default is not None else {}


def brl(v, dec=0):
    try:
        v = float(v)
    except Exception:
        return "—"
    s = f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def num(v, dec=0):
    try:
        return f"{float(v):,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "—"


def esc(s):
    return html.escape(str(s)) if s is not None else ""


CLAS_COR = {"🔴": "#C0392B", "🟡": "#E08600", "🟢": "#1E7A46",
            "ALTO": "#C0392B", "MÉDIO": "#E08600", "MEDIO": "#E08600", "BAIXO": "#1E7A46"}


def md_to_html(texto: str) -> str:
    """Conversão mínima de markdown (negrito, parágrafos, listas) p/ HTML."""
    import re
    if not texto:
        return ""
    out_blocks = []
    for bloco in re.split(r"\n\s*\n", texto.strip()):
        bloco = bloco.strip()
        linhas = bloco.split("\n")
        if all(re.match(r"^\s*[-*]\s+", ln) for ln in linhas):
            items = "".join(f"<li>{_inline(ln)}</li>" for ln in
                            (re.sub(r"^\s*[-*]\s+", "", x) for x in linhas))
            out_blocks.append(f"<ul>{items}</ul>")
        else:
            out_blocks.append(f"<p>{_inline(bloco)}</p>")
    return "\n".join(out_blocks)


def _inline(s):
    import re
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
    return s


def exhibit_kpis(d):
    km = d.get("kpis_mes", [])
    rows = "".join(
        f"<tr><td>{esc(k['competencia'])}</td><td class='r'>{num(k['n_servidores'])}</td>"
        f"<td class='r'>{brl(k['folha_total'])}</td><td class='r'>{brl(k['medio'])}</td>"
        f"<td class='r'>{brl(k['mediana'])}</td><td class='r'>{num(k['gini'],3)}</td>"
        f"<td class='r'>{num(k['elite_n'])}</td></tr>" for k in km)
    total = sum(k["folha_total"] for k in km)
    return f"""
    <div class="exhibit">
      <div class="ex-num">Exhibit 1</div>
      <h3>Evolução da folha do município — competências mar–mai/2026</h3>
      <table>
        <thead><tr><th>Competência</th><th class='r'>Servidores</th><th class='r'>Folha bruta</th>
        <th class='r'>Médio</th><th class='r'>Mediana</th><th class='r'>Gini</th><th class='r'>Acima de R$ 20k</th></tr></thead>
        <tbody>{rows}</tbody>
        <tfoot><tr><td><strong>Total 3 meses</strong></td><td></td><td class='r'><strong>{brl(total)}</strong></td>
        <td colspan="4"></td></tr></tfoot>
      </table>
      <p class="src">Fonte: base pessoal.xlsx (proventos brutos). Gini sobre proventos do mês.</p>
    </div>"""


def exhibit_dim(d, chave, titulo, exnum, col_label):
    regs = d.get(chave, [])[:12]
    colname = list(regs[0].keys())[0] if regs else "x"
    rows = "".join(
        f"<tr><td>{esc(r.get(colname))}</td><td class='r'>{num(r.get('n'))}</td>"
        f"<td class='r'>{brl(r.get('total'))}</td><td class='r'>{num(r.get('pct_folha'),1)}%</td>"
        f"<td class='bar'><span style='width:{min(float(r.get('pct_folha',0)),100):.1f}%'></span></td></tr>"
        for r in regs)
    return f"""
    <div class="exhibit">
      <div class="ex-num">Exhibit {exnum}</div>
      <h3>{esc(titulo)}</h3>
      <table>
        <thead><tr><th>{esc(col_label)}</th><th class='r'>Servidores</th><th class='r'>Folha/mês</th>
        <th class='r'>% folha</th><th></th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <p class="src">Fonte: base pessoal.xlsx × cadastro(32).csv, mai/2026 (mês de referência).</p>
    </div>"""


def exhibit_faixas(d):
    fa = d.get("faixas", [])
    rows = "".join(
        f"<tr><td>{esc(r['faixa'])}</td><td class='r'>{num(r['n'])}</td>"
        f"<td class='r'>{num(r['pct_n'],1)}%</td><td class='r'>{brl(r['total'])}</td>"
        f"<td class='r'>{num(r['pct_valor'],1)}%</td></tr>" for r in fa)
    return f"""
    <div class="exhibit">
      <div class="ex-num">Exhibit 4</div>
      <h3>Distribuição dos proventos por faixa (mai/2026)</h3>
      <table>
        <thead><tr><th>Faixa</th><th class='r'>Servidores</th><th class='r'>% serv.</th>
        <th class='r'>Folha</th><th class='r'>% folha</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <p class="src">Concentração: a faixa "20k+" é a elite remuneratória analisada na tese A2 (teto).</p>
    </div>"""


def exhibit_rubricas(d):
    ru = d.get("rubricas_top", [])[:15]
    par = d.get("rubricas_pareto", {})
    rows = "".join(
        f"<tr><td>{esc(r['descricao'])[:48]}</td><td class='r'>{brl(r.get('valor_mes_medio'))}</td>"
        f"<td class='r'>{num(r.get('pct'),1)}%</td><td class='r'>{num(r.get('pct_acum'),1)}%</td></tr>"
        for r in ru)
    return f"""
    <div class="exhibit">
      <div class="ex-num">Exhibit 5</div>
      <h3>Concentração de rubricas — top 15 (média mensal)</h3>
      <p class="lead">As 168 rubricas concentram-se: top 5 = {num(par.get('top5_pct'),1)}% ·
      top 10 = {num(par.get('top10_pct'),1)}% · top 20 = {num(par.get('top20_pct'),1)}% da folha.</p>
      <table>
        <thead><tr><th>Rubrica</th><th class='r'>Valor/mês</th><th class='r'>% folha</th><th class='r'>% acum.</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>"""


def exhibit_teses(aud):
    teses = aud.get("teses", [])
    if not teses:
        return ""
    rows = ""
    for t in teses:
        cls = t.get("classificacao_final") or t.get("classificacao") or "🟡"
        cor = CLAS_COR.get(cls.strip()[:1], "#E08600") if isinstance(cls, str) else "#E08600"
        rs = t.get("rs_ajustado_mes") or t.get("rs_mes")
        rows += (
            f"<tr><td><strong>{esc(t.get('id'))}</strong> {esc(t.get('titulo'))}</td>"
            f"<td style='color:{cor};font-weight:700'>{esc(cls)}</td>"
            f"<td class='r'>{brl(rs) if rs else '—'}</td>"
            f"<td>{esc(t.get('veredito',''))}</td></tr>")
    return f"""
    <div class="exhibit">
      <div class="ex-num">Exhibit 6</div>
      <h3>Teses jurídicas A1–A5 (município) — geradas e verificadas adversarialmente</h3>
      <table>
        <thead><tr><th>Tese</th><th>Risco</th><th class='r'>R$/mês em questão</th><th>Veredito do revisor</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <p class="src">🔴 alto · 🟡 atenção · 🟢 conforme. R$ = montante exposto/em discussão, não economia garantida.</p>
    </div>"""


def teses_detalhe(aud):
    teses = aud.get("teses", [])
    if not teses:
        return ""
    blocks = []
    for t in teses:
        cls = t.get("classificacao_final") or t.get("classificacao") or ""
        fund = t.get("fundamento") or []
        fund_html = "".join(f"<li>{_inline(f)}</li>" for f in fund) if isinstance(fund, list) else _inline(str(fund))
        blocks.append(f"""
        <div class="tese">
          <h4>{esc(t.get('id'))} · {esc(t.get('titulo'))} <span class="tag">{esc(cls)}</span></h4>
          <div class="tese-body">{md_to_html(t.get('achado',''))}</div>
          {('<p class="fund-label">Fundamento legal:</p><ul class="fund">'+fund_html+'</ul>') if fund else ''}
          {('<p class="rec"><strong>Recomendação:</strong> '+_inline(t.get('recomendacao',''))+'</p>') if t.get('recomendacao') else ''}
          {('<p class="verif"><strong>Verificação adversarial:</strong> '+_inline(t.get('critica_revisor',''))+'</p>') if t.get('critica_revisor') else ''}
        </div>""")
    return f'<h2 class="sec">Teses jurídicas — detalhamento</h2>{"".join(blocks)}'


def exhibit_matriz(aud):
    mz = aud.get("matriz", [])
    if not mz:
        return ""
    rows = "".join(
        f"<tr><td>{esc(m.get('item'))}</td><td>{esc(m.get('valor'))}</td>"
        f"<td>{esc(m.get('confianca'))}</td><td>{esc(m.get('exequibilidade'))}</td>"
        f"<td class='r'>{brl(m.get('rs_ano')) if m.get('rs_ano') else '—'}</td></tr>" for m in mz)
    return f"""
    <div class="exhibit">
      <div class="ex-num">Exhibit 8</div>
      <h3>Matriz de priorização — valor × confiança × exequibilidade</h3>
      <table>
        <thead><tr><th>Iniciativa</th><th>Valor</th><th>Confiança</th><th>Exequibilidade</th><th class='r'>R$/ano</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <p class="src">Envelope de oportunidade — não somar cegamente (glosa ≠ contingência ≠ risco ≠ saneamento).</p>
    </div>"""


def exhibit_eficiencia(tb, tc):
    oc = tb.get("outliers_cargo", {})
    fr = tb.get("fronteira", {})
    rt = tc.get("resumo_tipo", [])
    rows_c = "".join(
        f"<tr><td>{esc(r['tipo'])}</td><td class='r'>{num(r['n'])}</td><td class='r'>{brl(r['valor_mes'])}</td></tr>"
        for r in rt)
    return f"""
    <div class="exhibit">
      <div class="ex-num">Exhibit 7</div>
      <h3>Eficiência (Trilha B) e qualidade de dado (Trilha C)</h3>
      <div class="two-col">
        <div>
          <p class="lead">Eficiência — custo relativo</p>
          <ul>
            <li>Outliers de cargo (>2× a mediana do próprio cargo): <strong>{num(oc.get('n'))}</strong>,
            desvio de <strong>{brl(oc.get('desvio_total_mes'))}/mês</strong>.</li>
            <li>Folga de custo-hora vs. fronteira: <strong>{brl(fr.get('folga_total_mes'))}/mês</strong>
            <span class="cav">(teto teórico; mede custo, não produtividade).</span></li>
            <li>Concentração: Gini {num(tb.get('concentracao',{}).get('gini_global'),3)};
            top 5% = {num((tb.get('concentracao',{}).get('top5pct_share',0))*100,1)}% da folha.</li>
          </ul>
        </div>
        <div>
          <p class="lead">Quick wins — qualidade de dado</p>
          <table class="mini">
            <thead><tr><th>Anomalia</th><th class='r'>Casos</th><th class='r'>R$/mês</th></tr></thead>
            <tbody>{rows_c}</tbody>
          </table>
        </div>
      </div>
    </div>"""


def exhibit_teto_servidores(tap):
    """Exhibit 6.1 — os servidores acima do teto no LÍQUIDO §11 (= também acima no bruto)."""
    if not tap or not tap.get("lista_511"):
        return ""
    teto = tap["teto_proxy"]["valor"]
    liq = tap.get("liquido_real", {})
    cen = tap["cenarios"]
    rows = ""
    for r in tap["lista_511"]:
        lr = liq.get(r["matricula"], {}).get("liquido_fev")
        marca = " 🩺" if r.get("eh_medico") else (" ⚰️" if r.get("eh_inativo") else "")
        rows += (
            f"<tr><td>{esc(r['nome'][:28])}{marca}</td><td>{esc(r['descr_funcao'][:22])}</td>"
            f"<td>{esc(str(r['secretaria'])[:16])}</td>"
            f"<td class='r'>{brl(r['proventos'])}</td><td class='r'>{brl(r['indeniz'])}</td>"
            f"<td class='r'><strong>{brl(r['base_teto'])}</strong></td>"
            f"<td class='r'>{brl(lr) if lr else '—'}</td>"
            f"<td class='r'>{brl(r['excedente'])}</td>"
            f"<td class='r'>{r['meses_viola']}/3</td></tr>")
    return f"""
    <div class="exhibit">
      <div class="ex-num">Exhibit 6.1</div>
      <h3>Servidores acima do teto — líquido das indenizatórias (art. 37, §11), mai/2026</h3>
      <p class="lead">{cen['base_511']['n']} servidores excedem o subsídio do Prefeito
      ({brl(teto)}) já <em>líquidos</em> das verbas indenizatórias — e, por construção, também
      no bruto. Excedente total {brl(cen['base_511']['exc_mes'])}/mês ({brl(cen['base_511']['exc_ano'])}/ano).</p>
      <table>
        <thead><tr><th>Servidor</th><th>Função</th><th>Secretaria</th><th class='r'>Bruto</th>
        <th class='r'>Indeniz.</th><th class='r'>Base §11</th><th class='r'>Líq. real*</th>
        <th class='r'>Exced. §11</th><th class='r'>Recorr.</th></tr></thead>
        <tbody>{rows}</tbody>
        <tfoot><tr><td colspan="7"><strong>Excedente §11 ({cen['base_511']['n']} servidores)</strong></td>
        <td class='r'><strong>{brl(cen['base_511']['exc_mes'])}</strong></td><td></td></tr></tfoot>
      </table>
      <p class="src">🩺 médico (acumulação lícita / plantão limitado ao subsídio) · ⚰️ inativo/pensionista
      (teto alcança aposentados — EC 41/03 — mas pensão tem regra própria). *Líquido real pós-INSS/IRRF
      só existe na base Saúde/fev (14/{cen['bruto']['n']}), competência distinta — referência.
      Teto-proxy = bruto do Prefeito {brl(teto)}; valor nominal do subsídio ainda pendente.</p>
    </div>"""


def exhibit_delta_511(tap):
    """Exhibit 6.2 — os que superam o teto no BRUTO mas NÃO no líquido §11."""
    if not tap or not tap.get("delta_511"):
        return ""
    rows = "".join(
        f"<tr><td>{esc(r['nome'][:30])}</td><td>{esc(r['descr_funcao'][:20])}</td>"
        f"<td class='r'>{brl(r['proventos'])}</td><td class='r'>{brl(r['indeniz'])}</td>"
        f"<td class='r'><strong>{brl(r['base_teto'])}</strong></td>"
        f"<td>{esc(r['verba_dominante'][:34])}</td></tr>" for r in tap["delta_511"])
    n = len(tap["delta_511"])
    return f"""
    <div class="exhibit">
      <div class="ex-num">Exhibit 6.2</div>
      <h3>Efeito do art. 37, §11 — {n} servidores saem do teto ao excluir indenizatórias</h3>
      <p class="lead">Superam o teto no bruto, mas a base §11 fica <em>abaixo</em>: o excesso era
      férias/13º/rescisão, não remuneração contínua. Inclui o caso AUX.ADMINISTRATIVO I
      (R$ 125.985 → base §11 ≈ R$ 860), apontado no A2 original como prioridade — e que, de fato,
      é rescisão, não violação de teto.</p>
      <table>
        <thead><tr><th>Servidor</th><th>Função</th><th class='r'>Bruto</th><th class='r'>Indeniz.</th>
        <th class='r'>Base §11</th><th>Verba dominante</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <p class="src">Estes {n} são a diferença entre o cenário-bruto ({tap['cenarios']['bruto']['n']})
      e o cenário §11 ({tap['cenarios']['base_511']['n']}).</p>
    </div>"""


def exhibit_brechas(tap):
    """Exhibit 6.3 — aparato de produtividade fiscal e o argumento 'fora do teto'."""
    if not tap or not tap.get("brechas"):
        return ""
    rows = ""
    for x in tap["brechas"]:
        if not x["n_serv_long"]:
            continue
        rows += (
            f"<tr><td><strong>{esc(x['rotulo'])}</strong> <span class='cav'>(cód {x['codigo']})</span></td>"
            f"<td>{esc(x['lei'])}</td><td class='r'>{num(x['n_serv_long'])}</td>"
            f"<td class='r'>{brl(x['valor_mes_long'])}</td><td>{esc(x['tipo_rubrica'])}</td></tr>")
    ab = tap.get("abate_teto_r216", {})
    return f"""
    <div class="exhibit">
      <div class="ex-num">Exhibit 6.3</div>
      <h3>Brecha do teto — produtividade fiscal e gratificações tratadas como "não computáveis"</h3>
      <p class="lead">A Lei 9.526/2023 (art. 9º) diz que os prêmios "não se incorporam aos
      vencimentos" — cláusula de aposentadoria que <strong>não</strong> exclui do teto. O art. 37,
      §11 só exclui parcelas <em>indenizatórias</em>, e a LC 192/2016 (art. 130) inclui as parcelas
      "incorporados ou não": logo a produtividade fiscal <strong>compõe</strong> o teto.</p>
      <table>
        <thead><tr><th>Aparato</th><th>Lei</th><th class='r'>Servidores</th>
        <th class='r'>R$/mês (mai)</th><th>Natureza</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <p class="src">Abate-teto na folha: rubrica <strong>R216 DESC.LIMITE CONSTITUCIONAL</strong>
      aplicada a apenas {ab.get('n_servidores','—')} servidores ({ab.get('fonte','')}) — mecanismo
      existe mas está praticamente desligado. REVADEF segue vigente (Lei 6.990/04, alterada pela
      LC 205/2017, art. 38); cessou só para a Vigilância Sanitária (Lei 9.526/23, art. 10).</p>
    </div>"""


def build():
    d = _load(DATA / "dados_consolidados.json")
    tb = _load(OUT / "trilha_b_resultado.json")
    tc = _load(OUT / "trilha_c_resumo.json")
    aud = _load(OUT / "auditoria_municipio.json", {})
    tap = _load(OUT / "teto_aprofundamento.json", {})
    meta = d.get("meta", {})

    gov = aud.get("governing_thought") or (
        "A folha do município de Sete Lagoas custa ~R$ 49,5 milhões/mês (R$ 148,4 mi no "
        "trimestre mar–mai/2026). Dois terços da exposição de risco concentram-se em "
        "contratação temporária em atividade permanente e na fragmentação de gratificações — "
        "frentes de saneamento jurídico e organização, não de corte linear.")
    sumario = aud.get("sumario_executivo", "")
    km = d.get("kpis_mes", [])
    folha_mes = km[-1]["folha_total"] if km else 0
    headcount = km[-1]["n_servidores"] if km else 0

    limit = "".join(f"<li>{esc(x)}</li>" for x in meta.get("limitacoes", []))
    pend = "".join(f"<li>{_inline(x)}</li>" for x in aud.get("pendencias", [
        "Subsídio mensal do Prefeito (necessário para concluir a tese A2 do teto).",
        "Laudos LTCAT/perícia de insalubridade (tese A4).",
        "Atos de concessão dos apostilamentos (tese A5)."]))
    riscos = "".join(f"<li>{_inline(x)}</li>" for x in aud.get("riscos", []))

    css = """
    :root{--navy:#051C2C;--blue:#2251FF;--ink:#1a1a1a;--mut:#5b6770;--line:#d8dde1;--bg:#fff;--soft:#f4f6f8;}
    *{box-sizing:border-box;}
    body{margin:0;background:#e9edf0;color:var(--ink);font-family:Georgia, 'Times New Roman', serif;}
    .page{max-width:980px;margin:0 auto;background:var(--bg);}
    .sans{font-family:'Segoe UI',Arial,Helvetica,sans-serif;}
    p,li,td,th{font-family:'Segoe UI',Arial,Helvetica,sans-serif;font-size:14.5px;line-height:1.62;color:#23323c;}
    h1,h2,h3,h4{font-family:Georgia,'Times New Roman',serif;color:var(--navy);}
    .cover{background:var(--navy);color:#fff;padding:56px 60px 48px;}
    .cover .kicker{font-family:'Segoe UI',sans-serif;letter-spacing:.22em;font-size:12px;color:#8fb0ff;text-transform:uppercase;}
    .cover h1{color:#fff;font-size:34px;line-height:1.18;margin:14px 0 8px;font-weight:700;}
    .cover .sub{font-family:'Segoe UI',sans-serif;color:#c7d4e0;font-size:15px;}
    .cover .rule{height:3px;width:80px;background:var(--blue);margin:22px 0;}
    .cover .gov{font-size:18px;line-height:1.6;color:#eaf0f7;max-width:760px;}
    .kpibar{display:flex;flex-wrap:wrap;gap:0;border-top:1px solid rgba(255,255,255,.15);margin-top:30px;}
    .kpibar .k{flex:1 1 22%;padding:18px 14px 6px;border-right:1px solid rgba(255,255,255,.12);}
    .kpibar .k:last-child{border-right:none;}
    .kpibar .v{font-family:Georgia,serif;font-size:25px;color:#fff;}
    .kpibar .l{font-family:'Segoe UI',sans-serif;font-size:11.5px;color:#9fb3c8;text-transform:uppercase;letter-spacing:.08em;}
    .body{padding:42px 60px 60px;}
    h2.sec{font-size:23px;border-bottom:2px solid var(--navy);padding-bottom:7px;margin:46px 0 18px;}
    .lead{font-weight:600;color:var(--navy);}
    .exhibit{border:1px solid var(--line);border-radius:3px;margin:26px 0;padding:20px 22px 14px;background:#fff;box-shadow:0 1px 0 rgba(0,0,0,.03);}
    .ex-num{font-family:'Segoe UI',sans-serif;font-size:11px;font-weight:700;letter-spacing:.14em;color:var(--blue);text-transform:uppercase;}
    .exhibit h3{font-size:17px;margin:4px 0 14px;}
    table{width:100%;border-collapse:collapse;margin:6px 0;}
    th{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--mut);text-align:left;border-bottom:2px solid var(--navy);padding:7px 8px;}
    td{padding:6px 8px;border-bottom:1px solid #eceff1;}
    td.r,th.r{text-align:right;}
    tfoot td{border-top:2px solid var(--navy);border-bottom:none;}
    .bar{width:120px;}.bar span{display:block;height:9px;background:var(--blue);border-radius:2px;}
    .src{font-size:11.5px;color:var(--mut);font-style:italic;margin:8px 0 2px;}
    .two-col{display:flex;gap:28px;}.two-col>div{flex:1;}
    table.mini th,table.mini td{font-size:13px;padding:5px 6px;}
    .tese{border-left:4px solid var(--blue);background:var(--soft);padding:14px 18px;margin:14px 0;border-radius:0 3px 3px 0;}
    .tese h4{font-size:16px;margin:0 0 8px;}
    .tag{font-family:'Segoe UI',sans-serif;font-size:12px;font-weight:700;margin-left:8px;}
    .fund-label{font-size:12.5px;color:var(--mut);margin:8px 0 2px;font-weight:600;}
    ul.fund{margin:0 0 8px;padding-left:18px;}ul.fund li{font-size:13px;color:#3a4750;}
    .rec{background:#eef3ff;border:1px solid #cfdcff;padding:8px 12px;border-radius:3px;}
    .verif{font-size:13px;color:#5b6770;border-top:1px dashed #c8d0d6;padding-top:6px;margin-top:6px;}
    .cav{color:var(--mut);font-style:italic;}
    .callout{background:var(--navy);color:#eaf0f7;padding:22px 26px;border-radius:4px;margin:26px 0;}
    .callout p{color:#eaf0f7;}
    .two{display:flex;gap:26px;}.two>div{flex:1;}
    .note{font-size:12.5px;color:var(--mut);border-top:1px solid var(--line);margin-top:40px;padding-top:14px;}
    @media print{body{background:#fff;}.page{max-width:none;}.exhibit{break-inside:avoid;}.tese{break-inside:avoid;}}
    """

    kpibar = f"""
    <div class="kpibar sans">
      <div class="k"><div class="v">{brl(folha_mes)}</div><div class="l">Folha bruta / mês</div></div>
      <div class="k"><div class="v">{num(headcount)}</div><div class="l">Servidores pagos</div></div>
      <div class="k"><div class="v">{num(meta.get('competencias') and 3)} meses</div><div class="l">mar–mai 2026</div></div>
      <div class="k"><div class="v">{num(d.get('cobertura_secretaria_pct'),1)}%</div><div class="l">R$ classificado p/ secretaria</div></div>
    </div>"""

    html_doc = f"""<!doctype html><html lang="pt-br"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sumário Executivo — Auditoria da Folha · Sete Lagoas/MG</title>
<style>{css}</style></head>
<body><div class="page">
  <header class="cover">
    <div class="kicker">Auditoria de custo da folha de pagamento · Município inteiro</div>
    <h1>Prefeitura de Sete Lagoas / MG</h1>
    <div class="sub">Competências março–maio/2026 · 100% da folha · proventos brutos</div>
    <div class="rule"></div>
    <p class="gov">{_inline(gov)}</p>
    {kpibar}
  </header>
  <main class="body">
    <h2 class="sec">Sumário executivo</h2>
    {md_to_html(sumario) if sumario else '<p>(síntese a ser preenchida pelo workflow)</p>'}

    <h2 class="sec">Panorama da folha</h2>
    {exhibit_kpis(d)}
    {exhibit_dim(d, 'por_vinculo', 'Composição por vínculo (mai/2026)', 2, 'Vínculo')}
    {exhibit_dim(d, 'por_secretaria', 'Composição por secretaria (mai/2026)', 3, 'Secretaria')}
    {exhibit_faixas(d)}
    {exhibit_rubricas(d)}

    <h2 class="sec">Achados jurídicos</h2>
    {exhibit_teses(aud)}
    {teses_detalhe(aud)}
    {exhibit_teto_servidores(tap)}
    {exhibit_delta_511(tap)}
    {exhibit_brechas(tap)}

    <h2 class="sec">Eficiência e quick wins</h2>
    {exhibit_eficiencia(tb, tc)}
    {('<div class="two"><div>'+md_to_html(aud.get('eficiencia_texto',''))+'</div><div>'+md_to_html(aud.get('quickwins_texto',''))+'</div></div>') if (aud.get('eficiencia_texto') or aud.get('quickwins_texto')) else ''}

    <h2 class="sec">Priorização e envelope de oportunidade</h2>
    {exhibit_matriz(aud)}
    {('<div class="callout">'+md_to_html(aud.get('envelope_texto',''))+'</div>') if aud.get('envelope_texto') else ''}

    <h2 class="sec">Riscos e pendências</h2>
    <div class="two">
      <div><p class="lead">Pendências externas (bloqueiam conclusões jurídicas)</p><ul>{pend}</ul></div>
      <div><p class="lead">Riscos do diagnóstico</p><ul>{riscos if riscos else '<li>Ver nota metodológica.</li>'}</ul></div>
    </div>

    <div class="note">
      <strong>Nota metodológica e limitações.</strong>
      <ul>{limit}</ul>
      Fontes: <em>base pessoal.xlsx</em> (folha, proventos brutos) × <em>cadastro(32).csv</em>
      (metadados, snapshot 29/03/2026); acervo legal: todas as Leis Complementares do município
      + leis ordinárias citadas em rubricas (API SAPL da Câmara). Secretaria classificada por LLM
      (DeepSeek) sobre as lotações; cobertura {num(d.get('cobertura_secretaria_pct'),1)}% do R$.
      Anualização de recorrentes: fator 13,3× (12 + 13º + ⅓ de férias).
    </div>
  </main>
</div></body></html>"""

    out_html = OUT / "SUMARIO_EXECUTIVO.html"
    out_html.write_text(html_doc, encoding="utf-8")
    size_kb = out_html.stat().st_size / 1024
    print(f"HTML gravado: {out_html} ({size_kb:.0f} KB)")

    # ---------- Relatório consolidado em Markdown ----------
    md = [f"# Auditoria da Folha — Município de Sete Lagoas/MG",
          f"\n> Competências mar–mai/2026 · 100% da folha · proventos brutos · "
          f"gerado em pipeline determinístico + workflow multi-agente (Opus) + DeepSeek (leis).\n",
          f"\n## Governing thought\n\n{gov}\n",
          f"\n## Sumário executivo\n\n{sumario or '(workflow)'}\n",
          f"\n## Panorama (mai/2026)\n",
          f"- Folha: {brl(folha_mes)}/mês · {num(headcount)} servidores · total 3m "
          f"{brl(sum(k['folha_total'] for k in km))}",
          f"- Vínculo: " + " · ".join(f"{r['vinculo']} {num(r['pct_folha'],1)}%" for r in d.get('por_vinculo', [])[:4]),
          f"- Secretaria: " + " · ".join(f"{r['secretaria']} {num(r['pct_folha'],1)}%" for r in d.get('por_secretaria', [])[:4]),
          f"- Concentração: Gini {num(tb.get('concentracao',{}).get('gini_global'),3)} · "
          f"elite>20k {num(d.get('kpis_mes',[{}])[-1].get('elite_n'))} servidores ({num(d.get('faixas',[{}])[-1].get('pct_valor'),1)}% da folha)",
          f"\n## Teses jurídicas A1–A5\n"]
    for t in aud.get("teses", []):
        rs = t.get("rs_ajustado_mes") or t.get("rs_mes")
        md.append(f"\n### {t.get('id')} · {t.get('titulo')} — {t.get('classificacao_final') or t.get('classificacao','')}")
        md.append(f"\n{t.get('achado','')}\n")
        if t.get("fundamento"):
            md.append("**Fundamento:** " + "; ".join(t["fundamento"]) if isinstance(t["fundamento"], list) else str(t["fundamento"]))
        if rs:
            md.append(f"\n- R$ em questão: {brl(rs)}/mês (~{brl(float(rs)*13.3)}/ano)")
        if t.get("recomendacao"):
            md.append(f"- Recomendação: {t['recomendacao']}")
        if t.get("critica_revisor"):
            md.append(f"- Verificação adversarial ({t.get('veredito','')}): {t['critica_revisor']}")
    md.append(f"\n## Eficiência (Trilha B) e quick wins (Trilha C)\n")
    md.append(aud.get("eficiencia_texto", "") + "\n\n" + aud.get("quickwins_texto", ""))
    if aud.get("matriz"):
        md.append("\n## Matriz de priorização\n\n| Iniciativa | Valor | Confiança | Exequibilidade | R$/ano |\n|---|---|---|---|---|")
        for m in aud["matriz"]:
            md.append(f"| {m.get('item','')} | {m.get('valor','')} | {m.get('confianca','')} | "
                      f"{m.get('exequibilidade','')} | {brl(m.get('rs_ano')) if m.get('rs_ano') else '—'} |")
    if aud.get("envelope_texto"):
        md.append(f"\n## Envelope de oportunidade\n\n{aud['envelope_texto']}")
    if aud.get("sumario_final"):
        md.append(f"\n## Fechamento\n\n{aud['sumario_final']}")
    md.append("\n## Pendências externas\n")
    for x in aud.get("pendencias", []):
        md.append(f"- {x}")
    md.append("\n## Limitações e método\n")
    for x in meta.get("limitacoes", []):
        md.append(f"- {x}")
    out_md = OUT / "RELATORIO_AUDITORIA_MUNICIPIO.md"
    out_md.write_text("\n".join(md), encoding="utf-8")
    print(f"MD gravado:   {out_md}")
    return out_html


if __name__ == "__main__":
    build()
