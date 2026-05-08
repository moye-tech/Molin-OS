"""
Hermes Supermemory 自动归档脚本
每次对话/任务完成后，自动将关键信息保存到 Supermemory 云。

用法：
    from scripts.auto_archive import archive_task_result
    
    archive_task_result(
        title="吸收SOP引擎",
        summary="已完成SOP引擎的YAML流程定义吸收",
        tags=["吸收", "SOP引擎"],
        details={"模块": "sop/engine.py", "行数": 435, "状态": "测试通过"}
    )
"""
from __future__ import annotations

import sys
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from molib.infra.supermemory import save_memory


def archive_task_result(
    title: str,
    summary: str,
    tags: Optional[List[str]] = None,
    details: Optional[Dict[str, Any]] = None,
):
    """
    归档任务执行结果到 Supermemory。

    Args:
        title: 任务标题（简短）
        summary: 任务摘要（2-5句话）
        tags: 标签列表（如 ["吸收", "SOP引擎"]）
        details: 详细信息字典（可选）
    """
    content_parts = [f"# {title}", "", summary]

    if details:
        content_parts.append("")
        content_parts.append("**详情:**")
        for key, value in details.items():
            content_parts.append(f"- {key}: {value}")

    content_parts.append("")
    content_parts.append(f"_归档时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}_")

    content = "\n".join(content_parts)
    all_tags = (tags or []) + ["归档"]

    doc_id = save_memory(content, title=title, tags=all_tags, source="auto_archive")
    return doc_id


if __name__ == "__main__":
    # 命令行用法
    import argparse

    parser = argparse.ArgumentParser(description="归档任务结果到 Supermemory")
    parser.add_argument("--title", required=True, help="任务标题")
    parser.add_argument("--summary", required=True, help="任务摘要")
    parser.add_argument(
        "--tags", nargs="+", default=[], help="标签列表（空格分隔）"
    )

    args = parser.parse_args()
    doc_id = archive_task_result(
        title=args.title, summary=args.summary, tags=args.tags
    )
    print(f"✅ 已归档: {doc_id}")
