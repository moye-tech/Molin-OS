"""墨学教育 Worker — v2.1 开源武装升级 (STORM ⭐22k)

升级内容:
  - storm_outline: 用STORM生成深度调研后自动设计课程大纲
  - multi_agent_classroom: 多Agent互动课堂编排
  - debate: 辩论式教学场景
"""
from .base import SmartSubsidiaryWorker as _Base, Task, WorkerResult


class Education(_Base):
    worker_id = "education"
    worker_name = "墨学教育"
    description = "课程设计与知识付费 (v2.1: STORM深度调研+课程大纲自动生成)"
    oneliner = "STORM深度调研驱动课程设计·互动课堂·辩论教学"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "STORM深度调研驱动课程大纲 (⭐22k)",
            "多Agent互动课堂编排",
            "辩论式教学场景搭建",
            "知识付费定价策略建议",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨学教育",
            "vp": "运营",
            "description": "课程设计 (v2.1: STORM调研+大纲自动生成)",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            action = task.payload.get("action", "course_design")

            # ── v2.1: STORM深度调研驱动课程大纲 ──
            if action in ("storm_outline", "deep_course"):
                output = await self._storm_course_design(task.payload)

            elif action == "multi_agent_classroom":
                output = await self._classroom(task.payload)

            elif action == "debate":
                output = await self._debate(task.payload)

            else:
                output = await self._course_design(task.payload)

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

    async def _storm_course_design(self, payload: dict) -> dict:
        """STORM深度调研驱动课程大纲设计 (⭐22k)"""
        course_name = payload.get("course_name", "未命名课程")
        weeks = payload.get("duration_weeks", 4)
        price = payload.get("price", 299)

        storm_result = None
        try:
            from molib.infra.external.storm_research import storm_report
            storm_result = await storm_report(f"{course_name} 课程设计：行业现状、学员痛点、竞品课程分析、差异化定位")
        except Exception:
            pass

        # 基于STORM结果生成课程大纲 (LLM)
        storm_context = ""
        if storm_result and storm_result.get("status") == "success":
            storm_context = storm_result.get("report", "")[:3000]

        system = "你是课程设计师。请基于深度调研结果设计课程大纲。返回严格JSON。"
        prompt = (
            f"课程: {course_name}\n周数: {weeks}周\n受众: {payload.get('target_audience', '通用')}\n定价: {price}元\n"
        )
        if storm_context:
            prompt += f"\n【STORM深度调研】\n{storm_context}\n"

        prompt += (
            "输出JSON: course_name, duration('N周'), outline[{week, title, topics[]}], "
            "pricing{original, early_bird}, target_audience, unique_selling_points[], "
            "competitor_gap(与竞品差异), storm_research_used: true/false, status='course_outline_ready'"
        )

        result = await self.llm_chat_json(prompt, system=system)
        if result:
            result.setdefault("course_name", course_name)
            result.setdefault("duration", f"{weeks}周")
            result.setdefault("storm_research_used", bool(storm_context))
            return {**result, "source": "llm+storm"}
        return self._fallback_outline(course_name, weeks, price)

    def _fallback_outline(self, course_name: str, weeks: int, price: int) -> dict:
        return {
            "course_name": course_name,
            "duration": f"{weeks}周",
            "outline": [{"week": i+1, "title": f"第{i+1}周：{course_name}", "topics": ["核心概念", "案例实战"]} for i in range(weeks)],
            "pricing": {"original": price, "early_bird": int(price * 0.7)},
            "storm_research_used": False,
            "status": "course_outline_ready",
            "source": "mock",
        }

    async def _classroom(self, payload: dict) -> dict:
        prompt = f"设计多Agent课堂：主题={payload.get('topic')}, 轮次={payload.get('max_turns',10)}, 风格={payload.get('style','互动式')}\n输出JSON: classroom_type, agents[], topic, max_turns, status='orchestrator_initialized'"
        result = await self.llm_chat_json(prompt, system="你是教育技术架构师。返回严格JSON。")
        if result:
            result.setdefault("status", "orchestrator_initialized")
            return result
        return {"classroom_type": "interactive", "agents_available": ["AI教师", "AI助教", "思考者"], "topic": payload.get("topic", ""), "status": "orchestrator_initialized", "source": "mock"}

    async def _debate(self, payload: dict) -> dict:
        prompt = f"设计辩论教学：主题={payload.get('topic')}, 轮次={payload.get('max_turns',12)}, 难度={payload.get('difficulty','中等')}\n输出JSON: topic, participants[], max_rounds, debate_rules[], status='debate_initialized'"
        result = await self.llm_chat_json(prompt, system="你是辩论教学设计师。返回严格JSON。")
        if result:
            return result
        return {"topic": payload.get("topic", ""), "participants": ["主持人", "正方", "反方", "评审"], "max_rounds": 3, "status": "debate_initialized", "source": "mock"}

    async def _course_design(self, payload: dict) -> dict:
        course_name = payload.get("course_name", "未命名课程")
        weeks = payload.get("duration_weeks", 4)
        price = payload.get("price", 299)
        prompt = f"设计课程大纲：名称={course_name}, 周数={weeks}, 受众={payload.get('target_audience','通用')}, 定价={price}\n输出JSON: course_name, duration, outline[{week,title,topics}], pricing{{original,early_bird}}, status='course_outline_ready'"
        result = await self.llm_chat_json(prompt, system="你是课程设计师。返回严格JSON。")
        if result:
            result.setdefault("course_name", course_name)
            return {**result, "source": "llm"}
        return self._fallback_outline(course_name, weeks, price)
