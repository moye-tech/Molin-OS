"""
墨麟AIOS — RAGEngine (检索增强生成引擎)
参考 supermemory (22K⭐) RAG检索架构 + cocoindex (7.8K⭐) 增量计算思路。
支持文本索引、语义搜索、文档管理、统计。
"""

import os
import json
import re
import math
import hashlib
import sqlite3
import pickle
import time
from typing import Optional
from pathlib import Path
from collections import defaultdict, Counter

# ───────── 向量模拟器 ─────────
# 使用TF-IDF+关键词匹配模拟嵌入向量（免去真实嵌入模型依赖）
# 实际部署可替换为 sentence-transformers / text-embedding-3


class _VectorSimulator:
    """基于词频的语义相似度模拟器。"""

    def __init__(self):
        self._cache: dict[str, Counter] = {}

    def _tokenize(self, text: str) -> Counter:
        """分词并返回词频统计。"""
        text_lower = text.lower()
        # 中文按字/词混合
        tokens = []
        # 提取英文单词
        tokens.extend(re.findall(r'[a-zA-Z]+', text_lower))
        # 提取中文词（2-gram）
        chinese_chars = re.findall(r'[\u4e00-\u9fff]+', text_lower)
        for chunk in chinese_chars:
            # 单字词
            for c in chunk:
                tokens.append(c)
            # 2-gram
            for i in range(len(chunk) - 1):
                tokens.append(chunk[i:i+2])
        return Counter(tokens)

    def embed(self, text: str) -> Counter:
        """生成稀疏向量表示。"""
        if text in self._cache:
            return self._cache[text]
        vec = self._tokenize(text)
        self._cache[text] = vec
        return vec

    def cosine_similarity(self, vec1: Counter, vec2: Counter) -> float:
        """计算余弦相似度。"""
        if not vec1 or not vec2:
            return 0.0
        intersection = set(vec1.keys()) & set(vec2.keys())
        dot_product = sum(vec1[k] * vec2[k] for k in intersection)
        norm1 = math.sqrt(sum(v * v for v in vec1.values()))
        norm2 = math.sqrt(sum(v * v for v in vec2.values()))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def keyword_overlap(self, text1: str, text2: str) -> float:
        """关键词重叠率。"""
        tokens1 = set(self._tokenize(text1).keys())
        tokens2 = set(self._tokenize(text2).keys())
        if not tokens1 or not tokens2:
            return 0.0
        overlap = len(tokens1 & tokens2)
        return overlap / max(len(tokens1), len(tokens2))


