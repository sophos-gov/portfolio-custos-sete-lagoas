#!/usr/bin/env bash
# Executado NA VPS (Hermes). Cria venv, instala deps, configura systemd timer.
set -e
cd "$(dirname "$0")/.."
PROJ_DIR="$(pwd)"
echo "==> Projeto em: $PROJ_DIR"

# 1) venv + dependências
if [ ! -d venv ]; then
  python3.11 -m venv venv 2>/dev/null || python3 -m venv venv
fi
. venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
python -c "import pandas,anthropic,google.generativeai,bs4; print('==> deps OK')"

# 2) .env — garante o arquivo e PREENCHE chaves vazias a partir do Hermes
#    (a .env enviada no deploy já traz GEMINI/DEEPSEEK; ANTHROPIC/TELEGRAM vêm do Hermes)
if [ ! -f .env ]; then
  cat > .env <<'EOF'
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
DEEPSEEK_API_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=8969330678
ROUTER_MODEL=claude-sonnet-4-6
SYNTH_MODEL=claude-opus-4-8
GEMINI_MODEL=gemini-2.5-flash
DEEPSEEK_MODEL=deepseek-chat
AGENT_USD_BUDGET=3.0
AGENT_MAX_ITERATIONS=120
AGENT_MAX_WALL_SECONDS=14400
LAW_SCRAPE_DOMAINS=leismunicipais.com.br,camarasetelagoas.mg.gov.br,setelagoas.mg.leg.br,jusbrasil.com.br
EOF
fi
# preenche apenas as chaves AINDA vazias, herdando do Hermes
if [ -f /root/.hermes/.env ]; then
  for K in ANTHROPIC_API_KEY GEMINI_API_KEY DEEPSEEK_API_KEY TELEGRAM_BOT_TOKEN; do
    CUR=$(grep -E "^$K=" .env | head -1 | cut -d= -f2-)
    if [ -z "$CUR" ]; then
      V=$(grep -E "^$K=" /root/.hermes/.env | head -1 | cut -d= -f2-)
      if [ -n "$V" ]; then
        if grep -qE "^$K=" .env; then sed -i "s|^$K=.*|$K=$V|" .env; else echo "$K=$V" >> .env; fi
        echo "==> herdou $K do Hermes"
      fi
    fi
  done
fi
echo "==> .env pronto. Edite com 'nano $PROJ_DIR/.env' se faltar alguma chave."

# 3) systemd (nível de sistema, root)
mkdir -p logs
cp deploy/auditoria-folha.service /etc/systemd/system/
cp deploy/auditoria-folha.timer   /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now auditoria-folha.timer
echo "==> Timer ativo:"
systemctl list-timers --no-pager | grep auditoria-folha || true
echo ""
echo "==> Pronto. Rodar AGORA: systemctl start auditoria-folha.service"
echo "==> Acompanhar:        journalctl -u auditoria-folha.service -f"
