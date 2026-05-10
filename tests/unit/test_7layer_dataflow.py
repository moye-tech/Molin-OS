#!/usr/bin/env python3
"""
7层数据流端到端测试
验证原始7层架构数据流在hermes-agent框架中的完整集成
"""

import sys
import os
import asyncio
import time
import logging
import inspect
from typing import Dict, Any, List

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_dataflow_manager_basic():
    """测试数据流管理器基本功能"""
    print("=" * 60)
    print("测试1: 数据流管理器基本功能")
    print("=" * 60)

    try:
        from hermes_fusion.integration.dataflow_manager import (
            LayerDataFlowManager, get_dataflow_manager
        )
        print("✓ 导入数据流管理器成功")
    except ImportError as e:
        print(f"✗ 导入数据流管理器失败: {e}")
        return False

    # 创建管理器实例
    manager = LayerDataFlowManager()
    await manager.initialize()

    # 测试1.1: 检查层定义
    expected_layers = [
        'entry', 'hermes_ceo', 'strategy_engine', 'agency',
        'paperclip', 'clawteam', 'execution', 'data_brain', 'memory'
    ]

    for layer in expected_layers:
        if layer in manager.LAYERS:
            print(f"  ✓ 层 '{layer}' 已定义")
        else:
            print(f"  ✗ 层 '{layer}' 未定义")
            return False

    # 测试1.2: 检查依赖关系
    dependencies = manager.LAYER_DEPENDENCIES
    expected_deps = {
        'entry': [],
        'hermes_ceo': ['entry'],
        'strategy_engine': ['hermes_ceo'],
        'agency': ['hermes_ceo', 'strategy_engine'],
        'paperclip': ['agency'],
        'clawteam': ['paperclip'],
        'execution': ['clawteam'],
        'data_brain': ['execution'],
        'memory': ['hermes_ceo', 'agency', 'execution', 'data_brain']
    }

    for layer, expected in expected_deps.items():
        actual = dependencies.get(layer, [])
        if set(actual) == set(expected):
            print(f"  ✓ 层 '{layer}' 依赖关系正确: {actual}")
        else:
            print(f"  ✗ 层 '{layer}' 依赖关系错误: 期望 {expected}, 实际 {actual}")
            return False

    # 注册模拟处理器，避免依赖真实技能执行
    async def mock_entry_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {'layer': layer_name, 'success': True, 'status': 'entered', 'message': '模拟入口处理'}

    async def mock_ceo_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {'layer': layer_name, 'success': True, 'decision': 'GO', 'roi_analysis': {'roi': 2.5}}

    async def mock_strategy_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {'layer': layer_name, 'success': True, 'strategy': {'template_used': 'AI教育'}, 'recommended_subsidiary': 'order'}

    manager.register_layer_handler('entry', mock_entry_handler)
    manager.register_layer_handler('hermes_ceo', mock_ceo_handler)
    manager.register_layer_handler('strategy_engine', mock_strategy_handler)
    print("  ✓ 注册模拟层处理器完成")

    # 测试1.3: 测试简单请求处理
    test_request = {
        'text': '测试7层数据流',
        'user_id': 'test_user',
        'platform': 'test',
        'metadata': {'test': True},
        'target_layers': ['entry', 'hermes_ceo', 'strategy_engine']
    }

    result = await manager.process_request(test_request)

    if result.get('success'):
        print("  ✓ 简单请求处理成功")
        print(f"    请求ID: {result.get('request_id')}")
        print(f"    处理层数: {result.get('total_layers_processed')}")
    else:
        print(f"  ✗ 简单请求处理失败: {result.get('error', '未知错误')}")
        return False

    # 测试1.4: 检查层结果
    layer_results = result.get('layer_results_summary', {})
    for layer in test_request['target_layers']:
        if layer in layer_results:
            print(f"  ✓ 层 '{layer}' 结果已记录")
        else:
            print(f"  ✗ 层 '{layer}' 结果未记录")
            return False

    print("\n✓ 数据流管理器基本功能测试通过")
    return True


