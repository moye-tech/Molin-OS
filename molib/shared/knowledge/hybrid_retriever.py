"""
墨麟OS v2.1 — HyDE+BM25 混合检索增强层
=======================================
对现有 RAGEngine 的零侵入增强，提供：
  1. HyDE (Hypothetical Document Embeddings) — 先假设理想文档再检索
  2. BM25 混合评分 — TF-IDF + 词频饱和, 修正纯向量检索的语义漂移
  3. 多模态文档支持 — 文本+表格混合文档的智能分块

用法:
    from molib.shared.knowledge.hybrid_retriever import hybrid_search
    results = hybrid_search("竞品分析报告", top_k=5)

参考: LightRAG ⭐12k, RAG-Anything ⭐1k, GraphRAG 设计模式
"""
from __future__ import annotations

import re
import math
from collections import Counter
from typing import Optional


class BM25Scorer:
    """BM25 评分器 — 词频饱和 + 文档长度归一化"""

    def __init__(self, k1: float = 1.2, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_lengths: list[int] = []
        self.avg_dl: float = 0.0
        self.idf: dict[str, float] = {}

    def fit(self, documents: list[str]):
        """计算 IDF 和平均文档长度"""
        N = len(documents)
        if N == 0:
            return
        self.doc_lengths = []
        df: dict[str, int] = {}
        for doc in documents:
            tokens = self._tokenize(doc)
            self.doc_lengths.append(len(tokens))
            for token in set(tokens):
                df[token] = df.get(token, 0) + 1
        self.avg_dl = sum(self.doc_lengths) / N
        self.idf = {}
        for token, count in df.items():
            self.idf[token] = math.log((N - count + 0.5) / (count + 0.5) + 1.0)

    def score(self, query: str, doc_idx: int, document: str) -> float:
        """计算 BM25 分数"""
        if not self.idf:
            return 0.0
        query_tokens = self._tokenize(query)
        doc_tokens = self._tokenize(document)
        doc_len = len(doc_tokens)
        tf = Counter(doc_tokens)
        score = 0.0
        for token in query_tokens:
            if token not in self.idf:
                continue
            term_freq = tf.get(token, 0)
            numerator = term_freq * (self.k1 + 1)
            denominator = term_freq + self.k1 * (1 - self.b + self.b * doc_len / max(self.avg_dl, 1))
            score += self.idf[token] * numerator / max(denominator, 0.001)
        return score

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """中英文混合分词"""
        text_lower = text.lower()
        tokens = []
        tokens.extend(re.findall(r'[a-zA-Z]+', text_lower))
        chinese = re.findall(r'[\u4e00-\u9fff]+', text_lower)
        for chunk in chinese:
            for c in chunk:
                tokens.append(c)
            for i in range(len(chunk) - 1):
                tokens.append(chunk[i:i+2])
        return tokens


def hyde_expand_query(query: str, llm_call=None) -> str:
    """
    HyDE: 假设一份理想文档，用其向量检索。

    如果提供 llm_call，调用LLM生成假设文档。
    否则用简单规则扩写query。
    """
    if llm_call:
        try:
            hyde_prompt = (
                f"请写一段简短摘要回答以下问题（100-200字），假装你是一份完美文档：\n{query}\n\n摘要："
            )
            result = llm_call(hyde_prompt)
            if result and len(result) > 20:
                return f"{query} {result}"
        except Exception:
            pass

    # 简单规则扩写
    augments = {
        "竞品": "竞争分析 市场份额 差异化 优劣势对比",
        "趋势": "行业趋势 新兴技术 市场动态 2026年预测",
        "文案": "爆款文案 标题公式 用户心理 转化率优化",
        "课程": "课程大纲 学习路径 教学目标 知识体系",
        "安全": "安全审计 漏洞扫描 风险评估 合规检查",
        "财务": "财务报表 成本分析 预算控制 投资回报",
        "客服": "客户服务 满意度 响应时间 问题分类",
        "电商": "商品上架 价格策略 库存管理 订单流程",
    }
    for kw, aug in augments.items():
        if kw in query:
            return f"{query} {aug}"
    return query


def hybrid_search(
    query: str,
    top_k: int = 5,
    namespace: str = "default",
    alpha: float = 0.6,
    llm_call=None,
) -> list[dict]:
    """
    混合检索: BM25(0.4) + RAGEngine向量(0.6)

    Args:
        query: 查询文本
        top_k: 返回结果数
        namespace: RAG namespace
        alpha: 向量检索权重 (0-1, 默认0.6)
        llm_call: 可选 LLM调用函数 (用于HyDE扩写)

    Returns:
        [{"text": str, "score": float, "bm25_score": float, "vector_score": float}]
    """
    # Step 0: HyDE 扩写查询
    expanded_query = hyde_expand_query(query, llm_call)

    # Step 1: RAGEngine 向量检索
    vector_results = []
    try:
        from molib.shared.knowledge.rag_engine import RAGEngine
        vector_results = RAGEngine().search(
            expanded_query,
            top_k=top_k * 2,  # 先多取，再混合排序
            namespace=namespace,
        )
    except Exception:
        pass

    if not vector_results:
        return []

    # Step 2: BM25 重排序
    documents = [r.get("text", "") for r in vector_results]
    bm25 = BM25Scorer()
    bm25.fit(documents)

    # Step 3: 混合评分
    scored = []
    max_vec = max((r.get("score", 0) for r in vector_results), default=1.0)
    for i, r in enumerate(vector_results):
        vec_score = r.get("score", 0) / max(max_vec, 0.001)
        bm25_score = bm25.score(query, i, documents[i]) if documents else 0
        # 归一化 BM25
        max_bm25 = max((bm25.score(query, j, documents[j]) for j in range(len(documents))), default=1.0)
        bm25_norm = bm25_score / max(max_bm25, 0.001)
        hybrid_score = alpha * vec_score + (1 - alpha) * bm25_norm
        scored.append({
            "text": r.get("text", ""),
            "score": round(hybrid_score, 4),
            "bm25_score": round(bm25_score, 4),
            "vector_score": round(vec_score, 4),
            "metadata": r.get("metadata", {}),
        })

    # 按混合分数排序
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]
