#!/usr/bin/env python3
"""
墨麟记忆系统 — molin-memory
子公司级向量RAG引擎 + SQLite 结构化存储

基于 ChromaDB（按子公司设独立 collection）+ SQLite（结构化数据）
轻量级设计，M1 Air 8GB 友好

用法:
  python3 molin_memory.py init          # 初始化系统
  python3 molin_memory.py store <子公司名> <内容> [元数据JSON]  # 存入记忆
  python3 molin_memory.py recall <子公司名> <查询> [top_k]     # 检索记忆
  python3 molin_memory.py stats                                # 系统状态
  python3 molin_memory.py import-skills <skills目录>           # 批量导入 skill
  python3 molin_memory.py context <子公司名> <任务描述>         # 生成带记忆的上下文
"""

import sys
import json
import pathlib
import hashlib
import datetime
import sqlite3
import numpy as np
from typing import Optional

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None

# ── 配置 ──
MEMORY_DIR = pathlib.Path.home() / ".molin-memory"
VECTOR_DIR = MEMORY_DIR / "vectors"
DB_PATH = MEMORY_DIR / "state.db"
SKILLS_SOURCES = MEMORY_DIR / "skill_sources.json"

# 22 家子公司清单（标准名称）
SUBSIDIARY_PAIRS = [
    ("墨智", "mozhi"), ("墨码", "moma"), ("墨商BD", "moshang_bd"), ("墨影", "moying"),
    ("墨增", "mozeng"), ("墨声", "mosheng"), ("墨域", "moyu"), ("墨单", "modan"),
    ("墨算", "mosuan"), ("墨思", "mosi"), ("墨律", "molv"), ("墨盾", "modun"),
    ("墨品", "mopin"), ("墨数", "moshu"), ("墨维", "mowei"), ("墨育", "moyu_edu"),
    ("墨海", "mohai"), ("墨脑", "monao"), ("墨迹", "moji"), ("墨投", "motou"),
    ("墨商销售", "moshang_sale"), ("墨工", "mogong"),
]
SUBSIDIARIES = [p[0] for p in SUBSIDIARY_PAIRS]
SUBSIDIARY_NAMES_MAP = {p[0]: p[1] for p in SUBSIDIARY_PAIRS}

# 子公司英文别名映射（方便 skill 名匹配）
ALIAS_MAP = {
    "molin-legal": "墨律", "molin-trading": "墨投",
    "molin-trading-agents": "墨投", "molin-xiaohongshu": "墨影",
    "molin-vizro": "墨数", "molin-customer-service": "墨声",
    "molin-global": "墨海", "xianyu": "墨商销售",
    "xiaohongshu": "墨影", "content": "墨迹",
    "research": "墨思", "trend": "墨思",
}


def get_subsidiary(name: str) -> str:
    """将各种别名映射到标准子公司名"""
    if name in SUBSIDIARIES:
        return name
    return ALIAS_MAP.get(name, name)


def get_client():
    """获取 ChromaDB 客户端（持久化模式）"""
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(VECTOR_DIR),
        settings=Settings(anonymized_telemetry=False, allow_reset=False)
    )


def get_db() -> sqlite3.Connection:
    """获取 SQLite 连接"""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection):
    """初始化 SQLite 表结构"""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            subsidiary TEXT NOT NULL,
            action TEXT,
            summary TEXT,
            cost REAL DEFAULT 0,
            level TEXT DEFAULT 'L0',
            outcome TEXT DEFAULT 'completed',
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            source TEXT NOT NULL,
            target TEXT,
            event_type TEXT NOT NULL,
            payload TEXT,
            processed INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT UNIQUE,
            subsidiary TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            result TEXT,
            milestones TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            completed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            subsidiary TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL,
            UNIQUE(date, subsidiary, metric_name)
        );
        CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
        CREATE INDEX IF NOT EXISTS idx_decisions_subsidiary ON decisions(subsidiary);
        CREATE INDEX IF NOT EXISTS idx_tasks_subsidiary ON tasks(subsidiary);
    """)
    conn.commit()


def init_collections(client: chromadb.ClientAPI):
    """为所有子公司创建 ChromaDB collection"""
    for cn, en in SUBSIDIARY_PAIRS:
        try:
            client.get_or_create_collection(
                name=f"molin_{en}",
                metadata={"hnsw:space": "cosine", "subsidiary": cn, "en_name": en}
            )
        except Exception as e:
            print(f"  ⚠  {cn}: {e}")


# ── 核心操作 ──

def store_memory(subsidiary: str, content: str, metadata: Optional[dict] = None):
    """存入一条子公司记忆（向量 + 结构化双写）"""
    sub = get_subsidiary(subsidiary)
    meta = metadata or {}

    # 1. 存入 ChromaDB
    client = get_client()
    sub_en = SUBSIDIARY_NAMES_MAP.get(sub, sub)
    collection = client.get_collection(f"molin_{sub_en}")
    doc_id = hashlib.sha256(f"{sub}_{content}_{datetime.datetime.now().isoformat()}".encode()).hexdigest()[:24]

    chroma_meta = {
        "subsidiary": sub,
        "content_type": meta.get("type", "general"),
        "source": meta.get("source", "hermes"),
        "created_at": datetime.datetime.now().isoformat(),
    }
    if "tags" in meta:
        chroma_meta["tags"] = json.dumps(meta["tags"], ensure_ascii=False)

    collection.upsert(
        ids=[doc_id],
        documents=[content],
        metadatas=[chroma_meta]
    )

    # 2. 存入 SQLite（结构化摘要）
    conn = get_db()
    conn.execute(
        "INSERT INTO decisions (timestamp, subsidiary, action, summary, cost, level) VALUES (?, ?, ?, ?, ?, ?)",
        (datetime.datetime.now().isoformat(), sub, meta.get("action", "store"), content[:200], meta.get("cost", 0), meta.get("level", "L0"))
    )
    conn.commit()

    return {"id": doc_id, "subsidiary": sub, "length": len(content)}


def recall_memory(subsidiary: str, query: str, top_k: int = 5) -> list:
    """检索子公司记忆（语义搜索）"""
    sub = get_subsidiary(subsidiary)

    client = get_client()
    try:
        sub_en = SUBSIDIARY_NAMES_MAP.get(sub, sub)
        collection = client.get_collection(f"molin_{sub_en}")
    except ValueError:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, 20),
    )

    if not results["documents"] or not results["documents"][0]:
        return []

    memories = []
    for i, doc in enumerate(results["documents"][0]):
        dist = results["distances"][0][i] if results["distances"] else 1.0
        meta = results["metadatas"][0][i] if results["metadatas"] else {}
        memories.append({
            "content": doc[:500],
            "similarity": round(1.0 - dist, 4),
            "distance": round(dist, 4),
            "metadata": meta,
        })

    # 按相似度排序
    memories.sort(key=lambda x: x["similarity"], reverse=True)
    return memories


def build_context(subsidiary: str, task: str, top_k: int = 5) -> str:
    """为子公司组装带记忆的上下文——用于注入 Agent System Prompt"""
    memories = recall_memory(subsidiary, task, top_k)

    if not memories:
        return ""

    lines = ["## 📚 相关历史经验（记忆检索）\n"]
    for i, m in enumerate(memories, 1):
        sim_pct = int(m["similarity"] * 100)
        lines.append(f"### {i}. [{sim_pct}%匹配] {m['content']}")
        if m["metadata"].get("tags"):
            lines.append(f"  标签: {m['metadata']['tags']}")

    return "\n".join(lines)


def log_event(source: str, event_type: str, payload: dict, target: Optional[str] = None):
    """记录跨子公司事件"""
    conn = get_db()
    conn.execute(
        "INSERT INTO events (timestamp, source, target, event_type, payload) VALUES (?, ?, ?, ?, ?)",
        (datetime.datetime.now().isoformat(), source, target, event_type, json.dumps(payload, ensure_ascii=False))
    )
    conn.commit()


def get_unprocessed_events(source: Optional[str] = None) -> list:
    """获取未处理的事件"""
    conn = get_db()
    if source:
        rows = conn.execute("SELECT * FROM events WHERE processed=0 AND source=? ORDER BY timestamp", (source,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM events WHERE processed=0 ORDER BY timestamp").fetchall()

    events = []
    for r in rows:
        ev = dict(r)
        ev["payload"] = json.loads(ev["payload"])
        events.append(ev)
    return events


def mark_event_processed(event_id: int):
    """标记事件已处理"""
    conn = get_db()
    conn.execute("UPDATE events SET processed=1 WHERE id=?", (event_id,))
    conn.commit()


def get_stats() -> dict:
    """获取系统统计"""
    client = get_client()
    collections = client.list_collections()
    vector_stats = {}
    for c in collections:
        try:
            count = c.count()
            sub = c.metadata.get("subsidiary", c.name.replace("molin_", ""))
            vector_stats[sub] = count
        except:
            pass

    conn = get_db()
    decision_count = conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
    event_count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    unprocessed = conn.execute("SELECT COUNT(*) FROM events WHERE processed=0").fetchone()[0]
    task_count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    metric_count = conn.execute("SELECT COUNT(*) FROM metrics").fetchone()[0]

    return {
        "vector_db": {"type": "ChromaDB", "location": str(VECTOR_DIR), "collections": len(vector_stats), "drawers": vector_stats},
        "sqlite": {"location": str(DB_PATH), "decisions": decision_count, "events": event_count, "unprocessed_events": unprocessed, "tasks": task_count, "metrics": metric_count},
        "storage_mb": {"vectors": sum(f.stat().st_size for f in VECTOR_DIR.rglob("*") if f.is_file()) / 1024 / 1024 if VECTOR_DIR.exists() else 0,
                       "sqlite": DB_PATH.stat().st_size / 1024 / 1024 if DB_PATH.exists() else 0},
    }


# ── 批量导入 skills → 向量库 ──

def import_skills_to_vector(skills_dir: str):
    """读取所有 SKILL.md 文件，按 molin_owner 分配到对应子公司向量库"""
    import re
    base = pathlib.Path(skills_dir).expanduser()
    if not base.exists():
        print(f"❌ 目录不存在: {base}")
        return

    skill_files = list(base.rglob("SKILL.md"))
    total = len(skill_files)
    imported = 0
    errors = 0

    for sf in skill_files:
        try:
            content = sf.read_text(encoding="utf-8")
            # 提取名称和描述
            name = sf.parent.name
            desc = ""
            owner = ""

            # 解析 YAML frontmatter
            fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
            if fm_match:
                fm_text = fm_match.group(1)
                for line in fm_text.split("\n"):
                    if line.startswith("name:"):
                        name = line.split(":", 1)[1].strip().strip('"\'')
                    elif line.startswith("molin_owner:"):
                        owner = line.split(":", 1)[1].strip().strip('"\'')
                    elif "molin_owner" in line:
                        # owner 可能在 metadata 深层
                        pass

            # 确定归属子公司
            sub = get_subsidiary(owner) if owner else "墨脑"

            # 提取前2000字符作为向量内容
            body = content
            if fm_match:
                body = content[fm_match.end():].strip()

            # 去除 markdown 标记，提取纯文本
            plain = re.sub(r"[#*`\[\]()>|:-]", " ", body)
            plain = re.sub(r"\s+", " ", plain).strip()

            if len(plain) < 50:
                continue

            metadata = {
                "type": "skill",
                "source": str(sf.relative_to(base.parent) if str(sf).startswith(str(base.parent)) else sf.name),
                "skill_name": name,
                "tags": [],
            }

            store_memory(sub, plain[:2000], metadata)
            imported += 1

        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"  ⚠  {sf.name}: {e}")

    print(f"✅ 导入完成: {imported}/{total} skills → 向量库 ({errors} 错误)")


# ── CLI 入口 ──

def main():
    args = sys.argv[1:]

    if not args:
        print("用法:")
        print("  python3 molin_memory.py init                          # 初始化")
        print("  python3 molin_memory.py store <子公司> <内容> [元数据JSON]  # 存入")
        print("  python3 molin_memory.py recall <子公司> <查询> [top_k] # 检索")
        print("  python3 molin_memory.py stats                        # 统计")
        print("  python3 molin_memory.py import-skills <目录>          # 批量导入")
        print("  python3 molin_memory.py context <子公司> <任务>        # 上下文")
        print("  python3 molin_memory.py event <来源> <类型> <负载JSON> # 记录事件")
        print("  python3 molin_memory.py events                       # 未处理事件")
        return

    cmd = args[0]

    if cmd == "init":
        print("🔧 初始化墨麟记忆系统...")
        conn = get_db()
        init_db(conn)
        client = get_client()
        init_collections(client)
        print(f"✅ 系统就绪")
        print(f"   ChromaDB: {VECTOR_DIR}")
        print(f"   SQLite:   {DB_PATH}")
        print(f"   子公司:   {len(SUBSIDIARIES)} 家 collections")
        stats = get_stats()
        print(f"   存储:     {stats['storage_mb']['sqlite']:.1f}MB (SQLite) + {stats['storage_mb']['vectors']:.1f}MB (向量)")

    elif cmd == "store":
        if len(args) < 3:
            print("❌ 用法: store <子公司> <内容> [元数据JSON]")
            return
        sub = args[1]
        content = args[2]
        meta = json.loads(args[3]) if len(args) > 3 else {}
        result = store_memory(sub, content, meta)
        print(f"✅ 已存入 {result['subsidiary']} (id={result['id']}, {result['length']}字符)")

    elif cmd == "recall":
        if len(args) < 3:
            print("❌ 用法: recall <子公司> <查询> [top_k]")
            return
        sub = args[1]
        query = args[2]
        top_k = int(args[3]) if len(args) > 3 else 5
        results = recall_memory(sub, query, top_k)
        if not results:
            print(f"📭 {sub} 无匹配记忆")
            return
        print(f"🔍 {sub} 检索到 {len(results)} 条记忆（查询: {query}）")
        print()
        for i, r in enumerate(results, 1):
            print(f"─── [{r['similarity']*100:.0f}%] #{i} ───")
            print(f"  {r['content'][:200]}...")
            if r['metadata'].get('tags'):
                print(f"  标签: {r['metadata']['tags']}")
            print()

    elif cmd == "stats":
        stats = get_stats()
        print("📊 墨麟记忆系统状态")
        print()
        vec = stats["vector_db"]
        print(f"向量库 (ChromaDB): {vec['collections']} collections")
        for sub, count in sorted(vec["drawers"].items(), key=lambda x: -x[1]):
            icon = "🟢" if count > 10 else ("🟡" if count > 0 else "⚪")
            print(f"  {icon} {sub}: {count} 条记忆")
        sq = stats["sqlite"]
        print()
        print(f"结构化存储 (SQLite):")
        print(f"  📝 决策: {sq['decisions']}")
        print(f"  📨 事件: {sq['events']} ({sq['unprocessed_events']} 未处理)")
        print(f"  ✅ 任务: {sq['tasks']}")
        print(f"  📊 指标: {sq['metrics']}")
        print(f"  存储: {stats['storage_mb']['sqlite']:.1f}MB / 向量 {stats['storage_mb']['vectors']:.1f}MB")

    elif cmd == "import-skills":
        if len(args) < 2:
            print("❌ 用法: import-skills <skills目录>")
            return
        import_skills_to_vector(args[1])

    elif cmd == "context":
        if len(args) < 3:
            print("❌ 用法: context <子公司> <任务描述>")
            return
        ctx = build_context(args[1], args[2])
        if ctx:
            print(ctx)
        else:
            print("(无相关历史记忆)")

    elif cmd == "event":
        if len(args) < 3:
            print("❌ 用法: event <来源> <类型> <负载JSON>")
            return
        payload = json.loads(args[3]) if len(args) > 3 else {}
        log_event(args[1], args[2], payload)
        print("✅ 事件已记录")

    elif cmd == "events":
        events = get_unprocessed_events()
        if not events:
            print("📭 无未处理事件")
            return
        for e in events:
            target_str = f" → {e['target']}" if e['target'] else ""
            print(f"  [{e['id']}] {e['source']}{target_str} | {e['event_type']} | {json.dumps(e['payload'], ensure_ascii=False)[:100]}")


if __name__ == "__main__":
    main()
