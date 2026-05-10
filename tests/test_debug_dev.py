#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from core.managers.manager_dispatcher import get_dispatcher
from agencies.base import Task

async def test():
    dispatcher = await get_dispatcher()
    dev_manager = dispatcher.get_manager("dev_manager")
    print(f"Dev manager: {dev_manager}")
    print(f"Claude enabled: {dev_manager.claude_enabled}")

    task = Task(
        task_id="test_debug",
        task_type="code",
        payload={"description": "simple test"},
        priority=5,
        requester="debug"
    )

    print("Calling delegate_task...")
    try:
        result = await dev_manager.delegate_task(task)
        print(f"Result: {result}")
        print(f"Result type: {type(result)}")
        if hasattr(result, 'status'):
            print(f"Status: {result.status}")
        if hasattr(result, 'error'):
            print(f"Error: {result.error}")
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())