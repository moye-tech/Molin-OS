"""知识图谱 — 基于 SQLite 的轻量实体-关系存储"""
import json
import aiosqlite
from pathlib import Path
from datetime import datetime
from typing import Optional

# 多租户路径
try:
    from molib.infra.config.tenant_config import get_kg_db_path
    KG_DB = Path(get_kg_db_path())
except ImportError:
    KG_DB = Path(__file__).resolve().parent.parent.parent / "data" / "sqlite" / "knowledge_graph.db"


class KnowledgeGraph:
    """轻量知识图谱：节点（实体）+ 边（关系）存储在 SQLite"""

    async def init(self):
        Path(KG_DB).parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(KG_DB) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    properties TEXT DEFAULT '{}',
                    namespace TEXT DEFAULT 'global',
                    created_at TEXT DEFAULT (datetime('now','localtime'))
                );
                CREATE TABLE IF NOT EXISTS relations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_entity TEXT NOT NULL,
                    to_entity TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    properties TEXT DEFAULT '{}',
                    namespace TEXT DEFAULT 'global',
                    created_at TEXT DEFAULT (datetime('now','localtime'))
                );
                CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(entity_type);
                CREATE INDEX IF NOT EXISTS idx_relation_from ON relations(from_entity);
                CREATE INDEX IF NOT EXISTS idx_relation_to ON relations(to_entity);
                CREATE INDEX IF NOT EXISTS idx_relation_type ON relations(relation_type);
            """)
            await db.commit()

    async def add_entity(self, entity_id: str, name: str, entity_type: str,
                         properties: dict = None, namespace: str = "global"):
        async with aiosqlite.connect(KG_DB) as db:
            await db.execute(
                "INSERT OR REPLACE INTO entities(entity_id, name, entity_type, properties, namespace) "
                "VALUES(?,?,?,?,?)",
                (entity_id, name, entity_type, json.dumps(properties or {}), namespace)
            )
            await db.commit()

    async def add_relation(self, from_entity: str, to_entity: str, relation_type: str,
                           weight: float = 1.0, properties: dict = None, namespace: str = "global"):
        async with aiosqlite.connect(KG_DB) as db:
            await db.execute(
                "INSERT OR REPLACE INTO relations(from_entity, to_entity, relation_type, weight, properties, namespace) "
                "VALUES(?,?,?,?,?,?)",
                (from_entity, to_entity, relation_type, weight, json.dumps(properties or {}), namespace)
            )
            await db.commit()

    async def get_entity(self, entity_id: str) -> Optional[dict]:
        async with aiosqlite.connect(KG_DB) as db:
            async with db.execute(
                "SELECT entity_id, name, entity_type, properties, created_at FROM entities WHERE entity_id = ?",
                (entity_id,)
            ) as cur:
                row = await cur.fetchone()
                if not row:
                    return None
                return {
                    "entity_id": row[0], "name": row[1], "entity_type": row[2],
                    "properties": json.loads(row[3]), "created_at": row[4],
                }

    async def get_relations(self, entity_id: str, direction: str = "both") -> list[dict]:
        """获取实体的关系（from/to/both）"""
        async with aiosqlite.connect(KG_DB) as db:
            if direction == "from":
                query = """
                    SELECT r.from_entity, r.to_entity, r.relation_type, r.weight, r.properties
                    FROM relations r WHERE r.from_entity = ?
                """
            elif direction == "to":
                query = """
                    SELECT r.from_entity, r.to_entity, r.relation_type, r.weight, r.properties
                    FROM relations r WHERE r.to_entity = ?
                """
            else:
                query = """
                    SELECT r.from_entity, r.to_entity, r.relation_type, r.weight, r.properties
                    FROM relations r WHERE r.from_entity = ? OR r.to_entity = ?
                """
                params = (entity_id, entity_id)
            async with db.execute(query, (entity_id,) if direction != "both" else params) as cur:
                rows = await cur.fetchall()
                return [
                    {"from": r[0], "to": r[1], "relation": r[2], "weight": r[3],
                     "properties": json.loads(r[4])}
                    for r in rows
                ]

    async def search_entities(self, name_pattern: str, entity_type: str = None,
                              limit: int = 20) -> list[dict]:
        """模糊搜索实体"""
        conditions = ["name LIKE ?"]
        values = [f"%{name_pattern}%"]
        if entity_type:
            conditions.append("entity_type = ?")
            values.append(entity_type)
        where = " AND ".join(conditions)
        async with aiosqlite.connect(KG_DB) as db:
            async with db.execute(
                f"SELECT entity_id, name, entity_type, properties, created_at "
                f"FROM entities WHERE {where} ORDER BY created_at DESC LIMIT ?",
                (*values, limit)
            ) as cur:
                rows = await cur.fetchall()
                return [
                    {"entity_id": r[0], "name": r[1], "entity_type": r[2],
                     "properties": json.loads(r[3]), "created_at": r[4]}
                    for r in rows
                ]

    async def get_subgraph(self, seed_entity_id: str, depth: int = 2) -> dict:
        """获取从某实体出发的子图（BFS）"""
        visited = set()
        nodes = []
        edges = []

        async def bfs(start_id: str, max_depth: int):
            queue = [(start_id, 0)]
            while queue:
                eid, d = queue.pop(0)
                if eid in visited or d > max_depth:
                    continue
                visited.add(eid)

                entity = await self.get_entity(eid)
                if entity:
                    nodes.append(entity)

                relations = await self.get_relations(eid, direction="both")
                for rel in relations:
                    edges.append(rel)
                    next_id = rel["to"] if rel["from"] == eid else rel["from"]
                    if next_id not in visited:
                        queue.append((next_id, d + 1))

        await bfs(seed_entity_id, depth)
        return {"nodes": nodes, "edges": edges, "node_count": len(nodes), "edge_count": len(edges)}

    async def ingest_from_text(self, text: str, namespace: str = "global") -> dict:
        """从文本中提取实体和关系（简单关键词匹配）"""
        # 预定义实体类型关键词映射
        type_keywords = {
            "person": ["张", "李", "王", "赵", "刘", "陈", "杨", "黄", "周", "吴", "学员", "老师", "顾问"],
            "product": ["课程", "服务", "套餐", "产品", "方案", "班", "训练营"],
            "concept": ["方法", "流程", "框架", "模型", "策略", "机制"],
            "event": ["活动", "营销", "促销", "直播", "发布"],
        }

        ingested = {"entities": 0, "relations": 0}
        for entity_type, keywords in type_keywords.items():
            for kw in keywords:
                if kw in text:
                    eid = f"{entity_type}_{kw}"
                    await self.add_entity(eid, kw, entity_type, namespace=namespace)
                    ingested["entities"] += 1

        # 简单关系：同一段落中出现的实体自动关联
        paragraphs = text.split("\n\n")
        for para in paragraphs:
            found = []
            for entity_type, keywords in type_keywords.items():
                for kw in keywords:
                    if kw in para:
                        found.append(f"{entity_type}_{kw}")
            for i in range(len(found) - 1):
                await self.add_relation(found[i], found[i + 1], "co_occurs",
                                        weight=0.5, namespace=namespace)
                ingested["relations"] += 1

        return ingested
