# -*- coding: utf-8 -*-
"""
Re-verificacao do Achado A5 — Salario Apostilado (rubrica 36), mai/2026.
Confirma: universo (109 serv / R$ 506.153,21), 6 acima do teto RGPS, 15 admitidos >= 01/01/2004,
deduplicacao (FLAVIO/AFONSO nos dois grupos). Recalcula o excesso com teto parametrizavel.
Read-only sobre o parquet; exporta anexo CSV/XLSX.
"""
import sys
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent
PARQUET = BASE / "data" / "folha_municipio_long.parquet"
OUT_DIR = BASE.parent / "output" / "municipio"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MES = 5                 # maio/2026
RUBRICA_APOST = 36      # SALARIO APOSTILADO
CORTE = pd.Timestamp("2004-01-01")

# Teto do RGPS (maior provento/teto de beneficios). 2025 = 8157.41.
# Sobrescreva via argv[1] com o valor 2026 verificado na Fase A.
TETO_RGPS = float(sys.argv[1]) if len(sys.argv) > 1 else 8157.41

df = pd.read_parquet(PARQUET)
ap = df[(df["mes"] == MES) & (df["codigo_rubrica"] == RUBRICA_APOST)].copy()

# 1) Universo
n_serv = ap["matricula"].nunique()
total = ap["valor"].sum()
print(f"[UNIVERSO] rubrica {RUBRICA_APOST} / mes {MES}: {n_serv} servidores | R$ {total:,.2f}/mes")
print(f"           anualizado x13,3 = R$ {total*13.3:,.2f}/ano")

# agrega por matricula (caso haja >1 lancamento da mesma rubrica)
g = (ap.groupby("matricula")
       .agg(nome=("nome", "first"), valor=("valor", "sum"),
            admissao=("admissao", "first"), funcao=("descr_funcao", "first"),
            vinculo=("vinculo", "first"))
       .reset_index())

# 2) Acima do teto RGPS
acima = g[g["valor"] > TETO_RGPS].copy()
acima["excesso_mes"] = acima["valor"] - TETO_RGPS
acima = acima.sort_values("valor", ascending=False)
exc_mes = acima["excesso_mes"].sum()
print(f"\n[TETO §2] teto RGPS usado = R$ {TETO_RGPS:,.2f}")
print(f"          {len(acima)} servidores acima do teto | excesso = R$ {exc_mes:,.2f}/mes "
      f"= R$ {exc_mes*13.3:,.2f}/ano")
print(acima[["matricula", "nome", "valor", "excesso_mes"]].to_string(index=False))

# 3) Janela art. 89-B (admissao >= 01/01/2004)
g["adm_dt"] = pd.to_datetime(g["admissao"], format="%d/%m/%Y", errors="coerce")
janela = g[g["adm_dt"] >= CORTE].copy().sort_values("adm_dt")
jan_mes = janela["valor"].sum()
print(f"\n[JANELA 89-B] {len(janela)} servidores admitidos >= 01/01/2004 | "
      f"R$ {jan_mes:,.2f}/mes = R$ {jan_mes*13.3:,.2f}/ano")
print(janela[["matricula", "nome", "admissao", "valor"]].to_string(index=False))

# 4) Deduplicacao (intersecao teto x janela)
# A tese da janela poe em risco o valor INTEGRAL dos 15 (se falham o art. 89-B, o beneficio
# inteiro e improprio) — o que SUBSUME o excesso de teto dos que estao nos dois grupos.
# Combinada de-dup = excesso dos que estao SO no teto + valor integral de TODA a janela.
inter = set(acima["matricula"]) & set(janela["matricula"])
print(f"\n[DEDUP] matriculas nos DOIS grupos: {len(inter)}")
for m in inter:
    r = g[g["matricula"] == m].iloc[0]
    print(f"        {m} {r['nome']} (R$ {r['valor']:,.2f})")
exc_so_teto = acima[~acima["matricula"].isin(janela["matricula"])]["excesso_mes"].sum()
combinada = exc_so_teto + jan_mes
print(f"        excesso dos {len(acima)-len(inter)} so-teto = R$ {exc_so_teto:,.2f}/mes")
print(f"        + janela integral (15) = R$ {jan_mes:,.2f}/mes")
print(f"        exposicao combinada de-duplicada = R$ {combinada:,.2f}/mes "
      f"= R$ {combinada*13.3:,.2f}/ano")

# 5) Export anexo
acima_out = acima[["matricula", "nome", "funcao", "vinculo", "valor", "excesso_mes"]].copy()
acima_out.columns = ["matricula", "nome", "funcao", "vinculo", "valor_apostilado_mes", "excesso_sobre_teto_mes"]
janela_out = janela[["matricula", "nome", "admissao", "funcao", "vinculo", "valor"]].copy()
janela_out.columns = ["matricula", "nome", "admissao", "funcao", "vinculo", "valor_apostilado_mes"]
janela_out["tambem_acima_teto"] = janela_out["matricula"].isin(acima["matricula"])

csv1 = OUT_DIR / "anexo_apostilado_acima_teto.csv"
csv2 = OUT_DIR / "anexo_apostilado_janela_89b.csv"
acima_out.to_csv(csv1, index=False, encoding="utf-8-sig")
janela_out.to_csv(csv2, index=False, encoding="utf-8-sig")
print(f"\n[EXPORT] {csv1}")
print(f"[EXPORT] {csv2}")
try:
    xlsx = OUT_DIR / "anexo_apostilado.xlsx"
    with pd.ExcelWriter(xlsx) as xl:
        acima_out.to_excel(xl, sheet_name="acima_teto_89A2", index=False)
        janela_out.to_excel(xl, sheet_name="janela_89B", index=False)
    print(f"[EXPORT] {xlsx}")
except Exception as e:
    print(f"[EXPORT] xlsx pulado: {e}")
