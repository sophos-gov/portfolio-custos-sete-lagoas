#!/usr/bin/env python3
"""
classify_empenhos.py — Task 2
Classifica empenhos em 14 categorias de custo usando regras determinísticas + API Claude (fallback).
"""
import os, sys, json, time, logging
import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
SCRIPT_DIR  = Path(__file__).resolve().parent
TABELAS_DIR = SCRIPT_DIR / "tabelas"
SAUDE_DIR   = TABELAS_DIR / "saude"
EDUC_DIR    = TABELAS_DIR / "educacao"
CACHE_PATH  = TABELAS_DIR / "classificacao_cache.csv"
LOG_PATH    = TABELAS_DIR / "classificacao_erros.log"

logging.basicConfig(
    filename=str(LOG_PATH),
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s %(message)s",
)

# ---------------------------------------------------------------------------
# 14 Categorias
# ---------------------------------------------------------------------------
CATEGORIAS = {
    1:  "Pessoal",
    2:  "Medicamentos",
    3:  "Material hospitalar",
    4:  "Alimentação",
    5:  "Limpeza",
    6:  "Manutenção",
    7:  "Transporte",
    8:  "TI",
    9:  "Serviços terceirizados",
    10: "Material expediente/pedagógico",
    11: "Investimentos",
    12: "Previdência",
    13: "Transferências",
    14: "Outros",
}

# ---------------------------------------------------------------------------
# Regras determinísticas (design.md §3.1)
# ---------------------------------------------------------------------------
REGRAS_NATUREZA = {
    "3.1.90.11": 1,   # Vencimentos e salários → Pessoal
    "3.1.90.04": 1,
    "3.1.90.13": 1,
    "3.1.90.16": 1,
    "3.1.91.13": 1,
    "3.1.90.01": 1,
    "3.1.90.03": 1,
    "3.1.90.94": 12,  # Previdência
    "3.3.90.30.09": 2,  # Medicamentos
    "3.3.90.30.17": 3,  # Material farmacológico → Material hospitalar
    "3.3.90.30.35": 3,  # Material hospitalar
    "3.3.90.30.07": 4,  # Alimentação
    "3.3.90.30.22": 5,  # Limpeza
    "3.3.90.30.25": 6,  # Manutenção bens móveis
    "3.3.90.30.37": 6,  # Manutenção veículos
    "3.3.90.30.16": 10, # Material expediente/pedagógico
    "3.3.90.36": 9,   # Serviços PF → terceirizados
    "3.3.90.39": 9,   # Serviços PJ
    "3.3.90.37": 7,   # Locação meios de transporte
    "3.3.90.40": 8,   # TI
    "4.4.90.51": 11,  # Obras → Investimentos
    "4.4.90.52": 11,  # Equipamentos permanentes
    "3.3.50":    13,  # Transferências instituições privadas
    "3.3.90.48": 13,  # Auxílios financeiros PF
    "3.2.90.49": 13,  # Auxílios PJ
    # Prefixos mais genéricos (menor prioridade)
    "3.1":       1,   # Pessoal e encargos
    "4.4":       11,  # Investimentos
    "3.3.50":    13,
}

REGRAS_ACAO = {
    "2551": 1,   # Remuneração servidores ativos
    "2550": 1,   # Agentes políticos
    "2552": 12,  # Proventos inativos
    "2718": 12,  # Pensões e aposentadoria
    "2653": 7,   # Transporte escolar
    "2647": 4,   # Alimentação/nutrição
    "2607": 2,   # Assistência farmacêutica → Medicamentos
    "2637": 8,   # Gestão TI
}

