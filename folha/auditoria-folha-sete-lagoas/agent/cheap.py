"""
Roteador de modelo BARATO: tenta Gemini Flash primeiro; se falhar (ex.: limite de
requisições), cai para DeepSeek. Retorna str ou None — nunca explode a run.
"""
from __future__ import annotations

from typing import Optional

from . import gemini_client
from . import deepseek_client


def cheap_available() -> bool:
    return gemini_client.gemini_available() or deepseek_client.deepseek_available()


def gen_text(prompt: str, temperature: float = 0.2) -> Optional[str]:
    # 1) Gemini Flash (poucas tentativas — se bater limite, vamos para o DeepSeek logo)
    if gemini_client.gemini_available():
        r = gemini_client.gen_text(prompt, max_retries=2,
                                   generation_config={"temperature": temperature})
        if r:
            return r
    # 2) DeepSeek (segundo provedor)
    if deepseek_client.deepseek_available():
        r = deepseek_client.gen_text(prompt, temperature=temperature)
        if r:
            return r
    return None
