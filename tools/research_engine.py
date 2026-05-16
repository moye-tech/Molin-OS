#!/usr/bin/env python3
"""
墨麟OS · gpt-researcher接口封装
Agent D / shared Agent 的research-engine技能的实际执行引擎
支持DeepSeek作为LLM后端

用法:
  python3 ~/Molin-OS/tools/research_engine.py "调研主题"
  python3 ~/Molin-OS/tools/research_engine.py "调研主题" --type outline_report
"""
import asyncio
import sys
import json
import os
from pathlib import Path

# 配置使用DeepSeek作为LLM后端
os.environ["OPENAI_API_KEY"] = os.getenv("DEEPSEEK_API_KEY", "")
os.environ["OPENAI_BASE_URL"] = "https://api.deepseek.com/v1"


async def research(query: str, report_type: str = "research_report") -> dict:
    """
    执行深度联网调研
    Args:
        query: 调研主题（越具体越好）
        report_type: research_report / outline_report / custom_report
    Returns:
        dict: { "report": "完整报告", "sources": ["来源URL"], "summary": "摘要" }
    """
    try:
        from gpt_researcher import GPTResearcher
        researcher = GPTResearcher(
            query=query,
            report_type=report_type,
            verbose=False,
        )
        await researcher.conduct_research()
        report = await researcher.write_report()
        sources = researcher.get_source_urls() if hasattr(researcher, 'get_source_urls') else []

        return {
            "status": "success",
            "query": query,
            "report": report,
            "sources": sources,
            "summary": report[:300] + "..." if len(report) > 300 else report,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "query": query,
            "report": "",
            "sources": [],
            "summary": "",
        }


def research_sync(query: str, report_type: str = "research_report") -> dict:
    """同步版本（供Agent技能文件调用）"""
    return asyncio.run(research(query, report_type))


if __name__ == "__main__":
    args = sys.argv[1:]
    query = args[0] if args else "AI Agent技术2026年最新趋势"
    report_type = "research_report"

    if "--type" in args:
        idx = args.index("--type")
        if idx + 1 < len(args):
            report_type = args[idx + 1]

    result = research_sync(query, report_type)
    print(json.dumps(result, ensure_ascii=False, indent=2))
