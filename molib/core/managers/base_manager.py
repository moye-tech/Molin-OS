"""
Base Subsidiary Manager - 子公司管理器基类
实现 CEO → Subsidiary Manager → Worker Agents 三层架构中的中间管理层。
"""

import asyncio
import json
import time
from datetime import date
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from loguru import logger

from molib.agencies.base import Task, AgencyResult
from molib.core.managers.quality_gate import get_quality_gate


@dataclass
class SubTask:
    """子任务定义"""
    id: str
    description: str
    worker_type: str
    estimated_time: int  # 秒
    dependencies: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ManagerResult:
    """管理器结果"""
    task_id: str
    manager_id: str
    status: str  # success / partial_success / error
    subtasks: List[SubTask] = field(default_factory=list)
    results: List[AgencyResult] = field(default_factory=list)
    aggregated_output: Dict[str, Any] = field(default_factory=dict)
    total_cost: float = 0.0
    total_latency: float = 0.0
    error: Optional[str] = None


class BaseSubsidiaryManager(ABC):
    """子公司管理器基类"""

    def __init__(self, subsidiary_id: str, config: Dict[str, Any]):
        self.subsidiary_id = subsidiary_id
        self.config = config
        self.worker_pool = {}  # Worker Agent池，worker_type -> worker实例
        self.task_queue = asyncio.Queue(maxsize=100)
        self.metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "total_latency": 0.0,
            "total_cost": 0.0,
            "worker_import_fallbacks": 0,
            "worker_executions": 0,
            "worker_successes": 0,
            "llm_fallbacks": 0,
        }

        # LLM 路由：统一使用 ModelRouter（token-plan API），不再依赖 Claude Code CLI
        self.claude_enabled = config.get('claude_code_enabled', True)
        self.claude_client = None
        try:
            from molib.core.ceo.model_router import ModelRouter
            self.router = ModelRouter()
        except Exception as e:
            logger.warning(f"ModelRouter init failed: {e}, claude disabled")
            self.claude_enabled = False
            self.router = None

    async def initialize(self):
        """初始化Worker Agents"""
        worker_configs = self.config.get('worker_types', [])
        for worker_type in worker_configs:
            await self._add_worker(worker_type)
        logger.info(f"Subsidiary Manager {self.subsidiary_id} initialized with {len(worker_configs)} worker types")

    async def _add_worker(self, worker_type: str):
        """添加Worker Agent — 尝试真实实例化，失败则创建占位符"""
        try:
            import importlib
            candidate_paths = [
                f"agencies.workers.{worker_type}_worker",
                f"agencies.workers.{worker_type}",
            ]
            for module_path in candidate_paths:
                try:
                    module = importlib.import_module(module_path)
                    worker_base = __import__("agencies.worker", fromlist=["WorkerAgent"]).WorkerAgent
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and issubclass(attr, worker_base) and attr is not worker_base:
                            instance = attr()
                            from molib.core.tools.registry import ToolRegistry
                            instance._tools = ToolRegistry.get_tools_for_agent("worker")
                            self.worker_pool[worker_type] = {
                                "type": worker_type,
                                "available": True,
                                "concurrent_tasks": 0,
                                "max_concurrent": self.config.get('max_concurrent_per_worker', 1),
                                "instance": instance,
                            }
                            logger.info(f"[Worker] 真实实例化 {worker_type} → {module_path}，工具: {list(instance._tools.keys())}")
                            return
                except (ImportError, AttributeError):
                    continue
        except Exception as e:
            logger.debug(f"Worker {worker_type} 真实实例化失败: {e}，使用占位符")

        # 回退到占位符
        self.worker_pool[worker_type] = {
            "type": worker_type,
            "available": True,
            "concurrent_tasks": 0,
            "max_concurrent": self.config.get('max_concurrent_per_worker', 1),
        }
        logger.debug(f"Added placeholder worker {worker_type} to {self.subsidiary_id}")

    async def delegate_task(self, task: Task) -> ManagerResult:
        """任务委派：分解、分配、监控"""
        start_time = time.time()
        self.metrics["total_tasks"] += 1

        try:
            # 1. 任务分析（使用Claude Code或默认逻辑）
            subtasks = await self._analyze_task(task)

            # 2. Worker选择和执行
            results = await self._execute_subtasks(subtasks, task)

            # 3. 结果聚合（使用Claude Code或默认逻辑）
            aggregated_output = await self._aggregate_results(results, task)

            # 4. 计算指标
            latency = time.time() - start_time
            total_cost = sum(r.cost for r in results if r.cost)

            # 更新指标
            self.metrics["successful_tasks"] += 1
            self.metrics["total_latency"] += latency
            self.metrics["total_cost"] += total_cost

            # 返回成功结果
            return ManagerResult(
                task_id=task.task_id,
                manager_id=self.subsidiary_id,
                status="success",
                subtasks=subtasks,
                results=results,
                aggregated_output=aggregated_output,
                total_cost=total_cost,
                total_latency=latency
            )

        except Exception as e:
            logger.error(f"Task delegation failed for {task.task_id}: {e}")
            self.metrics["failed_tasks"] += 1

            return ManagerResult(
                task_id=task.task_id,
                manager_id=self.subsidiary_id,
                status="error",
                error=str(e),
                total_latency=time.time() - start_time
            )

    async def _analyze_task(self, task: Task) -> List[SubTask]:
        """分析任务，拆分为子任务 — 使用 ModelRouter LLM 调用"""
        if self.claude_enabled and self.router:
            try:
                description = str(task.payload.get("description", ""))
                worker_types = self.config.get("worker_types", ["general"])

                system_prompt = (
                    f"你是 {self.subsidiary_id} 子公司的任务分析器。"
                    "请将用户任务拆分为具体的子任务列表，每个子任务分配给合适的 worker 类型。"
                )
                user_prompt = (
                    f"原始任务: {description}\n"
                    f"可用的 worker 类型: {', '.join(worker_types)}\n\n"
                    "请返回 JSON 格式的子任务列表（不要 markdown 包裹），格式如下：\n"
                    '[{"description": "...", "worker_type": "...", "estimated_time": 300, "dependencies": [], "tools": []}]'
                )

                llm_result = await self.router.call_async(
                    prompt=user_prompt,
                    system=system_prompt,
                    task_type="content_creation",
                    team=self.subsidiary_id,
                )

                text = llm_result.get("text", "").strip()
                # 尝试清理可能的 markdown 代码块标记
                if text.startswith("```"):
                    text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                if text.endswith("```"):
                    text = text[:-3].strip()

                subtasks_data = json.loads(text)
                if isinstance(subtasks_data, list) and len(subtasks_data) > 0:
                    subtasks = []
                    for i, sd in enumerate(subtasks_data, 1):
                        subtasks.append(SubTask(
                            id=f"{task.task_id}_subtask_{i}",
                            description=sd.get("description", description),
                            worker_type=sd.get("worker_type", "general"),
                            estimated_time=sd.get("estimated_time", 300),
                            dependencies=sd.get("dependencies", []),
                            tools=sd.get("tools", []),
                            metadata={**sd, "llm_enhanced": True},
                        ))
                    logger.info(f"LLM analyzed [{self.subsidiary_id}] task {task.task_id} → {len(subtasks)} subtasks")
                    return subtasks
                else:
                    logger.warning(f"LLM returned invalid subtask format for {task.task_id}")
            except Exception as e:
                logger.warning(f"LLM analysis failed for {task.task_id}: {e}")
        return self._fallback_task_analysis(task)

    def _fallback_task_analysis(self, task: Task) -> List[SubTask]:
        """Claude Code不可用时的回退任务分析，使用 Manager 配置的 worker_types"""
        worker_types = self.config.get('worker_types', ['general'])
        return [
            SubTask(
                id=f"{task.task_id}_subtask_{i}",
                description=f"[{wt}] {task.payload.get('description', task.task_type)}",
                worker_type=wt,
                estimated_time=300,
                metadata={"fallback": True, "original_task": task.task_type}
            )
            for i, wt in enumerate(worker_types, 1)
        ] if worker_types else [
            SubTask(
                id=f"{task.task_id}_subtask_1",
                description=f"Execute task: {task.task_type}",
                worker_type="general",
                estimated_time=300,
                metadata={"fallback": True, "original_task": task.task_type}
            )
        ]

    async def _execute_subtasks(self, subtasks: List[SubTask], parent_task: Task) -> List[AgencyResult]:
        """执行子任务 — 增强：接入真实 Worker Agent 工具执行 + 进度发布"""
        results = []
        total = len(subtasks)

        for i, subtask in enumerate(subtasks):
            # Feature 1: 发布进度事件
            try:
                from molib.integrations.feishu.progress_card import publish_progress_event
                publish_progress_event(
                    task_id=parent_task.task_id,
                    message_id="",
                    current_step=2,
                    agency=f"{self.subsidiary_id}/{subtask.worker_type}",
                    status=f"执行中 ({i+1}/{total})",
                    eta_seconds=subtask.estimated_time or 120,
                )
            except Exception:
                pass
            try:
                # 优先尝试使用真实 Worker Agent 执行
                worker_agent = self._get_worker_agent(subtask.worker_type)
                if worker_agent is not None:
                    # 预注入历史知识上下文
                    knowledge_context = []
                    try:
                        from molib.core.evolution.engine import EvolutionEngine
                        knowledge_context = EvolutionEngine.retrieve_knowledge(
                            subtask.description, limit=3
                        )
                    except Exception:
                        pass

                    subtask_payload = {
                        "task_id": subtask.id,
                        "description": subtask.description,
                        "parent_task_id": parent_task.task_id,
                        "metadata": subtask.metadata,
                        "tools": subtask.tools,
                        "context": parent_task.payload,
                        "_knowledge_context": knowledge_context,
                    }
                    worker_result = await worker_agent.execute(subtask_payload)

                    result = AgencyResult(
                        task_id=subtask.id,
                        agency_id=self.subsidiary_id,
                        status="success" if worker_result.success else "partial_success",
                        output={
                            "report": worker_result.report,
                            "worker_id": worker_result.metadata.get("worker_id", ""),
                            "steps_count": len(worker_result.steps),
                        },
                        cost=0.0,
                        latency=worker_result.metadata.get("elapsed_seconds", 0),
                    )
                    logger.info(f"[Worker Agent] {worker_agent.worker_id} executed subtask {subtask.id}")
                    self.metrics["worker_executions"] += 1
                    if worker_result.success:
                        self.metrics["worker_successes"] += 1
                else:
                    # 回退到 LLM 执行
                    self.metrics["llm_fallbacks"] += 1
                    worker = self._select_worker(subtask.worker_type)
                    subtask_task = Task(
                        task_id=subtask.id,
                        task_type=subtask.worker_type,
                        payload={
                            "description": subtask.description,
                            "parent_task_id": parent_task.task_id,
                            "metadata": subtask.metadata,
                        },
                        priority=parent_task.priority,
                        requester=f"{self.subsidiary_id}_manager",
                    )
                    result = await self._execute_with_worker(worker, subtask_task)
                    logger.debug(f"[LLM fallback] executed subtask {subtask.id}")

                results.append(result)

            except Exception as e:
                logger.error(f"Subtask {subtask.id} execution failed: {e}")
                results.append(AgencyResult(
                    task_id=subtask.id,
                    agency_id=self.subsidiary_id,
                    status="error",
                    error=str(e),
                ))

        return results

    def _get_worker_agent(self, worker_type: str):
        """获取 Worker Agent 实例（真实工具执行）"""
        import importlib
        candidate_paths = [
            f"agencies.workers.{worker_type}_worker",  # 实际文件名
            f"agencies.workers.{worker_type}",          # 兼容旧命名
        ]
        for module_path in candidate_paths:
            try:
                module = importlib.import_module(module_path)
                worker_base = __import__("agencies.worker", fromlist=["WorkerAgent"]).WorkerAgent
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, worker_base) and attr is not worker_base:
                        instance = attr()
                        # 同步加载工具（避免异步 initialize）
                        from molib.core.tools.registry import ToolRegistry
                        instance._tools = ToolRegistry.get_tools_for_agent("worker")
                        logger.info(f"[Worker] 成功加载 {worker_type} → {module_path}，工具: {list(instance._tools.keys())}")
                        return instance
            except (ImportError, AttributeError):
                continue
        self.metrics.setdefault("worker_import_fallbacks", 0)
        self.metrics["worker_import_fallbacks"] += 1
        logger.debug(f"[Worker] {worker_type} 所有导入路径均失败，将回退 LLM")
        return None

    def _select_worker(self, worker_type: str):
        """选择Worker — 兼容 WorkerAgent 实例和 dict 占位符"""
        worker = self.worker_pool.get(worker_type)
        if not worker:
            worker = self.worker_pool.get("general", {"type": "general", "available": True})

        if hasattr(worker, "execute"):
            return worker

        if not worker.get("available", False):
            raise ValueError(f"No available worker of type {worker_type}")

        return worker

    async def _execute_with_worker(self, worker, task: Task,
                                    model_override: Optional[str] = None) -> AgencyResult:
        """使用Worker执行任务 — 优先使用真实 WorkerAgent，回退到 LLM"""
        import time as _time
        start = _time.time()

        # 如果是真实 WorkerAgent 实例，直接调用 execute
        if hasattr(worker, "execute"):
            try:
                worker_result = await worker.execute({
                    "description": task.payload.get("description", str(task.payload)),
                    "context": task.payload.get("metadata", {}),
                    "expected_output": "结构化执行结果",
                })
                latency = _time.time() - start
                return AgencyResult(
                    task_id=task.task_id,
                    agency_id=self.subsidiary_id,
                    status="success" if worker_result.success else "error",
                    output={"result": worker_result.report, "worker_id": worker_result.metadata.get("worker_id", "")},
                    error=worker_result.error,
                    latency=latency,
                )
            except Exception as e:
                logger.warning(f"WorkerAgent execute failed, falling back to LLM: {e}")

        worker_type = worker.get("type", "general")

        try:
            # 延迟导入避免循环依赖
            from molib.core.ceo.model_router import ModelRouter
            router = ModelRouter()

            # 构建面向 Worker 的 Prompt
            description = task.payload.get("description", str(task.payload))
            metadata = task.payload.get("metadata", {})
            tools_hint = ", ".join(task.payload.get("tools", [])) or "无特定工具"

            system_prompt = (
                f"你是一个专业的 {worker_type} 工作者 (Worker Agent)，"
                f"隶属于 {self.subsidiary_id} 子公司。"
                f"当前日期：{date.today().isoformat()}。所有分析和数据必须基于此日期判断时效性。"
                f"请根据任务描述完成工作，返回结构化的 JSON 结果。\n"
                f"可用工具提示: {tools_hint}"
            )

            user_prompt = (
                f"任务ID: {task.task_id}\n"
                f"任务类型: {task.task_type}\n"
                f"任务描述: {description}\n"
                f"优先级: {task.priority}\n"
                f"上下文: {metadata}\n\n"
                f"请完成此任务并返回 JSON 格式结果，包含：\n"
                f"- summary: 执行摘要\n"
                f"- details: 详细结果\n"
                f"- recommendations: 后续建议列表\n"
                f"- confidence: 结果置信度 (0-1)"
            )

            # 对调研/情报类任务启用联网搜索
            _enable_search = any(k in self.subsidiary_id + worker_type for k in ("research", "data", "情报", "调研"))

            # 通过 ModelRouter 调用 LLM
            call_kwargs = dict(
                prompt=user_prompt,
                system=system_prompt,
                task_type=task.task_type,
                team=self.subsidiary_id,
                enable_search=_enable_search,
            )
            if model_override:
                call_kwargs["model"] = model_override

            llm_result = await router.call_async(**call_kwargs)

            latency = _time.time() - start
            result = AgencyResult(
                task_id=task.task_id,
                agency_id=self.subsidiary_id,
                status="success",
                output={
                    "result": llm_result.get("text", ""),
                    "model_used": llm_result.get("model", "unknown"),
                    "provider": llm_result.get("provider", "unknown"),
                    "worker_type": worker_type,
                },
                cost=llm_result.get("cost", 0.0),
                latency=round(latency, 2),
            )

            # ── 质量门控评估 ──
            quality_gate = get_quality_gate()

            async def _retry_cb(t, model):
                return await self._execute_with_worker(worker, t, model_override=model)

            result, eval_meta = await quality_gate.evaluate(
                result, task, retry_callback=_retry_cb
            )
            if eval_meta.get("action") != "pass":
                result.output = {**(result.output or {}), "quality_gate": eval_meta}

            return result

        except Exception as e:
            logger.error(f"Worker execution failed [{worker_type}] for {task.task_id}: {e}")
            latency = _time.time() - start
            return AgencyResult(
                task_id=task.task_id,
                agency_id=self.subsidiary_id,
                status="error",
                output={"worker_type": worker_type, "error_detail": str(e)},
                error=str(e),
                latency=round(latency, 2),
            )

    async def _aggregate_results(self, results: List[AgencyResult], original_task: Task) -> Dict[str, Any]:
        """聚合结果 — 使用 ModelRouter LLM 调用"""
        if self.claude_enabled and self.router:
            try:
                description = str(original_task.payload.get("description", ""))

                # 构建各子任务结果文本
                result_parts = []
                for r in results:
                    if isinstance(r.output, dict):
                        text = r.output.get("report") or r.output.get("result") or r.output.get("content", "")
                    else:
                        text = str(r.output) if r.output else ""
                    result_parts.append(
                        f"- [{r.task_id}] 状态: {r.status}\n{text}"
                    )

                system_prompt = (
                    f"你是 {self.subsidiary_id} 子公司的结果聚合器。"
                    "请将多个子任务的执行结果整合为一份完整的、用户可读的综合报告。"
                    "要求内容详实、条理清晰，使用中文输出。"
                )
                user_prompt = (
                    f"原始任务: {description}\n\n"
                    f"各子任务结果：\n{''.join(result_parts)}\n\n"
                    "请生成一份综合分析报告，包含：\n"
                    "1. 核心发现/结论\n"
                    "2. 详细分析内容（按子任务展开）\n"
                    "3. 行动建议（具体、可执行）\n"
                    "4. 风险提示或注意事项"
                )

                llm_result = await self.router.call_async(
                    prompt=user_prompt,
                    system=system_prompt,
                    task_type="content_creation",
                    team=self.subsidiary_id,
                )

                aggregated_text = llm_result.get("text", "")
                return {
                    "status": "completed",
                    "content": aggregated_text,
                    "summary": aggregated_text[:300] if aggregated_text else f"[{self.subsidiary_id}] 聚合完成",
                    "success_rate": sum(1 for r in results if r.status == "success") / max(1, len(results)),
                    "results_count": len(results),
                    "success_count": sum(1 for r in results if r.status == "success"),
                }

            except Exception as e:
                logger.warning(f"LLM aggregation failed: {e}, using fallback")
                return await self._fallback_aggregate_results(results)
        else:
            return await self._fallback_aggregate_results(results)

    async def _fallback_aggregate_results(self, results: List[AgencyResult]) -> Dict[str, Any]:
        """Claude Code不可用时的回退结果聚合 — 提取真实输出内容"""
        success_count = sum(1 for r in results if r.status == "success")
        total_count = len(results)

        contents = []
        for r in results:
            if isinstance(r.output, dict):
                text = r.output.get("result") or r.output.get("report") or r.output.get("content", "")
            else:
                text = str(r.output) if r.output else ""
            if text:
                contents.append(f"[{r.task_id}]\n{text}")

        return {
            "status": "completed",
            "summary": f"Aggregated {total_count} results ({success_count} successful)",
            "content": "\n\n---\n\n".join(contents) if contents else "No content available",
            "success_rate": success_count / total_count if total_count > 0 else 0,
            "results_count": total_count,
            "success_count": success_count
        }

    def get_metrics(self) -> Dict[str, Any]:
        """获取管理器指标"""
        avg_latency = (
            self.metrics["total_latency"] / self.metrics["successful_tasks"]
            if self.metrics["successful_tasks"] > 0 else 0
        )

        success_rate = (
            self.metrics["successful_tasks"] / self.metrics["total_tasks"]
            if self.metrics["total_tasks"] > 0 else 0
        )

        worker_executions = self.metrics.get("worker_executions", 0)
        worker_successes = self.metrics.get("worker_successes", 0)
        worker_success_rate = (
            worker_successes / worker_executions if worker_executions > 0 else 0
        )

        return {
            **self.metrics,
            "avg_latency": avg_latency,
            "success_rate": success_rate,
            "worker_success_rate": round(worker_success_rate, 4),
            "llm_fallback_count": self.metrics.get("llm_fallbacks", 0),
            "claude_enabled": self.claude_enabled,
            "worker_count": len(self.worker_pool)
        }

    @abstractmethod
    async def can_handle(self, task: Task) -> bool:
        """检查是否能处理此任务"""
        pass

    @abstractmethod
    def get_trigger_keywords(self) -> List[str]:
        """获取触发关键词"""
        pass