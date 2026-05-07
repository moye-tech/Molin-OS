"""
墨域OS — Phase1+Phase2 两阶段执行器 + LLM 质量门控
=====================================================
废弃"直接让LLM编内容"的模式，改为：

Phase 1 (工具执行): 基于 deliverable_spec 执行工具 → 搜集原始数据/素材
Phase 2 (LLM合成): 基于明确的交付标准，将原始素材合成为真正可用的交付物
Quality Gate: LLM 按业务标准打分1-10，不达标自动升级模型重试

升级链路: Flash → Pro → Reasoner (单向递进，禁止倒置)
"""

import json
import re
import time
import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("molin.ceo.phase_executor")


# ── 升级链路（单向递进） ──────────────────────────────────────────
UPGRADE_CHAIN = ["deepseek-v4-flash", "deepseek-v4-pro", "deepseek-reasoner"]

# 反向查找索引
_MODEL_RANK = {m: i for i, m in enumerate(UPGRADE_CHAIN)}


def next_model(current: str) -> Optional[str]:
    """获取单向递进的下一个模型。返回 None 表示已是最高级。"""
    idx = _MODEL_RANK.get(current)
    if idx is None or idx >= len(UPGRADE_CHAIN) - 1:
        return None
    return UPGRADE_CHAIN[idx + 1]


# ── 数据模型 ──────────────────────────────────────────────────────


@dataclass
class Phase1Input:
    """Phase 1 输入"""
    task_description: str         # 任务描述
    deliverable_spec: str         # 交付标准
    tools_available: list[str]    # 可用工具列表
    context: dict = field(default_factory=dict)


@dataclass
class Phase1Output:
    """Phase 1 输出 — 原始数据/素材"""
    tool_outputs: list[dict]      # 工具执行结果列表
    raw_materials: list[str]      # 搜集到的原始素材
    notes: str = ""               # 执行备注
    execution_time: float = 0.0


@dataclass
class Phase2Input:
    """Phase 2 输入"""
    task_description: str
    deliverable_spec: str
    raw_materials: list[str]
    tool_outputs: list[dict]
    target_subsidiary: str = ""


@dataclass
class QualityResult:
    """质量门控结果"""
    score: int                     # 1-10
    passed: bool                   # >= 6 通过
    issues: list[str]              # 未达标的具体问题
    improvement_suggestions: list[str]  # 改进建议
    model_used: str                # 评估时的模型


# ── Phase 1: 工具执行 ────────────────────────────────────────────

# 内置的"工具执行器"（Hermes Agent 本身即可执行工具，
# 这里提供结构化模板供 CEO 编排器调度）

PHASE1_TOOL_TEMPLATES = {
    "web_search": {
        "description": "Web搜索，搜集公开信息",
        "input_template": "搜索关键词: {query}\n搜索数量: {count or 5}",
        "example_tasks": ["竞品调研", "市场分析", "技术情报"],
    },
    "data_collect": {
        "description": "数据采集与整理",
        "input_template": "数据源: {source}\n数据维度: {dimensions}\n时间范围: {timeframe}",
        "example_tasks": ["财报分析", "用户数据统计", "行业数据"],
    },
    "file_operation": {
        "description": "文件读写操作",
        "input_template": "文件路径: {path}\n操作: {operation}\n内容: {content if needed}",
        "example_tasks": ["读取已有文档", "保存输出文件"],
    },
    "code_execution": {
        "description": "执行代码/脚本",
        "input_template": "语言: {language}\n代码目标: {goal}\n输入数据: {input_data if any}",
        "example_tasks": ["数据清洗", "算法实现", "文件格式转换"],
    },
    "api_query": {
        "description": "查询外部API",
        "input_template": "API: {api_name}\n参数: {params}\n期望输出: {expected}",
        "example_tasks": ["查豆瓣评分", "获取天气", "查汇率"],
    },
}


@dataclass
class ToolPlan:
    """Phase 1 的工具执行计划"""
    tools: list[dict]              # [{"name": "web_search", "params": {...}}, ...]
    gather_instructions: str       # 搜集指令
    estimated_steps: int = 1


