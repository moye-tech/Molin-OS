#!/usr/bin/env python3
"""
基础框架测试（跳过hermes-agent导入）
"""

import sys
import os
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_directory_structure():
    """测试目录结构"""
    required_dirs = [
        "hermes_fusion",
        "hermes_fusion/providers",
        "hermes_fusion/skills/ceo_decision",
        "config/hermes-agent/skills",
        "config/hermes-agent/tools",
        "config/hermes-agent/gateways",
    ]

    missing = []
    for d in required_dirs:
        if not os.path.exists(d):
            missing.append(d)

    if missing:
        logger.error(f"缺少目录: {missing}")
        return False
    logger.info("目录结构测试通过")
    return True


def test_config_adapter():
    """测试配置适配器"""
    try:
        from hermes_fusion.providers.config_adapter import ConfigAdapter
        adapter = ConfigAdapter("config")
        adapter.load_all_legacy_configs()

        if len(adapter.subsidiaries) == 11:
            logger.info(f"配置适配器测试通过: {len(adapter.subsidiaries)}子公司")
            return True
        else:
            logger.error(f"子公司数量不正确: {len(adapter.subsidiaries)}，应为11")
            return False
    except Exception as e:
        logger.error(f"配置适配器测试失败: {e}")
        return False


def test_skill_classes():
    """测试技能类"""
    try:
        from hermes_fusion.skills.ceo_decision.skill import CeoDecisionSkill
        from hermes_fusion.skills.sop_execution.skill import SopExecutionSkill

        ceo_skill = CeoDecisionSkill()
        sop_skill = SopExecutionSkill()

        logger.info(f"技能类测试通过: {ceo_skill.name}, {sop_skill.name}")
        return True
    except Exception as e:
        logger.error(f"技能类测试失败: {e}")
        return False


def test_tool_classes():
    """测试工具类"""
    try:
        from hermes_fusion.tools.ceo_tools import CeoTools
        from hermes_fusion.tools.data_analysis_tools import DataAnalysisTools

        # 简单调用
        result = CeoTools.analyze_roi(10000, 30, 30000)
        logger.info(f"工具类测试通过，ROI分析结果: {result.get('roi_ratio', 0):.2f}")
        return True
    except Exception as e:
        logger.error(f"工具类测试失败: {e}")
        return False


def test_config_files():
    """测试配置文件"""
    required_files = [
        "config/hermes-agent/config.yaml",
        "config/hermes-agent/skills/ceo_decision.yaml",
        "config/legacy/subsidiaries.toml",
    ]

    missing = []
    for f in required_files:
        if not os.path.exists(f):
            missing.append(f)

    if missing:
        logger.error(f"缺少配置文件: {missing}")
        return False
    logger.info("配置文件测试通过")
    return True


def main():
    """运行测试"""
    logger.info("开始基础框架测试（跳过hermes-agent）")

    tests = [
        ("目录结构", test_directory_structure),
        ("配置适配器", test_config_adapter),
        ("技能类", test_skill_classes),
        ("工具类", test_tool_classes),
        ("配置文件", test_config_files),
    ]

    results = []
    for name, func in tests:
        logger.info(f"--- 测试: {name} ---")
        try:
            success = func()
            results.append((name, success))
        except Exception as e:
            logger.error(f"测试异常 {name}: {e}")
            results.append((name, False))

    # 汇总
    logger.info("=" * 50)
    logger.info("测试结果汇总:")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        logger.info(f"  {name}: {status}")

    logger.info(f"总计: {passed}/{total} 通过")

    if passed == total:
        logger.info("所有基础框架测试通过！")
        return 0
    else:
        logger.warning(f"{total - passed} 个测试失败，但基础框架可用")
        return 1


if __name__ == '__main__':
    sys.exit(main())