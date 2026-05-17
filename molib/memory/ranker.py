#!/usr/bin/env python3
"""
Molin-OS Ranker — 记忆检索结果排序

支持关键词评分 + 可升级的 embedding 排序。
"""

import re
from typing import Any


def rank_results(query: str, results: list[dict]) -> list[dict]:
    """
    对检索结果进行排序。

    当前: 关键词 + 区块类型加权评分
    可升级: 接入 embedding 相似度（预留接口）
    """
    query_lower = query.lower()
    query_terms = set(query_lower.split())

    for r in results:
        score = r.get("score", 0)

        # Section type bonus
        sections = r.get("sections", [])
        for s in sections:
            heading = s.get("heading", "").lower()
            content = s.get("content", "").lower()

            # 核心区块加权
            if any(kw in heading for kw in ["洞察", "结论", "可复用知识", "key learnings"]):
                if query_terms & set(content.split()):
                    score += 3

            # 行动区块
            if any(kw in heading for kw in ["执行动作", "actions", "风险"]):
                if query_terms & set(content.split()):
                    score += 2

        # Recency bonus
        date_str = r.get("date", "")
        if date_str and date_str != "unknown":
            year, month, day = date_str.split("-")
            # 较新的结果加分
            score += 1

        r["score"] = score

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def deduplicate(results: list[dict]) -> list[dict]:
    """去重（同一 Agent + 同一日期 + 相似内容）"""
    seen = set()
    deduped = []
    for r in results:
        key = (r.get("agent", ""), r.get("date", ""), r.get("title", "")[:30])
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    return deduped


def filter_by_type(results: list[dict],
                   include_types: list[str] = None) -> list[dict]:
    """按区块类型过滤"""
    if not include_types:
        return results

    filtered = []
    for r in results:
        matched = []
        for s in r.get("sections", []):
            h = s.get("heading", "")
            for t in include_types:
                if t.lower() in h.lower():
                    matched.append(s)
        if matched:
            r["matched_sections"] = matched
            filtered.append(r)

    return filtered
