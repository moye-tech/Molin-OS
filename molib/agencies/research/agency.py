"""墨思研究子公司 v2.5 — 行业研究、竞品分析、趋势洞察、技术情报

v2.5 升级：
- GPT-Researcher 实时联网调研层（替代纯 LLM 训练知识）
- 三步流水线：联网采集 → 分析综合 → 结构化输出
- 研究数据注入 ContextBus，供下游 Worker 使用
- 降级保护：GPT-Researcher 不可用时 fallback 到纯 LLM
"""

import json
import time
import logging

from molib.agencies.base import BaseAgency, Task, AgencyResult

logger = logging.getLogger(__name__)

RESEARCH_SYSTEM_PROMPT = """你是墨思研究子公司的行业研究员。
根据提供的实时研究数据（由 GPT-Researcher 联网采集），进行深度分析和结构化的研究报告输出。

输出必须是严格的 JSON 格式：
{
  "research_type": "market|competitor|trend|technology",
  "executive_summary": "执行摘要（基于实时数据）",
  "key_findings": ["发现1", "发现2", "发现3"],
  "data_sources": ["来源1", "来源2"],
  "market_size": "市场规模描述",
  "competitors": [
    {"name": "竞品名", "strengths": ["优势"], "weaknesses": ["劣势"], "market_share": "市场份额"}
  ],
  "trends": ["趋势1", "趋势2"],
  "opportunities": ["机会1", "机会2"],
  "threats": ["威胁1", "威胁2"],
  "recommendations": ["建议1", "建议2"],
  "quality_score": 质量评分(1-10)
}"""


