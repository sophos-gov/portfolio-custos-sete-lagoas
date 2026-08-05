# -*- coding: utf-8 -*-
"""
TRILHA C - Quick Wins de Qualidade de Dado
Auditoria da Folha de Sete Lagoas (2026-02)

Detecta, com matricula e valor:
 1. Horas Semanais fisicamente impossiveis (>60 ou ==0 com Proventos>0)
 2. Servidores com Descontos >= 99% dos Proventos (liquido ~ zero)
 3. Ghost-payment em rubricas de plantao/sobreaviso (Quant==0 e Valor>0)
 4. Fragmentacao de rubricas identicas (LC 192 art.149 + Funcao Gratificada)

REGRA "CERTEIRO": todo achado tem matricula e R$ quantificado.
Anualizacao de recorrentes: fator 13,3x (12 + 13o + 1/3 ferias).
"""
import sys
import io
import os
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import pandas as pd
import numpy as np

WIDE = "C:/Users/victo/OneDrive/Documentos/Python/projetos/custos/folha/01_folha_limpa/folha_2026_02_wide.parquet"
OUT_DIR = "C:/Users/victo/OneDrive/Documentos/Python/projetos/custos/folha/auditoria-folha-sete-lagoas/output/reducao_custos"
OUT_CSV = os.path.join(OUT_DIR, "trilha_c_anomalias.csv")
FATOR_ANUAL = 13.3

os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_parquet(WIDE)
cols = list(df.columns)

# Normaliza acesso aos campos meta
def col(name):
    return df[name]

anomalias = []  # lista de dicts: tipo, matricula, cargo, unidade, detalhe, valor

def add(tipo, row, detalhe, valor):
    anomalias.append({
        "tipo": tipo,
        "matricula": str(row["Matrícula"]),
        "cargo": str(row["Cargo"]),
        "unidade": str(row["nome_unidade"]),
        "detalhe": detalhe,
        "valor": round(float(valor), 2),
    })

# ============================================================
# 1. HORAS SEMANAIS FISICAMENTE IMPOSSIVEIS
# ============================================================
hs = df["Horas Semanais"]
prov = df["Proventos"]

mask_alta = hs > 60
mask_zero = (hs == 0) & (prov > 0)

for _, r in df[mask_alta].iterrows():
    add(
        "HORAS_IMPOSSIVEIS_>60",
        r,
        f"Horas Semanais = {r['Horas Semanais']:.0f} (fisicamente impossivel; "
        f"semana tem 168h). Erro de cadastro/digitacao. Proventos R$ {r['Proventos']:.2f}",
        r["Proventos"],
    )

for _, r in df[mask_zero].iterrows():
    add(
        "HORAS_ZERO_COM_PROVENTO",
        r,
        f"Horas Semanais = 0 porem Proventos = R$ {r['Proventos']:.2f}. "
        f"Cadastro de jornada ausente (impede controle de carga horaria).",
        r["Proventos"],
    )

# ============================================================
# 2. DESCONTOS >= 99% DOS PROVENTOS (LIQUIDO ~ ZERO)
# ============================================================
sub = df[df["Proventos"] > 0].copy()
sub["ratio"] = sub["Descontos"] / sub["Proventos"]
mask_desc = sub["ratio"] >= 0.99
for _, r in sub[mask_desc].iterrows():
    add(
        "DESCONTO_>=99%",
        r,
        f"Descontos R$ {r['Descontos']:.2f} = {r['ratio']*100:.1f}% dos Proventos "
        f"R$ {r['Proventos']:.2f}; Liquido R$ {r['Liquido']:.2f}. "
        f"Servidor sem remuneracao liquida (verificar consignacoes/devolucoes).",
        r["Descontos"],
    )

# ============================================================
# 3. GHOST-PAYMENT EM PLANTAO/SOBREAVISO (Quant==0 & Valor>0)
# ============================================================
PLANTAO_CODES = ["0249","0250","0251","0252","0253","0254","0255","0256","0258",
                 "0313","0314","0373","0374","0375","0376"]