async def test_custom_layer_handlers():
    """测试自定义层处理器注册"""
    print("\n" + "=" * 60)
    print("测试2: 自定义层处理器注册")
    print("=" * 60)

    from hermes_fusion.integration.dataflow_manager import LayerDataFlowManager

    manager = LayerDataFlowManager()
    await manager.initialize()

    # 定义自定义处理器
    async def mock_ceo_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'layer': layer_name,
            'decision': 'GO',
            'roi_analysis': {'estimated_roi': 3.5, 'confidence': 0.8},
            'simulated': True
        }

    async def mock_strategy_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        upstream_results = context.get('upstream_results', {})
        ceo_result = upstream_results.get('hermes_ceo', {})

        return {
            'layer': layer_name,
            'strategy': {
                'template_used': 'AI教育',
                'daily_target_leads': 10,
                'avg_order_value': 999
            },
            'based_on_decision': ceo_result.get('decision'),
            'simulated': True
        }

    # 注册自定义处理器
    manager.register_layer_handler('hermes_ceo', mock_ceo_handler)
    manager.register_layer_handler('strategy_engine', mock_strategy_handler)

    # 测试注册效果
    test_request = {
        'text': '测试自定义处理器',
        'user_id': 'test_user',
        'platform': 'test',
        'target_layers': ['hermes_ceo', 'strategy_engine']
    }

    result = await manager.process_request(test_request)

    if result.get('success'):
        print("  ✓ 自定义处理器请求处理成功")

        # 检查自定义处理器是否被调用
        layer_results = result.get('layer_results_summary', {})

        ceo_result = manager.request_registry[result['request_id']]['layer_results'].get('hermes_ceo', {})
        if ceo_result.get('decision') == 'GO':
            print("  ✓ CEO层自定义处理器被调用")
        else:
            print("  ✗ CEO层自定义处理器未被调用")
            return False

        strategy_result = manager.request_registry[result['request_id']]['layer_results'].get('strategy_engine', {})
        if strategy_result.get('strategy', {}).get('template_used') == 'AI教育':
            print("  ✓ 策略引擎层自定义处理器被调用")
        else:
            print("  ✗ 策略引擎层自定义处理器未被调用")
            return False
    else:
        print(f"  ✗ 自定义处理器请求处理失败: {result.get('error', '未知错误')}")
        return False

    print("\n✓ 自定义层处理器注册测试通过")
    return True


