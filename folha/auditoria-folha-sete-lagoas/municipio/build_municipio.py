# -*- coding: utf-8 -*-
"""
build_municipio.py — FASE 0 (engenharia de dados) da auditoria da folha do
MUNICÍPIO INTEIRO de Sete Lagoas/MG (competências mar/abr/mai 2026).

Fontes da verdade:
  - ../../base pessoal.xlsx   (folha, SÓ PROVENTOS, formato longo, 3 meses)
  - ../../cadastro(32).csv    (metadados por matrícula; sep=';', latin-1, snapshot 29/03/2026)

Determinístico, roda sem API. Saídas em municipio/data e municipio/tabelas:
  folha_municipio_long.parquet     servidor_mes.parquet
  lotacoes_para_classificar.csv     (input p/ classificação LLM de secretaria)
  dados_consolidados.json           (consumido pelo workflow e pelo build_html)
  + CSVs de apoio (por_vinculo, por_secretaria, faixas, top_*, rubricas_*)

Secretaria: usa municipio/mapa_secretaria.csv se existir (gerado por
classificar_secretaria.py); senão aplica heurística e marca o gap.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent.parent          # auditoria-folha-sete-lagoas/
ROOT = BASE.parent                                       # custos/folha/
XLSX = ROOT / "base pessoal.xlsx"
CAD = ROOT / "cadastro(32).csv"
DATA = BASE / "municipio" / "data"
TAB = BASE / "municipio" / "tabelas"
MAPA_SEC = BASE / "municipio" / "mapa_secretaria.csv"
DATA.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)

MESES = {3: "mar/2026", 4: "abr/2026", 5: "mai/2026"}
REF_MES = 5  # maio = snapshot de referência p/ distribuição/headcount
ELITE = 20000.0
FATOR_ANUAL = 13.3  # 12 + 13º + 1/3 férias (recorrentes)

FAIXAS = [
    (0, 2000, "Até 2k"), (2000, 3000, "2k–3k"), (3000, 5000, "3k–5k"),
    (5000, 8000, "5k–8k"), (8000, 12000, "8k–12k"), (12000, 20000, "12k–20k"),
    (20000, float("inf"), "20k+"),
]


# --------------------------------------------------------------------------- utils
def _sa(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", str(s)) if not unicodedata.combining(c))


def gini(v) -> float:
    x = np.asarray([t for t in v if t is not None and not pd.isna(t) and t >= 0], float)
    if x.size == 0 or x.sum() == 0:
        return 0.0
    x = np.sort(x)
    n = x.size
    idx = np.arange(1, n + 1)
    return float((2 * np.sum(idx * x) - (n + 1) * x.sum()) / (n * x.sum()))


# --------------------------------------------------------------------- classificação de rubrica (por descrição)
def classifica_rubrica(desc: str) -> str:
    d = _sa(desc).upper()
    if re.search(r"VENCIMENTO|SALARIO|SUBSIDIO|PROVENTO\b|VANT.*PESSOAL", d):
        return "BASE"
    if re.search(r"\b13|DECIMO TERCEIRO|FERIAS|ABONO|INDENIZ|RESCIS|SUBSTITUI", d):
        return "EVENTUAL_INDENIZATORIA"
    if re.search(r"INSALUBR|PERICUL|NOTURNO|PLANTAO|SOBREAVISO|HORA EXTRA|EXTRAORD|PRODUTIV", d):
        return "EVENTUAL_VARIAVEL"
    if re.search(r"GRATIF|FUNCAO|COMISS|REPRESENT|CHEFIA|DIRECAO|GERENCIA|ADICIONAL|QUINQUEN|ANUENIO|TRIENIO", d):
        return "GRATIFICACAO_ADICIONAL"
    if re.search(r"FAMILIA|TRANSPORTE|ALIMENTAC|AUXILIO|ABONO PERMANEN|COMPLEMENTO", d):
        return "AUXILIO_COMPLEMENTO"
    return "OUTROS"


# --------------------------------------------------------------------- secretaria (heurística fallback)
def heuristica_secretaria(descr: str) -> str:
    d = _sa(descr).upper()
    if re.search(r"\bESF\b|SAUDE|HOSPITAL|UPA|UBS|SAMU|CAPS|FARMAC|VIGIL.*SANIT|ENFERMAG|CENTRAL DE EXAMES|PRONTO ATEND|MATERNIDADE|AMBULAT|POSTO DE SAUDE|CEREST|NASF", d):
        return "Saúde"
    if re.search(r"ESCOLA|EDUCA|CRECHE|CEMEI|ENSINO|CMEI|PROFESSOR|MAGISTERIO|BIBLIOTEC", d):
        return "Educação"
    if re.search(r"ASSIST|CRAS|CREAS|SOCIAL|BOLSA|CONVIV|ACOLHIMENTO|ABRIGO", d):
        return "Assistência Social"
    if re.search(r"OBRA|INFRAEST|URBAN|PAVIMENT|MANUTENC|SERVICOS URBAN|LIMPEZA|TRANSITO|TRANSPORTE|VIARIO|ILUMINAC|CEMITER", d):
        return "Obras/Serviços Urbanos"
    if re.search(r"GABINETE|SECRETARIA DE ADMIN|FAZENDA|FINANC|PLANEJAMENTO|GESTAO|RECURSOS HUMANOS|PROCURAD|CONTROL|TRIBUT|COMPRAS|LICITAC|TECNOLOGIA|PROTOCOLO", d):
        return "Administração/Gestão"
    if re.search(r"APOSENT|PENSION|INATIV|PREVIDEN|IPSEL|FUNDO PREVID", d):
        return "Inativos/Pensionistas"
    if re.search(r"CULTURA|ESPORTE|LAZER|TURISMO|MEIO AMBIENTE|AMBIENT|AGRICULT|DESENV|INDUSTRIA|COMERCIO|DEFESA CIVIL|GUARDA", d):
        return "Outras"
    return "NAO_CLASSIFICADO"


# --------------------------------------------------------------------- vínculo normalizado
def grupo_vinculo(v: str) -> str:
    d = _sa(v).upper().strip()
    if not d or d == "NAN":
        return "SEM_CADASTRO"
    if "PENSION" in d:
        return "Pensionista"
    if "APOSENT" in d or "INATIV" in d:
        return "Inativo"
    if "TEMPORARI" in d or "CONTRAT" in d:
        return "Contrato Temporário"
    if "COMISS" in d and "ATIVO" in d:
        return "Estatutário+Comissionado"
    if "COMISS" in d:
        return "Cargo em Comissão"
    if "ESTAGI" in d:
        return "Estagiário"
    if "ESTATUTARIO" in d or "EFETIVO" in d:
        return "Estatutário Ativo"
    return d.title()


# --------------------------------------------------------------------- load
def load_folha() -> pd.DataFrame:
    df = pd.read_excel(XLSX, sheet_name="base pessoal")
    f = df.iloc[:, :5].copy()
    f.columns = ["mes", "matricula", "codigo_rubrica", "descricao", "valor"]
    f["matricula"] = f["matricula"].astype(str).str.strip()
    f["descricao"] = f["descricao"].astype(str).str.strip()
    f["valor"] = pd.to_numeric(f["valor"], errors="coerce").fillna(0.0)
    f["mes"] = pd.to_numeric(f["mes"], errors="coerce").astype("Int64")
    f = f[f["mes"].isin(MESES.keys())].copy()
    f["tipo_rubrica"] = f["descricao"].map(classifica_rubrica)
    return f


def load_cadastro() -> pd.DataFrame:
    c = pd.read_csv(CAD, sep=";", encoding="latin-1", dtype=str)
    c.columns = [str(x).strip() for x in c.columns]
    keep = {"matricula": "matricula", "nome": "nome", "admissao": "admissao",
            "rescisao": "rescisao", "lotacao": "lotacao", "descr_lotacao": "descr_lotacao",
            "funcao": "funcao", "descr_funcao": "descr_funcao",
            "descr_tipo_vinculo": "vinculo_raw", "C. Horaria": "horas"}
    cols = {k: v for k, v in keep.items() if k in c.columns}
    c = c.rename(columns=cols)[list(cols.values())].copy()
    c["matricula"] = c["matricula"].astype(str).str.strip()
    for col in ("descr_lotacao", "descr_funcao", "vinculo_raw", "nome"):
        if col in c.columns:
            c[col] = c[col].astype(str).str.strip()
    c["horas"] = pd.to_numeric(c.get("horas"), errors="coerce")
    c["rescindido"] = c["rescisao"].notna() & (c["rescisao"].astype(str).str.strip() != "")
    # dedup: 1 linha por matrícula — preferir ativo (sem rescisão); senão admissão mais recente
    c["_adm"] = pd.to_datetime(c.get("admissao"), format="%d/%m/%Y", errors="coerce")
    c = c.sort_values(["rescindido", "_adm"], ascending=[True, False])
    c = c.drop_duplicates(subset=["matricula"], keep="first").drop(columns=["_adm"])
    c["vinculo"] = c["vinculo_raw"].map(grupo_vinculo)
    return c


# --------------------------------------------------------------------- secretaria mapping
def aplica_secretaria(cad: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    if MAPA_SEC.exists():
        m = pd.read_csv(MAPA_SEC, dtype=str)
        m.columns = [c.strip().lower() for c in m.columns]
        m["descr_lotacao"] = m["descr_lotacao"].astype(str).str.strip()
        m = m.drop_duplicates(subset=["descr_lotacao"])
        cad = cad.merge(m[["descr_lotacao", "secretaria"]], on="descr_lotacao", how="left")
        cad["secretaria"] = cad["secretaria"].fillna(cad["descr_lotacao"].map(heuristica_secretaria))
        fonte = "mapa_secretaria.csv (LLM) + heurística p/ faltantes"
    else:
        cad["secretaria"] = cad["descr_lotacao"].map(heuristica_secretaria)
        fonte = "heurística (mapa_secretaria.csv ausente)"
    return cad, fonte


# --------------------------------------------------------------------- build
def build():
    print(">> carregando fontes...", file=sys.stderr)
    folha = load_folha()
    cad = load_cadastro()
    cad, fonte_sec = aplica_secretaria(cad)

    # servidor x mes (proventos totais) + metadados
    sm = folha.groupby(["mes", "matricula"], as_index=False)["valor"].sum()
    sm = sm.rename(columns={"valor": "proventos"})
    meta_cols = ["matricula", "nome", "descr_lotacao", "descr_funcao", "vinculo",
                 "secretaria", "horas", "admissao", "rescisao"]
    meta = cad[[c for c in meta_cols if c in cad.columns]].copy()
    sm = sm.merge(meta, on="matricula", how="left")
    sm["tem_cadastro"] = sm["nome"].notna()
    sm["vinculo"] = sm["vinculo"].fillna("SEM_CADASTRO")
    sm["secretaria"] = sm["secretaria"].fillna("SEM_CADASTRO")

    # long enriquecido
    long = folha.merge(meta, on="matricula", how="left")

    # persistir bases
    long.to_parquet(DATA / "folha_municipio_long.parquet", index=False)
    sm.to_parquet(DATA / "servidor_mes.parquet", index=False)

    # lotações a classificar (input LLM) — agregado no mês de referência
    smref = sm[sm["mes"] == REF_MES]
    lot = (smref.groupby("descr_lotacao", dropna=False)
           .agg(n_serv=("matricula", "nunique"), rs=("proventos", "sum"))
           .reset_index().sort_values("rs", ascending=False))
    lot["descr_lotacao"] = lot["descr_lotacao"].fillna("(SEM_CADASTRO)")
    lot["rs"] = lot["rs"].round(2)
    lot.to_csv(DATA / "lotacoes_para_classificar.csv", index=False, encoding="utf-8")

    # ----- KPIs por mês + evolução
    kpis_mes = []
    for m in sorted(MESES):
        s = sm[sm["mes"] == m]
        prov = s["proventos"]
        elite = s[prov > ELITE]
        kpis_mes.append({
            "mes": m, "competencia": MESES[m],
            "n_servidores": int(s["matricula"].nunique()),
            "folha_total": round(float(prov.sum()), 2),
            "medio": round(float(prov.mean()), 2),
            "mediana": round(float(prov.median()), 2),
            "gini": round(gini(prov), 4),
            "elite_n": int(len(elite)),
            "elite_total": round(float(elite["proventos"].sum()), 2),
            "elite_pct_folha": round(float(elite["proventos"].sum() / prov.sum() * 100), 2) if prov.sum() else 0.0,
            "cobertura_cadastro_pct": round(float(s["tem_cadastro"].mean() * 100), 2),
        })

    # ----- tabelas no mês de referência (maio)
    sref = sm[sm["mes"] == REF_MES].copy()
    prov = sref["proventos"]

    # faixas
    faixas = []
    for lo, hi, lab in FAIXAS:
        sub = sref[(prov >= lo) & (prov < hi)]
        faixas.append({"faixa": lab, "n": int(len(sub)),
                       "pct_n": round(len(sub) / len(sref) * 100, 2),
                       "total": round(float(sub["proventos"].sum()), 2),
                       "pct_valor": round(float(sub["proventos"].sum() / prov.sum() * 100), 2)})

    # por vínculo (ref) + evolução headcount
    def agg_dim(df, col):
        g = (df.groupby(col, dropna=False)
             .agg(n=("matricula", "nunique"), total=("proventos", "sum"), medio=("proventos", "mean"))
             .reset_index().sort_values("total", ascending=False))
        t = g["total"].sum()
        g["pct_folha"] = (g["total"] / t * 100).round(2)
        g["total"] = g["total"].round(2)
        g["medio"] = g["medio"].round(2)
        return g

    por_vinculo = agg_dim(sref, "vinculo")
    por_secretaria = agg_dim(sref, "secretaria")
    top_unidades = agg_dim(sref, "descr_lotacao").head(20)
    top_cargos = agg_dim(sref, "descr_funcao").head(20)

    # Saúde vs resto (ref)
    sref["_saude"] = np.where(sref["secretaria"] == "Saúde", "Saúde", "Restante do município")
    saude_vs = agg_dim(sref, "_saude")

    # cobertura de classificação de secretaria (% R$ não-classificado)
    nao_clas = sref[sref["secretaria"].isin(["NAO_CLASSIFICADO", "SEM_CADASTRO"])]["proventos"].sum()
    pct_classificado = round(float((1 - nao_clas / prov.sum()) * 100), 2)

    # ----- rubricas (Pareto) — 3 meses agregados / média mensal
    rub = (folha.groupby(["codigo_rubrica", "descricao", "tipo_rubrica"])
           .agg(valor_total_3m=("valor", "sum"),
                n_serv_ref=("matricula", "nunique"),
                n_pagamentos=("valor", "size"))
           .reset_index().sort_values("valor_total_3m", ascending=False))
    rub["valor_mes_medio"] = (rub["valor_total_3m"] / 3).round(2)
    tot_r = rub["valor_total_3m"].sum()
    rub["pct"] = (rub["valor_total_3m"] / tot_r * 100).round(2)
    rub["pct_acum"] = rub["pct"].cumsum().round(2)
    rub["valor_total_3m"] = rub["valor_total_3m"].round(2)
    rubricas_top = rub.head(30)
    pareto = {
        "valor_total_3m": round(float(tot_r), 2),
        "n_rubricas": int(len(rub)),
        "top5_pct": round(float(rub.head(5)["pct"].sum()), 2),
        "top10_pct": round(float(rub.head(10)["pct"].sum()), 2),
        "top20_pct": round(float(rub.head(20)["pct"].sum()), 2),
    }

    # composição por tipo de rubrica (média mensal)
    comp = (folha.groupby("tipo_rubrica")["valor"].sum() / 3).round(2).sort_values(ascending=False)
    comp_tot = comp.sum()
    composicao = [{"tipo": k, "valor_mes": float(v), "pct": round(float(v / comp_tot * 100), 2)}
                  for k, v in comp.items()]

    # ----- salvar CSVs
    por_vinculo.to_csv(TAB / "por_vinculo.csv", index=False, encoding="utf-8")
    por_secretaria.to_csv(TAB / "por_secretaria.csv", index=False, encoding="utf-8")
    pd.DataFrame(faixas).to_csv(TAB / "distribuicao_faixas.csv", index=False, encoding="utf-8")
    top_unidades.to_csv(TAB / "top_unidades.csv", index=False, encoding="utf-8")
    top_cargos.to_csv(TAB / "top_cargos.csv", index=False, encoding="utf-8")
    rubricas_top.to_csv(TAB / "rubricas_top.csv", index=False, encoding="utf-8")

    # ----- consolidado JSON
    dados = {
        "meta": {
            "municipio": "Sete Lagoas (MG)", "escopo": "Município inteiro (100% da folha)",
            "competencias": list(MESES.values()), "mes_referencia": MESES[REF_MES],
            "fonte_folha": "base pessoal.xlsx (só proventos)", "fonte_cadastro": "cadastro(32).csv (snapshot 29/03/2026)",
            "fonte_secretaria": fonte_sec, "fator_anualizacao": FATOR_ANUAL,
            "limitacoes": [
                "Folha contém SÓ PROVENTOS (sem descontos/INSS/IRRF) — sem líquido nem teto líquido.",
                "Secretaria derivada de descr_lotacao (não é coluna nativa).",
                "Cadastro é snapshot de 29/03/2026 — defasagem cresce mar→mai.",
                "Leis fora da Saúde não extraídas — teses fora da Saúde ficam 'pendente de norma'.",
            ],
        },
        "kpis_mes": kpis_mes,
        "kpis_ref": kpis_mes[REF_MES - 3],
        "cobertura_secretaria_pct": pct_classificado,
        "faixas": faixas,
        "por_vinculo": por_vinculo.to_dict("records"),
        "por_secretaria": por_secretaria.to_dict("records"),
        "saude_vs_resto": saude_vs.to_dict("records"),
        "top_unidades": top_unidades.to_dict("records"),
        "top_cargos": top_cargos.to_dict("records"),
        "rubricas_top": rubricas_top.to_dict("records"),
        "rubricas_pareto": pareto,
        "composicao_tipo": composicao,
    }
    (DATA / "dados_consolidados.json").write_text(
        json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

    # ----- reconciliação (mostrar)
    print("\n" + "=" * 64)
    print("RECONCILIAÇÃO — FASE 0 (município inteiro)")
    print("=" * 64)
    for k in kpis_mes:
        print(f"{k['competencia']}: {k['n_servidores']:>5} serv | "
              f"R$ {k['folha_total']:>16,.2f} | médio {k['medio']:>9,.2f} | "
              f"Gini {k['gini']} | elite>20k {k['elite_n']:>3} | cad {k['cobertura_cadastro_pct']}%")
    print(f"\nTotal 3 meses: R$ {sum(k['folha_total'] for k in kpis_mes):,.2f}")
    print(f"Cobertura de SECRETARIA (R$ classificado, {MESES[REF_MES]}): {pct_classificado}% "
          f"[fonte: {fonte_sec}]")
    print(f"Lotações distintas a classificar: {lot.shape[0]}")
    print(f"\nVÍNCULO ({MESES[REF_MES]}):")
    for r in por_vinculo.itertuples():
        print(f"  {r.vinculo:<28} n={r.n:>5}  R$ {r.total:>15,.2f}  ({r.pct_folha}%)")
    print(f"\nSECRETARIA ({MESES[REF_MES]}):")
    for r in por_secretaria.itertuples():
        print(f"  {r.secretaria:<28} n={r.n:>5}  R$ {r.total:>15,.2f}  ({r.pct_folha}%)")
    print(f"\nSaúde vs resto: " + " | ".join(
        f"{r['_saude']} {r['pct_folha']}%" for r in saude_vs.to_dict("records")))
    print(f"\nRubricas: {pareto['n_rubricas']} | top5 {pareto['top5_pct']}% | "
          f"top10 {pareto['top10_pct']}% | top20 {pareto['top20_pct']}%")
    print("\nArquivos gravados em municipio/data e municipio/tabelas.")
    return dados


if __name__ == "__main__":
    build()
