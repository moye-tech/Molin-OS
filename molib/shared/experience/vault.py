"""
墨麟OS v2.0 — ExperienceVault 经验金库
解决 BUG-01 (经验黑洞) + BUG-03 (执行前不查经验)

Worker成功执行后自动调用 vault.record() 将经验写入 RAGEngine；
Worker执行前自动调用 vault.recall() 检索相似经验并注入prompt。

v2.1: _extract_approach 升级为 LLM 驱动萃取（兜底字典遍历）
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
        """用LLM萃取本次执行的关键成功策略（兜底：字典遍历）"""
        output = result.output or {}

        # ── 优先：LLM 萃取策略摘要 ──
        try:
            from molib.shared.llm.llm_router import LLMRouter
            router = LLMRouter()
            task_summary = str(task.payload)[:300] if hasattr(task, 'payload') else str(task)
            output_summary = json.dumps(output, ensure_ascii=False)[:500] if isinstance(output, dict) else str(output)[:500]

            llm_prompt = (
                "你是墨麟OS经验萃取专家。请从以下Worker执行结果中，提炼1-2句话的关键成功策略。\n\n"
                f"任务描述: {task_summary}\n"
                f"执行输出: {output_summary}\n\n"
                "请输出: 一句话策略摘要（不超过100字）。只输出策略文本，不要加任何标记。"
            )
            approach = await router.chat(llm_prompt, max_tokens=120)
            if approach and len(approach.strip()) > 5:
                return approach.strip()[:200]
        except (ImportError, Exception):
            pass

        # ── 兜底：字典关键字段遍历 ──
        if isinstance(output, dict):
            keys = ["summary", "approach", "strategy", "outline", "key_finding", "key_findings"]
            for k in keys:
                if k in output:
                    val = output[k]
                    if isinstance(val, list):
                        return "; ".join(str(v) for v in val[:3])[:200]
                    return str(val)[:200]
            # 尝试递归找第一层嵌套的 summary
            for v in output.values():
                if isinstance(v, dict) and "summary" in v:
                    return str(v["summary"])[:200]
            return str(list(output.keys()))[:100]
        return str(output)[:200]


vault = ExperienceVault()
