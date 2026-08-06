"""Log de progresso append-only (progress.jsonl) — uma linha por passo."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from . import config


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log(event: str, **fields):
    rec = {"ts": _now(), "event": event}
    rec.update(fields)
    # nunca logar segredos (denylist explícita)
    _SECRET = {"api_key", "anthropic_api_key", "gemini_api_key",
               "telegram_bot_token", "bot_token", "secret", "password"}
    for k in list(rec.keys()):
        if k.lower() in _SECRET:
            rec.pop(k, None)
    try:
        with config.PROGRESS_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass
    # eco no stdout (capturado pelo journald/log)
    print(f"[{rec['ts']}] {event} " +
          " ".join(f"{k}={v}" for k, v in fields.items() if k not in ("history",)))
