#!/usr/bin/env python3
"""
基础框架集成测试
测试配置适配器、目录结构、依赖导入等基本功能
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_directory_structure():
    """测试目录结构是否正确创建"""
    logger.info("测试目录结构...")

    required_dirs = [
        "hermes_fusion",
        "hermes_fusion/providers",
        "hermes_fusion/skills",
        "hermes_fusion/skills/ceo_decision",
        "hermes_fusion/skills/subsidiaries",
        "hermes_fusion/skills/sop_execution",
        "hermes_fusion/tools",
        "hermes_fusion/integration/migration",
        "hermes_fusion/integration/compat",
        "config/hermes-agent/skills",
        "config/hermes-agent/tools",
        "config/hermes-agent/gateways",
        "config/legacy",
    ]

    missing_dirs = []
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)

    if missing_dirs:
        logger.error(f"缺少目录: {missing_dirs}")
        return False
    else:
        logger.info("目录结构测试通过")
        return True


def test_config_adapter():
    """测试配置适配器"""
    logger.info("测试配置适配器...")

    try:
        from hermes_fusion.providers.config_adapter import ConfigAdapter

        adapter = ConfigAdapter("config")
        adapter.load_all_legacy_configs()

        if len(adapter.subsidiaries) != 11:
            logger.error(f"子公司数量不正确: {len(adapter.subsidiaries)}，应为11")
            return False

        logger.info(f"配置适配器测试通过: {len(adapter.subsidiaries)}子公司")
        return True

    except Exception as e:
        logger.error(f"配置适配器测试失败: {e}")
        return False


def test_imports():
    """测试模块导入"""
    logger.info("测试模块导入...")

    modules_to_test = [
        "hermes_fusion",
        "hermes_fusion.providers",
        "hermes_fusion.skills",
        "hermes_fusion.tools",
        "hermes_fusion.integration",
    ]

    failed_imports = []
    for module_name in modules_to_test:
        try:
            __import__(module_name)
        except ImportError as e:
            failed_imports.append((module_name, str(e)))

    if failed_imports:
        for module_name, error in failed_imports:
            logger.error(f"导入失败 {module_name}: {error}")
        return False
    else:
        logger.info("模块导入测试通过")
        return True


def test_hermes_agent_import():
    """测试hermes-agent导入"""
    logger.info("测试hermes-agent导入...")

    try:
        # 尝试导入hermes_agent
        import hermes_agent
        version = getattr(hermes_agent, '__version__', '未知')
        logger.info(f"hermes-agent导入成功，版本: {version}")
        return True
    except ImportError as e:
        logger.warning(f"hermes-agent导入失败: {e}")
        logger.warning("注意: hermes-agent可能尚未安装，请运行 'pip install hermes-agent'")
        return False  # 但这不是致命错误


def test_config_files():
    """测试配置文件生成"""
    logger.info("测试配置文件...")

    required_files = [
        "config/hermes-agent/config.yaml",
        "config/hermes-agent/skills/ceo_decision.yaml",
        "config/hermes-agent/gateways/feishu.yaml",
    ]

    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        logger.error(f"缺少配置文件: {missing_files}")
        return False
    else:
        logger.info("配置文件测试通过")
        return True


def main():
    """运行所有测试"""
    logger.info("开始基础框架集成测试")

    tests = [
        ("目录结构", test_directory_structure),
        ("模块导入", test_imports),
        ("配置适配器", test_config_adapter),
        ("配置文件", test_config_files),
        ("hermes-agent导入", test_hermes_agent_import),
    ]

    results = []
    for test_name, test_func in tests:
        logger.info(f"--- 开始测试: {test_name} ---")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"测试异常 {test_name}: {e}")
            results.append((test_name, False))

    # 汇总结果
    logger.info("=" * 50)
    logger.info("测试结果汇总:")

    passed = 0
    total = len(results)

    for test_name, success in results:
        status = "通过" if success else "失败"
        logger.info(f"  {test_name}: {status}")
        if success:
            passed += 1

    logger.info(f"总计: {passed}/{total} 通过")

    if passed == total:
        logger.info("所有测试通过！基础框架集成正常。")
        return 0
    else:
        logger.error(f"{total - passed} 个测试失败，需要检查。")
        return 1


if __name__ == '__main__':
    sys.exit(main())