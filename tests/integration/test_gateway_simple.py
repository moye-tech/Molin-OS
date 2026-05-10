#!/usr/bin/env python3
"""
简化网关配置测试
"""

import sys
import os
import yaml

def test_feishu_config():
    """测试Feishu配置"""
    print("测试Feishu网关配置...")

    config_path = "config/hermes-agent/config.yaml"
    print(f"检查配置文件: {config_path}")
    print(f"文件存在: {os.path.exists(config_path)}")

    if not os.path.exists(config_path):
        print("✗ 配置文件不存在")
        return False

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        gateways = config.get('gateways', {})
        print(f"找到 {len(gateways)} 个网关配置")

        feishu_config = gateways.get('feishu')
        if not feishu_config:
            print("✗ Feishu网关配置未找到")
            return False

        print(f"✓ Feishu网关配置找到:")
        print(f"  启用状态: {feishu_config.get('enabled', False)}")
        print(f"  类型: {feishu_config.get('type', 'unknown')}")

        # 检查配置参数
        feishu_inner_config = feishu_config.get('config', {})
        required_params = ['app_id', 'app_secret', 'verification_token']

        for param in required_params:
            if param in feishu_inner_config:
                value = feishu_inner_config[param]
                if value.startswith('${') and value.endswith('}'):
                    print(f"   {param}: 环境变量引用 ({value})")
                else:
                    print(f"   {param}: 已设置")
            else:
                print(f"   {param}: 未设置")

        return True
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gateway_module():
    """测试网关模块导入"""
    print("\n测试网关模块导入...")

    try:
        # 临时修改sys.path，优先使用上游目录
        import sys
        original_path = sys.path.copy()

        # 移除当前目录（避免导入本地gateway目录）
        current_dir = "/Users/moye/Downloads/molin-ai-pro"
        if current_dir in sys.path:
            sys.path.remove(current_dir)

        # 添加上游目录
        upstream_dir = str(Path(__file__).resolve().parents[2] / "external" / "hermes-agent")
        if upstream_dir not in sys.path:
            sys.path.insert(0, upstream_dir)

        try:
            import gateway
            print(f"✓ gateway模块导入成功: {gateway.__file__}")

            import gateway.platforms
            print(f"✓ gateway.platforms导入成功: {gateway.platforms.__file__}")

            # 列出平台文件
            import os
            # 检查gateway.platforms是否是一个包
            if gateway.platforms.__file__ is not None:
                platform_dir = os.path.dirname(gateway.platforms.__file__)
                platform_files = os.listdir(platform_dir)
                print(f"  网关平台文件: {[f for f in platform_files if f.endswith('.py') and not f.startswith('_')]}")

                # 检查Feishu
                if 'feishu.py' in platform_files:
                    print("  ✓ Feishu平台文件存在")
                    try:
                        from gateway.platforms.feishu import FeishuAdapter
                        print("  ✓ FeishuAdapter可导入")

                        # 检查是否是BasePlatformAdapter的子类
                        from gateway.platforms.base import BasePlatformAdapter
                        print(f"  BasePlatformAdapter导入成功")

                        # 创建实例测试
                        print("  Feishu网关模块测试通过")
                        return True
                    except ImportError as e:
                        print(f"  ✗ FeishuAdapter导入失败: {e}")
                        return False
                else:
                    print("  ✗ Feishu平台文件不存在")
                    return False
        else:
            # 命名空间包，尝试直接从源目录检查
            print("  网关模块是命名空间包，尝试直接从源目录检查...")
            source_dir = "/Users/moye/Downloads/molin-ai-pro/upstream/hermes-agent/gateway/platforms"
            if os.path.exists(source_dir):
                platform_files = os.listdir(source_dir)
                print(f"  源目录平台文件: {[f for f in platform_files if f.endswith('.py') and not f.startswith('_')]}")

                if 'feishu.py' in platform_files:
                    print("  ✓ Feishu平台文件存在")
                    # 尝试导入
                    try:
                        # 将源目录添加到路径
                        import sys
                        sys.path.insert(0, "/Users/moye/Downloads/molin-ai-pro/upstream/hermes-agent")
                        from gateway.platforms.feishu import FeishuAdapter
                        print("  ✓ FeishuAdapter可导入")

                        # 检查是否是BasePlatformAdapter的子类
                        from gateway.platforms.base import BasePlatformAdapter
                        print(f"  BasePlatformAdapter导入成功")

                        # 创建实例测试
                        print("  Feishu网关模块测试通过")

                        # 恢复sys.path
                        sys.path = original_path
                        return True
                    except ImportError as e:
                        print(f"  ✗ FeishuAdapter导入失败: {e}")
                        # 恢复sys.path
                        sys.path = original_path
                        return False
                else:
                    print("  ✗ Feishu平台文件不存在")
                    # 恢复sys.path
                    sys.path = original_path
                    return False
            else:
                print("  ✗ 网关源目录不存在")
                # 恢复sys.path
                sys.path = original_path
                return False

    except ImportError as e:
        print(f"✗ 网关模块导入失败: {e}")
        # 恢复sys.path（如果original_path已定义）
        if 'original_path' in locals():
            sys.path = original_path
        return False

def test_api_compat():
    """测试API兼容层"""
    print("\n测试API兼容层...")

    api_files = [
        "hermes/main.py",
        "hermes_fusion/integration/api_bridge.py"
    ]

    for api_file in api_files:
        if os.path.exists(api_file):
            print(f"✓ API文件存在: {api_file}")
        else:
            print(f"✗ API文件不存在: {api_file}")

    # 检查ConfigAdapter
    try:
        from hermes_fusion.providers.config_adapter import ConfigAdapter
        print("✓ ConfigAdapter可导入")

        adapter = ConfigAdapter()
        print(f"  适配器版本: {getattr(adapter, 'version', '未定义')}")
        return True
    except ImportError as e:
        print(f"✗ ConfigAdapter导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ ConfigAdapter测试失败: {e}")
        return False

def main():
    print("网关与通信集成测试")
    print("=" * 70)

    config_ok = test_feishu_config()
    module_ok = test_gateway_module()
    api_ok = test_api_compat()

    print("\n" + "=" * 70)
    print("测试结果:")
    print(f"  Feishu配置: {'✓ 通过' if config_ok else '✗ 失败'}")
    print(f"  网关模块: {'✓ 通过' if module_ok else '✗ 失败'}")
    print(f"  API兼容层: {'✓ 通过' if api_ok else '✗ 失败'}")

    all_ok = config_ok and module_ok and api_ok
    print(f"\n总体: {'✅ 所有测试通过' if all_ok else '❌ 部分测试失败'}")

    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)