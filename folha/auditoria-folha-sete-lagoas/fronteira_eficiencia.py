# -*- coding: utf-8 -*-
"""
TRILHA B - FRONTEIRA DE EFICIENCIA (modo "fronteira so com a folha")
Auditoria Folha Sete Lagoas - Saude 2026-02

OBJETIVO: medir CUSTO RELATIVO por hora padronizado entre unidades de funcao
homogenea, identificar folga (diferenca para a fronteira de menor custo viavel),
outliers alocativos por cargo e concentracao da folha.

LIMITACAO DECLARADA (CRITICA): este modelo mede CUSTO RELATIVO por hora-contratada,
NAO PRODUTIVIDADE. Nao temos outputs de producao (consultas, procedimentos,
atendimentos) por unidade. Uma unidade "cara por hora" pode ser cara porque
produz mais/complexidade maior. A folga estimada e um TETO de oportunidade a ser
validado contra producao real (SIA/SUS, BPA, produtividade), NAO um corte direto.

Regra CERTEIRO: todo numero e quantificado em R$. Recorrentes anualizados x13,3
(12 + 13o + 1/3 ferias).
"""
import json
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path("C:/Users/victo/OneDrive/Documentos/Python/projetos/custos/folha")
PARQUET = BASE / "01_folha_limpa" / "folha_2026_02_wide.parquet"
AUD = BASE / "auditoria-folha-sete-lagoas"
ALERTAS = AUD / "analysis" / "tabelas" / "alertas_folha.csv"
OUT_DIR = AUD / "output" / "reducao_custos"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FATOR_ANUAL = 13.3  # 12 + 13o + 1/3 ferias

# ---------------------------------------------------------------------------
# 1. CARGA
# ---------------------------------------------------------------------------
df = pd.read_parquet(PARQUET)  # preserva acentos (NAO usar CSV wide / mojibake)

# Ativos: excluir APOSENTADO / PENSIONISTA
ATIVOS = ~df["categoria_vinculo"].isin(["APOSENTADO", "PENSIONISTA"])
df = df[ATIVOS].copy()

# ---------------------------------------------------------------------------
# 2. HORAS MENSAIS PADRONIZADAS
#    - usar 'Horas Mensais' se valida (>0)
#    - senao derivar de 'Horas Semanais' * 4.33
#    - descartar Horas Semanais invalidas (>60 ou ==0)
# ---------------------------------------------------------------------------
hm = pd.to_numeric(df["Horas Mensais"], errors="coerce")
hs = pd.to_numeric(df["Horas Semanais"], errors="coerce")

# semanais validas: 0 < hs <= 60
hs_valida = hs.where((hs > 0) & (hs <= 60))
hm_derivada = hs_valida * 4.33

horas = hm.where(hm > 0)            # comeca com horas mensais validas
horas = horas.fillna(hm_derivada)  # preenche com derivada das semanais
# Horas mensais absurdas tambem sao suspeitas: limite plausivel 60*4.33=259.8 -> deixar teto 280
horas = horas.where(horas <= 280)  # descarta horas mensais absurdas (>280)

df["horas_pad"] = horas

prov = pd.to_numeric(df["Proventos"], errors="coerce")
df["prov_num"] = prov

# custo por hora: somente onde horas validas e proventos > 0
mask_valido = (df["horas_pad"] > 0) & (df["prov_num"] > 0)
df["custo_hora"] = np.where(mask_valido, df["prov_num"] / df["horas_pad"], np.nan)

n_descartados = int((~mask_valido).sum())
print(f"[B.1] Servidores ativos: {len(df)} | com custo_hora valido: {int(mask_valido.sum())} | descartados (horas/prov invalidos): {n_descartados}")

