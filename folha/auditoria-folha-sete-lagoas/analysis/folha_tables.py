#!/usr/bin/env python3
"""
folha_tables.py — Núcleo DETERMINÍSTICO da análise de custo da folha (Saúde / Sete Lagoas).

Roda 100% sem API. Consome o LONG já-classificado (`folha_2026_02_rubricas_long.csv`)
e os agregados de `01_folha_limpa/`, e gera as tabelas analíticas em `tabelas/`.

Saídas (em <out_dir>):
  kpis_folha.json          distribuicao_faixas.csv   rubricas_top.csv
  por_vinculo.csv          top_unidades.csv          rubricas_pareto.json
  alertas_folha.csv        top_cargos.csv            dados_consolidados.json

`gerar_tudo()` retorna o dicionário consolidado (também salvo em dados_consolidados.json),
consumido por build_html.py e pela narrativa do agente.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

# Rubricas que NÃO compõem proventos (descontos numéricos; todos os R### já são excluídos)
DESCONTOS_NUMERICOS = {"0500", "1952", "1959", "1960"}

# Vínculos que não são "ativos" para fins de custo de pessoal corrente
VINCULOS_INATIVOS = {"APOSENTADO", "PENSIONISTA"}

# Faixas de proventos (R$) — adaptadas ao perfil da Saúde
FAIXAS = [
    (0, 2000, "Até 2k"),
    (2000, 3000, "2k–3k"),
    (3000, 5000, "3k–5k"),
    (5000, 8000, "5k–8k"),
    (8000, 12000, "8k–12k"),
    (12000, 20000, "12k–20k"),
    (20000, float("inf"), "20k+"),
]

ELITE_THRESHOLD = 20000.0
DESCONTO_ALTO_PCT = 0.50


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------
def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def _norm_col(c: str) -> str:
    c = _strip_accents(str(c)).strip().lower()
    c = re.sub(r"[^\w]+", "_", c).strip("_")
    return c


def _read_csv_robusto(path: Path, **kw) -> pd.DataFrame:
    """Lê CSV ';' tentando utf-8 e caindo para latin-1 (mojibake-safe)."""
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(path, sep=";", encoding=enc, **kw)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, sep=";", encoding="latin-1", errors="replace", **kw)


def gini(valores) -> float:
    """Coeficiente de Gini de uma série de valores não-negativos."""
    x = np.asarray([v for v in valores if v is not None and not pd.isna(v) and v >= 0], dtype=float)
    if x.size == 0 or x.sum() == 0:
        return 0.0
    x = np.sort(x)
    n = x.size
    cum = np.cumsum(x)
    # G = (2*sum(i*x_i) - (n+1)*sum(x)) / (n*sum(x))
    idx = np.arange(1, n + 1)
    return float((2 * np.sum(idx * x) - (n + 1) * cum[-1]) / (n * cum[-1]))


# ---------------------------------------------------------------------------
# Carregamento
# ---------------------------------------------------------------------------
def load_long(data_dir: Path) -> pd.DataFrame:
    """Carrega o LONG (1 linha por servidor×rubrica) com colunas normalizadas."""
    csv = data_dir / "folha_2026_02_rubricas_long.csv"
    pq = data_dir / "folha_2026_02_rubricas_long.parquet"
    if csv.exists():
        df = _read_csv_robusto(csv, dtype={"codigo": str})
    elif pq.exists():
        df = pd.read_parquet(pq)
    else:
        raise FileNotFoundError(f"LONG não encontrado em {data_dir}")

    df.columns = [_norm_col(c) for c in df.columns]
    # Garantir colunas esperadas
    rename = {"matricula": "matricula", "categoria_vinculo": "categoria_vinculo",
              "nome_unidade": "nome_unidade", "cargo": "cargo"}
    for col in ("proventos", "descontos", "liquido", "valor"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "codigo" in df.columns:
        df["codigo"] = df["codigo"].astype(str).str.strip()
    return df


def servidores_frame(long: pd.DataFrame) -> pd.DataFrame:
    """Reduz o LONG a 1 linha por servidor (totais Proventos/Descontos/Liquido)."""
    cols = [c for c in ("matricula", "nome", "nome_unidade", "cargo", "categoria_vinculo",
                        "proventos", "descontos", "liquido") if c in long.columns]
    serv = long[cols].drop_duplicates(subset=["matricula"]).reset_index(drop=True)
    return serv


def _ativos(serv: pd.DataFrame) -> pd.DataFrame:
    return serv[~serv["categoria_vinculo"].isin(VINCULOS_INATIVOS)].copy()


# ---------------------------------------------------------------------------
# Tabelas
# ---------------------------------------------------------------------------
def gerar_kpis(serv: pd.DataFrame) -> dict:
    ativos = _ativos(serv)
    prov = ativos["proventos"].fillna(0)
    desc = ativos["descontos"].fillna(0)
    elite = ativos[ativos["proventos"] > ELITE_THRESHOLD]
    return {
        "competencia": "2026-02",
        "secretaria": "Saúde",
        "municipio": "Sete Lagoas (MG)",
        "n_servidores_total": int(len(serv)),
        "n_ativos": int(len(ativos)),
        "n_inativos": int(len(serv) - len(ativos)),
        "proventos_total": round(float(prov.sum()), 2),
        "descontos_total": round(float(desc.sum()), 2),
        "liquido_total": round(float(ativos["liquido"].fillna(0).sum()), 2),
        "proventos_medio": round(float(prov.mean()), 2),
        "proventos_mediana": round(float(prov.median()), 2),
        "gini_proventos": round(gini(prov), 4),
        "taxa_desconto_pct": round(float(desc.sum() / prov.sum() * 100) if prov.sum() else 0.0, 2),
        "elite_acima_20k": {
            "n": int(len(elite)),
            "total": round(float(elite["proventos"].sum()), 2),
            "pct_servidores": round(float(len(elite) / len(ativos) * 100) if len(ativos) else 0.0, 2),
            "pct_folha": round(float(elite["proventos"].sum() / prov.sum() * 100) if prov.sum() else 0.0, 2),
        },
    }


def gerar_por_vinculo(serv: pd.DataFrame, data_dir: Path | None = None) -> pd.DataFrame:
    g = (serv.groupby("categoria_vinculo")
         .agg(n=("matricula", "nunique"),
              proventos_total=("proventos", "sum"),
              proventos_medio=("proventos", "mean"),
              liquido_total=("liquido", "sum"))
         .reset_index()
         .sort_values("proventos_total", ascending=False))
    tot = g["proventos_total"].sum()
    g["pct_folha"] = (g["proventos_total"] / tot * 100).round(2) if tot else 0.0
    g["proventos_total"] = g["proventos_total"].round(2)
    g["proventos_medio"] = g["proventos_medio"].round(2)
    g["liquido_total"] = g["liquido_total"].round(2)
    return g


def gerar_faixas(serv: pd.DataFrame) -> pd.DataFrame:
    ativos = _ativos(serv)
    rows = []
    tot_n = len(ativos)
    tot_v = ativos["proventos"].sum()
    for lo, hi, label in FAIXAS:
        m = (ativos["proventos"] >= lo) & (ativos["proventos"] < hi)
        sub = ativos[m]
        rows.append({
            "faixa": label,
            "n": int(len(sub)),
            "pct_n": round(len(sub) / tot_n * 100, 2) if tot_n else 0.0,
            "proventos_total": round(float(sub["proventos"].sum()), 2),
            "pct_valor": round(float(sub["proventos"].sum() / tot_v * 100), 2) if tot_v else 0.0,
        })
    return pd.DataFrame(rows)


def gerar_top_unidades(serv: pd.DataFrame, data_dir: Path | None = None, top: int = 15) -> pd.DataFrame:
    # Preferir agregado pré-calculado se existir
    if data_dir and (data_dir / "agg_por_unidade.csv").exists():
        g = _read_csv_robusto(data_dir / "agg_por_unidade.csv")
        g.columns = [_norm_col(c) for c in g.columns]
        g = g.rename(columns={"n_servidores": "n"})
        g = g.sort_values("proventos_total", ascending=False).head(top)
    else:
        g = (serv.groupby("nome_unidade")
             .agg(n=("matricula", "nunique"),
                  proventos_total=("proventos", "sum"),
                  proventos_medio=("proventos", "mean"))
             .reset_index().sort_values("proventos_total", ascending=False).head(top))
    tot = serv["proventos"].sum()
    g["pct_folha"] = (g["proventos_total"] / tot * 100).round(2) if tot else 0.0
    for c in ("proventos_total", "proventos_medio"):
        if c in g.columns:
            g[c] = g[c].round(2)
    return g.reset_index(drop=True)


def gerar_top_cargos(serv: pd.DataFrame, data_dir: Path | None = None, top: int = 15) -> pd.DataFrame:
    if data_dir and (data_dir / "agg_por_cargo.csv").exists():
        g = _read_csv_robusto(data_dir / "agg_por_cargo.csv")
        g.columns = [_norm_col(c) for c in g.columns]
        g = g.sort_values("proventos_total", ascending=False).head(top)
    else:
        g = (serv.groupby("cargo")
             .agg(n=("matricula", "nunique"),
                  proventos_total=("proventos", "sum"),
                  proventos_medio=("proventos", "mean"))
             .reset_index().sort_values("proventos_total", ascending=False).head(top))
    tot = serv["proventos"].sum()
    g["pct_folha"] = (g["proventos_total"] / tot * 100).round(2) if tot else 0.0
    for c in ("proventos_total", "proventos_medio"):
        if c in g.columns:
            g[c] = g[c].round(2)
    return g.reset_index(drop=True)


def gerar_alertas(serv: pd.DataFrame) -> pd.DataFrame:
    ativos = _ativos(serv)
    alertas = []

    # 1) Elite > 20k
    for _, r in ativos[ativos["proventos"] > ELITE_THRESHOLD].iterrows():
        alertas.append({
            "tipo": "ELITE_>20k", "matricula": r["matricula"],
            "cargo": r.get("cargo", ""), "unidade": r.get("nome_unidade", ""),
            "categoria_vinculo": r.get("categoria_vinculo", ""),
            "proventos": round(float(r["proventos"]), 2),
            "detalhe": f"Proventos R$ {r['proventos']:,.2f} acima do teto de referência de R$ {ELITE_THRESHOLD:,.0f}",
        })

    # 2) Desconto > 50% dos proventos
    m = (ativos["proventos"] > 0) & (ativos["descontos"] / ativos["proventos"] > DESCONTO_ALTO_PCT)
    for _, r in ativos[m].iterrows():
        ratio = r["descontos"] / r["proventos"]
        alertas.append({
            "tipo": "DESCONTO_>50%", "matricula": r["matricula"],
            "cargo": r.get("cargo", ""), "unidade": r.get("nome_unidade", ""),
            "categoria_vinculo": r.get("categoria_vinculo", ""),
            "proventos": round(float(r["proventos"]), 2),
            "detalhe": f"Descontos consomem {ratio*100:.1f}% dos proventos",
        })

    # 3) Outliers por cargo (IQR, apenas cargos com >= 8 servidores)
    for cargo, sub in ativos.groupby("cargo"):
        if len(sub) < 8:
            continue
        q1, q3 = sub["proventos"].quantile([0.25, 0.75])
        iqr = q3 - q1
        if iqr <= 0:
            continue
        sup = q3 + 1.5 * iqr
        for _, r in sub[sub["proventos"] > sup].iterrows():
            if r["proventos"] > ELITE_THRESHOLD:
                continue  # já listado como elite
            alertas.append({
                "tipo": "OUTLIER_CARGO", "matricula": r["matricula"],
                "cargo": cargo, "unidade": r.get("nome_unidade", ""),
                "categoria_vinculo": r.get("categoria_vinculo", ""),
                "proventos": round(float(r["proventos"]), 2),
                "detalhe": f"Proventos {r['proventos']/sub['proventos'].median():.1f}× a mediana do cargo (R$ {sub['proventos'].median():,.0f})",
            })

    df = pd.DataFrame(alertas)
    if not df.empty:
        df = df.sort_values(["tipo", "proventos"], ascending=[True, False]).reset_index(drop=True)
    return df


def _eh_provento(codigo: str) -> bool:
    c = str(codigo).strip()
    if c.upper().startswith("R"):
        return False
    return c not in DESCONTOS_NUMERICOS


def gerar_rubricas_top(long: pd.DataFrame, top: int = 25) -> tuple[pd.DataFrame, dict]:
    """Concentração de rubricas de PROVENTO (composição da remuneração bruta)."""
    prov = long[long["codigo"].map(_eh_provento)].copy()
    prov = prov[prov["valor"].fillna(0) > 0]
    g = (prov.groupby(["codigo", "descricao_rubrica"])
         .agg(valor_total=("valor", "sum"),
              n_servidores=("matricula", "nunique"),
              n_pagamentos=("valor", "size"),
              valor_medio=("valor", "mean"))
         .reset_index().sort_values("valor_total", ascending=False))
    total = g["valor_total"].sum()
    g["pct_folha"] = (g["valor_total"] / total * 100).round(2) if total else 0.0
    g["pct_acum"] = g["pct_folha"].cumsum().round(2)
    for c in ("valor_total", "valor_medio"):
        g[c] = g[c].round(2)

    pareto = {
        "valor_total_proventos": round(float(total), 2),
        "n_rubricas": int(len(g)),
        "top5_pct": round(float(g.head(5)["pct_folha"].sum()), 2),
        "top10_pct": round(float(g.head(10)["pct_folha"].sum()), 2),
        "top20_pct": round(float(g.head(20)["pct_folha"].sum()), 2),
    }
    return g.head(top).reset_index(drop=True), pareto


# ---------------------------------------------------------------------------
# Orquestração
# ---------------------------------------------------------------------------
def gerar_tudo(data_dir: Path, out_dir: Path) -> dict:
    data_dir = Path(data_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    long = load_long(data_dir)
    serv = servidores_frame(long)

    kpis = gerar_kpis(serv)
    por_vinculo = gerar_por_vinculo(serv, data_dir)
    faixas = gerar_faixas(serv)
    top_unidades = gerar_top_unidades(serv, data_dir)
    top_cargos = gerar_top_cargos(serv, data_dir)
    alertas = gerar_alertas(serv)
    rubricas_top, pareto = gerar_rubricas_top(long)

    # Validação de reconciliação (proventos rubricas vs total servidor)
    prov_rubricas = long[long["codigo"].map(_eh_provento)]["valor"].fillna(0).sum()
    prov_serv = _ativos(serv)["proventos"].fillna(0).sum()
    reconc = {
        "proventos_rubricas": round(float(prov_rubricas), 2),
        "proventos_servidores_ativos": round(float(prov_serv), 2),
        "divergencia_pct": round(abs(prov_rubricas - prov_serv) / prov_serv * 100, 2) if prov_serv else None,
    }

    # Persistir
    (out_dir / "kpis_folha.json").write_text(json.dumps(kpis, ensure_ascii=False, indent=2), encoding="utf-8")
    por_vinculo.to_csv(out_dir / "por_vinculo.csv", index=False, encoding="utf-8")
    faixas.to_csv(out_dir / "distribuicao_faixas.csv", index=False, encoding="utf-8")
    top_unidades.to_csv(out_dir / "top_unidades.csv", index=False, encoding="utf-8")
    top_cargos.to_csv(out_dir / "top_cargos.csv", index=False, encoding="utf-8")
    alertas.to_csv(out_dir / "alertas_folha.csv", index=False, encoding="utf-8")
    rubricas_top.to_csv(out_dir / "rubricas_top.csv", index=False, encoding="utf-8")
    (out_dir / "rubricas_pareto.json").write_text(json.dumps(pareto, ensure_ascii=False, indent=2), encoding="utf-8")

    dados = {
        "kpis": kpis,
        "por_vinculo": por_vinculo.to_dict("records"),
        "faixas": faixas.to_dict("records"),
        "top_unidades": top_unidades.to_dict("records"),
        "top_cargos": top_cargos.to_dict("records"),
        "alertas": alertas.to_dict("records"),
        "rubricas_top": rubricas_top.to_dict("records"),
        "rubricas_pareto": pareto,
        "reconciliacao": reconc,
    }
    (out_dir / "dados_consolidados.json").write_text(
        json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    return dados


if __name__ == "__main__":
    import sys
    base = Path(__file__).resolve().parent.parent
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else base / "data"
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else base / "analysis" / "tabelas"
    d = gerar_tudo(data_dir, out_dir)
    k = d["kpis"]
    print(f"OK — {k['n_ativos']} ativos | bruto R$ {k['proventos_total']:,.2f} | "
          f"Gini {k['gini_proventos']} | elite>20k {k['elite_acima_20k']['n']} | "
          f"alertas {len(d['alertas'])} | rubricas top {len(d['rubricas_top'])}")
    print(f"Reconciliação rubricas vs servidores: {d['reconciliacao']}")
