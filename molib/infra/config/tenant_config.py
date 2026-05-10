"""多租户配置 — 按 tenant_id 隔离存储路径"""
import os

TENANT_ID = os.getenv("TENANT_ID", "default")
STORAGE_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "storage")


def get_tenant_path(*parts: str) -> str:
    """获取租户隔离的路径：storage/{tenant_id}/..."""
    return os.path.join(STORAGE_ROOT, TENANT_ID, *parts)


def get_sqlite_path() -> str:
    return get_tenant_path("molin.db")


def get_qdrant_path() -> str:
    return get_tenant_path("qdrant")


def get_sop_path() -> str:
    return get_tenant_path("sop")


def get_log_path() -> str:
    return get_tenant_path("logs")


def get_kg_db_path() -> str:
    return get_tenant_path("knowledge_graph.db")


def ensure_tenant_dirs():
    """确保租户目录存在"""
    for path_fn in [get_sqlite_path, get_qdrant_path, get_sop_path, get_log_path]:
        path = path_fn()
        os.makedirs(os.path.dirname(path) if path.endswith("/") else path, exist_ok=True)
