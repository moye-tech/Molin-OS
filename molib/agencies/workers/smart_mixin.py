"""
墨麟OS v2.0 — SmartWorkerMixin 智能Worker基因
解决 BUG-03 (执行前不查经验) + BUG-04 (孤岛执行)

零侵入改造：所有Worker只需将基类从 SubsidiaryWorker 改为 SmartSubsidiaryWorker。
"""


class SmartWorkerMixin:
    """智能Worker基因 — 注入三大能力"""

    async def smart_execute(self, task, context: dict = None):
        """包装execute()，自动加入经验检索和入库"""
        from molib.shared.experience.vault import vault

        context = context or {}
        past_exp = await vault.recall(self.worker_id, task)
        if past_exp:
            context["past_experiences"] = past_exp
            context["exp_hint"] = "【历史成功经验】\n" + "\n---\n".join(past_exp)

        result = await self.execute(task, context)
        await vault.record(self.worker_id, task, result)

        if task.payload.get("plan_id") and getattr(result, "status", None) == "success":
            try:
                from molib.agencies.planning_bridge import PlanningBridge
                PlanningBridge.mark_step_done(task.payload["plan_id"], self.worker_id)
            except (ImportError, Exception):
                pass

        return result

    async def request_collaboration(self, worker_id: str, payload: dict, context: dict = None) -> dict:
        """Worker主动向兄弟子公司发起协作请求"""
        try:
            from molib.agencies.handoff import HandoffManager, HandoffInputData
            input_data = HandoffInputData(
                task_payload=payload,
                pre_handoff_items={"requester": self.worker_id},
                input_history=str(context) if context else ""
            )
            result, _ = HandoffManager.route(worker_id, input_data, self.worker_id)
            return result.output if hasattr(result, "output") else {}
        except (ImportError, Exception):
            return {}


try:
    from molib.agencies.workers.base import SubsidiaryWorker
    class SmartSubsidiaryWorker(SmartWorkerMixin, SubsidiaryWorker):
        pass
except ImportError:
    class SmartSubsidiaryWorker(SmartWorkerMixin):
        worker_id = "unknown"
        async def execute(self, task, context=None):
            raise NotImplementedError
