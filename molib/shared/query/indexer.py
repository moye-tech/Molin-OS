"""
墨麟OS v2.0 — MQL 索引器

统一索引多个数据源，为 MQL 查询提供快速数据访问。

索引源:
  - skills: ~/.hermes/skills/*/SKILL.md (YAML frontmatter)
  - experiences: ExperienceVault 中的经验记录
  - notes: Obsidian Vault 中的 Markdown 笔记
  - memory: ~/.hermes/memory/ 和 Hermes 记忆系统
  - hermes_sessions: ~/.hermes/sessions/ JSONL 会话记录

对标 Obsidian Dataview 的索引机制：
  预解析所有笔记的 frontmatter + 内联字段，建立内存索引。
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml


# ── 数据模型 ─────────────────────────────────

class IndexEntry:
    """索引条目 — 统一的扁平化记录"""

    __slots__ = ("source", "id", "name", "description", "tags", "category",
                 "version", "created_at", "modified_at", "metadata", "_raw")

    def __init__(self, source: str, id: str, **kwargs):
        self.source = source
        self.id = id
        self.name = kwargs.get("name", "")
        self.description = kwargs.get("description", "")
        self.tags = kwargs.get("tags", [])
        self.category = kwargs.get("category", "")
        self.version = kwargs.get("version", "")
        self.created_at = kwargs.get("created_at", "")
        self.modified_at = kwargs.get("modified_at", "")
        self.metadata = kwargs.get("metadata", {})
        self._raw = kwargs  # 原始数据

    def get(self, field: str, default=None) -> Any:
        """获取字段值（包括嵌套字段，如 'metadata.worker_id'）"""
        if "." in field:
            parts = field.split(".")
            current = self._raw
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return default
            return current

        if field in self._raw:
            return self._raw[field]

        # 检查标准属性
        attr_map = {
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "category": self.category,
            "version": self.version,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "source": self.source,
            "id": self.id,
        }
        return attr_map.get(field, default)

    def has_tag(self, tag: str) -> bool:
        """检查是否有指定标签"""
        return tag in (self.tags or [])

    def __repr__(self):
        return f"IndexEntry(source={self.source}, id={self.id}, name={self.name})"


# ── 索引器 ───────────────────────────────────

class MQLIndexer:
    """MQL 索引器 — 管理所有数据源索引"""

    def __init__(self):
        self._entries: dict[str, list[IndexEntry]] = {}
        self._last_indexed: dict[str, datetime] = {}

    # ── 索引构建 ──────────────────────────

    def index_skills(self, skills_dir: Optional[Path] = None) -> list[IndexEntry]:
        """索引 ~/.hermes/skills/ 中的所有技能"""
        if skills_dir is None:
            skills_dir = Path.home() / ".hermes" / "skills"

        entries = []
        if not skills_dir.exists():
            return entries

        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir() or skill_dir.name.startswith("."):
                continue

            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue

            try:
                content = skill_md.read_text(encoding="utf-8")
            except Exception:
                continue

            fm = self._parse_frontmatter(content)
            stat = skill_md.stat()

            entry = IndexEntry(
                source="skills",
                id=skill_dir.name,
                name=fm.get("name", skill_dir.name),
                description=fm.get("description", "")[:300],
                tags=fm.get("tags", []),
                category=fm.get("category", ""),
                version=fm.get("version", "0.0.0"),
                created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                metadata={
                    "path": str(skill_dir),
                    "source_url": fm.get("source", ""),
                    "min_hermes_version": fm.get("min_hermes_version", ""),
                    "dependencies": fm.get("dependencies", []),
                }
            )
            entries.append(entry)

        self._entries["skills"] = entries
        self._last_indexed["skills"] = datetime.now()
        return entries

    def index_notes(self, vault_path: Optional[Path] = None) -> list[IndexEntry]:
        """索引 Obsidian Vault 中的所有笔记"""
        if vault_path is None:
            vault_path = Path(os.environ.get(
                "OBSIDIAN_VAULT_PATH",
                str(Path.home() / "Documents" / "Obsidian Vault")
            ))

        entries = []
        if not vault_path.exists():
            return entries

        for md_file in vault_path.rglob("*.md"):
            # 跳过 .obsidian 和隐藏目录
            if any(part.startswith(".") for part in md_file.parts):
                continue

            try:
                content = md_file.read_text(encoding="utf-8")
            except Exception:
                continue

            fm = self._parse_frontmatter(content)

            # 提取 wikilinks
            wikilinks = re.findall(r'\[\[([^\]|#]+)', content)

            # 提取标签（#tag 和 frontmatter tags）
            inline_tags = re.findall(r'#([a-zA-Z_][\w/-]*)', content)
            tags = fm.get("tags", []) + inline_tags

            stat = md_file.stat()
            rel_path = md_file.relative_to(vault_path)

            entry = IndexEntry(
                source="notes",
                id=str(rel_path.with_suffix("")),
                name=fm.get("title") or fm.get("name") or md_file.stem,
                description=self._extract_summary(content)[:300],
                tags=list(set(tags))[:20],
                category=fm.get("category", ""),
                created_at=fm.get("date") or fm.get("created") or
                          datetime.fromtimestamp(stat.st_ctime).isoformat(),
                modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                metadata={
                    "path": str(md_file),
                    "rel_path": str(rel_path),
                    "wikilinks": wikilinks[:50],
                    "word_count": len(content.split()),
                }
            )
            entries.append(entry)

        self._entries["notes"] = entries
        self._last_indexed["notes"] = datetime.now()
        return entries

    def index_memory(self) -> list[IndexEntry]:
        """索引 Hermes 持久记忆"""
        entries = []

        # Memory.md
        memory_md = Path.home() / ".hermes" / "memory.md"
        if memory_md.exists():
            try:
                content = memory_md.read_text(encoding="utf-8")
                entries.append(IndexEntry(
                    source="memory",
                    id="memory.md",
                    name="Persistent Memory",
                    description=content[:300],
                    tags=["memory", "persistent"],
                    category="system",
                    metadata={"path": str(memory_md)},
                ))
            except Exception:
                pass

        # User.md
        user_md = Path.home() / ".hermes" / "user.md"
        if user_md.exists():
            try:
                content = user_md.read_text(encoding="utf-8")
                entries.append(IndexEntry(
                    source="memory",
                    id="user.md",
                    name="User Profile",
                    description=content[:300],
                    tags=["user", "profile"],
                    category="system",
                    metadata={"path": str(user_md)},
                ))
            except Exception:
                pass

        self._entries["memory"] = entries
        self._last_indexed["memory"] = datetime.now()
        return entries

    def index_experiences(self) -> list[IndexEntry]:
        """索引 ExperienceVault 经验记录"""
        entries = []
        try:
            from molib.shared.experience.vault import ExperienceVault
            # ExperienceVault 目前是 RAG-based，尝试通过文件系统查找
            exp_dir = Path.home() / ".hermes" / "memory" / "experiences"
            if exp_dir.exists():
                for f in exp_dir.glob("*.json"):
                    try:
                        data = json.loads(f.read_text())
                        entries.append(IndexEntry(
                            source="experiences",
                            id=data.get("id", f.stem),
                            name=data.get("task_summary", "")[:100],
                            description=data.get("approach", "")[:300],
                            tags=data.get("tags", []),
                            category="experience",
                            created_at=data.get("created_at", ""),
                            metadata=data,
                        ))
                    except Exception:
                        continue
        except ImportError:
            pass

        self._entries["experiences"] = entries
        self._last_indexed["experiences"] = datetime.now()
        return entries

    def index_sessions(self, limit: int = 100) -> list[IndexEntry]:
        """索引 Hermes 会话记录"""
        entries = []
        sessions_dir = Path.home() / ".hermes" / "sessions"

        if not sessions_dir.exists():
            return entries

        session_files = sorted(sessions_dir.glob("*.jsonl"), reverse=True)[:limit]
        for sf in session_files:
            try:
                stat = sf.stat()
                # 读第一行获取会话元数据
                with open(sf) as fh:
                    first_line = fh.readline()
                    first_msg = json.loads(first_line) if first_line.strip() else {}

                entries.append(IndexEntry(
                    source="hermes_sessions",
                    id=sf.stem,
                    name=f"Session {sf.stem[:16]}",
                    description=first_msg.get("content", "")[:200],
                    tags=["session"],
                    category="hermes",
                    created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    metadata={
                        "path": str(sf),
                        "size": stat.st_size,
                    }
                ))
            except Exception:
                continue

        self._entries["hermes_sessions"] = entries
        self._last_indexed["hermes_sessions"] = datetime.now()
        return entries

    # ── 索引查询 ──────────────────────────

    def get_entries(self, source: str) -> list[IndexEntry]:
        """获取指定数据源的所有条目（自动索引如果未缓存）"""
        if source not in self._entries:
            self._index_source(source)
        return self._entries.get(source, [])

    def refresh(self, source: Optional[str] = None):
        """刷新索引"""
        if source:
            self._index_source(source)
        else:
            for src in self._entries:
                self._index_source(src)

    # ── 辅助方法 ──────────────────────────

    def _index_source(self, source: str):
        """按需索引单个数据源"""
        indexers = {
            "skills": self.index_skills,
            "notes": self.index_notes,
            "memory": self.index_memory,
            "experiences": self.index_experiences,
            "hermes_sessions": self.index_sessions,
        }
        if source in indexers:
            indexers[source]()

    @staticmethod
    def _parse_frontmatter(content: str) -> dict:
        """解析 Markdown YAML frontmatter"""
        content = content.lstrip()
        if not content.startswith("---"):
            return {}
        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}
        try:
            return yaml.safe_load(parts[1]) or {}
        except yaml.YAMLError:
            return {}

    @staticmethod
    def _extract_summary(content: str) -> str:
        """提取文档摘要（去除 frontmatter 后前 300 字符）"""
        body = content
        if body.startswith("---"):
            parts = body.split("---", 2)
            body = parts[2] if len(parts) > 2 else body
        # 去除 markdown 格式
        body = re.sub(r'[#*>`\[\]|]', '', body)
        body = re.sub(r'\n+', ' ', body)
        return body.strip()[:300]


# ── 全局单例 ────────────────────────────────

_indexer: Optional[MQLIndexer] = None


def get_indexer() -> MQLIndexer:
    """获取全局索引器单例"""
    global _indexer
    if _indexer is None:
        _indexer = MQLIndexer()
    return _indexer


def reset_indexer():
    """重置全局索引器"""
    global _indexer
    _indexer = None
