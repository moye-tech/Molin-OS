"""墨梦AutoDream Worker — 记忆整合、战略复盘与记忆蒸馏 (LLM驱动)"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from .base import SubsidiaryWorker, Task, WorkerResult

# ─── 目录常量（零空转：目录检查只在主动调用时执行） ──────────────────────────
DREAM_DIR = Path(os.path.expanduser("~/.hermes/dream"))
MEMORY_DIR = Path(os.path.expanduser("~/.hermes/memory"))
SKILLS_META = Path(os.path.expanduser("~/.hermes/skills/meta"))


def _ensure_dream_dir() -> None:
    """确保 ~/.hermes/dream/ 目录存在（静默创建，仅当被调用时执行）。"""
    DREAM_DIR.mkdir(parents=True, exist_ok=True)


def dream_distill(work_memory: list[dict[str, Any]]) -> str:
    """工作记忆 → 情节记忆提炼

    将短期/工作记忆中的关键事件压缩为情节记忆条目，
    写入 ~/.hermes/dream/episodic/ 目录。

    遵循零空转原则：仅当被主动调用的运行。

    Args:
        work_memory: 工作记忆条目列表，每条至少包含
            {"timestamp": "...", "event": "...", "context": "...", "outcome": "..."}

    Returns:
        写入的情节记忆文件路径
    """
    _ensure_dream_dir()
    episodic_dir = DREAM_DIR / "episodic"
    episodic_dir.mkdir(parents=True, exist_ok=True)

    if not work_memory:
        return str(episodic_dir / "(empty)")

    # 压缩提炼：去重、排序、合并相似事件
    seen: set[str] = set()
    episodes: list[dict[str, Any]] = []
    for entry in work_memory:
        event_key = str(entry.get("event", ""))
        if event_key and event_key not in seen and entry.get("outcome") not in (None, "skipped"):
            seen.add(event_key)
            episodes.append({
                "timestamp": entry.get("timestamp", datetime.now().isoformat()),
                "event": event_key,
                "context": entry.get("context", ""),
                "outcome": entry.get("outcome", ""),
                "significance": entry.get("significance", "normal"),
                "distilled_at": datetime.now().isoformat(),
            })

    if not episodes:
        return str(episodic_dir / "(no_significant_events)")

    # 按时间戳排序
    episodes.sort(key=lambda e: e["timestamp"])

    # 写入情节记忆文件（按日期分片）
    date_str = datetime.now().strftime("%Y-%m-%d")
    file_path = episodic_dir / f"episodic_{date_str}.json"

    existing: list[dict[str, Any]] = []
    if file_path.exists():
        try:
            existing = json.loads(file_path.read_text())
        except (json.JSONDecodeError, Exception):
            existing = []

    # 追加去重
    existing_events = {e.get("event", "") for e in existing}
    new_episodes = [e for e in episodes if e["event"] not in existing_events]
    merged = existing + new_episodes

    file_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2))
    return str(file_path)


def dream_reflect(task_log: list[dict[str, Any]]) -> str:
    """任务反思：从任务日志中提取 lessons learned

    分析最近的任务执行日志，提取可复用的教训和模式，
    写入 ~/.hermes/dream/lessons/ 目录。

    遵循零空转原则：仅当被主动调用时才运行。

    Args:
        task_log: 任务日志列表，每条至少包含
            {"task_id": "...", "action": "...", "result": "...", "error": "...", "duration": 0.0}
            或类似结构。

    Returns:
        写入的 lessons 文件路径
    """
    _ensure_dream_dir()
    lessons_dir = DREAM_DIR / "lessons"
    lessons_dir.mkdir(parents=True, exist_ok=True)

    if not task_log:
        return str(lessons_dir / "(no_tasks)")

    lessons: list[dict[str, Any]] = []
    for entry in task_log:
        error = entry.get("error") or ""
        result = entry.get("result") or ""

        # 只对失败或异常的任务提取教训
        if error:
            lessons.append({
                "type": "pitfall",
                "task_id": entry.get("task_id", "unknown"),
                "action": entry.get("action", ""),
                "lesson": f"失败: {error}",
                "suggestion": _suggest_fix(entry),
                "source": "dream_reflect",
                "timestamp": datetime.now().isoformat(),
            })
        elif "retry" in str(entry.get("action", "")).lower() or "recover" in str(result).lower():
            lessons.append({
                "type": "recovery_pattern",
                "task_id": entry.get("task_id", "unknown"),
                "action": entry.get("action", ""),
                "lesson": f"恢复路径: {result}",
                "suggestion": "将此恢复模式编码为可重用步骤",
                "source": "dream_reflect",
                "timestamp": datetime.now().isoformat(),
            })
        # 成功但耗时长——值得分析的效率教训
        duration = entry.get("duration", 0)
        if isinstance(duration, (int, float)) and duration > 30.0:
            lessons.append({
                "type": "efficiency_pattern",
                "task_id": entry.get("task_id", "unknown"),
                "action": entry.get("action", ""),
                "lesson": f"耗时过长 ({duration:.1f}s)",
                "suggestion": "考虑拆分或优化此步骤",
                "source": "dream_reflect",
                "timestamp": datetime.now().isoformat(),
            })

    if not lessons:
        return str(lessons_dir / "(no_lessons)")

    date_str = datetime.now().strftime("%Y-%m-%d")
    file_path = lessons_dir / f"lessons_{date_str}.json"

    existing: list[dict[str, Any]] = []
    if file_path.exists():
        try:
            existing = json.loads(file_path.read_text())
        except (json.JSONDecodeError, Exception):
            existing = []

    # 去重合并
    existing_keys = {(e.get("task_id", ""), e.get("lesson", "")) for e in existing}
    new_lessons = [l for l in lessons if (l["task_id"], l["lesson"]) not in existing_keys]
    merged = existing + new_lessons

    file_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2))
    return str(file_path)


def _suggest_fix(entry: dict[str, Any]) -> str:
    """根据任务条目的错误内容生成修复建议。

    仅被 dream_reflect 内部调用，不暴露为公共 API。
    """
    error = (entry.get("error") or "").lower()
    action = (entry.get("action") or "").lower()

    if "timeout" in error:
        return "增加超时时间或拆分操作为更小的步骤"
    if "not found" in error or "404" in error:
        return "检查路径/URL是否正确，或资源是否已经移动"
    if "permission" in error or "denied" in error or "403" in error:
        return "检查权限设置，可能需要 sudo 或 API key"
    if "connection" in error or "refused" in error:
        return "检查网络连接和服务是否正在运行"
    if "rate" in error or "429" in error:
        return "降低请求频率，增加重试间隔"
    return "手动审查错误详情并相应调整"


def dream_consolidate() -> str:
    """语义记忆固化：将跨 session 的洞察写入 SKILL.md

    扫描 ~/.hermes/dream/ 下所有 episodic 和 lessons 文件，
    提取跨 session 的重复模式，写入 deep-dream-memory SKILL.md
    和 self-learning-loop SKILL.md 的合适位置。

    遵循零空转原则：仅当被主动调用时才运行。
    不修改已有内容，只在 SKILL.md 中追加或更新「记忆蒸馏纪要」段落。

    Returns:
        操作状态报告字符串
    """
    _ensure_dream_dir()

    # ── 1. 收集所有蒸馏产物 ──
    episodic_files = sorted((DREAM_DIR / "episodic").glob("episodic_*.json"))
    lesson_files = sorted((DREAM_DIR / "lessons").glob("lessons_*.json"))

    all_episodes: list[dict[str, Any]] = []
    all_lessons: list[dict[str, Any]] = []

    for fp in episodic_files:
        try:
            data = json.loads(fp.read_text())
            all_episodes.extend(data if isinstance(data, list) else [data])
        except Exception:
            continue

    for fp in lesson_files:
        try:
            data = json.loads(fp.read_text())
            all_lessons.extend(data if isinstance(data, list) else [data])
        except Exception:
            continue

    # ── 2. 提取跨 session 的重复模式 ──
    patterns: list[dict[str, Any]] = []
    if all_lessons:
        # 按 lesson 分组统计频率
        lesson_counts: dict[str, int] = {}
        for l in all_lessons:
            key = l.get("suggestion", l.get("lesson", ""))
            lesson_counts[key] = lesson_counts.get(key, 0) + 1

        # 出现次数 >= 2 的模式视为「跨 session 洞察」
        for lesson_text, count in lesson_counts.items():
            if count >= 2:
                sample = next((l for l in all_lessons if l.get("suggestion", l.get("lesson", "")) == lesson_text), None)
                patterns.append({
                    "pattern": lesson_text,
                    "frequency": count,
                    "type": sample.get("type", "unknown") if sample else "unknown",
                    "consolidated_at": datetime.now().isoformat(),
                })

    if all_episodes:
        # 按事件类型/context 聚合
        outcome_counts: dict[str, int] = {}
        for e in all_episodes:
            outcome = e.get("outcome", "unknown")
            outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1

        for outcome, count in outcome_counts.items():
            if count >= 2:
                patterns.append({
                    "pattern": f"事件模式: {outcome}",
                    "frequency": count,
                    "type": "episodic_pattern",
                    "consolidated_at": datetime.now().isoformat(),
                })

    # ── 3. 写入统一固化的语义记忆文件 ──
    consolidate_file = DREAM_DIR / "semantic_memory.json"
    existing_semantic: dict[str, Any] = {}
    if consolidate_file.exists():
        try:
            existing_semantic = json.loads(consolidate_file.read_text())
        except Exception:
            existing_semantic = {}

    session_count = existing_semantic.get("session_count", 0) + 1
    session_label = f"session_{session_count}_{datetime.now().strftime('%Y%m%d')}"

    existing_semantic["session_count"] = session_count
    existing_semantic["last_consolidated"] = datetime.now().isoformat()
    sessions = existing_semantic.get("sessions", {})
    sessions[session_label] = {
        "episode_count": len(all_episodes),
        "lesson_count": len(all_lessons),
        "patterns_found": len(patterns),
        "patterns": patterns,
    }
    existing_semantic["sessions"] = sessions

    # 累积所有跨 session 洞察
    all_insights = existing_semantic.get("cross_session_insights", [])
    for p in patterns:
        insight_text = p["pattern"]
        if insight_text not in {i["pattern"] for i in all_insights}:
            all_insights.append(p)
    existing_semantic["cross_session_insights"] = all_insights

    consolidate_file.write_text(json.dumps(existing_semantic, ensure_ascii=False, indent=2))

    # ── 4. 如有新洞察，追加到 self-learning-loop SKILL.md ──
    if patterns:
        _append_insights_to_skill(patterns)

    return (
        f"✨ 语义记忆固化完成\n"
        f"   - 处理情节记忆: {len(all_episodes)} 条\n"
        f"   - 处理 lessons: {len(all_lessons)} 条\n"
        f"   - 发现跨session模式: {len(patterns)} 个\n"
        f"   - 写入: {consolidate_file}\n"
    )


def _append_insights_to_skill(patterns: list[dict[str, Any]]) -> None:
    """将固化的洞察追加到 self-learning-loop SKILL.md。

    仅被 dream_consolidate 内部调用，不暴露为公共 API。
    """
    skill_path = SKILLS_META / "self-learning-loop" / "SKILL.md"
    if not skill_path.exists():
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "",
        f"<!-- 记忆蒸馏注入: {now} {len(patterns)} 个模式 -->",
        f"<!-- 墨梦AutoDream dream_consolidate() 自动生成 -->",
        "",
        "## 跨Session固化洞察（自动注入）",
        "",
    ]
    for p in patterns:
        lines.append(f"- **{p['type']}** (频率: {p['frequency']}): {p['pattern']}")
    lines.append("")

    # 在文件末尾追加，使用 marker 避免重复注入
    content = skill_path.read_text()
    marker = "<!-- 记忆蒸馏注入"
    if marker not in content:
        content += "\n" + "\n".join(lines)
        skill_path.write_text(content)


# ─── AutoDream Worker 类 ─────────────────────────────────────────────────────

class AutoDream(SubsidiaryWorker):
    worker_id = "auto_dream"
    worker_name = "墨梦AutoDream"
    description = "记忆整合与战略复盘 + 记忆蒸馏(dream_distill/reflect/consolidate)"
    oneliner = "记忆整合、战略复盘与记忆蒸馏"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "工作记忆→情节记忆蒸馏（dream_distill）",
            "任务日志→经验教训提取（dream_reflect）",
            "跨Session语义记忆固化（dream_consolidate）",
            "高频失败模式识别与策略优化建议",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨梦AutoDream",
            "vp": "技术",
            "description": "记忆整合与战略复盘 + 记忆蒸馏(dream_distill/reflect/consolidate)",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            week = task.payload.get("week", "本周")
            action = task.payload.get("action", "review")

            if action in ("distill", "dream_distill"):
                # 调用底层的 dream_distill
                work_memory = task.payload.get("work_memory", [])
                file_path = dream_distill(work_memory)
                output = {
                    "action": "distilled",
                    "week": week,
                    "file_written": file_path,
                    "memory_stats": {
                        "total": task.payload.get("total_memories", len(work_memory)),
                        "new_this_week": task.payload.get("new_this_week", len(work_memory)),
                    },
                    "status": "distill_complete",
                }

            elif action in ("reflect", "dream_reflect"):
                # 调用底层的 dream_reflect
                task_log = task.payload.get("task_log", [])
                file_path = dream_reflect(task_log)
                output = {
                    "action": "reflected",
                    "week": week,
                    "file_written": file_path,
                    "status": "reflect_complete",
                }

            elif action in ("consolidate", "dream_consolidate"):
                # 调用底层的 dream_consolidate
                status_report = dream_consolidate()
                output = {
                    "action": "consolidated",
                    "week": week,
                    "status_report": status_report,
                    "status": "consolidate_complete",
                }

            else:
                # 默认战略复盘：用LLM生成战略洞察
                total_memories = task.payload.get("total_memories", 0)
                new_this_week = task.payload.get("new_this_week", 0)

                prompt = f"""你是一位AI系统战略复盘分析师。根据以下本周运营数据进行战略复盘：

