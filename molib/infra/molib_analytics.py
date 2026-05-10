"""
MolibAnalytics — 轻量自托管分析（Umami 纯 Python 替代）
=====================================================
对标 Umami (23K★): 实时数据 · 隐私优先 · 单SQLite文件
Mac M2: <5MB 内存，stdlib only。

用法:
    python -m molib analytics track --event pageview --page "/home" --referrer "google"
    python -m molib analytics stats --period 7d
    python -m molib analytics top-pages
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("molib.analytics")

DB_PATH = Path.home() / ".hermes" / "molib_analytics.db"


class MolibAnalytics:
    """轻量自托管分析引擎。"""

    def __init__(self, db_path: str = ""):
        self.db_path = db_path or str(DB_PATH)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL DEFAULT 'pageview',
                    page TEXT DEFAULT '',
                    referrer TEXT DEFAULT '',
                    user_agent TEXT DEFAULT '',
                    ip_hash TEXT DEFAULT '',
                    country TEXT DEFAULT '',
                    session_id TEXT DEFAULT '',
                    properties TEXT DEFAULT '{}',
                    created_at TEXT DEFAULT (datetime('now'))
                );
                CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
                CREATE INDEX IF NOT EXISTS idx_events_page ON events(page);
                CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);
                CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
            """)
            conn.commit()

    # ── Track ────────────────────────────────────────────────

    def track(
        self,
        event_type: str = "pageview",
        page: str = "",
        referrer: str = "",
        user_agent: str = "",
        ip_hash: str = "",
        country: str = "",
        session_id: str = "",
        properties: dict = None,
    ) -> dict:
        """记录分析事件。"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO events (event_type, page, referrer, user_agent, ip_hash, country, session_id, properties)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (event_type, page, referrer, user_agent, ip_hash[:16] if ip_hash else "",
                 country, session_id, json.dumps(properties or {}, ensure_ascii=False)),
            )
            conn.commit()
        return {"event": event_type, "page": page, "status": "tracked"}

    # ── Stats ────────────────────────────────────────────────

    def stats(self, period: str = "7d") -> dict:
        """分析统计。

        Args:
            period: 时间范围 24h / 7d / 30d / all
        """
        since = self._period_since(period)

        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM events WHERE created_at >= ?", (since,)
            ).fetchone()[0]

            pageviews = conn.execute(
                "SELECT COUNT(*) FROM events WHERE event_type='pageview' AND created_at >= ?", (since,)
            ).fetchone()[0]

            visitors = conn.execute(
                "SELECT COUNT(DISTINCT COALESCE(session_id, ip_hash)) FROM events WHERE created_at >= ?", (since,)
            ).fetchone()[0]

            sessions = conn.execute(
                "SELECT COUNT(DISTINCT session_id) FROM events WHERE session_id != '' AND created_at >= ?", (since,)
            ).fetchone()[0]

        return {
            "period": period,
            "total_events": total,
            "pageviews": pageviews,
            "unique_visitors": visitors,
            "sessions": sessions,
            "bounce_rate": f"{(1 - sessions / max(visitors, 1)) * 100:.0f}%" if visitors > 0 else "N/A",
        }

    def top_pages(self, period: str = "7d", limit: int = 10) -> list[dict]:
        since = self._period_since(period)
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """SELECT page, COUNT(*) as views, COUNT(DISTINCT COALESCE(session_id, ip_hash)) as visitors
                   FROM events WHERE event_type='pageview' AND created_at >= ?
                   GROUP BY page ORDER BY views DESC LIMIT ?""",
                (since, limit),
            ).fetchall()
        return [{"page": r[0] or "/", "views": r[1], "visitors": r[2]} for r in rows]

    def top_referrers(self, period: str = "7d", limit: int = 10) -> list[dict]:
        since = self._period_since(period)
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """SELECT referrer, COUNT(*) as count
                   FROM events WHERE event_type='pageview' AND referrer != '' AND created_at >= ?
                   GROUP BY referrer ORDER BY count DESC LIMIT ?""",
                (since, limit),
            ).fetchall()
        return [{"referrer": r[0], "count": r[1]} for r in rows]

    def hourly_breakdown(self, period: str = "24h") -> list[dict]:
        since = self._period_since(period)
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """SELECT strftime('%H:00', created_at) as hour, COUNT(*) as events
                   FROM events WHERE created_at >= ?
                   GROUP BY hour ORDER BY hour""",
                (since,),
            ).fetchall()
        return [{"hour": r[0], "events": r[1]} for r in rows]

    def _period_since(self, period: str) -> str:
        now = datetime.now(timezone.utc)
        deltas = {"24h": timedelta(hours=24), "7d": timedelta(days=7),
                  "30d": timedelta(days=30), "all": timedelta(days=3650)}
        delta = deltas.get(period, timedelta(days=7))
        return (now - delta).strftime("%Y-%m-%d %H:%M:%S")


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def cmd_analytics_track(args: list[str]) -> dict:
    a = MolibAnalytics()
    event, page, ref = "pageview", "", ""
    i = 0
    while i < len(args):
        if args[i] == "--event" and i + 1 < len(args):
            event = args[i + 1]; i += 2
        elif args[i] == "--page" and i + 1 < len(args):
            page = args[i + 1]; i += 2
        elif args[i] == "--referrer" and i + 1 < len(args):
            ref = args[i + 1]; i += 2
        else:
            i += 1
    return a.track(event, page, ref)


def cmd_analytics_stats(args: list[str]) -> dict:
    a = MolibAnalytics()
    period = "7d"
    i = 0
    while i < len(args):
        if args[i] == "--period" and i + 1 < len(args):
            period = args[i + 1]; i += 2
        else:
            i += 1
    return a.stats(period)


def cmd_analytics_top(args: list[str]) -> dict:
    a = MolibAnalytics()
    period, limit = "7d", 10
    i = 0
    while i < len(args):
        if args[i] == "--period" and i + 1 < len(args):
            period = args[i + 1]; i += 2
        elif args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1]); i += 2
        else:
            i += 1
    return {"pages": a.top_pages(period, limit), "referrers": a.top_referrers(period, limit)}
