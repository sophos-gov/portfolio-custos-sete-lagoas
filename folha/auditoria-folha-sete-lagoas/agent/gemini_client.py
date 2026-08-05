"""
Cliente Gemini robusto (retry exponencial + fallback), inicialização LAZY.

Diferente do template padrão: NÃO levanta exceção no import se a chave faltar.
Use gemini_available() antes; gen_text() retorna str ou None (nunca explode a run).
Baseado na skill gemini-robust (victorbarcelosf@gmail.com).
"""
from __future__ import annotations

import time
from typing import Optional

from . import config

_configured = False
_genai = None


def gemini_available() -> bool:
    return bool(config.GEMINI_API_KEY)


def _ensure() -> bool:
    global _configured, _genai
    if _configured:
        return _genai is not None
    _configured = True
    if not config.GEMINI_API_KEY:
        return False
    try:
        import warnings
        warnings.filterwarnings("ignore", category=FutureWarning)
        import google.generativeai as genai
        genai.configure(api_key=config.GEMINI_API_KEY)
        _genai = genai
        return True
    except Exception as e:  # módulo ausente ou chave inválida
        print(f"[gemini] indisponível: {e}")
        _genai = None
        return False


def gen_text(prompt: str, model_name: Optional[str] = None,
             max_retries: int = 5, **gen_kwargs) -> Optional[str]:
    """Gera texto com retry exponencial e fallback Pro→Flash. Retorna None se falhar."""
    if not _ensure():
        return None
    model_name = model_name or config.GEMINI_MODEL
    from google.api_core import exceptions as gexc

    original = model_name
    model = _genai.GenerativeModel(model_name)
    tentativa = 0
    retries = max_retries
    while tentativa < retries:
        try:
            resp = model.generate_content(prompt, **gen_kwargs)
            return (resp.text or "").strip()
        except (gexc.InternalServerError, gexc.ServiceUnavailable,
                gexc.DeadlineExceeded, gexc.ResourceExhausted) as e:
            wait = 2 ** tentativa
            print(f"[gemini] {type(e).__name__} (tent. {tentativa+1}/{retries}); aguardando {wait}s")
            if tentativa == retries - 1:
                if "pro" in original.lower():
                    print("[gemini] fallback → gemini-2.5-flash")
                    model = _genai.GenerativeModel("gemini-2.5-flash")
                    original = "flash"
                    retries = 3
                    tentativa = -1
                else:
                    print(f"[gemini] esgotado após {retries} tentativas")
                    return None
            else:
                time.sleep(wait)
            tentativa += 1
        except Exception as e:
            print(f"[gemini] erro não recuperável: {type(e).__name__}: {e}")
            return None
    return None