class RAGEngine:
    """
    检索增强生成引擎 — 知识库索引与语义搜索。

    参考 supermemory RAG检索架构，支持：
    - 文本索引 (index_text) → 分块→向量化→存储
    - 语义搜索 (search) → 向量相似度→重排序
    - 文档管理 (delete/stats)
    - 增量更新 (参考cocoindex数据流变更传播)
    """

    def __init__(self, storage_path: str = "~/.hermes/knowledge/"):
        """
        Args:
            storage_path: 知识库存储路径
        """
        self.storage_path = Path(storage_path).expanduser()
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # 向量模拟器
        self._vector_sim = _VectorSimulator()

        # 统计计数器（必须在_init_database之前）
        self._stats = {
            "total_documents": 0,
            "total_chunks": 0,
            "total_indexed_texts": 0,
            "total_searches": 0,
            "total_namespaces": 0,
        }

        # 数据库
        self._db_path = self.storage_path / "rag_knowledge.db"
        self._init_database()

        # 内存缓存
        self._cache: dict[str, dict] = {}

    # ───────── 数据库初始化 ─────────

    def _init_database(self):
        """初始化SQLite数据库。"""
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                namespace TEXT DEFAULT 'default',
                tokens TEXT DEFAULT '{}',
                chunk_ids TEXT DEFAULT '[]',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                text TEXT NOT NULL,
                position INTEGER NOT NULL,
                tokens TEXT DEFAULT '{}',
                embedding BLOB,
                FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_doc_namespace
            ON documents(namespace)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunk_doc
            ON chunks(doc_id)
        """)

        conn.commit()
        conn.close()

        # 加载统计
        self._load_stats()

    def _load_stats(self):
        """从数据库加载统计信息。"""
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        self._stats["total_documents"] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM chunks")
        self._stats["total_chunks"] = cursor.fetchone()[0]
        conn.close()

    # ───────── 文本分块 ─────────

    def _chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
        """
        将文本分块。

        Args:
            text: 原始文本
            chunk_size: 每块字符数
            overlap: 重叠字符数

        Returns:
            list[str]: 文本块列表
        """
        if not text:
            return []

        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            # 尽量在句号处断开
            if end < len(text):
                # 找最近的句号/换行
                search_start = max(end - 100, start)
                cut_positions = []
                for sep in ['。', '！', '？', '\n\n', '. ', '!\n', '?\n']:
                    pos = text.rfind(sep, search_start, end)
                    if pos > search_start:
                        cut_positions.append(pos + len(sep))
                if cut_positions:
                    end = max(cut_positions)

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - overlap if end < len(text) else len(text)

        return chunks if chunks else [text]

    # ───────── 索引文本 ─────────

    def index_text(
        self,
        text: str,
        metadata: Optional[dict] = None,
        namespace: str = "default",
    ) -> str:
        """
        索引文本到知识库。

        Args:
            text: 文本内容
            metadata: 元数据字典 (如 {source, author, tags})
            namespace: 命名空间，用于分类隔离

        Returns:
            str: 文档ID
        """
        if not text or not text.strip():
            raise ValueError("文本内容不能为空")

        metadata = metadata or {}
        doc_id = self._generate_doc_id(text, namespace)

        # 分块
        chunks = self._chunk_text(text)
        chunk_ids = []

        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()

        # 向量化
        text_tokens = self._vector_sim.embed(text)

        now = time.time()

        # 插入文档
        cursor.execute(
            "INSERT OR REPLACE INTO documents (doc_id, text, metadata, namespace, tokens, chunk_ids, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                doc_id,
                text,
                json.dumps(metadata, ensure_ascii=False),
                namespace,
                json.dumps(dict(text_tokens.most_common(100))),
                json.dumps([]),
                now,
                now,
            )
        )

        # 插入块
        for i, chunk_text in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            chunk_ids.append(chunk_id)
            chunk_tokens = self._vector_sim.embed(chunk_text)

            cursor.execute(
                "INSERT OR REPLACE INTO chunks (chunk_id, doc_id, text, position, tokens, embedding) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    chunk_id,
                    doc_id,
                    chunk_text,
                    i,
                    json.dumps(dict(chunk_tokens.most_common(50))),
                    b"",  # 模拟嵌入向量（真实场景存二进制向量）
                )
            )

        # 更新文档的chunk_ids
        cursor.execute(
            "UPDATE documents SET chunk_ids = ? WHERE doc_id = ?",
            (json.dumps(chunk_ids), doc_id),
        )

        conn.commit()
        conn.close()

        # 更新统计
        self._stats["total_documents"] += 1
        self._stats["total_chunks"] += len(chunks)
        self._stats["total_indexed_texts"] += 1
        self._stats["last_index_time"] = now

        return doc_id

    def _generate_doc_id(self, text: str, namespace: str) -> str:
        """生成唯一文档ID。"""
        raw = f"{namespace}:{text[:200]}:{time.time()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:24]

    # ───────── 搜索 ─────────

    def search(
        self,
        query: str,
        top_k: int = 5,
        namespace: Optional[str] = None,
    ) -> list[dict]:
        """
        语义搜索知识库。

        Args:
            query: 查询字符串
            top_k: 返回结果数
            namespace: 限定命名空间 (None表示全部)

        Returns:
            list[dict]: 搜索结果，每个包含:
                - doc_id: 文档ID
                - text: 匹配片段
                - chunk_id: 块ID
                - relevance: 相关性评分 (0-1)
                - metadata: 文档元数据
                - context: 片段上下文
                - position: 块位置
        """
        if not query or not query.strip():
            return []

        self._stats["total_searches"] += 1

        # 查询向量
        query_tokens = self._vector_sim.embed(query)

        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()

        # 查询所有块
        if namespace:
            cursor.execute(
                "SELECT c.chunk_id, c.doc_id, c.text, c.position, c.tokens, d.metadata, d.namespace "
                "FROM chunks c JOIN documents d ON c.doc_id = d.doc_id "
                "WHERE d.namespace = ?",
                (namespace,)
            )
        else:
            cursor.execute(
                "SELECT c.chunk_id, c.doc_id, c.text, c.position, c.tokens, d.metadata, d.namespace "
                "FROM chunks c JOIN documents d ON c.doc_id = d.doc_id"
            )

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return []

        # 计算相关性
        scored_results = []
        for chunk_id, doc_id, text, position, tokens_json, metadata_json, ns in rows:
            try:
                chunk_tokens = Counter(json.loads(tokens_json))
            except (json.JSONDecodeError, TypeError):
                chunk_tokens = self._vector_sim.embed(text)

            # 余弦相似度
            vec_sim = self._vector_sim.cosine_similarity(query_tokens, chunk_tokens)

            # 关键词重叠
            kw_overlap = self._vector_sim.keyword_overlap(query, text)

            # 综合评分
            relevance = 0.6 * vec_sim + 0.4 * kw_overlap

            if relevance > 0.05:  # 过滤低相关
                try:
                    metadata_dict = json.loads(metadata_json) if metadata_json else {}
                except json.JSONDecodeError:
                    metadata_dict = {}

                # 片段上下文
                context = self._get_context(text, query)

                scored_results.append({
                    "chunk_id": chunk_id,
                    "doc_id": doc_id,
                    "text": text[:500],  # 限制长度
                    "relevance": round(relevance, 4),
                    "metadata": metadata_dict,
                    "namespace": ns,
                    "context": context,
                    "position": position,
                })

        # 排序并取top_k
        scored_results.sort(key=lambda x: x["relevance"], reverse=True)
        return scored_results[:top_k]

    def _get_context(self, text: str, query: str) -> dict:
        """提取查询上下文的片段。"""
        query_terms = set(re.findall(r'[\w\u4e00-\u9fff]+', query.lower()))
        text_terms = set(re.findall(r'[\w\u4e00-\u9fff]+', text.lower()))
        matches = query_terms & text_terms

        return {
            "query_terms": list(query_terms),
            "match_terms": list(matches),
            "match_count": len(matches),
            "text_length": len(text),
        }

    # ───────── 文档删除 ─────────

    def delete_document(self, doc_id: str) -> bool:
        """
        删除文档及其所有块。

        Args:
            doc_id: 文档ID

        Returns:
            bool: 是否成功删除
        """
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()

        # 检查存在
        cursor.execute("SELECT doc_id FROM documents WHERE doc_id = ?", (doc_id,))
        if not cursor.fetchone():
            conn.close()
            return False

        # 删除块
        cursor.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
        deleted_chunks = cursor.rowcount

        # 删除文档
        cursor.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        deleted_docs = cursor.rowcount

        conn.commit()
        conn.close()

        if deleted_docs > 0:
            self._stats["total_documents"] -= 1
            self._stats["total_chunks"] -= deleted_chunks

        return deleted_docs > 0

    # ───────── 统计 ─────────

    def stats(self) -> dict:
        """
        获取知识库统计信息。

        Returns:
            dict: 统计信息
        """
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()

        # 各命名空间文档数
        cursor.execute(
            "SELECT namespace, COUNT(*) as cnt FROM documents GROUP BY namespace"
        )
        namespaces = {row[0]: row[1] for row in cursor.fetchall()}

        # 总大小
        cursor.execute("SELECT SUM(LENGTH(text)) FROM documents")
        total_size = cursor.fetchone()[0] or 0

        # 平均分块数
        cursor.execute("SELECT AVG(chunk_count) FROM (SELECT COUNT(*) as chunk_count FROM chunks GROUP BY doc_id)")
        avg_chunks = cursor.fetchone()[0] or 0

        # 最近文档
        cursor.execute(
            "SELECT doc_id, namespace, created_at FROM documents ORDER BY created_at DESC LIMIT 5"
        )
        recent = [
            {
                "doc_id": row[0],
                "namespace": row[1],
                "created_at": row[2],
            }
            for row in cursor.fetchall()
        ]

        conn.close()

        return {
            "total_documents": self._stats["total_documents"],
            "total_chunks": self._stats["total_chunks"],
            "total_searches": self._stats["total_searches"],
            "total_indexed_texts": self._stats["total_indexed_texts"],
            "total_size_bytes": total_size,
            "avg_chunks_per_doc": round(avg_chunks, 1),
            "namespaces": namespaces,
            "recent_documents": recent,
            "storage_path": str(self.storage_path),
            "last_index_time": self._stats["last_index_time"],
        }

    # ───────── 工具方法 ─────────

    def get_document(self, doc_id: str) -> Optional[dict]:
        """获取文档详情。"""
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT doc_id, text, metadata, namespace, chunk_ids, created_at, updated_at "
            "FROM documents WHERE doc_id = ?",
            (doc_id,),
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "doc_id": row[0],
            "text": row[1][:1000],
            "metadata": json.loads(row[2]) if row[2] else {},
            "namespace": row[3],
            "chunk_ids": json.loads(row[4]) if row[4] else [],
            "created_at": row[5],
            "updated_at": row[6],
        }

    def list_namespaces(self) -> list[str]:
        """列出所有命名空间。"""
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT namespace FROM documents")
        namespaces = [row[0] for row in cursor.fetchall()]
        conn.close()
        return namespaces

    def clear(self) -> int:
        """清空知识库（保留表结构）。"""
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chunks")
        deleted_chunks = cursor.rowcount
        cursor.execute("DELETE FROM documents")
        deleted_docs = cursor.rowcount
        conn.commit()
        conn.close()

        self._stats["total_documents"] = 0
        self._stats["total_chunks"] = 0

        return deleted_docs

    def __repr__(self) -> str:
        return f"RAGEngine(storage={self.storage_path}, docs={self._stats['total_documents']})"