# ---------------------------------------------------------------------------
# 3. FUNCAO HOMOGENEA inferida do nome_unidade
#    Mapeamento documentado por palavras-chave (ordem importa - mais especifico antes).
# ---------------------------------------------------------------------------
def norm(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return s.upper().strip()

def grupo_funcional(nome_unidade: str) -> str:
    u = norm(nome_unidade)
    # Urgencia/emergencia primeiro (UPA, PA, PRONTO)
    if "UPA" in u or "P.A" in u or "PA BELO" in u or "PRONTO" in u or "P A " in u or u.startswith("PA "):
        return "URGENCIA_UPA_PA"
    if "HOSPITAL" in u or "HOSPITALAR" in u:
        return "HOSPITAL"
    if "SAMU" in u:
        return "SAMU"
    if "HEMOMINAS" in u:
        return "HEMOMINAS"
    if "LABORAT" in u or "CENTRAL DE EXAMES" in u:
        return "LABORATORIO_EXAMES"
    # Saude mental
    if "CAPS" in u:
        return "SAUDE_MENTAL_CAPS"
    if "AUTISMO" in u or "VIVA VIDA" in u or "REFERENCIA AO AUTISMO" in u:
        return "REABILITACAO_ESPECIAL"
    # Saude bucal / odontologia
    if "SAUDE BUCAL" in u or "ODONTOLOG" in u or "CEO" in u:
        return "SAUDE_BUCAL"
    # Atencao basica (ESF, CS, ACS, NASF, UAA, SAE)
    if u.startswith("ESF") or "ESF " in u or "ACS" in u or u.startswith("CS ") or "NASF" in u \
       or u == "UAA" or u.startswith("UAA") or "SAE" in u:
        return "ATENCAO_BASICA_ESF_CS"
    # Especialidades medicas
    if "C.E.M" in u or "CEM" in u or "ESPEC. MEDICAS" in u or "CENTRAL DE EXAMES CONTRAT" in u \
       or "SAUDE AUDITIVA" in u or "CENTRO DE REF" in u:
        return "ESPECIALIDADES_CEM"
    # Fisioterapia / reabilitacao
    if "FISIOTERAPIA" in u:
        return "REABILITACAO_ESPECIAL"
    # Vigilancia (sanitaria, epidemiologica, zoonose, endemias, dengue)
    if "VIGIL" in u or "ZOONOSE" in u or "C.C.Z" in u or "CCZ" in u or "ENDEMIA" in u or "DENGUE" in u or "EAPP" in u:
        return "VIGILANCIA_ENDEMIAS"
    # Farmacia / almoxarifado / logistica / transporte / manutencao
    if "FARMAC" in u or "ALMOX" in u or "TRANSPORTE" in u or "MANUTENC" in u:
        return "LOGISTICA_APOIO"
    # Administracao / comissionados / cedidos
    if "ADMINISTRA" in u or "COMISSIONAD" in u or "CEDIDOS" in u:
        return "ADMINISTRACAO"
    return "OUTROS"

df["grupo_funcional"] = df["nome_unidade"].map(grupo_funcional)

# ---------------------------------------------------------------------------
# 4. FRONTEIRA POR GRUPO (B.1)
#    - custo_hora medio por unidade (so servidores validos)
#    - fronteira do grupo = percentil 10 do custo_hora das UNIDADES do grupo
#    - folga unidade = (custo_hora_unid - fronteira) * horas_med_unid * n_serv_unid
#    - so folga positiva
# ---------------------------------------------------------------------------
valid = df[df["custo_hora"].notna()].copy()

# agregado por unidade
unid = (
    valid.groupby(["grupo_funcional", "nome_unidade"])
    .agg(
        n_servidores=("custo_hora", "size"),
        custo_hora=("custo_hora", "mean"),
        horas_med=("horas_pad", "mean"),
        proventos_total=("prov_num", "sum"),
    )
    .reset_index()
)

# fronteira: percentil 10 do custo_hora medio das unidades de cada grupo
# usar apenas grupos com >=3 unidades para a fronteira ser robusta; senao usar min do grupo
def fronteira_grupo(sub: pd.DataFrame) -> float:
    if len(sub) >= 3:
        return float(np.percentile(sub["custo_hora"], 10))
    return float(sub["custo_hora"].min())

fronteira_map = unid.groupby("grupo_funcional")[["custo_hora"]].apply(fronteira_grupo)
unid["custo_hora_fronteira"] = unid["grupo_funcional"].map(fronteira_map)

# n de unidades por grupo (para transparencia)
n_unid_grupo = unid.groupby("grupo_funcional")["nome_unidade"].transform("size")
unid["n_unidades_grupo"] = n_unid_grupo

unid["delta_custo_hora"] = unid["custo_hora"] - unid["custo_hora_fronteira"]
unid["folga_mes"] = np.where(
    unid["delta_custo_hora"] > 0,
    unid["delta_custo_hora"] * unid["horas_med"] * unid["n_servidores"],
    0.0,
)
unid["folga_ano_x13_3"] = unid["folga_mes"] * FATOR_ANUAL

unid = unid.sort_values("folga_mes", ascending=False).reset_index(drop=True)

folga_total_mes = float(unid["folga_mes"].sum())
print(f"[B.1] Folga total estimada/mes (teto de custo relativo): R$ {folga_total_mes:,.2f}")
print(f"[B.1] Folga total anualizada x13,3: R$ {folga_total_mes*FATOR_ANUAL:,.2f}")

# salvar ranking de unidades
cols_out = [
    "grupo_funcional", "nome_unidade", "n_unidades_grupo", "n_servidores",
    "custo_hora", "custo_hora_fronteira", "delta_custo_hora",
    "horas_med", "proventos_total", "folga_mes", "folga_ano_x13_3",
]
unid_out = unid[cols_out].round(2)
unid_out.to_csv(OUT_DIR / "trilha_b_fronteira.csv", sep=";", index=False, encoding="utf-8-sig")
print(f"[B.1] Salvo: {OUT_DIR / 'trilha_b_fronteira.csv'}")

# resumo por grupo
resumo_grupo = (
    unid.groupby("grupo_funcional")
    .agg(
        n_unidades=("nome_unidade", "size"),
        n_servidores=("n_servidores", "sum"),
        custo_hora_fronteira=("custo_hora_fronteira", "first"),
        folga_mes=("folga_mes", "sum"),
    )
    .sort_values("folga_mes", ascending=False)
    .round(2)
)
print("\n[B.1] Folga por GRUPO FUNCIONAL (R$/mes):")
print(resumo_grupo.to_string())

# ---------------------------------------------------------------------------
# 5. OUTLIERS ALOCATIVOS POR CARGO (B.2)
#    reaproveita alertas OUTLIER_CARGO; desvio = proventos - mediana do cargo.
#    Mediana do cargo recomputada a partir da propria folha (todos ativos) p/ robustez.
# ---------------------------------------------------------------------------
al = pd.read_csv(ALERTAS)
oc = al[al["tipo"] == "OUTLIER_CARGO"].copy()

# mediana do cargo a partir da folha completa de ativos
med_cargo = df.groupby("Cargo")["prov_num"].median()
oc["mediana_cargo"] = oc["cargo"].map(med_cargo)
# fallback: extrair mediana do texto detalhe se cargo nao casar
import re
def med_from_detalhe(s):
    m = re.search(r"R\$\s*([\d\.\,]+)", str(s))
    if not m:
        return np.nan
    v = m.group(1).replace(".", "").replace(",", ".")
    try:
        return float(v)
    except ValueError:
        return np.nan
oc["mediana_cargo"] = oc["mediana_cargo"].fillna(oc["detalhe"].map(med_from_detalhe))

oc["proventos"] = pd.to_numeric(oc["proventos"], errors="coerce")
oc["desvio_mes"] = oc["proventos"] - oc["mediana_cargo"]
oc["multiplo"] = oc["proventos"] / oc["mediana_cargo"]
oc["desvio_ano_x13_3"] = oc["desvio_mes"] * FATOR_ANUAL

oc = oc.sort_values("desvio_mes", ascending=False).reset_index(drop=True)

out_oc = oc[[
    "matricula", "cargo", "unidade", "categoria_vinculo",
    "proventos", "mediana_cargo", "desvio_mes", "multiplo", "desvio_ano_x13_3",
]].round(2)
out_oc.to_csv(OUT_DIR / "trilha_b_outliers.csv", sep=";", index=False, encoding="utf-8-sig")
print(f"\n[B.2] Outliers de cargo: {len(oc)} | salvo: {OUT_DIR / 'trilha_b_outliers.csv'}")
desvio_total_mes = float(oc["desvio_mes"].clip(lower=0).sum())
print(f"[B.2] Desvio total sobre mediana (positivo)/mes: R$ {desvio_total_mes:,.2f} | anualizado x13,3: R$ {desvio_total_mes*FATOR_ANUAL:,.2f}")

# ---------------------------------------------------------------------------
# 6. CONCENTRACAO (B.3)
#    Gini global da folha (proventos, ativos) e por unidade; checagem do
#    "4,54% dos servidores = 19,37% da folha".
# ---------------------------------------------------------------------------
def gini(x: np.ndarray) -> float:
    x = np.sort(np.asarray(x, dtype=float))
    x = x[x >= 0]
    n = len(x)
    if n == 0 or x.sum() == 0:
        return float("nan")
    cum = np.cumsum(x)
    return float((n + 1 - 2 * np.sum(cum) / cum[-1]) / n)

prov_ativos = df["prov_num"].dropna().values
gini_global = gini(prov_ativos)

# checagem 4,54% = 19,37%
n_tot = len(df)
prov_sorted = np.sort(prov_ativos)[::-1]
total_folha = prov_sorted.sum()
k = int(round(0.0454 * n_tot))
share_topk = prov_sorted[:k].sum() / total_folha
print(f"\n[B.3] N ativos={n_tot} | Folha ativos/mes=R$ {total_folha:,.2f} | Gini global={gini_global:.4f}")
print(f"[B.3] Top {k} servidores ({k/n_tot*100:.2f}%) concentram {share_topk*100:.2f}% da folha (claim: 4,54% = 19,37%)")

# busca o ponto exato que da ~19,37%
csum = np.cumsum(prov_sorted) / total_folha
idx_1937 = int(np.searchsorted(csum, 0.1937)) + 1
print(f"[B.3] {idx_1937} servidores ({idx_1937/n_tot*100:.2f}%) acumulam exatamente 19,37% da folha")

# Gini por unidade (unidades com >=5 servidores)
gini_rows = []
for u, sub in df.groupby("nome_unidade"):
    pv = sub["prov_num"].dropna().values
    if len(pv) >= 5:
        gini_rows.append({
            "nome_unidade": u,
            "n_servidores": len(pv),
            "proventos_total": float(pv.sum()),
            "gini": gini(pv),
            "prov_max": float(pv.max()),
            "prov_min": float(pv.min()),
        })
gini_df = pd.DataFrame(gini_rows).sort_values("gini", ascending=False).round(4)
print("\n[B.3] Top 10 unidades por desigualdade interna (Gini, >=5 serv):")
print(gini_df.head(10).to_string(index=False))

# ---------------------------------------------------------------------------
# 7. SAIDA ESTRUTURADA (JSON) para o orquestrador
# ---------------------------------------------------------------------------
top_fronteira = unid_out.head(15).to_dict(orient="records")
top_outliers = out_oc.head(15).to_dict(orient="records")

resultado = {
    "fronteira_unidades": top_fronteira,
    "outliers_cargo": top_outliers,
    "folga_total_estimada_mes": round(folga_total_mes, 2),
    "folga_total_estimada_ano_x13_3": round(folga_total_mes * FATOR_ANUAL, 2),
    "desvio_outliers_total_mes": round(desvio_total_mes, 2),
    "gini_global": round(gini_global, 4),
    "concentracao": {
        "n_ativos": n_tot,
        "folha_mensal_ativos": round(float(total_folha), 2),
        "top_4_54pct_share": round(float(share_topk), 4),
        "n_serv_para_19_37pct": int(idx_1937),
        "pct_serv_para_19_37pct": round(idx_1937 / n_tot * 100, 2),
    },
    "resumo_grupos": resumo_grupo.reset_index().to_dict(orient="records"),
    "arquivos": [
        str(OUT_DIR / "trilha_b_fronteira.csv"),
        str(OUT_DIR / "trilha_b_outliers.csv"),
    ],
    "limitacao": (
        "Mede CUSTO RELATIVO por hora-contratada padronizada, NAO PRODUTIVIDADE. "
        "Faltam outputs de producao (consultas/procedimentos/atendimentos) por unidade. "
        "A folga e TETO de oportunidade a validar contra producao real, nao corte direto."
    ),
}

with open(OUT_DIR / "trilha_b_resultado.json", "w", encoding="utf-8") as f:
    json.dump(resultado, f, ensure_ascii=False, indent=2)
print(f"\n[OK] JSON salvo: {OUT_DIR / 'trilha_b_resultado.json'}")
print("[OK] FIM TRILHA B")