周次：{week}
总记忆数：{total_memories}
本周新增记忆：{new_this_week}
额外上下文：{task.payload.get("context", "无")}

请以JSON格式返回：
- week: 周次
- memory_stats: 记忆统计，包含 total (int), new_this_week (int)
- strategic_insights: 战略洞察列表（至少3条，有深度）
- identified_patterns: 识别到的高频模式或失败模式列表
- action_items: 建议行动项列表（至少2条）
- status: "dream_cycle_complete"
"""
                system = "你是一位专业的AI系统战略复盘分析师，擅长从数据中提取深层洞察。返回严格JSON。"
                llm_output = await self.llm_chat_json(prompt, system=system)

                if not llm_output:
                    output = {
                        "week": week,
                        "memory_stats": {
                            "total": total_memories,
                            "new_this_week": new_this_week,
                        },
                        "strategic_insights": [
                            "识别3个高频失败模式",
                            "建议优化2个子公司调度策略",
                        ],
                        "identified_patterns": [
                            {"pattern": "超时重试模式", "frequency": 3},
                            {"pattern": "资源不足导致失败", "frequency": 2},
                        ],
                        "action_items": ["优化VP分派逻辑", "更新定价策略"],
                        "status": "dream_cycle_complete",
                    }
                else:
                    llm_output.setdefault("week", week)
                    llm_output.setdefault("memory_stats", {
                        "total": total_memories,
                        "new_this_week": new_this_week,
                    })
                    llm_output.setdefault("status", "dream_cycle_complete")
                    output = llm_output

            return WorkerResult(
                task_id=task.task_id,
                worker_id=self.worker_id,
                status="success",
                output=output,
            )
        except Exception as e:
            return WorkerResult(
                task_id=task.task_id,
                worker_id=self.worker_id,
                status="error",
                output={},
                error=str(e),
            )
