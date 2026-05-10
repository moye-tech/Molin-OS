#!/usr/bin/env python3
"""
测试新版分层记忆提供者
验证基于MemoryManager的实现
"""

import sys
import os
import asyncio

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_imports():
    """测试导入"""
    print("测试导入...")

    try:
        from hermes_fusion.providers.memory_provider import HierarchicalMemoryProvider
        print("✓ HierarchicalMemoryProvider导入成功")

        # 尝试导入MemoryManager
        from memory.memory_manager import MemoryManager
        print("✓ MemoryManager导入成功")

        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_provider_initialization():
    """测试提供者初始化"""
    print("\n测试提供者初始化...")

    from hermes_fusion.providers.memory_provider import HierarchicalMemoryProvider

    config = {
        'sqlite': {'enabled': True},
        'qdrant': {'enabled': True},
        'redis': {'enabled': False},
        'supermemory': {'enabled': False}
    }

    try:
        provider = HierarchicalMemoryProvider(config)
        await provider.initialize()
        print(f"✓ 提供者初始化成功")

        stats = await provider.get_stats()
        print(f"✓ 统计信息: {stats}")

        return True
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_memory_store():
    """测试记忆存储"""
    print("\n测试记忆存储...")

    from hermes_fusion.providers.memory_provider import HierarchicalMemoryProvider

    config = {
        'sqlite': {'enabled': True},
        'qdrant': {'enabled': True},
        'redis': {'enabled': False},
        'supermemory': {'enabled': False}
    }

    provider = HierarchicalMemoryProvider(config)
    await provider.initialize()

    # 测试不同场景的存储
    test_cases = [
        {
            'name': '事务性记忆',
            'context': {'scenario': 'transactional', 'user_id': 'test_user_1'},
            'data': {'type': 'event', 'action': 'login', 'result': 'success'}
        },
        {
            'name': '语义搜索记忆',
            'context': {'scenario': 'semantic_search', 'user_id': 'test_user_2'},
            'data': '机器学习模型训练的最佳实践'
        }
    ]

    for test in test_cases:
        print(f"测试: {test['name']}")
        try:
            record_id = await provider.store(test['context'], test['data'])
            print(f"✓ 存储成功，记录ID: {record_id}")
        except Exception as e:
            print(f"✗ 存储失败: {e}")
            return False

    return True

async def test_memory_retrieve():
    """测试记忆检索"""
    print("\n测试记忆检索...")

    from hermes_fusion.providers.memory_provider import HierarchicalMemoryProvider

    config = {
        'sqlite': {'enabled': True},
        'qdrant': {'enabled': True},
        'redis': {'enabled': False},
        'supermemory': {'enabled': False}
    }

    provider = HierarchicalMemoryProvider(config)
    await provider.initialize()

    # 先存储一些测试数据
    context = {'scenario': 'transactional', 'user_id': 'test_user_retrieve'}
    data = {'type': 'test', 'message': '这是检索测试数据'}

    try:
        record_id = await provider.store(context, data)
        print(f"存储测试数据，记录ID: {record_id}")

        # 按ID检索
        results = await provider.retrieve(context, record_id, limit=5)
        print(f"按ID检索结果: {len(results)}条记录")

        if results:
            print(f"第一条记录内容: {results[0].get('content')}")

        # 搜索查询
        search_context = {'scenario': 'semantic_search'}
        search_results = await provider.search(search_context, '机器学习', limit=3)
        print(f"语义搜索结果: {len(search_results)}条记录")

        return True
    except Exception as e:
        print(f"✗ 检索失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("=" * 60)
    print("新版分层记忆提供者测试")
    print("=" * 60)

    tests = [
        ("导入测试", test_imports),
        ("初始化测试", test_provider_initialization),
        ("存储测试", test_memory_store),
        ("检索测试", test_memory_retrieve)
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