# Regras extras por palavras-chave no dsc_empenho
PALAVRAS_CHAVE = [
    # (lista de palavras, categoria)
    (["salário", "salario", "folha", "vencimento", "remuneração", "remuneracao",
      "gratificação", "gratificacao", "13°", "decimo", "ferias", "férias",
      "adicional", "inss", "encargo"], 1),
    (["medicamento", "farmácia", "farmacia", "remédio", "remedio",
      "comprimido", "vacina", "insulina", "antibiótico"], 2),
    (["material hospitalar", "hospital", "cirúrgico", "cirurgico",
      "epi", "luva", "seringa", "equipamento médico", "catéter"], 3),
    (["alimentação", "alimentacao", "merenda", "refeição", "refeicao",
      "generos alimentícios", "generos alimenticios", "marmita"], 4),
    (["limpeza", "higiene", "conservação", "conservacao", "desinfeção",
      "desinfecao", "saneamento"], 5),
    (["manutenção", "manutencao", "reparo", "conserto", "reforma"], 6),
    (["transporte", "veículo", "veiculo", "ônibus", "onibus", "ambulância",
      "ambulancia", "combustível", "combustivel", "frota"], 7),
    (["software", "sistema", "tecnologia", "informática", "informatica",
      "licença", "licenca", "ti ", "suporte técnico", "internet"], 8),
    (["assessoria", "consultoria", "terceirizado", "terceirizado",
      "prestação de serviço", "prestacao de servico", "outsourcing"], 9),
    (["material pedagógico", "material pedagogico", "didático", "didatico",
      "expediente", "papel", "caneta", "livro", "apostila"], 10),
    (["obra", "construção", "construcao", "ampliação", "ampliacao",
      "bem permanente", "aquisição de imóvel", "aquisicao de imovel"], 11),
    (["previdência", "previdencia", "aposentadoria", "pensão", "pensao",
      "inativo", "inativa"], 12),
    (["transferência", "transferencia", "subvenção", "subvencao",
      "convênio", "convenio", "auxílio", "auxilio"], 13),
]


def classificar_por_regras(row) -> int | None:
    natureza = str(row.get("dsc_naturezadespesa") or "").strip()
    acao_raw = str(row.get("dsc_acao") or "").strip()
    # Pegar só os 4 primeiros dígitos numéricos da ação
    acao = "".join(filter(str.isdigit, acao_raw))[:4]

    # Natureza: match do mais específico ao menos
    for prefixo in sorted(REGRAS_NATUREZA, key=len, reverse=True):
        if natureza.startswith(prefixo):
            return REGRAS_NATUREZA[prefixo]

    # Ação
    if acao in REGRAS_ACAO:
        return REGRAS_ACAO[acao]

    # Palavras-chave no dsc_empenho
    desc = str(row.get("dsc_empenho") or "").lower()
    for palavras, cat in PALAVRAS_CHAVE:
        if any(p in desc for p in palavras):
            return cat

    return None  # ambíguo → API


# ---------------------------------------------------------------------------
# API Claude
# ---------------------------------------------------------------------------
PROMPT_TEMPLATE = """Você é um classificador de empenhos públicos municipais brasileiros.

Classifique cada empenho abaixo em UMA das categorias:
1. Pessoal  2. Medicamentos  3. Material hospitalar  4. Alimentação
5. Limpeza  6. Manutenção  7. Transporte  8. TI  9. Serviços terceirizados
10. Material expediente/pedagógico  11. Investimentos  12. Previdência
13. Transferências  14. Outros

Use dsc_empenho, dsc_naturezadespesa e dsc_acao como contexto.
Responda APENAS com JSON: [{{"seq_empenho": "X", "categoria": N}}, ...]

Empenhos:
{batch_json}"""


def classificar_lote_api(client, batch_df: pd.DataFrame, max_retries: int = 3) -> list:
    items = batch_df[["seq_empenho", "dsc_empenho", "dsc_naturezadespesa", "dsc_acao"]].to_dict("records")
    # Garantir que seq_empenho é string
    for item in items:
        item["seq_empenho"] = str(item["seq_empenho"])

    prompt = PROMPT_TEMPLATE.format(batch_json=json.dumps(items, ensure_ascii=False))

    for tentativa in range(max_retries):
        try:
            resp = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                temperature=0,
                messages=[{"role": "user", "content": prompt}],
            )
            texto = resp.content[0].text.strip()
            # Remover possíveis markdown code fences
            if texto.startswith("```"):
                texto = texto.split("```")[1]
                if texto.startswith("json"):
                    texto = texto[4:]
            resultado = json.loads(texto)
            return resultado
        except Exception as e:
            logging.warning(f"Tentativa {tentativa+1} falhou: {e}")
            if tentativa < max_retries - 1:
                time.sleep(2 ** tentativa)

    # Fallback: todos como Outros (14)
    logging.warning(f"Lote de {len(items)} empenhos classificado como 'Outros' após {max_retries} tentativas")
    return [{"seq_empenho": str(r["seq_empenho"]), "categoria": 14} for r in items]