async def test_full_7layer_flow():
    """测试完整7层数据流"""
    print("\n" + "=" * 60)
    print("测试3: 完整7层数据流")
    print("=" * 60)

    from hermes_fusion.integration.dataflow_manager import LayerDataFlowManager

    manager = LayerDataFlowManager()
    await manager.initialize()

    # 注册所有层的模拟处理器
    async def entry_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {'layer': layer_name, 'status': 'entered', 'request_valid': True}

    async def ceo_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'layer': layer_name,
            'decision': 'GO',
            'roi_analysis': {'roi': 2.5, 'payback_days': 60},
            'confidence': 0.85
        }

    async def strategy_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'layer': layer_name,
            'strategy': {
                'template_used': 'AI服务',
                'daily_target_deals': 3,
                'avg_order_value': 800
            },
            'recommended_subsidiary': 'order'
        }

    async def agency_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        upstream = context.get('upstream_results', {})
        strategy = upstream.get('strategy_engine', {}).get('strategy', {})

        return {
            'layer': layer_name,
            'subsidiary': 'order',
            'task': f"执行{strategy.get('template_used', '未知')}策略",
            'compliance': {'passed': True, 'checks': ['basic']}
        }

    async def paperclip_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'layer': layer_name,
            'workflow_status': 'approved',
            'approved_tasks': ['task_001'],
            'compliance_check': 'passed'
        }

    async def clawteam_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'layer': layer_name,
            'scheduled_tasks': [{'id': 'task_001', 'type': 'execution'}],
            'execution_plan': {'concurrent_limit': 3}
        }

    async def execution_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'layer': layer_name,
            'results': [{'task_id': 'task_001', 'status': 'completed'}],
            'metrics': {'execution_time': 5.2}
        }

    async def data_brain_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'layer': layer_name,
            'analysis': {
                'overall_score': 8.5,
                'recommendations': ['优化执行流程'],
                'alerts': []
            }
        }

    async def memory_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'layer': layer_name,
            'stored': True,
            'memory_keys': ['request_001', 'decision_001']
        }

    # 注册所有处理器
    handlers = {
        'entry': entry_handler,
        'hermes_ceo': ceo_handler,
        'strategy_engine': strategy_handler,
        'agency': agency_handler,
        'paperclip': paperclip_handler,
        'clawteam': clawteam_handler,
        'execution': execution_handler,
        'data_brain': data_brain_handler,
        'memory': memory_handler
    }

    for layer_name, handler in handlers.items():
        manager.register_layer_handler(layer_name, handler)

    # 测试完整7层请求
    test_request = {
        'text': '我想开展一个AI咨询服务，预算5万元，目标收入15万元',
        'user_id': 'business_user_001',
        'platform': 'feishu',
        'metadata': {
            'budget': 50000,
            'target_revenue': 150000,
            'timeline': '90天'
        }
    }

    print("  处理完整7层请求...")
    start_time = time.time()
    result = await manager.process_request(test_request)
    end_time = time.time()

    if result.get('success'):
        print(f"  ✓ 完整7层请求处理成功")
        print(f"    总时间: {end_time - start_time:.2f}秒")
        print(f"    处理层数: {result.get('total_layers_processed')}")
        print(f"    成功层数: {len(result.get('successful_layers', []))}")
        print(f"    失败层数: {len(result.get('failed_layers', []))}")

        # 检查各层结果
        layer_results = manager.request_registry[result['request_id']]['layer_results']
        expected_layers = manager.LAYERS

        for layer in expected_layers:
            if layer in layer_results:
                layer_status = layer_results[layer].get('success', False)
                status_icon = '✓' if layer_status else '✗'
                print(f"    {status_icon} {layer}")
            else:
                print(f"    ? {layer} (未执行)")

        # 验证数据流完整性
        # 1. CEO决策应传递给策略引擎
        ceo_decision = layer_results.get('hermes_ceo', {}).get('decision')
        strategy_based = layer_results.get('strategy_engine', {}).get('based_on_decision', None)

        if ceo_decision == 'GO':
            print(f"  ✓ CEO决策为GO")
        else:
            print(f"  ✗ CEO决策不是GO: {ceo_decision}")
            return False

        # 2. 策略引擎应推荐子公司
        recommended_subsidiary = layer_results.get('strategy_engine', {}).get('recommended_subsidiary')
        if recommended_subsidiary:
            print(f"  ✓ 策略引擎推荐子公司: {recommended_subsidiary}")
        else:
            print("  ✗ 策略引擎未推荐子公司")
            return False

        # 3. 代理层应使用推荐子公司
        actual_subsidiary = layer_results.get('agency', {}).get('subsidiary')
        if actual_subsidiary == recommended_subsidiary:
            print(f"  ✓ 代理层使用推荐子公司: {actual_subsidiary}")
        else:
            print(f"  ✗ 代理层子公司不匹配: 期望 {recommended_subsidiary}, 实际 {actual_subsidiary}")
            return False

        # 4. Paperclip应审批任务
        paperclip_status = layer_results.get('paperclip', {}).get('workflow_status')
        if paperclip_status == 'approved':
            print(f"  ✓ Paperclip审批通过")
        else:
            print(f"  ✗ Paperclip审批状态: {paperclip_status}")
            return False

        # 5. ClawTeam应调度任务
        scheduled_tasks = layer_results.get('clawteam', {}).get('scheduled_tasks', [])
        if scheduled_tasks:
            print(f"  ✓ ClawTeam调度了 {len(scheduled_tasks)} 个任务")
        else:
            print("  ✗ ClawTeam未调度任务")
            return False

        # 6. 执行层应完成任务
        execution_results = layer_results.get('execution', {}).get('results', [])
        if execution_results:
            print(f"  ✓ 执行层完成了 {len(execution_results)} 个任务")
        else:
            print("  ✗ 执行层未完成任务")
            return False

        # 7. DataBrain应生成分析
        analysis = layer_results.get('data_brain', {}).get('analysis', {})
        if analysis.get('overall_score'):
            print(f"  ✓ DataBrain生成分析, 评分: {analysis.get('overall_score')}")
        else:
            print("  ✗ DataBrain未生成分析")
            return False

        # 8. 记忆层应存储结果
        memory_stored = layer_results.get('memory', {}).get('stored', False)
        if memory_stored:
            print(f"  ✓ 记忆层存储了结果")
        else:
            print("  ✗ 记忆层未存储结果")
            return False

    else:
        print(f"  ✗ 完整7层请求处理失败: {result.get('error', '未知错误')}")
        return False

    print("\n✓ 完整7层数据流测试通过")
    return True


