"""
Hermes OS — Worker 执行器
"""
from .base import BaseAgency, Task, AgencyResult

class WorkerAgent:
    def __init__(self, agency: BaseAgency):
        self.agency = agency
    
    async def execute(self, task: Task) -> AgencyResult:
        # 加载子公司技能，注入上下文
        skills = self.agency.load_skills()
        identity = self.agency.get_identity_prompt()
        context = self.agency.enrich_task_context(task)
        
        # 如果有 Hermes Agent，调用它执行
        # 否则用 LLM 直接执行
        try:
            return await self.agency.execute(task)
        except Exception as e:
            return AgencyResult(
                task_id=task.task_id,
                agency_id=self.agency.agency_id,
                status="error",
                error=str(e),
            )