def classificar_com_cache(client, empenhos_df: pd.DataFrame) -> pd.DataFrame:
    """Classifica empenhos ambíguos via API, usando cache incremental."""
    # Carregar cache
    if CACHE_PATH.exists():
        cache = pd.read_csv(CACHE_PATH, dtype={"seq_empenho": str})
        ja_feitos = set(cache["seq_empenho"].astype(str))
    else:
        cache = pd.DataFrame(columns=["seq_empenho", "categoria", "origem"])
        ja_feitos = set()

    empenhos_df["seq_empenho"] = empenhos_df["seq_empenho"].astype(str)
    pendentes = empenhos_df[~empenhos_df["seq_empenho"].isin(ja_feitos)]

    print(f"  Cache: {len(ja_feitos)} já classificados, {len(pendentes)} pendentes para API")

    if len(pendentes) == 0:
        return cache

    novos = []
    total_lotes = (len(pendentes) + 49) // 50
    for i, start in enumerate(range(0, len(pendentes), 50)):
        batch = pendentes.iloc[start:start + 50]
        print(f"  Lote {i+1}/{total_lotes} ({len(batch)} empenhos)…")
        resultado = classificar_lote_api(client, batch)
        for r in resultado:
            novos.append({
                "seq_empenho": str(r.get("seq_empenho", "")),
                "categoria": int(r.get("categoria", 14)),
                "origem": "api",
            })

    if novos:
        cache = pd.concat([cache, pd.DataFrame(novos)], ignore_index=True)
        cache.to_csv(CACHE_PATH, index=False)
        print(f"  Cache atualizado: {len(cache)} classificações salvas")

    return cache


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("TASK 2 — Classificação de Empenhos")
    print("=" * 60)

    # Verificar API key
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    usar_api = bool(api_key)
    client = None

    if usar_api:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            print("[OK] ANTHROPIC_API_KEY disponível — usando API Claude para ambíguos")
        except ImportError:
            usar_api = False
            print("[AVISO] anthropic não instalado — usando apenas regras")
    else:
        print("[AVISO] ANTHROPIC_API_KEY não definida — usando apenas regras determinísticas")

    # Carregar empenhos de ambas as secretarias
    dfs = []
    for nome, dir_ in [("saude", SAUDE_DIR), ("educacao", EDUC_DIR)]:
        parquet = dir_ / "empenho_2025.parquet"
        if not parquet.exists():
            print(f"[ERRO] {parquet} não encontrado — execute extract_data.py primeiro")
            sys.exit(1)
        df = pd.read_parquet(parquet)
        df["secretaria"] = nome
        dfs.append(df)
        print(f"  {nome}: {len(df)} empenhos carregados")

    df_all = pd.concat(dfs, ignore_index=True)
    print(f"\n  Total: {len(df_all)} empenhos")

    # ---------------------------------------------------------------------------
    # Camada 1 — Regras determinísticas
    # ---------------------------------------------------------------------------
    print("\n=== Camada 1: Regras determinísticas ===")
    df_all["categoria_custo"] = df_all.apply(classificar_por_regras, axis=1)
    classificados = df_all["categoria_custo"].notna()
    n_regra = classificados.sum()
    n_total = len(df_all)
    print(f"  Classificados por regra: {n_regra}/{n_total} ({n_regra/n_total*100:.1f}%)")

    ambiguos = df_all[~classificados].copy()
    print(f"  Ambíguos para API: {len(ambiguos)}")

    # ---------------------------------------------------------------------------
    # Camada 2 — Cache + API Claude
    # ---------------------------------------------------------------------------
    if len(ambiguos) > 0:
        df_all["seq_empenho"] = df_all["seq_empenho"].astype(str)

        # Sempre carregar cache (independente da API)
        if CACHE_PATH.exists():
            cache_df = pd.read_csv(CACHE_PATH, dtype={"seq_empenho": str})
            cache_df["seq_empenho"] = cache_df["seq_empenho"].astype(str)
            cat_map = dict(zip(cache_df["seq_empenho"], cache_df["categoria"]))
            mask = ~classificados
            df_all.loc[mask, "categoria_custo"] = df_all.loc[mask, "seq_empenho"].map(cat_map)
            n_cache = (~classificados & df_all["categoria_custo"].notna()).sum()
            print(f"\n[INFO] Cache aplicado: {n_cache} empenhos classificados do cache")
            # Reclacular ambíguos restantes
            ambiguos = df_all[df_all["categoria_custo"].isna()].copy()
            print(f"  Ainda ambíguos após cache: {len(ambiguos)}")

        if len(ambiguos) > 0:
            if usar_api and client:
                print("\n=== Camada 2: API Claude (apenas empenhos sem cache) ===")
                cols_needed = ["seq_empenho", "dsc_empenho", "dsc_naturezadespesa", "dsc_acao"]
                cols_ok = [c for c in cols_needed if c in ambiguos.columns]
                cache_df2 = classificar_com_cache(client, ambiguos[cols_ok].copy())
                cache_df2["seq_empenho"] = cache_df2["seq_empenho"].astype(str)
                cat_map2 = dict(zip(cache_df2["seq_empenho"], cache_df2["categoria"]))
                mask2 = df_all["categoria_custo"].isna()
                df_all.loc[mask2, "categoria_custo"] = df_all.loc[mask2, "seq_empenho"].map(cat_map2)
            else:
                print(f"\n[INFO] Sem API — {len(ambiguos)} empenhos restantes classificados como 'Outros' (14)")
                df_all.loc[df_all["categoria_custo"].isna(), "categoria_custo"] = 14

    # Garantir 100% classificados (fallback final)
    ainda_nulos = df_all["categoria_custo"].isna()
    if ainda_nulos.any():
        df_all.loc[ainda_nulos, "categoria_custo"] = 14
        print(f"  [FALLBACK] {ainda_nulos.sum()} empenhos classificados como 'Outros'")

    df_all["categoria_custo"] = df_all["categoria_custo"].astype(int)
    df_all["categoria_nome"] = df_all["categoria_custo"].map(CATEGORIAS)

    # ---------------------------------------------------------------------------
    # Salvar por secretaria
    # ---------------------------------------------------------------------------
    print("\n=== Salvando empenho_classificado.parquet ===")
    for nome, dir_ in [("saude", SAUDE_DIR), ("educacao", EDUC_DIR)]:
        subset = df_all[df_all["secretaria"] == nome].copy()
        path = dir_ / "empenho_classificado.parquet"
        subset.to_parquet(path, index=False)
        print(f"  {nome}: {len(subset)} empenhos salvos -> {path.name}")

    # ---------------------------------------------------------------------------
    # Distribuição final
    # ---------------------------------------------------------------------------
    print("\n=== Distribuição por Categoria × Secretaria ===")
    pivot = df_all.groupby(["secretaria", "categoria_nome"])["vlr_empenhado"].sum().unstack(fill_value=0)
    for sec in ["saude", "educacao"]:
        if sec in df_all["secretaria"].values:
            sub = df_all[df_all["secretaria"] == sec]
            total = sub["vlr_empenhado"].sum()
            dist = sub.groupby("categoria_nome")["vlr_empenhado"].sum().sort_values(ascending=False)
            print(f"\n  {sec.upper()} (total empenhado: R$ {total:,.0f})")
            for cat, val in dist.items():
                print(f"    {cat:<35} R$ {val:>14,.0f}  ({val/total*100:5.1f}%)")

    print("\n[CONCLUÍDO] Task 2 — classify_empenhos.py")


if __name__ == "__main__":
    main()
