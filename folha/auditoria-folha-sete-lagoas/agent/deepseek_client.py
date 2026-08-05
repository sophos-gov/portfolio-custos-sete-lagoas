"""
Cliente DeepSeek (API compatível com OpenAI) via requests. Init lazy/graceful.

Usado como SEGUNDO provedor barato quando o Gemini atinge limite de requisições.
gen_text() retorna str ou None (nunca explode a run).
"""
from __future__ import annotations

import time
from typing import Optional

from . import config


def deepseek_available() -> bool:
    return bool(config.DEEPSEEK_API_KEY)


def gen_text(prompt: str, model_name: Optional[str] = None,
             max_retries: int = 4, temperature: float = 0.2,
             max_tokens: int = 2048) -> Optional[str]:
    if not config.DEEPSEEK_API_KEY:
        return None
    try:
        import requests
    except Exception:
        return None
    model_name = model_name or config.DEEPSEEK_MODEL
    url = config.DEEPSEEK_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {config.DEEPSEEK_API_KEY}",
               "Content-Type": "application/json"}
    body = {"model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature, "max_tokens": max_tokens, "stream": False}
    for tent in range(max_retries):
        try:
            r = requests.post(url, headers=headers, json=body, timeout=90)
            if r.status_code == 200:
                data = r.json()
                return (data["choices"][0]["message"]["content"] or "").strip()
            if r.status_code in (429, 500, 502, 503, 529):
                wait = 2 ** tent
                print(f"[deepseek] status {r.status_code} (tent. {tent+1}/{max_retries}); aguardando {wait}s")
                time.sleep(wait)
                continue
            print(f"[deepseek] status não recuperável {r.status_code}: {r.text[:200]}")
            return None
        except Exception as e:
            wait = 2 ** tent
            print(f"[deepseek] {type(e).__name__}: {e}; aguardando {wait}s")
            time.sleep(wait)
    return None
