"""墨学教育 Worker — 课程设计 + 多Agent互动课堂 (LLM驱动)"""
from .base import SmartSubsidiaryWorker as _Base, Task, WorkerResult


class Education(_Base):
    worker_id = "education"
    worker_name = "墨学教育"
    description = "课程设计与知识付费 | 多Agent互动课堂"
    oneliner = "课程设计知识付费课堂"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "课程大纲与学习路径设计",
            "多Agent互动课堂编排",
            "辩论式教学场景搭建",
            "知识付费定价策略建议",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨学教育",
            "vp": "运营",
            "description": "课程设计与知识付费 | 多Agent互动课堂",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            action = task.payload.get("action", "course_design")

            if action == "multi_agent_classroom":
                # LLM驱动：生成多Agent课堂编排方案
                prompt = f"""你是一位教育技术架构师。根据以下需求设计多Agent互动课堂编排方案：

主题：{task.payload.get("topic", "未指定")}
最大轮次：{task.payload.get("max_turns", 10)}
教学风格：{task.payload.get("style", "互动式")}

请以JSON格式返回：
- classroom_type: 课堂类型（interactive/debate/guided）
- agents: 每个Agent的名称和角色定义列表
- topic: 主题
- max_turns: 最大轮次
- status: "orchestrator_initialized"
"""
                system = "你是一位专业的AI教育架构师，擅长多Agent互动课堂编排。返回严格JSON。"
                llm_output = await self.llm_chat_json(prompt, system=system)

                # fallback
                if not llm_output:
                    llm_output = {
                        "action": "classroom_ready",
                        "classroom_type": "interactive",
                        "agents_available": ["AI教师", "AI助教", "思考者", "好奇宝"],
                        "topic": task.payload.get("topic", ""),
                        "max_turns": task.payload.get("max_turns", 10),
                        "orchestrator_ready": True,
                        "status": "orchestrator_initialized",
                    }
                else:
                    llm_output.setdefault("action", "classroom_ready")
                    llm_output.setdefault("orchestrator_ready", True)

                output = llm_output

            elif action == "debate":
                # LLM驱动：生成辩论式教学场景
                prompt = f"""你是一位教育辩论设计师。根据以下需求设计辩论式教学场景：

主题：{task.payload.get("topic", "未指定")}
最大轮次：{task.payload.get("max_turns", 12)}
难度：{task.payload.get("difficulty", "中等")}

请以JSON格式返回：
- topic: 辩论主题
- participants: 参与者角色列表（如主持人、正方辩手、反方辩手、评审）
- max_rounds: 辩论轮数（max_turns / 4）
- debate_rules: 辩论规则简要列表
- status: "debate_initialized"
"""
                system = "你是一位专业的辩论教学设计师。返回严格JSON。"
                llm_output = await self.llm_chat_json(prompt, system=system)

                if not llm_output:
                    llm_output = {
                        "action": "debate_ready",
                        "topic": task.payload.get("topic", ""),
                        "participants": ["主持人", "正方辩手", "反方辩手", "评审"],
                        "max_rounds": task.payload.get("max_turns", 12) // 4,
                        "status": "debate_initialized",
                    }
                else:
                    llm_output.setdefault("action", "debate_ready")

                output = llm_output

            else:
                # 默认课程设计：LLM生成课程大纲
                course_name = task.payload.get("course_name", "未命名课程")
                weeks = task.payload.get("duration_weeks", 4)
                price = task.payload.get("price", 299)

                prompt = f"""你是一位课程设计师。根据以下信息设计课程大纲：

课程名称：{course_name}
持续周数：{weeks}周
目标受众：{task.payload.get("target_audience", "通用")}
定价：{price}元

请以JSON格式返回：
- course_name: 课程名称
- duration: 持续周数字符串（如"4周"）
- outline: 每周的课程大纲列表，每个元素包含 week (int), title (str), topics (list[str])
- pricing: 定价方案，包含 original (int), early_bird (int, original的7折)
- status: "course_outline_ready"
"""
                system = "你是一位专业的课程设计师，擅长结构化课程大纲设计。返回严格JSON。"
                llm_output = await self.llm_chat_json(prompt, system=system)

                if not llm_output:
                    llm_output = {
                        "course_name": course_name,
                        "duration": f"{weeks}周",
                        "outline": [
                            {"week": i + 1, "title": f"第{i + 1}周：{course_name}"}
                            for i in range(weeks)
                        ],
                        "pricing": {
                            "original": price,
                            "early_bird": int(price * 0.7),
                        },
                        "status": "course_outline_ready",
                    }
                else:
                    # 确保必要字段存在
                    llm_output.setdefault("course_name", course_name)
                    llm_output.setdefault("duration", f"{weeks}周")
                    llm_output.setdefault("pricing", {"original": price, "early_bird": int(price * 0.7)})
                    if "outline" not in llm_output or not llm_output["outline"]:
                        llm_output["outline"] = [
                            {"week": i + 1, "title": f"第{i + 1}周：{course_name}"}
                            for i in range(weeks)
                        ]
                    llm_output.setdefault("status", "course_outline_ready")

                output = llm_output

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
