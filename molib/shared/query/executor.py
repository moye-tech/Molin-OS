"""
墨麟OS v2.0 — MQL 查询执行器

执行 AST 查询，对标 Dataview 的查询语义。

支持操作符:
  比较: =, !=, >, <, >=, <=
  包含: CONTAINS (字符串包含), IN (值在列表中)
  标签: HAS_TAG
  模式: MATCHES (正则), STARTS_WITH, ENDS_WITH
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional

from .parser import (
    MQLQuery, Condition, WhereClause, SortClause,
    GroupClause, FlattenClause, parse_query,
)
from .indexer import MQLIndexer, IndexEntry, get_indexer


@dataclass
class QueryStats:
    """查询统计"""
    sources_searched: list[str] = field(default_factory=list)
    entries_scanned: int = 0
    entries_matched: int = 0
    time_ms: float = 0.0


@dataclass
class QueryResult:
    """查询结果"""
    entries: list[IndexEntry]
    stats: QueryStats = field(default_factory=QueryStats)
    query_text: str = ""

    def __len__(self):
        return len(self.entries)

    def __iter__(self):
        return iter(self.entries)

    def __getitem__(self, index):
        return self.entries[index]

    def to_dicts(self) -> list[dict]:
        """转为字典列表"""
        return [
            {
                "source": e.source,
                "id": e.id,
                "name": e.name,
                "description": e.description,
                "tags": e.tags,
                "category": e.category,
                "version": e.version,
                "created_at": e.created_at,
                "modified_at": e.modified_at,
            }
            for e in self.entries
        ]

    def table_view(self) -> str:
        """生成表格视图字符串"""
        if not self.entries:
            return "(空结果)"

        # 检测可用列
        cols = ["source", "name"]
        sample = self.entries[0]
        if any(e.description for e in self.entries):
            cols.append("description")
        if any(e.tags for e in self.entries):
            cols.append("tags")

        lines = []
        # 表头
        header = " | ".join(c.upper() for c in cols)
        lines.append(header)
        lines.append("-" * len(header))

        for entry in self.entries:
            vals = []
            for c in cols:
                if c == "source":
                    vals.append(entry.source[:8])
                elif c == "name":
                    vals.append(entry.name[:30])
                elif c == "description":
                    vals.append((entry.description or "")[:50])
                elif c == "tags":
                    vals.append(", ".join(entry.tags[:3]))
            lines.append(" | ".join(vals))

        return "\n".join(lines)


# ── 条件评估 ────────────────────────────────

class ConditionEvaluator:
    """评估单个条件"""

    @staticmethod
    def evaluate(entry: IndexEntry, condition: Condition) -> bool:
        field = condition.field
        operator = condition.operator
        target_value = condition.value

        actual_value = entry.get(field)

        handlers = {
            "=": ConditionEvaluator._eval_equals,
            "!=": ConditionEvaluator._eval_not_equals,
            ">": ConditionEvaluator._eval_greater,
            "<": ConditionEvaluator._eval_less,
            ">=": ConditionEvaluator._eval_greater_equal,
            "<=": ConditionEvaluator._eval_less_equal,
            "CONTAINS": ConditionEvaluator._eval_contains,
            "IN": ConditionEvaluator._eval_in,
            "HAS_TAG": ConditionEvaluator._eval_has_tag,
            "MATCHES": ConditionEvaluator._eval_matches,
            "STARTS_WITH": ConditionEvaluator._eval_starts_with,
            "ENDS_WITH": ConditionEvaluator._eval_ends_with,
        }

        handler = handlers.get(operator)
        if handler is None:
            return False

        return handler(actual_value, target_value)

    @staticmethod
    def _eval_equals(actual: Any, target: Any) -> bool:
        if actual is None:
            return target is None
        if isinstance(target, (int, float)) and isinstance(actual, str):
            try:
                return float(actual) == float(target)
            except (ValueError, TypeError):
                pass
        return str(actual).lower() == str(target).lower()

    @staticmethod
    def _eval_not_equals(actual: Any, target: Any) -> bool:
        return not ConditionEvaluator._eval_equals(actual, target)

    @staticmethod
    def _eval_greater(actual: Any, target: Any) -> bool:
        try:
            return float(actual) > float(target)
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _eval_less(actual: Any, target: Any) -> bool:
        try:
            return float(actual) < float(target)
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _eval_greater_equal(actual: Any, target: Any) -> bool:
        try:
            return float(actual) >= float(target)
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _eval_less_equal(actual: Any, target: Any) -> bool:
        try:
            return float(actual) <= float(target)
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _eval_contains(actual: Any, target: Any) -> bool:
        if actual is None:
            return False
        if isinstance(actual, list):
            return any(str(target).lower() in str(item).lower() for item in actual)
        return str(target).lower() in str(actual).lower()

    @staticmethod
    def _eval_in(actual: Any, target: Any) -> bool:
        if target is None:
            return False
        if isinstance(target, list):
            return str(actual).lower() in [str(t).lower() for t in target]
        return str(actual).lower() == str(target).lower()

    @staticmethod
    def _eval_has_tag(actual: Any, target: Any) -> bool:
        if actual is None:
            return False
        if isinstance(actual, list):
            return str(target) in [str(t) for t in actual]
        return False

    @staticmethod
    def _eval_matches(actual: Any, target: Any) -> bool:
        if actual is None:
            return False
        try:
            return bool(re.search(str(target), str(actual), re.IGNORECASE))
        except re.error:
            return False

    @staticmethod
    def _eval_starts_with(actual: Any, target: Any) -> bool:
        if actual is None:
            return False
        return str(actual).lower().startswith(str(target).lower())

    @staticmethod
    def _eval_ends_with(actual: Any, target: Any) -> bool:
        if actual is None:
            return False
        return str(actual).lower().endswith(str(target).lower())


# ── 执行器 ──────────────────────────────────

class MQLExecutor:
    """MQL 查询执行器"""

    def __init__(self, indexer: Optional[MQLIndexer] = None):
        self.indexer = indexer or get_indexer()

    def execute(self, query: MQLQuery, query_text: str = "") -> QueryResult:
        """执行查询并返回结果"""
        import time
        start = time.time()

        stats = QueryStats(sources_searched=query.sources)

        # 1. 收集所有条目
        all_entries = []
        for source in query.sources:
            if source == "all":
                # 索引所有数据源
                for src in ["skills", "notes", "memory", "experiences", "hermes_sessions"]:
                    entries = self.indexer.get_entries(src)
                    all_entries.extend(entries)
                break
            else:
                entries = self.indexer.get_entries(source)
                all_entries.extend(entries)

        stats.entries_scanned = len(all_entries)

        # 2. 应用 WHERE 过滤
        if query.where:
            filtered = self._apply_where(all_entries, query.where)
        else:
            filtered = all_entries

        # 3. 应用 SORT
        if query.sort:
            filtered = self._apply_sort(filtered, query.sort)

        # 4. 应用 GROUP BY
        if query.group:
            filtered = self._apply_group(filtered, query.group)

        # 5. 应用 FLATTEN
        if query.flatten:
            filtered = self._apply_flatten(filtered, query.flatten)

        # 6. 应用 LIMIT
        if query.limit is not None and query.limit > 0:
            filtered = filtered[:query.limit]

        stats.entries_matched = len(filtered)
        stats.time_ms = (time.time() - start) * 1000

        return QueryResult(
            entries=filtered,
            stats=stats,
            query_text=query_text,
        )

    def execute_text(self, query_text: str) -> QueryResult:
        """解析并执行查询文本"""
        query = parse_query(query_text)
        return self.execute(query, query_text)

    # ── 内部方法 ──────────────────────────

    def _apply_where(self, entries: list[IndexEntry],
                     where: WhereClause) -> list[IndexEntry]:
        """应用 WHERE 子句过滤"""
        evaluator = ConditionEvaluator()
        results = []

        for entry in entries:
            matches = [evaluator.evaluate(entry, cond) for cond in where.conditions]

            # 应用 AND/OR 连接符
            if not matches:
                continue

            final = matches[0]
            for i, connector in enumerate(where.connectors):
                if connector == "AND":
                    final = final and matches[i + 1]
                else:  # OR
                    final = final or matches[i + 1]

            if final:
                results.append(entry)

        return results

    def _apply_sort(self, entries: list[IndexEntry],
                    sort: SortClause) -> list[IndexEntry]:
        """应用排序"""
        reverse = sort.direction == "DESC"

        def sort_key(entry: IndexEntry):
            val = entry.get(sort.field)
            if val is None:
                return ""
            if isinstance(val, str):
                return val.lower()
            return val

        try:
            return sorted(entries, key=sort_key, reverse=reverse)
        except TypeError:
            return entries

    def _apply_group(self, entries: list[IndexEntry],
                     group: GroupClause) -> list[IndexEntry]:
        """应用分组 — 返回各组第一条记录"""
        groups = defaultdict(list)
        for entry in entries:
            key = str(entry.get(group.field) or "(null)")
            groups[key].append(entry)

        # 返回每组的第一条作为代表
        result = []
        for key in sorted(groups.keys()):
            representative = groups[key][0]
            representative.metadata["_group_count"] = len(groups[key])
            representative.metadata["_group_key"] = key
            result.append(representative)

        return result

    def _apply_flatten(self, entries: list[IndexEntry],
                       flatten: FlattenClause) -> list[IndexEntry]:
        """展开数组字段"""
        result = []
        for entry in entries:
            val = entry.get(flatten.field)
            if isinstance(val, list):
                for item in val:
                    # 创建副本并设置展平后的值
                    import copy
                    flat_entry = copy.copy(entry)
                    flat_entry._raw = dict(flat_entry._raw)
                    flat_entry._raw[flatten.field] = item
                    result.append(flat_entry)
            else:
                result.append(entry)
        return result


# ── 便捷函数 ────────────────────────────────

def query(text: str) -> QueryResult:
    """快捷查询"""
    executor = MQLExecutor()
    return executor.execute_text(text)


def search(text: str, source: str = "all", limit: int = 20) -> QueryResult:
    """全文搜索快捷方式"""
    safe_text = text.replace("'", "\\'")
    mql = f"FROM {source} WHERE description CONTAINS '{safe_text}' LIMIT {limit}"
    return query(mql)


def lookup(field: str, value: str, source: str = "all") -> QueryResult:
    """精确查找"""
    safe_val = value.replace("'", "\\'")
    mql = f"FROM {source} WHERE {field} = '{safe_val}'"
    return query(mql)
