"""墨麟CEO 人性化对话 — 时间感知 + 状态摘要"""
import datetime
from typing import List


def get_greeting() -> str:
    h = datetime.datetime.now().hour
    if h < 6:   return "夜深了，老板"
    if h < 12:  return "早安，老板"
    if h < 14:  return "午好"
    if h < 18:  return "下午好"
    return "晚上好，老板"


def get_status_prefix(cost_cny: float, elapsed: float, agencies: list) -> str:
    """在回复顶部注入状态摘要"""
    ag_str = "、".join(agencies[:3])
    if len(agencies) > 3:
        ag_str += f" 等{len(agencies)}个团队"
    return (
        f"📋 调用了 {ag_str}\n"
        f"⏱️ 耗时 {int(elapsed)}s · 花费 ¥{cost_cny:.4f}\n\n"
    )
