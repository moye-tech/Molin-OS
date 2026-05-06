"""
墨麟AIOS — FileStore (文件即数据库)
参考 nanobot (41K⭐) "文件即数据库" 哲学。
每个collection对应一个目录，每个doc_id对应一个JSON文件。
支持增删查改、过滤查询、集合管理。
"""

import os
import json
import time
import glob
import re
import uuid
import fnmatch
from pathlib import Path
from typing import Any, Optional


class FileStore:
    """
    文件即数据库 — 每个collection一个目录，每个doc_id一个JSON文件。

    参考 nanobot (41K⭐) "文件即数据库" 核心理念：
    - save(collection, doc_id, data) → dict
    - get(collection, doc_id) → dict
    - query(collection, filters) → list[dict]
    - delete(collection, doc_id) → bool
    - list_collections() → list[str]

    数据以JSON文件存储在磁盘上，零依赖、易备份、可直接查看。
    """

    def __init__(self, storage_path: str = "~/.hermes/filestore/"):
        """
        Args:
            storage_path: 文件存储根路径
        """
        self.storage_path = Path(storage_path).expanduser()
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # 统计
        self._stats = {
            "total_saves": 0,
            "total_gets": 0,
            "total_queries": 0,
            "total_deletes": 0,
            "started_at": time.time(),
        }

    # ───────── 路径工具 ─────────

    def _collection_path(self, collection: str) -> Path:
        """获取collection目录路径。"""
        # 安全化collection名称
        safe_name = self._sanitize_name(collection)
        return self.storage_path / safe_name

    def _doc_path(self, collection: str, doc_id: str) -> Path:
        """获取文档文件路径。"""
        col_path = self._collection_path(collection)
        safe_doc_id = self._sanitize_name(doc_id)
        return col_path / f"{safe_doc_id}.json"

    def _sanitize_name(self, name: str) -> str:
        """
        清理名称，移除不安全的文件系统字符。
        保留字母、数字、连字符、下划线、点。
        """
        # 替换路径分隔符等危险字符
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
        # 限制长度
        if len(sanitized) > 200:
            sanitized = sanitized[:200]
        # 不能为空
        if not sanitized:
            sanitized = f"unnamed_{uuid.uuid4().hex[:8]}"
        return sanitized

    # ───────── 核心CRUD ─────────

    def save(self, collection: str, doc_id: str, data: dict) -> dict:
        """
        保存文档到collection。

        Args:
            collection: 集合名称
            doc_id: 文档ID（唯一标识）
            data: 文档数据字典（必须是JSON可序列化的）

        Returns:
            dict: 保存后的文档完整信息（含自动添加的元数据字段）
        """
        if not collection:
            raise ValueError("collection不能为空")
        if not doc_id:
            raise ValueError("doc_id不能为空")
        if not isinstance(data, dict):
            raise ValueError("data必须是字典类型")

        # 构建存储文档（自动添加元数据）
        now = time.time()
        document = {
            "_id": doc_id,
            "_collection": collection,
            "_updated_at": now,
            **data,
        }

        # 检查是否存在（首次保存时添加_created_at）
        doc_path = self._doc_path(collection, doc_id)
        if doc_path.exists():
            try:
                existing = self.get(collection, doc_id)
                if existing:
                    document["_created_at"] = existing.get("_created_at", now)
            except (json.JSONDecodeError, OSError):
                document["_created_at"] = now
        else:
            document["_created_at"] = now

        # 确保collection目录存在
        col_path = self._collection_path(collection)
        col_path.mkdir(parents=True, exist_ok=True)

        # 原子写入
        tmp_path = doc_path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(document, f, ensure_ascii=False, indent=2)
        tmp_path.replace(doc_path)

        self._stats["total_saves"] += 1

        return document

    def get(self, collection: str, doc_id: str) -> Optional[dict]:
        """
        获取文档。

        Args:
            collection: 集合名称
            doc_id: 文档ID

        Returns:
            dict or None: 文档数据，不存在返回None
        """
        doc_path = self._doc_path(collection, doc_id)

        if not doc_path.exists():
            self._stats["total_gets"] += 1
            return None

        try:
            with open(doc_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._stats["total_gets"] += 1
            return data
        except (json.JSONDecodeError, OSError):
            self._stats["total_gets"] += 1
            return None

    def query(
        self,
        collection: str,
        filters: Optional[dict] = None,
    ) -> list[dict]:
        """
        查询collection中的文档，支持字段级过滤。

        Args:
            collection: 集合名称
            filters: 过滤条件字典。
                     - 精确匹配: {"field": value}
                     - 嵌套字段: {"field.subfield": value}
                     - 支持 $gt, $gte, $lt, $lte, $ne, $in, $nin, $exists, $regex
                       示例: {"age": {"$gt": 18}}
                             {"tags": {"$in": ["ai", "ml"]}}
                             {"name": {"$regex": ".*test.*"}}

        Returns:
            list[dict]: 匹配的文档列表，每个文档包含 _id, _collection, _created_at, _updated_at
        """
        self._stats["total_queries"] += 1
        filters = filters or {}

        col_path = self._collection_path(collection)
        if not col_path.exists() or not col_path.is_dir():
            return []

        # 读取所有文档
        results = []
        for json_file in sorted(col_path.glob("*.json")):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    doc = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            # 应用过滤
            if self._matches_filters(doc, filters):
                results.append(doc)

        return results

    def _matches_filters(self, doc: dict, filters: dict) -> bool:
        """
        检查文档是否匹配所有过滤条件。

        支持的运算符:
        - $gt: 大于
        - $gte: 大于等于
        - $lt: 小于
        - $lte: 小于等于
        - $ne: 不等于
        - $in: 在列表中
        - $nin: 不在列表中
        - $exists: 字段存在
        - $regex: 正则匹配
        """
        for field, condition in filters.items():
            # 支持点号分隔的嵌套字段
            value = self._get_nested_value(doc, field)

            # 精确匹配（非运算符）
            if not isinstance(condition, dict):
                if value != condition:
                    return False
                continue

            # 运算符匹配
            for op, expected in condition.items():
                if op == "$gt":
                    if not (isinstance(value, (int, float)) and value > expected):
                        return False
                elif op == "$gte":
                    if not (isinstance(value, (int, float)) and value >= expected):
                        return False
                elif op == "$lt":
                    if not (isinstance(value, (int, float)) and value < expected):
                        return False
                elif op == "$lte":
                    if not (isinstance(value, (int, float)) and value <= expected):
                        return False
                elif op == "$ne":
                    if value == expected:
                        return False
                elif op == "$in":
                    if not (isinstance(expected, list) and value in expected):
                        return False
                elif op == "$nin":
                    if isinstance(expected, list) and value in expected:
                        return False
                elif op == "$exists":
                    if expected:
                        if value is None:
                            return False
                    else:
                        if value is not None:
                            return False
                elif op == "$regex":
                    if not isinstance(value, str):
                        return False
                    try:
                        if not re.search(expected, value):
                            return False
                    except re.error:
                        return False
                else:
                    # 未知运算符，当作精确匹配
                    if value != expected:
                        return False

        return True

    def _get_nested_value(self, doc: dict, field: str) -> Any:
        """
        从嵌套字典中获取字段值（支持点号分隔）。
        例如 "user.profile.name" → doc["user"]["profile"]["name"]
        """
        parts = field.split(".")
        current = doc
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    def delete(self, collection: str, doc_id: str) -> bool:
        """
        删除文档。

        Args:
            collection: 集合名称
            doc_id: 文档ID

        Returns:
            bool: 是否成功删除
        """
        doc_path = self._doc_path(collection, doc_id)

        if not doc_path.exists():
            return False

        try:
            doc_path.unlink()  # 删除文件
            self._stats["total_deletes"] += 1

            # 如果collection目录为空，删除目录
            col_path = self._collection_path(collection)
            if col_path.exists() and not list(col_path.iterdir()):
                col_path.rmdir()

            return True
        except OSError:
            return False

    def list_collections(self) -> list[str]:
        """
        列出所有collection。

        Returns:
            list[str]: collection名称列表
        """
        collections = []
        for item in sorted(self.storage_path.iterdir()):
            if item.is_dir() and not item.name.startswith("."):
                # 检查目录内是否有.json文件
                has_json = any(item.glob("*.json"))
                if has_json:
                    collections.append(item.name)
        return collections

    # ───────── 扩展功能 ─────────

    def count(self, collection: str) -> int:
        """
        统计collection中文档数量。

        Args:
            collection: 集合名称

        Returns:
            int: 文档数量
        """
        col_path = self._collection_path(collection)
        if not col_path.exists() or not col_path.is_dir():
            return 0
        return len(list(col_path.glob("*.json")))

    def list_docs(self, collection: str) -> list[str]:
        """
        列出collection中所有doc_id。

        Args:
            collection: 集合名称

        Returns:
            list[str]: doc_id列表
        """
        col_path = self._collection_path(collection)
        if not col_path.exists() or not col_path.is_dir():
            return []

        doc_ids = []
        for json_file in sorted(col_path.glob("*.json")):
            doc_id = json_file.stem  # 去掉.json后缀
            doc_ids.append(doc_id)
        return doc_ids

    def update(
        self,
        collection: str,
        doc_id: str,
        data: dict,
        upsert: bool = False,
    ) -> Optional[dict]:
        """
        部分更新文档字段（合并而非替换）。

        Args:
            collection: 集合名称
            doc_id: 文档ID
            data: 要更新的字段字典
            upsert: 如果文档不存在是否创建

        Returns:
            dict or None: 更新后的文档，失败返回None
        """
        existing = self.get(collection, doc_id)

        if existing is None:
            if upsert:
                return self.save(collection, doc_id, data)
            return None

        # 合并数据（不覆盖自动元数据字段）
        for key, value in data.items():
            if not key.startswith("_"):  # 保护自动字段
                existing[key] = value

        # 更新_updated_at
        existing["_updated_at"] = time.time()

        # 写回
        doc_path = self._doc_path(collection, doc_id)
        tmp_path = doc_path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        tmp_path.replace(doc_path)

        self._stats["total_saves"] += 1
        return existing

    def stats(self) -> dict:
        """
        获取文件存储统计信息。

        Returns:
            dict: 统计信息包含:
                - total_collections: 集合数量
                - total_documents: 文档总数
                - storage_size_bytes: 存储总大小
                - collections: 每个集合的文档数和大小
                - total_saves: 保存总次数
                - total_gets: 读取总次数
                - total_queries: 查询总次数
                - total_deletes: 删除总次数
                - uptime_seconds: 运行时长
                - storage_path: 存储路径
        """
        collections = self.list_collections()
        total_docs = 0
        total_size = 0
        collection_details = []

        for col in collections:
            col_path = self._collection_path(col)
            doc_count = self.count(col)
            col_size = sum(
                f.stat().st_size for f in col_path.glob("*.json")
            )
            total_docs += doc_count
            total_size += col_size
            collection_details.append({
                "name": col,
                "doc_count": doc_count,
                "size_bytes": col_size,
            })

        return {
            "total_collections": len(collections),
            "total_documents": total_docs,
            "storage_size_bytes": total_size,
            "collections": collection_details,
            "total_saves": self._stats["total_saves"],
            "total_gets": self._stats["total_gets"],
            "total_queries": self._stats["total_queries"],
            "total_deletes": self._stats["total_deletes"],
            "uptime_seconds": round(time.time() - self._stats["started_at"], 2),
            "storage_path": str(self.storage_path),
        }

    def drop_collection(self, collection: str) -> bool:
        """
        删除整个collection（目录及其所有文件）。

        Args:
            collection: 集合名称

        Returns:
            bool: 是否成功删除
        """
        import shutil
        col_path = self._collection_path(collection)
        if not col_path.exists() or not col_path.is_dir():
            return False

        try:
            shutil.rmtree(str(col_path))
            self._stats["total_deletes"] += self.count(collection)
            return True
        except OSError:
            return False
