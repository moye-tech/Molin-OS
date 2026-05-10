"""
墨麟OS v2.0 — MQL 查询引擎

对标 Obsidian Dataview，为墨麟OS提供结构化知识查询语言。

用法:
  from molib.shared.query import query, search, lookup

  # 查询所有 AI 相关技能
  result = search("AI", source="skills")

  # 结构化查询
  result = query("FROM notes WHERE tags HAS_TAG 'project' SORT BY modified_at DESC LIMIT 10")

  # 精确查找
  result = lookup("name", "obsidian", source="skills")
"""

from .parser import parse_query, parse_query_safe, MQLQuery
from .indexer import MQLIndexer, IndexEntry, get_indexer, reset_indexer
from .executor import MQLExecutor, QueryResult, query, search, lookup

__all__ = [
    "parse_query",
    "parse_query_safe",
    "MQLQuery",
    "MQLIndexer",
    "IndexEntry",
    "get_indexer",
    "reset_indexer",
    "MQLExecutor",
    "QueryResult",
    "query",
    "search",
    "lookup",
]
