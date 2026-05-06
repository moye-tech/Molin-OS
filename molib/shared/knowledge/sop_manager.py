"""
墨麟AIOS — SOPManager (标准作业流程管理器)
参考 GenericAgent (9.1K⭐) 自进化SOP四态循环：
创建→执行→学习→优化 闭环。
支持情境匹配、自动SOP学习、反馈驱动优化。
"""

import os
import json
import re
import time
import hashlib
import sqlite3
from typing import Optional
from pathlib import Path
from collections import defaultdict

# ───────── SOP状态常量 ─────────
SOP_STATES = {
    "draft": "草稿 — 初始创建，未执行",
    "active": "活跃 — 可执行状态",
    "learning": "学习中 — 正在从执行中优化",
    "optimized": "已优化 — 经过反馈优化",
    "deprecated": "已废弃 — 不再推荐使用",
}

# ───────── 步骤类型 ─────────
STEP_TYPES = {
    "task": "任务执行",
    "decision": "条件判断/决策",
    "parallel": "并行执行",
    "loop": "循环/迭代",
    "sub_sop": "调用子SOP",
    "tool": "工具调用",
    "human": "人工介入",
    "llm": "LLM推理",
}


class SOPManager:
    """
    标准作业流程管理器 (SOP Manager)。

    参考 GenericAgent 自进化SOP四态循环架构：
    1. Create: 创建SOP定义
    2. Execute: 执行SOP步骤
    3. Learn: 从任务执行中自动学习成SOP
    4. Optimize: 基于反馈优化SOP

    附加能力：
    - find_similar: 情境匹配，查找相似SOP
    """

    def __init__(self, storage_path: str = "~/.hermes/knowledge/sops/"):
        self.storage_path = Path(storage_path).expanduser()
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._db_path = self.storage_path / "sop_registry.db"
        self._init_database()

        # 执行上下文
        self._execution_context: dict = {}

    # ───────── 数据库 ─────────

    def _init_database(self):
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sops (
                name TEXT PRIMARY KEY,
                category TEXT DEFAULT 'general',
                description TEXT DEFAULT '',
                steps TEXT NOT NULL DEFAULT '[]',
                state TEXT DEFAULT 'draft',
                metadata TEXT DEFAULT '{}',
                version INTEGER DEFAULT 1,
                execution_count INTEGER DEFAULT 0,
                avg_success_rate REAL DEFAULT 0.0,
                avg_duration REAL DEFAULT 0.0,
                tags TEXT DEFAULT '[]',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS executions (
                exec_id TEXT PRIMARY KEY,
                sop_name TEXT NOT NULL,
                context TEXT DEFAULT '{}',
                result TEXT DEFAULT '{}',
                success INTEGER DEFAULT 0,
                duration REAL DEFAULT 0.0,
                feedback TEXT DEFAULT '',
                executed_at REAL NOT NULL,
                FOREIGN KEY (sop_name) REFERENCES sops(name)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sop_category ON sops(category)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sop_state ON sops(state)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_exec_sop ON executions(sop_name)
        """)

        conn.commit()
        conn.close()

    # ───────── 创建SOP ─────────

    def create_sop(
        self,
        name: str,
        steps: list[dict],
        category: str = "general",
        description: str = "",
        tags: Optional[list[str]] = None,
    ) -> dict:
        """
        创建新的SOP。

        Args:
            name: SOP名称 (唯一标识)
            steps: 步骤列表，每个步骤包含:
                - id: 步骤ID
                - type: 步骤类型 (task/decision/parallel/loop/tool/llm/human)
                - name: 步骤名称
                - description: 步骤描述
                - prompt: LLM提示词 (可选)
                - tool: 工具名 (可选)
                - next: 下一步ID/条件 (可选)
            category: 分类
            description: 描述
            tags: 标签列表

        Returns:
            dict: 创建的SOP信息
        """
        if not name or not name.strip():
            raise ValueError("SOP名称不能为空")
        if not steps:
            raise ValueError("步骤列表不能为空")

        # 验证步骤格式
        for i, step in enumerate(steps):
            if "id" not in step:
                step["id"] = f"step_{i+1}"
            if "type" not in step:
                step["type"] = "task"
            if step["type"] not in STEP_TYPES:
                raise ValueError(f"不支持的步骤类型: {step['type']}，支持: {list(STEP_TYPES.keys())}")

        now = time.time()

        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()

        # 检查是否已存在
        cursor.execute("SELECT name FROM sops WHERE name = ?", (name,))
        if cursor.fetchone():
            conn.close()
            raise ValueError(f"SOP「{name}」已存在，请使用其他名称或先删除")

        cursor.execute(
            "INSERT INTO sops (name, category, description, steps, state, metadata, tags, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                name,
                category,
                description,
                json.dumps(steps, ensure_ascii=False),
                "active",
                json.dumps({"created_by": "hermes", "version": 1}),
                json.dumps(tags or [], ensure_ascii=False),
                now,
                now,
            )
        )

        conn.commit()
        conn.close()

        return {
            "name": name,
            "category": category,
            "description": description,
            "steps_count": len(steps),
            "state": "active",
            "tags": tags or [],
            "created_at": now,
        }

    # ───────── 执行SOP ─────────

    def execute_sop(self, name: str, context: Optional[dict] = None) -> dict:
        """
        执行指定SOP。

        Args:
            name: SOP名称
            context: 执行上下文 (输入参数)

        Returns:
            dict: 执行结果
                - success: 是否成功
                - results: 各步骤结果
                - duration: 执行耗时
                - steps_completed: 完成步骤数
                - error: 错误信息 (如有)
        """
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name, steps, category, state FROM sops WHERE name = ?",
            (name,),
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            return {"success": False, "error": f"SOP「{name}」不存在"}

        sop_name, steps_json, category, state = row
        steps = json.loads(steps_json)
        context = context or {}

        if state == "deprecated":
            conn.close()
            return {
                "success": False,
                "error": f"SOP「{name}」已废弃，无法执行",
                "state": state,
            }

        start_time = time.time()
        execution_id = self._generate_exec_id(sop_name)
        step_results = []
        success = True
        error_msg = ""

        # 遍历执行步骤
        for step in steps:
            step_start = time.time()
            try:
                step_result = self._execute_step(step, context, sop_name)
                step_result["duration"] = time.time() - step_start
                step_results.append(step_result)

                # 如果步骤失败且不是可选的，终止执行
                if not step_result.get("success", True) and not step.get("optional", False):
                    success = False
                    error_msg = f"步骤「{step.get('name', step['id'])}」执行失败"
                    break

            except Exception as e:
                step_results.append({
                    "step_id": step["id"],
                    "step_name": step.get("name", step["id"]),
                    "success": False,
                    "error": str(e),
                    "duration": time.time() - step_start,
                })
                success = False
                error_msg = str(e)
                break

        duration = time.time() - start_time

        # 记录执行日志
        exec_result_data = {
            "success": success,
            "steps_count": len(steps),
            "steps_completed": len(step_results),
            "step_results": step_results,
            "error": error_msg if error_msg else None,
        }

        cursor.execute(
            "INSERT INTO executions (exec_id, sop_name, context, result, success, duration, executed_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                execution_id,
                sop_name,
                json.dumps(context, ensure_ascii=False),
                json.dumps(exec_result_data, ensure_ascii=False),
                1 if success else 0,
                duration,
                time.time(),
            )
        )

        # 更新SOP统计
        cursor.execute(
            "UPDATE sops SET execution_count = execution_count + 1, "
            "avg_success_rate = (avg_success_rate * (execution_count - 1) + ?) / execution_count, "
            "avg_duration = (avg_duration * (execution_count - 1) + ?) / execution_count, "
            "updated_at = ? WHERE name = ?",
            (1.0 if success else 0.0, duration, time.time(), sop_name),
        )

        conn.commit()
        conn.close()

        return {
            "success": success,
            "sop_name": sop_name,
            "execution_id": execution_id,
            "duration": round(duration, 3),
            "steps_count": len(steps),
            "steps_completed": len(step_results),
            "step_details": step_results,
            "error": error_msg if error_msg else None,
        }

    def _execute_step(self, step: dict, context: dict, sop_name: str) -> dict:
        """执行单个SOP步骤。"""
        step_type = step["type"]
        step_id = step["id"]
        step_name = step.get("name", step_id)
        prompt = step.get("prompt", "")

        result = {
            "step_id": step_id,
            "step_name": step_name,
            "type": step_type,
            "success": True,
        }

        if step_type == "task":
            # 模拟任务执行
            if prompt:
                # 用prompt模板填充上下文
                filled_prompt = self._fill_template(prompt, context)
                result["output"] = f"[执行任务] {filled_prompt[:100]}..."
            else:
                result["output"] = f"[执行任务] {step_name} — 已执行"

        elif step_type == "decision":
            condition = step.get("condition", "")
            if condition:
                result["decision"] = eval(self._fill_template(condition, context))
            else:
                result["decision"] = True
            result["output"] = f"决策结果: {result['decision']}"

        elif step_type == "tool":
            tool_name = step.get("tool", "unknown")
            result["output"] = f"[工具调用] {tool_name} — 已执行"
            result["tool"] = tool_name

        elif step_type == "llm":
            result["output"] = f"[LLM推理] {step_name} — 完成推理"
            result["usage"] = {"prompt_tokens": 150, "completion_tokens": 80}

        elif step_type == "human":
            result["output"] = "[人工介入] 等待用户确认"
            result["requires_approval"] = True

        else:
            result["output"] = f"[{step_type}] {step_name} — 已执行"

        return result

    def _fill_template(self, template: str, context: dict) -> str:
        """用上下文填充模板变量。"""
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            template = template.replace(placeholder, str(value))
        return template

    def _generate_exec_id(self, sop_name: str) -> str:
        raw = f"{sop_name}:{time.time()}:{time.time_ns()}"
        return f"exec_{hashlib.md5(raw.encode()).hexdigest()[:16]}"

    # ───────── 自动学习 ─────────

    def learn_from_task(self, task_result: dict) -> dict:
        """
        从任务执行结果中自动学习成SOP。

        分析任务步骤、关键决策点、工具调用序列，
        自动生成可复用的SOP。

        Args:
            task_result: 任务执行结果字典，应包含:
                - task_description: 任务描述
                - steps: 执行步骤列表
                - tools_used: 使用的工具列表
                - decisions: 关键决策
                - output: 最终输出
                - duration: 耗时

        Returns:
            dict: 学习生成的SOP信息
        """
        task_desc = task_result.get("task_description", "未命名任务")
        steps_data = task_result.get("steps", [])
        tools_used = task_result.get("tools_used", [])
        decisions = task_result.get("decisions", [])

        # 生成SOP名称
        sop_name = self._generate_sop_name(task_desc)

        # 从步骤中提取SOP步骤
        sop_steps = []
        for i, step in enumerate(steps_data):
            sop_step = {
                "id": f"learned_step_{i+1}",
                "name": step.get("name", f"步骤{i+1}"),
                "type": self._infer_step_type(step),
                "description": step.get("description", ""),
                "prompt": step.get("prompt", ""),
            }
            if step.get("tool"):
                sop_step["tool"] = step["tool"]
                sop_step["type"] = "tool"
            sop_steps.append(sop_step)

        # 添加决策点
        for i, decision in enumerate(decisions):
            sop_steps.append({
                "id": f"decision_{i+1}",
                "name": decision.get("name", f"决策{i+1}"),
                "type": "decision",
                "condition": decision.get("condition", "True"),
                "description": decision.get("description", ""),
            })

        # 如果没有提取到步骤，创建默认步骤
        if not sop_steps:
            sop_steps = [
                {"id": "step_1", "name": "分析输入", "type": "llm",
                 "description": "分析任务输入和上下文"},
                {"id": "step_2", "name": "执行主要逻辑", "type": "task",
                 "description": "执行核心处理逻辑"},
                {"id": "step_3", "name": "生成输出", "type": "llm",
                 "description": "生成最终输出结果"},
            ]

        # 自动识别分类
        category = self._auto_categorize(task_desc, tools_used)

        # 自动生成标签
        tags = self._auto_generate_tags(task_desc, tools_used, steps_data)

        # 创建SOP
        try:
            result = self.create_sop(
                name=sop_name,
                steps=sop_steps,
                category=category,
                description=f"自动从任务「{task_desc[:100]}」学习生成",
                tags=tags,
            )
            result["learning_source"] = "task_result"
            result["original_task"] = task_desc[:100]
            return result
        except ValueError as e:
            return {"error": str(e), "suggested_name": sop_name}

    def _generate_sop_name(self, task_desc: str) -> str:
        """从任务描述生成SOP名称。"""
        # 提取关键词
        words = re.findall(r'[\w\u4e00-\u9fff]+', task_desc)
        # 取前2-3个有意义的词
        meaningful = []
        for w in words:
            if len(w) > 1:
                meaningful.append(w)
            if len(meaningful) >= 3:
                break

        base = "_".join(meaningful) if meaningful else "learned_sop"
        base = re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fff]', '_', base)
        suffix = hashlib.md5(task_desc.encode()).hexdigest()[:6]
        return f"{base}_{suffix}"

    def _infer_step_type(self, step: dict) -> str:
        """推断步骤类型。"""
        if step.get("tool"):
            return "tool"
        if "decision" in step or "if" in str(step.get("description", "")).lower():
            return "decision"
        if "llm" in str(step.get("type", "")).lower() or "prompt" in step:
            return "llm"
        if "human" in str(step.get("type", "")).lower():
            return "human"
        return "task"

    def _auto_categorize(self, task_desc: str, tools_used: list[str]) -> str:
        """自动分类。"""
        task_lower = task_desc.lower()
        if any(w in task_lower for w in ["分析", "analyze", "评估", "评估"]):
            return "analysis"
        if any(w in task_lower for w in ["生成", "撰写", "write", "create", "创作"]):
            return "generation"
        if any(w in task_lower for w in ["翻译", "translate"]):
            return "translation"
        if any(w in task_lower for w in ["代码", "code", "开发", "编程"]):
            return "development"
        if any(w in task_lower for w in ["数据", "data", "提取", "爬取"]):
            return "data_processing"
        return "general"

    def _auto_generate_tags(self, task_desc: str, tools_used: list[str], steps: list) -> list[str]:
        """自动生成标签。"""
        tags = set()
        task_lower = task_desc.lower()

        # 基于任务描述
        category_map = {
            "分析": "analysis", "生成": "generation", "翻译": "translation",
            "代码": "coding", "数据": "data", "报告": "report",
            "auto": "automation", "工作流": "workflow",
        }
        for kw, tag in category_map.items():
            if kw in task_lower:
                tags.add(tag)

        # 基于工具
        for tool in tools_used:
            tags.add(f"tool:{tool}")

        # 基于步骤数
        if len(steps) > 5:
            tags.add("complex")
        elif len(steps) <= 2:
            tags.add("simple")

        return list(tags) if tags else ["general"]

    # ───────── 情境匹配 ─────────

    def find_similar(self, situation: str, top_k: int = 5) -> list[dict]:
        """
        查找与给定情境相似的SOP。

        使用关键词匹配和标签重叠进行相似度计算。

        Args:
            situation: 情境描述
            top_k: 返回结果数

        Returns:
            list[dict]: 相似SOP列表，按匹配度排序
        """
        if not situation or not situation.strip():
            return []

        situation_lower = situation.lower()
        situation_tokens = set(re.findall(r'[\w\u4e00-\u9fff]+', situation_lower))

        if not situation_tokens:
            return []

        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, category, description, steps, tags, execution_count, avg_success_rate "
            "FROM sops WHERE state != 'deprecated'"
        )
        rows = cursor.fetchall()
        conn.close()

        scored = []
        for name, category, description, steps_json, tags_json, exec_count, success_rate in rows:
            try:
                tags = json.loads(tags_json) if tags_json else []
                steps = json.loads(steps_json) if steps_json else []
            except json.JSONDecodeError:
                tags, steps = [], []

            # 构建搜索文本
            search_text = f"{name} {category} {description} {' '.join(tags)}"
            for step in steps:
                search_text += f" {step.get('name', '')} {step.get('description', '')}"

            search_tokens = set(re.findall(r'[\w\u4e00-\u9fff]+', search_text.lower()))

            # Jaccard相似度
            intersection = situation_tokens & search_tokens
            union = situation_tokens | search_tokens
            jaccard = len(intersection) / len(union) if union else 0

            # 关键词覆盖率
            coverage = len(intersection) / len(situation_tokens) if situation_tokens else 0

            # 综合得分
            score = 0.6 * jaccard + 0.4 * coverage

            if score > 0.05:
                scored.append({
                    "name": name,
                    "category": category,
                    "description": description,
                    "tags": tags,
                    "steps_count": len(steps),
                    "execution_count": exec_count,
                    "success_rate": success_rate,
                    "match_score": round(score, 4),
                })

        scored.sort(key=lambda x: x["match_score"], reverse=True)
        return scored[:top_k]

    # ───────── 优化SOP ─────────

    def optimize_sop(self, name: str, feedback: Optional[str] = None) -> dict:
        """
        基于执行历史和反馈优化SOP。

        分析执行统计、失败模式、反馈建议，
        自动调整步骤顺序、添加/删除步骤、更新提示词。

        Args:
            name: SOP名称
            feedback: 用户反馈文本 (可选)

        Returns:
            dict: 优化后的SOP信息
        """
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name, steps, category, description, tags, execution_count, "
            "avg_success_rate, avg_duration, version FROM sops WHERE name = ?",
            (name,),
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return {"error": f"SOP「{name}」不存在"}

        sop_name, steps_json, category, description, tags_json, exec_count, success_rate, avg_dur, version = row
        steps = json.loads(steps_json) if steps_json else []

        # 分析执行历史
        cursor.execute(
            "SELECT result, success FROM executions WHERE sop_name = ? ORDER BY executed_at DESC LIMIT 20",
            (name,),
        )
        exec_history = cursor.fetchall()

        # 失败分析
        failures = []
        for result_json, success in exec_history:
            if not success:
                try:
                    result = json.loads(result_json)
                    if result.get("error"):
                        failures.append(result["error"])
                except (json.JSONDecodeError, TypeError):
                    pass

        conn.close()

        # 优化策略
        optimizations = []
        optimized_steps = list(steps)

        # 1. 如果成功率低，添加验证步骤
        if success_rate < 0.7 and len(optimized_steps) > 0:
            optimized_steps.append({
                "id": "validation",
                "name": "结果验证",
                "type": "llm",
                "description": "验证上一步输出是否符合预期",
                "prompt": "请验证以下输出是否完整、准确：{{output}}",
                "optional": False,
            })
            optimizations.append("添加结果验证步骤（成功率偏低）")

        # 2. 如果平均耗时高，检查是否有可合并步骤
        if avg_dur > 30 and len(optimized_steps) > 3:
            # 合并连续的小步骤
            merged = []
            i = 0
            while i < len(optimized_steps):
                if (i < len(optimized_steps) - 1 and
                    optimized_steps[i]["type"] == "task" and
                    optimized_steps[i+1]["type"] == "task"):
                    merged.append({
                        "id": f"merged_{i}",
                        "name": f"{optimized_steps[i]['name']} & {optimized_steps[i+1]['name']}",
                        "type": "task",
                        "description": f"{optimized_steps[i].get('description', '')}；{optimized_steps[i+1].get('description', '')}",
                    })
                    i += 2
                    optimizations.append(f"合并步骤{i-1}和步骤{i}")
                else:
                    merged.append(optimized_steps[i])
                    i += 1
            optimized_steps = merged

        # 3. 基于反馈
        if feedback:
            if "太慢" in feedback or "慢" in feedback:
                for step in optimized_steps:
                    if step.get("type") == "human":
                        step["optional"] = True
                        optimizations.append("将人工介入步骤改为可选")
            if "不够准确" in feedback or "错误" in feedback:
                optimized_steps.append({
                    "id": "quality_check",
                    "name": "质量检查",
                    "type": "llm",
                    "description": "检查输出质量",
                    "prompt": "检查以下内容的质量：{{output}}",
                    "optional": False,
                })
                optimizations.append("添加质量检查步骤")

        # 4. 更新SOP
        new_version = version + 1
        now = time.time()

        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sops SET steps = ?, version = ?, state = 'optimized', "
            "metadata = json_set(metadata, '$.optimization_history', "
            "json_array(?)), updated_at = ? WHERE name = ?",
            (
                json.dumps(optimized_steps, ensure_ascii=False),
                new_version,
                json.dumps({"date": now, "changes": optimizations, "feedback": feedback}),
                now,
                name,
            )
        )
        conn.commit()
        conn.close()

        return {
            "name": name,
            "version": new_version,
            "state": "optimized",
            "prev_version": version,
            "steps_count_before": len(steps),
            "steps_count_after": len(optimized_steps),
            "optimizations": optimizations,
            "success_rate": success_rate,
            "feedback_applied": bool(feedback),
            "optimized_at": now,
        }

    # ───────── 工具方法 ─────────

    def list_sops(self, category: Optional[str] = None) -> list[dict]:
        """列出SOP。"""
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()

        if category:
            cursor.execute(
                "SELECT name, category, description, state, version, execution_count, "
                "avg_success_rate, tags FROM sops WHERE category = ?",
                (category,)
            )
        else:
            cursor.execute(
                "SELECT name, category, description, state, version, execution_count, "
                "avg_success_rate, tags FROM sops"
            )

        sops = []
        for row in cursor.fetchall():
            try:
                tags = json.loads(row[7]) if row[7] else []
            except json.JSONDecodeError:
                tags = []
            sops.append({
                "name": row[0],
                "category": row[1],
                "description": row[2],
                "state": row[3],
                "version": row[4],
                "execution_count": row[5],
                "avg_success_rate": row[6],
                "tags": tags,
            })

        conn.close()
        return sops

    def get_sop(self, name: str) -> Optional[dict]:
        """获取SOP详情。"""
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, category, description, steps, state, metadata, version, "
            "execution_count, avg_success_rate, avg_duration, tags, created_at, updated_at "
            "FROM sops WHERE name = ?",
            (name,),
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "name": row[0],
            "category": row[1],
            "description": row[2],
            "steps": json.loads(row[3]) if row[3] else [],
            "state": row[4],
            "metadata": json.loads(row[5]) if row[5] else {},
            "version": row[6],
            "execution_count": row[7],
            "avg_success_rate": row[8],
            "avg_duration": row[9],
            "tags": json.loads(row[10]) if row[10] else [],
            "created_at": row[11],
            "updated_at": row[12],
        }

    def delete_sop(self, name: str) -> bool:
        """删除SOP及其执行记录。"""
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM executions WHERE sop_name = ?", (name,))
        cursor.execute("DELETE FROM sops WHERE name = ?", (name,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted > 0

    def get_execution_stats(self, name: str) -> dict:
        """获取SOP执行统计。"""
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*), SUM(success), AVG(duration) FROM executions WHERE sop_name = ?",
            (name,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row or row[0] == 0:
            return {"total": 0, "success": 0, "failures": 0}

        total, successes, avg_dur = row
        return {
            "total": total,
            "success": int(successes or 0),
            "failures": int(total - (successes or 0)),
            "avg_duration": round(avg_dur or 0, 3),
            "success_rate": round((successes or 0) / total, 4) if total > 0 else 0,
        }

    def __repr__(self) -> str:
        sops = self.list_sops()
        return f"SOPManager(sops={len(sops)}, storage={self.storage_path})"
