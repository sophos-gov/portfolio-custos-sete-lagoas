#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "=== [1/5] Extração dos dados 2025 ==="
py -3 extract_data.py

echo ""
echo "=== [2/5] Classificação de empenhos ==="
py -3 classify_empenhos.py

echo ""
echo "=== [3/5] Geração de tabelas analíticas ==="
py -3 generate_tables.py

echo ""
echo "=== [4/5] Relatório HTML — Saúde ==="
py -3 build_html_saude.py

echo ""
echo "=== [5/5] Relatório HTML — Educação ==="
py -3 build_html_educacao.py

echo ""
echo "✅ CONCLUÍDO. Relatórios gerados:"
echo "   → relatorio_custos_saude_2025.html"
echo "   → relatorio_custos_educacao_2025.html"
