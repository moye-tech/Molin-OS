"""Planning Tool — 从 deepagents (langchain-ai/deepagents ⭐22.4K) 吸收的规划工具

将复杂任务分解为结构化 todo 列表，每个 todo 有状态追踪。
AI 通过 write_todos 工具自我管理任务进度。

吸收来源: deepagents TodoListMiddleware + langchain.agents.middleware.todo
升级前: 纯 Hermes todo 工具（仅看/写，无状态机）
升级后: todo 状态机（pending→in_progress→completed）+ CLI plan 命令 + AI 端自动规划

设计模式:
  - PlanningState: {todos: list[Todo]} — 结构化任务列表
  - write_todos: AI 通过此工具更新 todo 状态
  - TodoPlanner: Python 端创建和管理计划
  - plan CLI: 从自然语言描述生成结构化计划
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal

# ──────────────────────────────────────────────
# 类型定义（复刻自 deepagents Todo/TodoListMiddleware）
# ──────────────────────────────────────────────

TodoStatus = Literal["pending", "in_progress", "completed"]


@dataclass
class Todo:
    """单个 todo 项"""

    content: str
    """任务描述"""
    status: TodoStatus = "pending"
    """当前状态: pending / in_progress / completed"""

    def to_dict(self) -> dict:
        return {"content": self.content, "status": self.status}

    @classmethod
    def from_dict(cls, d: dict) -> "Todo":
        return cls(content=d.get("content", ""), status=d.get("status", "pending"))  # type: ignore


@dataclass
class Plan:
    """一个完整的任务计划"""

    title: str
    """计划标题"""
    todos: list[Todo] = field(default_factory=list)
    """任务列表"""
    created_at: str = ""
    """创建时间（ISO 格式）"""
    updated_at: str = ""
    """最后更新时间"""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "todos": [t.to_dict() for t in self.todos],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "stats": self.stats(),
        }

    def stats(self) -> dict:
        """返回任务统计"""
        total = len(self.todos)
        completed = sum(1 for t in self.todos if t.status == "completed")
        in_progress = sum(1 for t in self.todos if t.status == "in_progress")
        pending = sum(1 for t in self.todos if t.status == "pending")
        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "progress_pct": round(completed / total * 100, 1) if total > 0 else 0,
        }

    def update_status(self, content: str, status: TodoStatus) -> bool:
        """更新某个 todo 的状态。返回是否找到并更新。"""
        for todo in self.todos:
            if todo.content == content:
                todo.status = status
                self.updated_at = datetime.now().isoformat()
                return True
        return False

    def get_summary(self) -> str:
        """返回人类可读的摘要"""
        s = self.stats()
        lines = [
            f"📋 {self.title}",
            f"   {s['completed']}/{s['total']} 完成 ({s['progress_pct']}%)",
        ]
        for todo in self.todos:
            icon = {"pending": "⬜", "in_progress": "🔄", "completed": "✅"}.get(
                todo.status, "⬜"
            )
            lines.append(f"  {icon} {todo.content}")
        return "\n".join(lines)


# ──────────────────────────────────────────────
# 持久化
# ──────────────────────────────────────────────

PLANS_DIR = Path.home() / ".hermes" / "plans"


def _ensure_plans_dir() -> Path:
    PLANS_DIR.mkdir(parents=True, exist_ok=True)
    return PLANS_DIR


def list_plans() -> list[dict]:
    """列出所有已保存的计划"""
    d = _ensure_plans_dir()
    plans = []
    for f in sorted(d.glob("*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            plans.append(data)
        except Exception:
            continue
    return plans


def load_plan(plan_id: str) -> Plan | None:
    """按 ID 加载计划"""
    path = _ensure_plans_dir() / f"{plan_id}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Plan(
            title=data.get("title", ""),
            todos=[Todo.from_dict(t) for t in data.get("todos", [])],
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )
    except Exception:
        return None


def save_plan(plan: Plan) -> str:
    """保存计划，返回 plan_id（基于标题生成的文件名）"""
    plan_id = re.sub(r"[^a-z0-9-]", "", plan.title.lower().replace(" ", "-"))[:48]
    if not plan_id:
        plan_id = f"plan-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    path = _ensure_plans_dir() / f"{plan_id}.json"
    path.write_text(json.dumps(plan.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return plan_id


# ──────────────────────────────────────────────
# 任务分解 — 从自然语言生成计划
# ──────────────────────────────────────────────

def decompose_task(description: str, auto_split: bool = True) -> Plan:
    """将自然语言任务描述分解为结构化计划。

    支持两种模式:
    1. 自动拆分 - 按标点/换行/序号拆分为子任务
    2. 用户指定 - description 本身就是 todo 列表

    Args:
        description: 任务描述或待办事项列表
        auto_split: 是否自动拆分（默认 True）

    Returns:
        Plan 对象
    """
    title = description.split("\n")[0][:64] if "\n" in description else description[:64]

    if not auto_split:
        return Plan(title=title, todos=[Todo(content=description.strip(), status="pending")])

    # 按换行拆分
    lines = description.strip().split("\n")
    todos: list[Todo] = []

    # 尝试按换行拆分的序号列表
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # 去除序号前缀: "1." "1)" "- " "* " "• "
        cleaned = re.sub(r"^\s*(?:\d+[\.\)、]\s*|[-*•]\s+|[\u4e00-\u9fff]+[：:]\s*)", "", line)
        if cleaned:
            todos.append(Todo(content=cleaned, status="pending"))

    # 如果第一行没被拆开（单行描述），尝试按序号或标点拆分
    if len(todos) <= 1:
        # 按序号分割: "1. xxx 2. xxx 3. xxx"
        numbered = re.split(r"\d+[\.\)、]+\s*", description)
        numbered = [p.strip() for p in numbered if p.strip() and len(p.strip()) > 1]
        if len(numbered) > 1:
            todos = [Todo(content=p, status="pending") for p in numbered]
        elif len(description) > 60:
            # 按标点分割
            parts = re.split(r"[；;。！？\n]", description)
            for part in parts:
                part = part.strip()
                if part and len(part) > 4:
                    todos.append(Todo(content=part, status="pending"))
                if len(todos) > 10:
                    break

    if not todos:
        todos = [Todo(content=description.strip(), status="pending")]

    # 提取标题：使用第一行或整段的前48字
    title = todos[0].content[:48] + ("..." if len(todos[0].content) > 48 else "")

    return Plan(title=title, todos=todos)


# ──────────────────────────────────────────────
# CLI 命令
# ──────────────────────────────────────────────

def cmd_create(args: list[str]) -> dict:
    """创建新计划"""
    description = " ".join(args) if args else ""
    if not description:
        return {"error": "请提供任务描述"}

    plan = decompose_task(description)
    plan_id = save_plan(plan)
    return {
        "status": "ok",
        "plan_id": plan_id,
        "plan": plan.to_dict(),
        "summary": plan.get_summary(),
    }


def cmd_list(args: list[str]) -> dict:
    """列出所有计划"""
    plans = list_plans()
    return {"status": "ok", "plans": plans}


def cmd_show(args: list[str]) -> dict:
    """显示某个计划的详情"""
    if not args:
        return {"error": "请提供 plan_id"}
    plan_id = args[0]
    plan = load_plan(plan_id)
    if not plan:
        return {"error": f"计划不存在: {plan_id}"}
    return {
        "status": "ok",
        "plan": plan.to_dict(),
        "summary": plan.get_summary(),
    }


def cmd_update(args: list[str]) -> dict:
    """更新 todo 状态: <plan_id> <todo_content> <new_status>"""
    if len(args) < 3:
        return {"error": "用法: plan update <plan_id> <todo_content> <pending|in_progress|completed>"}

    plan_id = args[0]
    todo_content = args[1]
    new_status = args[2]

    if new_status not in ("pending", "in_progress", "completed"):
        return {"error": f"无效状态: {new_status}，支持: pending / in_progress / completed"}

    plan = load_plan(plan_id)
    if not plan:
        return {"error": f"计划不存在: {plan_id}"}

    if not plan.update_status(todo_content, new_status):
        return {"error": f"未找到 todo: {todo_content}"}

    save_plan(plan)
    return {
        "status": "ok",
        "plan_id": plan_id,
        "plan": plan.to_dict(),
        "summary": plan.get_summary(),
    }


def cmd_stats(args: list[str]) -> dict:
    """汇总统计所有计划的进度"""
    plans = list_plans()
    total_todos = 0
    total_completed = 0
    total_in_progress = 0
    for p in plans:
        total_todos += p.get("stats", {}).get("total", 0)
        total_completed += p.get("stats", {}).get("completed", 0)
        total_in_progress += p.get("stats", {}).get("in_progress", 0)

    return {
        "status": "ok",
        "total_plans": len(plans),
        "total_todos": total_todos,
        "total_completed": total_completed,
        "total_in_progress": total_in_progress,
        "overall_progress_pct": round(total_completed / total_todos * 100, 1) if total_todos > 0 else 0,
    }


def main(args: list[str]) -> dict:
    """plan 命令入口"""
    if not args or args[0] in ("help", "--help", "-h"):
        return {
            "usage": "python -m molib plan <subcommand> [args]",
            "subcommands": {
                "create <描述>": "从任务描述创建计划",
                "list": "列出所有计划",
                "show <plan_id>": "查看计划详情",
                "update <plan_id> <todo> <status>": "更新 todo 状态",
                "stats": "统计所有计划进度",
                "decompose <描述>": "仅分解任务（不保存）",
            },
        }

    subcmd = args[0]
    rest = args[1:]

    dispatch = {
        "create": cmd_create,
        "list": cmd_list,
        "show": cmd_show,
        "update": cmd_update,
        "stats": cmd_stats,
        "decompose": lambda a: {
            "status": "ok",
            "plan": decompose_task(" ".join(a) if a else "").to_dict(),
        },
    }

    handler = dispatch.get(subcmd)
    if handler:
        return handler(rest)

    return {"error": f"未知子命令: {subcmd}，支持: create / list / show / update / stats / decompose"}
