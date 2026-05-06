"""
墨麟AIOS — DataProcessor (数据处理引擎)
数据清洗、转换、聚合、导出管线。

参考 Crawlee 的数据处理流水线设计：
- clean()    — 去重 + 格式标准化（对应 Dataset 的自动去重）
- transform() — 根据 schema 映射转换（对应 Crawlee 的 dataset mapping）
- aggregate() — 分组聚合统计（对应 Crawlee 的 data stats）
- export()   — 多格式导出

核心能力:
1. clean      — 数据清洗（去重、空值处理、类型标准化）
2. transform  — 按 schema 映射转换字段
3. aggregate  — 按字段分组 + 多指标聚合
4. export     — 导出为 JSON / CSV / Markdown
"""

import csv
import io
import json
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class DataProcessor:
    """
    数据处理引擎 —— 完整的数据清洗→转换→聚合→导出管线。

    对应 Crawlee 的数据层设计：
    - 自动去重（内容指纹）
    - 字段映射（Schema 转换）
    - 聚合统计（分组 + 多指标）
    - 多格式导出（JSON / CSV / Markdown）
    """

    def __init__(self):
        self._clean_stats: dict[str, int] = {
            "total_input": 0,
            "total_output": 0,
            "dedup_removed": 0,
            "null_fields_fixed": 0,
            "format_errors_fixed": 0,
        }

    # ───────── 数据清洗 ─────────

    def clean(self, raw_data: list[dict]) -> list[dict]:
        """
        数据清洗 —— 去重、空值处理、类型标准化。

        对应 Crawlee Dataset 的自动去重和数据规范化:
        1. 基于内容指纹去重（sha256 全字段哈希）
        2. 缺失字段填充默认值
        3. 字段类型标准化（数值、字符串、布尔）
        4. 时间戳格式化
        5. 非法字符过滤

        Args:
            raw_data: 原始数据列表（如 DataCollector.get_data 的输出）

        Returns:
            list[dict]: 清洗后的数据列表
        """
        self._clean_stats["total_input"] = len(raw_data)

        if not raw_data:
            self._clean_stats["total_output"] = 0
            return []

        cleaned: list[dict] = []
        seen_hashes: set[str] = set()
        null_fields_fixed = 0
        format_errors_fixed = 0

        for item in raw_data:
            if not isinstance(item, dict):
                format_errors_fixed += 1
                continue

            # Step 1: 生成内容指纹用于去重
            # 排除元数据字段（_id, _collected_at 等）只对业务内容去重
            content_fields = {k: v for k, v in item.items() if not k.startswith("_")}
            content_str = json.dumps(content_fields, sort_keys=True, ensure_ascii=False)
            content_hash = hashlib.sha256(content_str.encode()).hexdigest()

            if content_hash in seen_hashes:
                self._clean_stats["dedup_removed"] += 1
                continue
            seen_hashes.add(content_hash)

            # Step 2: 字段类型标准化 + 空值填充
            normalized: dict[str, Any] = {}
            for key, value in item.items():
                # 保留元数据字段原样
                if key.startswith("_"):
                    normalized[key] = value
                    continue

                # 空值处理
                if value is None:
                    null_fields_fixed += 1
                    # 根据字段名推断默认值
                    if any(kw in key.lower() for kw in ["count", "num", "times", "index", "rank", "likes", "views"]):
                        normalized[key] = 0
                    elif any(kw in key.lower() for kw in ["rate", "pct", "ratio", "score"]):
                        normalized[key] = 0.0
                    elif any(kw in key.lower() for kw in ["title", "name", "desc", "author", "topic"]):
                        normalized[key] = ""
                    else:
                        normalized[key] = ""
                    continue

                # 类型修复: 数字字符串 → 数值
                if isinstance(value, str):
                    # 尝试转换为数值
                    if value.replace(".", "", 1).replace("-", "", 1).isdigit():
                        if "." in value:
                            try:
                                normalized[key] = float(value)
                                format_errors_fixed += 1
                                continue
                            except ValueError:
                                pass
                        else:
                            try:
                                normalized[key] = int(value)
                                format_errors_fixed += 1
                                continue
                            except ValueError:
                                pass
                    # 布尔字符串
                    if value.lower() in ("true", "yes", "1"):
                        normalized[key] = True
                        format_errors_fixed += 1
                        continue
                    elif value.lower() in ("false", "no", "0"):
                        normalized[key] = False
                        format_errors_fixed += 1
                        continue

                normalized[key] = value

            # Step 3: 添加清洗元数据
            normalized["_cleaned_at"] = datetime.now().isoformat()
            normalized["_content_hash"] = content_hash

            cleaned.append(normalized)

        self._clean_stats["total_output"] = len(cleaned)
        self._clean_stats["null_fields_fixed"] = null_fields_fixed
        self._clean_stats["format_errors_fixed"] = format_errors_fixed

        return cleaned

    # ───────── 数据转换 ─────────

    def transform(self, data: list[dict], schema: Optional[dict] = None) -> list[dict]:
        """
        数据转换 —— 按 Schema 映射规则变换数据。

        对应 Crawlee 的 Dataset.map() 模式:
        可以将采集到的平坦数据结构映射为所需的输出格式。

        Args:
            data:   待转换的数据列表
            schema: 转换 schema 字典，格式:
                    {
                        "output_field_name": {
                            "source": "input_field_name",   # 源字段
                            "default": default_value,        # 默认值
                            "transform": "upper|lower|capitalize|round|int|float|str|date",
                            "computed": "lambda expr"        # 计算表达式
                        }
                    }
                    如果 schema 为 None，则返回数据的深拷贝副本。

        Returns:
            list[dict]: 转换后的数据列表
        """
        if not data:
            return []

        if schema is None:
            # 无 schema 时，做深拷贝并添加转换元数据
            result = []
            for item in data:
                copy = dict(item)
                copy["_transformed_at"] = datetime.now().isoformat()
                result.append(copy)
            return result

        transformed: list[dict] = []
        for item in data:
            record: dict[str, Any] = {}
            for output_field, rules in schema.items():
                if not isinstance(rules, dict):
                    # 简单映射: {"new_field": "old_field"} 或 {"new_field": default_value}
                    if isinstance(rules, str):
                        # 字符串 = 源字段名
                        record[output_field] = item.get(rules, rules)
                    else:
                        # 其他 = 直接作为默认值
                        record[output_field] = rules
                    continue

                source_field = rules.get("source", output_field)
                default_value = rules.get("default")
                transform_type = rules.get("transform")
                computed = rules.get("computed")

                # 获取源值
                raw_value = item.get(source_field, default_value)

                # 计算表达式优先
                if computed:
                    try:
                        # 安全计算环境
                        safe_globals = {"__builtins__": {}}
                        safe_locals = {"item": item, "raw_value": raw_value}
                        computed_result = eval(computed, safe_globals, safe_locals)
                        record[output_field] = computed_result
                        continue
                    except Exception:
                        record[output_field] = raw_value
                        continue

                # 应用转换
                if transform_type and raw_value is not None:
                    try:
                        if transform_type == "upper":
                            record[output_field] = str(raw_value).upper()
                        elif transform_type == "lower":
                            record[output_field] = str(raw_value).lower()
                        elif transform_type == "capitalize":
                            record[output_field] = str(raw_value).capitalize()
                        elif transform_type == "round":
                            record[output_field] = round(float(raw_value), 2)
                        elif transform_type == "int":
                            record[output_field] = int(float(raw_value))
                        elif transform_type == "float":
                            record[output_field] = float(raw_value)
                        elif transform_type == "str":
                            record[output_field] = str(raw_value)
                        elif transform_type == "date":
                            # 尝试多种日期格式
                            if isinstance(raw_value, str):
                                for fmt in [
                                    "%Y-%m-%dT%H:%M:%S",
                                    "%Y-%m-%d %H:%M:%S",
                                    "%Y-%m-%d",
                                    "%Y/%m/%d",
                                ]:
                                    try:
                                        dt = datetime.strptime(raw_value, fmt)
                                        record[output_field] = dt.isoformat()
                                        break
                                    except ValueError:
                                        continue
                                else:
                                    record[output_field] = raw_value
                            else:
                                record[output_field] = str(raw_value)
                        else:
                            record[output_field] = raw_value
                    except (ValueError, TypeError, AttributeError):
                        record[output_field] = raw_value
                else:
                    record[output_field] = raw_value

            record["_transformed_at"] = datetime.now().isoformat()
            transformed.append(record)

        return transformed

    # ───────── 数据聚合 ─────────

    def aggregate(
        self,
        data: list[dict],
        group_by: str | list[str],
        metrics: Optional[dict[str, str]] = None,
    ) -> dict:
        """
        数据聚合 —— 按字段分组 + 多指标统计。

        对应 Crawlee 的数据统计功能:
        支持按一个或多个字段分组，计算 sum / avg / count / min / max / median。

        Args:
            data:     待聚合的数据列表
            group_by: 分组字段名（字符串）或字段名列表
            metrics:  指标定义，格式:
                     {
                         "output_name": {
                             "field": "source_field",
                             "op": "sum|avg|count|min|max|median",
                         }
                     }
                     如果为 None，默认对所有数值字段计算 {sum, avg, count}。

        Returns:
            dict: {
                groups: [
                    {
                        key: 分组键值,
                        count: 组内记录数,
                        metrics: {指标名: 值, ...},
                        records: [第一条记录...] (可选)
                    }
                ],
                totals: 全局汇总 meta
            }
        """
        if not data:
            return {"groups": [], "totals": {"total_records": 0, "group_count": 0}}

        # 标准化 group_by 为列表
        group_fields = [group_by] if isinstance(group_by, str) else list(group_by)

        # 自动检测数值字段
        numeric_fields = set()
        for item in data:
            for key, value in item.items():
                if key.startswith("_"):
                    continue
                if isinstance(value, (int, float)):
                    numeric_fields.add(key)

        # 构建默认 metrics（如果未提供）
        if metrics is None:
            metrics = {}
            for field in sorted(numeric_fields)[:10]:  # 最多处理10个字段
                metrics[field] = {
                    "field": field,
                    "op": "sum",
                }
                metrics[f"{field}_avg"] = {
                    "field": field,
                    "op": "avg",
                }

        # 分组聚合
        groups_dict: dict[str, dict[str, Any]] = {}

        for item in data:
            # 构建分组键
            group_key_parts = []
            for gf in group_fields:
                val = item.get(gf, "__null__")
                group_key_parts.append(str(val))
            group_key = "|".join(group_key_parts)

            if group_key not in groups_dict:
                groups_dict[group_key] = {
                    "_key_parts": group_key_parts,
                    "_records": [],
                    "_first_record": item,
                }
                for metric_name, metric_def in metrics.items():
                    groups_dict[group_key][metric_name] = []

            groups_dict[group_key]["_records"].append(item)

            for metric_name, metric_def in metrics.items():
                field = metric_def.get("field")
                op = metric_def.get("op", "sum")
                value = item.get(field)

                if isinstance(value, (int, float)):
                    groups_dict[group_key][metric_name].append(value)

        # 计算结果
        groups_result = []
        for group_key, gdata in groups_dict.items():
            result_item: dict[str, Any] = {}

            # 分组键
            if len(group_fields) == 1:
                result_item["key"] = gdata["_key_parts"][0]
            else:
                result_item["key"] = dict(zip(group_fields, gdata["_key_parts"]))

            result_item["count"] = len(gdata["_records"])
            result_item["metrics"] = {}

            for metric_name, metric_def in metrics.items():
                values = gdata.get(metric_name, [])
                op = metric_def.get("op", "sum")

                if not values:
                    result_item["metrics"][metric_name] = 0
                    continue

                if op == "sum":
                    result_item["metrics"][metric_name] = round(sum(values), 2)
                elif op == "avg":
                    result_item["metrics"][metric_name] = round(
                        sum(values) / len(values), 2
                    )
                elif op == "count":
                    result_item["metrics"][metric_name] = len(values)
                elif op == "min":
                    result_item["metrics"][metric_name] = min(values)
                elif op == "max":
                    result_item["metrics"][metric_name] = max(values)
                elif op == "median":
                    sorted_vals = sorted(values)
                    n = len(sorted_vals)
                    if n % 2 == 1:
                        result_item["metrics"][metric_name] = sorted_vals[n // 2]
                    else:
                        result_item["metrics"][metric_name] = round(
                            (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2, 2
                        )
                else:
                    result_item["metrics"][metric_name] = sum(values)

            groups_result.append(result_item)

        # 按 count 降序排列
        groups_result.sort(key=lambda x: x["count"], reverse=True)

        # 计算全局汇总
        total_records = len(data)
        total_groups = len(groups_result)

        return {
            "groups": groups_result,
            "totals": {
                "total_records": total_records,
                "group_count": total_groups,
                "group_fields": group_fields,
                "metrics_defined": list(metrics.keys()),
                "aggregated_at": datetime.now().isoformat(),
            },
        }

    # ───────── 数据导出 ─────────

    def export(self, data: list[dict], format: str = "json") -> str:
        """
        数据导出 —— 将处理后的数据导出为指定格式。

        支持格式:
        - "json": 标准 JSON 格式（默认，缩进美化）
        - "jsonl": JSON Lines 格式（每行一个 JSON）
        - "csv": 逗号分隔值
        - "markdown": Markdown 表格

        Args:
            data:   待导出的数据列表
            format: 导出格式 ("json" | "jsonl" | "csv" | "markdown")

        Returns:
            str: 格式化后的数据字符串
        """
        if not data:
            if format == "json":
                return "[]"
            elif format == "jsonl":
                return ""
            elif format == "csv":
                return ""
            elif format == "markdown":
                return "*(无数据)*"
            return ""

        fmt = format.lower()

        if fmt == "json":
            return json.dumps(data, ensure_ascii=False, indent=2, default=str)

        elif fmt == "jsonl":
            lines = []
            for item in data:
                lines.append(json.dumps(item, ensure_ascii=False, default=str))
            return "\n".join(lines)

        elif fmt == "csv":
            # 提取所有字段（保留元数据字段的顺序优先）
            all_fields: list[str] = []
            seen_fields: set[str] = set()
            for item in data:
                for key in item:
                    if key not in seen_fields:
                        all_fields.append(key)
                        seen_fields.add(key)

            output = io.StringIO()
            writer = csv.writer(output)

            # 写入表头
            writer.writerow(all_fields)

            # 写入数据行
            for item in data:
                row = []
                for field in all_fields:
                    value = item.get(field, "")
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value, ensure_ascii=False)
                    elif isinstance(value, bool):
                        value = "true" if value else "false"
                    elif value is None:
                        value = ""
                    row.append(str(value))
                writer.writerow(row)

            return output.getvalue()

        elif fmt == "markdown":
            if not data:
                return "*(无数据)*"

            # 提取字段
            all_fields: list[str] = []
            seen_fields: set[str] = set()
            for item in data:
                for key in item:
                    if key not in seen_fields:
                        all_fields.append(key)
                        seen_fields.add(key)

            lines: list[str] = []

            # 表头
            header = "| " + " | ".join(all_fields) + " |"
            separator = "| " + " | ".join("---" for _ in all_fields) + " |"
            lines.append(header)
            lines.append(separator)

            # 数据行（最多100行，避免过长的表格）
            max_rows = min(len(data), 100)
            for i in range(max_rows):
                item = data[i]
                row = []
                for field in all_fields:
                    value = item.get(field, "")
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value, ensure_ascii=False)
                    elif value is None:
                        value = ""
                    row.append(str(value).replace("|", "\\|"))
                lines.append("| " + " | ".join(row) + " |")

            if len(data) > 100:
                lines.append(f"*(共 {len(data)} 行，仅展示前 100 行)*")

            return "\n".join(lines)

        else:
            raise ValueError(f"不支持的导出格式: {format}，支持: json, jsonl, csv, markdown")

    # ───────── 工具方法 ─────────

    def clean_stats(self) -> dict:
        """获取清洗统计信息。"""
        return dict(self._clean_stats)
