"""
记忆蒸馏引擎 — 两层架构（Mac M2 8GB 适配）
==========================================
跳过中间"情节记忆"层，直接从工作记忆蒸馏到语义记忆。

两层结构:
  Layer 1: Working Memory — 最近 N 次会话的原始对话摘要
  Layer 2: Semantic Memory — 提炼为可复用的 SOP 模式、经验法则

存储:
  SQLite: ~/.hermes/memory/distillation.db  
  ChromaDB: ~/.hermes/memory/chroma_db/ (已有)

CLI:
  python -m molib memory distill — 手动触发蒸馏
  python -m molib memory stats — 查看记忆统计
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("molin.memory_distill")

DB_PATH = Path.home() / ".hermes" / "memory" / "distillation.db"


@dataclass
class MemoryEntry:
    id: int = 0
    source: str = ""          # session_id 或来源标识
    content: str = ""         # 原始内容摘要
    layer: str = "working"    # working | semantic
    distilled_from: str = ""  # 从哪个 working memory 提炼的
    created_at: str = ""
    tags: str = ""            # 逗号分隔的标签


class MemoryDistiller:
    """两层记忆蒸馏引擎。"""

    def __init__(self, db_path: str = ""):
        self.db_path = db_path or str(DB_PATH)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT DEFAULT '',
                    content TEXT NOT NULL,
                    layer TEXT CHECK(layer IN ('working','semantic')) DEFAULT 'working',
                    distilled_from TEXT DEFAULT '',
                    created_at TEXT DEFAULT (datetime('now')),
                    tags TEXT DEFAULT ''
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_layer ON memories(layer)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tags ON memories(tags)")
            conn.commit()

    # ── Layer 1: Working Memory ──────────────────────────────

    def add_working_memory(self, source: str, content: str, tags: str = "") -> int:
        """添加工作记忆（原始对话摘要）。自动触发压缩检查。"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO memories (source, content, layer, tags) VALUES (?, ?, 'working', ?)",
                (source, content[:5000], tags),
            )
            conn.commit()
            memory_id = cursor.lastrowid

        # 自动压缩：超过 50 条工作记忆 → 触发蒸馏
        count = self._count_layer("working")
        if count > 50:
            logger.info(f"工作记忆 {count} 条，触发自动蒸馏...")
            self._auto_distill(count)

        return memory_id

    def _count_layer(self, layer: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM memories WHERE layer=?", (layer,)
            ).fetchone()[0]

    # ── Layer 2: Semantic Memory ─────────────────────────────

    def _extract_patterns(self, workings: list[dict]) -> list[dict]:
        """从工作记忆中提取语义模式（启发式规则）。"""
        patterns = []
        content_text = "\n".join(w["content"] for w in workings)

        keyword_rules = {
            "错误": "⚠️ 常见错误模式",
            "修复": "🔧 已知修复方案",
            "优化": "📈 性能优化经验",
            "配置": "⚙️ 配置最佳实践",
            "API": "🔗 API 使用经验",
            "Bug": "🐛 Bug 修复记录",
            "成功": "✅ 已验证的工作流程",
            "失败": "❌ 避免的操作",
            "飞书": "📱 飞书集成经验",
            "闲鱼": "🛒 闲鱼自动化经验",
            "备份": "💾 备份策略",
            "部署": "🚀 部署流程",
        }

        for keyword, label in keyword_rules.items():
            if keyword.lower() in content_text.lower():
                # 提取相关句子
                related = []
                for w in workings:
                    if keyword.lower() in w["content"].lower():
                        related.append(w["content"][:300])
                if related:
                    patterns.append({
                        "label": label,
                        "keyword": keyword,
                        "sources": len(related),
                        "sample": related[0][:150],
                    })

        return patterns

    def distill(
        self,
        working_ids: Optional[list[int]] = None,
        min_pattern_confidence: int = 2,
    ) -> dict[str, Any]:
        """执行蒸馏：工作记忆 → 语义记忆。

        Args:
            working_ids: 指定要蒸馏的工作记忆 ID，不传则蒸馏最近 50 条
            min_pattern_confidence: 最少出现次数才算有效模式
        """
        with sqlite3.connect(self.db_path) as conn:
            if working_ids:
                placeholders = ",".join("?" * len(working_ids))
                rows = conn.execute(
                    f"SELECT id, source, content, tags FROM memories WHERE id IN ({placeholders}) AND layer='working'",
                    working_ids,
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, source, content, tags FROM memories WHERE layer='working' ORDER BY id DESC LIMIT 50"
                ).fetchall()

        if not rows:
            return {"distilled": 0, "patterns": [], "message": "无工作记忆可蒸馏"}

        workings = [{"id": r[0], "source": r[1], "content": r[2], "tags": r[3]} for r in rows]
        patterns = self._extract_patterns(workings)

        # 过滤低频模式
        patterns = [p for p in patterns if p["sources"] >= min_pattern_confidence]

        distilled_count = 0
        with sqlite3.connect(self.db_path) as conn:
            for p in patterns:
                distilled_from = ",".join(str(w["id"]) for w in workings if p["keyword"].lower() in w["content"].lower())
                content = f"[{p['label']}] 关键词: {p['keyword']} | 样本: {p['sample']}"
                conn.execute(
                    "INSERT INTO memories (source, content, layer, distilled_from, tags) VALUES (?, ?, 'semantic', ?, ?)",
                    ("auto_distill", content, distilled_from[:500], p['keyword']),
                )
                distilled_count += 1

            # 标记已蒸馏的工作记忆
            distilled_ids = [w["id"] for w in workings]
            placeholders = ",".join("?" * len(distilled_ids))
            conn.execute(
                f"UPDATE memories SET tags = tags || ',distilled' WHERE id IN ({placeholders}) AND tags NOT LIKE '%distilled%'",
                distilled_ids,
            )
            conn.commit()

        logger.info(f"蒸馏完成: {distilled_count} 个语义模式, 来源 {len(workings)} 条工作记忆")
        return {
            "distilled": distilled_count,
            "patterns": [{"label": p["label"], "sources": p["sources"]} for p in patterns],
            "working_memories": len(workings),
        }

    def _auto_distill(self, working_count: int):
        """自动蒸馏（内部触发）。"""
        # 蒸馏最老的 30 条（保留最近 20 条）
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id FROM memories WHERE layer='working' ORDER BY id ASC LIMIT ?",
                (working_count - 20,),
            ).fetchall()
        if rows:
            ids = [r[0] for r in rows]
            self.distill(working_ids=ids)

    # ── 查询 ─────────────────────────────────────────────────

    def get_semantic_memories(self, keyword: str = "", limit: int = 10) -> list[dict[str, Any]]:
        """查询语义记忆。"""
        with sqlite3.connect(self.db_path) as conn:
            if keyword:
                rows = conn.execute(
                    "SELECT id, content, tags, created_at FROM memories WHERE layer='semantic' AND (content LIKE ? OR tags LIKE ?) ORDER BY id DESC LIMIT ?",
                    (f"%{keyword}%", f"%{keyword}%", limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, content, tags, created_at FROM memories WHERE layer='semantic' ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [
            {"id": r[0], "content": r[1], "tags": r[2], "created_at": r[3]}
            for r in rows
        ]

    def stats(self) -> dict[str, Any]:
        """记忆统计。"""
        with sqlite3.connect(self.db_path) as conn:
            working = conn.execute("SELECT COUNT(*) FROM memories WHERE layer='working'").fetchone()[0]
            semantic = conn.execute("SELECT COUNT(*) FROM memories WHERE layer='semantic'").fetchone()[0]
            tag_rows = conn.execute("SELECT tags FROM memories WHERE layer='semantic'").fetchall()
            tags = set()
            for (t,) in tag_rows:
                if t:
                    tags.update(t.split(","))

        return {
            "working_memories": working,
            "semantic_memories": semantic,
            "distilled_tags": sorted(tags),
            "auto_distill_threshold": "50 条触发",
        }


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def cmd_memory_distill():
    md = MemoryDistiller()
    result = md.distill()
    print(f"🧠 记忆蒸馏完成:")
    print(f"   语义模式: {result['distilled']}")
    print(f"   来源记忆: {result['working_memories']}")
    for p in result.get("patterns", []):
        print(f"   • {p['label']} (来源 {p['sources']} 条)")


def cmd_memory_stats():
    md = MemoryDistiller()
    s = md.stats()
    print(f"🧠 记忆系统统计:")
    print(f"   工作记忆: {s['working_memories']} 条")
    print(f"   语义记忆: {s['semantic_memories']} 条")
    print(f"   语义标签: {', '.join(s['distilled_tags'][:10]) or '无'}")
    print(f"   自动蒸馏: {s['auto_distill_threshold']}")
