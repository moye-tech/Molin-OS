"""
墨麟OS v2.0 — ExperienceVault 经验金库
解决 BUG-01 (经验黑洞) + BUG-03 (执行前不查经验)

Worker成功执行后自动调用 vault.record() 将经验写入 RAGEngine；
Worker执行前自动调用 vault.recall() 检索相似经验并注入prompt。
"""
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class ExperienceEntry:
    worker_id: str
    task_summary: str
    approach: str
    output_snippet: str
    quality_score: float = 85.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class ExperienceVault:
    """经验金库：Worker成功经验的存取中心"""

    async def record(self, worker_id: str, task, result) -> None:
        """Worker成功后自动调用，将经验写入RAG"""
        if not hasattr(result, 'status'):
            return
        if result.status != "success":
            return

        approach = await self._extract_approach(task, result)
        text = (
            f"[经验][{worker_id}]\n"
            f"任务: {str(task.payload)[:200]}\n"
            f"成功策略: {approach}\n"
            f"输出摘要: {json.dumps(result.output, ensure_ascii=False)[:300]}"
        )
        try:
            from molib.shared.knowledge.rag_engine import RAGEngine
            RAGEngine().index_text(
                text=text,
                metadata={"type": "experience", "worker": worker_id},
                namespace=f"experience:{worker_id}"
            )
        except (ImportError, Exception):
            pass

    async def recall(self, worker_id: str, task, top_k: int = 3) -> list:
        """执行前查询：找出同类任务的成功经验"""
        try:
            from molib.shared.knowledge.rag_engine import RAGEngine
            query = f"{worker_id} {str(task.payload)[:100]}"
            results = RAGEngine().search(
                query, top_k=top_k, namespace=f"experience:{worker_id}"
            )
            return [r["text"] for r in results if r.get("score", 0) > 0.7]
        except (ImportError, Exception):
            return []

    async def _extract_approach(self, task, result) -> str:
        """用LLM萃取本次执行的关键成功策略"""
        output = result.output or {}
        if isinstance(output, dict):
            keys = ["summary", "approach", "strategy", "outline", "key_finding"]
            for k in keys:
                if k in output:
                    return str(output[k])[:200]
            return str(list(output.keys()))[:100]
        return str(output)[:200]


vault = ExperienceVault()