ghost_resumo = {}   # code -> dict(desc, n_ghost, valor_ghost, n_com_quant, total_pagantes)
for cd in PLANTAO_CODES:
    qcols = [c for c in cols if c.startswith("Quant__" + cd)]
    vcols = [c for c in cols if c.startswith("Valor__" + cd)]
    if not qcols or not vcols:
        ghost_resumo[cd] = {"desc": "(coluna ausente)", "n_ghost": 0,
                            "valor_ghost": 0.0, "n_com_quant": 0, "n_pagantes": 0}
        continue
    qc, vc = qcols[0], vcols[0]
    desc = vc.split("__", 2)[-1] if vc.count("__") >= 2 else vc
    q = df[qc].fillna(0)
    v = df[vc].fillna(0)
    pagantes = v > 0
    ghost_mask = (q == 0) & (v > 0)
    n_ghost = int(ghost_mask.sum())
    n_com_quant = int(((q > 0) & (v > 0)).sum())
    n_pagantes = int(pagantes.sum())
    valor_ghost = float(v[ghost_mask].sum())
    ghost_resumo[cd] = {
        "desc": desc, "n_ghost": n_ghost, "valor_ghost": valor_ghost,
        "n_com_quant": n_com_quant, "n_pagantes": n_pagantes,
    }
    for _, r in df[ghost_mask].iterrows():
        add(
            "GHOST_PAYMENT_PLANTAO",
            r,
            f"Rubrica {cd} {desc}: Quant = 0 porem Valor = R$ {r[vc]:.2f} "
            f"(pagamento sem registro de plantao/sobreaviso).",
            r[vc],
        )

# ============================================================
# 4. FRAGMENTACAO DE RUBRICAS IDENTICAS
# ============================================================
# 4a. LC 192 art. 149 (5 codigos, mesma descricao)
LC192_CODES = ["0266","0275","0276","0281","0307"]
# 4b. Funcao Gratificada em 4 niveis
FG_CODES = ["0368","0369","0370","0371"]

frag_resumo = {"LC192_ART149": {}, "FUNCAO_GRATIFICADA": {}}

def perfil_codigo(cd):
    vcols = [c for c in cols if c.startswith("Valor__" + cd)]
    if not vcols:
        return None
    vc = vcols[0]
    desc = vc.split("__", 2)[-1] if vc.count("__") >= 2 else vc
    v = df[vc].fillna(0)
    pagantes = v > 0
    return {
        "codigo": cd, "rubrica_col": vc, "desc": desc,
        "n_serv": int(pagantes.sum()), "valor_mes": float(v[pagantes].sum()),
        "mask": pagantes, "vcol": vc,
    }

for cd in LC192_CODES:
    p = perfil_codigo(cd)
    if p:
        frag_resumo["LC192_ART149"][cd] = {k: p[k] for k in ("desc","n_serv","valor_mes")}
        # registra linha-a-linha como anomalia de fragmentacao (rastreabilidade)
        for _, r in df[p["mask"]].iterrows():
            add(
                "FRAGMENTACAO_LC192_ART149",
                r,
                f"Rubrica {cd} ({p['desc']}) - uma de 5 rubricas com a MESMA base "
                f"legal (LC192 art.149). Valor R$ {r[p['vcol']]:.2f}. "
                f"Recomenda-se consolidacao administrativa em codigo unico.",
                r[p["vcol"]],
            )

for cd in FG_CODES:
    p = perfil_codigo(cd)
    if p:
        frag_resumo["FUNCAO_GRATIFICADA"][cd] = {k: p[k] for k in ("desc","n_serv","valor_mes")}
        for _, r in df[p["mask"]].iterrows():
            add(
                "FRAGMENTACAO_FUNCAO_GRATIFICADA",
                r,
                f"Rubrica {cd} ({p['desc']}) - uma de 4 rubricas distintas de "
                f"Funcao Gratificada por nivel. Valor R$ {r[p['vcol']]:.2f}. "
                f"Avaliar consolidacao/tabela unica de niveis.",
                r[p["vcol"]],
            )

# ============================================================
# EXPORTA CSV LINHA-A-LINHA
# ============================================================
adf = pd.DataFrame(anomalias, columns=["tipo","matricula","cargo","unidade","detalhe","valor"])
adf.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

