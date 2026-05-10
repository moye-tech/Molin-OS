#!/usr/bin/env python3
"""
测试网关配置
验证hermes-agent原生Feishu网关配置是否正确加载
"""
import sys
import os
import yaml

def test_feishu_gateway_config():
    """测试Feishu网关配置"""
    print("测试Feishu网关配置...")

    # 加载主配置文件
    config_path = "config/hermes-agent/config.yaml"
    if not os.path.exists(config_path):
        print(f"✗ 配置文件不存在: {config_path}")
        return False

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 检查gateways配置
        gateways = config.get('gateways', {})
        print(f"找到 {len(gateways)} 个网关配置")

        # 检查Feishu网关
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
        missing_params = []

        for param in required_params:
            if param not in feishu_inner_config:
                missing_params.append(param)
            else:
                value = feishu_inner_config[param]
                if value.startswith('${') and value.endswith('}'):
                    print(f"   {param}: 环境变量引用 ({value})")
                else:
                    print(f"   {param}: 已设置")

        if missing_params:
            print(f"✗ 缺少必要参数: {missing_params}")
            return False

        # 检查hermes-agent网关模块
        print("\n检查hermes-agent网关模块...")
        try:
            # 尝试导入hermes-agent网关模块
            # 注意：hermes_agent不是直接模块，网关在gateway模块中
            from gateway.base import BaseGatewayProvider
            print("✓ BaseGatewayProvider可导入")

            # 检查是否安装了lark_oapi
            try:
                import lark_oapi
                print("✓ lark_oapi已安装")
            except ImportError:
                print("⚠ lark_oapi未安装，Feishu功能可能受限")

            return True
        except ImportError as e:
            print(f"✗ hermes-agent网关模块导入失败: {e}")
            # 尝试查看gateway目录是否存在
            try:
                import gateway
                print(f"  gateway模块位置: {gateway.__file__}")
                import gateway.platforms
                print(f"  gateway.platforms位置: {gateway.platforms.__file__}")

                # 列出平台文件
                import os
                platform_dir = os.path.dirname(gateway.platforms.__file__)
                platform_files = os.listdir(platform_dir)
                print(f"  网关平台文件: {platform_files}")

                # 检查Feishu平台
                if 'feishu.py' in platform_files:
                    print("  ✓ Feishu平台文件存在")
                else:
                    print("  ✗ Feishu平台文件不存在")
            except Exception as e2:
                print(f"  网关目录检查失败: {e2}")
            return False

    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_compat_layer():
    """测试API兼容层"""
    print("\n\n测试API兼容层...")

    # 检查现有API文件
    api_files = [
        "hermes/main.py",
        "hermes_fusion/integration/api_bridge.py"
    ]

    for api_file in api_files:
        if os.path.exists(api_file):
            print(f"✓ API文件存在: {api_file}")

            # 读取文件检查关键端点
            with open(api_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查常见端点
            endpoints = ['/api/decide', '/api/agency/dispatch', '/api/memory/query', '/api/sop/execute']
            found_endpoints = []

            for endpoint in endpoints:
                if endpoint in content:
                    found_endpoints.append(endpoint)

            if found_endpoints:
                print(f"  包含端点: {found_endpoints}")
            else:
                print(f"  未找到标准端点")
        else:
            print(f"✗ API文件不存在: {api_file}")

    # 检查配置映射
    print("\n检查配置映射...")
    try:
        from hermes_fusion.providers.config_adapter import ConfigAdapter
        print("✓ ConfigAdapter可导入")

        # 测试配置转换
        adapter = ConfigAdapter()
        print(f"  适配器版本: {adapter.version}")

        return True
    except ImportError as e:
        print(f"✗ ConfigAdapter导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 配置映射测试失败: {e}")
        return False

def test_multiplatform_support():
    """测试多平台支持"""
    print("\n\n测试多平台支持...")

    # 检查现有网关实现
    gateway_dir = "gateway/platforms"
    if os.path.exists(gateway_dir):
        gateway_files = os.listdir(gateway_dir)
        print(f"网关平台文件: {gateway_files}")

        # 检查常见平台
        platforms = ['feishu.py', 'telegram.py', 'discord.py', 'slack.py']
        for platform in platforms:
            if platform in gateway_files:
                print(f"✓ {platform}: 已实现")
            else:
                print(f"  {platform}: 未实现")
    else:
        print(f"网关目录不存在: {gateway_dir}")

    # 检查hermes-agent原生平台支持
    print("\n检查hermes-agent原生平台支持...")
    try:
        import gateway.platforms as ha_platforms
        print(f"hermes-agent网关平台模块可导入")

        # 列出可用平台
        platform_dir = os.path.dirname(ha_platforms.__file__)
        if os.path.exists(platform_dir):
            ha_platform_files = [f for f in os.listdir(platform_dir) if f.endswith('.py') and not f.startswith('_')]
            print(f"hermes-agent原生平台: {ha_platform_files}")

            # 检查是否包含feishu
            if 'feishu.py' in ha_platform_files:
                print("✓ hermes-agent包含原生Feishu网关")

                # 测试导入
                try:
                    from gateway.platforms.feishu import FeishuPlatformAdapter
                    print("✓ FeishuPlatformAdapter可导入")
                    return True
                except ImportError as e:
                    print(f"✗ FeishuPlatformAdapter导入失败: {e}")
                    return False
            else:
                print("✗ hermes-agent不包含原生Feishu网关")
                return False
        else:
            print("✗ hermes-agent网关平台目录不存在")
            return False

    except ImportError as e:
        print(f"✗ hermes-agent网关平台模块导入失败: {e}")
        return False

def main():
    print("阶段5：网关与通信集成测试")
    print("=" * 70)

    # 测试Feishu网关配置
    gateway_ok = test_feishu_gateway_config()

    # 测试API兼容层
    api_ok = test_api_compat_layer()

    # 测试多平台支持
    platform_ok = test_multiplatform_support()

    print("\n" + "=" * 70)
    print("测试结果:")
    print(f"  Feishu网关配置: {'✓ 通过' if gateway_ok else '✗ 失败'}")
    print(f"  API兼容层: {'✓ 通过' if api_ok else '✗ 失败'}")
    print(f"  多平台支持: {'✓ 通过' if platform_ok else '✗ 失败'}")

    all_ok = gateway_ok and api_ok and platform_ok
    print(f"\n总体: {'✅ 所有测试通过' if all_ok else '❌ 部分测试失败'}")

    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)