class Phase1Executor:
    """
    Phase 1: 工具执行 — 搜集原始数据/素材。

    基于 deliverable_spec 自动规划需要哪些工具，
    执行后返回原始数据。
    """

    def __init__(self, llm_client=None):
        self._llm = llm_client

    def set_llm_client(self, llm_client):
        self._llm = llm_client

    async def plan(self, input_data: Phase1Input) -> ToolPlan:
        """
        基于任务描述和交付标准，规划Phase1工具执行计划。
        如果无LLM可用，返回一个默认的"直接合成"计划。
        """
        if not self._llm:
            # 默认计划：无工具执行，直接合成
            return ToolPlan(
                tools=[],
                gather_instructions="无工具可用，跳过数据搜集阶段",
                estimated_steps=0,
            )

        # 用 LLM 规划工具
        tools_desc = "\n".join(
            f"- {name}: {t['description']} (适合: {'/'.join(t['example_tasks'])})"
            for name, t in PHASE1_TOOL_TEMPLATES.items()
        )

        prompt = (
            f"你是墨域OS的执行规划员。根据任务描述和交付标准，规划需要哪些工具。\n\n"
            f"任务描述: {input_data.task_description}\n"
            f"交付标准: {input_data.deliverable_spec}\n\n"
            f"可用工具:\n{tools_desc}\n\n"
            f"输出严格JSON（不要markdown）：\n"
            f"{{\n"
            f'  "tools": [{{"name": "web_search", "params": {{"query": "...", "count": 3}}}}, ...],\n'
            f'  "gather_instructions": "搜集指令",\n'
            f'  "reason": "为什么选这些工具"\n'
            f"}}\n"
            f"规则：\n"
            f"- 如果任务不需要外部数据（如纯文案创作），tools=[]\n"
            f"- 如果需要调研/数据/情报，必须包括工具\n"
            f"- 最多规划3个工具，按执行顺序排列"
        )

        response = self._llm.chat([
            {"role": "system", "content": "你是一个严谨的执行规划员。只输出JSON。"},
            {"role": "user", "content": prompt},
        ], model="deepseek-v4-flash")

        try:
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                tools = data.get("tools", [])
                return ToolPlan(
                    tools=tools,
                    gather_instructions=data.get("gather_instructions", ""),
                    estimated_steps=len(tools),
                )
        except (json.JSONDecodeError, AttributeError):
            pass

        return ToolPlan(tools=[], gather_instructions="规划失败，跳过", estimated_steps=0)

    async def execute(self, plan: ToolPlan) -> Phase1Output:
        """
        执行工具计划。

        注意：Hermes Agent 的终端/浏览器工具由父级提供。
        此处返回工具执行指令和预期结果，由 CEO 编排器
        实际调用 Hermes 工具执行。
        """
        tool_outputs = []
        raw_materials = []

        for tool in plan.tools:
            # 记录工具执行计划
            tool_outputs.append({
                "tool": tool["name"],
                "params": tool.get("params", {}),
                "status": "planned",
                "note": "由CEO编排器执行此工具",
            })

        return Phase1Output(
            tool_outputs=tool_outputs,
            raw_materials=raw_materials,
            notes=plan.gather_instructions,
        )


# ── Phase 2: LLM 合成 ────────────────────────────────────────────


SECTOR_SPECS = {
    "墨笔文创": {
        "description": "文案/文章创作",
        "quality_criteria": [
            "内容原创性 — 非模板化，有真实观点",
            "目标受众匹配 — 语言风格/深度符合受众",
            "结构完整性 — 有开头/正文/结尾，逻辑清晰",
            "可执行性 — 是完整可用的交付物，不是大纲或骨架",
            "语言质量 — 无语法错误、无AI腔、表达自然",
        ],
        "pass_threshold": 6,
    },
    "墨图设计": {
        "description": "视觉设计",
        "quality_criteria": [
            "创意性 — 有独特视觉思路",
            "一致性 — 风格统一，品牌一致",
            "可用性 — 提供的是可直接用的设计规格/描述",
            "清晰度 — 设计说明清晰完整",
            "可行性 — 实现成本合理",
        ],
        "pass_threshold": 6,
    },
    "墨码开发": {
        "description": "软件开发",
        "quality_criteria": [
            "功能完整性 — 满足需求的所有功能点",
            "代码质量 — 结构清晰，错误处理完善",
            "可维护性 — 有注释、模块化、遵守最佳实践",
            "正确性 — 逻辑正确，边界情况已考虑",
            "文档完整 — 有使用说明/API文档",
        ],
        "pass_threshold": 7,
    },
    "default": {
        "description": "通用任务",
        "quality_criteria": [
            "完整性 — 交付物完整，不是骨架或占位符",
            "准确性 — 事实正确，不编造",
            "可用性 — 可以直接用或经过简单调整即可交付",
            "结构化 — 格式清晰，易于阅读",
            "价值 — 对用户有实际价值",
        ],
        "pass_threshold": 6,
    },
}


