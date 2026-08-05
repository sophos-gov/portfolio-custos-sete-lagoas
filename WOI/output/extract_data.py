#!/usr/bin/env python3
"""
extract_data.py — Task 1
Descompacta ZIPs do SICOM 2025, lê CSVs (latin-1, sep=;), filtra por secretaria e salva Parquets.
"""
import os, sys, zipfile, glob
import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
SCRIPT_DIR   = Path(__file__).resolve().parent
OUTPUT_DIR   = SCRIPT_DIR
TABELAS_DIR  = OUTPUT_DIR / "tabelas"
SAUDE_DIR    = TABELAS_DIR / "saude"
EDUC_DIR     = TABELAS_DIR / "educacao"
ZIPS_DIR     = SCRIPT_DIR.parent.parent / "2025"   # custos/2025/
TMP_DIR      = Path(os.environ.get("TEMP", "/tmp")) / "sicom_2025"
EDUC_XLSX    = SCRIPT_DIR.parent / "educ-10-2025.xlsx"

# ZIPs esperados
ZIP_FILES = {
    "despesa":     "SICOM.2025.3167202.despesa (2).zip",
    "empenho":     "SICOM.2025.3167202.empenho (2).zip",
    "desp_pessoal":"SICOM.2025.3167202.desp_pessoal.zip",
    "contrato":    "SICOM.2025.3167202.contrato.zip",
}

