"""molib.shared.finance.cost_tracker — 成本追踪与预算报告

增量存储 token 使用数据到 SQLite 数据库。
支持每日/月度聚合、预算水位监控。
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


@dataclass
class CostEstimate:
    """成本估算"""
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_cost_cny: float = 0.0  # USD→CNY 估算
    by_model: dict[str, dict] = field(default_factory=dict)
    period: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class BudgetReport:
    """预算报告"""
    budget_monthly_cny: float = 0.0
    spent_cny: float = 0.0
    remaining_cny: float = 0.0
    usage_pct: float = 0.0
    days_remaining: int = 0
    daily_burn_cny: float = 0.0
    projected_cny: float = 0.0
    by_model: dict[str, dict] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


# USD → CNY 估算汇率 (2026年5月)
USD_TO_CNY = 7.2

# 默认月度预算 (CNY)
DEFAULT_MONTHLY_BUDGET = 1360


class CostTracker:
    """成本追踪器

    将 UsageRecord 增量存储到 SQLite 数据库。
    支持按时间段/模型聚合，输出预算报告。
    """

    def __init__(self, db_path: Optional[str] = None,
                 monthly_budget_cny: float = DEFAULT_MONTHLY_BUDGET):
        self._db_path = db_path or os.path.expanduser("~/.hermes/finance/usage.db")
        self._budget = monthly_budget_cny
        self._ensure_db()

    def _ensure_db(self):
        """确保数据库和表存在"""
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usage (
                    session_id TEXT,
                    model TEXT,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    cache_write_tokens INTEGER DEFAULT 0,
                    cache_read_tokens INTEGER DEFAULT 0,
                    cost_usd REAL DEFAULT 0.0,
                    timestamp TEXT,
                    project TEXT DEFAULT '',
                    file_path TEXT DEFAULT '',
                    scanned_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_usage_timestamp
                ON usage(timestamp)
            """)
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # CLI Integration
    #   python -m molib finance store-usage [--records records.json]
    #   python -m molib finance report [--period month]
    #   python -m molib finance budget
    # ------------------------------------------------------------------

    def store(self, records: list[UsageRecord]) -> int:
        """增量存储记录

        Returns:
            存储的记录数
        """
        conn = sqlite3.connect(self._db_path)
        try:
            cursor = conn.cursor()
            # 检查已存在的 session_id + model 组合
            existing = set()
            for row in cursor.execute("SELECT DISTINCT session_id, model FROM usage"):
                existing.add((row[0], row[1]))

            count = 0
            for r in records:
                key = (r.session_id, r.model)
                if key in existing:
                    continue
                cursor.execute(
                    """INSERT INTO usage
                       (session_id, model, input_tokens, output_tokens,
                        cache_write_tokens, cache_read_tokens, cost_usd,
                        timestamp, project, file_path)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (r.session_id, r.model, r.input_tokens, r.output_tokens,
                     r.cache_write_tokens, r.cache_read_tokens, r.cost_usd,
                     r.timestamp, r.project, r.file_path),
                )
                count += 1
                existing.add(key)
            conn.commit()
            return count
        finally:
            conn.close()

    def estimate(self, period: str = "month") -> CostEstimate:
        """获取成本估算

        Args:
            period: "day", "week", "month", "all"

        Returns:
            CostEstimate
        """
        period_sql = ""
        if period == "day":
            period_sql = "WHERE date(timestamp) = date('now')"
        elif period == "week":
            period_sql = "WHERE timestamp >= datetime('now', '-7 days')"
        elif period == "month":
            period_sql = "WHERE timestamp >= datetime('now', '-30 days')"

        conn = sqlite3.connect(self._db_path)
        try:
            cursor = conn.cursor()

            # 总成本
            cursor.execute(f"""
                SELECT COALESCE(SUM(input_tokens + output_tokens), 0),
                       COALESCE(SUM(cost_usd), 0)
                FROM usage {period_sql}
            """)
            total_tokens, total_cost = cursor.fetchone()

            # 按模型
            cursor.execute(f"""
                SELECT model,
                       SUM(input_tokens + output_tokens),
                       SUM(cost_usd),
                       SUM(input_tokens),
                       SUM(output_tokens),
                       SUM(cache_write_tokens),
                       SUM(cache_read_tokens)
                FROM usage {period_sql}
                GROUP BY model
                ORDER BY SUM(cost_usd) DESC
            """)
            by_model = {}
            for row in cursor.fetchall():
                model, tokens, cost, inp, out, cw, cr = row
                by_model[model] = {
                    "total_tokens": tokens or 0,
                    "cost_usd": round(cost or 0, 4),
                    "input_tokens": inp or 0,
                    "output_tokens": out or 0,
                    "cache_write_tokens": cw or 0,
                    "cache_read_tokens": cr or 0,
                }

            return CostEstimate(
                total_tokens=total_tokens or 0,
                total_cost_usd=round(total_cost or 0, 4),
                total_cost_cny=round((total_cost or 0) * USD_TO_CNY, 2),
                by_model=by_model,
                period=period,
            )
        finally:
            conn.close()

    def budget_report(self) -> BudgetReport:
        """生成预算报告"""
        now = datetime.now()
        days_in_month = 30
        days_passed = now.day
        days_remaining = days_in_month - days_passed

        estimate = self.estimate(period="month")
        spent = estimate.total_cost_cny
        remaining = max(0.0, self._budget - spent)
        usage_pct = (spent / self._budget * 100) if self._budget > 0 else 0.0

        daily_burn = (spent / days_passed) if days_passed > 0 else 0.0
        projected = daily_burn * days_in_month

        return BudgetReport(
            budget_monthly_cny=self._budget,
            spent_cny=round(spent, 2),
            remaining_cny=round(remaining, 2),
            usage_pct=round(usage_pct, 1),
            days_remaining=days_remaining,
            daily_burn_cny=round(daily_burn, 2),
            projected_cny=round(projected, 2),
            by_model=estimate.by_model,
        )
