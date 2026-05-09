"""
墨麟OS — API 成本追踪与预警
==========================
跟踪 DeepSeek、百炼(DashScope)等 API 的调用次数和估算成本。

⚠️ 两套成本追踪系统并存说明：
   - 本文件 (molib/cost.py): 使用 ~/.hermes/cost.db 记录 API 调用成本
     按模型定价估算费用（元），配合 governance.yaml 的 budget 做月度预算控制。
   - molib/shared/finance/cost_tracker.py: 使用 ~/.hermes/usage.db 记录 token 用量
     从 provider 维度统计，支持 USD/CNY 双币种，偏重用量审计。
   两者数据源独立但互补：cost.py 关注「花了多少钱」与预算对齐，
   cost_tracker.py 关注「用了多少 token」与用量审计对齐。
   未来可考虑合并到统一成本数据库。

DeepSeek API 定价（2026.5）:
  - deepseek-chat (V3): ¥2/1M input, ¥8/1M output
  - deepseek-reasoner (R1): ¥4/1M input, ¥16/1M output

DashScope (百炼) 定价:
  - qwen-max: ¥0.8/1K input, ¥2/1K output
  - qwen-vl-plus: ¥6/1K input, ¥12/1K output
  - qwen-image-2.0-pro: ¥0.02/image

用法:
    python3 -m molib.cost record --input 100 --output 50 --model deepseek-chat
    python3 -m molib.cost report                  # 月度报告
    python3 -m molib.cost alert                    # 检查预警
"""

import json
import logging
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger("molin.cost")

DB_PATH = Path.home() / ".hermes" / "cost.db"

# 模型定价（元/1M tokens / 图片）
MODEL_PRICING: dict[str, dict[str, float]] = {
    # DeepSeek
    "deepseek-chat": {"input": 2.0, "output": 8.0},
    "deepseek-reasoner": {"input": 4.0, "output": 16.0},
    # DashScope
    "qwen-max": {"input": 0.8, "output": 2.0},
    "qwen-plus": {"input": 0.8, "output": 2.0},
    "qwen-turbo": {"input": 0.3, "output": 0.6},
    "qwen3-chat": {"input": 2.0, "output": 8.0},
    "qwen3-reasoner": {"input": 4.0, "output": 16.0},
    "qwen-vl-plus": {"input": 6.0, "output": 12.0},
    "qwen-vl-max": {"input": 5.0, "output": 10.0},
    "qwen-image-2.0-pro": {"input": 0, "output": 0, "per_image": 0.02},
    # 默认
    "default": {"input": 2.0, "output": 8.0},
}

# 月度预算上限
MONTHLY_BUDGET = 1360.0  # 预算/月
ALERT_THRESHOLD = 0.8    # 达到 80% 预警
CRITICAL_THRESHOLD = 0.95  # 达到 95% 严重预警


def _get_db() -> sqlite3.Connection:
    """获取数据库连接"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cost_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            model TEXT NOT NULL DEFAULT 'unknown',
            input_tokens INTEGER NOT NULL DEFAULT 0,
            output_tokens INTEGER NOT NULL DEFAULT 0,
            images INTEGER NOT NULL DEFAULT 0,
            task TEXT DEFAULT '',
            provider TEXT DEFAULT 'deepseek',
            cost REAL NOT NULL DEFAULT 0.0
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_cost_month
        ON cost_log(timestamp)
    """)
    conn.commit()
    return conn


def _estimate_cost(model: str, input_tokens: int, output_tokens: int, images: int = 0) -> float:
    """估算 API 调用成本（元）"""
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["default"])
    cost = 0.0
    cost += (input_tokens / 1_000_000) * pricing.get("input", 2.0)
    cost += (output_tokens / 1_000_000) * pricing.get("output", 8.0)
    cost += images * pricing.get("per_image", 0.02)
    return round(cost, 6)


def record(model: str = "unknown", input_tokens: int = 0, output_tokens: int = 0,
           images: int = 0, task: str = "", provider: str = "deepseek") -> float:
    """记录一次 API 调用并返回成本

    用法:
        record("deepseek-chat", 500, 200, task="日常对话")
        record("qwen-image-2.0-pro", images=1, task="生成封面")
    """
    cost = _estimate_cost(model, input_tokens, output_tokens, images)
    conn = _get_db()
    conn.execute(
        "INSERT INTO cost_log (timestamp, model, input_tokens, output_tokens, images, task, provider, cost) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (time.time(), model, input_tokens, output_tokens, images, task, provider, cost),
    )
    conn.commit()
    conn.close()
    return cost


