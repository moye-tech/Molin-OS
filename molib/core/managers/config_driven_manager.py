"""
ConfigDrivenManager — 配置驱动的通用子公司管理器
用一个类 + TOML 配置替代 12 个几乎相同的 Manager 子类，
消除约 5,000 行重复代码。

现有的 12 个 *_manager.py 文件可逐步废弃：
  - 如果某个 Manager 有独特的业务逻辑（不只是关键词/工具差异），
    保留其子类并 override 对应方法。
  - 纯配置差异的 Manager 直接由本类接管。
"""

import asyncio
from typing import Dict, Any, List, Optional
from loguru import logger

from .base_manager import BaseSubsidiaryManager, SubTask
from molib.agencies.base import Task, AgencyResult


class ConfigDrivenManager(BaseSubsidiaryManager):
    """
    通用配置驱动管理器 — 所有行为从配置字典中读取。

    config 示例（来自 managers.toml + subsidiaries.toml 合并）：
    {
        "subsidiary_id": "growth",
        "worker_types": ["marketing_writer", "ab_test_designer", "growth_analyst"],
        "trigger_keywords": ["增长", "营销", "获客", ...],
        "worker_type_mapping": {
            "marketing_writer": ["营销", "文案", "推广"],
            "ab_test_designer": ["测试", "A/B", "实验"],
            "growth_analyst": ["分析", "数据", "漏斗"]
        },
        "tools": {
            "marketing_writer": ["content_generator", "seo_optimizer"],
            ...
        },
        "fallback_recommendations": ["优化渠道", "监控指标"],
        "max_concurrent_tasks": 3,
        "claude_code_enabled": false
    }
    """

    def __init__(self, config: Dict[str, Any]):
        subsidiary_id = config.get("subsidiary_id", "generic")
        config.setdefault("subsidiary_id", subsidiary_id)
        super().__init__(subsidiary_id=subsidiary_id, config=config)

        # 从配置加载领域特定数据
        self.worker_type_mapping: Dict[str, List[str]] = config.get("worker_type_mapping", {})
        self.domain_tools: Dict[str, List[str]] = config.get("tools", {})
        self.trigger_keywords_list: List[str] = config.get("trigger_keywords", [])
        self.fallback_recommendations: List[str] = config.get("fallback_recommendations", [])
        self.task_type_aliases: List[str] = config.get("task_type_aliases", [subsidiary_id])
        self.domain_terms: List[str] = config.get("domain_terms", [])

        logger.info(
            f"ConfigDrivenManager[{subsidiary_id}] initialized: "
            f"{len(self.worker_type_mapping)} worker types, "
            f"{len(self.trigger_keywords_list)} keywords"
        )

    # ── 抽象方法实现 ──────────────────────────────────

    async def can_handle(self, task: Task) -> bool:
        """根据配置的关键词判断是否能处理任务"""
        task_description = str(task.payload.get("description", "")).lower()
        task_type = task.task_type.lower()

        # 1. 任务类型匹配
        if task_type in self.task_type_aliases:
            return True

        # 2. 关键词匹配
        for keyword in self.trigger_keywords_list:
            if keyword.lower() in task_description:
                return True

        # 3. 领域术语匹配
        for term in self.domain_terms:
            if term.lower() in task_description:
                return True

        return False

    def get_trigger_keywords(self) -> List[str]:
        return self.trigger_keywords_list

    # ── 领域特定任务分析 ──────────────────────────────

    async def _analyze_task(self, task: Task) -> List[SubTask]:
        """使用 ModelRouter LLM 或配置驱动的回退分析"""
        if self.claude_enabled and getattr(self, "router", None):
            try:
                description = str(task.payload.get("description", ""))
                worker_types = list(self.worker_type_mapping.keys()) or self.config.get("worker_types", ["general"])

                system_prompt = (
                    f"你是 {self.subsidiary_id} 子公司的任务分析器，专注于该领域的专业分析。"
                    "请将任务拆解为具体的、可执行的子任务。"
                )
                user_prompt = (
                    f"任务描述: {description}\n"
                    f"可用 worker 类型: {', '.join(worker_types)}\n\n"
                    "请返回 JSON 格式的子任务列表，格式如下：\n"
                    '[{"description": "...", "worker_type": "...", "estimated_time": 300}]'
                )

                llm_result = await self.router.call_async(
                    prompt=user_prompt,
                    system=system_prompt,
                    task_type="content_creation",
                    team=self.subsidiary_id,
                )

                text = llm_result.get("text", "").strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                if text.endswith("```"):
                    text = text[:-3].strip()

                import json
                subtasks_data = json.loads(text)
                if isinstance(subtasks_data, list) and len(subtasks_data) > 0:
                    subtasks = []
                    for i, sd in enumerate(subtasks_data, 1):
                        wt = self._determine_worker_type(sd)
                        subtasks.append(SubTask(
                            id=f"{task.task_id}_subtask_{i}",
                            description=sd.get("description", description),
                            worker_type=wt,
                            estimated_time=sd.get("estimated_time", 300),
                            dependencies=sd.get("dependencies", []),
                            tools=self.domain_tools.get(wt, []),
                            metadata={
                                **sd,
                                "domain": self.subsidiary_id,
                                "original_task_type": task.task_type,
                                "llm_enhanced": True,
                            },
                        ))
                    logger.info(
                        f"LLM analyzed [{self.subsidiary_id}] task "
                        f"{task.task_id} → {len(subtasks)} subtasks"
                    )
                    return subtasks
                else:
                    logger.warning(f"LLM returned invalid subtask format for {task.task_id}")
            except Exception as e:
                logger.warning(f"LLM analysis failed for {task.task_id}: {e}")

        return await self._config_driven_fallback(task)

    def _determine_worker_type(self, subtask_data: Dict[str, Any]) -> str:
        """根据配置的 worker_type_mapping 匹配最合适的 Worker"""
        desc = subtask_data.get("description", "").lower()
        for worker_type, keywords in self.worker_type_mapping.items():
            for kw in keywords:
                if kw.lower() in desc:
                    return worker_type
        # 返回第一个 worker type 作为默认
        if self.worker_type_mapping:
            return next(iter(self.worker_type_mapping))
        return "general"

    async def _config_driven_fallback(self, task: Task) -> List[SubTask]:
        """LLM 驱动的任务拆解，替代关键词 if-else"""
        import json as _json, re as _re
        desc = str(task.payload.get("description", ""))
        worker_types = list(self.worker_type_mapping.keys()) or self.config.get('worker_types', ['general'])
        tools_hint = {wt: self.domain_tools.get(wt, []) for wt in worker_types}

        # 尝试 LLM 拆解
        try:
            from molib.core.ceo.model_router import ModelRouter
            router = ModelRouter()
            decompose_prompt = f"""你是{self.subsidiary_id}子公司的 Manager。

任务描述：{desc}

可用 Worker 类型及工具：
{chr(10).join(f"- {wt}: {', '.join(tools)}" for wt, tools in tools_hint.items())}

请将任务分解为 1-3 个子任务，每个分配给最合适的 Worker。
如果任务简单，1 个就够了。不要强行分配不需要的 Worker。

输出纯 JSON 数组（不要代码块标记）：
[
  {{
    "description": "具体子任务描述",
    "worker_type": "worker类型",
    "estimated_time": 30
  }}
]"""
            result = await router.call_async(
                prompt=decompose_prompt,
                task_type="task_decomposition",
                team=self.subsidiary_id,
            )
            text = result.get("text", "")
            match = _re.search(r'\[[\s\S]*\]', text)
            if match:
                subtasks_data = _json.loads(match.group())
                subtasks = []
                for i, sd in enumerate(subtasks_data, 1):
                    wt = sd.get("worker_type", worker_types[0])
                    subtasks.append(SubTask(
                        id=f"{task.task_id}_subtask_{i}",
                        description=sd.get("description", desc)[:200],
                        worker_type=wt,
                        estimated_time=sd.get("estimated_time", 300),
                        tools=self.domain_tools.get(wt, []),
                        metadata={"llm_decomposed": True, "domain": self.subsidiary_id},
                    ))
                if subtasks:
                    logger.info(f"[LLM] [{self.subsidiary_id}] 任务拆解为 {len(subtasks)} 个子任务")
                    return subtasks
        except Exception as e:
            logger.warning(f"[{self.subsidiary_id}] LLM 任务拆解失败: {e}，使用关键词兜底")

        # 最终兜底：关键词匹配（保留原逻辑）
        task_description = desc.lower()
        selected_worker = worker_types[0] if worker_types else "general"
        for worker_type, keywords in self.worker_type_mapping.items():
            if any(kw.lower() in task_description for kw in keywords):
                selected_worker = worker_type
                break

        return [SubTask(
            id=f"{task.task_id}_subtask_1",
            description=f"[{selected_worker}] {desc[:150]}",
            worker_type=selected_worker,
            estimated_time=600,
            tools=self.domain_tools.get(selected_worker, []),
            metadata={"keyword_fallback": True, "domain": self.subsidiary_id},
        )]

    # ── 子任务执行（支持并行） ────────────────────────

    async def _execute_subtasks(
        self, subtasks: List[SubTask], parent_task: Task
    ) -> List[AgencyResult]:
        """支持并行的子任务执行"""
        results = []

        # 分离有无依赖的任务
        no_deps = [st for st in subtasks if not st.dependencies]
        has_deps = [st for st in subtasks if st.dependencies]

        # 并行执行无依赖任务
        if no_deps:
            parallel = await self._execute_parallel(no_deps, parent_task)
            results.extend(parallel)

        # 顺序执行有依赖任务
        completed_ids = {r.task_id for r in results}
        for st in has_deps:
            if all(d in completed_ids for d in st.dependencies):
                r = await self._execute_single(st, parent_task)
                results.append(r)
                completed_ids.add(r.task_id)
            else:
                logger.warning(f"Subtask {st.id} deps not met: {st.dependencies}")
                results.append(AgencyResult(
                    task_id=st.id, agency_id=self.subsidiary_id,
                    status="error", error=f"Dependencies not met: {st.dependencies}",
                ))

        return results

    async def _execute_parallel(
        self, subtasks: List[SubTask], parent_task: Task
    ) -> List[AgencyResult]:
        """并行执行子任务"""
        coros = [self._execute_single(st, parent_task) for st in subtasks]
        raw = await asyncio.gather(*coros, return_exceptions=True)
        results = []
        for i, r in enumerate(raw):
            if isinstance(r, Exception):
                logger.error(f"Parallel subtask {subtasks[i].id} failed: {r}")
                results.append(AgencyResult(
                    task_id=subtasks[i].id, agency_id=self.subsidiary_id,
                    status="error", error=str(r),
                ))
            else:
                results.append(r)
        return results

    async def _execute_single(
        self, subtask: SubTask, parent_task: Task
    ) -> AgencyResult:
        """执行单个子任务 — 优先尝试真实 Worker Agent，回退 LLM"""
        # 1. 优先尝试真实 Worker Agent
        worker_agent = self._get_worker_agent(subtask.worker_type)
        if worker_agent is not None:
            subtask_payload = {
                "task_id": subtask.id,
                "description": subtask.description,
                "parent_task_id": parent_task.task_id,
                "metadata": subtask.metadata,
                "tools": subtask.tools,
                "context": parent_task.payload,
            }
            worker_result = await worker_agent.execute(subtask_payload)
            self.metrics["worker_executions"] += 1
            if worker_result.success:
                self.metrics["worker_successes"] += 1
                logger.info(f"[Worker Agent] {worker_agent.worker_id} executed subtask {subtask.id}")
                return AgencyResult(
                    task_id=subtask.id,
                    agency_id=self.subsidiary_id,
                    status="success",
                    output={
                        "report": worker_result.report,
                        "worker_id": worker_agent.worker_id,
                        "steps_count": len(worker_result.steps),
                    },
                    cost=0.0,
                    latency=worker_result.metadata.get("elapsed_seconds", 0),
                )
            # Worker 失败 → 回退到 LLM 执行（带联网搜索）
            logger.warning(f"[Worker Agent] {worker_agent.worker_id} 执行失败: {worker_result.report[:200]}")

        # 2. 回退到 LLM 执行
        self.metrics["llm_fallbacks"] += 1
        worker = self._select_worker(subtask.worker_type)
        subtask_task = Task(
            task_id=subtask.id,
            task_type=subtask.worker_type,
            payload={
                "description": subtask.description,
                "parent_task_id": parent_task.task_id,
                "metadata": subtask.metadata,
                "tools": subtask.tools,
            },
            priority=parent_task.priority,
            requester=f"{self.subsidiary_id}_manager",
        )
        return await self._execute_with_worker(worker, subtask_task)

    # ── 结果聚合 ──────────────────────────────────────

    async def _fallback_aggregate_results(self, results: List[AgencyResult]) -> Dict[str, Any]:
        """LLM 驱动的结果聚合 — 整合 Worker 真实产出，生成综合分析报告"""
        success_count = sum(1 for r in results if r.status == "success")
        total_count = len(results)

        # 提取各结果的真实内容
        contents = []
        for r in results:
            if isinstance(r.output, dict):
                text = r.output.get("result") or r.output.get("report") or r.output.get("content", "")
            else:
                text = str(r.output) if r.output else ""
            if text:
                contents.append(f"[{r.task_id}]\n{text[:1500]}")

        raw_content = "\n\n---\n\n".join(contents) if contents else "No content available"

        # 尝试 LLM 聚合
        if getattr(self, "router", None):
            try:
                agg_prompt = f"""你是 {self.subsidiary_id} 子公司的结果聚合器。

原始子任务结果：
{raw_content[:6000]}

请生成一份综合分析报告，包含：
1. 核心结论
2. 各子任务发现
3. 行动建议
4. 风险提示"""
                llm_result = await self.router.call_async(
                    prompt=agg_prompt,
                    system=f"你是专业的 {self.subsidiary_id} 分析师。用中文输出完整的分析报告。",
                    task_type="content_creation",
                    team=self.subsidiary_id,
                )
                summary = llm_result.get("text", raw_content)
            except Exception as e:
                logger.warning(f"[{self.subsidiary_id}] LLM aggregation failed: {e}")
                summary = raw_content
        else:
            summary = raw_content

        return {
            "status": "completed",
            "content": raw_content,
            "summary": summary,
            "success_rate": success_count / total_count if total_count > 0 else 0,
            "results_count": total_count,
            "success_count": success_count,
            "recommendations": self.fallback_recommendations or [],
        }

    # ── 指标 ──────────────────────────────────────────

    def get_metrics(self) -> Dict[str, Any]:
        base = super().get_metrics()
        return {
            **base,
            "domain": self.subsidiary_id,
            "configured_worker_types": list(self.worker_type_mapping.keys()),
            "trigger_keywords_count": len(self.trigger_keywords_list),
        }
