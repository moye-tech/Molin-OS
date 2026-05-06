"""
墨麟AIOS — VectorStore (向量存储)
参考 supermemory (22K⭐) 向量数据库持久化方案。
基于JSON文件持久化模拟向量存储，支持余弦相似度搜索。
"""

import os
import json
import math
import time
import uuid
import hashlib
from pathlib import Path
from typing import Optional


class VectorStore:
    """
    向量存储 — 使用JSON文件持久化模拟向量存储与搜索。

    参考 supermemory 的持久化向量存储架构：
    - index(embeddings, metadata) → doc_id
    - search(query_vector, top_k) → list[dict] 余弦相似度搜索
    - delete(doc_id) → bool
    - stats() → dict 索引统计
    """

    def __init__(self, storage_path: str = "~/.hermes/vectors/", backend: str = "json"):
        """
        Args:
            storage_path: 向量存储路径
            backend: 后端类型（当前仅支持"json"）
        """
        self.storage_path = Path(storage_path).expanduser()
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.backend = backend
        self._index_file = self.storage_path / "index.json"
        self._meta_file = self.storage_path / "metadata.json"

        # 内存索引缓存
        self._vectors: dict[str, list[float]] = {}
        self._metadata: dict[str, dict] = {}

        # 统计信息
        self._stats = {
            "total_vectors": 0,
            "total_searches": 0,
            "last_index_time": None,
            "dimension": 0,
        }

        self._load()

    # ───────── 持久化 ─────────

    def _load(self):
        """从JSON文件加载索引和元数据。"""
        if self._index_file.exists():
            try:
                with open(self._index_file, "r", encoding="utf-8") as f:
                    self._vectors = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._vectors = {}
        if self._meta_file.exists():
            try:
                with open(self._meta_file, "r", encoding="utf-8") as f:
                    self._metadata = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._metadata = {}

        self._stats["total_vectors"] = len(self._vectors)

        # 推断维度
        if self._vectors:
            sample = next(iter(self._vectors.values()))
            self._stats["dimension"] = len(sample)

    def _save(self):
        """持久化索引和元数据到JSON文件。"""
        # 原子写入：先写临时文件再重命名，避免写入中断损坏
        index_tmp = self._index_file.with_suffix(".tmp")
        meta_tmp = self._meta_file.with_suffix(".tmp")

        with open(index_tmp, "w", encoding="utf-8") as f:
            json.dump(self._vectors, f, ensure_ascii=False, indent=2)
        index_tmp.replace(self._index_file)

        with open(meta_tmp, "w", encoding="utf-8") as f:
            json.dump(self._metadata, f, ensure_ascii=False, indent=2)
        meta_tmp.replace(self._meta_file)

    # ───────── 向量操作 ─────────

    def _cosine_similarity(self, vec_a: list[float], vec_b: list[float]) -> float:
        """计算两个向量的余弦相似度。"""
        if not vec_a or not vec_b:
            return 0.0
        if len(vec_a) != len(vec_b):
            # 维度不匹配时尝试截断或补零
            min_len = min(len(vec_a), len(vec_b))
            vec_a = vec_a[:min_len]
            vec_b = vec_b[:min_len]

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def _validate_embedding(self, embeddings: list[float]) -> list[float]:
        """验证并规范化嵌入向量。"""
        if not embeddings:
            raise ValueError("嵌入向量不能为空")

        # 确保是float列表
        validated = [float(v) for v in embeddings]

        # 检查是否有NaN或Inf
        for v in validated:
            if math.isnan(v) or math.isinf(v):
                raise ValueError(f"嵌入向量包含无效值: {v}")

        # 检查维度一致性
        if self._stats["dimension"] == 0:
            self._stats["dimension"] = len(validated)
        elif len(validated) != self._stats["dimension"]:
            raise ValueError(
                f"嵌入向量维度不一致: 期望 {self._stats['dimension']}, 实际 {len(validated)}"
            )

        return validated

    def index(
        self,
        embeddings: list[float],
        metadata: Optional[dict] = None,
    ) -> str:
        """
        索引一个嵌入向量到存储中。

        Args:
            embeddings: 嵌入向量 (float列表)
            metadata: 关联的元数据 (如 {text, source, timestamp, tags})

        Returns:
            str: 文档ID (doc_id)
        """
        embeddings = self._validate_embedding(embeddings)
        metadata = metadata or {}

        # 生成唯一doc_id
        raw_key = f"{json.dumps(embeddings, ensure_ascii=False)}:{time.time()}:{uuid.uuid4().hex}"
        doc_id = hashlib.sha256(raw_key.encode()).hexdigest()[:24]

        # 存入索引
        self._vectors[doc_id] = embeddings

        # 存入元数据（附加时间戳）
        metadata_entry = {
            **metadata,
            "_indexed_at": time.time(),
            "_vector_dim": len(embeddings),
        }
        self._metadata[doc_id] = metadata_entry

        # 持久化
        self._save()

        # 更新统计
        self._stats["total_vectors"] = len(self._vectors)
        self._stats["last_index_time"] = time.time()

        return doc_id

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
    ) -> list[dict]:
        """
        余弦相似度搜索。

        Args:
            query_vector: 查询向量
            top_k: 返回前K个结果

        Returns:
            list[dict]: 搜索结果，每个包含:
                - doc_id: 文档ID
                - similarity: 余弦相似度 (0-1)
                - metadata: 元数据
                - rank: 排名
        """
        if not self._vectors:
            return []

        self._stats["total_searches"] += 1

        query_vector = self._validate_embedding(query_vector)

        # 计算所有向量的余弦相似度
        scored_results = []
        for doc_id, vec in self._vectors.items():
            similarity = self._cosine_similarity(query_vector, vec)
            scored_results.append({
                "doc_id": doc_id,
                "similarity": round(similarity, 6),
                "metadata": self._metadata.get(doc_id, {}),
            })

        # 按相似度降序排序
        scored_results.sort(key=lambda x: x["similarity"], reverse=True)

        # 取top_k并添加排名
        results = scored_results[:top_k]
        for i, r in enumerate(results):
            r["rank"] = i + 1

        return results

    def delete(self, doc_id: str) -> bool:
        """
        删除一个向量索引。

        Args:
            doc_id: 文档ID

        Returns:
            bool: 是否成功删除
        """
        if doc_id not in self._vectors:
            return False

        # 删除向量和元数据
        del self._vectors[doc_id]
        self._metadata.pop(doc_id, None)

        # 持久化
        self._save()

        # 更新统计
        self._stats["total_vectors"] = len(self._vectors)

        return True

    def stats(self) -> dict:
        """
        获取索引统计信息。

        Returns:
            dict: 统计信息包含:
                - total_vectors: 向量总数
                - dimension: 向量维度
                - total_searches: 搜索总次数
                - last_index_time: 最后索引时间
                - storage_size_bytes: 存储文件大小
                - backend: 后端类型
                - storage_path: 存储路径
        """
        # 计算存储文件大小
        index_size = self._index_file.stat().st_size if self._index_file.exists() else 0
        meta_size = self._meta_file.stat().st_size if self._meta_file.exists() else 0

        # 更新实时统计
        self._stats["total_vectors"] = len(self._vectors)

        return {
            "total_vectors": self._stats["total_vectors"],
            "dimension": self._stats["dimension"],
            "total_searches": self._stats["total_searches"],
            "last_index_time": self._stats["last_index_time"],
            "storage_size_bytes": index_size + meta_size,
            "index_file_size": index_size,
            "metadata_file_size": meta_size,
            "backend": self.backend,
            "storage_path": str(self.storage_path),
        }

    def get(self, doc_id: str) -> Optional[dict]:
        """
        根据doc_id获取向量和元数据。

        Args:
            doc_id: 文档ID

        Returns:
            dict or None: 包含 vector 和 metadata 的字典
        """
        if doc_id not in self._vectors:
            return None

        return {
            "doc_id": doc_id,
            "vector": self._vectors[doc_id],
            "metadata": self._metadata.get(doc_id, {}),
        }

    def list_ids(self) -> list[str]:
        """列出所有doc_id。"""
        return list(self._vectors.keys())

    def clear(self) -> int:
        """
        清空所有向量索引。

        Returns:
            int: 被清空的向量数量
        """
        count = len(self._vectors)
        self._vectors.clear()
        self._metadata.clear()
        self._save()
        self._stats["total_vectors"] = 0
        return count
