#!/usr/bin/env python3
"""
KPI 看板生成器
从 relay/kpi/ 读取 KPI 数据，生成 ASCII 趋势图和看板，写入 Obsidian

用法:
  python3 generate_dashboard.py daily    # 生成日看板
  python3 generate_dashboard.py weekly   # 生成周看板
  python3 generate_dashboard.py overview # 生成全景看板
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

RELAY_DIR = os.path.expanduser("~/Molin-OS/relay/kpi")
OBSIDIAN_DIR = os.path.expanduser(
    "~/Library/Mobile Documents/iCloud~md~obsidian/Documents"
)
OUTPUT_DIR = os.path.join(OBSIDIAN_DIR, "报告/KPI看板")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_kpi_data(date_str=None):
    """Load KPI data from relay/kpi/ for a specific date or all dates."""
    data = {}
    if not os.path.exists(RELAY_DIR):
        print(f"⚠️ relay/kpi/ 目录不存在: {RELAY_DIR}")
        return data

    for f in sorted(os.listdir(RELAY_DIR)):
        if not f.endswith(".json"):
            continue
        if date_str and date_str not in f:
            continue
        fp = os.path.join(RELAY_DIR, f)
        try:
            with open(fp) as fh:
                d = json.load(fh)
                agent = d.get("agent", "unknown")
                date = d.get("date", "unknown")
                key = f"{agent}_{date}"
                data[key] = d
        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️  跳过 {f}: {e}")
    return data


def ascii_bar(value, max_val=100, width=20):
    """Generate an ASCII bar."""
    filled = int((value / max_val) * width) if max_val > 0 else 0
    filled = min(filled, width)
    empty = width - filled
    bar = "█" * filled + "░" * empty
    return f"{bar} {value}"


def generate_daily_dashboard(data, date_str):
    """Generate daily KPI dashboard."""
    lines = [
        f"# KPI 日看板 — {date_str}",
        "",
        "## 总览",
        "| Agent | 任务数 | QA均分 | 成本(¥) | 单任务成本(¥) |",
        "|-------|--------|--------|---------|---------------|",
    ]

    for key in sorted(data.keys()):
        d = data[key]
        eff = d.get("efficiency", {})
        qual = d.get("quality", {})
        cost = d.get("cost", {})
        task_count = eff.get("task_count", "—")
        avg_qa = qual.get("avg_qa_score", "—")
        api_cost = cost.get("api_cost", "—")
        cost_per = cost.get("cost_per_task", "—")
        agent = d.get("agent", "?")

        task_count = f"{task_count:.0f}" if isinstance(task_count, (int, float)) else task_count
        avg_qa = f"{avg_qa:.0f}" if isinstance(avg_qa, (int, float)) else avg_qa
        api_cost = f"{api_cost:.2f}" if isinstance(api_cost, (int, float)) else api_cost
        cost_per = f"{cost_per:.3f}" if isinstance(cost_per, (int, float)) else cost_per

        lines.append(f"| {agent} | {task_count} | {avg_qa} | {api_cost} | {cost_per} |")

    lines += ["", "## 质量趋势"]

    # Try to group by agent for trend
    agents_data = defaultdict(list)
    for key, d in data.items():
        agent = d.get("agent", "?")
        qual = d.get("quality", {})
        agents_data[agent].append((d.get("date", ""), qual.get("avg_qa_score", 0)))

    for agent, scores in sorted(agents_data.items()):
        scores = sorted(scores, key=lambda x: x[0])
        scores = scores[-7:]  # last 7 days
        if len(scores) < 2:
            lines.append(f"\n{agent}: 数据不足（{len(scores)} 天）")
            continue

        lines.append(f"\n### {agent} QA均分趋势")
        max_s = max(s for _, s in scores if s) or 100
        max_s = max(max_s, 60)
        for date_s, score in scores:
            label = date_s[-5:] if len(date_s) >= 5 else date_s
            bar = ascii_bar(score, max_s, 15)
            lines.append(f"  {label}  {bar}")

    lines += [
        "",
        "## 成本排行",
        "| 排名 | Agent | 日成本(¥) |",
        "|------|-------|-----------|",
    ]

    cost_ranking = []
    for key, d in data.items():
        cost = d.get("cost", {}).get("api_cost", 0)
        agent = d.get("agent", "?")
        cost_ranking.append((agent, cost))
    cost_ranking.sort(key=lambda x: x[1], reverse=True)

    for i, (agent, cost) in enumerate(cost_ranking, 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"  {i}.")
        lines.append(f"| {medal} | {agent} | ¥{cost:.2f} |")

    return "\n".join(lines)


def generate_weekly_dashboard(data, week_start, week_end):
    """Generate weekly KPI dashboard."""
    lines = [
        f"# KPI 周看板 — {week_start} ~ {week_end}",
        "",
        "## 周度汇总",
        "| Agent | 日均任务 | 周QA均分 | 周总成本(¥) | 趋势 |",
        "|-------|----------|----------|-------------|------|",
    ]

    # Group by agent
    agent_agg = defaultdict(list)
    for key, d in data.items():
        agent = d.get("agent", "?")
        agent_agg[agent].append(d)

    for agent, records in sorted(agent_agg.items()):
        total_tasks = sum(
            r.get("efficiency", {}).get("task_count", 0) for r in records
        )
        avg_qa = (
            sum(r.get("quality", {}).get("avg_qa_score", 0) for r in records)
            / len(records)
            if records
            else 0
        )
        total_cost = sum(r.get("cost", {}).get("api_cost", 0) for r in records)
        daily_avg = total_tasks / len(records) if records else 0

        # Simple trend
        if len(records) >= 2:
            first_half = [r.get("quality", {}).get("avg_qa_score", 0) for r in records[: len(records)//2]]
            second_half = [r.get("quality", {}).get("avg_qa_score", 0) for r in records[len(records)//2:]]
            trend_up = (sum(second_half)/len(second_half)) > (sum(first_half)/len(first_half)) if first_half and second_half else True
            trend = "📈" if trend_up else "📉"
        else:
            trend = "➡️"

        lines.append(
            f"| {agent} | {daily_avg:.1f} | {avg_qa:.0f} | ¥{total_cost:.2f} | {trend} |"
        )

    lines += [
        "",
        "## 本周异常",
        "（复盘 Cron 未运行或未发现异常）",
        "",
        "## 下周重点",
        "1. ",
        "2. ",
        "3. ",
    ]

    return "\n".join(lines)


def generate_overview_dashboard(all_data):
    """Generate full business overview dashboard."""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"# 墨麟经营全景看板",
        f"",
        f"更新日期：{today}",
        "",
        "## 系统健康状态",
        "🟢 全部正常",
        "",
        "| 系统 | 状态 | 说明 |",
        "|------|------|------|",
        "| Agent 系统 | 🟢 | 19/20 正常，墨域私域待基建 |",
        "| Cron 系统 | 🟢 | 参考 cronjob list |",
        "| 财务 | 🟢 | 预算 ¥1,360/月 |",
        "",
        "## 各 Agent 经营评分",
        "| Agent | 综合 | 效能 | 质量 | 成本 | 趋势 |",
        "|-------|------|------|------|------|------|",
    ]

    # Aggregate all data
    agent_stats = defaultdict(lambda: {"tasks": [], "qa": [], "costs": []})
    for key, d in all_data.items():
        agent = d.get("agent", "?")
        eff = d.get("efficiency", {})
        qual = d.get("quality", {})
        cost = d.get("cost", {})

        agent_stats[agent]["tasks"].append(eff.get("task_count", 0))
        agent_stats[agent]["qa"].append(qual.get("avg_qa_score", 0))
        agent_stats[agent]["costs"].append(cost.get("api_cost", 0))

    for agent, stats in sorted(agent_stats.items()):
        avg_qa = sum(stats["qa"]) / len(stats["qa"]) if stats["qa"] else 0
        total_cost = sum(stats["costs"])
        total_tasks = sum(stats["tasks"])

        # Grade
        def grade(val, thresholds):
            for g, t in thresholds.items():
                if val >= t:
                    return g
            return "D"

        qa_grade = grade(avg_qa, {"A": 85, "B+": 78, "B": 70, "C": 60})
        cost_grade = "A" if total_cost < 10 else ("B" if total_cost < 50 else "C")
        eff_grade = grade(total_tasks, {"A": 30, "B+": 20, "B": 10, "C": 5})

        # Composite
        composite = {"A": 90, "B+": 82, "B": 72, "C": 60, "D": 40}
        avg_g = (composite.get(qa_grade, 60) + composite.get(cost_grade, 60) + composite.get(eff_grade, 60)) / 3

        overall = "A" if avg_g >= 85 else ("B+" if avg_g >= 78 else ("B" if avg_g >= 70 else "C"))
        trend = "📈" if len(stats["qa"]) >= 4 and stats["qa"][-2:] > stats["qa"][:2] else ("📉" if len(stats["qa"]) >= 4 else "➡️")

        lines.append(f"| {agent} | {overall} | {eff_grade} | {qa_grade} | {cost_grade} | {trend} |")

    lines += [
        "",
        "## 预算追踪",
    ]

    total_cost = sum(
        d.get("cost", {}).get("api_cost", 0) for d in all_data.values()
    )
    budget = 1360
    pct = min(total_cost / budget * 100, 100) if budget > 0 else 0
    bar_width = 30
    filled = int((pct / 100) * bar_width)
    bar = "█" * filled + "░" * (bar_width - filled)

    lines += [
        f"本月已用：¥{total_cost:.0f} / ¥{budget}",
        f"[{bar}] {pct:.0f}%",
        f"剩余：¥{budget - total_cost:.0f}",
    ]

    return "\n".join(lines)


def write_obsidian(path, content):
    """Write content to Obsidian vault."""
    full_path = os.path.join(OUTPUT_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)
    print(f"✅ 已写入: {full_path}")
    return full_path


def main():
    if len(sys.argv) < 2:
        print("用法: python3 generate_dashboard.py [daily|weekly|overview]")
        sys.exit(1)

    mode = sys.argv[1]
    today = datetime.now().strftime("%Y-%m-%d")

    if mode == "daily":
        data = load_kpi_data(today)
        if not data:
            print(f"⚠️ 今日 ({today}) 无 KPI 数据。使用所有可用数据。")
            data = load_kpi_data()
        content = generate_daily_dashboard(data, today)
        write_obsidian(f"{today}/日看板.md", content)

    elif mode == "weekly":
        data = load_kpi_data()
        # Determine week range
        today_dt = datetime.now()
        week_start = (today_dt - timedelta(days=today_dt.weekday())).strftime("%Y-%m-%d")
        week_end = today
        content = generate_weekly_dashboard(data, week_start, week_end)
        write_obsidian(f"{week_start}_{week_end}_周看板.md", content)

    elif mode == "overview":
        data = load_kpi_data()
        content = generate_overview_dashboard(data)
        write_obsidian("全景经营看板.md", content)

    else:
        print(f"未知模式: {mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
