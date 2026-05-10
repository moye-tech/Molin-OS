"""
墨麟OS — BudgetGuard 预算守卫（含 SQLite 持久化）

修复 P1-1: BudgetGuard 成本数据重启丢失。
来源：molinOS_upgrade_plan.html §02 P1-1
"""
import sqlite3
import os
import time
import logging
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger("molin.ceo.budget_guard")

DB_PATH = Path.home() / ".hermes" / "state" / "budget.db"

@dataclass
class BudgetState:
    today_spent: float = 0.0
    month_spent: float = 0.0
    daily_limit: float = 50.0
    monthly_limit: float = 1360.0
    alert_threshold: float = 0.8

class BudgetGuard:
    """预算守卫 — 内存缓存 + SQLite 持久化"""

    def __init__(self):
        self._state = BudgetState()
        self._db = None
        self._init_db()
        self._load_state()

    def _init_db(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(DB_PATH))
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS budget (
                id INTEGER PRIMARY KEY CHECK(id=1),
                today_spent REAL DEFAULT 0,
                month_spent REAL DEFAULT 0,
                daily_limit REAL DEFAULT 50,
                monthly_limit REAL DEFAULT 1360,
                date TEXT DEFAULT '',
                updated_at REAL DEFAULT 0
            )
        """)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS budget_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL,
                model TEXT,
                task TEXT,
                timestamp REAL
            )
        """)
        self._db.commit()

    def _load_state(self):
        row = self._db.execute("SELECT * FROM budget WHERE id=1").fetchone()
        if row:
            today = row[1]
            month = row[2]
            stored_date = row[4]
            today_str = time.strftime("%Y-%m-%d")
            if stored_date != today_str:
                today = 0.0
            self._state.today_spent = today
            self._state.month_spent = month
            self._state.daily_limit = row[3]
            self._state.monthly_limit = row[5]
        else:
            self._db.execute(
                "INSERT INTO budget(id,date,updated_at) VALUES(1,?,?)",
                (time.strftime("%Y-%m-%d"), time.time())
            )
            self._db.commit()

    def spend(self, amount: float, model: str = "", task: str = ""):
        self._state.today_spent += amount
        self._state.month_spent += amount
        self._db.execute(
            "UPDATE budget SET today_spent=?, month_spent=?, date=?, updated_at=? WHERE id=1",
            (self._state.today_spent, self._state.month_spent,
             time.strftime("%Y-%m-%d"), time.time())
        )
        self._db.execute(
            "INSERT INTO budget_log(amount,model,task,timestamp) VALUES(?,?,?,?)",
            (amount, model, task, time.time())
        )
        self._db.commit()
        self._check_alerts()

    def can_spend(self, amount: float) -> bool:
        return (self._state.today_spent + amount) <= self._state.daily_limit

    def daily_remaining(self) -> float:
        return max(0, self._state.daily_limit - self._state.today_spent)

    def monthly_remaining(self) -> float:
        return max(0, self._state.monthly_limit - self._state.month_spent)

    def _check_alerts(self):
        if self._state.today_spent >= self._state.daily_limit * self._state.alert_threshold:
            logger.warning(f"预算告警: 今日已花费 ¥{self._state.today_spent:.2f}/{self._state.daily_limit:.2f}")
        if self._state.month_spent >= self._state.monthly_limit * self._state.alert_threshold:
            logger.warning(f"月度预算告警: ¥{self._state.month_spent:.2f}/{self._state.monthly_limit:.2f}")

    def get_stats(self) -> dict:
        return {
            "today_spent": self._state.today_spent,
            "daily_remaining": self.daily_remaining(),
            "daily_limit": self._state.daily_limit,
            "month_spent": self._state.month_spent,
            "monthly_remaining": self.monthly_remaining(),
            "monthly_limit": self._state.monthly_limit,
            "alert": self._state.today_spent >= self._state.daily_limit * self._state.alert_threshold,
        }

_budget_guard: BudgetGuard | None = None

def get_budget_guard() -> BudgetGuard:
    global _budget_guard
    if _budget_guard is None:
        _budget_guard = BudgetGuard()
    return _budget_guard
