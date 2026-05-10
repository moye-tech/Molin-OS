#!/usr/bin/env python3
"""
测试数据流管理器基本功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from tests.unit.test_7layer_dataflow import test_dataflow_manager_basic

async def main():
    print("运行数据流管理器基本功能测试...")
    result = await test_dataflow_manager_basic()
    print(f"\n测试完成，结果: {result}")
    return result

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)