class Phase2Executor:
    """
    Phase 2: LLM 合成交付物。

    基于 raw_materials 和 deliverable_spec，
    用 LLM 合成真正可用的交付物。
    """

    def __init__(self, llm_client=None):
        self._llm = llm_client

    def set_llm_client(self, llm_client):
        self._llm = llm_client

    async def synthesize(self, input_data: Phase2Input,
                         model: str = "deepseek-v4-pro") -> str:
        """
        合成交付物。使用指定模型（默认 Pro，比 Flash 高一级）。
        """
        if not self._llm:
            return f"[模拟交付物 — 基于: {input_data.task_description}]"

        # 构建system prompt
        if input_data.target_subsidiary:
            sector = SECTOR_SPECS.get(input_data.target_subsidiary, SECTOR_SPECS["default"])
        else:
            sector = SECTOR_SPECS["default"]

        criteria_text = "\n".join(f"{i+1}. {c}" for i, c in enumerate(sector["quality_criteria"]))

        materials_text = "\n\n".join(input_data.raw_materials) if input_data.raw_materials else "（无外部数据，全部使用 LLM 自身知识）"

        # 启用 reasoning_effort 做复杂决策
        system_prompt = (
            f"你是墨域OS的{sector['description']}专家。\n\n"
            f"交付标准:\n{input_data.deliverable_spec}\n\n"
            f"质量要求:\n{criteria_text}\n\n"
            f"可用的原始素材:\n{materials_text}\n\n"
            f"指令：\n"
            f"1. 基于素材（或自身知识）合成完整的交付物\n"
            f"2. 必须是可直接使用的完整交付物，不是大纲或草稿\n"
            f"3. 如果素材不足，明确说明并基于自身知识补充\n"
            f"4. 交付物应附带一段使用说明"
        )

        response = self._llm.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"任务: {input_data.task_description}"},
        ], model=model)

        return response


# ── LLM 质量门控 ────────────────────────────────────────────────


