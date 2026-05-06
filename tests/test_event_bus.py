"""墨麟OS — 事件总线单元测试"""
import pytest
import asyncio
import time
from molib.shared.event_bus import FileEventBus


@pytest.mark.asyncio
async def test_publish_and_poll():
    """发布事件后能轮询到"""
    bus = FileEventBus()
    eid = await bus.publish("content_published", {"title": "测试文章"})
    assert eid.startswith("evt-")
    
    events = await bus.poll(since=0)
    assert len(events) >= 1
    assert events[0]["type"] == "content_published"
    assert events[0]["payload"]["title"] == "测试文章"


@pytest.mark.asyncio
async def test_subscribe():
    """订阅制回调"""
    bus = FileEventBus()
    received = []
    
    async def handler(event):
        received.append(event)
    
    await bus.subscribe("test_event", handler)
    await bus.publish("test_event", {"data": 123})
    
    assert len(received) == 1
    assert received[0]["type"] == "test_event"


@pytest.mark.asyncio
async def test_unsubscribe():
    """取消订阅后不再收到"""
    bus = FileEventBus()
    received = []
    
    async def handler(event):
        received.append(event)
    
    await bus.subscribe("test", handler)
    await bus.unsubscribe("test", handler)
    await bus.publish("test", {})
    
    assert len(received) == 0


@pytest.mark.asyncio
async def test_filtered_poll():
    """按事件类型过滤轮询"""
    bus = FileEventBus()
    await bus.publish("type_a", {"a": 1})
    await bus.publish("type_b", {"b": 2})
    
    a_events = await bus.poll(event_type="type_a", since=0)
    assert len(a_events) == 1
    assert a_events[0]["type"] == "type_a"


@pytest.mark.asyncio
async def test_cleanup():
    """清理过期事件"""
    bus = FileEventBus()
    await bus.publish("test", {})
    before = len(await bus.poll(since=0))
    assert before >= 1
    
    cleaned = await bus.cleanup(older_than=0)
    assert cleaned >= 1
    
    after = len(await bus.poll(since=0))
    assert after == 0
