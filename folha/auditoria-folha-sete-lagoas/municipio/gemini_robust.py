# -*- coding: utf-8 -*-
"""
gemini_robust.py — Cliente Gemini resiliente para GRANDES CONTEXTOS.

Padrão da skill gemini-robust (Victor Barcelos):
  - Retry exponencial (1s, 2s, 4s, 8s, 16s) em 500/503/timeout/rate-limit
  - Fallback automático Pro -> Flash
  - SDK novo `google.genai`; fallback para o CLI `gemini -p` se o SDK falhar na auth.

Uso típico (este projeto): ler ~556 KB de leis municipais (legislacao_full/*.txt)
e extrair um brief jurídico por tese. Contexto grande -> Pro (2M) com fallback Flash.
"""
from __future__ import annotations

import os
import sys
import time
import subprocess
from pathlib import Path

# Carrega .env do diretório pai (auditoria-folha-sete-lagoas/.env)
try:
    from dotenv import load_dotenv
    _envp = Path(__file__).resolve().parent.parent / ".env"
    if _envp.exists():
        load_dotenv(_envp)
except Exception:
    pass

PRO = "gemini-2.5-pro"
FLASH = "gemini-2.5-flash"

_RETRYABLE = ("500", "503", "internal", "unavailable", "deadline", "timeout",
              "resource", "exhausted", "overloaded", "rate")


def _is_retryable(err: Exception) -> bool:
    s = (str(err) + " " + type(err).__name__).lower()
    return any(tok in s for tok in _RETRYABLE)


def _gen_sdk(prompt: str, model: str, max_output_tokens: int, temperature: float) -> str:
    from google import genai
    from google.genai import types
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        ),
    )
    return resp.text or ""


def _gen_cli(prompt: str, model: str) -> str:
    """Fallback: usa o CLI gemini (auth própria)."""
    exe = "gemini.cmd" if os.name == "nt" else "gemini"
    for cand in (exe, "gemini"):
        try:
            p = subprocess.run(
                [cand, "-p", prompt, "--model", model],
                capture_output=True, text=True, encoding="utf-8", timeout=600,
            )
            if p.returncode == 0 and p.stdout.strip():
                return p.stdout.strip()
            last = (p.stderr or p.stdout or "").strip()
        except FileNotFoundError:
            last = "gemini CLI não encontrado"
            continue
        except Exception as e:  # noqa
            last = str(e)
    raise RuntimeError(f"CLI gemini falhou: {last[:300]}")


def generate(prompt: str,
             model_name: str = FLASH,
             max_retries: int = 5,
             fallback_to_flash: bool = True,
             max_output_tokens: int = 8192,
             temperature: float = 0.2,
             allow_cli_fallback: bool = True) -> str:
    """Gera conteúdo com retry exponencial + fallback Pro->Flash (+ CLI por último)."""
    model = model_name
    original = model_name
    attempt = 0
    while attempt < max_retries:
        try:
            out = _gen_sdk(prompt, model, max_output_tokens, temperature)
            if attempt > 0:
                print(f"[gemini] OK após {attempt+1} tentativas (modelo {model})", file=sys.stderr)
            return out
        except Exception as e:  # noqa
            retry = _is_retryable(e)
            last = attempt == max_retries - 1
            print(f"[gemini] {type(e).__name__}: {str(e)[:160]} "
                  f"(tent {attempt+1}/{max_retries}, retry={retry})", file=sys.stderr)
            if last:
                if fallback_to_flash and "pro" in original.lower() and model != FLASH:
                    print(f"[gemini] fallback {original} -> {FLASH}", file=sys.stderr)
                    model = FLASH
                    original = FLASH
                    attempt = 0
                    max_retries = 3
                    continue
                if allow_cli_fallback:
                    print("[gemini] fallback SDK -> CLI", file=sys.stderr)
                    try:
                        return _gen_cli(prompt, FLASH)
                    except Exception as ce:  # noqa
                        raise RuntimeError(f"Gemini esgotou SDK+CLI: {ce}") from e
                raise
            if not retry and not (fallback_to_flash and "pro" in original.lower()):
                # erro não-recuperável (ex.: auth) -> tentar CLI direto
                if allow_cli_fallback:
                    print("[gemini] erro não-retryable; tentando CLI", file=sys.stderr)
                    try:
                        return _gen_cli(prompt, FLASH)
                    except Exception:
                        pass
                raise
            time.sleep(2 ** attempt)
            attempt += 1
    raise RuntimeError("Gemini: fluxo inesperado")


if __name__ == "__main__":
    # Smoke test
    print(generate("Responda apenas: OK", model_name=FLASH, max_output_tokens=20))
