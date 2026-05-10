#!/usr/bin/env python3
"""
Hermes Native技能测试
测试子公司技能Hermes Native适配
"""

import sys
import os
import asyncio
import logging
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_hermes_native_skill_initialization():
    """测试Hermes Native技能初始化"""
    from hermes_fusion.skills.hermes_native import EduSubsidiaryMolinSkill

    # 创建技能实例
    skill = EduSubsidiaryMolinSkill()

    # 验证基本属性
    assert skill.name == "教育子公司", f"技能名称错误: {skill.name}"
    assert "教育" in skill.description, f"技能描述错误: {skill.description}"
    assert len(skill.keywords) > 0, "关键词列表为空"
    assert "教育" in skill.keywords, "关键词中应包含'教育'"

    logger.info("✓ Hermes Native技能初始化测试通过")
    return True


def test_hermes_native_skill_can_handle():
    """测试技能触发判断"""
    from hermes_fusion.skills.hermes_native import EduSubsidiaryMolinSkill

    skill = EduSubsidiaryMolinSkill()

    # 测试关键词匹配
    context = {"text": "我想报名一个培训课程"}
    result = skill.sync_can_handle(context)
    assert result == True, "应触发教育子公司技能"

    # 测试不匹配
    context = {"text": "我要买一件衣服"}
    result = skill.sync_can_handle(context)
    assert result == False, "不应触发教育子公司技能"

    logger.info("✓ Hermes Native技能触发测试通过")
    return True


def test_hermes_native_skill_execute():
    """测试技能执行"""
    from hermes_fusion.skills.hermes_native import EduSubsidiaryMolinSkill

    skill = EduSubsidiaryMolinSkill()

    context = {
        "text": "我想报名一个培训课程",
        "user_id": "test_user",
        "platform": "test"
    }

    result = skill.sync_execute(context)

    # 验证结果格式
    assert isinstance(result, dict), "结果应为字典类型"
    assert "success" in result, "结果应包含success字段"
    assert result["success"] == True, "执行应成功"
    assert "result" in result, "结果应包含result字段"
    assert "execution_time" in result, "结果应包含execution_time字段"

    logger.info("✓ Hermes Native技能执行测试通过")
    return True


async def test_hermes_native_skill_async():
    """测试异步接口"""
    from hermes_fusion.skills.hermes_native import EduSubsidiaryMolinSkill

    skill = EduSubsidiaryMolinSkill()

    context = {
        "text": "我想报名一个培训课程",
        "user_id": "test_user",
        "platform": "test"
    }

    # 测试异步can_handle
    can_handle = await skill.can_handle(context)
    assert can_handle == True, "异步can_handle应返回True"

    # 测试异步execute
    result = await skill.execute(context)
    assert result["success"] == True, "异步执行应成功"

    logger.info("✓ Hermes Native技能异步接口测试通过")
    return True


def test_subsidiary_hermes_skill_adapter():
    """测试子公司技能适配器"""
    from hermes_fusion.skills.hermes_skill_base import HermesSkillAdapter
    from hermes_fusion.skills.subsidiaries.edu_subsidiary import EduSubsidiarySkill

    # 创建原始子公司技能
    original_skill = EduSubsidiarySkill()

    # 创建适配器
    adapter = HermesSkillAdapter(original_skill)

    # 验证适配器属性
    assert adapter.get_name() == "教育子公司", f"适配器名称错误: {adapter.get_name()}"
    assert len(adapter.get_tools()) == 0, "适配器工具列表应为空"

    # 测试同步接口
    context = {"text": "培训课程"}
    can_handle = adapter.sync_can_handle(context)
    assert can_handle == True, "适配器应能处理培训相关请求"

    result = adapter.sync_execute(context)
    assert result["success"] == True, "适配器执行应成功"

    logger.info("✓ 子公司技能适配器测试通过")
    return True


def test_hermes_tool_wrapper():
    """测试Hermes工具包装器"""
    from hermes_fusion.skills.subsidiaries.edu_subsidiary import EduSubsidiarySkill
    from hermes_fusion.integration.hermes_tool_wrapper import HermesToolWrapper

    # 创建子公司技能
    subsidiary_skill = EduSubsidiarySkill()

    # 创建工具包装器
    wrapper = HermesToolWrapper(subsidiary_skill)

    # 验证包装器属性
    assert wrapper.get_tool_name() == "教育_skill", f"工具名称错误: {wrapper.get_tool_name()}"
    assert wrapper.get_toolset() == "business_tools", f"工具集错误: {wrapper.get_toolset()}"
    assert wrapper.get_emoji() == "🏢", f"emoji错误: {wrapper.get_emoji()}"

    # 验证工具可用性检查
    available = wrapper.check_availability()
    assert available == True, "工具应可用"

    logger.info("✓ Hermes工具包装器测试通过")
    return True


def run_all_tests():
    """运行所有测试"""
    tests = [
        test_hermes_native_skill_initialization,
        test_hermes_native_skill_can_handle,
        test_hermes_native_skill_execute,
        test_subsidiary_hermes_skill_adapter,
        test_hermes_tool_wrapper,
    ]

    results = []
    for test_func in tests:
        try:
            logger.info(f"运行测试: {test_func.__name__}")
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            logger.error(f"测试失败 {test_func.__name__}: {e}")
            results.append((test_func.__name__, False))

    # 运行异步测试
    try:
        logger.info("运行异步测试")
        async_result = asyncio.run(test_hermes_native_skill_async())
        results.append(("test_hermes_native_skill_async", async_result))
    except Exception as e:
        logger.error(f"异步测试失败: {e}")
        results.append(("test_hermes_native_skill_async", False))

    # 汇总结果
    passed = sum(1 for _, success in results if success)
    total = len(results)

    logger.info("=" * 60)
    logger.info(f"测试结果: {passed}/{total} 通过")

    for test_name, success in results:
        status = "✓" if success else "✗"
        logger.info(f"  {status} {test_name}")

    if passed == total:
        logger.info("✓ 所有测试通过")
        return True
    else:
        logger.error("✗ 部分测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)