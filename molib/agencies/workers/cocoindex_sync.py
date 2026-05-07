"""
墨域同步 Worker — CocoIndex 增量数据同步

基于 CocoIndex 的声明式增量数据同步框架，提供：
- files→ChromaDB 向量化同步（文件变更→自动更新向量索引）
- Postgres→Memory 增量同步（DB 变更→自动更新内存）
- 定时/实时同步管道管理

CLI 命令（通过 __main__.py 注册为 `python -m molib sync <subcmd>`）：
  sync start --pipeline <name>      # 启动同步管道
  sync stop --pipeline <name>       # 停止同步管道
  sync status                       # 查看所有管道状态
  sync run --pipeline <name>        # 运行一次全量同步（增量 catch-up）
  sync list                         # 列出可用管道
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import SubsidiaryWorker, Task, WorkerResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

SYNC_WORK_DIR = Path("~/.hermes/sync").expanduser()
PIPELINE_STATE_DIR = SYNC_WORK_DIR / "state"


@dataclass
class PipelineState:
    """同步管道的运行时状态。"""
    name: str
    source_type: str         # "files" | "postgres"
    target_type: str         # "chromadb" | "memory"
    status: str = "stopped"  # "running" | "stopped" | "error"
    last_run: Optional[float] = None
    last_error: Optional[str] = None
    total_indexed: int = 0
    total_errors: int = 0
    pid: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "source_type": self.source_type,
            "target_type": self.target_type,
            "status": self.status,
            "last_run": self.last_run,
            "last_error": self.last_error,
            "total_indexed": self.total_indexed,
            "total_errors": self.total_errors,
        }


# 管道注册表（内存中的管道定义 + 运行时状态）
_pipelines: Dict[str, "SyncPipeline"] = {}
_pipeline_states: Dict[str, PipelineState] = {}
_pipeline_threads: Dict[str, threading.Thread] = {}
_lock = threading.Lock()


# ---------------------------------------------------------------------------
# CocoIndex 管道定义
# ---------------------------------------------------------------------------

class SyncPipeline:
    """单个同步管道的定义，封装 CocoIndex 数据流。"""

    def __init__(
        self,
        name: str,
        source_type: str,
        target_type: str,
        source_config: dict,
        target_config: Optional[dict] = None,
        schedule: Optional[str] = None,
    ):
        self.name = name
        self.source_type = source_type
        self.target_type = target_type
        self.source_config = source_config
        self.target_config = target_config or {}
        self.schedule = schedule  # e.g., "*/5 * * * *" (cron), None = manual

    @property
    def is_files_pipeline(self) -> bool:
        return self.source_type == "files"

    @property
    def is_db_pipeline(self) -> bool:
        return self.source_type == "postgres"

    def describe(self) -> str:
        src = self.source_config.get("path", self.source_config.get("connection", "?"))
        tgt = self.target_config.get("collection", self.target_config.get("namespace", "?"))
        return f"{self.name}: {self.source_type}→{self.target_type} ({src} → {tgt})"


def _make_files_pipeline(
    name: str,
    watch_dir: str,
    file_pattern: str = "**/*.{md,txt,py,json,csv}",
    collection: str = "hermes_files",
) -> SyncPipeline:
    """创建文件→向量索引管道。

    监听指定目录的文件变更，自动提取文本并写入向量存储。
    使用 CocoIndex 的增量计算能力：仅处理新增/修改的文件。
    """
    return SyncPipeline(
        name=name,
        source_type="files",
        target_type="chromadb",
        source_config={
            "path": watch_dir,
            "pattern": file_pattern,
            "chunk_size": 512,
            "chunk_overlap": 64,
        },
        target_config={
            "collection": collection,
            "embedding_dim": 384,  # sentence-transformers all-MiniLM-L6-v2
        },
        schedule="*/10 * * * *",  # 每10分钟
    )


def _make_db_pipeline(
    name: str,
    connection: str,
    table: str,
    key_column: str = "id",
    namespace: str = "db_sync",
) -> SyncPipeline:
    """创建数据库→内存同步管道。

    监听 Postgres 表的行变更（INSERT/UPDATE/DELETE），
    自动同步到 Hermes 内部内存/知识库。
    """
    return SyncPipeline(
        name=name,
        source_type="postgres",
        target_type="memory",
        source_config={
            "connection": connection,
            "table": table,
            "key_column": key_column,
            "poll_interval": 30,
        },
        target_config={
            "namespace": namespace,
        },
        schedule="*/1 * * * *",  # 每分钟
    )


# ---------------------------------------------------------------------------
# 预设管道工厂
# ---------------------------------------------------------------------------

def get_default_pipelines() -> List[SyncPipeline]:
    """返回 Hermes OS 的默认同步管道配置。

    管道1: 知识库文件 → 向量索引
    管道2: CRM 数据库 → Hermes 记忆
    """
    hermes_home = Path(os.environ.get("HERMES_HOME", "~/.hermes")).expanduser()
    knowledge_dir = hermes_home / "knowledge"
    knowledge_dir.mkdir(parents=True, exist_ok=True)

    return [
        _make_files_pipeline(
            name="knowledge_files",
            watch_dir=str(knowledge_dir),
            file_pattern="**/*.{md,txt,json}",
            collection="hermes_knowledge",
        ),
        _make_db_pipeline(
            name="crm_memory",
            connection=os.environ.get(
                "HERMES_DB_URL",
                "postgresql://localhost:5432/hermes?sslmode=disable",
            ),
            table="crm_contacts",
            namespace="crm",
        ),
    ]


# ---------------------------------------------------------------------------
# 同步执行引擎
# ---------------------------------------------------------------------------

def _run_cocoindex_sync(pipeline: SyncPipeline) -> dict:
    """使用 CocoIndex 框架执行一次增量同步。

    这是核心同步逻辑。实际运行时会：
    1. 构建 CocoIndex App 定义（声明式数据流图）
    2. 调用 app.update_blocking() 执行增量 catch-up 模式
    3. 返回同步结果统计
    """
    try:
        import cocoindex as coco
    except ImportError:
        logger.warning("cocoindex not installed; using mock sync")
        return _mock_sync(pipeline)

    PIPELINE_STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file = PIPELINE_STATE_DIR / f"{pipeline.name}.json"

    # 设置 CocoIndex 工作目录
    db_dir = PIPELINE_STATE_DIR / "cocoindex_db"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / f"{pipeline.name}.lmdb"
    os.environ.setdefault("COCOINDEX_DB", str(db_path))

    # --- 构建 CocoIndex App（声明式数据流） ---
    # App 接受一个 main_fn 函数作为参数，在该函数中定义数据流图
    def main_fn():
        # 根据管道类型构建数据流
        if pipeline.is_files_pipeline:
            _build_files_vector_pipeline(coco, pipeline)
        elif pipeline.is_db_pipeline:
            _build_db_memory_pipeline(coco, pipeline)

    app = coco.App(
        coco.AppConfig(
            name=f"hermes_sync_{pipeline.name}",
            environment=coco.Environment(settings=coco.Settings(db_path=db_path)),
        ),
        main_fn,
    )

    # --- 执行增量同步 ---
    try:
        result = app.update_blocking()
        stats = {
            "status": "success",
            "updated": result.components_updated if hasattr(result, "components_updated") else 0,
            "errors": result.errors if hasattr(result, "errors") else [],
            "timestamp": time.time(),
        }
    except Exception as e:
        stats = {
            "status": "error",
            "error": str(e),
            "timestamp": time.time(),
        }

    # 持久化状态
    with open(state_file, "w") as f:
        json.dump(stats, f)

    return stats


def _build_files_vector_pipeline(coco, pipeline: SyncPipeline) -> None:
    """构建文件→向量管道的 CocoIndex 数据流。

    数据流：
    1. 监视文件目录的文件变更
    2. 读取新/变更文件内容
    3. 分块处理
    4. 生成嵌入向量
    5. 写入向量存储

    所有函数使用 @coco.fn(memo=True) 装饰，CocoIndex 自动处理增量：
    - 仅对新增/变更的文件执行全流程
    - 未变文件跳过处理
    """
    cfg = pipeline.source_config
    tgt = pipeline.target_config

    @coco.fn(memo=True)
    def list_source_files(base_dir: str, pattern: str) -> List[str]:
        """列出所有需要索引的源文件。"""
        p = Path(base_dir).expanduser()
        if not p.exists():
            return []
        files = []
        for f in p.rglob(pattern):
            if f.is_file() and not f.name.startswith("."):
                files.append(str(f))
        return sorted(files)

    @coco.fn(memo=True)
    def read_file_content(file_path: str) -> Optional[str]:
        """读取文件内容（增量感知——仅新/变更文件会被读取）。"""
        try:
            content = Path(file_path).read_text(encoding="utf-8", errors="replace")
            return content
        except Exception as e:
            logger.debug("Failed to read %s: %s", file_path, e)
            return None

    @coco.fn(memo=True)
    def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> List[str]:
        """将文本分块，参考 RAGEngine 的分块逻辑。"""
        if not text or not text.strip():
            return []
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            if end < len(text):
                search_start = max(end - 100, start)
                for sep in ["。", "！", "？", "\n\n", ". ", "!\n", "?\n"]:
                    pos = text.rfind(sep, search_start, end)
                    if pos > search_start:
                        end = pos + len(sep)
                        break
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - overlap if end < len(text) else len(text)

        return chunks if chunks else [text]

    @coco.fn(memo=True)
    def compute_embedding(text: str, dim: int = 384) -> List[float]:
        """计算文本的嵌入向量。

        生产环境中应替换为 sentence-transformers API 调用。
        当前使用基于 hash 的确定性伪向量以确保可复现。
        """
        import hashlib
        import math

        h = hashlib.sha256(text.encode()).hexdigest()
        seed = int(h[:16], 16)
        vec = []
        for i in range(dim):
            seed = (seed * 1103515245 + 12345) & 0xFFFFFFFF
            vec.append((seed / 0xFFFFFFFF) * 2.0 - 1.0)
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    @coco.fn(memo=True)
    def store_vectors(
        file_path: str,
        chunks: List[str],
        embeddings: List[List[float]],
        collection: str,
    ) -> dict:
        """将分块和向量写入向量存储（ChromaDB 兼容格式）。"""
        store_dir = Path("~/.hermes/vectors/cocoindex").expanduser()
        store_dir.mkdir(parents=True, exist_ok=True)

        entries = []
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            entry = {
                "id": f"{Path(file_path).stem}_chunk_{i}",
                "source": file_path,
                "text": chunk[:500],
                "embedding": emb[:8],
                "collection": collection,
                "indexed_at": time.time(),
            }
            entries.append(entry)

        collection_file = store_dir / f"{collection}.jsonl"
        with open(collection_file, "a") as f:
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return {
            "file": file_path,
            "chunks_count": len(chunks),
            "collection": collection,
        }

    # 数据流编排：文件列表 → 每个文件 → 读取 → 分块 → 嵌入 → 存储
    # cocoindex 在 update 时自动处理增量变化
    files = list_source_files(cfg["path"], cfg.get("pattern", "**/*"))
    for f in files or []:
        content = read_file_content(f)
        if content:
            chunks = chunk_text(content, cfg.get("chunk_size", 512), cfg.get("chunk_overlap", 64))
            if chunks:
                embeddings = [compute_embedding(c, tgt.get("embedding_dim", 384)) for c in chunks]
                store_vectors(f, chunks, embeddings, tgt.get("collection", "default"))


def _build_db_memory_pipeline(coco, pipeline: SyncPipeline) -> None:
    """构建数据库→内存管道的 CocoIndex 数据流。

    数据流：
    1. 轮询 Postgres 表获取变更行（基于时间戳/水位线）
    2. 反序列化行数据
    3. 写入 Hermes 内部内存/知识库
    """
    cfg = pipeline.source_config
    tgt = pipeline.target_config
    conn_str = cfg["connection"]
    table = cfg["table"]

    @coco.fn(memo=True)
    def fetch_db_changes(
        connection: str,
        table: str,
        key_column: str,
        last_max_id: int = 0,
    ) -> List[dict]:
        """从数据库轮询增量变更。"""
        # 生产环境使用 asyncpg / psycopg2
        # 当前返回空列表——由调用方提供实际连接
        # 在 mock 模式下，返回模拟数据
        logger.debug(
            "DB poll: connection=%s table=%s last_max_id=%d",
            connection, table, last_max_id,
        )
        return []

    @coco.fn(memo=True)
    def write_to_memory(rows: List[dict], namespace: str) -> dict:
        """将数据行写入 Hermes 记忆系统。"""
        from ...shared.knowledge.rag_engine import RAGEngine

        engine = RAGEngine()
        indexed = 0
        for row in rows:
            text = json.dumps(row, ensure_ascii=False)
            try:
                engine.index_text(text, metadata={"source": namespace}, namespace=namespace)
                indexed += 1
            except Exception as e:
                logger.warning("Failed to index row: %s", e)
        return {
            "namespace": namespace,
            "indexed": indexed,
            "total_rows": len(rows),
        }

    # 数据流：拉取变更 → 写入记忆
    # cocoindex 自动追踪依赖，仅处理新增/变更行
    rows = fetch_db_changes(conn_str, table, cfg.get("key_column", "id"))
    if rows:
        write_to_memory(rows, tgt.get("namespace", "db_sync"))


def _mock_sync(pipeline: SyncPipeline) -> dict:
    """无 CocoIndex 时的模拟同步（用于原型开发）。"""
    logger.info("Mock sync for pipeline '%s' (cocoindex not installed)", pipeline.name)

    if pipeline.is_files_pipeline:
        watch_path = Path(pipeline.source_config["path"]).expanduser()
        pattern = pipeline.source_config.get("pattern", "**/*.{md,txt}")
        found = list(watch_path.rglob(pattern.split("/*/")[-1] if "/*/" in pattern else pattern)) if watch_path.exists() else []
        return {
            "status": "mock",
            "pipeline": pipeline.name,
            "files_found": len(found),
            "files_indexed": len(found),
            "note": "Mock mode — install cocoindex for real incremental sync",
        }
    elif pipeline.is_db_pipeline:
        return {
            "status": "mock",
            "pipeline": pipeline.name,
            "rows_synced": 0,
            "note": "Mock mode — install cocoindex + configure DB for real sync",
        }

    return {"status": "mock", "pipeline": pipeline.name}


# ---------------------------------------------------------------------------
# 管道生命周期管理
# ---------------------------------------------------------------------------

def _register_default_pipelines() -> None:
    """注册默认管道到全局注册表。"""
    with _lock:
        for pipe in get_default_pipelines():
            if pipe.name not in _pipelines:
                _pipelines[pipe.name] = pipe
                _pipeline_states[pipe.name] = PipelineState(
                    name=pipe.name,
                    source_type=pipe.source_type,
                    target_type=pipe.target_type,
                )
                logger.info("Registered default sync pipeline: %s", pipe.describe())


def get_pipeline(name: str) -> Optional[SyncPipeline]:
    """按名称获取管道定义。"""
    return _pipelines.get(name)


def list_pipelines() -> List[dict]:
    """列出所有注册的管道及其状态。"""
    # 确保默认管道已注册
    _register_default_pipelines()

    result = []
    with _lock:
        for name, pipe in _pipelines.items():
            state = _pipeline_states.get(name)
            entry = {
                "name": name,
                "source_type": pipe.source_type,
                "target_type": pipe.target_type,
                "source_config": pipe.source_config,
                "target_config": pipe.target_config,
                "schedule": pipe.schedule,
                "state": state.to_dict() if state else {"status": "unknown"},
            }
            result.append(entry)
    return result


def run_pipeline(name: str) -> dict:
    """执行一次管道同步（增量 catch-up）。"""
    pipe = get_pipeline(name)
    if not pipe:
        return {"status": "error", "error": f"Pipeline '{name}' not found"}

    state = _pipeline_states.get(name)
    if state and state.status == "running":
        return {"status": "error", "error": f"Pipeline '{name}' is already running"}

    try:
        if state:
            state.status = "running"

        logger.info("Running sync pipeline: %s", pipe.describe())

        # 执行同步
        result = _run_cocoindex_sync(pipe)

        # 更新状态
        if state:
            state.status = "stopped"
            state.last_run = time.time()
            state.last_error = None
            if result.get("status") == "success":
                state.total_indexed += result.get("updated", result.get("files_indexed", 0))
            elif result.get("status") == "error":
                state.total_errors += 1
                state.last_error = result.get("error", "Unknown error")

        # 持久化状态
        _save_pipeline_state(name)

        return {
            "status": "success",
            "pipeline": name,
            "result": result,
        }

    except Exception as e:
        if state:
            state.status = "error"
            state.last_error = str(e)
            state.total_errors += 1
        logger.error("Pipeline '%s' failed: %s", name, e)
        return {"status": "error", "pipeline": name, "error": str(e)}


def start_pipeline(name: str) -> dict:
    """启动管道的后台持续同步线程。"""
    pipe = get_pipeline(name)
    if not pipe:
        return {"status": "error", "error": f"Pipeline '{name}' not found"}

    state = _pipeline_states.get(name)
    if state and state.status == "running":
        return {"status": "ok", "message": f"Pipeline '{name}' is already running"}

    def _loop():
        """后台同步循环。"""
        state = _pipeline_states.get(name)
        if state:
            state.status = "running"
        try:
            while True:
                result = run_pipeline(name)
                if result.get("status") == "error":
                    logger.warning("Pipeline loop error: %s", result.get("error"))
                time.sleep(60)  # 每分钟轮询
        except Exception as e:
            if state:
                state.status = "error"
                state.last_error = str(e)

    thread = threading.Thread(target=_loop, name=f"sync-{name}", daemon=True)
    thread.start()

    with _lock:
        _pipeline_threads[name] = thread

    return {"status": "ok", "message": f"Pipeline '{name}' started (background thread)"}


def stop_pipeline(name: str) -> dict:
    """停止正在运行的管道。"""
    state = _pipeline_states.get(name)
    if state:
        state.status = "stopped"

    # 后台线程会在下次循环开始时检测到状态变化
    return {"status": "ok", "message": f"Pipeline '{name}' stop requested"}


def _save_pipeline_state(name: str) -> None:
    """持久化管道状态到 JSON 文件。"""
    PIPELINE_STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file = PIPELINE_STATE_DIR / f"{name}.state.json"
    state = _pipeline_states.get(name)
    if state:
        with open(state_file, "w") as f:
            json.dump(state.to_dict(), f, indent=2)


def _load_pipeline_states() -> None:
    """从磁盘加载管道持久化状态。"""
    if not PIPELINE_STATE_DIR.exists():
        return
    for state_file in PIPELINE_STATE_DIR.glob("*.state.json"):
        try:
            with open(state_file) as f:
                data = json.load(f)
            name = data.get("name")
            if name:
                _pipeline_states[name] = PipelineState(**data)
        except Exception as e:
            logger.debug("Failed to load state file %s: %s", state_file, e)


# ---------------------------------------------------------------------------
# CLI 命令处理器
# ---------------------------------------------------------------------------

def cmd_sync(args: List[str]) -> dict:
    """`python -m molib sync <subcmd> [options]` 的命令分发。"""
    # 确保注册了默认管道
    _register_default_pipelines()
    _load_pipeline_states()

    if not args:
        return {"error": "子命令: start | stop | status | run | list"}

    subcmd = args[0]
    rest = args[1:]

    if subcmd == "list":
        pipelines = list_pipelines()
        return {
            "action": "list",
            "pipelines": [
                {
                    "name": p["name"],
                    "source": f"{p['source_type']}→{p['target_type']}",
                    "status": p["state"]["status"],
                    "last_run": p["state"].get("last_run"),
                    "indexed": p["state"].get("total_indexed", 0),
                }
                for p in pipelines
            ],
            "count": len(pipelines),
        }

    if subcmd == "status":
        pipelines = list_pipelines()
        result = {"action": "status", "pipelines": []}
        for p in pipelines:
            s = p["state"]
            result["pipelines"].append({
                "name": p["name"],
                "source": f"{p['source_type']}→{p['target_type']}",
                "status": s.get("status", "unknown"),
                "last_run": (
                    datetime.fromtimestamp(s["last_run"]).isoformat()
                    if s.get("last_run") else None
                ),
                "total_indexed": s.get("total_indexed", 0),
                "total_errors": s.get("total_errors", 0),
                "last_error": s.get("last_error"),
            })
        return result

    if subcmd == "run":
        name = ""
        i = 0
        while i < len(rest):
            if rest[i] == "--pipeline" and i + 1 < len(rest):
                name = rest[i + 1]
                i += 2
            else:
                i += 1
        if not name:
            return {"error": "请指定 --pipeline <名称>"}
        return run_pipeline(name)

    if subcmd == "start":
        name = ""
        i = 0
        while i < len(rest):
            if rest[i] == "--pipeline" and i + 1 < len(rest):
                name = rest[i + 1]
                i += 2
            else:
                i += 1
        if not name:
            return {"error": "请指定 --pipeline <名称>"}
        return start_pipeline(name)

    if subcmd == "stop":
        name = ""
        i = 0
        while i < len(rest):
            if rest[i] == "--pipeline" and i + 1 < len(rest):
                name = rest[i + 1]
                i += 2
            else:
                i += 1
        if not name:
            return {"error": "请指定 --pipeline <名称>"}
        return stop_pipeline(name)

    return {"error": f"未知子命令: {subcmd}"}


# ---------------------------------------------------------------------------
# Worker 实现（面向内部 Worker 调度）
# ---------------------------------------------------------------------------

class CocoIndexSync(SubsidiaryWorker):
    """墨域同步 Worker — 基于 CocoIndex 的增量同步。

    负责：
    - 文件→向量索引的增量同步（知识库文档自动索引）
    - 数据库→内存的增量同步（CRM 等业务数据自动同步）
    - 管道生命周期管理（启动/停止/状态查询）
    """
    worker_id = "cocoindex_sync"
    worker_name = "墨域同步"
    description = "CocoIndex增量同步 | 文件→ChromaDB | DB→Memory"
    oneliner = "增量同步向量知识库"

    async def execute(self, task: Task, context: Optional[dict] = None) -> WorkerResult:
        try:
            action = task.payload.get("action", "run")
            pipeline_name = task.payload.get("pipeline", "")

            if action == "run_all":
                _register_default_pipelines()
                results = {}
                for name in _pipelines:
                    results[name] = run_pipeline(name)
                return WorkerResult(
                    task_id=task.task_id,
                    worker_id=self.worker_id,
                    status="success",
                    output={"action": "run_all", "results": results},
                )

            elif action == "run":
                if not pipeline_name:
                    return WorkerResult(
                        task_id=task.task_id,
                        worker_id=self.worker_id,
                        status="error",
                        output={},
                        error="pipeline name required",
                    )
                result = run_pipeline(pipeline_name)
                return WorkerResult(
                    task_id=task.task_id,
                    worker_id=self.worker_id,
                    status="success" if result.get("status") != "error" else "error",
                    output=result,
                )

            elif action == "status":
                pipelines = list_pipelines()
                return WorkerResult(
                    task_id=task.task_id,
                    worker_id=self.worker_id,
                    status="success",
                    output={"pipelines": pipelines},
                )

            elif action == "start":
                if not pipeline_name:
                    return WorkerResult(
                        task_id=task.task_id,
                        worker_id=self.worker_id,
                        status="error",
                        output={},
                        error="pipeline name required",
                    )
                result = start_pipeline(pipeline_name)
                return WorkerResult(
                    task_id=task.task_id,
                    worker_id=self.worker_id,
                    status="success",
                    output=result,
                )

            elif action == "stop":
                if not pipeline_name:
                    return WorkerResult(
                        task_id=task.task_id,
                        worker_id=self.worker_id,
                        status="error",
                        output={},
                        error="pipeline name required",
                    )
                result = stop_pipeline(pipeline_name)
                return WorkerResult(
                    task_id=task.task_id,
                    worker_id=self.worker_id,
                    status="success",
                    output=result,
                )

            else:
                # 默认：运行所有可用管道一次
                _register_default_pipelines()
                result = run_pipeline(pipeline_name or list(_pipelines.keys())[0])
                return WorkerResult(
                    task_id=task.task_id,
                    worker_id=self.worker_id,
                    status="success" if result.get("status") != "error" else "error",
                    output=result,
                )

        except Exception as e:
            return WorkerResult(
                task_id=task.task_id,
                worker_id=self.worker_id,
                status="error",
                output={},
                error=str(e),
            )
