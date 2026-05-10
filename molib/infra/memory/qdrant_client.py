import os, json
import random

# 多租户：使用 TENANT_ID 作为 collection 前缀
try:
    from molib.infra.config.tenant_config import TENANT_ID
    _tenant_prefix = f"{TENANT_ID}_"
except ImportError:
    TENANT_ID = "default"
    _tenant_prefix = "default_"

# 尝试导入dashscope，如果不可用则使用模拟嵌入
try:
    import dashscope
    from dashscope import TextEmbedding
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    # 创建模拟TextEmbedding类
    class TextEmbedding:
        @staticmethod
        def call(model, input):
            class MockResponse:
                status_code = 200
                output = {"embeddings": [{"embedding": [random.uniform(-0.1, 0.1) for _ in range(1536)]}]}
            return MockResponse()
    # 创建模拟dashscope模块
    class MockDashscope:
        api_key = None
    dashscope = MockDashscope()

from qdrant_client import QdrantClient as QC
from qdrant_client.models import Distance, VectorParams, PointStruct

HOST = os.getenv("QDRANT_HOST", "qdrant")
PORT = int(os.getenv("QDRANT_PORT", "6333"))
DIM = 1536
COLS = {
    "users": f"{_tenant_prefix}user_behaviors",
    "content": f"{_tenant_prefix}winning_content",
    "decisions": f"{_tenant_prefix}decision_history",
    "knowledge": f"{_tenant_prefix}knowledge_base",
}

class MolinMemory:
    def __init__(self):
        self.client = QC(host=HOST, port=PORT)
        if DASHSCOPE_AVAILABLE:
            dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

    def init_collections(self):
        existing = [c.name for c in self.client.get_collections().collections]
        for col in COLS.values():
            if col not in existing:
                self.client.create_collection(col, vectors_config=VectorParams(
                    size=DIM, distance=Distance.COSINE))

    def _embed(self, text):
        r = TextEmbedding.call(model="text-embedding-v2", input=text)
        if r.status_code == 200:
            return r.output["embeddings"][0]["embedding"]
        raise Exception(f"Embed failed: {r.code}")

    def upsert_user(self, user_id, behavior):
        self.client.upsert(COLS["users"], points=[PointStruct(
            id=abs(hash(user_id)) % 10**9,
            vector=self._embed(json.dumps(behavior, ensure_ascii=False)),
            payload={"user_id": user_id, **behavior})])

    def search_similar_users(self, query, limit=10):
        results = self.client.search(COLS["users"], self._embed(query),
                                     limit=limit, with_payload=True)
        return [{"user_id": r.payload.get("user_id"), "score": r.score} for r in results]

    def save_winning_content(self, cid, content, perf):
        text = f"标题:{content.get('title','')} 内容:{content.get('body','')}"
        self.client.upsert(COLS["content"], points=[PointStruct(
            id=abs(hash(cid)) % 10**9, vector=self._embed(text),
            payload={"content_id": cid, "content": content, "performance": perf})])

    def save_knowledge(self, doc_id, title, text_content):
        """保存系统知识库/生态文档"""
        try:
            vector = self._embed(text_content[:8000])  # 防止超长
            self.client.upsert(COLS["knowledge"], points=[PointStruct(
                id=abs(hash(doc_id)) % 10**9, vector=vector,
                payload={"doc_id": doc_id, "title": title, "content": text_content[:2000]})])
            return True
        except Exception as e:
            return False