class ResearchAgency(BaseAgency):
    agency_id = "research"
    agency_name = "墨思研究"
    personality = "严谨的研究分析师，擅长从数据中发现洞察，不满足于表面答案"
    trigger_keywords = ["研究", "竞品", "趋势", "情报", "行业", "调研", "分析报", "竞品分析", "市场"]
    approval_level = "low"
    cost_level = "medium"

    # ── GPT-Researcher 配置 ──
    _gpt_researcher_available: bool = None  # 延迟检测

    @classmethod
    def _check_gpt_researcher(cls) -> bool:
        """检测 GPT-Researcher 是否可用"""
        if cls._gpt_researcher_available is not None:
            return cls._gpt_researcher_available
        try:
            from gpt_researcher import GPTResearcher
            cls._gpt_researcher_available = True
            return True
        except ImportError:
            logger.warning("GPT-Researcher 未安装，将使用纯 LLM 模式")
            cls._gpt_researcher_available = False
            return False

    async def _conduct_web_research(self, topic: str, depth: str = "standard") -> dict:
        """
        使用 GPT-Researcher 进行实时联网调研。

        Args:
            topic: 研究主题
            depth: 研究深度 - "quick"(快速) / "standard"(标准) / "deep"(深度)

        Returns:
            {"report": str, "sources": list, "success": bool}
        """
        if not self._check_gpt_researcher():
            return {"report": "", "sources": [], "success": False}

        # 映射深度到 GPT-Researcher 的报告类型
        report_type_map = {
            "quick": "research_report",       # 快速报告
            "standard": "research_report",    # 标准报告
            "deep": "deep",                   # 深度报告
        }
        report_type = report_type_map.get(depth, "research_report")

        try:
            from gpt_researcher import GPTResearcher

            # 使用免费模型做研究（降低成本）
            researcher = GPTResearcher(
                query=topic,
                report_type=report_type,
                report_source="web",  # 强制联网
            )

            logger.info(f"墨思研究 GPT-Researcher 开始联网调研: {topic}")
            research_data = await researcher.conduct_research()
            report = await researcher.write_report()

            # 提取数据源
            sources = []
            if hasattr(researcher, 'get_research_context'):
                context = researcher.get_research_context()
                if isinstance(context, list):
                    sources = [s.get("url", str(s)) for s in context[:10]]

            logger.info(f"墨思研究 GPT-Researcher 完成: {len(report)} 字符, {len(sources)} 个来源")
            return {
                "report": report,
                "sources": sources[:30],  # 最多30个来源
                "success": True,
            }

        except Exception as e:
            logger.warning(f"GPT-Researcher 调研失败: {e}，降级到纯 LLM 模式")
            return {"report": "", "sources": [], "success": False, "error": str(e)}

    def _parse_research_json(self, text: str) -> dict:
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
            "research_type": "market",
            "executive_summary": text[:300],
            "key_findings": [],
            "data_sources": [],
            "market_size": "",
            "competitors": [],
            "trends": [],
            "opportunities": [],
            "threats": [],
            "recommendations": [],
            "quality_score": 5.0,
        }

    async def execute(self, task: Task) -> AgencyResult:
        desc = task.payload.get("description", task.payload.get("topic", ""))
        depth = task.payload.get("depth", "standard")

        start = time.time()

        # ── 第一步：GPT-Researcher 联网采集实时数据 ──
        web_research = await self._conduct_web_research(desc, depth)

        # ── 第二步：构建增强 prompt ──
        if web_research.get("success") and web_research.get("report"):
            # 有实时数据：注入到 prompt
            research_context = web_research["report"]
            sources_text = "\n".join(f"- {s}" for s in web_research.get("sources", [])[:10])
            prompt = (
                f"请基于以下实时联网调研数据，进行深度分析并输出结构化研究报告。\n\n"
                f"=== 研究主题 ===\n{desc}\n\n"
                f"=== 实时调研数据（GPT-Researcher 联网采集） ===\n{research_context[:8000]}\n\n"
                f"=== 数据来源 ===\n{sources_text}\n\n"
                f"请综合分析以上数据，提取关键洞察，输出结构化 JSON 报告。"
            )
            data_mode = "GPT-Researcher 实时联网"
        else:
            # 降级到纯 LLM
            prompt = f"请研究以下主题并输出结构化研究报告：{desc}"
            # 尝试挂载 Web Browser 工具
            tools_doc = ""
            try:
                from molib.integrations.external_tools.web_browser import get_web_browser
                browser = get_web_browser()
                tools_doc = f"\n\n[Available Tools]:\n- {browser.tool_name}: 可用于实时网络搜索和信息获取"
            except ImportError:
                pass
            prompt += tools_doc
            data_mode = "LLM 训练知识（GPT-Researcher 不可用）"

        # ── 第三步：LLM 分析综合 ──
        # 使用 DeepSeek Pro 做分析（研究质量优先）
        res = await self.router.call_async(
            prompt=prompt, system=RESEARCH_SYSTEM_PROMPT,
            task_type="deep_research", team="research",
        )
        parsed = self._parse_research_json(res.get("text", ""))

        # 合并 GPT-Researcher 的来源
        if web_research.get("sources") and not parsed.get("data_sources"):
            parsed["data_sources"] = web_research["sources"]

        score = parsed.get("quality_score", 5.0)
        return AgencyResult(
            task_id=task.task_id, agency_id=self.agency_id, status="success",
            output={
                "research_type": parsed.get("research_type", "market"),
                "executive_summary": parsed.get("executive_summary", ""),
                "key_findings": parsed.get("key_findings", []),
                "data_sources": parsed.get("data_sources", []),
                "competitors": parsed.get("competitors", []),
                "trends": parsed.get("trends", []),
                "opportunities": parsed.get("opportunities", []),
                "threats": parsed.get("threats", []),
                "recommendations": parsed.get("recommendations", []),
                "quality_score": score,
                "model_used": res.get("model", "unknown"),
                "data_mode": data_mode,
                "web_report_length": len(web_research.get("report", "")),
            },
            cost=res.get("cost", 0.0),
            latency=round(time.time() - start, 2),
        )
