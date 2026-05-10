"""墨影IP子公司 — 小红书/抖音/知乎内容创作、社媒运营、爆款文案"""
import json
import time
from pathlib import Path

from molib.agencies.base import BaseAgency, Task, AgencyResult

IP_SYSTEM_PROMPT = """你是墨影IP子公司的内容创作专家，擅长为不同社媒平台生成高质量内容。
根据话题和平台特性生成有吸引力的社媒内容。

输出必须是严格的 JSON 格式（每篇内容）：
{
  "platform": "平台名",
  "title": "标题",
  "content": "正文内容",
  "hashtags": ["标签1", "标签2"],
  "ab_variant": "A|B",
  "hook_score": 吸引力评分(1-10),
  "quality_score": 质量评分(1-10)
}"""

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "xiaohongshu.txt"
PROMPT_TEXT = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.exists() else ""
if PROMPT_TEXT:
    SYSTEM = PROMPT_TEXT + "\n\n" + IP_SYSTEM_PROMPT
else:
    SYSTEM = IP_SYSTEM_PROMPT


class IpAgency(BaseAgency):
    agency_id = "ip"
    agency_name = "墨影内容"
    personality = "资深内容总监，10年社媒经验，追求真实有温度的表达"
    trigger_keywords = ["内容", "小红书", "文案", "爆款", "标题", "抖音", "知乎", "选题", "社媒"]
    approval_level = "low"
    cost_level = "medium"

    def _parse_ip_json(self, text: str) -> dict:
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
            "platform": "小红书",
            "title": "",
            "content": text[:500],
            "hashtags": [],
            "ab_variant": "A",
            "hook_score": 5.0,
            "quality_score": 5.0,
        }

    async def execute(self, task: Task) -> AgencyResult:
        topic = task.payload.get("topic", "AI副业赚钱")
        platform = task.payload.get("platform", "小红书")
        count = task.payload.get("count", 1)
        desc = task.payload.get("description", "")
        start = time.time()

        # CEO 简报上下文（人性化：知道 WHY 被调用）
        brief = self.enrich_task_context(task)
        identity = self.get_identity_prompt()

        # 加载 SocialHub 与 VisionEngine 工具
        tools_doc = ""
        try:
            from molib.integrations.external_tools.social_hub import get_social_hub
            from molib.integrations.external_tools.vision_engine import get_vision_engine
            social = get_social_hub()
            vision = get_vision_engine()
            tools_doc = f"\n[Available Tools]:\n- {social.tool_name}: {social.get_available_commands()}\n- {vision.tool_name}: {vision.get_available_commands()}"
        except ImportError:
            pass

        platform_prompt = SYSTEM.replace("小红书", platform)
        # 注入身份 + CEO 简报到 system prompt
        full_system = f"{identity}\n\n{platform_prompt}\n\n{brief}"
        results, total_cost = [], 0.0

        for i in range(count):
            variant = "A" if i % 2 == 0 else "B"
            prompt = (
                f"话题：{topic}\n平台：{platform}\n变体：{variant}\n任务描述：{desc}\n"
                f"目标人群：25-35岁 AI 副业感兴趣\n请按格式生成1篇内容。" + tools_doc
            )
            res = await self.router.call_async(
                prompt=prompt, system=full_system,
                task_type="content_creation", team="ip",
            )
            total_cost += res.get("cost", 0)
            parsed = self._parse_ip_json(res.get("text", ""))
            parsed["ab_variant"] = variant
            results.append(parsed)

        return AgencyResult(
            task_id=task.task_id, agency_id=self.agency_id, status="success",
            output={"contents": results, "count": len(results)},
            cost=total_cost, latency=round(time.time() - start, 2),
        )
