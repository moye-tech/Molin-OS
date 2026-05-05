"""墨学教育 Worker — 课程设计 + 多Agent互动课堂"""
from .base import SubsidiaryWorker, Task, WorkerResult

class Education(SubsidiaryWorker):
    worker_id = "education"
    worker_name = "墨学教育"
    description = "课程设计与知识付费 | 多Agent互动课堂"
    oneliner = "课程设计知识付费课堂"

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            action = task.payload.get("action", "course_design")

            if action == "multi_agent_classroom":
                from ...shared.ai.multi_agent_orchestrator import (
                    create_classroom_orchestrator, OrchestratorState
                )
                # 异步非生成器模式
                state = OrchestratorState(
                    available_agent_ids=["teacher", "assistant", "student1", "student2"],
                    max_turns=task.payload.get("max_turns", 10),
                    messages=[{"role": "user", "content": task.payload.get("topic", "")}]
                )
                orchestrator = create_classroom_orchestrator(None)  # llm_func在运行时注入
                output = {
                    "action": "classroom_ready",
                    "classroom_type": "interactive",
                    "agents_available": ["AI教师", "AI助教", "思考者", "好奇宝"],
                    "topic": task.payload.get("topic", ""),
                    "max_turns": state.max_turns,
                    "orchestrator_ready": True,
                    # 实际执行需要注入llm_func
                    "status": "orchestrator_initialized"
                }
            elif action == "debate":
                from ...shared.ai.multi_agent_orchestrator import (
                    create_debate_orchestrator, OrchestratorState
                )
                state = OrchestratorState(
                    available_agent_ids=["moderator", "pro", "con", "judge"],
                    max_turns=task.payload.get("max_turns", 12),
                )
                orchestrator = create_debate_orchestrator(None)
                output = {
                    "action": "debate_ready",
                    "topic": task.payload.get("topic", ""),
                    "participants": ["主持人", "正方辩手", "反方辩手", "评审"],
                    "max_rounds": state.max_turns // 4,
                    "status": "debate_initialized"
                }
            else:
                course_name = task.payload.get("course_name", "未命名课程")
                weeks = task.payload.get("duration_weeks", 4)
                output = {
                    "course_name": course_name,
                    "duration": "{}周".format(weeks),
                    "outline": [
                        {"week": i+1, "title": "第{}周：{}".format(i+1, course_name)}
                        for i in range(weeks)
                    ],
                    "pricing": {
                        "original": task.payload.get("price", 299),
                        "early_bird": int(task.payload.get("price", 299) * 0.7),
                    },
                    "status": "course_outline_ready"
                }
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
