#!/usr/bin/env python3
"""
generate_tables.py — Task 3
Gera todas as tabelas analíticas (CSVs e JSONs) para Saúde e Educação.
"""
import sys, json
import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
SCRIPT_DIR  = Path(__file__).resolve().parent
TABELAS_DIR = SCRIPT_DIR / "tabelas"
SAUDE_DIR   = TABELAS_DIR / "saude"
EDUC_DIR    = TABELAS_DIR / "educacao"

MESES_BR = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
            7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}

# ---------------------------------------------------------------------------
# Macro-agrupamento de natureza (design.md §4.2)
# ---------------------------------------------------------------------------
MACRO_NATUREZA = {
    "3.3.90.30.09": "Medicamentos",
    "3.3.90.30.17": "Material Hospitalar",
    "3.3.90.30.35": "Material Hospitalar",
    "3.3.90.30.07": "Alimentação",
    "3.3.90.30.22": "Limpeza e Higiene",
    "3.3.90.30.25": "Manutenção",
    "3.3.90.30.37": "Manutenção",
    "3.3.90.30.16": "Material Expediente",
    "3.3.90.40":    "TI e Serv. Tecnológicos",
    "3.3.90.39":    "Serviços PJ",
    "3.3.90.36":    "Serviços PF",
    "3.3.90.37":    "Locações",
    "3.3.90.48":    "Auxílios e Transferências",
    "3.3.50":       "Transf. Instituições Privadas",
    "4.4.90":       "Investimentos",
    "3.1.90.01":    "Aposentadorias / Pensões",
    "3.1.90.03":    "Aposentadorias / Pensões",
    "3.1":          "Pessoal e Encargos",
    "3.3.90.30":    "Materiais de Consumo",
}


def categorizar_natureza(nat_code: str) -> str:
    nat = str(nat_code).strip()
    for prefixo in sorted(MACRO_NATUREZA, key=len, reverse=True):
        if nat.startswith(prefixo):
            return MACRO_NATUREZA[prefixo]
    return "Outros"


def simplificar_fonte(fonte: str) -> str:
    """Simplifica nomes longos de fonte de recurso."""
    fonte = str(fonte).strip()
    mapa = {
        "1.500.000": "Recursos Próprios",
        "1.540.000": "Recursos Próprios (FUNDEB)",
        "1.660.000": "Transferências SUS",
        "1.661.000": "Transfer. Bloco Básica",
        "1.662.000": "Transfer. Bloco MAC",
        "1.663.000": "Transfer. Bloco Farmácia",
        "1.670.000": "Transfer. Vigilância",
        "6.600.000": "FUNDEB",
        "6.660.000": "FUNDEB 60%",
        "6.661.000": "FUNDEB 40%",
    }
    for codigo, nome in mapa.items():
        if fonte.startswith(codigo):
            return nome
    # Tentativa por palavras-chave
    fl = fonte.lower()
    if "fundeb" in fl:
        return "FUNDEB"
    if "sus" in fl or "saúde" in fl or "bloco" in fl:
        return "Transferências SUS"
    if "próprio" in fl or "proprio" in fl or "municipal" in fl:
        return "Recursos Próprios"
    if "transferência" in fl or "transferencia" in fl:
        return "Transferências Federais"
    # Pegar código numérico no início
    partes = fonte.split(" - ", 1)
    if len(partes) == 2:
        return partes[1][:40]
    return fonte[:40]


# ---------------------------------------------------------------------------
# A1 — Composição por programa
# ---------------------------------------------------------------------------
def composicao_programa(despesa_df: pd.DataFrame) -> pd.DataFrame:
    cols = ["dsc_programa", "vlr_pago", "vlr_empenhado", "vlr_previsto"]
    cols_ok = [c for c in cols if c in despesa_df.columns]
    agg_map = {c: "sum" for c in cols_ok if c != "dsc_programa"}

    t = despesa_df.groupby("dsc_programa").agg(agg_map).reset_index()
    t = t.sort_values("vlr_pago", ascending=False)
    total = t["vlr_pago"].sum()
    t["pct_total"] = (t["vlr_pago"] / total * 100).round(2) if total else 0
    return t


