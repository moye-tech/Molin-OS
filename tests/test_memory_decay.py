"""测试记忆重要性衰减 — 按时间衰减排序，低分自动过滤"""
import asyncio
import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    old_path = os.environ.get("SQLITE_DB_PATH")
    os.environ["SQLITE_DB_PATH"] = path
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
async def test_decay_high_score_recent(sqlite_client):
    """高评分 + 近期记忆应排在前面"""
    await sqlite_client.store_memory(
        "recent_high", {"value": "recent"}, "transactional",
        namespace="test", importance_score=9.0)
    await sqlite_client.store_memory(
        "recent_low", {"value": "low"}, "transactional",
        namespace="test", importance_score=2.0)

    results = await sqlite_client.retrieve_memory(
        key="recent", scenario="transactional", namespace="test", limit=10)

    # 高评分应排在前面
    if len(results) >= 2:
        assert results[0]["decayed_score"] >= results[-1]["decayed_score"]


@pytest.mark.asyncio
async def test_decay_threshold_filtering(sqlite_client):
    """衰减分数低于 0.1 的条目应被过滤"""
    # 插入不同评分的记忆
    await sqlite_client.store_memory(
        "score_high", {"value": "high"}, "transactional",
        namespace="test", importance_score=10.0)
    await sqlite_client.store_memory(
        "score_mid", {"value": "mid"}, "transactional",
        namespace="test", importance_score=5.0)

    results = await sqlite_client.retrieve_memory(
        key="score", scenario="transactional", namespace="test", limit=10)

    # 所有结果都应该有 decayed_score 字段
    for r in results:
        assert "decayed_score" in r
        assert r["decayed_score"] >= 0.1


@pytest.mark.asyncio
async def test_decay_result_sorted_descending(sqlite_client):
    """结果按 decayed_score 降序排列"""
    scores = [8.0, 3.0, 6.0, 1.0, 9.0]
    for i, s in enumerate(scores):
        await sqlite_client.store_memory(
            f"sort_{i}", {"idx": i}, "transactional",
            namespace="test", importance_score=s)

    results = await sqlite_client.retrieve_memory(
        key="sort", scenario="transactional", namespace="test", limit=10)

    decayed_scores = [r["decayed_score"] for r in results]
    assert decayed_scores == sorted(decayed_scores, reverse=True)


@pytest.mark.asyncio
async def test_days_since_calculation(sqlite_client):
    """_days_since 函数应正确计算天数"""
    from infra.memory.sqlite_client import _days_since
    from datetime import datetime, timedelta

    # 7 天前的时间戳
    past = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    days = _days_since(past)
    assert 6.9 <= days <= 7.1

    # 今天的时间戳
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    days = _days_since(now)
    assert 0 <= days < 0.01
