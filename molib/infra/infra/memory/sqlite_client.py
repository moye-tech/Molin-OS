from __future__ import annotations
import os
import json
import math
import aiosqlite
from pathlib import Path
from datetime import date, datetime

# 多租户路径：优先使用 TENANT_ID 环境变量
try:
    from molib.infra.config.tenant_config import get_sqlite_path, ensure_tenant_dirs
    TENANT_MODE = True
except ImportError:
    TENANT_MODE = False

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sqlite", "hermes.db")
if TENANT_MODE:
    # 确保租户目录存在
    try:
        ensure_tenant_dirs()
    except Exception:
        pass
    DEFAULT_DB_PATH = get_sqlite_path()

DB = os.getenv("SQLITE_DB_PATH", os.path.abspath(DEFAULT_DB_PATH))


def _days_since(timestamp_str: str) -> float:
    """计算从时间戳到现在的天数"""
    try:
        created = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        return max(0, (datetime.now() - created).total_seconds() / 86400)
    except (ValueError, TypeError):
        return 0

DDL = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event TEXT NOT NULL, data TEXT, source TEXT, namespace TEXT DEFAULT 'global',
    created_at TEXT DEFAULT (datetime('now','localtime')));
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY, tags TEXT DEFAULT '[]',
    ltv REAL DEFAULT 0.0, intent_score REAL DEFAULT 0.0,
    stage TEXT DEFAULT 'cold', platform TEXT, contact TEXT,
    namespace TEXT DEFAULT 'global',
    created_at TEXT DEFAULT (datetime('now','localtime')),
    updated_at TEXT DEFAULT (datetime('now','localtime')));
CREATE TABLE IF NOT EXISTS deals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT, amount REAL NOT NULL,
    stage TEXT DEFAULT 'lead', package TEXT, source TEXT,
    namespace TEXT DEFAULT 'global',
    created_at TEXT DEFAULT (datetime('now','localtime')));
CREATE TABLE IF NOT EXISTS model_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT, model TEXT, team TEXT, task_type TEXT,
    cost REAL DEFAULT 0.0, latency REAL DEFAULT 0.0,
    success INTEGER DEFAULT 1, fallback INTEGER DEFAULT 0,
    namespace TEXT DEFAULT 'global',
    created_at TEXT DEFAULT (datetime('now','localtime')));
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT, roi REAL DEFAULT 0.0, confidence REAL DEFAULT 0.0,
    input_summary TEXT, output_json TEXT,
    namespace TEXT DEFAULT 'global',
    created_at TEXT DEFAULT (datetime('now','localtime')));
CREATE TABLE IF NOT EXISTS memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_key TEXT NOT NULL, data TEXT,
    scenario TEXT NOT NULL, namespace TEXT DEFAULT 'global',
    importance_score REAL DEFAULT 1.0,
    metadata TEXT DEFAULT '{}',
    created_at TEXT DEFAULT (datetime('now','localtime')),
    updated_at TEXT DEFAULT (datetime('now','localtime'))
);
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
    title, content, source, tags,
    content='knowledge_base', content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);