# ---------------------------------------------------------------------------
# A2 — Composição por natureza macro
# ---------------------------------------------------------------------------
def composicao_natureza(despesa_df: pd.DataFrame) -> pd.DataFrame:
    df = despesa_df.copy()
    df["macro_natureza"] = df["dsc_naturezadespesa"].apply(categorizar_natureza)
    t = df.groupby("macro_natureza")["vlr_pago"].sum().reset_index()
    t = t.sort_values("vlr_pago", ascending=False)
    total = t["vlr_pago"].sum()
    t["pct_total"] = (t["vlr_pago"] / total * 100).round(2) if total else 0
    return t


# ---------------------------------------------------------------------------
# A3 — Composição por ação (top 20)
# ---------------------------------------------------------------------------
def composicao_acao(despesa_df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    t = despesa_df.groupby("dsc_acao")["vlr_pago"].sum().reset_index()
    t = t.sort_values("vlr_pago", ascending=False).head(top_n)
    total = despesa_df["vlr_pago"].sum()
    t["pct_total"] = (t["vlr_pago"] / total * 100).round(2) if total else 0
    return t.reset_index(drop=True)


# ---------------------------------------------------------------------------
# A4 + A5 — Ranking de fornecedores + Pareto
# ---------------------------------------------------------------------------
def ranking_fornecedores(pagamento_df: pd.DataFrame, top_n: int = 20) -> tuple:
    df = pagamento_df.copy()

    # Normalizar nom_credor
    if "nom_credor" not in df.columns:
        df["nom_credor"] = "NÃO IDENTIFICADO"
    df["nom_credor"] = df["nom_credor"].fillna("NÃO IDENTIFICADO").str.strip()
    df.loc[df["nom_credor"] == "", "nom_credor"] = "NÃO IDENTIFICADO"

    # Verificar coluna de valor
    if "vlr_pag_fonte" not in df.columns:
        # Tentar outras colunas
        for alt in ("vlr_pago", "vlr_pagamento"):
            if alt in df.columns:
                df["vlr_pag_fonte"] = df[alt]
                break
        else:
            df["vlr_pag_fonte"] = 0.0

    # Garantir colunas de contagem
    for col in ("seq_pagamento", "seq_empenho"):
        if col not in df.columns:
            df[col] = range(len(df))

    r = (
        df.groupby("nom_credor")
        .agg(
            total_pago=("vlr_pag_fonte", "sum"),
            qtd_pagamentos=("seq_pagamento", "count"),
            qtd_empenhos=("seq_empenho", "nunique"),
        )
        .sort_values("total_pago", ascending=False)
        .reset_index()
    )

    total_geral = r["total_pago"].sum()
    r["pct_total"] = (r["total_pago"] / total_geral * 100).round(2) if total_geral else 0
    r["pct_acumulado"] = r["pct_total"].cumsum().round(2)

    # Concentração
    top5  = float(r.head(5)["pct_total"].sum())
    top10 = float(r.head(10)["pct_total"].sum())
    top20 = float(r.head(20)["pct_total"].sum())
    concentracao = {"pct_top5": round(top5, 2), "pct_top10": round(top10, 2), "pct_top20": round(top20, 2)}

    return r.head(top_n), concentracao


# ---------------------------------------------------------------------------
# A6 — Composição por categoria de custo
# ---------------------------------------------------------------------------
def composicao_categorias(empenho_class_df: pd.DataFrame) -> tuple:
    """Retorna (composicao_df, mensal_df)"""
    df = empenho_class_df.copy()
    if "vlr_empenhado" not in df.columns:
        df["vlr_empenhado"] = 0.0

    # Total por categoria
    t = df.groupby("categoria_nome")["vlr_empenhado"].sum().reset_index()
    t = t.sort_values("vlr_empenhado", ascending=False)
    total = t["vlr_empenhado"].sum()
    t["pct_total"] = (t["vlr_empenhado"] / total * 100).round(2) if total else 0

    # Mensal por categoria
    if "num_mesexercicio" in df.columns:
        mensal = df.groupby(["categoria_nome", "num_mesexercicio"])["vlr_empenhado"].sum().reset_index()
        mensal["mes_nome"] = mensal["num_mesexercicio"].map(MESES_BR)
    else:
        mensal = pd.DataFrame(columns=["categoria_nome", "num_mesexercicio", "vlr_empenhado", "mes_nome"])

    return t, mensal


# ---------------------------------------------------------------------------
# A7 — Série mensal
# ---------------------------------------------------------------------------
def serie_mensal(despesa_df: pd.DataFrame) -> pd.DataFrame:
    s = despesa_df.groupby("num_mesexercicio")["vlr_pago"].sum().reset_index()
    s.columns = ["mes", "vlr_pago"]
    s = s[s["mes"] > 0].sort_values("mes")
    s["mes_nome"] = s["mes"].map(MESES_BR)
    media = s["vlr_pago"].mean()
    s["media"] = media
    return s


# ---------------------------------------------------------------------------
# A8 — Fontes de recurso
# ---------------------------------------------------------------------------
def fontes_recurso(despesa_df: pd.DataFrame) -> pd.DataFrame:
    col_fonte = None
    for c in ("dsc_fonterecurso", "dsc_fonte_recurso", "dsc_cod_orcamentario"):
        if c in despesa_df.columns:
            col_fonte = c
            break

    if not col_fonte:
        return pd.DataFrame(columns=["fonte", "vlr_pago", "pct_total"])

    df = despesa_df.copy()
    df["fonte"] = df[col_fonte].apply(simplificar_fonte)
    t = df.groupby("fonte")["vlr_pago"].sum().reset_index()
    t = t.sort_values("vlr_pago", ascending=False)
    total = t["vlr_pago"].sum()
    t["pct_total"] = (t["vlr_pago"] / total * 100).round(2) if total else 0
    return t


# ---------------------------------------------------------------------------
# KPIs JSON (design.md §4.5)
# ---------------------------------------------------------------------------
def gerar_kpis(despesa_df: pd.DataFrame, pagamento_df: pd.DataFrame,
               empenho_df: pd.DataFrame, secretaria: str) -> dict:
    serie = serie_mensal(despesa_df)
    mes_max = int(despesa_df["num_mesexercicio"].max()) if not despesa_df.empty else 0

    # Mês pico e vale
    if not serie.empty:
        idx_pico = serie["vlr_pago"].idxmax()
        idx_vale = serie["vlr_pago"].idxmin()
        mes_pico  = int(serie.loc[idx_pico, "mes"])
        mes_vale  = int(serie.loc[idx_vale, "mes"])
        valor_pico = float(serie.loc[idx_pico, "vlr_pago"])
        valor_vale = float(serie.loc[idx_vale, "vlr_pago"])
        media_mensal = float(serie["vlr_pago"].mean())
    else:
        mes_pico = mes_vale = 1
        valor_pico = valor_vale = media_mensal = 0.0

    meses_lista = ["","Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

    # Programa top
    prog_top = "N/A"
    if not despesa_df.empty and "dsc_programa" in despesa_df.columns:
        prog_totais = despesa_df.groupby("dsc_programa")["vlr_pago"].sum()
        if not prog_totais.empty:
            prog_top = str(prog_totais.idxmax())

    # num_fornecedores
    if not pagamento_df.empty and "nom_credor" in pagamento_df.columns:
        num_forn = int(pagamento_df["nom_credor"].nunique())
    else:
        num_forn = 0

    # num_empenhos
    if not empenho_df.empty and "seq_empenho" in empenho_df.columns:
        num_emp = int(empenho_df["seq_empenho"].nunique())
    else:
        num_emp = 0

    return {
        "secretaria":       secretaria,
        "total_pago":       float(despesa_df["vlr_pago"].sum()),
        "total_empenhado":  float(despesa_df["vlr_empenhado"].sum()),
        "total_previsto":   float(despesa_df.get("vlr_previsto", pd.Series([0])).sum()),
        "num_fornecedores": num_forn,
        "num_empenhos":     num_emp,
        "meses_cobertos":   mes_max,
        "periodo":          f"Jan–{meses_lista[mes_max] if mes_max <= 12 else '?'} 2025",
        "mes_pico":         mes_pico,
        "mes_pico_nome":    MESES_BR.get(mes_pico, ""),
        "valor_pico":       valor_pico,
        "mes_vale":         mes_vale,
        "mes_vale_nome":    MESES_BR.get(mes_vale, ""),
        "valor_vale":       valor_vale,
        "media_mensal":     media_mensal,
        "programa_top":     prog_top,
    }


# ---------------------------------------------------------------------------
# Processar uma secretaria
# ---------------------------------------------------------------------------
def processar_secretaria(nome: str, dir_: Path):
    print(f"\n{'='*50}")
    print(f"Processando: {nome.upper()}")
    print(f"{'='*50}")

    # Carregar Parquets
    despesa_df = pd.read_parquet(dir_ / "despesa_2025.parquet")
    empenho_df = pd.read_parquet(dir_ / "empenho_2025.parquet")

    pag_path = dir_ / "pagamento_2025.parquet"
    pagamento_df = pd.read_parquet(pag_path) if pag_path.exists() else pd.DataFrame()

    class_path = dir_ / "empenho_classificado.parquet"
    empenho_class = pd.read_parquet(class_path) if class_path.exists() else empenho_df.copy()

    print(f"  despesa: {len(despesa_df)} | empenho: {len(empenho_df)} | pagamento: {len(pagamento_df)}")

    # A1 — Programa
    df_prog = composicao_programa(despesa_df)
    df_prog.to_csv(dir_ / "composicao_programa.csv", index=False)
    print(f"  A1 composicao_programa.csv: {len(df_prog)} programas")

    # A2 — Natureza
    df_nat = composicao_natureza(despesa_df)
    df_nat.to_csv(dir_ / "composicao_natureza.csv", index=False)
    print(f"  A2 composicao_natureza.csv: {len(df_nat)} categorias")

    # A3 — Ação
    df_acao = composicao_acao(despesa_df)
    df_acao.to_csv(dir_ / "composicao_acao.csv", index=False)
    print(f"  A3 composicao_acao.csv: {len(df_acao)} ações")

    # A4 + A5 — Fornecedores + Pareto
    if not pagamento_df.empty:
        df_forn, concentracao = ranking_fornecedores(pagamento_df)
    else:
        df_forn = pd.DataFrame(columns=["nom_credor", "total_pago", "pct_total", "pct_acumulado"])
        concentracao = {"pct_top5": 0, "pct_top10": 0, "pct_top20": 0}
    df_forn.to_csv(dir_ / "ranking_fornecedores.csv", index=False)
    (dir_ / "concentracao.json").write_text(json.dumps(concentracao, ensure_ascii=False), encoding="utf-8")
    print(f"  A4 ranking_fornecedores.csv: {len(df_forn)} fornecedores")
    print(f"  A5 concentracao.json: top5={concentracao['pct_top5']:.1f}%")

    # A6 — Categorias
    if "categoria_nome" in empenho_class.columns:
        df_cat, df_cat_mensal = composicao_categorias(empenho_class)
    else:
        df_cat = pd.DataFrame(columns=["categoria_nome", "vlr_empenhado", "pct_total"])
        df_cat_mensal = pd.DataFrame()
    df_cat.to_csv(dir_ / "composicao_categorias.csv", index=False)
    df_cat_mensal.to_csv(dir_ / "composicao_categorias_mensal.csv", index=False)
    print(f"  A6 composicao_categorias.csv: {len(df_cat)} categorias")

    # A7 — Série mensal
    df_serie = serie_mensal(despesa_df)
    df_serie.to_csv(dir_ / "serie_mensal.csv", index=False)
    print(f"  A7 serie_mensal.csv: {len(df_serie)} meses")

    # A8 — Fontes
    df_fontes = fontes_recurso(despesa_df)
    df_fontes.to_csv(dir_ / "fontes_recurso.csv", index=False)
    print(f"  A8 fontes_recurso.csv: {len(df_fontes)} fontes")

    # KPIs
    kpis = gerar_kpis(despesa_df, pagamento_df, empenho_df, nome)
    (dir_ / "kpis.json").write_text(json.dumps(kpis, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  KPIs: total_pago=R$ {kpis['total_pago']:,.0f} | periodo={kpis['periodo']}")

    # Validação: soma programas vs total
    soma_prog = df_prog["vlr_pago"].sum()
    total_desp = despesa_df["vlr_pago"].sum()
    if total_desp > 0:
        delta = abs(soma_prog - total_desp) / total_desp * 100
        status = "OK" if delta < 0.1 else f"DIVERGÊNCIA {delta:.3f}%"
        print(f"  [Validação] soma programas vs total: {status}")

    return kpis


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("TASK 3 — Geração de Tabelas Analíticas")
    print("=" * 60)

    for nome, dir_ in [("saude", SAUDE_DIR), ("educacao", EDUC_DIR)]:
        if not (dir_ / "despesa_2025.parquet").exists():
            print(f"[ERRO] {dir_ / 'despesa_2025.parquet'} não encontrado")
            print("  Execute extract_data.py primeiro")
            sys.exit(1)
        processar_secretaria(nome, dir_)

    print("\n" + "=" * 60)
    print("[CONCLUÍDO] Task 3 — generate_tables.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
