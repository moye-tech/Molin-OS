"""墨商BD Worker — v2.1 开源武装升级 (browser-use ⭐50k)

升级内容:
  - prospect_research: browser-use AI浏览器自动化 采集潜在客户信息
  - 保留原有合作方案生成功能
"""
from .base import SmartSubsidiaryWorker as _Base, Task, WorkerResult


class Bd(_Base):
    worker_id = "bd"
    worker_name = "墨商BD"
    description = "商务拓展 (v2.1: browser-use自动化触达 + 合作方案生成)"
    oneliner = "AI浏览器自动化采集+合作方案生成+商务触达"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "AI浏览器自动化客户采集 (browser-use ⭐50k)",
            "合作方案自动生成",
            "报价与合同条款建议",
            "客户关系管理与跟进",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨商BD",
            "vp": "战略",
            "description": "商务拓展 (v2.1: browser-use自动化采集)",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            action = task.payload.get("action", "proposal")

            # ── v2.1: browser-use 自动采集潜在客户 ──
            if action in ("prospect_research", "scrape_clients", "采集客户"):
                output = await self._prospect_research(task.payload)
            else:
                output = await self._generate_proposal(task.payload)

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

    async def _prospect_research(self, payload: dict) -> dict:
        """browser-use AI浏览器自动化采集潜在客户"""
        platform = payload.get("platform", "小红书")
        keyword = payload.get("keyword", "AI服务需求")
        task_desc = payload.get("task", "")

        if not task_desc:
            tasks = {
                "小红书": f"搜索'{keyword}'相关帖子，找到发布过AI工具/服务需求的用户，提取用户昵称、需求内容、粉丝数",
                "LinkedIn": f"搜索'{keyword}'相关公司和决策者，提取公司名、职位、联系方式",
            }
            task_desc = tasks.get(platform, tasks["小红书"])

        try:
            from molib.infra.external.browser_use import execute_browser_task
            result = await execute_browser_task(task_desc, headless=True, max_steps=10)
            return {**result, "action": "prospect_research", "platform": platform}
        except Exception:
            return {
                "action": "prospect_research",
                "platform": platform,
                "keyword": keyword,
                "result": "browser-use不可用，请pip install browser-use并playwright install",
                "status": "unavailable",
            }

    async def _generate_proposal(self, payload: dict) -> dict:
        """现有合作方案生成"""
        client = payload.get("client", "未指定客户")
        industry = payload.get("industry", "")
        needs = payload.get("needs", "")
        budget = payload.get("budget_range", "")

        system = "你是墨商BD——墨麟AI集团商务拓展子公司。请输出结构化合作方案。"
        prompt = (
            f"客户: {client}\n行业: {industry}\n需求: {needs}\n预算: {budget}\n"
            "输出JSON: client, proposal(title/value/deliverables/pricing), engagement_strategy, key_talking_points, risk_notes, next_steps, status='proposal_draft_ready'"
        )
        result = await self.llm_chat_json(prompt, system=system)
        if result:
            return {"client": client, **result, "source": "llm"}
        return {
            "client": client,
            "proposal": {"title": f"{client}合作方案", "value": "提升3倍运营效率", "deliverables": ["AI客服", "内容自动化", "数据看板"], "pricing": {"setup": 5000, "monthly": 2000}},
            "status": "proposal_draft_ready",
            "source": "mock",
        }
