"""实时预算熔断器 — 每次 LLM 调用前预检，超限自动降级为 Flash"""
import os
import time
from loguru import logger


class BudgetGuard:
    """预算熔断器：日预算耗尽时 Pro 模型自动降级为 Flash"""

    PRO_MODELS = {"deepseek-v4-pro", "qwen3.6-max-preview"}

    def __init__(self):
        self._today: float = 0.0
        self._day_ts: int = 0

    def _reset_if_new_day(self):
        today_start = int(time.time() / 86400) * 86400
        if today_start != self._day_ts:
            self._today = 0.0
            self._day_ts = today_start

    def check_and_select(self, model: str, estimated_cost: float = 0.01) -> str:
        """返回实际应使用的模型（可能被降级）"""
        if os.getenv("BUDGET_GUARD_ENABLED", "true").lower() != "true":
            return model
        self._reset_if_new_day()
        budget = float(os.getenv("DAILY_BUDGET_CNY", "50"))
        threshold = float(os.getenv("BUDGET_ALERT_THRESHOLD", "0.8"))

        if self._today >= budget and model in self.PRO_MODELS:
            logger.warning(
                f"BudgetGuard: 预算耗尽 ¥{self._today:.2f}/{budget}，"
                f"降级 {model} → deepseek-v4-flash"
            )
            return "deepseek-v4-flash"

        if budget > 0 and self._today / budget >= threshold:
            logger.warning(
                f"BudgetGuard: 预算告警 ¥{self._today:.2f}/{budget} "
                f"（{threshold*100:.0f}%）"
            )
        return model

    def record_cost(self, cost: float):
        self._reset_if_new_day()
        self._today += cost


_guard = BudgetGuard()


def get_budget_guard() -> BudgetGuard:
    return _guard
