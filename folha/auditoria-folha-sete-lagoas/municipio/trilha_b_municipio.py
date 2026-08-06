# -*- coding: utf-8 -*-
"""
trilha_b_municipio.py — TRILHA B (eficiência / custo relativo) — MUNICÍPIO INTEIRO.

Consome municipio/data/servidor_mes.parquet (mês de referência = maio).
LIMITAÇÃO DECLARADA: mede CUSTO RELATIVO por hora-contratada, NÃO produtividade.

B.1 Outliers de cargo: por descr_funcao (≥8 serv), servidores > 2× a mediana do cargo.
B.2 Custo-hora por secretaria: fronteira = p10 do custo_hora das unidades; folga em R$.
B.3 Concentração: Gini global + share dos top X%.

Saídas em output/municipio/: trilha_b_*.csv + trilha_b_resultado.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "municipio" / "data"
OUT = BASE / "output" / "municipio"
OUT.mkdir(parents=True, exist_ok=True)
REF_MES = 5
FATOR = 13.3
INATIVOS = {"Inativo", "Pensionista"}


def gini(x):
    x = np.sort(np.asarray([v for v in x if v >= 0], float))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return float("nan")
    cum = np.cumsum(x)
    return float((n + 1 - 2 * np.sum(cum) / cum[-1]) / n)


def main():
    sm = pd.read_parquet(DATA / "servidor_mes.parquet")
    df = sm[sm["mes"] == REF_MES].copy()
    df = df[~df["vinculo"].isin(INATIVOS)].copy()
    df["proventos"] = pd.to_numeric(df["proventos"], errors="coerce")
    df["horas"] = pd.to_numeric(df["horas"], errors="coerce")

    # horas mensais padronizadas a partir das semanais (válidas 0<h<=60)
    hs = df["horas"].where((df["horas"] > 0) & (df["horas"] <= 60))
    df["horas_mes"] = hs * 4.33
    mask = (df["horas_mes"] > 0) & (df["proventos"] > 0)
    df["custo_hora"] = np.where(mask, df["proventos"] / df["horas_mes"], np.nan)

    # ---------- B.1 OUTLIERS DE CARGO (> 2x mediana do cargo, >=8 serv) ----------
    out_rows = []
    for cargo, sub in df.groupby("descr_funcao"):
        if len(sub) < 8 or not isinstance(cargo, str):
            continue
        med = sub["proventos"].median()
        if med <= 0:
            continue
        for r in sub[sub["proventos"] > 2 * med].itertuples():
            out_rows.append({
                "matricula": r.matricula, "cargo": cargo,
                "secretaria": getattr(r, "secretaria", ""), "unidade": getattr(r, "descr_lotacao", ""),
                "vinculo": r.vinculo, "proventos": round(float(r.proventos), 2),
                "mediana_cargo": round(float(med), 2),
                "multiplo": round(float(r.proventos / med), 2),
                "desvio_mes": round(float(r.proventos - med), 2),
                "desvio_ano_x13_3": round(float((r.proventos - med) * FATOR), 2),
            })
    outliers = pd.DataFrame(out_rows).sort_values("desvio_mes", ascending=False) if out_rows else pd.DataFrame()
    if not outliers.empty:
        outliers.to_csv(OUT / "trilha_b_outliers.csv", sep=";", index=False, encoding="utf-8-sig")
    desvio_total = float(outliers["desvio_mes"].clip(lower=0).sum()) if not outliers.empty else 0.0

    # ---------- B.2 CUSTO-HORA POR SECRETARIA (fronteira p10 das unidades) ----------
    valid = df[df["custo_hora"].notna()].copy()
    unid = (valid.groupby(["secretaria", "descr_lotacao"])
            .agg(n=("custo_hora", "size"), custo_hora=("custo_hora", "mean"),
                 horas_med=("horas_mes", "mean"), proventos=("proventos", "sum"))
            .reset_index())

    def fronteira(s):
        return float(np.percentile(s["custo_hora"], 10)) if len(s) >= 3 else float(s["custo_hora"].min())
    fmap = unid.groupby("secretaria")[["custo_hora"]].apply(fronteira)
    unid["fronteira"] = unid["secretaria"].map(fmap)
    unid["delta"] = unid["custo_hora"] - unid["fronteira"]
    unid["folga_mes"] = np.where(unid["delta"] > 0, unid["delta"] * unid["horas_med"] * unid["n"], 0.0)
    unid = unid.sort_values("folga_mes", ascending=False)
    unid_out = unid.round(2)
    unid_out.to_csv(OUT / "trilha_b_fronteira.csv", sep=";", index=False, encoding="utf-8-sig")
    folga_total = float(unid["folga_mes"].sum())

    resumo_sec = (unid.groupby("secretaria")
                  .agg(n_unidades=("descr_lotacao", "size"), folga_mes=("folga_mes", "sum"))
                  .sort_values("folga_mes", ascending=False).round(2).reset_index())

    # ---------- B.3 CONCENTRAÇÃO ----------
    prov = df["proventos"].dropna().values
    gini_global = gini(prov)
    ps = np.sort(prov)[::-1]
    tot = ps.sum()
    csum = np.cumsum(ps) / tot
    n = len(ps)
    share_top5 = ps[:int(0.05 * n)].sum() / tot
    share_top1 = ps[:int(0.01 * n)].sum() / tot

    resultado = {
        "limitacao": ("Mede CUSTO RELATIVO por hora-contratada padronizada (horas do cadastro × 4,33), "
                      "NÃO PRODUTIVIDADE. Folga é TETO de oportunidade a validar contra produção real."),
        "n_servidores_ativos": int(len(df)),
        "n_com_custo_hora": int(mask.sum()),
        "outliers_cargo": {
            "n": int(len(outliers)),
            "desvio_total_mes": round(desvio_total, 2),
            "desvio_total_ano_x13_3": round(desvio_total * FATOR, 2),
            "top": outliers.head(15).to_dict("records") if not outliers.empty else [],
        },
        "fronteira": {
            "folga_total_mes": round(folga_total, 2),
            "folga_total_ano_x13_3": round(folga_total * FATOR, 2),
            "por_secretaria": resumo_sec.to_dict("records"),
            "top_unidades": unid_out.head(15).to_dict("records"),
        },
        "concentracao": {
            "gini_global": round(gini_global, 4),
            "top1pct_share": round(float(share_top1), 4),
            "top5pct_share": round(float(share_top5), 4),
        },
    }
    (OUT / "trilha_b_resultado.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[B] ativos {len(df)} | outliers cargo {len(outliers)} (desvio R$ {desvio_total:,.0f}/mês) | "
          f"folga fronteira R$ {folga_total:,.0f}/mês | Gini {gini_global:.4f} | "
          f"top5% = {share_top5*100:.1f}% da folha")


if __name__ == "__main__":
    main()
