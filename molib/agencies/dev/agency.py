"""墨码研发子公司 — 代码开发、脚本编写、接口设计、自动化部署"""
import json
import time

from molib.agencies.base import BaseAgency, Task, AgencyResult

DEV_SYSTEM_PROMPT = """你是墨码研发子公司的工程师。
根据需求提供代码实现方案、架构设计或自动化脚本。

遵循编码规范：
1. 使用清晰的变量名和函数名
2. 避免过度复杂的单行代码
3. 注意边界条件和异常处理
4. 不要使用不存在的 API

输出必须是严格的 JSON 格式：
{
  "task_type": "code|script|api|debug",
  "approach": "实现思路",
  "code_blocks": [
    {"language": "语言", "description": "说明", "code": "代码内容"}
  ],
  "dependencies": ["依赖1", "依赖2"],
  "risks": ["风险1"],
  "quality_score": 质量评分(1-10)
}"""


class DevAgency(BaseAgency):
    agency_id = "dev"
    agency_name = "墨码研发"
    personality = "务实的技术负责人，追求简洁有效的方案，不炫技"
    trigger_keywords = ["开发", "部署", "脚本", "自动化", "接口", "代码", "API", "修复", "bug", "调试", "爬虫"]
    approval_level = "low"
    cost_level = "medium"

    def _parse_dev_json(self, text: str) -> dict:
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            if "```json" in text:
                try:
                    start = text.index("```json") + 7
                    end = text.index("```", start)
                    return json.loads(text[start:end].strip())
                except Exception:
                    pass
        return {
            "task_type": "code",
            "approach": text[:300],
            "code_blocks": [],
            "dependencies": [],
            "risks": [],
            "quality_score": 5.0,
        }

    async def execute(self, task: Task) -> AgencyResult:
        desc = task.payload.get("description", task.payload.get("topic", ""))
        prompt = f"请为以下需求给出开发实现方案：{desc}"

        # 挂载 agent-skills 工具文档
        tools_doc = ""
        try:
            from molib.integrations.external_tools.agent_skills import get_agent_skills
            skills = get_agent_skills()
            tools_doc = f"\n\n[Available Skills]:\n{skills.get_skill_system_prompt_addon()}"
        except ImportError:
            pass

        prompt += tools_doc

        start = time.time()
        res = await self.router.call_async(
            prompt=prompt, system=DEV_SYSTEM_PROMPT,
            task_type="code_execution", team="dev",
        )
        parsed = self._parse_dev_json(res.get("text", ""))

        score = parsed.get("quality_score", 5.0)
        return AgencyResult(
            task_id=task.task_id, agency_id=self.agency_id, status="success",
            output={
                "task_type": parsed.get("task_type", "code"),
                "approach": parsed.get("approach", ""),
                "code_blocks": parsed.get("code_blocks", []),
                "dependencies": parsed.get("dependencies", []),
                "risks": parsed.get("risks", []),
                "quality_score": score,
                "model_used": res.get("model", "unknown"),
            },
            cost=res.get("cost", 0.0),
            latency=round(time.time() - start, 2),
        )
