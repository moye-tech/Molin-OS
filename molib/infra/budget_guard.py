"""
BudgetGuard — API cost tracking with auto-fuse for Mac M2 (Python 3.11, 8GB RAM)

Design:
  - Zero external deps (stdlib only)
  - Lightweight (<300 lines)
  - File-backed persistence at ~/.hermes/budget_guard.json
  - Works offline, no cloud dependency

Usage:
  from molib.infra.budget_guard import BudgetGuard
  bg = BudgetGuard()
  bg.track('deepseek', 'deepseek-v4-pro', 10000, 5000)
  r = bg.check()  # {"blocked": bool, "usage_pct": float, "warning": bool}
"""

import json
import os
import time
from pathlib import Path
from datetime import date

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STORAGE_PATH = Path.home() / ".hermes" / "budget_guard.json"

# Pricing: ¥ per 1K tokens (or per image for vision models)
PRICING = {
    "deepseek": {
        "deepseek-v4-pro":   {"input_per_1k": 0.014, "output_per_1k": 0.056},
        "deepseek-v4-flash": {"input_per_1k": 0.004, "output_per_1k": 0.014},
    },
    "anthropic": {
        "claude-sonnet-4":   {"input_per_1k": 0.022, "output_per_1k": 0.11},
    },
    "qwen": {
        "qwen-vl-plus":      {"per_image": 0.002},
    },
}

DAILY_BUDGET      = 100.0   # ¥100 total daily budget
WARNING_THRESHOLD = 0.80    # 80% → warning
BLOCK_THRESHOLD   = 1.00    # 100% → blocked

# Fallback rate for unknown models
FALLBACK_RATE_PER_1K = 0.01

# ---------------------------------------------------------------------------
# BudgetGuard
# ---------------------------------------------------------------------------

class BudgetGuard:
    """API cost tracker with auto-fuse (block) at daily budget exhaustion."""

    def __init__(self, storage_path: Path | str | None = None):
        self._path = Path(storage_path) if storage_path else STORAGE_PATH
        self._data = self._load()
        self._check_date_rollover()

    # ---- persistence -------------------------------------------------------

    def _load(self) -> dict:
        """Load state from JSON file or return fresh defaults."""
        if self._path.exists():
            try:
                return json.loads(self._path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, IOError):
                pass
        return self._default_state()

    def _default_state(self) -> dict:
        return {
            "daily": {
                "date": str(date.today()),
                "spent": 0.0,
                "calls": 0,
            },
            "history": [],       # [{date, spent, calls}, …]  last 90 days
            "by_provider": {},   # {provider: {spent, calls}}
            "by_model": {},      # {"provider/model": {spent, calls}}
            "config": {
                "daily_budget": DAILY_BUDGET,
                "warning_threshold": WARNING_THRESHOLD,
                "block_threshold": BLOCK_THRESHOLD,
            },
        }

    def _persist(self) -> None:
        """Write current state to JSON (atomic-ish via temp file)."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        tmp.replace(self._path)

    def _check_date_rollover(self) -> None:
        """Reset daily counters if the date has changed."""
        today = str(date.today())
        if self._data["daily"]["date"] == today:
            return
        # archive previous day
        prev = self._data["daily"]
        self._data["history"].append({
            "date": prev["date"],
            "spent": prev["spent"],
            "calls": prev["calls"],
        })
        # trim to 90 days
        if len(self._data["history"]) > 90:
            self._data["history"] = self._data["history"][-90:]
        # fresh day
        self._data["daily"] = {"date": today, "spent": 0.0, "calls": 0}
        self._persist()

    # ---- cost computation --------------------------------------------------

    def _compute_cost(self, provider: str, model: str,
                      input_tokens: int, output_tokens: int,
                      images: int = 0) -> float:
        """Return cost in ¥ for a single API call."""
        prov_pricing = PRICING.get(provider, {})
        mod_pricing  = prov_pricing.get(model, {})

        if not mod_pricing:
            # unknown model — use fallback
            return (input_tokens + output_tokens) * FALLBACK_RATE_PER_1K / 1000

        if "per_image" in mod_pricing:
            return images * mod_pricing["per_image"]

        cost = 0.0
        if input_tokens:
            cost += (input_tokens / 1000) * mod_pricing.get("input_per_1k", 0)
        if output_tokens:
            cost += (output_tokens / 1000) * mod_pricing.get("output_per_1k", 0)
        return cost

    # ---- public API --------------------------------------------------------

    def track(self, provider: str, model: str,
              input_tokens: int, output_tokens: int,
              images: int = 0) -> float:
        """Record an API call and persist immediately.  Returns cost in ¥."""
        self._check_date_rollover()
        cost = self._compute_cost(provider, model, input_tokens, output_tokens, images)

        # daily
        self._data["daily"]["spent"] += cost
        self._data["daily"]["calls"] += 1

        # by provider
        if provider not in self._data["by_provider"]:
            self._data["by_provider"][provider] = {"spent": 0.0, "calls": 0}
        self._data["by_provider"][provider]["spent"] += cost
        self._data["by_provider"][provider]["calls"] += 1

        # by model
        model_key = f"{provider}/{model}"
        if model_key not in self._data["by_model"]:
            self._data["by_model"][model_key] = {"spent": 0.0, "calls": 0}
        self._data["by_model"][model_key]["spent"] += cost
        self._data["by_model"][model_key]["calls"] += 1

        self._persist()
        return cost

    def check(self, provider: str | None = None) -> dict:
        """Return {"blocked": bool, "usage_pct": float, "warning": bool}.

        If *provider* is given the usage percentage reflects that provider's
        share of the daily budget (same ¥100 cap).
        """
        self._check_date_rollover()
        budget = self._data["config"]["daily_budget"]

        if provider:
            prov = self._data["by_provider"].get(provider, {"spent": 0.0})
            spent = prov["spent"]
        else:
            spent = self._data["daily"]["spent"]

        usage_pct = round((spent / budget) * 100, 2) if budget > 0 else 0.0
        return {
            "blocked": usage_pct >= 100.0,
            "usage_pct": usage_pct,
            "warning": usage_pct >= 80.0,
        }

    def get_report(self) -> dict:
        """Full stats: daily, by-provider, by-model, recent history."""
        self._check_date_rollover()
        daily = self._data["daily"]
        cfg   = self._data["config"]
        spent = daily["spent"]
        budget = cfg["daily_budget"]
        usage_pct = round((spent / budget) * 100, 2) if budget > 0 else 0.0

        return {
            "daily": {
                "date":      daily["date"],
                "spent":     round(spent, 4),
                "calls":     daily["calls"],
                "budget":    budget,
                "usage_pct": usage_pct,
                "remaining": round(budget - spent, 4),
            },
            "by_provider": self._data["by_provider"],
            "by_model":    self._data["by_model"],
            "history":     self._data["history"][-7:],  # last 7 days
            "status": (
                "blocked" if usage_pct >= 100 else
                "warning" if usage_pct >= 80 else
                "ok"
            ),
        }

    def reset_daily(self) -> dict:
        """Force-reset today's counters (archive previous day)."""
        today = str(date.today())
        prev = self._data["daily"]
        self._data["history"].append({
            "date":  prev["date"],
            "spent": prev["spent"],
            "calls": prev["calls"],
        })
        self._data["daily"] = {"date": today, "spent": 0.0, "calls": 0}
        self._persist()
        return {"reset": True, "date": today}