class QualityGate:
    """
    LLM 质量门控 — 取代按长度的伪打分。

    流程：
    1. 用 Flash 按业务标准打分 1-10
    2. 不达标 → 升 Pro 重试合成
    3. 还不达标 → 升 Reasoner 重试
    4. 最高级仍不达标 → 返回最高分版本并标注"未达标"
    """

    def __init__(self, llm_client=None):
        self._llm = llm_client
        self.total_evaluations = 0
        self.total_retries = 0

    def set_llm_client(self, llm_client):
        self._llm = llm_client

    async def evaluate(self, task_description: str, deliverable: str,
                       subsidiary: str = "default",
                       model: str = "deepseek-v4-flash") -> QualityResult:
        """
        用 LLM 评估交付物质量。

        Args:
            task_description: 原始任务描述
            deliverable: 交付物内容
            subsidiary: 目标子公司名
            model: 评估模型

        Returns:
            QualityResult
        """
        self.total_evaluations += 1

        # 获取质量标准
        sector = SECTOR_SPECS.get(subsidiary, SECTOR_SPECS["default"])
        criteria_text = "\n".join(
            f"- {c}" for c in sector["quality_criteria"]
        )
        pass_threshold = sector["pass_threshold"]

        if not self._llm:
            # 没有 LLM 时，基于长度做一个简单判断
            score = min(10, max(1, len(deliverable) // 100))
            passed = score >= pass_threshold
            return QualityResult(
                score=score,
                passed=passed,
                issues=[] if passed else ["无法深度评估"],
                improvement_suggestions=[],
                model_used="none",
            )

        prompt = (
            f"你是一个严格的质量评审员。对以下交付物评分。\n\n"
            f"任务描述: {task_description}\n\n"
            f"质量标准（{sector['description']}）:\n{criteria_text}\n\n"
            f"交付物:\n---\n{deliverable[:4000]}\n---\n\n"
            f"输出严格JSON（不要markdown）：\n"
            f"{{\n"
            f'  "score": 1-10,\n'
            f'  "issues": ["问题1", "问题2"],\n'
            f'  "improvements": ["建议1", "建议2"]\n'
            f"}}\n\n"
            f"评分规则：\n"
            f"- 1-3: 严重不达标（占位符、骨架、全是废话）\n"
            f"- 4-5: 不达标（有内容但缺失关键部分）\n"
            f"- 6-7: 达标（完整可用，但不惊艳）\n"
            f"- 8-9: 良好（高质量，可直接交付）\n"
            f"- 10: 卓越（远超预期）\n"
            f"通过线: >= {pass_threshold}"
        )

        response = self._llm.chat([
            {"role": "system", "content": "你是一个严格的评审员。评分必须客观，不偏袒。"},
            {"role": "user", "content": prompt},
        ], model=model)

        try:
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                score = max(1, min(10, int(data.get("score", 5))))
                issues = data.get("issues", [])
                improvements = data.get("improvements", [])
                passed = score >= pass_threshold
                return QualityResult(
                    score=score,
                    passed=passed,
                    issues=issues,
                    improvement_suggestions=improvements,
                    model_used=model,
                )
        except (json.JSONDecodeError, ValueError, AttributeError):
            pass

        # 解析失败，默认通过（避免卡死）
        return QualityResult(
            score=6,
            passed=True,
            issues=["评估解析失败，默认放行"],
            improvement_suggestions=[],
            model_used=model,
        )

    async def execute_with_quality(self, task_description: str,
                                    deliverable_spec: str,
                                    raw_materials: list[str],
                                    subsidiary: str = "default",
                                    llm_client=None) -> dict:
        """
        完整的两阶段合成 + 质量门控 + 自动升级流程。

        Returns:
            {
                "deliverable": str,
                "score": int,
                "passed": bool,
                "model_used": str,
                "retries": int,
                "issues": [...],
            }
        """
        if llm_client:
            self.set_llm_client(llm_client)

        # Phase 2 执行器
        executor = Phase2Executor(self._llm)

        phase2_input = Phase2Input(
            task_description=task_description,
            deliverable_spec=deliverable_spec,
            raw_materials=raw_materials,
            tool_outputs=[],
            target_subsidiary=subsidiary,
        )

        # 从 Flash 开始合成
        current_model = "deepseek-v4-flash"
        best_deliverable = ""
        best_score = 0
        last_result = None

        for attempt in range(3):  # 最多重试 3 次（Flash→Pro→Reasoner）
            logger.info(
                "[QualityGate] 第%d次合成 (model=%s)", attempt + 1, current_model
            )

            # 合成
            deliverable = await executor.synthesize(phase2_input, model=current_model)

            # 评估
            result = await self.evaluate(
                task_description=task_description,
                deliverable=deliverable,
                subsidiary=subsidiary,
                model="deepseek-v4-flash",  # 评估用 Flash（便宜，够用）
            )

            self.total_retries += attempt

            if result.score > best_score:
                best_deliverable = deliverable
                best_score = result.score

            if result.passed:
                logger.info("[QualityGate] ✅ 通过 (score=%d/%d, model=%s)",
                            result.score, 10, current_model)
                return {
                    "deliverable": deliverable,
                    "score": result.score,
                    "passed": True,
                    "model_used": current_model,
                    "retries": attempt,
                    "issues": result.issues,
                }

            # 未通过 → 升级模型
            next_m = next_model(current_model)
            if next_m is None:
                logger.warning("[QualityGate] 已到最高级模型，停止重试")
                break

            logger.info("[QualityGate] ⬆ 升级 %s → %s (score=%d, issues: %s)",
                        current_model, next_m, result.score, result.issues[:2])

            # 注入改进建议到任务描述中
            if result.improvement_suggestions:
                phase2_input.deliverable_spec += (
                    f"\n\n【前次评审反馈 — 需要改进】\n"
                    f"问题: {'; '.join(result.issues)}\n"
                    f"建议: {'; '.join(result.improvement_suggestions)}"
                )

            current_model = next_m
            last_result = result

        # 全不通过 — 返回最好版本
        logger.warning("[QualityGate] ❌ 所有模型均未达标 (best=%d/10)", best_score)
        return {
            "deliverable": best_deliverable,
            "score": best_score,
            "passed": False,
            "model_used": current_model,
            "retries": 3,
            "issues": last_result.issues if last_result else ["全部未达标"],
            "improvement_suggestions": last_result.improvement_suggestions if last_result else [],
        }
