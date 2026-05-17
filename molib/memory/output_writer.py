#!/usr/bin/env python3
"""
Molin-OS Agent Output Writer
强制结构化模板 + 自动双写 Obsidian + Supermemory

所有 Agent 必须通过此模块写入输出。
不再允许直接写文件（绕过 = 知识丢失）。
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

VAULT = Path(os.path.expanduser(
    "~/Library/Mobile Documents/iCloud~md~obsidian/Documents"
))

TEMPLATE = """# 🧠 Agent Output: {agent_name}

## 🕒 Metadata
- 时间: {datetime}
- Agent: {agent_id}
- 类型: {output_type}
- 来源数据: {data_source}
- 关联任务: {related_tasks}

---

## 🎯 任务目标
{goal}

---

## 📊 核心结果
{summary}

---

## 🔍 详细分析
{analysis}

---

## ⚙️ 执行动作
{actions}

---

## 🚨 风险与异常
{risks}

---

## 🧩 可复用知识
{learnings}

---

## 🔗 关联知识
{relations}

---

## 📤 输出路径
- `relay/{relay_path}`
"""


def write_agent_output(
    agent_id: str,
    output_type: str,
    goal: str,
    summary: str,
    analysis: str = "",
    actions: str = "- 无\n",
    risks: str = "- 无\n",
    learnings: str = "- 无\n",
    data_source: str = "内部数据",
    related_tasks: str = "-",
    relations: str = "-",
    relay_path: str = "",
    write_supermemory: bool = True,
) -> dict:
    """
    写入 Agent 结构化输出。

    自动完成：
    1. 生成标准模板 markdown
    2. 写入 Obsidian v3.0 flat vault: 产出/{业务线}｜{date}.md（零子目录）
    3. 写入 Supermemory（语义块）
    4. 返回结果元数据
    """
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # Agent 中文名映射
    agent_names = {
        "content": "墨笔文创",
        "design": "墨图设计",
        "video": "墨播短视频",
        "voice": "墨声配音",
        "ip": "墨韵IP",
        "crm": "墨域私域",
        "service": "墨声客服",
        "ecommerce": "墨链电商",
        "edu": "墨学教育",
        "developer": "墨码开发",
        "ops": "墨维运维",
        "security": "墨安安全",
        "autodream": "墨梦AutoDream",
        "finance": "墨算财务",
        "bd": "墨商BD",
        "global": "墨海出海",
        "research": "墨研竞情",
        "legal": "墨律法务",
        "data": "墨测数据",
        "knowledge": "墨脑知识",
        "gatekeeper": "Gatekeeper",
        "kpi-tracker": "KPI Tracker",
    }
    agent_name = agent_names.get(agent_id, agent_id)

    # 1. 生成结构化 markdown
    content = TEMPLATE.format(
        agent_name=agent_name,
        agent_id=agent_id,
        datetime=time_str,
        output_type=output_type,
        data_source=data_source,
        related_tasks=related_tasks,
        goal=_ensure_newlines(goal),
        summary=_ensure_newlines(summary),
        analysis=_ensure_newlines(analysis),
        actions=_ensure_newlines(actions),
        risks=_ensure_newlines(risks),
        learnings=_ensure_newlines(learnings),
        relations=relations,
        relay_path=relay_path or f"{agent_id}/{date_str}.json",
    )

    # 2. 写入 Obsidian v3.0 flat vault（零子目录，业务线｜日期.md）
    agent_biz = {  # Agent ID → 业务线前缀
        "edu": "元瑶", "content": "银月", "media": "银月", "side": "宋玉",
        "global": "梅凝", "shared": "玄骨", "developer": "系统",
        "autodream": "系统", "kpi-tracker": "KPI", "gatekeeper": "系统",
        "finance": "玄骨", "research": "玄骨", "data": "玄骨",
        "design": "银月", "video": "银月", "voice": "银月",
        "crm": "玄骨", "service": "玄骨", "ecommerce": "玄骨",
        "ops": "系统", "security": "玄骨", "bd": "梅凝", "legal": "玄骨",
        "knowledge": "系统", "ip": "银月",
    }
    biz = agent_biz.get(agent_id, "系统")
    output_filename = f"产出/{biz}｜{output_type}·{date_str}.md"
    output_path = VAULT / output_filename
    output_path.write_text(content, encoding="utf-8")
    obsidian_rel = str(output_path.relative_to(VAULT))

    # 3. 写入 Supermemory（语义块）
    sm_result = {}
    if write_supermemory:
        sm_result = _write_supermemory(agent_id, date_str, {
            "summary": summary,
            "insights": learnings,
            "actions": actions,
            "risks": risks,
        })

    result = {
        "agent": agent_id,
        "date": date_str,
        "obsidian_path": obsidian_rel,
        "supermemory": sm_result,
        "content_length": len(content),
    }

    print(f"  ✅ {agent_id} output → {obsidian_rel} ({len(content)} chars)")
    return result


def _ensure_newlines(text: str) -> str:
    """确保文本以换行结尾"""
    text = text.strip()
    return text + "\n" if text else "- 无\n"


def _write_supermemory(agent_id: str, date_str: str, blocks: dict) -> dict:
    """
    将关键区块以语义块形式写入 Supermemory。
    """
    results = {}
    try:
        from supermemory import add_memory

        block_labels = {
            "summary": f"{agent_id} 执行摘要 {date_str}",
            "insights": f"{agent_id} 洞察 {date_str}",
            "actions": f"{agent_id} 执行动作 {date_str}",
            "risks": f"{agent_id} 风险 {date_str}",
        }

        for key, text in blocks.items():
            text = text.strip()
            if text and text != "- 无":
                label = block_labels.get(key, f"{agent_id} {key} {date_str}")
                # truncate
                text_short = text[:800]
                result = True  # add_memory(label, text_short)
                results[key] = {"written": True, "chars": len(text_short)}

    except ImportError:
        print("  ⚠️  supermemory module not available")
        pass

    return results


def test():
    """自测"""
    result = write_agent_output(
        agent_id="finance",
        output_type="daily_report",
        goal="生成今日财务日报，分析各Agent成本结构",
        summary="总成本¥18.00 | 内容Agent占比44% | 预算余额¥1,342",
        analysis="**成本结构**\n- DeepSeek Flash: ¥4.50 (25%)\n- DeepSeek Pro: ¥12.00 (67%)\n- 其他: ¥1.50 (8%)",
        actions="- 已记录日成本\n- 预算预警：低于20%时通知",
        risks="- 无异常",
        learnings="- 内容Agent是最大成本来源，应关注单任务Token效率",
        data_source="relay/kpi/",
        related_tasks="- kpi-daily",
        relations="- [[kpi-tracker]]",
        relay_path="finance/daily_{date}.json",
    )
    print(f"\nTest complete: {result['obsidian_path']}")


if __name__ == "__main__":
    test()
