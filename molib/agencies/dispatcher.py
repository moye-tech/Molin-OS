"""
Hermes OS — 任务调度器
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
        """调度任务到对应子公司"""
        worker = self.workers.get(task.task_type)
        if not worker:
            return AgencyResult(
                task_id=task.task_id,
                agency_id="unknown",
                status="error",
                error=f"No agency found for task_type: {task.task_type}",
            )
        return await worker.execute(task)
