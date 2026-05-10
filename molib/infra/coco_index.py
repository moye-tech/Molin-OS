"""
CocoIndex — 本地文件监听 + SQLite 知识同步管道
==============================================
Mac M2 适配：无 Redis、无云端依赖、轮询 Windows/macOS 通用。
纯 stdlib：sqlite3 + pathlib + json + hashlib + mimetypes。

用法:
    python -m molib index watch --path /path/to/dir
    python -m molib index query --term "关键词"
    python -m molib index sync
    python -m molib index stats
"""

from __future__ import annotations

import hashlib
import json
import logging
import mimetypes
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("molin.coco_index")

DB_PATH = Path.home() / ".hermes" / "coco_index.db"
SCAN_INTERVAL = 60  # 秒


@dataclass
class IndexEntry:
    path: str
    content_hash: str
    mtime: float
    indexed_at: str
    file_type: str
    summary: str = ""  # 前200字摘要


class CocoIndex:
    """本地文件索引引擎。"""

    def __init__(self, db_path: str = ""):
        self.db_path = db_path or str(DB_PATH)
        self._watched: list[str] = []
        self._init_db()

    # ── DB ──────────────────────────────────────────────────

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    path TEXT PRIMARY KEY,
                    content_hash TEXT NOT NULL,
                    mtime REAL NOT NULL,
                    indexed_at TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    summary TEXT DEFAULT ''
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ftype ON files(file_type)")
            conn.commit()

    # ── Watch ───────────────────────────────────────────────

    def watch_directory(self, path: str):
        """注册监控目录。"""
        abs_path = str(Path(path).resolve())
        if abs_path not in self._watched:
            self._watched.append(abs_path)
            logger.info(f"CocoIndex watching: {abs_path}")

    # ── Index ───────────────────────────────────────────────

    def _extract_summary(self, filepath: str, content: str) -> str:
        ext = Path(filepath).suffix.lower()
        if ext == ".py":
            # 提取 docstring + 函数签名
            lines = []
            in_doc = False
            for line in content.split("\n")[:100]:
                stripped = line.strip()
                if stripped.startswith('def ') or stripped.startswith('class '):
                    lines.append(stripped.split("(")[0] + "(...)" if "(" in stripped else stripped)
                elif '"""' in stripped:
                    in_doc = not in_doc
                    lines.append(stripped)
                elif in_doc:
                    lines.append(stripped)
                elif not stripped or stripped.startswith("#"):
                    continue
                if len(lines) >= 10:
                    break
            return "\n".join(lines)[:500]
        elif ext in (".md", ".txt", ".rst"):
            return content[:200].replace("\n", " ")
        elif ext in (".json",):
            try:
                data = json.loads(content)
                keys = list(data.keys()) if isinstance(data, dict) else []
                return f"JSON: {len(keys)} keys — {', '.join(keys[:8])}"
            except json.JSONDecodeError:
                return content[:200]
        elif ext in (".yaml", ".yml", ".toml"):
            return content[:200].replace("\n", " ")
        else:
            return content[:200].replace("\n", " ") if self._is_text(filepath) else ""

    def _is_text(self, filepath: str) -> bool:
        mime, _ = mimetypes.guess_type(filepath)
        if mime and mime.startswith("text/"):
            return True
        ext = Path(filepath).suffix.lower()
        return ext in (".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".csv")

    def _get_file_type(self, filepath: str) -> str:
        ext = Path(filepath).suffix.lower()
        type_map = {
            ".py": "python",
            ".md": "markdown",
            ".txt": "text",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".csv": "csv",
            ".html": "html",
            ".css": "css",
            ".js": "javascript",
            ".ts": "typescript",
            ".sh": "shell",
        }
        return type_map.get(ext, ext.lstrip(".") if ext else "unknown")

    def index_file(self, filepath: str) -> Optional[IndexEntry]:
        """索引单个文件。"""
        path = str(Path(filepath).resolve())

        if not self._is_text(path):
            return None

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except (OSError, UnicodeDecodeError):
            return None

        mtime = os.path.getmtime(path)
        content_hash = hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()

        # 检查是否需要更新
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT content_hash FROM files WHERE path=?", (path,)).fetchone()
            if row and row[0] == content_hash:
                return None  # 未变化

        entry = IndexEntry(
            path=path,
            content_hash=content_hash,
            mtime=mtime,
            indexed_at=datetime.now(timezone.utc).isoformat(),
            file_type=self._get_file_type(path),
            summary=self._extract_summary(path, content),
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO files(path, content_hash, mtime, indexed_at, file_type, summary)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (entry.path, entry.content_hash, entry.mtime, entry.indexed_at, entry.file_type, entry.summary),
            )
            conn.commit()

        logger.debug(f"Indexed: {path}")
        return entry

    def sync_all(self) -> dict[str, Any]:
        """全量扫描所有监控目录。"""
        new_count = 0
        updated_count = 0
        total_scanned = 0

        for watch_dir in self._watched:
            for root, dirs, files in os.walk(watch_dir):
                # 跳过隐藏目录和 venv/node_modules
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__", "venv", ".venv")]
                for fn in files:
                    if fn.startswith("."):
                        continue
                    filepath = os.path.join(root, fn)
                    total_scanned += 1
                    result = self.index_file(filepath)
                    if result:
                        new_count += 1

        stats = self.get_stats()
        return {
            "scanned": total_scanned,
            "indexed": new_count,
            "total_indexed": stats["total_files"],
            "watch_dirs": len(self._watched),
        }

    # ── Query ───────────────────────────────────────────────

    def query(self, term: str, limit: int = 20) -> list[dict[str, Any]]:
        """搜索已索引内容。"""
        with sqlite3.connect(self.db_path) as conn:
            conn.create_function("MATCH_TERM", 2, lambda p, t: 1 if t.lower() in p.lower() else 0)
            rows = conn.execute(
                """SELECT path, file_type, summary, indexed_at
                   FROM files
                   WHERE (path LIKE ? OR summary LIKE ?)
                   ORDER BY indexed_at DESC
                   LIMIT ?""",
                (f"%{term}%", f"%{term}%", limit),
            ).fetchall()

        return [
            {"path": r[0], "file_type": r[1], "summary": r[2][:100], "indexed_at": r[3]}
            for r in rows
        ]

    # ── Stats ───────────────────────────────────────────────

    def get_stats(self) -> dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
            by_type = conn.execute(
                "SELECT file_type, COUNT(*) FROM files GROUP BY file_type ORDER BY COUNT(*) DESC"
            ).fetchall()
            latest = conn.execute(
                "SELECT indexed_at FROM files ORDER BY indexed_at DESC LIMIT 1"
            ).fetchone()

        return {
            "total_files": total,
            "by_type": dict(by_type) if by_type else {},
            "last_indexed": latest[0] if latest else None,
            "watch_dirs": self._watched,
        }

    # ── Cleanup ─────────────────────────────────────────────

    def prune_deleted(self) -> int:
        """移除已删除文件的索引记录。"""
        removed = 0
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT path FROM files").fetchall()
            for (path,) in rows:
                if not os.path.exists(path):
                    conn.execute("DELETE FROM files WHERE path=?", (path,))
                    removed += 1
            conn.commit()
        return removed


# ═══════════════════════════════════════════════════════════════
# 便捷CLI
# ═══════════════════════════════════════════════════════════════

def cmd_index_watch(path: str):
    ci = CocoIndex()
    ci.watch_directory(path)
    print(f"👁  CocoIndex watching: {path}")
    result = ci.sync_all()
    print(f"   初始扫描: {result['scanned']} 文件, 索引 {result['indexed']} 条")


def cmd_index_query(term: str):
    ci = CocoIndex()
    results = ci.query(term)
    if not results:
        print(f"🔍 无匹配结果: {term}")
    else:
        print(f"🔍 匹配 {len(results)} 条:")
        for r in results:
            print(f"  [{r['file_type']}] {r['path']}")
            print(f"     {r['summary']}")


def cmd_index_sync():
    # 自动监控 Molin-OS 核心目录
    ci = CocoIndex()
    for watch_dir in [
        str(Path.home() / "Molin-OS" / "molib"),
        str(Path.home() / ".hermes" / "relay"),
    ]:
        if os.path.isdir(watch_dir):
            ci.watch_directory(watch_dir)

    result = ci.sync_all()
    pruned = ci.prune_deleted()
    print(f"🔄 CocoIndex 同步: {result['indexed']} 新/更新, {pruned} 过期移除")
    print(f"   总计: {result['total_indexed']} 文件, {len(result['watch_dirs'])} 监控目录")


def cmd_index_stats():
    ci = CocoIndex()
    stats = ci.get_stats()
    print(f"📊 CocoIndex 统计")
    print(f"   总文件数: {stats['total_files']}")
    print(f"   监控目录: {stats['watch_dirs']}")
    print(f"   最后索引: {stats['last_indexed'] or 'N/A'}")
    print(f"   按类型: ")
    for ftype, count in stats["by_type"].items():
        print(f"     {ftype}: {count}")
