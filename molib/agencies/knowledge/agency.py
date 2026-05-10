"""墨脑知识子公司 — 工作经验沉淀、SOP自动更新、最佳实践提炼、知识图谱构建"""
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from molib.agencies.base import BaseAgency, Task, AgencyResult

KNOWLEDGE_SYSTEM_PROMPT = """你是墨脑知识子公司的知识管理专家。
根据需求进行知识提取、SOP更新、文档编写或知识图谱构建。

输出必须是严格的 JSON 格式：
{
  "knowledge_type": "extraction|sop_update|doc_writing|graph_building",
  "title": "知识标题",
  "summary": "知识摘要",
  "key_concepts": ["概念1", "概念2"],
  "action_items": ["行动项1", "行动项2"],
  "related_topics": ["关联主题1", "关联主题2"],
  "quality_score": 质量评分(1-10)
}"""

PROMPTS_DIR = Path(__file__).parent / "prompts"
WORKER_PROMPTS = {}
for _wt, _wf in {
    "knowledge_extractor": "knowledge_extractor.txt",
    "sop_manager": "sop_manager.txt",
    "knowledge_mapper": "knowledge_mapper.txt",
    "doc_writer": "doc_writer.txt",
}.items():
    _fp = PROMPTS_DIR / _wf
    if _fp.exists():
        WORKER_PROMPTS[_wt] = _fp.read_text(encoding="utf-8")


@dataclass
class KnowledgeEntry:
    id: str
    title: str
    knowledge_type: str
    concepts: List[str] = field(default_factory=list)
    summary: str = ""
    quality_score: float = 5.0
    created_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id, "title": self.title, "knowledge_type": self.knowledge_type,
            "concepts": self.concepts, "summary": self.summary,
            "quality_score": self.quality_score, "created_at": self.created_at,
        }