def get_monthly_stats(year: int | None = None, month: int | None = None) -> dict[str, Any]:
    """获取月度统计"""
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    month_start = datetime(year, month, 1)
    if month == 12:
        month_end = datetime(year + 1, 1, 1)
    else:
        month_end = datetime(year, month + 1, 1)

    conn = _get_db()
    cur = conn.execute(
        "SELECT model, SUM(input_tokens), SUM(output_tokens), SUM(images), SUM(cost), COUNT(*) "
        "FROM cost_log WHERE timestamp >= ? AND timestamp < ? GROUP BY model ORDER BY SUM(cost) DESC",
        (month_start.timestamp(), month_end.timestamp()),
    )
    rows = cur.fetchall()

    total_cost = sum(r[4] for r in rows)
    total_calls = sum(r[5] for r in rows)
    total_input = sum(r[1] for r in rows)
    total_output = sum(r[2] for r in rows)
    total_images = sum(r[3] for r in rows)

    models = []
    for row in rows:
        models.append({
            "model": row[0],
            "input_tokens": row[1],
            "output_tokens": row[2],
            "images": row[3],
            "cost": round(row[4], 4),
            "calls": row[5],
        })

    budget_used = round(total_cost / MONTHLY_BUDGET * 100, 1) if MONTHLY_BUDGET > 0 else 0

    conn.close()
    return {
        "year": year,
        "month": month,
        "total_calls": total_calls,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_images": total_images,
        "total_cost": round(total_cost, 4),
        "budget": MONTHLY_BUDGET,
        "budget_used_pct": budget_used,
        "remaining": round(MONTHLY_BUDGET - total_cost, 4),
        "models": models,
    }


def get_daily_stats(days: int = 7) -> list[dict[str, Any]]:
    """获取每日成本趋势（最近N天）"""
    conn = _get_db()
    results = []
    for i in range(days - 1, -1, -1):
        day = datetime.now() - timedelta(days=i)
        day_start = datetime(day.year, day.month, day.day)
        day_end = day_start + timedelta(days=1)
        cur = conn.execute(
            "SELECT SUM(cost), COUNT(*) FROM cost_log WHERE timestamp >= ? AND timestamp < ?",
            (day_start.timestamp(), day_end.timestamp()),
        )
        row = cur.fetchone()
        cost = round(row[0] or 0, 4)
        calls = row[1] or 0
        results.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "cost": cost,
            "calls": calls,
            "label": f"{day_start.month}/{day_start.day}",
        })
    conn.close()
    return results


def check_alerts() -> list[dict[str, Any]]:
    """检查是否触发预警"""
    stats = get_monthly_stats()
    alerts = []

    if stats["total_cost"] > 0:
        pct = stats["budget_used_pct"]
        if pct >= CRITICAL_THRESHOLD * 100:
            alerts.append({
                "level": "critical",
                "message": f"月度预算已用 {pct}% (¥{stats['total_cost']:.2f}/¥{MONTHLY_BUDGET})，接近上限！",
            })
        elif pct >= ALERT_THRESHOLD * 100:
            alerts.append({
                "level": "warning",
                "message": f"月度预算已用 {pct}% (¥{stats['total_cost']:.2f}/¥{MONTHLY_BUDGET})，请注意控制",
            })

    # 检查今日消耗是否异常（超过日均3倍）
    daily = get_daily_stats(days=3)
    if len(daily) == 3:
        avg = sum(d["cost"] for d in daily[:2]) / 2
        today = daily[-1]["cost"]
        if avg > 0 and today > avg * 3:
            alerts.append({
                "level": "info",
                "message": f"今日消耗 ¥{today:.4f}，是日均 {avg:.4f} 的 {today/avg:.1f} 倍",
            })

    return alerts


def report() -> dict[str, Any]:
    """生成完整月度报告"""
    stats = get_monthly_stats()
    daily = get_daily_stats(days=7)
    alerts = check_alerts()
    stats["daily_trend"] = daily
    stats["alerts"] = alerts
    return stats


