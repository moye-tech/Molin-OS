"""墨脑知识 Worker — RAG + SOP管理 + 知识图谱"""
from .base import SmartSubsidiaryWorker as _Base, Task, WorkerResult

class Knowledge(_Base):
    worker_id = "knowledge"
    worker_name = "墨脑知识"
    description = "知识库RAG与SOP管理 | 知识图谱构建"
    oneliner = "知识库知识图谱SOP"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "知识库RAG检索与问答",
            "SOP标准操作流程管理",
            "代码知识图谱自动构建",
            "概念图谱与知识关联分析",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨脑知识",
            "vp": "共同服务",
            "description": "知识库RAG与SOP管理 | 知识图谱构建",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            action = task.payload.get("action", "query")
            query = task.payload.get("query", "")
            namespace = task.payload.get("namespace")

            if action == "build_knowledge_graph":
                from ...shared.knowledge.knowledge_grapher import KnowledgeGrapher
                files = task.payload.get("files", {})
                grapher = KnowledgeGrapher()
                graph = grapher.build_from_code(files)
                output = {
                    "action": "knowledge_graph",
                    "node_count": len(graph.nodes),
                    "edge_count": len(graph.edges),
                    "mermaid": grapher.export_mermaid(graph),
                    "status": "graph_built"
                }
            elif action == "build_concept_graph":
                from ...shared.knowledge.knowledge_grapher import KnowledgeGrapher
                pages = task.payload.get("pages", {})
                grapher = KnowledgeGrapher()
                graph = grapher.build_from_knowledge_base(pages)
                output = {
                    "action": "concept_graph",
                    "node_count": len(graph.nodes),
                    "edge_count": len(graph.edges),
                    "json": grapher.export_json(graph),
                    "status": "graph_built"
                }
            elif action in ("index", "index_text"):
                from ...shared.knowledge.rag_engine import RAGEngine
                engine = RAGEngine()
                text = task.payload.get("text", "")
                metadata = task.payload.get("metadata", {})
                ns = task.payload.get("namespace", query)
                if text:
                    engine.index_text(text, metadata=metadata, namespace=ns or query)
                    output = {"action": "indexed", "text_len": len(text), "namespace": ns or query, "status": "indexed"}
                else:
                    output = {"action": "indexed", "status": "skipped", "reason": "text为空"}
            elif action in ("stats", "status"):
                from ...shared.knowledge.rag_engine import RAGEngine
                engine = RAGEngine()
                output = engine.stats()
                output["action"] = "stats"
            else:
                # 默认 query：调 RAGEngine 语义搜索
                from ...shared.knowledge.rag_engine import RAGEngine
                engine = RAGEngine()
                top_k = task.payload.get("top_k", 5)
                results = engine.search(query, top_k=top_k, namespace=namespace)
                output = {
                    "query": query,
                    "results": results,
                    "total": len(results),
                    "status": "knowledge_retrieved"
                }
            return WorkerResult(
                task_id=task.task_id,
                worker_id=self.worker_id,
                status="success",
                output=output,
            )
        except Exception as e:
            return WorkerResult(
                task_id=task.task_id,
                worker_id=self.worker_id,
                status="error",
                output={},
                error=str(e),
            )