class KnowledgeAgency(BaseAgency):
    agency_id = "knowledge"
    trigger_keywords = ["知识库", "总结", "复盘", "文档", "SOP更新", "经验沉淀", "最佳实践", "方法论", "归档"]
    approval_level = "low"
    cost_level = "low"

    def __init__(self):
        super().__init__()
        self._load_kg()
        self._load_sqlite()

    def _load_kg(self):
        try:
            from molib.infra.memory.knowledge_graph import KnowledgeGraph
            self.kg = KnowledgeGraph()
        except ImportError:
            self.kg = None

    def _load_sqlite(self):
        try:
            from molib.infra.memory.sqlite_client import SQLiteClient
            self._db = SQLiteClient()
        except ImportError:
            self._db = None

    def _select_worker(self, desc: str) -> str:
        desc_l = desc.lower()
        if any(k in desc_l for k in ["sop", "流程", "版本"]):
            return "sop_manager"
        if any(k in desc_l for k in ["图谱", "关联", "知识地图"]):
            return "knowledge_mapper"
        if any(k in desc_l for k in ["文档", "撰写", "手册", "报告"]):
            return "doc_writer"
        return "knowledge_extractor"

    def _parse_knowledge_json(self, text: str) -> dict:
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            if "```json" in text:
                try:
                    start = text.index("```json") + 7
                    end = text.index("```", start)
                    return json.loads(text[start:end].strip())
                except Exception:
                    pass
        return {
            "knowledge_type": "extraction",
            "title": "未命名知识",
            "summary": text[:300],
            "key_concepts": [],
            "action_items": [],
            "related_topics": [],
            "quality_score": 5.0,
        }

    async def execute(self, task: Task) -> AgencyResult:
        self.load_sop()
        sop_prompt = self.get_sop_prompt()
        desc = task.payload.get("description", "")
        worker_type = self._select_worker(desc)

        # 知识图谱操作：如果请求包含图谱相关关键词，直接操作图谱
        kg_result = {}
        if worker_type == "knowledge_mapper" and self.kg:
            try:
                await self.kg.init()
                # 尝试从文本中提取实体和关系
                ingested = await self.kg.ingest_from_text(desc, namespace="knowledge")
                kg_result = {"ingested": ingested}
                # 搜索相关实体
                related = await self.kg.search_entities(name_pattern=desc[:50], limit=10)
                kg_result["related_entities"] = related
            except Exception as e:
                kg_result["error"] = str(e)

        # 知识检索：从 knowledge_base 中搜索相关内容
        search_result = []
        if self._db:
            try:
                search_result = await self._db.search_knowledge(query=desc[:100], limit=5)
            except Exception:
                pass

        # 查询历史知识记录
        history_info = ""
        if self._db:
            try:
                memories = await self._db.retrieve_memory(
                    key="knowledge_", scenario="transactional", namespace="knowledge", limit=3
                )
                if memories:
                    history_info = "\n历史知识参考:\n" + "\n".join(
                        f"- {m['data'].get('title', m['key'])}" for m in memories
                    )
            except Exception:
                pass

        system_prompt = WORKER_PROMPTS.get(worker_type, KNOWLEDGE_SYSTEM_PROMPT)
        system_prompt += "\n\n" + KNOWLEDGE_SYSTEM_PROMPT
        if sop_prompt:
            system_prompt += f"\n\n请遵循SOP规范：\n{sop_prompt}"

        context_parts = [desc]
        if search_result:
            context_parts.append(f"\n已有相关知识:\n" + "\n".join(
                f"- {r['title']}: {r['content'][:100]}" for r in search_result
            ))
        if history_info:
            context_parts.append(history_info)
        if kg_result.get("related_entities"):
            context_parts.append(f"\n图谱相关实体:\n" + "\n".join(
                f"- {e['name']} ({e['entity_type']})" for e in kg_result["related_entities"]
            ))

        prompt = "\n".join(context_parts)

        start = time.time()
        res = await self.router.call_async(
            prompt=prompt, system=system_prompt,
            task_type="knowledge", team="knowledge",
        )
        parsed = self._parse_knowledge_json(res.get("text", ""))

        score = parsed.get("quality_score", 5.0)

        # 持久化到 SQLite + knowledge_base
        if self._db:
            try:
                entry = KnowledgeEntry(
                    id=f"knowledge_{int(time.time())}",
                    title=parsed.get("title", ""),
                    knowledge_type=parsed.get("knowledge_type", ""),
                    concepts=parsed.get("key_concepts", []),
                    summary=parsed.get("summary", ""),
                    quality_score=score,
                    created_at=time.time(),
                )
                await self._db.store_memory(
                    key=f"knowledge_{entry.id}",
                    data=entry.to_dict(),
                    scenario="transactional",
                    namespace="knowledge"
                )
                # 同步到 knowledge_base 表
                await self._db.add_knowledge(
                    title=entry.title,
                    content=entry.summary,
                    source="knowledge_agency",
                    tags=entry.concepts
                )
            except Exception:
                pass

        # 知识图谱：将新概念添加到图谱
        if self.kg:
            try:
                await self.kg.init()
                for concept in parsed.get("key_concepts", []):
                    await self.kg.add_entity(
                        f"concept_{concept}", concept, "concept",
                        namespace="knowledge"
                    )
                # 与知识标题建立关系
                if parsed.get("title"):
                    await self.kg.add_entity(
                        f"knowledge_{parsed['title']}", parsed["title"], "document",
                        properties={"type": parsed.get("knowledge_type")},
                        namespace="knowledge"
                    )
                    for concept in parsed.get("key_concepts", [])[:3]:
                        await self.kg.add_relation(
                            f"knowledge_{parsed['title']}", f"concept_{concept}",
                            "contains", namespace="knowledge"
                        )
            except Exception:
                pass

        output = {
            "knowledge_type": parsed.get("knowledge_type", "extraction"),
            "title": parsed.get("title", ""),
            "summary": parsed.get("summary", ""),
            "key_concepts": parsed.get("key_concepts", []),
            "action_items": parsed.get("action_items", []),
            "related_topics": parsed.get("related_topics", []),
            "worker_type": worker_type,
            "quality_score": score,
            "model_used": res.get("model", "unknown"),
        }
        if kg_result:
            output["knowledge_graph"] = kg_result
        if search_result:
            output["search_results"] = search_result

        return AgencyResult(
            task_id=task.task_id, agency_id=self.agency_id, status="success",
            output=output,
            cost=res.get("cost", 0.0),
            latency=round(time.time() - start, 2),
        )
