"""
GenericAgent Integration Bridge
利用 GenericAgent 框架的树状任务拆解与自进化调度能力，处理 墨麟CEO 层难以用单步骤解决的极高复杂度任务。
"""
import asyncio
import json
from typing import Dict, Any, Optional
from loguru import logger
from molib.agencies.base import Task

GENERIC_AGENT_AVAILABLE = False
try:
    from generic_agent import Agent, TreePlanner
    GENERIC_AGENT_AVAILABLE = True
    logger.info("GenericAgent library available")
except ImportError:
    logger.info("GenericAgent not installed, using LLM fallback decomposition")


class GenericAgentBridge:
    def __init__(self):
        self.enabled = True
        logger.info(f"GenericAgent bridge initialized (native={'yes' if GENERIC_AGENT_AVAILABLE else 'fallback'})")

    async def delegate_complex_task(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        当任务难度评级极高或涉及多个未定义领域的跨部门协作时，CEO 可将任务委托给此桥接器。
        """
        prompt = task.payload.get("description", "")
        logger.info(f"Task {task.task_id} delegated to GenericAgent: {prompt[:80]}...")

        if GENERIC_AGENT_AVAILABLE:
            return await self._run_native_agent(prompt, context)

        # 回退：使用 LLM 驱动的真实树状拆解
        return await self._llm_decompose(prompt, context)

    async def _run_native_agent(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        planner = TreePlanner(model="qwen3-max", max_depth=4, max_nodes=12)
        agent = Agent(planner=planner)
        result = await agent.run(goal=prompt, context=context)
        return {
            "status": "success",
            "execution_engine": "GenericAgent",
            "result": result,
        }

    async def _llm_decompose(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用 LLM 进行真实的树状任务拆解（替代硬编码模拟）"""
        from molib.core.ceo.model_router import ModelRouter
        router = ModelRouter()

        decompose_prompt = f"""你是一个高级任务拆解器。请将以下复杂任务拆解为可执行的子任务树。

任务: {prompt}

请以 JSON 格式返回，格式如下:
{{
  "nodes": [
    {{"id": "1", "action": "收集相关背景资料", "depends_on": []}},
    {{"id": "2", "action": "制定整体策略框架", "depends_on": ["1"]}},
    {{"id": "3", "action": "执行第一阶段", "depends_on": ["2"]}},
    {{"id": "4", "action": "评估并优化", "depends_on": ["3"]}}
  ]
}}

只返回 JSON，不要其他文字。"""

        try:
            result = await router.call_async(
                prompt=decompose_prompt,
                system="你是一个专业的任务拆解专家。只输出 JSON 格式的任务拆解结果。",
                task_type="default",
            )
            text = result.get("text", "")
            # 提取 JSON
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                plan = json.loads(text[start:end])
                nodes = plan.get("nodes", [])
                logger.info(f"LLM 拆解完成: {len(nodes)} 个子任务")
                return {
                    "status": "success",
                    "execution_engine": "LLM_Decomposer",
                    "nodes_explored": len(nodes),
                    "result_summary": f"已将任务拆解为 {len(nodes)} 个子节点",
                    "details": {"sub_tasks": nodes, "confidence": 0.85},
                }
        except Exception as e:
            logger.error(f"LLM 拆解失败: {e}")

        # 最终回退
        return {
            "status": "partial",
            "execution_engine": "LLM_Decomposer_Fallback",
            "result_summary": f"任务拆解回退到默认模板: {prompt[:50]}...",
            "details": {
                "sub_tasks": [
                    {"id": "1", "action": "背景调研", "depends_on": []},
                    {"id": "2", "action": "方案制定", "depends_on": ["1"]},
                    {"id": "3", "action": "执行验证", "depends_on": ["2"]},
                ],
                "confidence": 0.7,
            },
        }


_generic_agent_bridge = GenericAgentBridge()

def get_generic_agent_bridge() -> GenericAgentBridge:
    return _generic_agent_bridge
