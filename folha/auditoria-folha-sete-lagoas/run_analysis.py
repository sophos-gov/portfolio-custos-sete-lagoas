#!/usr/bin/env python3
"""
run_analysis.py — Pipeline DETERMINÍSTICO completo, SEM nenhuma chamada de IA.

Gera todas as tabelas + o dashboard HTML. É o caminho de fallback obrigatório:
se o agente noturno falhar ou não houver chaves de API, este script sozinho
produz um relatório válido. Também serve de smoke-test local.

Uso:
    python run_analysis.py
"""
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / "analysis"))

import folha_tables          # noqa: E402
import build_html            # noqa: E402

DATA_DIR = BASE / "data"
TABELAS_DIR = BASE / "analysis" / "tabelas"
OUTPUT_HTML = BASE / "output" / "relatorio_custos_folha_saude_setelagoas.html"


def main() -> int:
    print("==> Gerando tabelas determinísticas...")
    dados = folha_tables.gerar_tudo(DATA_DIR, TABELAS_DIR)
    k = dados["kpis"]
    print(f"    {k['n_ativos']} ativos | bruto R$ {k['proventos_total']:,.2f} | "
          f"Gini {k['gini_proventos']} | elite>20k {k['elite_acima_20k']['n']} | "
          f"alertas {len(dados['alertas'])}")
    print(f"    reconciliação: {dados['reconciliacao']}")

    print("==> Construindo dashboard HTML...")
    html = build_html.build(TABELAS_DIR, OUTPUT_HTML)
    kb = html.stat().st_size / 1024
    print(f"    {html} ({kb:.0f} KB)")

    # Sanidade
    assert 0.2 <= k["gini_proventos"] <= 0.9, "Gini fora da faixa esperada"
    assert k["n_ativos"] > 2000, "Headcount inesperadamente baixo (recorte errado?)"
    assert kb < 2560, "HTML acima do limite de 2,5 MB"
    print("==> OK — pipeline determinístico concluído.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
