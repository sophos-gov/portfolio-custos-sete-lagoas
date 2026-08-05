# -*- coding: utf-8 -*-
"""
trilha_c_municipio.py — TRILHA C (quick wins / qualidade de dado) — MUNICÍPIO.

Adaptado ao formato município (long só-proventos + cadastro). Detecta, com
matrícula e R$:
  C.1 Carga horária impossível (>60h/sem) ou ausente/0 com provento>0.
  C.2 Matrícula PAGA SEM CADASTRO (defasagem do snapshot 29/03) — R$ por mês.
  C.3 Fragmentação de rubricas de mesmo propósito (várias GRAT/FUNÇÃO/ADICIONAL).
  C.4 Variação brusca de proventos mar→mai (> 50% p/ mais ou p/ menos).

Saídas em output/municipio/: trilha_c_anomalias.csv + trilha_c_resumo.json
"""
from __future__ import annotations

import io
import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
except Exception:
    pass

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "municipio" / "data"
OUT = BASE / "output" / "municipio"
OUT.mkdir(parents=True, exist_ok=True)
FATOR = 13.3


def _up(s):
    return "".join(c for c in unicodedata.normalize("NFKD", str(s)) if not unicodedata.combining(c)).upper()


def main():
    sm = pd.read_parquet(DATA / "servidor_mes.parquet")
    long = pd.read_parquet(DATA / "folha_municipio_long.parquet")
    anomalias = []

    def add(tipo, matricula, detalhe, valor, **extra):
        anomalias.append({"tipo": tipo, "matricula": str(matricula), "detalhe": detalhe,
                          "valor": round(float(valor), 2), **extra})

    ref = sm[sm["mes"] == 5].copy()
    ref["horas"] = pd.to_numeric(ref["horas"], errors="coerce")

    # ---------- C.1 carga horária ----------
    for r in ref[ref["horas"] > 60].itertuples():
        add("HORAS_IMPOSSIVEIS_>60", r.matricula,
            f"Carga horária {r.horas:.0f}h/sem (impossível). Cargo {getattr(r,'descr_funcao','')}. "
            f"Proventos R$ {r.proventos:.2f}", r.proventos, cargo=getattr(r, "descr_funcao", ""))
    m0 = ref[(ref["horas"].isna() | (ref["horas"] == 0)) & (ref["proventos"] > 0) & (ref["tem_cadastro"])]
    for r in m0.itertuples():
        add("HORAS_ZERO_OU_AUSENTE", r.matricula,
            f"Carga horária ausente/0 com proventos R$ {r.proventos:.2f} (impede controle de jornada).",
            r.proventos, cargo=getattr(r, "descr_funcao", ""))

    # ---------- C.2 pago SEM cadastro (por mês) ----------
    sem_cad_resumo = {}
    for m in sorted(sm["mes"].unique()):
        s = sm[(sm["mes"] == m) & (~sm["tem_cadastro"])]
        sem_cad_resumo[int(m)] = {"n": int(len(s)), "valor": round(float(s["proventos"].sum()), 2)}
    # listar os do mês de referência (maio) como anomalias rastreáveis
    for r in sm[(sm["mes"] == 5) & (~sm["tem_cadastro"])].itertuples():
        add("PAGO_SEM_CADASTRO", r.matricula,
            f"Matrícula paga em mai/2026 (R$ {r.proventos:.2f}) sem registro no cadastro "
            f"(snapshot 29/03; contratação posterior ou inconsistência).", r.proventos)

    # ---------- C.3 fragmentação de rubricas (mesmo propósito) ----------
    rub = (long[long["mes"] == 5].groupby(["codigo_rubrica", "descricao"])
           .agg(n=("matricula", "nunique"), valor=("valor", "sum")).reset_index())
    def familia(d):
        u = _up(d)
        if "FUNCAO GRATIFICADA" in u or re.search(r"\bFG\b", u):
            return "FUNCAO_GRATIFICADA"
        if "INSALUBR" in u:
            return "INSALUBRIDADE"
        if "PLANTAO" in u:
            return "PLANTAO"
        if "URGENCIA" in u or "URGÊNCIA" in u:
            return "URGENCIA"
        if "PRODUTIV" in u:
            return "PRODUTIVIDADE"
        if u.startswith("GRATIFICACAO") or u.startswith("GRATIF") or "GRAT." in u or "GRAT " in u:
            return "GRATIFICACAO_GERAL"
        if "ADICIONAL" in u:
            return "ADICIONAL"
        return None
    rub["familia"] = rub["descricao"].map(familia)
    frag = (rub.dropna(subset=["familia"]).groupby("familia")
            .agg(n_rubricas=("codigo_rubrica", "nunique"), n_serv=("n", "sum"),
                 valor_mes=("valor", "sum")).reset_index().sort_values("valor_mes", ascending=False))
    frag = frag[frag["n_rubricas"] >= 2]
    frag_resumo = frag.to_dict("records")

    # ---------- C.4 variação brusca mar->mai ----------
    piv = sm.pivot_table(index="matricula", columns="mes", values="proventos", aggfunc="sum")
    if 3 in piv.columns and 5 in piv.columns:
        both = piv.dropna(subset=[3, 5])
        both = both[both[3] > 0]
        var = (both[5] - both[3]) / both[3]
        bruscas = both[(var.abs() > 0.5)].copy()
        bruscas["var_pct"] = (var[bruscas.index] * 100).round(1)
        bruscas = bruscas.reindex(var[bruscas.index].abs().sort_values(ascending=False).index)
        meta = sm[sm["mes"] == 5].set_index("matricula")[["descr_funcao", "vinculo", "secretaria"]]
        for mat, row in bruscas.head(300).iterrows():
            info = meta.loc[mat] if mat in meta.index else {}
            add("VARIACAO_BRUSCA_MAR_MAI", mat,
                f"Proventos mar R$ {row[3]:.2f} -> mai R$ {row[5]:.2f} ({row['var_pct']:+.0f}%). "
                f"Cargo {info.get('descr_funcao','') if hasattr(info,'get') else ''}.",
                abs(row[5] - row[3]), var_pct=float(row["var_pct"]))
        n_bruscas = int(len(bruscas))
    else:
        n_bruscas = 0

    # ---------- export ----------
    adf = pd.DataFrame(anomalias)
    if not adf.empty:
        adf.to_csv(OUT / "trilha_c_anomalias.csv", index=False, encoding="utf-8-sig")
    resumo_tipo = (adf.groupby("tipo").agg(n=("matricula", "count"), valor_mes=("valor", "sum"))
                   .reset_index().sort_values("valor_mes", ascending=False)) if not adf.empty else pd.DataFrame()

    saida = {
        "resumo_tipo": resumo_tipo.to_dict("records") if not resumo_tipo.empty else [],
        "total_casos": int(len(adf)),
        "sem_cadastro_por_mes": sem_cad_resumo,
        "fragmentacao": frag_resumo,
        "n_variacoes_bruscas": n_bruscas,
        "exemplos": {},
    }
    if not adf.empty:
        for t in adf["tipo"].unique():
            saida["exemplos"][t] = adf[adf["tipo"] == t].head(6)[["matricula", "valor", "detalhe"]].to_dict("records")
    (OUT / "trilha_c_resumo.json").write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")

    print("[C] anomalias:", len(adf))
    if not resumo_tipo.empty:
        for r in resumo_tipo.itertuples():
            print(f"   {r.tipo:<28} n={r.n:>4}  R$/mês {r.valor_mes:>14,.2f}")
    print("   SEM_CADASTRO por mês:", {k: v["n"] for k, v in sem_cad_resumo.items()})
    print("   Fragmentação famílias:", [(f["familia"], f["n_rubricas"]) for f in frag_resumo])
    print("   Variações bruscas mar→mai:", n_bruscas)


if __name__ == "__main__":
    main()
