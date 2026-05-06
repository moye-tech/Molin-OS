"""
墨域OS — SOP持久化存储
========================
保存每次CEO处理任务的标准作业程序(SOP)记录，
支持按任务描述相似度检索历史记录。
"""

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any

logger = logging.getLogger("molin.sop")

# 全局 SOP 存储路径
SOP_DIR = Path.home() / ".hermes" / "sops"


class SOPStore:
    """SOP持久化存储引擎"""

    def __init__(self, storage_dir: str | Path | None = None):
        self._storage_dir = Path(storage_dir) if storage_dir else SOP_DIR
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self._storage_dir / "_index.json"
        self._index: dict[str, dict[str, Any]] = {}
        self._load_index()

    # ── 公开接口 ──────────────────────────────────────────────────────

    def save(
        self,
        task_id: str,
        vp_used: list[str],
        steps: list[dict],
        quality: float,
        duration: float,
        task_description: str = "",
        risk_score: float = 0.0,
        **extra,
    ) -> str:
        """保存一条SOP记录，返回记录ID"""
        record_id = f"sop-{uuid.uuid4().hex[:12]}"
        record = {
            "record_id": record_id,
            "task_id": task_id,
            "task_description": task_description,
            "vp_used": vp_used,
            "steps": steps,
            "quality": round(quality, 2),
            "duration": round(duration, 3),
            "risk_score": round(risk_score, 2),
            "timestamp": time.time(),
            **extra,
        }
        file_path = self._storage_dir / f"{record_id}.json"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
            self._index[record_id] = {
                "record_id": record_id,
                "task_id": task_id,
                "task_description": task_description,
                "vp_used": vp_used,
                "quality": record["quality"],
                "timestamp": record["timestamp"],
            }
            self._save_index()
            logger.info("[SOP] 已保存 record=%s task=%s vps=%s", record_id, task_id, vp_used)
        except Exception as e:
            logger.error("[SOP] 保存失败 record=%s: %s", record_id, e)
        return record_id

    def query_similar(
        self,
        task_description: str,
        top_k: int = 5,
        min_quality: float = 0.0,
    ) -> list[dict]:
        """
        查询相似历史SOP记录。

        使用基于关键词重叠的简单相似度匹配（后续可升级为embedding检索）。
        返回按相似度降序排列的记录列表。
        """
        if not task_description:
            return []

        query_keywords = self._tokenize(task_description)
        if not query_keywords:
            return []

        scored: list[tuple[float, dict]] = []
        for rid, meta in self._index.items():
            desc_kws = self._tokenize(meta.get("task_description", ""))
            if not desc_kws:
                continue
            overlap = len(query_keywords & desc_kws)
            similarity = overlap / max(len(query_keywords), len(desc_kws))
            quality = meta.get("quality", 0)
            if similarity > 0 and quality >= min_quality:
                scored.append((similarity, rid))

        scored.sort(key=lambda x: (-x[0], -self._index[x[1]].get("quality", 0)))

        results = []
        for sim, rid in scored[:top_k]:
            record = self._load_record(rid)
            if record:
                record["_similarity"] = round(sim, 4)
                results.append(record)
        return results

    def get(self, record_id: str) -> dict | None:
        """按record_id获取完整SOP记录"""
        return self._load_record(record_id)

    def list_recent(self, limit: int = 20) -> list[dict]:
        """列出最近的SOP记录摘要"""
        sorted_items = sorted(
            self._index.values(),
            key=lambda x: x.get("timestamp", 0),
            reverse=True,
        )
        return sorted_items[:limit]

    def count(self) -> int:
        return len(self._index)

    # ── 内部方法 ──────────────────────────────────────────────────────

    def _tokenize(self, text: str) -> set[str]:
        """中文+英文分词（简易版）"""
        if not text:
            return set()
        import re
        # 提取中文词（单字太短无意义，用2-gram）
        chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)
        words = set()
        for i in range(len(chinese_chars) - 1):
            words.add(chinese_chars[i] + chinese_chars[i + 1])
        # 提取英文单词
        words.update(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{1,}", text.lower()))
        # 数字
        words.update(re.findall(r"\d+", text))
        return words

    def _load_record(self, record_id: str) -> dict | None:
        """从磁盘加载完整记录"""
        file_path = self._storage_dir / f"{record_id}.json"
        if not file_path.exists():
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("[SOP] 读取失败 %s: %s", record_id, e)
            return None

    def _load_index(self):
        """加载索引文件"""
        if self._index_path.exists():
            try:
                with open(self._index_path, "r", encoding="utf-8") as f:
                    self._index = json.load(f)
            except Exception as e:
                logger.warning("[SOP] 索引加载失败，重置: %s", e)
                self._index = {}

    def _save_index(self):
        """保存索引文件"""
        try:
            with open(self._index_path, "w", encoding="utf-8") as f:
                json.dump(self._index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("[SOP] 索引保存失败: %s", e)
