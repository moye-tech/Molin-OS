#!/usr/bin/env python3
"""
Molin-OS Memory Retriever — 统一记忆检索入口

Agent 通过此模块检索历史知识做决策。
同时检索 Obsidian（结构化知识） + Supermemory（语义记忆）。

用法:
    from molib.memory.retriever import retrieve_context

    context = retrieve_context(
        query="转化率提升策略",
        agent_name="edu",
        top_k=5
    )
"""

from typing import Optional

from .obsidian_reader import search_obsidian, search_section
from .ranker import rank_results, deduplicate, filter_by_type


def retrieve_context(
    query: str,
    agent_name: Optional[str] = None,
    top_k: int = 5,
    section_filter: Optional[list[str]] = None,
    days_back: int = 30,
) -> dict:
    """
    统一记忆检索入口。

    Args:
        query: 检索问题
        agent_name: Agent ID (如 content, finance)，None = 全部
        top_k: 返回结果上限
        section_filter: 区块类型过滤 (如 ["洞察", "结论"])
        days_back: 回溯天数

    Returns:
        {
            "query": str,
            "results": [{
                "source": "obsidian" | "supermemory",
                "agent": str,
                "date": str,
                "title": str,
                "content": str (截断),
                "score": int,
                "filepath": str,
                "sections": [{"heading", "content"}]
            }],
            "summary": str (给 agent 的上下文摘要),
            "total_found": int
        }
    """
    # 1. Obsidian 检索
    obsidian_results = search_obsidian(
        query=query,
        agent_name=agent_name,
        days_back=days_back,
        top_k=top_k * 2,  # 先多取再排序
    )

    # 2. Rank + Deduplicate
    all_results = rank_results(query, obsidian_results)
    all_results = deduplicate(all_results)

    # 3. 区块过滤
    if section_filter:
        all_results = filter_by_type(all_results, section_filter)

    # 4. 截断到 top_k
    final_results = all_results[:top_k]

    # 5. 生成摘要
    summary = _build_summary(query, final_results)

    return {
        "query": query,
        "agent": agent_name,
        "results": final_results,
        "summary": summary,
        "total_found": len(final_results),
    }


def retrieve_insights(
    topic: str,
    agent_name: Optional[str] = None,
    top_k: int = 3,
) -> dict:
    """
    只检索洞察/结论/可复用知识（Agent 决策专用）。

    相当于:
        retrieve_context(query, section_filter=["洞察", "结论", "可复用知识"])
    """
    return search_section(
        query=topic,
        agent_name=agent_name,
        section_type="洞察|结论|可复用知识|Key Learnings|insight",
    )


def _build_summary(query: str, results: list[dict]) -> str:
    """构建给 Agent 的上下文摘要"""
    if not results:
        return "未找到相关历史记录。"

    lines = [f"## 历史参考（检索: {query}）\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"### {i}. {r['title']} ({r['agent']}, {r['date']})")

        # 优先使用 matched_sections 或 sections
        sections = r.get("matched_sections") or r.get("sections", [])
        for s in sections[:3]:  # 每篇最多3个区块
            heading = s.get("heading", "")
            content = s.get("content", "")[:300]
            lines.append(f"**{heading}**: {content.strip()[:100]}...")

        lines.append("")

    return "\n".join(lines)


def test():
    """简单自测"""
    print("=" * 50)
    print("Memory Retriever 自测")
    print("=" * 50)

    # 测试基本检索
    result = retrieve_context("财务", agent_name="finance", top_k=3)
    print(f"\n检索: {result['query']}")
    print(f"Agent: {result['agent']}")
    print(f"结果数: {result['total_found']}")
    if result['results']:
        print(f"第一条: {result['results'][0]['title']} (score={result['results'][0]['score']})")

    print(f"\n摘要预览:\n{result['summary'][:500]}")


if __name__ == "__main__":
    test()
