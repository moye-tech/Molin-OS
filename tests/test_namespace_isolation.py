"""测试 namespace 隔离 — 各子公司数据互不干扰"""
import asyncio
import json
import os
import sys
import tempfile
import time

import pytest

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def temp_db():
    """创建临时 SQLite DB，避免污染正式数据"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    old_path = os.environ.get("SQLITE_DB_PATH")
    os.environ["SQLITE_DB_PATH"] = path
    # 需要重新导入以使用新路径
    yield path
    if old_path:
        os.environ["SQLITE_DB_PATH"] = old_path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
async def sqlite_client(temp_db):
    from infra.memory.sqlite_client import SQLiteClient
    client = SQLiteClient()
    await client.init()
    return client


@pytest.mark.asyncio
async def test_namespace_isolation_store_retrieve(sqlite_client):
    """不同 namespace 存储和检索应相互隔离"""
    await sqlite_client.store_memory("key1", {"data": "edu_data"}, "transactional", namespace="edu")
    await sqlite_client.store_memory("key2", {"data": "crm_data"}, "transactional", namespace="crm")
    await sqlite_client.store_memory("key3", {"data": "shop_data"}, "transactional", namespace="shop")

    edu_results = await sqlite_client.retrieve_memory(key="key", scenario="transactional", namespace="edu")
    crm_results = await sqlite_client.retrieve_memory(key="key", scenario="transactional", namespace="crm")
    shop_results = await sqlite_client.retrieve_memory(key="key", scenario="transactional", namespace="shop")

    assert len(edu_results) == 1
    assert edu_results[0]["data"] == {"data": "edu_data"}

    assert len(crm_results) == 1
    assert crm_results[0]["data"] == {"data": "crm_data"}

    assert len(shop_results) == 1
    assert shop_results[0]["data"] == {"data": "shop_data"}


@pytest.mark.asyncio
async def test_cross_namespace_leak(sqlite_client):
    """查询 edu namespace 不应返回 crm 的数据"""
    await sqlite_client.store_memory("edu_secret", {"value": "edu_only"}, "transactional", namespace="edu")
    await sqlite_client.store_memory("crm_secret", {"value": "crm_only"}, "transactional", namespace="crm")

    edu_results = await sqlite_client.retrieve_memory(key="secret", scenario="transactional", namespace="edu")

    assert len(edu_results) == 1
    assert edu_results[0]["key"] == "edu_secret"
    assert "crm_secret" not in [r["key"] for r in edu_results]


@pytest.mark.asyncio
async def test_knowledge_namespace_isolation(sqlite_client):
    """知识库搜索按 namespace 隔离"""
    await sqlite_client.add_knowledge_with_namespace(
        "edu课程", "教育内容", namespace="edu", source="test", tags=["edu"])
    await sqlite_client.add_knowledge_with_namespace(
        "crm策略", "私域内容", namespace="crm", source="test", tags=["crm"])

    edu_results = await sqlite_client.search_knowledge_by_namespace("教育", namespace="edu")
    crm_results = await sqlite_client.search_knowledge_by_namespace("教育", namespace="crm")

    assert len(edu_results) >= 1
    assert len(crm_results) == 0


@pytest.mark.asyncio
async def test_multiple_items_same_namespace(sqlite_client):
    """同一 namespace 下多条数据应正常检索"""
    for i in range(5):
        await sqlite_client.store_memory(
            f"edu_item_{i}", {"idx": i}, "transactional", namespace="edu")

    results = await sqlite_client.retrieve_memory(
        key="edu_item", scenario="transactional", namespace="edu", limit=10)

    assert len(results) == 5
    idx_values = [r["data"]["idx"] for r in results]
    assert set(idx_values) == {0, 1, 2, 3, 4}
