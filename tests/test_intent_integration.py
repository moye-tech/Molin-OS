#!/usr/bin/env python3
"""
测试CEO与意图处理器集成的脚本
"""

import asyncio
import sys
import os
import tempfile

# 设置临时数据库文件路径
temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
temp_db.close()
os.environ['SQLITE_DB_PATH'] = temp_db.name

sys.path.insert(0, '.')

from core.ceo.ceo import MolinCEO

async def test_intent_processor():
    """测试意图处理器集成"""
    print("=== 测试CEO与意图处理器集成 ===\n")

    ceo = MolinCEO(daily_budget_cny=50.0)

    # 测试用例1: 简单问候语（应该直接响应）
    print("测试1: 简单问候语")
    print("输入: '你好'")
    result = await ceo.run_async("你好")
    print(f"结果: {result.get('decision')}")
    print(f"响应: {result.get('message', 'N/A')}")
    print()

    # 测试用例2: 需要补充信息（广告任务但缺少预算）
    print("测试2: 广告任务（缺少预算）")
    print("输入: '我想投放广告'")
    result = await ceo.run_async("我想投放广告")
    print(f"结果: {result.get('decision')}")
    print(f"问题: {result.get('questions', [])}")
    print(f"目标机构: {result.get('target_agency')}")
    print()

    # 测试用例3: 完整信息广告任务
    print("测试3: 完整信息广告任务")
    print("输入: '我想投放广告，预算5000元，时间一周，目标收入20000元'")
    result = await ceo.run_async(
        "我想投放广告，预算5000元，时间一周，目标收入20000元",
        budget=5000,
        timeline="一周",
        target_revenue=20000
    )
    print(f"结果: {result.get('decision')}")
    print(f"意图类型: {result.get('intent_processing', {}).get('intent_type', 'N/A')}")
    print(f"目标机构: {result.get('intent_processing', {}).get('target_agency', 'N/A')}")
    print()

    # 测试用例4: 状态查询
    print("测试4: 状态查询")
    print("输入: '查询系统状态'")
    result = await ceo.run_async("查询系统状态")
    print(f"结果: {result.get('decision')}")
    print(f"响应: {result.get('message', 'N/A')}")
    print()

    # 测试用例5: 感谢语
    print("测试5: 感谢语")
    print("输入: '谢谢'")
    result = await ceo.run_async("谢谢")
    print(f"结果: {result.get('decision')}")
    print(f"响应: {result.get('message', 'N/A')}")
    print()

    # 测试用例6: 告别语
    print("测试6: 告别语")
    print("输入: '再见'")
    result = await ceo.run_async("再见")
    print(f"结果: {result.get('decision')}")
    print(f"响应: {result.get('message', 'N/A')}")
    print()

    print("=== 所有测试完成 ===")

if __name__ == "__main__":
    try:
        asyncio.run(test_intent_processor())
    finally:
        # 清理临时数据库文件
        if os.path.exists(temp_db.name):
            os.unlink(temp_db.name)