#!/usr/bin/env python3
"""
测试Paperclip工作流加载
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hermes_fusion.skills.paperclip.skill import PaperclipSkill

def test_workflow_loading():
    """测试工作流加载"""
    print("测试Paperclip工作流加载...")

    # 创建技能实例
    config = {
        'workflow_defs_dir': 'config/hermes-agent/workflows'
    }

    skill = PaperclipSkill(config)

    # 检查工作流定义
    print(f"加载的工作流数量: {len(skill.workflow_definitions)}")

    for workflow_id, definition in skill.workflow_definitions.items():
        print(f"  工作流ID: {workflow_id}")
        print(f"    名称: {definition.get('name', '未命名')}")
        print(f"    步骤数: {len(definition.get('steps', []))}")

        # 检查步骤
        steps = definition.get('steps', [])
        for i, step in enumerate(steps):
            print(f"      步骤 {i+1}: {step.get('id', '未命名')} - {step.get('type', '未知')}")

    # 测试工作流执行
    if skill.workflow_definitions:
        workflow_id = list(skill.workflow_definitions.keys())[0]
        print(f"\n测试启动工作流: {workflow_id}")

        # 模拟上下文
        context = {
            'text': f'启动工作流 {workflow_id}',
            'user_id': 'test_user',
            'platform': 'test',
            'variables': {'content': '测试内容'}
        }

        # 需要异步执行
        import asyncio

        async def test_start():
            result = await skill._start_workflow(workflow_id, context)
            print(f"  启动结果: {result}")

            if 'error' in result:
                print(f"  错误: {result['error']}")
            else:
                print(f"  工作流实例: {result.get('workflow_instance_id', 'N/A')}")
                print(f"  状态: {result.get('status', 'N/A')}")
                print(f"  当前步骤: {result.get('current_step', 'N/A')}")

        asyncio.run(test_start())
    else:
        print("未加载任何工作流定义")

if __name__ == "__main__":
    test_workflow_loading()