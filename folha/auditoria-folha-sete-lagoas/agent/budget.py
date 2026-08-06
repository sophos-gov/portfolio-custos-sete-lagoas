"""Acumulador de tokens/custo com teto rígido (guardrail overnight)."""
from __future__ import annotations

from . import config


class Budget:
    def __init__(self, usd_ceiling: float | None = None):
        self.usd_ceiling = usd_ceiling if usd_ceiling is not None else config.USD_BUDGET
        self.usd_spent = 0.0
        self.tokens_in = 0
        self.tokens_out = 0
        self.calls = 0
        self.by_model: dict[str, dict] = {}

    def add(self, model: str, tokens_in: int, tokens_out: int):
        p = config.price_for(model)
        cost = tokens_in / 1e6 * p["in"] + tokens_out / 1e6 * p["out"]
        self.usd_spent += cost
        self.tokens_in += tokens_in
        self.tokens_out += tokens_out
        self.calls += 1
        m = self.by_model.setdefault(model, {"in": 0, "out": 0, "usd": 0.0, "calls": 0})
        m["in"] += tokens_in
        m["out"] += tokens_out
        m["usd"] += cost
        m["calls"] += 1
        return cost

    def exceeded(self) -> bool:
        return self.usd_spent >= self.usd_ceiling

    def remaining(self) -> float:
        return max(0.0, self.usd_ceiling - self.usd_spent)

    def to_dict(self) -> dict:
        return {
            "usd_ceiling": round(self.usd_ceiling, 4),
            "usd_spent": round(self.usd_spent, 4),
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "calls": self.calls,
            "by_model": {k: {**v, "usd": round(v["usd"], 4)} for k, v in self.by_model.items()},
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Budget":
        b = cls(d.get("usd_ceiling"))
        b.usd_spent = d.get("usd_spent", 0.0)
        b.tokens_in = d.get("tokens_in", 0)
        b.tokens_out = d.get("tokens_out", 0)
        b.calls = d.get("calls", 0)
        b.by_model = d.get("by_model", {})
        return b
