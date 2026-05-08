"""molib.shared.finance.usage_scanner — 扫描 JSONL 日志提取 token/成本数据

吸收自 phuryn/claude-usage 的 scanner.py。
扫描 Claude Code JSONL 会话日志，提取 token 使用量和模型信息。
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class UsageRecord:
    """单条使用记录"""
    session_id: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0
    cost_usd: float = 0.0
    timestamp: str = ""
    project: str = ""
    file_path: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# Anthropic API 定价 (2026年4月)
MODEL_PRICING: dict[str, dict[str, float]] = {
    "claude-opus-4-7":    {"input": 5.00,  "output": 25.00, "cache_write": 6.25, "cache_read": 0.50},
    "claude-opus-4-6":    {"input": 5.00,  "output": 25.00, "cache_write": 6.25, "cache_read": 0.50},
    "claude-sonnet-4-6":  {"input": 3.00,  "output": 15.00, "cache_write": 3.75, "cache_read": 0.30},
    "claude-haiku-4-5":   {"input": 1.00,  "output": 5.00,  "cache_write": 1.25, "cache_read": 0.10},
}


def estimate_cost(model: str, input_t: int, output_t: int,
                  cache_write: int = 0, cache_read: int = 0) -> float:
    """估算单条记录成本 (USD)"""
    for model_prefix, rates in MODEL_PRICING.items():
        if model_prefix in model:
            cost = (
                input_t / 1_000_000 * rates["input"]
                + output_t / 1_000_000 * rates["output"]
                + cache_write / 1_000_000 * rates["cache_write"]
                + cache_read / 1_000_000 * rates["cache_read"]
            )
            return round(cost, 6)
    return 0.0


class UsageScanner:
    """扫描 Claude Code JSONL 日志文件"""

    # ------------------------------------------------------------------
    # CLI Integration
    #   python -m molib finance scan-usage [--projects-dir ~/.claude/projects]
    #   python -m molib finance today
    #   python -m molib finance week
    # ------------------------------------------------------------------

    def __init__(self, projects_dir: Optional[str] = None):
        self._projects_dir = projects_dir or os.path.expanduser("~/.claude/projects")

    def scan(self, max_files: int = 100) -> list[UsageRecord]:
        """扫描 JSONL 文件

        Args:
            max_files: 最多扫描文件数

        Returns:
            UsageRecord 列表
        """
        records: list[UsageRecord] = []
        projects_path = Path(self._projects_dir)
        if not projects_path.exists():
            return records

        jsonl_files = sorted(projects_path.rglob("*.jsonl"),
                             key=lambda p: p.stat().st_mtime, reverse=True)[:max_files]

        for fp in jsonl_files:
            session_records = self._parse_file(fp)
            records.extend(session_records)

        return records

    def _parse_file(self, filepath: Path) -> list[UsageRecord]:
        """解析单个 JSONL 文件"""
        records: list[UsageRecord] = []
        session_data: dict[str, dict] = {}

        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return records

        for line in content.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg = entry.get("message", {})
            usage = msg.get("usage", {})
            if not usage:
                continue

            model = msg.get("model", "unknown")
            uid = f"{filepath.name}:{model}"
            if uid not in session_data:
                session_data[uid] = {
                    "model": model,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cache_write": 0,
                    "cache_read": 0,
                }

            sd = session_data[uid]
            sd["input_tokens"] += usage.get("input_tokens", 0) or 0
            sd["output_tokens"] += usage.get("output_tokens", 0) or 0
            sd["cache_write"] += usage.get("cache_creation_input_tokens", 0) or 0
            sd["cache_read"] += usage.get("cache_read_input_tokens", 0) or 0

        for uid, sd in session_data.items():
            model = sd["model"]
            cost = estimate_cost(
                model, sd["input_tokens"], sd["output_tokens"],
                sd["cache_write"], sd["cache_read"],
            )
            records.append(UsageRecord(
                session_id=filepath.stem,
                model=model,
                input_tokens=sd["input_tokens"],
                output_tokens=sd["output_tokens"],
                cache_write_tokens=sd["cache_write"],
                cache_read_tokens=sd["cache_read"],
                cost_usd=cost,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(filepath.stat().st_mtime)),
                project=filepath.parent.name,
                file_path=str(filepath),
            ))

        return records

    def scan_today(self, max_files: int = 50) -> list[UsageRecord]:
        """仅扫描今天的文件"""
        import datetime
        today = datetime.date.today().isoformat()
        all_records = self.scan(max_files=max_files)
        return [r for r in all_records if r.timestamp.startswith(today)]

    def scan_week(self, max_files: int = 200) -> list[UsageRecord]:
        """扫描最近7天"""
        import datetime
        week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
        all_records = self.scan(max_files=max_files)
        return [r for r in all_records if r.timestamp[:10] >= week_ago]
