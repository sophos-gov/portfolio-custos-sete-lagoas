"""Checkpoint retomável: serializa o estado do agente após cada passo."""
from __future__ import annotations

import json
from pathlib import Path

from . import config

STATE = config.CKPT_DIR / "state.json"
STATE_BAK = config.CKPT_DIR / "state.bak.json"


def save(state: dict):
    """Escreve atômico: tmp → rename; mantém .bak da versão anterior."""
    tmp = config.CKPT_DIR / "state.tmp.json"
    tmp.write_text(json.dumps(state, ensure_ascii=False, default=str), encoding="utf-8")
    if STATE.exists():
        try:
            STATE_BAK.write_text(STATE.read_text(encoding="utf-8"), encoding="utf-8")
        except Exception:
            pass
    tmp.replace(STATE)


def load() -> dict | None:
    for p in (STATE, STATE_BAK):
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
    return None


def clear():
    for p in (STATE, STATE_BAK):
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass
