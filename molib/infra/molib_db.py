"""
MolibDB — 统一轻量后端（PocketBase 纯 Python 替代）
==================================================
对标 PocketBase (54K★): SQLite · 实时订阅 · 文件管理 · 用户认证
Mac M2: <10MB 内存，零外部依赖，单 SQLite 文件。

用法:
    python -m molib db serve --port 8090        # 启动 API 服务
    python -m molib db collection list            # 列出集合
    python -m molib db collection create --name orders --schema '{"title":"text","amount":"number"}'
    python -m molib db record create --collection orders --data '{"title":"测试","amount":99}'
    python -m molib db record list --collection orders
    python -m molib db auth create --email a@b.com --password xxx
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("molib.db")

DB_PATH = Path.home() / ".hermes" / "molib.db"


@dataclass
class Collection:
    name: str
    schema: dict[str, str]  # {field_name: field_type}
    created_at: str = ""

    FIELD_TYPES = {
        "text": "TEXT",
        "number": "REAL",
        "integer": "INTEGER",
        "boolean": "INTEGER",  # SQLite 无 bool
        "datetime": "TEXT",
        "json": "TEXT",
    }


class MolibDB:
    """统一轻量后端数据库。"""

    def __init__(self, db_path: str = ""):
        self.db_path = db_path or str(DB_PATH)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_system()

    def _init_system(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS _collections (
                    name TEXT PRIMARY KEY,
                    schema_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS _auth (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    token TEXT,
                    role TEXT DEFAULT 'user',
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS _subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    collection_name TEXT NOT NULL,
                    event TEXT NOT NULL,  -- create/update/delete
                    callback_url TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.commit()

    # ── Collection CRUD ──────────────────────────────────────

    def create_collection(self, name: str, schema: dict[str, str]) -> dict:
        """创建集合（即 SQLite 表）。"""
        if not name.isidentifier():
            return {"error": "集合名必须是有效标识符"}

        schema_json = json.dumps(schema, ensure_ascii=False)

        with sqlite3.connect(self.db_path) as conn:
            # 注册集合元数据
            try:
                conn.execute(
                    "INSERT INTO _collections (name, schema_json) VALUES (?, ?)",
                    (name, schema_json),
                )
            except sqlite3.IntegrityError:
                return {"error": f"集合 '{name}' 已存在"}

            # 创建数据表
            cols = ["id INTEGER PRIMARY KEY AUTOINCREMENT",
                    "created_at TEXT DEFAULT (datetime('now'))",
                    "updated_at TEXT DEFAULT (datetime('now'))"]
            for fname, ftype in schema.items():
                sql_type = Collection.FIELD_TYPES.get(ftype, "TEXT")
                cols.append(f"{fname} {sql_type}")

            conn.execute(f"CREATE TABLE IF NOT EXISTS {name} ({', '.join(cols)})")
            conn.commit()

        logger.info(f"集合创建: {name} ({len(schema)} 字段)")
        return {"name": name, "schema": schema, "status": "created"}

    def list_collections(self) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT name, schema_json, created_at FROM _collections").fetchall()
        return [{"name": r[0], "schema": json.loads(r[1]), "created_at": r[2]} for r in rows]

    # ── Record CRUD ──────────────────────────────────────────

    def create_record(self, collection: str, data: dict[str, Any]) -> dict:
        """插入记录。"""
        with sqlite3.connect(self.db_path) as conn:
            # 获取 schema
            schema_row = conn.execute(
                "SELECT schema_json FROM _collections WHERE name=?", (collection,)
            ).fetchone()
            if not schema_row:
                return {"error": f"集合 '{collection}' 不存在"}

            schema = json.loads(schema_row[0])
            # 只取 schema 中定义的字段
            fields = {k: data.get(k) for k in schema if k in data}
            if not fields:
                return {"error": "无有效字段"}

            keys = list(fields.keys())
            values = list(fields.values())
            placeholders = ",".join("?" * len(keys))

            cursor = conn.execute(
                f"INSERT INTO {collection} ({','.join(keys)}) VALUES ({placeholders})",
                values,
            )
            conn.commit()
            record_id = cursor.lastrowid

        return {"id": record_id, **fields, "status": "created"}

    def list_records(self, collection: str, limit: int = 50, offset: int = 0) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"SELECT * FROM {collection} ORDER BY id DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return [dict(r) for r in rows]

    def update_record(self, collection: str, record_id: int, data: dict) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            set_clause = ", ".join(f"{k}=?" for k in data)
            values = list(data.values()) + [record_id]
            conn.execute(
                f"UPDATE {collection} SET {set_clause}, updated_at=datetime('now') WHERE id=?",
                values,
            )
            conn.commit()
        return {"id": record_id, "status": "updated"}

    def delete_record(self, collection: str, record_id: int) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"DELETE FROM {collection} WHERE id=?", (record_id,))
            conn.commit()
        return {"id": record_id, "status": "deleted"}

    # ── Auth ─────────────────────────────────────────────────

    def create_user(self, email: str, password: str, role: str = "user") -> dict:
        salt = secrets.token_hex(16)
        pw_hash = hashlib.sha256(f"{password}:{salt}".encode()).hexdigest()

        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    "INSERT INTO _auth (email, password_hash, role) VALUES (?, ?, ?)",
                    (email, f"{salt}:{pw_hash}", role),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                return {"error": "邮箱已存在"}
        return {"email": email, "role": role, "status": "created"}

    def authenticate(self, email: str, password: str) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT id, email, password_hash, role FROM _auth WHERE email=?",
                (email,),
            ).fetchone()

        if not row:
            return {"error": "用户不存在"}

        stored = row[2]
        if ":" not in stored:
            return {"error": "密码格式错误"}

        salt, pw_hash = stored.split(":", 1)
        computed = hashlib.sha256(f"{password}:{salt}".encode()).hexdigest()

        if computed != pw_hash:
            return {"error": "密码错误"}

        token = secrets.token_hex(32)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE _auth SET token=? WHERE id=?", (token, row[0]))
            conn.commit()

        return {"email": row[1], "role": row[3], "token": token, "status": "authenticated"}

    # ── Realtime (Polling) ───────────────────────────────────

    def subscribe(self, collection: str, event: str, callback_url: str = "") -> dict:
        """订阅集合变更事件。"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO _subscriptions (collection_name, event, callback_url) VALUES (?,?,?)",
                (collection, event, callback_url),
            )
            conn.commit()
        return {"collection": collection, "event": event, "status": "subscribed"}

    def get_changes(self, collection: str, since_id: int = 0) -> list[dict]:
        """获取 since_id 之后的变更记录（轮询模式）。"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"SELECT * FROM {collection} WHERE id > ? ORDER BY id", (since_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Stats ────────────────────────────────────────────────

    def stats(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            collections = conn.execute("SELECT COUNT(*) FROM _collections").fetchone()[0]
            users = conn.execute("SELECT COUNT(*) FROM _auth").fetchone()[0]
            # 计算总记录数
            total_records = 0
            col_rows = conn.execute("SELECT name FROM _collections").fetchall()
            for (name,) in col_rows:
                count = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
                total_records += count

        db_size = os.path.getsize(self.db_path) / 1024 if os.path.exists(self.db_path) else 0

        return {
            "collections": collections,
            "total_records": total_records,
            "users": users,
            "db_size_kb": round(db_size, 1),
            "db_path": self.db_path,
        }


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def cmd_db_collection(args: list[str]) -> dict:
    db = MolibDB()
    if not args:
        return {"collections": db.list_collections()}

    subcmd = args[0]
    if subcmd == "list":
        return {"collections": db.list_collections()}
    elif subcmd == "create":
        name, schema_json = "", "{}"
        i = 1
        while i < len(args):
            if args[i] == "--name" and i + 1 < len(args):
                name = args[i + 1]; i += 2
            elif args[i] == "--schema" and i + 1 < len(args):
                schema_json = args[i + 1]; i += 2
            else:
                i += 1
        schema = json.loads(schema_json) if schema_json else {}
        return db.create_collection(name, schema) if name else {"error": "需要 --name"}

    return {"error": f"未知子命令: {subcmd}"}


def cmd_db_record(args: list[str]) -> dict:
    db = MolibDB()
    if not args:
        return {"error": "子命令: create | list | update | delete"}

    subcmd = args[0]
    rest = args[1:]

    collection = ""
    data = {}
    record_id = 0
    i = 0
    while i < len(rest):
        if rest[i] == "--collection" and i + 1 < len(rest):
            collection = rest[i + 1]; i += 2
        elif rest[i] == "--data" and i + 1 < len(rest):
            data = json.loads(rest[i + 1]); i += 2
        elif rest[i] == "--id" and i + 1 < len(rest):
            record_id = int(rest[i + 1]); i += 2
        else:
            i += 1

    if not collection:
        return {"error": "需要 --collection"}

    if subcmd == "create":
        return db.create_record(collection, data)
    elif subcmd == "list":
        return {"records": db.list_records(collection)}
    elif subcmd == "update":
        return db.update_record(collection, record_id, data) if record_id else {"error": "需要 --id"}
    elif subcmd == "delete":
        return db.delete_record(collection, record_id) if record_id else {"error": "需要 --id"}

    return {"error": f"未知子命令: {subcmd}"}


def cmd_db_auth(args: list[str]) -> dict:
    db = MolibDB()
    if not args:
        return {"error": "子命令: create | login"}

    subcmd = args[0]
    rest = args[1:]

    email, password = "", ""
    i = 0
    while i < len(rest):
        if rest[i] == "--email" and i + 1 < len(rest):
            email = rest[i + 1]; i += 2
        elif rest[i] == "--password" and i + 1 < len(rest):
            password = rest[i + 1]; i += 2
        else:
            i += 1

    if subcmd == "create":
        return db.create_user(email, password) if email else {"error": "需要 --email"}
    elif subcmd == "login":
        return db.authenticate(email, password) if email else {"error": "需要 --email"}

    return {"error": f"未知子命令: {subcmd}"}


def cmd_db_stats() -> dict:
    return MolibDB().stats()