def record_hermes_call(tokens_in: int, tokens_out: int, model: str = "deepseek-chat", task: str = "") -> float:
    """Hermes 每次 LLM 调用后记录（便捷方法）"""
    return record(model=model, input_tokens=tokens_in, output_tokens=tokens_out, task=task)


# ── CLI ──────────────────────────────────────────────

def main():
    import sys

    if len(sys.argv) < 2:
        print("用法: python3 -m molib.cost [record|report|alert|daily]")
        print("  record --input N --output N --model M [--task T]")
        print("  report                        # 月度报告")
        print("  alert                         # 预警检查")
        print("  daily [days=7]                # 每日趋势")
        return

    cmd = sys.argv[1]

    if cmd == "record":
        args = _parse_record_args(sys.argv[2:])
        cost = record(**args)
        print(f"✅ 已记录: {args['model']} input={args['input_tokens']} output={args['output_tokens']} → ¥{cost:.6f}")

    elif cmd == "report":
        s = report()
        print(f"📊 月度成本报告 ({s['year']}-{s['month']:02d})")
        print(f"   · 总调用: {s['total_calls']}")
        print(f"   · 总输入: {s['total_input_tokens']:,} tokens")
        print(f"   · 总输出: {s['total_output_tokens']:,} tokens")
        print(f"   · 总成本: ¥{s['total_cost']:.2f}")
        print(f"   · 预算:   ¥{s['budget']:.0f}")
        print(f"   · 使用率: {s['budget_used_pct']}%")
        print(f"   · 剩余:   ¥{s['remaining']:.2f}")
        print()
        if s["models"]:
            print("  📋 按模型:")
            for m in s["models"]:
                print(f"     · {m['model']}: ¥{m['cost']:.4f} ({m['calls']}次调用)")
        if s["alerts"]:
            print()
            for a in s["alerts"]:
                icon = "🔴" if a["level"] == "critical" else "🟡"
                print(f"   {icon} {a['message']}")
        if s.get("daily_trend"):
            print()
            print("  📈 最近7日:")
            for d in s["daily_trend"]:
                bar = "█" * max(1, int(d["cost"] * 100)) if d["cost"] > 0 else "·"
                print(f"     {d['label']}: ¥{d['cost']:.4f} {bar}")

    elif cmd == "alert":
        alerts = check_alerts()
        if not alerts:
            print("✅ 无预警，预算健康")
        else:
            for a in alerts:
                icon = "🔴" if a["level"] == "critical" else ("🟡" if a["level"] == "warning" else "ℹ️")
                print(f"  {icon} {a['message']}")

    elif cmd == "daily":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        trend = get_daily_stats(days=days)
        total = sum(d["cost"] for d in trend)
        print(f"📈 最近 {days} 日趋势 (总计 ¥{total:.4f}):")
        for d in trend:
            bar = "█" * max(1, int(d["cost"] * 100)) if d["cost"] > 0 else "·"
            print(f"  {d['label']}: ¥{d['cost']:.4f} ({d['calls']}次) {bar}")

    else:
        print(f"未知命令: {cmd}")


def _parse_record_args(args: list[str]) -> dict:
    """解析 record 子命令参数"""
    kwargs: dict[str, Any] = {}
    i = 0
    while i < len(args):
        if args[i] == "--input" and i + 1 < len(args):
            kwargs["input_tokens"] = int(args[i + 1])
            i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            kwargs["output_tokens"] = int(args[i + 1])
            i += 2
        elif args[i] == "--model" and i + 1 < len(args):
            kwargs["model"] = args[i + 1]
            i += 2
        elif args[i] == "--task" and i + 1 < len(args):
            kwargs["task"] = args[i + 1]
            i += 2
        elif args[i] == "--images" and i + 1 < len(args):
            kwargs["images"] = int(args[i + 1])
            i += 2
        elif args[i] == "--provider" and i + 1 < len(args):
            kwargs["provider"] = args[i + 1]
            i += 2
        else:
            i += 1
    kwargs.setdefault("model", "unknown")
    kwargs.setdefault("input_tokens", 0)
    kwargs.setdefault("output_tokens", 0)
    return kwargs


if __name__ == "__main__":
    main()
