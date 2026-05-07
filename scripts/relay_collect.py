#!/usr/bin/env python3
"""
Cron 数据采集脚本 — 在每个 cron job 执行前收集上下文数据，写入接力文件。
用于 cronjob 的 script 参数。

用法（在 cronjob create/update 的 script 中指定）：
    cronjob/relay_collect.py

输出到 stdout，被 cron 注入到 prompt 前置上下文中。
"""
import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.expanduser("~/hermes-os"))
from molib.relay import RelayReader

today = date.today().isoformat()
reader = RelayReader()

print(f"# 墨麟OS 接力数据预采集 — {today}")
print()

# 读取今天已有的接力数据
relays = reader.read_all(today)
found_count = sum(1 for v in relays.values() if v is not None)
print(f"今日接力文件: {found_count}/8 个已就绪")
print()

# 逐个展示已有的接力数据
for prefix, label in [
    ("intelligence", "🕐 08:00 墨思情报"),
    ("content", "🕐 09:00 墨迹内容"),
    ("briefing", "🕐 09:00 CEO简报"),
    ("growth", "🕐 10:00 墨增增长"),
    ("governance", "🕐 10:00 墨盾治理"),
    ("crm", "🕐 11:00 墨域私域"),
    ("order", "🕐 14:00 墨单订单"),
    ("ceo_review", "🕐 17:00 CEO复盘"),
]:
    data = relays.get(prefix)
    if data:
        summary = data.get("summary", data.get("summary", "N/A"))
        errors = data.get("errors", [])
        err_flag = " ⚠️" if errors else ""
        print(f"[{label}]{err_flag}")
        print(f"  摘要: {summary}")
        if errors:
            print(f"  错误: {'; '.join(errors)}")
        # 只输出摘要不输出完整 data（太长会占上下文）
        print()
    else:
        print(f"[{label}] ⏳ 未执行")
        print()
