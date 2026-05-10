"""
墨麟OS — GPT-Researcher 集成 (⭐18k)
=====================================
自主深度调研Agent，自动联网搜索→综合→生成带引用报告。

用法:
    from molib.infra.external.gpt_researcher import deep_research
    result = await deep_research("AI Agent 2026年行业趋势", depth="medium")

集成点: Research Worker 替代静态LLM输出，提供实时联网调研
"""

from __future__ import annotations

import os
import json
import asyncio
from typing import Optional


async def deep_research(
    query: str,
    depth: str = "medium",
    report_type: str = "research_report",
    max_sources: int = 5,
    tone: str = "professional",
    language: str = "zh-CN",
) -> dict:
    """
    执行深度联网调研并返回结构化报告。

    Args:
        query: 调研主题
        depth: 深度 (basic/medium/deep)
        report_type: 报告类型 (research_report/resource_report/outline_report)
        max_sources: 最大引用源数量
        tone: 语调
        language: 报告语言

    Returns:
        {
            "query": str,
            "report": str (Markdown),
            "sources": [{"url": str, "title": str}],
            "key_findings": [str],
            "source": "gpt-researcher"
        }
    """
    try:
        from gpt_researcher import GPTResearcher

        # 从环境变量获取 API key
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("DEEPSEEK_API_KEY", "")
        llm_kwargs = {"timeout": 120, "temperature": 0.2}

        researcher = GPTResearcher(
            query=query,
            report_type=report_type,
            report_source="web",
            tone=tone,
            language=language,
            max_subtopics=3 if depth == "basic" else 5 if depth == "medium" else 8,
        )
        # 注入 API key
        if api_key:
            researcher.set_verbose(False)
            if hasattr(researcher, 'llm_kwargs'):
                researcher.llm_kwargs = {**getattr(researcher, 'llm_kwargs', {}), "api_key": api_key}

        report = await asyncio.wait_for(
            researcher.conduct_research(), timeout=120
        )
        full_report = await asyncio.wait_for(
            researcher.write_report(), timeout=180
        )

        sources = []
        try:
            context = researcher.get_research_context()
            if context:
                for src in context[:max_sources]:
                    sources.append({
                        "url": getattr(src, "url", ""),
                        "title": getattr(src, "title", ""),
                    })
        except Exception:
            pass

        # 提取关键发现
        key_findings = []
        for line in full_report.split("\n"):
            line = line.strip()
            if line.startswith(("- ", "* ", "• ")) and len(line) > 5:
                key_findings.append(line.lstrip("- *• "))
                if len(key_findings) >= 8:
                    break

        return {
            "query": query,
            "report": full_report,
            "sources": sources,
            "key_findings": key_findings,
            "depth": depth,
            "source": "gpt-researcher",
            "status": "success",
        }

    except ImportError:
        return {
            "query": query,
            "error": "gpt-researcher not installed. Run: pip install gpt-researcher",
            "status": "unavailable",
            "source": "gpt-researcher",
        }
    except asyncio.TimeoutError:
        return {
            "query": query,
            "error": "Research timed out (180s)",
            "status": "timeout",
            "source": "gpt-researcher",
        }
    except Exception as e:
        return {
            "query": query,
            "error": str(e),
            "status": "error",
            "source": "gpt-researcher",
        }


async def quick_scan(query: str) -> dict:
    """快速扫描（basic depth，适合简单问题）"""
    return await deep_research(query, depth="basic", max_sources=3)


async def competitor_analysis(domain: str, competitors: list[str] = None) -> dict:
    """竞品深度分析"""
    comps = ", ".join(competitors) if competitors else "主要竞品"
    query = f"{domain}领域竞品分析：{comps}，包括市场份额、差异化、优劣势"
    return await deep_research(query, depth="medium", report_type="research_report")
