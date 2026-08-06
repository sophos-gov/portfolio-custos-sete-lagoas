"""Wrapper da Anthropic Messages API com retry e contabilização de budget."""
from __future__ import annotations

import json
import re
import time
from typing import Optional

from . import config
from .budget import Budget


class Claude:
    def __init__(self, budget: Budget):
        self.budget = budget
        self._client = None
        self._ok = None

    def available(self) -> bool:
        if self._ok is not None:
            return self._ok
        if not config.ANTHROPIC_API_KEY:
            self._ok = False
            return False
        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
            self._ok = True
        except Exception as e:
            print(f"[claude] indisponível: {e}")
            self._ok = False
        return self._ok

    def create(self, model: str, system: str, messages: list,
               tools: Optional[list] = None, max_tokens: int = 4096,
               max_retries: int = 4):
        """Chama messages.create com retry exponencial. Retorna response ou None."""
        if not self.available():
            return None
        import anthropic
        kwargs = dict(model=model, system=system, messages=messages, max_tokens=max_tokens)
        if tools:
            kwargs["tools"] = tools
        for tent in range(max_retries):
            try:
                resp = self._client.messages.create(**kwargs)
                u = getattr(resp, "usage", None)
                if u:
                    self.budget.add(model, getattr(u, "input_tokens", 0), getattr(u, "output_tokens", 0))
                return resp
            except (anthropic.RateLimitError, anthropic.InternalServerError,
                    anthropic.APIConnectionError, anthropic.APITimeoutError) as e:
                wait = 2 ** tent
                print(f"[claude] {type(e).__name__} (tent. {tent+1}/{max_retries}); aguardando {wait}s")
                time.sleep(wait)
            except anthropic.APIStatusError as e:
                if getattr(e, "status_code", 0) in (429, 500, 529, 503):
                    wait = 2 ** tent
                    print(f"[claude] status {e.status_code} (tent. {tent+1}); aguardando {wait}s")
                    time.sleep(wait)
                    continue
                print(f"[claude] erro de status não recuperável: {e}")
                return None
            except Exception as e:
                print(f"[claude] erro inesperado: {type(e).__name__}: {e}")
                return None
        return None

    @staticmethod
    def text_of(resp) -> str:
        if not resp:
            return ""
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")

    def complete_json(self, model: str, system: str, prompt: str, max_tokens: int = 4096) -> Optional[dict]:
        """Pede um JSON e devolve dict (ou None)."""
        resp = self.create(model, system, [{"role": "user", "content": prompt}], max_tokens=max_tokens)
        txt = self.text_of(resp)
        if not txt:
            return None
        txt = re.sub(r"^```(?:json)?|```$", "", txt.strip(), flags=re.MULTILINE).strip()
        try:
            return json.loads(txt)
        except Exception:
            m = re.search(r"\{.*\}", txt, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:
                    return None
            return None