# ============================================================
# RESUMO POR TIPO
# ============================================================
print("=" * 70)
print("TRILHA C - RESUMO POR TIPO")
print("=" * 70)
resumo_tipo = (adf.groupby("tipo")
               .agg(n_casos=("matricula","count"), valor_mes=("valor","sum"))
               .reset_index()
               .sort_values("valor_mes", ascending=False))
for _, r in resumo_tipo.iterrows():
    print(f"{r['tipo']:<35} n={int(r['n_casos']):>4}  R$/mes={r['valor_mes']:>14,.2f}")
print(f"\nTOTAL CASOS: {len(adf)}")
print(f"CSV salvo: {OUT_CSV}")

# ============================================================
# DETALHE GHOST
# ============================================================
print("\n" + "=" * 70)
print("GHOST-PAYMENT PLANTAO/SOBREAVISO (por rubrica)")
print("=" * 70)
print(f"{'cod':<5}{'pagantes':>9}{'c/Quant>0':>11}{'ghost':>7}{'R$ ghost':>14}  desc")
for cd in PLANTAO_CODES:
    g = ghost_resumo[cd]
    print(f"{cd:<5}{g['n_pagantes']:>9}{g['n_com_quant']:>11}{g['n_ghost']:>7}"
          f"{g['valor_ghost']:>14,.2f}  {g['desc']}")
g0249 = ghost_resumo["0249"]
print(f"\nCONFIRMACAO 0249: {g0249['n_com_quant']}/{g0249['n_pagantes']} com Quant>0, "
      f"ghost={g0249['n_ghost']} (plano afirma SEM ghost em 0249).")

# ============================================================
# DETALHE FRAGMENTACAO
# ============================================================
print("\n" + "=" * 70)
print("FRAGMENTACAO LC192 ART.149 (5 rubricas, mesma base legal)")
print("=" * 70)
tot_serv_192 = 0
tot_val_192 = 0.0
for cd, info in frag_resumo["LC192_ART149"].items():
    print(f"{cd}  serv={info['n_serv']:>4}  R$/mes={info['valor_mes']:>13,.2f}  {info['desc']}")
    tot_serv_192 += info["n_serv"]
    tot_val_192 += info["valor_mes"]
print(f"TOTAL LC192: {tot_serv_192} pagamentos, R$ {tot_val_192:,.2f}/mes "
      f"(R$ {tot_val_192*FATOR_ANUAL:,.2f}/ano)")

print("\nFRAGMENTACAO FUNCAO GRATIFICADA (4 niveis)")
print("=" * 70)
tot_serv_fg = 0
tot_val_fg = 0.0
for cd, info in frag_resumo["FUNCAO_GRATIFICADA"].items():
    print(f"{cd}  serv={info['n_serv']:>4}  R$/mes={info['valor_mes']:>13,.2f}  {info['desc']}")
    tot_serv_fg += info["n_serv"]
    tot_val_fg += info["valor_mes"]
print(f"TOTAL FG: {tot_serv_fg} pagamentos, R$ {tot_val_fg:,.2f}/mes "
      f"(R$ {tot_val_fg*FATOR_ANUAL:,.2f}/ano)")

# ============================================================
# DUMP JSON ESTRUTURADO (para o agente montar saida)
# ============================================================
saida = {
    "resumo_tipo": resumo_tipo.to_dict(orient="records"),
    "total_casos": len(adf),
    "ghost_resumo": ghost_resumo,
    "frag_resumo": frag_resumo,
    "frag_totais": {
        "LC192_n_pagamentos": tot_serv_192, "LC192_valor_mes": tot_val_192,
        "FG_n_pagamentos": tot_serv_fg, "FG_valor_mes": tot_val_fg,
    },
    "exemplos": {},
}
for tipo in adf["tipo"].unique():
    ex = adf[adf["tipo"] == tipo].head(8)[["matricula","cargo","valor","detalhe"]]
    saida["exemplos"][tipo] = ex.to_dict(orient="records")

with open(os.path.join(OUT_DIR, "trilha_c_resumo.json"), "w", encoding="utf-8") as f:
    json.dump(saida, f, ensure_ascii=False, indent=2)

print("\nJSON resumo salvo:", os.path.join(OUT_DIR, "trilha_c_resumo.json"))
