"""墨研竞情 Worker — 竞争情报 + 群体智能预测（基于MiroFish设计模式）"""
from .base import SubsidiaryWorker, Task, WorkerResult


class Research(SubsidiaryWorker):
    worker_id = "research"
    worker_name = "墨研竞情"
    description = "竞品监控、行业情报与群体智能预测"
    oneliner = "从情报采集到趋势预测，以群体智能辅助决策"

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            action = task.payload.get("action", "analyze")
            domain = task.payload.get("domain", "AI Agent")
            topic = task.payload.get("topic", "")
            context_info = task.payload.get("context", "")

            if action == "predict":
                # 群体智能预测（基于MiroFish设计模式）
                from molib.intelligence.predictor import predict
                result = await predict(
                    topic=topic or domain,
                    context=context_info,
                    num_agents=task.payload.get("num_agents", 5),
                )
                output = {
                    "action": "prediction",
                    "topic": result["topic"],
                    "num_agents": result["num_agents"],
                    "final_report": result["final_report"],
                    "confidence_avg": result["confidence_avg"],
                }
            elif action == "trending":
                # 趋势分析
                output = await self._analyze_trends(domain)
            else:
                # 默认竞品分析
                output = await self._analyze_competitors(
                    task.payload.get("competitors", []),
                    domain,
                )

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
                output={"error": str(e)},
            )

    async def _analyze_competitors(self, competitors: list, domain: str) -> dict:
        return {
            "action": "competitor_analysis",
            "domain": domain,
            "competitors": [{"name": c, "threat": "medium"} for c in competitors] if competitors else [],
            "status": "intel_ready",
        }

    async def _analyze_trends(self, domain: str) -> dict:
        return {
            "action": "trend_analysis",
            "domain": domain,
            "trends": [
                {"trend": "Agent协作主流化", "impact": "高"},
                {"trend": "成本控制关键", "impact": "高"},
            ],
            "status": "intel_ready",
        }