# Filtros de unidade
UNIDADES_SAUDE = {"13001"}
UNIDADES_EDUC  = {"11001", "22001"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def parse_valor_br(s) -> float:
    """'1.234.567,89' → 1234567.89"""
    if pd.isna(s):
        return 0.0
    s = str(s).strip()
    if s in ("", "-", "0", "0,00", "0.00"):
        return 0.0
    try:
        return float(s.replace(".", "").replace(",", "."))
    except ValueError:
        return 0.0


def ler_csv_sicom(path: Path, chunksize: int = None) -> pd.DataFrame:
    kwargs = dict(
        sep=";",
        encoding="utf-8",
        encoding_errors="replace",
        low_memory=False,
    )
    if chunksize:
        chunks = pd.read_csv(path, chunksize=chunksize, **kwargs)
        return pd.concat(chunks, ignore_index=True)
    return pd.read_csv(path, **kwargs)


def normalizar_df(df: pd.DataFrame) -> pd.DataFrame:
    # Normalizar cod_unidade → string sem espaços
    if "cod_unidade" in df.columns:
        df["cod_unidade"] = df["cod_unidade"].astype(str).str.strip()

    # Normalizar num_mesexercicio → int
    for col in ("num_mesexercicio", "num_mes_referencia"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Converter campos vlr_* → float
    vlr_cols = [c for c in df.columns if c.startswith("vlr_")]
    for col in vlr_cols:
        if df[col].dtype == object:
            df[col] = df[col].apply(parse_valor_br)
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    return df


def filtrar_unidade(df: pd.DataFrame, unidades: set) -> pd.DataFrame:
    if "cod_unidade" not in df.columns:
        return df
    return df[df["cod_unidade"].isin(unidades)].copy()


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
def criar_estrutura():
    for d in (TABELAS_DIR, SAUDE_DIR, EDUC_DIR, TMP_DIR):
        d.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Estrutura de diretórios em {TABELAS_DIR}")


# ---------------------------------------------------------------------------
# Descompactar ZIPs
# ---------------------------------------------------------------------------
def descompactar_zips():
    print("\n=== Descompactando ZIPs ===")
    for nome, arquivo in ZIP_FILES.items():
        zip_path = ZIPS_DIR / arquivo
        if not zip_path.exists():
            print(f"  [AVISO] ZIP não encontrado: {zip_path}")
            continue
        print(f"  Extraindo: {arquivo}")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(TMP_DIR)
    print(f"[OK] Arquivos extraídos em {TMP_DIR}")

    # Listar CSVs extraídos
    csvs = list(TMP_DIR.rglob("*.csv"))
    print(f"  {len(csvs)} arquivos CSV encontrados:")
    for c in csvs:
        print(f"    {c.name} ({c.stat().st_size / 1e6:.1f} MB)")
    return {c.name: c for c in csvs}


def encontrar_csv(csv_map: dict, patterns: list) -> Path | None:
    for pat in patterns:
        for name, path in csv_map.items():
            if pat.lower() in name.lower():
                return path
    return None


# ---------------------------------------------------------------------------
# Ler CSVs principais
# ---------------------------------------------------------------------------
def ler_todos_csvs(csv_map: dict) -> dict:
    print("\n=== Lendo CSVs ===")
    dfs = {}

    # despesa.despesa
    p = encontrar_csv(csv_map, ["despesa.despesa", "despesa.despesa"])
    if p:
        print(f"  Lendo despesa.despesa ({p.stat().st_size/1e6:.1f} MB)…")
        df = ler_csv_sicom(p)
        df = normalizar_df(df)
        print(f"    Shape: {df.shape} | Colunas: {list(df.columns)}")
        dfs["despesa"] = df
    else:
        print("  [ERRO] despesa.despesa.csv não encontrado")

    # empenho.empenho
    p = encontrar_csv(csv_map, ["empenho.empenho"])
    if p:
        print(f"  Lendo empenho.empenho ({p.stat().st_size/1e6:.1f} MB)…")
        df = ler_csv_sicom(p)
        df = normalizar_df(df)
        print(f"    Shape: {df.shape}")
        dfs["empenho"] = df
    else:
        print("  [ERRO] empenho.empenho.csv não encontrado")

    # despesa.pagamento (28 MB — usar chunks)
    p = encontrar_csv(csv_map, ["despesa.pagamento", "pagamento"])
    if p:
        print(f"  Lendo pagamento ({p.stat().st_size/1e6:.1f} MB) em chunks…")
        df = ler_csv_sicom(p, chunksize=50_000)
        df = normalizar_df(df)
        print(f"    Shape: {df.shape}")
        dfs["pagamento"] = df
    else:
        print("  [ERRO] despesa.pagamento.csv não encontrado")

    # empenho.credorEmpenho
    p = encontrar_csv(csv_map, ["credorEmpenho", "credor"])
    if p:
        print(f"  Lendo credorEmpenho ({p.stat().st_size/1e6:.1f} MB)…")
        df = ler_csv_sicom(p)
        df = normalizar_df(df)
        print(f"    Shape: {df.shape}")
        dfs["credorEmpenho"] = df
    else:
        print("  [AVISO] credorEmpenho.csv não encontrado")

    return dfs


# ---------------------------------------------------------------------------
# Filtrar por secretaria
# ---------------------------------------------------------------------------
def filtrar_secretaria(dfs: dict, unidades: set, nome: str) -> dict:
    print(f"\n=== Filtrando dados para {nome.upper()} (unidades: {unidades}) ===")
    filtrados = {}
    for tabela, df in dfs.items():
        if "cod_unidade" in df.columns:
            filt = filtrar_unidade(df, unidades)
        else:
            # pagamento não tem cod_unidade diretamente — filtrar por seq_empenho se possível
            filt = df.copy()
        filtrados[tabela] = filt
        print(f"  {tabela}: {len(df)} -> {len(filt)} linhas")
    return filtrados


def filtrar_pagamento_por_empenho(pagamento_df: pd.DataFrame, empenho_df: pd.DataFrame) -> pd.DataFrame:
    """Filtra pagamentos pelos seq_empenho que pertencem à secretaria."""
    if "seq_empenho" not in pagamento_df.columns or "seq_empenho" not in empenho_df.columns:
        return pagamento_df
    empenhos_validos = set(empenho_df["seq_empenho"].astype(str))
    pag = pagamento_df.copy()
    pag["seq_empenho"] = pag["seq_empenho"].astype(str)
    filtrado = pag[pag["seq_empenho"].isin(empenhos_validos)].copy()
    return filtrado


# ---------------------------------------------------------------------------
# Salvar Parquets
# ---------------------------------------------------------------------------
def salvar_parquets(filtrados: dict, out_dir: Path):
    mapa = {
        "despesa":       "despesa_2025.parquet",
        "empenho":       "empenho_2025.parquet",
        "pagamento":     "pagamento_2025.parquet",
        "credorEmpenho": "credorEmpenho_2025.parquet",
    }
    for tabela, nome_arquivo in mapa.items():
        if tabela not in filtrados:
            continue
        df = filtrados[tabela]
        if df.empty:
            print(f"  [AVISO] {tabela} está vazio — parquet não salvo")
            continue
        path = out_dir / nome_arquivo
        df.to_parquet(path, index=False)
        print(f"  Salvo: {path.name} ({len(df)} linhas, {path.stat().st_size/1e3:.0f} KB)")


# ---------------------------------------------------------------------------
# Log de extração
# ---------------------------------------------------------------------------
def gerar_log(saude: dict, educ: dict):
    MESES = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
             7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}
    linhas = ["=== Extraction Log — SICOM 2025 — Sete Lagoas (3167202) ===\n"]

    for nome, dados in [("SAUDE", saude), ("EDUCACAO", educ)]:
        linhas.append(f"\n--- {nome} ---")
        for tabela, df in dados.items():
            linhas.append(f"  {tabela}: {len(df)} linhas")
            if "num_mesexercicio" in df.columns and not df.empty:
                meses = sorted(df["num_mesexercicio"].unique())
                nomes = [MESES.get(m, str(m)) for m in meses if m > 0]
                linhas.append(f"    Meses: {', '.join(nomes)} ({len(nomes)} meses)")
            if "dsc_programa" in df.columns and not df.empty:
                progs = sorted(df["dsc_programa"].unique())
                linhas.append(f"    Programas: {len(progs)}")
                for p in progs:
                    linhas.append(f"      - {p}")

    log_path = TABELAS_DIR / "extraction_log.txt"
    log_path.write_text("\n".join(linhas), encoding="utf-8")
    print(f"\n[OK] Log salvo: {log_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("TASK 1 — Extração de Dados SICOM 2025")
    print("=" * 60)

    criar_estrutura()
    csv_map = {}

    # Verificar se já extraídos
    csvs_existentes = list(TMP_DIR.rglob("*.csv"))
    if csvs_existentes:
        print(f"\n[INFO] {len(csvs_existentes)} CSVs já extraídos em {TMP_DIR}")
        csv_map = {c.name: c for c in csvs_existentes}
    else:
        csv_map = descompactar_zips()

    # Ler CSVs
    dfs = ler_todos_csvs(csv_map)

    if not dfs:
        print("[ERRO] Nenhum CSV lido. Abortando.")
        sys.exit(1)

    # -----------------------------------------------------------------------
    # SAÚDE
    # -----------------------------------------------------------------------
    print("\n" + "=" * 40)
    saude_raw = filtrar_secretaria(dfs, UNIDADES_SAUDE, "Saúde")

    # Pagamento: filtrar pelos empenhos da Saúde
    if "pagamento" in dfs and "empenho" in saude_raw:
        pag_saude = filtrar_pagamento_por_empenho(dfs["pagamento"], saude_raw["empenho"])
        saude_raw["pagamento"] = pag_saude
        print(f"  pagamento (via empenho): {len(pag_saude)} linhas")

    # credorEmpenho: filtrar pelos empenhos da Saúde
    if "credorEmpenho" in dfs and "empenho" in saude_raw:
        emps = set(saude_raw["empenho"]["seq_empenho"].astype(str))
        cred = dfs["credorEmpenho"].copy()
        cred["seq_empenho"] = cred["seq_empenho"].astype(str)
        saude_raw["credorEmpenho"] = cred[cred["seq_empenho"].isin(emps)]

    print(f"\n[SAÚDE] Salvando Parquets…")
    salvar_parquets(saude_raw, SAUDE_DIR)

    # -----------------------------------------------------------------------
    # EDUCAÇÃO
    # -----------------------------------------------------------------------
    print("\n" + "=" * 40)
    educ_raw = filtrar_secretaria(dfs, UNIDADES_EDUC, "Educação")

    # Pagamento: filtrar pelos empenhos da Educação
    if "pagamento" in dfs and "empenho" in educ_raw:
        pag_educ = filtrar_pagamento_por_empenho(dfs["pagamento"], educ_raw["empenho"])
        educ_raw["pagamento"] = pag_educ
        print(f"  pagamento (via empenho): {len(pag_educ)} linhas")

    # credorEmpenho: filtrar pelos empenhos da Educação
    if "credorEmpenho" in dfs and "empenho" in educ_raw:
        emps = set(educ_raw["empenho"]["seq_empenho"].astype(str))
        cred = dfs["credorEmpenho"].copy()
        cred["seq_empenho"] = cred["seq_empenho"].astype(str)
        educ_raw["credorEmpenho"] = cred[cred["seq_empenho"].isin(emps)]

    print(f"\n[EDUCAÇÃO] Salvando Parquets…")
    salvar_parquets(educ_raw, EDUC_DIR)

    # -----------------------------------------------------------------------
    # Log
    # -----------------------------------------------------------------------
    gerar_log(saude_raw, educ_raw)

    # Resumo final
    print("\n" + "=" * 60)
    print("RESUMO FINAL")
    print("=" * 60)
    for nome, dados in [("SAÚDE", saude_raw), ("EDUCAÇÃO", educ_raw)]:
        desp = dados.get("despesa", pd.DataFrame())
        print(f"  {nome}: {len(desp)} registros despesa", end="")
        if not desp.empty and "num_mesexercicio" in desp.columns:
            meses = sorted(desp["num_mesexercicio"].unique())
            meses = [m for m in meses if m > 0]
            print(f" | {len(meses)} meses", end="")
        print()

    print("\n[CONCLUÍDO] Task 1 — extract_data.py")


if __name__ == "__main__":
    main()