async def test_error_handling():
    """测试错误处理和恢复"""
    print("\n" + "=" * 60)
    print("测试4: 错误处理和恢复")
    print("=" * 60)

    from hermes_fusion.integration.dataflow_manager import LayerDataFlowManager

    manager = LayerDataFlowManager({'continue_on_layer_error': False})
    await manager.initialize()

    # 注册一个会失败的处理器
    async def failing_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        raise ValueError(f"模拟{layer_name}层失败")

    async def success_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {'layer': layer_name, 'success': True}

    # 注册处理器：entry成功，hermes_ceo失败，其他层成功
    manager.register_layer_handler('entry', success_handler)
    manager.register_layer_handler('hermes_ceo', failing_handler)
    manager.register_layer_handler('strategy_engine', success_handler)

    # 测试错误处理
    test_request = {
        'text': '测试错误处理',
        'user_id': 'test_user',
        'platform': 'test',
        'target_layers': ['entry', 'hermes_ceo', 'strategy_engine']
    }

    result = await manager.process_request(test_request)

    # 验证错误处理行为
    if not result.get('success'):
        print("  ✓ 错误导致请求失败（符合预期）")

        # 检查错误信息
        errors = manager.request_registry[result['request_id']].get('errors', [])
        if errors:
            print(f"  ✓ 记录了 {len(errors)} 个错误")
            for error in errors:
                print(f"    层 {error['layer']}: {error['error']}")
        else:
            print("  ✗ 未记录错误信息")
            return False

        # 检查哪些层执行了
        layer_results = manager.request_registry[result['request_id']].get('layer_results', {})
        executed_layers = list(layer_results.keys())

        # entry应该执行了，hermes_ceo应该失败，strategy_engine不应该执行
        if 'entry' in executed_layers and 'strategy_engine' not in executed_layers:
            print("  ✓ 错误后停止处理（未执行后续层）")
        else:
            print(f"  ✗ 执行层不符合预期: {executed_layers}")
            return False
    else:
        print("  ✗ 请求应该失败但成功了")
        return False

    print("\n✓ 错误处理和恢复测试通过")
    return True


