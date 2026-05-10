"""
墨测数据 Worker 升级 — 从定义骨架到真实分析
=========================================
集成 MolibAnalytics + CocoIndex，支持：
  - 网站分析 (pageview/visitor/referrer)
  - 内容效果追踪 (top pages)
  - 时段分布 (hourly breakdown)
  - 数据导出 (CSV/JSON)
"""

from __future__ import annotations

import csv
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("molin.analyst")

OUTPUT = Path.home() / "Molin-OS" / "output" / "reports"


class DataAnalyst:
    """墨测数据 — 真实分析引擎。"""

    def __init__(self):
        OUTPUT.mkdir(parents=True, exist_ok=True)
        self._analytics = None
        self._coco = None

    @property
    def analytics(self):
        if self._analytics is None:
            from molib.infra.molib_analytics import MolibAnalytics
            self._analytics = MolibAnalytics()
        return self._analytics

    @property
    def coco(self):
        if self._coco is None:
            from molib.infra.coco_index import CocoIndex
            self._coco = CocoIndex()
        return self._coco

    def dashboard(self, period: str = "7d") -> dict:
        """综合仪表盘。"""
        stats = self.analytics.stats(period)
        top = self.analytics.top_pages(period, 5)
        hourly = self.analytics.hourly_breakdown(period)

        # 整合 CocoIndex 数据
        coco_stats = self.coco.get_stats()

        return {
            "period": period,
            "traffic": stats,
            "top_pages": top,
            "hourly": hourly,
            "knowledge_index": {
                "files_indexed": coco_stats.get("total_files", 0),
                "watch_dirs": len(coco_stats.get("watch_dirs", [])),
            },
            "generated_at": datetime.now().isoformat(),
        }

    def export(self, format: str = "json") -> dict:
        """导出分析报告。"""
        data = self.dashboard("7d")

        if format == "csv":
            path = str(OUTPUT / f"report_{datetime.now():%Y%m%d}.csv")
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["metric", "value"])
                writer.writerow(["pageviews", data["traffic"]["pageviews"]])
                writer.writerow(["visitors", data["traffic"]["unique_visitors"]])
                writer.writerow(["bounce_rate", data["traffic"]["bounce_rate"]])
                for p in data["top_pages"]:
                    writer.writerow([f"page:{p['page']}", p["views"]])
        else:
            path = str(OUTPUT / f"report_{datetime.now():%Y%m%d}.json")
            with open(path, "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        return {"format": format, "path": path, "size_kb": round(os.path.getsize(path)/1024, 1)}

    def track_content(self, page: str, referrer: str = "", event: str = "pageview") -> dict:
        """追踪内容表现。"""
        return self.analytics.track(event, page, referrer)


def cmd_data_dashboard(period: str = "7d") -> dict:
    return DataAnalyst().dashboard(period)


def cmd_data_export(format: str = "json") -> dict:
    return DataAnalyst().export(format)
