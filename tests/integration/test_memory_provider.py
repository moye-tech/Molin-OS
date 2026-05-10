#!/usr/bin/env python3
"""
测试分层记忆提供者
验证HierarchicalMemoryProvider是否能正确初始化和工作
"""

import sys
import os
import asyncio

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hermes_fusion.providers.memory_provider import HierarchicalMemoryProvider


async def test_memory_provider_initialization():
    """测试记忆提供者初始化"""
    print("测试记忆提供者初始化...")

    # 创建配置
    config = {
        'sqlite': {
            'enabled': True,
            'db_path': 'data/sqlite/test_memory.db'
        },
        'qdrant': {
            'enabled': True,
            'host': 'localhost',
            'port': 6333
        },
        'redis': {
            'enabled': True,
            'host': 'localhost',
            'port': 6379
        },
        'supermemory': {
            'enabled': False
        }
    }

    provider = HierarchicalMemoryProvider(config)

    # 初始化
    await provider.initialize()
    print(f"✓ 初始化完成，提供者: {list(provider.providers.keys())}")

    # 获取统计信息
    stats = await provider.get_stats()
    print(f"✓ 统计信息: {stats}")

    return True


async def test_memory_store_retrieve():
    """测试记忆存储和检索"""
    print("\n测试记忆存储和检索...")

    config = {
        'sqlite': {'enabled': True},
        'qdrant': {'enabled': True},
        'redis': {'enabled': True},
        'supermemory': {'enabled': False}
    }

    provider = HierarchicalMemoryProvider(config)
    await provider.initialize()

    # 测试不同场景的存储
    test_cases = [
        {
            'name': '事务性记忆',
            'context': {'scenario': 'transactional', 'user_id': 'test_user'},
            'data': {'type': 'event', 'action': 'test_action', 'result': 'success'}
        },
        {
            'name': '语义搜索记忆',
            'context': {'scenario': 'semantic_search', 'user_id': 'test_user'},
            'data': '这是一个测试文本内容，用于语义搜索'
        },
        {
            'name': '缓存记忆',
            'context': {'scenario': 'cache', 'user_id': 'test_user', 'ttl': 60},
            'data': {'key': 'value', 'expires_in': '60s'}
        }
    ]

    for test in test_cases:
        print(f"\n测试: {test['name']}")

        # 存储
        record_id = await provider.store(test['context'], test['data'])
        print(f"✓ 存储成功，记录ID: {record_id}")

        # 检索
        results = await provider.retrieve(test['context'], query=record_id)
        print(f"✓ 检索结果: {len(results)}条记录")

        if results:
            print(f"  第一条记录: {results[0].get('content')}")

    return True


async def test_memory_search():
    """测试记忆搜索"""
    print("\n测试记忆搜索...")

    config = {
        'sqlite': {'enabled': True},
        'qdrant': {'enabled': True},
        'redis': {'enabled': True},
        'supermemory': {'enabled': False}
    }

    provider = HierarchicalMemoryProvider(config)
    await provider.initialize()

    # 存储一些测试数据
    context = {'scenario': 'semantic_search', 'user_id': 'test_user'}
    test_data = [
        '机器学习模型训练',
        '深度学习神经网络',
        '自然语言处理技术',
        '计算机视觉应用',
        '强化学习算法'
    ]

    for i, text in enumerate(test_data):
        record_id = await provider.store(context, text)
        print(f"存储测试数据 {i+1}: {text[:20]}...")

    # 搜索
    query = '机器学习'
    results = await provider.search(context, query, limit=3)
    print(f"\n搜索查询: '{query}'")
    print(f"搜索结果: {len(results)}条记录")

    for i, result in enumerate(results):
        print(f"  结果 {i+1}: {result.get('content', 'N/A')[:30]}... (分数: {result.get('score', 0)})")

    return True


async def main():
    """主测试函数"""
    print("=" * 60)
    print("分层记忆提供者测试")
    print("=" * 60)

    tests = [
        ("初始化测试", test_memory_provider_initialization),
        ("存储检索测试", test_memory_store_retrieve),
        ("搜索测试", test_memory_search)
    ]

    passed_tests = 0
    total_tests = len(tests)

    for test_name, test_func in tests:
        print(f"\n[测试] {test_name}")
        try:
            if await test_func():
                print(f"✓ {test_name} - 通过")
                passed_tests += 1
            else:
                print(f"✗ {test_name} - 失败")
        except Exception as e:
            print(f"✗ {test_name} - 异常: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"测试结果: {passed_tests}/{total_tests} 通过")

    if passed_tests == total_tests:
        print("✓ 所有记忆提供者测试通过!")
        return True
    else:
        print("✗ 部分测试失败，请检查实现")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)