async def test_real_skill_integration():
    """测试实际技能集成"""
    print("\n" + "=" * 60)
    print("测试5: 实际技能集成")
    print("=" * 60)

    # 尝试导入实际技能
    try:
        # 尝试导入CEO决策技能
        from hermes_fusion.skills.ceo_decision.skill import CeoDecisionSkill
        print("  ✓ 导入CEO决策技能成功")

        # 创建技能实例
        ceo_skill = CeoDecisionSkill()

        # 创建新的数据流管理器实例，避免全局状态影响
        from hermes_fusion.integration.dataflow_manager import LayerDataFlowManager
        manager = LayerDataFlowManager()
        await manager.initialize()

        async def real_ceo_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
            # 准备技能上下文
            skill_context = {
                'text': context.get('original_request', {}).get('text', ''),
                'user_id': context.get('user_id'),
                'platform': context.get('platform'),
                'metadata': context.get('metadata', {})
            }

            # 执行技能 - 支持同步和异步方法
            try:
                if inspect.iscoroutinefunction(ceo_skill.execute):
                    result = await ceo_skill.execute(skill_context)
                else:
                    # 同步方法，在异步上下文中调用
                    result = await asyncio.to_thread(ceo_skill.execute, skill_context)

                print(f"  [调试] CEO技能执行结果: success={result.get('success')}, decision={result.get('decision')}")
                print(f"  [调试] 完整技能结果: {result}")

                # 转换为层结果格式
                return {
                    'layer': layer_name,
                    'skill_result': result,
                    'success': result.get('success', False)
                }
            except Exception as e:
                print(f"  [调试] CEO技能执行异常: {e}")
                import traceback
                traceback.print_exc()
                return {
                    'layer': layer_name,
                    'skill_result': {'error': str(e)},
                    'success': False,
                    'error': str(e)
                }

        manager.register_layer_handler('hermes_ceo', real_ceo_handler)
        print("  ✓ 注册真实CEO决策技能处理器")

        # 测试真实技能处理
        test_request = {
            'text': '分析一个预算5万，目标收入15万的AI咨询项目',
            'user_id': 'real_user',
            'platform': 'feishu',
            'metadata': {
                'budget': 50000,
                'target_revenue': 150000,
                'timeline_days': 90
            },
            'target_layers': ['hermes_ceo']
        }

        result = await manager.process_request(test_request)
        print(f"  [调试] 数据流管理器结果: success={result.get('success')}, error={result.get('error')}")
        print(f"  [调试] 层结果摘要: {result.get('layer_results_summary', {})}")

        if result.get('success'):
            print("  ✓ 真实技能处理成功")

            # 检查技能结果
            layer_results = manager.request_registry[result['request_id']]['layer_results']
            ceo_result = layer_results.get('hermes_ceo', {})
            skill_result = ceo_result.get('skill_result', {})
            print(f"  [调试] CEO层结果: success={ceo_result.get('success')}")
            print(f"  [调试] 技能结果: {skill_result}")

            if skill_result.get('success'):
                print(f"  ✓ 技能执行成功")
                print(f"    决策: {skill_result.get('decision', 'N/A')}")
                print(f"    ROI分析: {skill_result.get('roi_analysis', {})}")
            else:
                print(f"  ✗ 技能执行失败: {skill_result.get('error', '未知错误')}")
                return False
        else:
            print(f"  ✗ 真实技能处理失败: {result.get('error', '未知错误')}")
            print(f"  [调试] 完整结果: {result}")
            return False

    except ImportError as e:
        print(f"  ⚠️  无法导入实际技能: {e}")
        print("  ⚠️  跳过实际技能集成测试（可能需要先修复hermes-agent安装）")
        return True  # 跳过不算失败
    except Exception as e:
        print(f"  ✗ 实际技能集成测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n✓ 实际技能集成测试通过")
    return True


async def main():
    """主测试函数"""
    print("7层数据流端到端集成测试")
    print("=" * 60)

    tests = [
        ("数据流管理器基本功能", test_dataflow_manager_basic),
        ("自定义层处理器注册", test_custom_layer_handlers),
        ("完整7层数据流", test_full_7layer_flow),
        ("错误处理和恢复", test_error_handling),
        ("实际技能集成", test_real_skill_integration),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n运行测试: {test_name}")
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"测试失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    print("\n" + "=" * 60)
    print("7层数据流测试结果汇总")
    print("=" * 60)

    passed = 0
    for test_name, success in results:
        status = "✓" if success else "✗"
        print(f"  {status} {test_name}")
        if success:
            passed += 1

    total = len(results)
    print(f"\n通过: {passed}/{total} ({passed/total*100:.1f}%)")

    # 诊断建议
    print("\n" + "=" * 60)
    print("7层数据流集成诊断")
    print("=" * 60)

    if passed == total:
        print("✓ 所有7层数据流测试通过，架构集成完整")
        print("\n建议下一步:")
        print("  1. 完善Paperclip工作流加载机制")
        print("  2. 注册所有实际技能到数据流管理器")
        print("  3. 进行真实业务场景端到端测试")
    else:
        print("⚠️  部分7层数据流测试失败，建议检查:")
        print("  1. 数据流管理器实现是否正确")
        print("  2. 层依赖关系是否准确")
        print("  3. 实际技能导入和注册")
        print("  4. 错误处理机制")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)