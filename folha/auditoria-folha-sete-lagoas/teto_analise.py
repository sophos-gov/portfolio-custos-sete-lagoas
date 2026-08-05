#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
teto_analise.py — Análise rigorosa do teto remuneratório (CF art. 37, XI + §11)
Sete Lagoas / MG — competência de referência mai/2026 (município inteiro).

Diferença em relação ao A2 do relatório entregue:
  - O A2 original compara PROVENTOS BRUTOS contra o proxy (subsídio do Prefeito),
    porque assumiu que a base não permitia separar verbas indenizatórias.
  - Aqui usamos o tag `tipo_rubrica == EVENTUAL_INDENIZATORIA` da base LONG para
    EXCLUIR as parcelas indenizatórias (art. 37, §11) e calcular a BASE DE TETO
    correta. A reconciliação long->servidor_mes fecha ao centavo (diff = 0,00).

Saída: output/municipio/teto_aprofundamento.json (single source of truth dos R$),
consumido por municipio/build_html_municipio.py e municipio/injeta_teto_a6.py.

Uso:  python teto_analise.py
"""
import json
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent
FATOR_ANUAL = 13.3          # 12 meses + 13º + 1/3 de férias
MES_REF = 5                 # mai/2026
LONG = BASE / "municipio/data/folha_municipio_long.parquet"
SM = BASE / "municipio/data/servidor_mes.parquet"
SAUDE_FEV = BASE / "data/folha_2026_02_rubricas_long.parquet"
OUT_JSON = BASE / "output/municipio/teto_aprofundamento.json"

RE_MEDICO = "MEDIC|CIRURG|PEDIATR|ORTOPED|ANESTES|PSIQUIATR|GINECOL|RADIOLOG|OTORRIN"
RE_INATIVO = "INATIV|APOSENT|PENS"

# Subsídio do Prefeito — localizado no SAPL/Leis Municipais (2026-06-17).
SUBSIDIO_LEGAL = dict(
    lei_fixacao="Lei nº 8.180/2012 (fixa subsídios p/ a legislatura 2013-2016)",
    lei_alteracao="Lei nº 8.325/2014 (assegura revisão anual pelo IPCA, em janeiro)",
    prefeito_2013=21000.00, vice_2013=14700.00, secretario_2013=9900.00,
    parcela_unica=True, decimo_terceiro=True,
    sem_fixacao_posterior="Não consta no SAPL lei de fixação para as legislaturas "
                          "2017-2020, 2021-2024 nem 2025-2028.",
    proxy_folha_mai2026=33259.37,
    fonte="SAPL Sete Lagoas (normas 5898 e 240); Leis Municipais.")


# --------------------------------------------------------------------------- #
# Carga e base de teto
# --------------------------------------------------------------------------- #
def carregar():
    fl = pd.read_parquet(LONG)
    sm = pd.read_parquet(SM)
    # base de teto = proventos totais - soma das indenizatórias (art. 37, §11)
    ind = (fl[fl["tipo_rubrica"] == "EVENTUAL_INDENIZATORIA"]
           .groupby(["mes", "matricula"])["valor"].sum().rename("indeniz"))
    base = sm.merge(ind, on=["mes", "matricula"], how="left")
    base["indeniz"] = base["indeniz"].fillna(0.0)
    base["base_teto"] = base["proventos"] - base["indeniz"]
    base["eh_medico"] = base["descr_funcao"].str.contains(RE_MEDICO, case=False, na=False)
    base["eh_inativo"] = (base["vinculo"].str.contains(RE_INATIVO, case=False, na=False) |
                          base["descr_funcao"].str.contains("PENS", case=False, na=False))
    return fl, base


def teto_proxy(base):
    """Proxy do teto = maior base_teto do Prefeito (subsídio puro, sem indenizatórias)."""
    pref = base[(base["mes"] == MES_REF) &
                base["descr_funcao"].str.contains("PREFEITO", case=False, na=False) &
                ~base["descr_funcao"].str.contains("VICE", case=False, na=False)]
    r = pref.sort_values("base_teto", ascending=False).iloc[0]
    return dict(valor=float(r["base_teto"]), nome=str(r["nome"]),
                proventos=float(r["proventos"]), indeniz=float(r["indeniz"]))


def _sem_agente_politico(base):
    return base[(base["mes"] == MES_REF) &
                ~base["descr_funcao"].str.contains("PREFEITO", case=False, na=False)]


def cenarios(base, teto):
    """Compara violadores e excedente: critério bruto vs base §11."""
    mai = _sem_agente_politico(base)
    out = {}
    for nome, col in [("bruto", "proventos"), ("base_511", "base_teto")]:
        v = mai[mai[col] > teto]
        exc = float((v[col] - teto).sum())
        out[nome] = dict(n=int(len(v)), exc_mes=round(exc, 2),
                         exc_ano=round(exc * FATOR_ANUAL, 2))
    out["reducao_pct"] = round(
        (1 - out["base_511"]["exc_ano"] / out["bruto"]["exc_ano"]) * 100, 1)
    return out


# --------------------------------------------------------------------------- #
# Listagens (entrega 1: bruto e §11)
# --------------------------------------------------------------------------- #
def _recorrencia(base, teto, col):
    base = base.copy()
    base["_viola"] = base[col] > teto
    return base.groupby("matricula")["_viola"].sum().rename("meses_viola")


def listar(base, teto, criterio):
    """criterio in {'proventos','base_teto'} -> lista de dicts ordenada desc."""
    mai = _sem_agente_politico(base).copy()
    rec = _recorrencia(base, teto, criterio)
    v = mai[mai[criterio] > teto].merge(rec, on="matricula")
    v["excedente"] = v[criterio] - teto
    v = v.sort_values(criterio, ascending=False)
    cols = ["matricula", "nome", "descr_funcao", "secretaria", "vinculo",
            "proventos", "indeniz", "base_teto", "excedente", "meses_viola",
            "eh_medico", "eh_inativo"]
    return [
        {k: (round(float(r[k]), 2) if k in ("proventos", "indeniz", "base_teto", "excedente")
             else int(r[k]) if k == "meses_viola"
             else bool(r[k]) if k in ("eh_medico", "eh_inativo")
             else str(r[k]))
         for k in cols}
        for _, r in v.iterrows()
    ]


def delta_511(fl, base, teto):
    """Os servidores que VIOLAM no bruto mas SAEM no §11, com a verba que os derruba."""
    mai = _sem_agente_politico(base)
    saem = mai[(mai["proventos"] > teto) & (mai["base_teto"] <= teto)].copy()
    out = []
    for _, r in saem.sort_values("indeniz", ascending=False).iterrows():
        comp = fl[(fl["mes"] == MES_REF) & (fl["matricula"] == r["matricula"]) &
                  (fl["tipo_rubrica"] == "EVENTUAL_INDENIZATORIA")]
        top = comp.sort_values("valor", ascending=False).head(1)
        verba = str(top["descricao"].iloc[0]) if len(top) else "—"
        out.append(dict(
            matricula=str(r["matricula"]), nome=str(r["nome"]),
            descr_funcao=str(r["descr_funcao"]), secretaria=str(r["secretaria"]),
            proventos=round(float(r["proventos"]), 2),
            indeniz=round(float(r["indeniz"]), 2),
            base_teto=round(float(r["base_teto"]), 2),
            verba_dominante=verba))
    return out


def liquido_real(matriculas):
    """Anexa líquido real pós-descontos (INSS/IRRF/consignações) da base Saúde/fev.
    Só existe para servidores da Saúde; competência fev/2026 (distinta de mai)."""
    try:
        sau = pd.read_parquet(SAUDE_FEV)
    except Exception:
        return {}
    mcol = sau.columns[0]  # 'Matrícula' (nome com encoding ruim) -> acesso posicional
    liq = sau[[mcol, "Proventos", "Descontos", "Liquido"]].drop_duplicates()
    liq[mcol] = liq[mcol].astype(str)
    alvo = set(str(m) for m in matriculas)
    sub = liq[liq[mcol].isin(alvo)]
    return {str(r[mcol]): dict(proventos_fev=round(float(r["Proventos"]), 2),
                               descontos_fev=round(float(r["Descontos"]), 2),
                               liquido_fev=round(float(r["Liquido"]), 2))
            for _, r in sub.iterrows()}


# --------------------------------------------------------------------------- #
# Abate-teto (R216) e brechas de produtividade fiscal
# --------------------------------------------------------------------------- #
def abate_teto_r216():
    """R216 DESC.LIMITE CONSTITUCIONAL: existe na base limpa Saúde/fev, NÃO no LONG
    do município (que só tem proventos). Mecanismo existe mas é aplicado a ~ninguém."""
    res = dict(fonte="base Saúde/fev (data/folha_2026_02_rubricas_long.parquet)",
               n_servidores=0, total=0.0,
               nota="No LONG do município (proventos brutos) R216 não aparece (0 linhas).")
    try:
        f = pd.read_parquet(SAUDE_FEV)
        r216 = f[f["codigo"] == "R216"]
        res["n_servidores"] = int(r216.iloc[:, 0].nunique())
        res["total"] = round(float(r216["valor"].abs().sum()), 2)
    except Exception:
        pass
    return res


# código -> (rótulo, lei)
APARATO_FISCAL = {
    8:   ("REVADEF", "Lei 6.990/2004 (revogada pela Lei 9.526/2023?)"),
    32:  ("PRODUTIVIDADE FISCAL", "—"),
    347: ("PREVISA", "Lei 9.526/2023"),
    348: ("PROVISA", "Lei 9.526/2023"),
    50:  ("GEPFF", "— (gratificação a investigar; cross-ref A5 apostilamento)"),
}


def brechas(fl):
    """Aparato de produtividade fiscal na folha: nº servidores e R$/mês no LONG
    município (mai) e na base Saúde/fev (divergência de fonte é, em si, um achado)."""
    try:
        sau = pd.read_parquet(SAUDE_FEV)
    except Exception:
        sau = None
    mai = fl[fl["mes"] == MES_REF]
    out = []
    for cod, (rotulo, lei) in APARATO_FISCAL.items():
        g = mai[mai["codigo_rubrica"] == cod]
        reg = dict(codigo=cod, rotulo=rotulo, lei=lei,
                   tipo_rubrica=(str(g["tipo_rubrica"].iloc[0]) if len(g) else "—"),
                   n_serv_long=int(g["matricula"].nunique()),
                   valor_mes_long=round(float(g["valor"].sum()), 2),
                   n_serv_fev=None, valor_mes_fev=None)
        if sau is not None:
            sg = sau[sau["descricao_rubrica"].astype(str).str.contains(
                rotulo.split()[0], case=False, na=False)]
            if len(sg):
                reg["n_serv_fev"] = int(sg.iloc[:, 0].nunique())
                reg["valor_mes_fev"] = round(float(sg["valor"].sum()), 2)
        out.append(reg)
    return out


# --------------------------------------------------------------------------- #
# Agregados e emissão
# --------------------------------------------------------------------------- #
def agregados(lista_511):
    med = [r for r in lista_511 if r["eh_medico"]]
    nao = [r for r in lista_511 if not r["eh_medico"]]
    inat = [r for r in lista_511 if r["eh_inativo"]]
    estrut = [r for r in lista_511 if r["meses_viola"] == 3]
    s = lambda L: round(sum(r["excedente"] for r in L), 2)
    return dict(
        total=len(lista_511),
        medico=dict(n=len(med), exc_mes=s(med), exc_ano=round(s(med) * FATOR_ANUAL, 2)),
        nao_medico=dict(n=len(nao), exc_mes=s(nao), exc_ano=round(s(nao) * FATOR_ANUAL, 2)),
        inativo_pensionista=dict(n=len(inat), exc_mes=s(inat),
                                 exc_ano=round(s(inat) * FATOR_ANUAL, 2)),
        estrutural_3de3=dict(n=len(estrut), exc_mes=s(estrut),
                             exc_ano=round(s(estrut) * FATOR_ANUAL, 2)),
    )


def emitir_json():
    fl, base = carregar()
    proxy = teto_proxy(base)
    teto = proxy["valor"]
    lista_b = listar(base, teto, "proventos")
    lista_5 = listar(base, teto, "base_teto")
    mats = [r["matricula"] for r in lista_b]
    payload = dict(
        meta=dict(competencia="mai/2026", mes_ref=MES_REF, fator_anual=FATOR_ANUAL,
                  metodo="base §11 = proventos − tipo_rubrica==EVENTUAL_INDENIZATORIA"),
        teto_proxy=proxy,
        cenarios=cenarios(base, teto),
        lista_bruto=lista_b,
        lista_511=lista_5,
        delta_511=delta_511(fl, base, teto),
        liquido_real=liquido_real(mats),
        agregados=agregados(lista_5),
        abate_teto_r216=abate_teto_r216(),
        brechas=brechas(fl),
        subsidio_legal=SUBSIDIO_LEGAL,
    )
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main():
    p = emitir_json()
    c = p["cenarios"]
    print(f"TETO proxy (subsídio Prefeito, base §11): R$ {p['teto_proxy']['valor']:,.2f}")
    print(f"  bruto    -> {c['bruto']['n']:3} violadores | "
          f"R$ {c['bruto']['exc_mes']:>12,.0f}/mês | R$ {c['bruto']['exc_ano']:>14,.0f}/ano")
    print(f"  base §11 -> {c['base_511']['n']:3} violadores | "
          f"R$ {c['base_511']['exc_mes']:>12,.0f}/mês | R$ {c['base_511']['exc_ano']:>14,.0f}/ano")
    print(f"  efeito §11: -{c['reducao_pct']:.0f}% na exposição anual")
    a = p["agregados"]
    print(f"  estrutural (3/3): {a['estrutural_3de3']['n']} | "
          f"não-médicos: {a['nao_medico']['n']} (R$ {a['nao_medico']['exc_ano']:,.0f}/ano) | "
          f"médicos: {a['medico']['n']} | inativos/pensão: {a['inativo_pensionista']['n']}")
    print(f"  delta §11 (caem): {len(p['delta_511'])} | "
          f"líquido real disponível p/ {len(p['liquido_real'])} matrículas (Saúde/fev)")
    r = p["abate_teto_r216"]
    print(f"  abate-teto R216: {r['n_servidores']} servidores, R$ {r['total']:,.2f} ({r['fonte']})")
    print(f"  brechas mapeadas: {', '.join(b['rotulo'] for b in p['brechas'])}")
    print(f"JSON -> {OUT_JSON}")


if __name__ == "__main__":
    main()
