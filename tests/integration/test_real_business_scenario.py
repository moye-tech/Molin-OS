#!/usr/bin/env python3
"""
真实业务场景端到端测试
模拟用户请求AI咨询项目，通过7层数据流，部分使用真实技能
"""
import sys
import os
import asyncio
import time
import inspect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hermes_fusion.integration.dataflow_manager import LayerDataFlowManager
from hermes_fusion.skills.ceo_decision.skill import CeoDecisionSkill
from hermes_fusion.skills.paperclip.skill import PaperclipSkill

async def test_real_business_scenario():
    """测试真实业务场景"""
    print("=" * 70)
    print("真实业务场景端到端测试")
    print("=" * 70)

    # 创建数据流管理器
    manager = LayerDataFlowManager()
    await manager.initialize()

    # 创建真实技能实例
    ceo_skill = CeoDecisionSkill()
    paperclip_skill = PaperclipSkill({'workflow_defs_dir': 'config/hermes-agent/workflows'})

    # 注册真实技能处理器
    async def real_ceo_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """真实CEO决策处理器"""
        skill_context = {
            'text': context.get('original_request', {}).get('text', ''),
            'user_id': context.get('user_id'),
            'platform': context.get('platform'),
            'metadata': context.get('metadata', {}),
            'upstream_results': context.get('upstream_results', {})
        }

        # 执行技能 - 支持同步和异步方法
        if inspect.iscoroutinefunction(ceo_skill.execute):
            result = await ceo_skill.execute(skill_context)
        else:
            result = await asyncio.to_thread(ceo_skill.execute, skill_context)

        print(f"  [业务场景] CEO决策结果: {result.get('decision')}, ROI: {result.get('roi_analysis', {}).get('roi_ratio')}")

        return {
            'layer': layer_name,
            'skill_result': result,
            'success': result.get('success', False),
            'decision': result.get('decision'),
            'roi_analysis': result.get('roi_analysis', {}),
            'composite_score': result.get('composite_score', 0)
        }

    async def real_paperclip_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """真实Paperclip工作流处理器"""
        # 从上游获取任务
        upstream_results = context.get('upstream_results', {})
        agency_result = upstream_results.get('agency', {})
        task = agency_result.get('task', '未知任务')

        # 启动工作流
        workflow_id = 'content_approval_workflow'
        skill_context = {
            'text': f'审批任务: {task}',
            'user_id': context.get('user_id'),
            'platform': context.get('platform'),
            'metadata': context.get('metadata', {}),
            'action': 'start_workflow',
            'workflow_id': workflow_id,
            'variables': {'task': task}
        }

        # 执行技能
        if inspect.iscoroutinefunction(paperclip_skill.execute):
            result = await paperclip_skill.execute(skill_context)
        else:
            result = await asyncio.to_thread(paperclip_skill.execute, skill_context)

        print(f"  [业务场景] Paperclip工作流结果: {result.get('success')}")

        return {
            'layer': layer_name,
            'skill_result': result,
            'success': result.get('success', False),
            'workflow_status': 'approved' if result.get('success') else 'rejected',
            'approved_tasks': [task] if result.get('success') else []
        }

    # 模拟其他层处理器
    async def mock_entry_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {'layer': layer_name, 'status': 'entered', 'request_valid': True}

    async def mock_strategy_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        upstream = context.get('upstream_results', {})
        ceo_result = upstream.get('hermes_ceo', {})
        decision = ceo_result.get('decision', 'NEED_INFO')

        if decision == 'GO':
            strategy = {
                'template_used': 'AI服务',
                'daily_target_deals': 3,
                'avg_order_value': 800,
                'recommended_subsidiary': 'order'
            }
        else:
            strategy = {
                'template_used': '需求分析',
                'daily_target_deals': 0,
                'avg_order_value': 0,
                'recommended_subsidiary': 'research'
            }

        return {
            'layer': layer_name,
            'strategy': strategy,
            'recommended_subsidiary': strategy['recommended_subsidiary']
        }

    async def mock_agency_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        upstream = context.get('upstream_results', {})
        strategy = upstream.get('strategy_engine', {}).get('strategy', {})

        return {
            'layer': layer_name,
            'subsidiary': strategy.get('recommended_subsidiary', 'general'),
            'task': f"执行{strategy.get('template_used', '未知')}策略"
        }

    async def mock_clawteam_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        upstream = context.get('upstream_results', {})
        paperclip_result = upstream.get('paperclip', {})
        approved_tasks = paperclip_result.get('approved_tasks', [])

        return {
            'layer': layer_name,
            'scheduled_tasks': [{'id': f'task_{i}', 'type': 'execution'} for i, _ in enumerate(approved_tasks)],
            'execution_plan': {'concurrent_limit': 3}
        }

    async def mock_execution_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        upstream = context.get('upstream_results', {})
        clawteam_result = upstream.get('clawteam', {})
        scheduled_tasks = clawteam_result.get('scheduled_tasks', [])

        return {
            'layer': layer_name,
            'results': [{'task_id': task['id'], 'status': 'completed'} for task in scheduled_tasks],
            'metrics': {'execution_time': 5.2, 'success_rate': 1.0}
        }

    async def mock_data_brain_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        upstream = context.get('upstream_results', {})
        execution_result = upstream.get('execution', {})

        return {
            'layer': layer_name,
            'analysis': {
                'overall_score': 8.5,
                'recommendations': ['优化执行流程', '增加自动化测试'],
                'alerts': []
            }
        }

    async def mock_memory_handler(layer_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'layer': layer_name,
            'stored': True,
            'memory_keys': ['business_scenario_001']
        }

    # 注册处理器
    manager.register_layer_handler('entry', mock_entry_handler)
    manager.register_layer_handler('hermes_ceo', real_ceo_handler)
    manager.register_layer_handler('strategy_engine', mock_strategy_handler)
    manager.register_layer_handler('agency', mock_agency_handler)
    manager.register_layer_handler('paperclip', real_paperclip_handler)
    manager.register_layer_handler('clawteam', mock_clawteam_handler)
    manager.register_layer_handler('execution', mock_execution_handler)
    manager.register_layer_handler('data_brain', mock_data_brain_handler)
    manager.register_layer_handler('memory', mock_memory_handler)

    # 模拟真实业务请求
    test_request = {
        'text': '我想开展一个AI咨询服务，预算5万元，目标收入15万元，时间线30天',
        'user_id': 'business_user_001',
        'platform': 'feishu',
        'metadata': {
            'budget': 50000,
            'target_revenue': 150000,
            'timeline': '30天'
        }
    }

    print("\n处理真实业务请求...")
    print(f"  请求: {test_request['text']}")
    print(f"  预算: {test_request['metadata']['budget']}元")
    print(f"  目标收入: {test_request['metadata']['target_revenue']}元")

    start_time = time.time()
    result = await manager.process_request(test_request)
    end_time = time.time()

    print(f"\n处理完成，总时间: {end_time - start_time:.2f}秒")

    if result.get('success'):
        print("✓ 业务场景处理成功")

        # 输出关键结果
        layer_results = manager.request_registry[result['request_id']]['layer_results']

        # CEO决策
        ceo_result = layer_results.get('hermes_ceo', {})
        print(f"\n1. CEO决策:")
        print(f"   决策: {ceo_result.get('decision', 'N/A')}")
        print(f"   复合评分: {ceo_result.get('composite_score', 'N/A')}")
        print(f"   ROI比率: {ceo_result.get('roi_analysis', {}).get('roi_ratio', 'N/A')}")

        # 策略引擎
        strategy_result = layer_results.get('strategy_engine', {})
        print(f"\n2. 策略引擎:")
        print(f"   模板: {strategy_result.get('strategy', {}).get('template_used', 'N/A')}")
        print(f"   推荐子公司: {strategy_result.get('recommended_subsidiary', 'N/A')}")

        # 代理层
        agency_result = layer_results.get('agency', {})
        print(f"\n3. 代理层:")
        print(f"   子公司: {agency_result.get('subsidiary', 'N/A')}")
        print(f"   任务: {agency_result.get('task', 'N/A')}")

        # Paperclip审批
        paperclip_result = layer_results.get('paperclip', {})
        print(f"\n4. Paperclip审批:")
        print(f"   工作流状态: {paperclip_result.get('workflow_status', 'N/A')}")
        print(f"   批准任务数: {len(paperclip_result.get('approved_tasks', []))}")

        # ClawTeam调度
        clawteam_result = layer_results.get('clawteam', {})
        print(f"\n5. ClawTeam调度:")
        print(f"   调度任务数: {len(clawteam_result.get('scheduled_tasks', []))}")

        # 执行层
        execution_result = layer_results.get('execution', {})
        print(f"\n6. 执行层:")
        print(f"   完成任务数: {len(execution_result.get('results', []))}")

        # DataBrain分析
        data_brain_result = layer_results.get('data_brain', {})
        print(f"\n7. DataBrain分析:")
        print(f"   总体评分: {data_brain_result.get('analysis', {}).get('overall_score', 'N/A')}")

        # 记忆层
        memory_result = layer_results.get('memory', {})
        print(f"\n8. 记忆层:")
        print(f"   存储成功: {memory_result.get('stored', False)}")

        print(f"\n✓ 业务场景端到端测试通过")
        return True

    else:
        print(f"✗ 业务场景处理失败: {result.get('error', '未知错误')}")
        print(f"  失败层: {result.get('failed_layers', [])}")
        return False

if __name__ == "__main__":
    # 导入Dict和Any
    from typing import Dict, Any

    success = asyncio.run(test_real_business_scenario())
    sys.exit(0 if success else 1)