"""
墨麟OS v2.0 — 任务调度器
升级: dispatch() 优先使用 SmartDispatcher 语义路由，
兜底使用原有精确匹配逻辑。
"""
from .base import Task, AgencyResult
from .worker import WorkerAgent


class Dispatcher:
    def __init__(self):
        self.workers: dict[str, WorkerAgent] = {}

    def register(self, agency):
        """注册子公司 Agency"""
        self.workers[agency.agency_id] = WorkerAgent(agency)

    async def dispatch(self, task: Task) -> AgencyResult:
        """v2.0 升级：三步路由（SmartDispatcher → 字符串匹配兜底）"""
        # 优先尝试 SmartDispatcher 语义路由
        try:
            from molib.agencies.smart_dispatcher import smart_dispatcher
            result = await smart_dispatcher.dispatch(task)
            if result and not isinstance(result, dict):
                return result
            if result and isinstance(result, dict) and result.get("fallback"):
                # SmartDispatcher 降级，继续兜底
                pass
            elif result:
                # 包装为 AgencyResult
                return AgencyResult(
                    task_id=task.task_id,
                    agency_id=result.get("agency_id", "smart"),
                    status=result.get("status", "success"),
                    output=result.get("output", result),
                )
        except (ImportError, Exception):
            pass

        # 兜底：原有精确匹配逻辑
        worker = self.workers.get(task.task_type)
        if not worker:
            return AgencyResult(
                task_id=task.task_id,
                agency_id="unknown",
                status="error",
                error=f"No agency found for task_type: {task.task_type}",
            )
        return await worker.execute(task)