CREATE TABLE IF NOT EXISTS knowledge_base (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL, content TEXT,
    source TEXT DEFAULT 'system', tags TEXT DEFAULT '[]',
    namespace TEXT DEFAULT 'global',
    created_at TEXT DEFAULT (datetime('now','localtime')),
    updated_at TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS pending_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    approval_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL, description TEXT,
    task_type TEXT, agency_id TEXT,
    decision_data TEXT DEFAULT '{}',
    status TEXT DEFAULT 'pending',
    reviewer_comment TEXT,
    instance_code TEXT DEFAULT '',
    namespace TEXT DEFAULT 'global',
    created_at TEXT DEFAULT (datetime('now','localtime')),
    reviewed_at TEXT
);
CREATE TABLE IF NOT EXISTS ads_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    spend_cny REAL DEFAULT 0.0,
    leads INTEGER DEFAULT 0,
    m0 INTEGER DEFAULT 0,
    m1 INTEGER DEFAULT 0,
    m2 INTEGER DEFAULT 0,
    cac_cny REAL DEFAULT 0.0,
    roi REAL DEFAULT 0.0,
    ctr REAL DEFAULT 0.0,
    cvr REAL DEFAULT 0.0,
    namespace TEXT DEFAULT 'global',
    created_at TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS evolution_knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL, content TEXT,
    source_task TEXT, outcome TEXT, score REAL DEFAULT 0.0,
    tags TEXT DEFAULT '[]', namespace TEXT DEFAULT 'default',
    created_at TEXT DEFAULT (datetime('now','localtime'))
);
"""

class SQLiteClient:
    async def init(self):
        Path(DB).parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(DB) as db:
            # WAL 模式：支持并发读写，避免写入阻塞
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA synchronous=NORMAL")
            await db.execute("PRAGMA cache_size=-64000")  # 64MB cache
            await db.execute("PRAGMA foreign_keys=ON")
            await db.executescript(DDL)
            await db.commit()

    async def _fts_insert_triggers(self):
        """创建 FTS 同步触发器（幂等）"""
        triggers = """
        CREATE TRIGGER IF NOT EXISTS knowledge_fts_ins AFTER INSERT ON knowledge_base
        BEGIN
            INSERT INTO knowledge_fts(rowid, title, content, source, tags)
            VALUES (NEW.id, NEW.title, NEW.content, NEW.source, NEW.tags);
        END;
        CREATE TRIGGER IF NOT EXISTS knowledge_fts_upd AFTER UPDATE ON knowledge_base
        BEGIN
            UPDATE knowledge_fts SET title=NEW.title, content=NEW.content,
                source=NEW.source, tags=NEW.tags WHERE rowid=NEW.id;
        END;
        CREATE TRIGGER IF NOT EXISTS knowledge_fts_del AFTER DELETE ON knowledge_base
        BEGIN
            DELETE FROM knowledge_fts WHERE rowid=OLD.id;
        END;
        """
        async with aiosqlite.connect(DB) as db:
            await db.executescript(triggers)
            await db.commit()

    async def log_event(self, event, data=None, source="system"):
        async with aiosqlite.connect(DB) as db:
            await db.execute("INSERT INTO events(event,data,source) VALUES(?,?,?)",
                             (event, json.dumps(data or {}), source))
            await db.commit()

    async def log_decision(self, action, roi, confidence, input_summary, output_json=None):
        async with aiosqlite.connect(DB) as db:
            await db.execute(
                "INSERT INTO decisions(action,roi,confidence,input_summary,output_json) VALUES(?,?,?,?,?)",
                (action, roi, confidence, input_summary, json.dumps(output_json or {})))
            await db.commit()

    async def log_deal(self, user_id, amount, stage, package=None, source=None):
        async with aiosqlite.connect(DB) as db:
            await db.execute(
                "INSERT INTO deals(user_id,amount,stage,package,source) VALUES(?,?,?,?,?)",
                (user_id, amount, stage, package, source))
            await db.commit()

    async def get_daily_summary(self):
        today = date.today().isoformat()
        async with aiosqlite.connect(DB) as db:
            cur = await db.execute(
                "SELECT COUNT(*) FROM deals WHERE stage='lead' AND DATE(created_at)=?", (today,))
            leads = (await cur.fetchone())[0]
            cur = await db.execute(
                "SELECT COUNT(*),COALESCE(SUM(amount),0) FROM deals WHERE stage='closed' AND DATE(created_at)=?", (today,))
            cnt, rev = await cur.fetchone()
            cur = await db.execute(
                "SELECT COALESCE(SUM(cost),0) FROM model_logs WHERE DATE(created_at)=?", (today,))
            api_cost = (await cur.fetchone())[0]
            cur = await db.execute(
                "SELECT model, COUNT(*), COALESCE(SUM(cost),0) FROM model_logs WHERE DATE(created_at)=? GROUP BY model",
                (today,),
            )
            model_usage = [
                {"model": row[0], "calls": row[1], "cost": row[2]}
                for row in await cur.fetchall()
            ]
            cur = await db.execute(
                """
                SELECT
                    COALESCE(AVG(daily_leads), 0),
                    COALESCE(AVG(daily_deals), 0),
                    COALESCE(AVG(daily_revenue), 0),
                    COALESCE(AVG(daily_api_cost), 0)
                FROM (
                    SELECT
                        DATE(created_at) AS day,
                        SUM(CASE WHEN stage='lead' THEN 1 ELSE 0 END) AS daily_leads,
                        SUM(CASE WHEN stage='closed' THEN 1 ELSE 0 END) AS daily_deals,
                        SUM(CASE WHEN stage='closed' THEN amount ELSE 0 END) AS daily_revenue,
                        0 AS daily_api_cost
                    FROM deals
                    WHERE DATE(created_at) >= DATE('now', '-7 day')
                    GROUP BY DATE(created_at)
                )
                """
            )
            avg_leads, avg_deals, avg_revenue, _ = await cur.fetchone()
            cur = await db.execute(
                """
                SELECT COALESCE(AVG(daily_api_cost), 0)
                FROM (
                    SELECT DATE(created_at) AS day, SUM(cost) AS daily_api_cost
                    FROM model_logs
                    WHERE DATE(created_at) >= DATE('now', '-7 day')
                    GROUP BY DATE(created_at)
                )
                """
            )
            avg_api_cost = (await cur.fetchone())[0]
        cvr = cnt / leads if leads > 0 else 0
        roi = rev / api_cost if api_cost > 0 else 0
        return {"date": today, "leads": leads, "deals": cnt, "total_revenue": rev,
                "api_cost": api_cost, "cvr": cvr, "roi": roi,
                "api_cost_rate": api_cost / rev if rev > 0 else 0,
                "model_usage": model_usage,
                "prev_7day_avg": {
                    "leads": avg_leads,
                    "deals": avg_deals,
                    "total_revenue": avg_revenue,
                    "api_cost": avg_api_cost,
                }}

    # ── 知识管理（FTS5 全文搜索）──

    async def add_knowledge(self, title: str, content: str, source: str = "system", tags: list = None):
        """添加知识条目，自动同步到 FTS 索引"""
        tags_json = json.dumps(tags or [])
        async with aiosqlite.connect(DB) as db:
            await db.execute(
                "INSERT INTO knowledge_base(title, content, source, tags) VALUES(?,?,?,?)",
                (title, content, source, tags_json))
            await db.commit()

    async def search_knowledge(self, query: str, limit: int = 10) -> list[dict]:
        """FTS5 全文搜索知识"""
        async with aiosqlite.connect(DB) as db:
            async with db.execute(
                "SELECT kb.id, kb.title, kb.content, kb.source, kb.tags, kb.created_at, "
                "rank FROM knowledge_fts fts "
                "JOIN knowledge_base kb ON kb.id = fts.rowid "
                "WHERE knowledge_fts MATCH ? "
                "ORDER BY rank LIMIT ?",
                (query, limit),
            ) as cur:
                rows = await cur.fetchall()
                return [
                    {"id": r[0], "title": r[1], "content": r[2], "source": r[3],
                     "tags": json.loads(r[4]), "created_at": r[5], "rank": r[6]}
                    for r in rows
                ]

    async def get_knowledge(self, knowledge_id: int) -> dict | None:
        """按 ID 获取知识条目"""
        async with aiosqlite.connect(DB) as db:
            async with db.execute(
                "SELECT id, title, content, source, tags, created_at, updated_at "
                "FROM knowledge_base WHERE id = ?",
                (knowledge_id,)
            ) as cur:
                row = await cur.fetchone()
                if row is None:
                    return None
                return {
                    "id": row[0], "title": row[1], "content": row[2], "source": row[3],
                    "tags": json.loads(row[4]), "created_at": row[5], "updated_at": row[6]
                }

    async def update_knowledge(self, knowledge_id: int, title: str = None, content: str = None):
        """更新知识条目"""
        fields, values = [], []
        if title is not None:
            fields.append("title = ?")
            values.append(title)
        if content is not None:
            fields.append("content = ?")
            values.append(content)
        fields.append("updated_at = datetime('now','localtime')")
        values.append(knowledge_id)
        async with aiosqlite.connect(DB) as db:
            await db.execute(
                f"UPDATE knowledge_base SET {', '.join(fields)} WHERE id = ?",
                tuple(values))
            await db.commit()

    async def delete_knowledge(self, knowledge_id: int) -> bool:
        """删除知识条目"""
        async with aiosqlite.connect(DB) as db:
            cur = await db.execute("DELETE FROM knowledge_base WHERE id = ?", (knowledge_id,))
            await db.commit()
            return cur.rowcount > 0

    # ── Namespace 隔离方法 ──

    async def store_memory(self, key: str, data: dict, scenario: str, namespace: str = "global",
                           importance_score: float = 1.0):
        """存储到 memory 表，按 namespace 隔离，带重要性评分"""
        async with aiosqlite.connect(DB) as db:
            await db.execute(
                "INSERT INTO memory(memory_key, data, scenario, namespace, importance_score, metadata) VALUES(?,?,?,?,?,?)",
                (key, json.dumps(data), scenario, namespace, importance_score, json.dumps({})))
            await db.commit()

    async def retrieve_memory(self, key: str = None, scenario: str = None, namespace: str = "global",
                              limit: int = 20, decay_lambda: float = 0.05) -> list[dict]:
        """从 memory 表检索，按 namespace 隔离 + 重要性衰减排序

        Args:
            decay_lambda: 每日衰减系数（默认 0.05 = 5%/天）
        """
        conditions, values = ["namespace = ?"], [namespace]
        if key:
            conditions.append("memory_key LIKE ?")
            values.append(f"%{key}%")
        if scenario:
            conditions.append("scenario = ?")
            values.append(scenario)
        where = " AND ".join(conditions)
        async with aiosqlite.connect(DB) as db:
            async with db.execute(
                "SELECT id, memory_key, data, scenario, namespace, created_at, importance_score "
                f"FROM memory WHERE {where} ORDER BY id DESC LIMIT ?",
                (*values, limit * 3)  # 取更多数据以便衰减过滤后有足够结果
            ) as cur:
                rows = await cur.fetchall()
                results = []
                for r in rows:
                    try:
                        d = json.loads(r[2]) if r[2] else {}
                    except (json.JSONDecodeError, TypeError):
                        d = {"raw": r[2]}
                    # 计算衰减分数: score * exp(-λ * days)
                    base_score = r[6] if len(r) > 6 else 1.0
                    days_old = _days_since(r[5])
                    import math
                    decayed_score = base_score * math.exp(-decay_lambda * days_old)
                    results.append({
                        "id": r[0], "key": r[1], "data": d,
                        "scenario": r[3], "namespace": r[4], "created_at": r[5],
                        "importance_score": base_score,
                        "decayed_score": round(decayed_score, 4),
                    })
                # 按衰减分数排序，过滤低于阈值的条目
                results.sort(key=lambda x: x["decayed_score"], reverse=True)
                # 过滤：衰减分数 < 0.1 的条目视为已归档
                results = [r for r in results if r["decayed_score"] >= 0.1]
                return results[:limit]

    async def search_knowledge_by_namespace(self, query: str, namespace: str = "global",
                                            limit: int = 10) -> list[dict]:
        """FTS5 全文搜索 + namespace 过滤（中文回退 LIKE）"""
        import re
        has_cjk = bool(re.search(r'[一-鿿]', query))

        if has_cjk:
            # FTS5 unicode61 不拆分中文，回退到 LIKE 搜索
            pattern = f"%{query}%"
            async with aiosqlite.connect(DB) as db:
                async with db.execute(
                    "SELECT id, title, content, source, tags, namespace, created_at "
                    "FROM knowledge_base "
                    "WHERE namespace = ? AND (title LIKE ? OR content LIKE ?) "
                    "ORDER BY id DESC LIMIT ?",
                    (namespace, pattern, pattern, limit)
                ) as cur:
                    rows = await cur.fetchall()
                    return [
                        {"id": r[0], "title": r[1], "content": r[2], "source": r[3],
                         "tags": json.loads(r[4]), "namespace": r[5], "created_at": r[6], "rank": 0}
                        for r in rows
                    ]
        else:
            # FTS5 英文全文搜索
            async with aiosqlite.connect(DB) as db:
                async with db.execute(
                    "SELECT kb.id, kb.title, kb.content, kb.source, kb.tags, kb.namespace, kb.created_at, "
                    "rank FROM knowledge_fts fts "
                    "JOIN knowledge_base kb ON kb.id = fts.rowid "
                    "WHERE knowledge_fts MATCH ? AND kb.namespace = ? "
                    "ORDER BY rank LIMIT ?",
                    (query, namespace, limit)
                ) as cur:
                    rows = await cur.fetchall()
                    return [
                        {"id": r[0], "title": r[1], "content": r[2], "source": r[3],
                         "tags": json.loads(r[4]), "namespace": r[5], "created_at": r[6], "rank": r[7]}
                        for r in rows
                    ]

    async def add_knowledge_with_namespace(self, title: str, content: str,
                                           namespace: str = "global",
                                           source: str = "system", tags: list = None):
        """添加知识条目，带 namespace"""
        tags_json = json.dumps(tags or [])
        async with aiosqlite.connect(DB) as db:
            await db.execute(
                "INSERT INTO knowledge_base(title, content, source, tags, namespace) VALUES(?,?,?,?,?)",
                (title, content, source, tags_json, namespace))
            await db.commit()

    # ── 审批管理 ──

    async def add_pending_approval(self, approval_id: str, title: str, description: str = "",
                                    task_type: str = "", agency_id: str = "",
                                    decision_data: dict = None, namespace: str = "global",
                                    instance_code: str = ""):
        async with aiosqlite.connect(DB) as db:
            await db.execute(
                "INSERT INTO pending_approvals(approval_id, title, description, task_type, agency_id, decision_data, namespace, instance_code) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (approval_id, title, description, task_type, agency_id, json.dumps(decision_data or {}), namespace, instance_code))
            await db.commit()

    async def update_approval_instance_code(self, approval_id: str, instance_code: str):
        async with aiosqlite.connect(DB) as db:
            await db.execute(
                "UPDATE pending_approvals SET instance_code = ? WHERE approval_id = ?",
                (instance_code, approval_id))
            await db.commit()

    async def get_pending_approvals(self, status: str = "pending", limit: int = 50) -> list[dict]:
        async with aiosqlite.connect(DB) as db:
            async with db.execute(
                "SELECT id, approval_id, title, description, task_type, agency_id, "
                "decision_data, status, reviewer_comment, created_at, reviewed_at "
                "FROM pending_approvals WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status, limit)
            ) as cur:
                rows = await cur.fetchall()
                return [
                    {
                        "id": r[0], "approval_id": r[1], "title": r[2], "description": r[3],
                        "task_type": r[4], "agency_id": r[5],
                        "decision_data": json.loads(r[6]), "status": r[7],
                        "reviewer_comment": r[8], "created_at": r[9], "reviewed_at": r[10],
                    }
                    for r in rows
                ]

    async def approve(self, approval_id: str, comment: str = "") -> bool:
        async with aiosqlite.connect(DB) as db:
            await db.execute(
                "UPDATE pending_approvals SET status = 'approved', reviewer_comment = ?, "
                "reviewed_at = datetime('now','localtime') WHERE approval_id = ?",
                (comment, approval_id))
            await db.commit()
            return True

    async def reject(self, approval_id: str, comment: str = "") -> bool:
        async with aiosqlite.connect(DB) as db:
            await db.execute(
                "UPDATE pending_approvals SET status = 'rejected', reviewer_comment = ?, "
                "reviewed_at = datetime('now','localtime') WHERE approval_id = ?",
                (comment, approval_id))
            await db.commit()
            return True

    # ── 广告指标（AdsAgency 真实数据读取）──

    async def get_ads_metrics(self, days: int = 1) -> list[dict]:
        """从 ads_metrics 表读取最近 N 天的广告指标"""
        async with aiosqlite.connect(DB) as db:
            async with db.execute(
                "SELECT date, spend_cny, leads, m0, m1, m2, cac_cny, roi, ctr, cvr "
                "FROM ads_metrics ORDER BY date DESC LIMIT ?",
                (days,)
            ) as cur:
                rows = await cur.fetchall()
                return [
                    {
                        "date": r[0], "spend_cny": r[1], "leads": r[2],
                        "m0": r[3], "m1": r[4], "m2": r[5],
                        "cac_cny": r[6], "roi": r[7], "ctr": r[8], "cvr": r[9],
                    }
                    for r in rows
                ]

    async def save_ads_metrics(self, date: str, spend_cny: float, leads: int,
                                m0: int = 0, m1: int = 0, m2: int = 0,
                                cac_cny: float = 0.0, roi: float = 0.0,
                                ctr: float = 0.0, cvr: float = 0.0) -> None:
        """保存广告指标到 ads_metrics 表（幂等：同日期覆盖）"""
        async with aiosqlite.connect(DB) as db:
            await db.execute(
                "INSERT INTO ads_metrics(date, spend_cny, leads, m0, m1, m2, cac_cny, roi, ctr, cvr) "
                "VALUES(?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(date) DO UPDATE SET "
                "spend_cny=excluded.spend_cny, leads=excluded.leads, "
                "m0=excluded.m0, m1=excluded.m1, m2=excluded.m2, "
                "cac_cny=excluded.cac_cny, roi=excluded.roi, ctr=excluded.ctr, cvr=excluded.cvr",
                (date, spend_cny, leads, m0, m1, m2, cac_cny, roi, ctr, cvr))
            await db.commit()

    def add_evolution_knowledge(self, card_id: str, title: str, content: str = "",
                                 source_task: str = "", outcome: str = "",
                                 score: float = 0.0, tags: str = "[]",
                                 namespace: str = "default") -> None:
        """写入进化引擎知识卡片（同步，供 EvolutionEngine 调用）"""
        import sqlite3
        with sqlite3.connect(DB) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO evolution_knowledge(card_id, title, content, source_task, outcome, score, tags, namespace) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (card_id, title, content, source_task, outcome, score, tags, namespace))
            conn.commit()

    def search_evolution_knowledge(self, query: str, limit: int = 5) -> list:
        """语义/关键词检索历史知识卡片"""
        import sqlite3
        with sqlite3.connect(DB) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                "SELECT card_id, title, content, score, tags, outcome FROM evolution_knowledge "
                "WHERE title LIKE ? OR content LIKE ? ORDER BY score DESC LIMIT ?",
                (f"%{query}%", f"%{query}%", limit))
            return [dict(r) for r in cur.fetchall()]
