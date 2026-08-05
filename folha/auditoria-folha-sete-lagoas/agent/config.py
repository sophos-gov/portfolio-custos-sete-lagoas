"""Configuração central: caminhos, modelos, budgets. Carrega .env se presente."""
from __future__ import annotations

import os
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# Carregar .env do projeto (sem depender de python-dotenv estar instalado)
def _load_env():
    try:
        from dotenv import load_dotenv
        env = BASE / ".env"
        if env.exists():
            load_dotenv(env)
            return
    except Exception:
        pass
    # Fallback manual
    env = BASE / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())


_load_env()

# --- Diretórios ---
DATA_DIR = BASE / "data"
TABELAS_DIR = BASE / "analysis" / "tabelas"
OUTPUT_DIR = BASE / "output"
OUTPUT_HTML = OUTPUT_DIR / "relatorio_custos_folha_saude_setelagoas.html"
CACHE_DIR = BASE / "legislacao_cache"
SEED_DIR = BASE / "legislacao_seed"   # textos de lei pré-extraídos (versionados; .doc que a VPS não parseia)
CKPT_DIR = BASE / "checkpoints"
LOGS_DIR = BASE / "logs"
PROGRESS_FILE = BASE / "progress.jsonl"
MISSION_FILE = BASE / "MISSION.md"
PLAN_FILE = BASE / "plan.json"
RELATORIO_EXEC = BASE / "RELATORIO_EXECUCAO.md"

for d in (TABELAS_DIR, OUTPUT_DIR, CACHE_DIR, CKPT_DIR, LOGS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# --- Chaves ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8969330678").strip()

# --- Modelos (override por env; ajuste conforme acesso da sua API) ---
ROUTER_MODEL = os.getenv("ROUTER_MODEL", "claude-sonnet-4-6")
SYNTH_MODEL = os.getenv("SYNTH_MODEL", "claude-opus-4-8")
SELFCHECK_MODEL = os.getenv("SELFCHECK_MODEL", ROUTER_MODEL)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

# --- Guardrails ---
USD_BUDGET = float(os.getenv("AGENT_USD_BUDGET", "3.0"))
MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITERATIONS", "120"))
MAX_WALL_SECONDS = int(os.getenv("AGENT_MAX_WALL_SECONDS", "14400"))
LAW_SCRAPE_DOMAINS = [d.strip() for d in os.getenv(
    "LAW_SCRAPE_DOMAINS",
    "leismunicipais.com.br,camarasetelagoas.mg.gov.br,setelagoas.mg.leg.br,jusbrasil.com.br"
).split(",") if d.strip()]

# --- Preços aproximados (USD por 1M tokens) para o acumulador de budget ---
PRICES = {
    "opus":   {"in": 15.0, "out": 75.0},
    "sonnet": {"in": 3.0,  "out": 15.0},
    "haiku":  {"in": 0.80, "out": 4.0},
    "gemini": {"in": 0.10, "out": 0.40},
    "deepseek": {"in": 0.27, "out": 1.10},
}


def price_for(model: str) -> dict:
    m = (model or "").lower()
    if "opus" in m:
        return PRICES["opus"]
    if "haiku" in m:
        return PRICES["haiku"]
    if "deepseek" in m:
        return PRICES["deepseek"]
    if "gemini" in m or "flash" in m:
        return PRICES["gemini"]
    return PRICES["sonnet"]


def anthropic_available() -> bool:
    return bool(ANTHROPIC_API_KEY)
