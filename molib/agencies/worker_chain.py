"""
墨麟OS v2.0 — WorkerChain + ContextBus 协作链与上下文总线
解决 BUG-04 (孤岛执行) + BUG-05 (上下文断层)
"""
from dataclasses import dataclass, field


@dataclass
class ContextBus:
    """上下文总线：贯穿WorkerChain整个生命周期"""
    ceo_intent: str = ""
    accumulated_outputs: dict = field(default_factory=dict)
    insights: list = field(default_factory=list)

    def inject(self, worker_id: str, output: dict):
        self.accumulated_outputs[worker_id] = output
        if isinstance(output, dict):
            key = output.get("summary") or output.get("key_finding") or output.get("result")
            if key:
                self.insights.append(f"[{worker_id}]: {key}")

    def to_context_str(self) -> str:
        lines = [f"CEO意图: {self.ceo_intent}"]
        if self.insights:
            lines.append("上游协作产出:")
            lines += [f"  * {i}" for i in self.insights]
        return "\n".join(lines)


class WorkerChain:
    """按序执行多Worker，上下文沿链累积，完成后结晶为SOP"""

    def __init__(self, worker_ids: list, original_task, context: dict = None):
        self.worker_ids = worker_ids
        self.original_task = original_task
        self.bus = ContextBus(
            ceo_intent=str(getattr(original_task, 'payload', original_task))
        )

    async def execute(self, use_fault_tolerance: bool = True):
        """
        执行 WorkerChain。

        Args:
            use_fault_tolerance: 是否使用 Prefect 断点续跑（默认 True，自动降级）
        """
        # 尝试使用 Prefect 容错执行
        if use_fault_tolerance:
            try:
                from molib.shared.fault_tolerance import FaultTolerantChain
                ft_chain = FaultTolerantChain(
                    worker_ids=self.worker_ids,
                    original_task=self.original_task,
                    context=self.bus.accumulated_outputs,
                )
                result = await ft_chain.execute()
                if result.get("status") != "error":
                    await self._crystallize_sop()
                    return result
            except ImportError:
                pass
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"FaultTolerantChain 失败，降级原生执行: {e}")

        # 原生执行（降级模式）
        final_output = {}

        for i, wid in enumerate(self.worker_ids):
            worker = self._get_worker(wid)
            if not worker:
                continue

            enriched = {
                **getattr(self.original_task, 'payload', {}),
                "__context__": self.bus.to_context_str(),
                "__upstream__": self.bus.accumulated_outputs,
            }

            task_id = f"{getattr(self.original_task, 'task_id', 'chain')}_s{i}"

            class _Task:
                def __init__(self, tid, ttype, payload):
                    self.task_id = tid
                    self.task_type = ttype
                    self.payload = payload

            sub_task = _Task(task_id, wid, enriched)

            try:
                if hasattr(worker, 'smart_execute'):
                    result = await worker.smart_execute(sub_task)
                elif hasattr(worker, 'execute'):
                    result = await worker.execute(
                        {"task_type": wid, "payload": enriched}
                    )
                else:
                    continue
            except Exception as e:
                self.bus.inject(wid, {"error": str(e)})
                continue

            output = getattr(result, 'output', result) if hasattr(result, 'output') else result
            self.bus.inject(wid, output if isinstance(output, dict) else {"result": str(output)})
            final_output = output

        await self._crystallize_sop()

        return {
            "task_id": getattr(self.original_task, 'task_id', 'chain'),
            "status": "success",
            "output": {"final": final_output, "chain": self.bus.accumulated_outputs},
            "chain": self.bus.insights,
            "mode": "native",
        }

    def _get_worker(self, worker_id: str):
        worker_map = {
            "content_writer": "molib.agencies.workers.content_writer.ContentWriter",
            "designer": "molib.agencies.workers.designer.Designer",
            "research": "molib.agencies.workers.research.ResearchWorker",
            "short_video": "molib.agencies.workers.short_video.ShortVideo",
            "ecommerce": "molib.agencies.workers.ecommerce.EcommerceWorker",
            "legal": "molib.agencies.workers.legal.LegalWorker",
            "finance": "molib.agencies.workers.finance.FinanceWorker",
            "education": "molib.agencies.workers.education.EducationWorker",
            "developer": "molib.agencies.workers.developer.Developer",
            "customer_service": "molib.agencies.workers.customer_service.CustomerServiceWorker",
            "global_marketing": "molib.agencies.workers.global_marketing.GlobalMarketingWorker",
            "data_analyst": "molib.agencies.workers.data_analyst.DataAnalyst",
        }
        if worker_id in worker_map:
            module_path, class_name = worker_map[worker_id].rsplit(".", 1)
            try:
                mod = __import__(module_path, fromlist=[class_name])
                return getattr(mod, class_name)()
            except (ImportError, AttributeError):
                pass
        return None

    async def _crystallize_sop(self):
        sop = (
            f"[SOP] 任务: {getattr(self.original_task, 'task_type', 'unknown')}\n"
            f"成功协作链: {' -> '.join(self.worker_ids)}\n"
            f"CEO意图: {self.bus.ceo_intent[:100]}\n"
            f"产出: {str(self.bus.insights)[:200]}"
        )
        try:
            from molib.shared.knowledge.rag_engine import RAGEngine
            RAGEngine().index_text(sop, namespace="sop:chains")
        except (ImportError, Exception):
            pass
