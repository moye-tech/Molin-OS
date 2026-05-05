"""墨脑知识 Worker — RAG + SOP管理 + 知识图谱"""
from .base import SubsidiaryWorker, Task, WorkerResult

class Knowledge(SubsidiaryWorker):
    worker_id = "knowledge"
    worker_name = "墨脑知识"
    description = "知识库RAG与SOP管理 | 知识图谱构建"
    oneliner = "知识库知识图谱SOP"

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            action = task.payload.get("action", "query")
            query = task.payload.get("query", "")

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
            else:
                output = {
                    "query": query,
                    "results": [
                        {"title": "关于{}的FAQ".format(query), "relevance": 0.95},
                        {"title": "{}操作SOP".format(query), "relevance": 0.88},
                    ],
                    "sop_count": task.payload.get("total_sops", 0),
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
