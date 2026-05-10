"""墨育教育子公司 — 课程设计、大纲生成、评估方案、招生方案"""
import json
import time
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path

from molib.agencies.base import BaseAgency, Task, AgencyResult

EDU_TASKS = ["course_design", "syllabus_generation", "assessment_design", "enrollment_plan"]

COURSE_SYSTEM_PROMPT = """你是墨育教育子公司的课程设计师。
根据用户需求生成结构化的教育课程方案。

输出必须是严格的 JSON 格式：
{
  "course_name": "课程名称",
  "target_audience": "目标学员",
  "duration_hours": 总课时数(数字),
  "modules": [
    {
      "title": "模块名称",
      "description": "模块描述",
      "hours": 课时数,
      "key_points": ["知识点1", "知识点2"]
    }
  ],
  "learning_outcomes": ["学习成果1", "学习成果2"],
  "prerequisites": ["前置要求"],
  "quality_score": 质量评分(1-10)
}"""

ENROLLMENT_SYSTEM_PROMPT = """你是墨育教育子公司的招生策划师。
根据课程特点设计招生方案。

输出必须是严格的 JSON 格式：
{
  "target_channels": ["招生渠道1", "招生渠道2"],
  "messaging_strategy": "核心宣传策略",
  "pricing_tiers": [
    {"name": "档位名", "price": 价格(数字), "features": ["权益1", "权益2"]}
  ],
  "timeline": "招生时间线",
  "conversion_tactics": ["转化手段1", "转化手段2"],
  "quality_score": 质量评分(1-10)
}"""


@dataclass
class CourseRecord:
    """课程记录"""
    id: str
    name: str
    task_type: str
    content: dict = field(default_factory=dict)
    quality_score: float = 0.0
    created_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "task_type": self.task_type,
            "content": self.content,
            "quality_score": self.quality_score,
            "created_at": self.created_at,
        }


class EduAgency(BaseAgency):
    agency_id = "edu"
    trigger_keywords = ["课程", "训练营", "知识付费", "教学", "教培", "培训", "学习", "招生"]
    approval_level = "low"
    cost_level = "medium"

    def __init__(self):
        super().__init__()
        self._course_db: List[CourseRecord] = []
        self._load_sqlite()

    def _load_sqlite(self):
        try:
            from molib.infra.memory.sqlite_client import SQLiteClient
            self._db = SQLiteClient()
        except ImportError:
            self._db = None

    def _select_task_type(self, desc: str) -> str:
        desc_l = desc.lower()
        if any(k in desc_l for k in ["招生", "营销", "推广", "获客"]):
            return "enrollment_plan"
        if any(k in desc_l for k in ["评估", "考试", "测试", "考核"]):
            return "assessment_design"
        if any(k in desc_l for k in ["大纲", "课表", "章节"]):
            return "syllabus_generation"
        return "course_design"

    def _parse_llm_json(self, text: str) -> Optional[dict]:
        """从 LLM 输出中提取 JSON"""
        text = text.strip()
        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # 尝试提取代码块中的 JSON
        if "```json" in text:
            start = text.index("```json") + 7
            end = text.index("```", start)
            try:
                return json.loads(text[start:end].strip())
            except (json.JSONDecodeError, ValueError):
                pass
        if "```" in text:
            start = text.index("```") + 3
            end = text.index("```", start)
            try:
                return json.loads(text[start:end].strip())
            except (json.JSONDecodeError, ValueError):
                pass
        return None

    async def _execute_course(self, task: Task, prompt: str, system: str) -> AgencyResult:
        """执行课程设计类任务"""
        start = time.time()
        res = await self.router.call_async(
            prompt=prompt, system=system,
            task_type="content_creation", team="edu",
        )
        parsed = self._parse_llm_json(res.get("text", ""))
        if parsed is None:
            parsed = {"outline": res.get("text", ""), "quality_score": 5.0}

        score = parsed.get("quality_score", 5.0)
        course = CourseRecord(
            id=f"edu_{int(time.time())}_{hash(prompt) % 10000}",
            name=parsed.get("course_name", parsed.get("target_channels", "未命名课程")),
            task_type=self._select_task_type(task.payload.get("description", "")),
            content=parsed,
            quality_score=score,
            created_at=time.time(),
        )
        self._course_db.append(course)

        # 持久化到 SQLite
        if self._db:
            try:
                await self._db.store_memory(
                    key=f"edu_course_{course.id}",
                    data={"course_name": course.name, "content": course.content, "quality_score": course.quality_score},
                    scenario="transactional",
                    namespace="edu"
                )
            except Exception:
                pass

        return AgencyResult(
            task_id=task.task_id, agency_id=self.agency_id, status="success",
            output={
                "course": course.to_dict(),
                "quality_score": score,
                "model_used": res.get("model", "unknown"),
            },
            cost=res.get("cost", 0.0),
            latency=round(time.time() - start, 2),
        )

    async def execute(self, task: Task) -> AgencyResult:
        self.load_sop()
        sop_prompt = self.get_sop_prompt()
        desc = task.payload.get("description", task.payload.get("topic", ""))
        task_type = self._select_task_type(desc)

        # 查询历史课程记录
        history_info = ""
        if self._db:
            try:
                memories = await self._db.retrieve_memory(
                    key="edu_course", scenario="transactional", namespace="edu", limit=3
                )
                if memories:
                    history_info = "\n\n历史参考:\n" + "\n".join(
                        f"- {m['data'].get('course_name', m['key'])}" for m in memories
                    )
            except Exception:
                pass

        if task_type == "enrollment_plan":
            system = ENROLLMENT_SYSTEM_PROMPT
            prompt = f"请为以下需求设计招生方案：{desc}{history_info}"
        else:
            system = COURSE_SYSTEM_PROMPT
            prompt = f"请为以下需求设计课程方案：{desc}{history_info}"

        if sop_prompt:
            prompt = f"请遵循以下SOP规范：\n{sop_prompt}\n\n{prompt}"

        return await self._execute_course(task, prompt, system)
