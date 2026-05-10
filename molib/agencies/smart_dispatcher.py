"""
墨麟OS v2.0 — SmartDispatcher 智能调度器
解决 BUG-02 (调度盲区)

三步路由策略：SOP金库 → 协作规则表 → Handoff语义评分
"""


class SmartDispatcher:
    """语义路由 + WorkerChain编排"""

    COLLAB_RULES = {
        "营销文案": ["research", "content_writer", "designer"],
        "小红书":   ["research", "content_writer", "designer"],
        "产品上架": ["content_writer", "designer", "ecommerce"],
        "竞品报告": ["research", "data_analyst", "content_writer"],
        "法律合同": ["legal", "finance"],
        "出海":     ["research", "global_marketing", "legal"],
        "课程":     ["research", "education", "content_writer"],
        "视频":     ["content_writer", "short_video"],
        "闲鱼商品": ["content_writer", "customer_service"],
        "AI设计":   ["designer", "developer"],
    }

    async def dispatch(self, task, context: dict = None):
        """三步路由"""
        chain = await self._recall_sop(task)
        if not chain:
            chain = self._match_collab_rule(task)

        if len(chain) <= 1:
            return await self._dispatch_single(task, context)
        else:
            return await self._dispatch_chain(task, chain, context)

    async def _dispatch_single(self, task, context):
        try:
            from molib.agencies.handoff import HandoffManager, HandoffInputData
            result, _ = HandoffManager.route(
                task.task_type,
                HandoffInputData(
                    task_payload=task.payload,
                    input_history=str(context or {})
                )
            )
            return result
        except (ImportError, Exception) as e:
            return {"error": str(e), "fallback": True}

    async def _dispatch_chain(self, task, worker_ids, context):
        try:
            from molib.agencies.worker_chain import WorkerChain
            chain = WorkerChain(worker_ids, task, context)
            return await chain.execute()
        except ImportError:
            if worker_ids:
                return await self._dispatch_single(task, context)
            return {"error": "WorkerChain不可用", "fallback": True}

    def _match_collab_rule(self, task) -> list:
        desc = str(task.payload) if hasattr(task, 'payload') else str(task)
        for kw, workers in self.COLLAB_RULES.items():
            if kw in desc:
                return workers
        return [task.task_type] if hasattr(task, 'task_type') else []

    async def _recall_sop(self, task) -> list:
        try:
            from molib.shared.knowledge.rag_engine import RAGEngine
            desc = str(task.payload)[:100] if hasattr(task, 'payload') else str(task)
            results = RAGEngine().search(desc, namespace="sop:chains", top_k=1)
            if not results:
                return []
            sop_text = results[0].get("text", "")
            import re
            m = re.search(r"成功协作链: (.+)", sop_text)
            if m:
                return [w.strip() for w in m.group(1).split("→")]
        except (ImportError, Exception):
            pass
        return []


smart_dispatcher = SmartDispatcher()
