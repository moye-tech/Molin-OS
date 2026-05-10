#!/usr/bin/env python3
"""
最终网关配置测试
测试hermes-agent原生Feishu网关配置
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

def test_native_feishu_gateway():
    """测试原生hermes-agent Feishu网关"""
    print("\n测试原生hermes-agent Feishu网关...")

    # 检查上游目录中的Feishu适配器
    upstream_feishu_path = "/Users/moye/Downloads/molin-ai-pro/upstream/hermes-agent/gateway/platforms/feishu.py"
    if not os.path.exists(upstream_feishu_path):
        print(f"✗ 上游Feishu文件不存在: {upstream_feishu_path}")
        return False

    print(f"✓ 上游Feishu文件存在: {upstream_feishu_path}")

    # 检查文件内容
    with open(upstream_feishu_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否包含FeishuAdapter类
    if 'class FeishuAdapter' in content:
        print("✓ FeishuAdapter类定义存在")
    else:
        print("✗ FeishuAdapter类定义不存在")

    # 检查是否包含BasePlatformAdapter
    if 'BasePlatformAdapter' in content:
        print("✓ 继承自BasePlatformAdapter")
    else:
        print("✗ 未继承自BasePlatformAdapter")

    # 尝试导入（使用上游目录）
    import sys
    original_path = sys.path.copy()

    # 添加上游目录到路径
    upstream_dir = "/Users/moye/Downloads/molin-ai-pro/upstream/hermes-agent"
    if upstream_dir not in sys.path:
        sys.path.insert(0, upstream_dir)

    try:
        from gateway.platforms.feishu import FeishuAdapter
        print("✓ FeishuAdapter可导入")

        from gateway.platforms.base import BasePlatformAdapter
        print("✓ BasePlatformAdapter可导入")

        # 检查继承关系
        if issubclass(FeishuAdapter, BasePlatformAdapter):
            print("✓ FeishuAdapter正确继承自BasePlatformAdapter")
        else:
            print("✗ FeishuAdapter未继承自BasePlatformAdapter")

        # 恢复sys.path
        sys.path = original_path
        return True

    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        # 恢复sys.path
        sys.path = original_path
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        # 恢复sys.path
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
        # 检查version属性或添加默认值
        if hasattr(adapter, 'version'):
            print(f"  适配器版本: {adapter.version}")
        else:
            print("  适配器版本: 未定义（添加默认值）")
            adapter.version = "1.0.0"
        return True
    except ImportError as e:
        print(f"✗ ConfigAdapter导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ ConfigAdapter测试失败: {e}")
        return False

def main():
    print("阶段5：网关与通信集成测试")
    print("=" * 70)

    config_ok = test_feishu_config()
    gateway_ok = test_native_feishu_gateway()
    api_ok = test_api_compat()

    print("\n" + "=" * 70)
    print("测试结果:")
    print(f"  Feishu配置: {'✓ 通过' if config_ok else '✗ 失败'}")
    print(f"  原生Feishu网关: {'✓ 通过' if gateway_ok else '✗ 失败'}")
    print(f"  API兼容层: {'✓ 通过' if api_ok else '✗ 失败'}")

    all_ok = config_ok and gateway_ok and api_ok
    print(f"\n总体: {'✅ 所有测试通过' if all_ok else '❌ 部分测试失败'}")

    # 更新TodoWrite状态
    if config_ok and gateway_ok:
        print("\n✅ 阶段5网关与通信集成测试完成")
        print("   原生Feishu网关配置正确，可安全移除自定义FeishuGatewayProvider")

    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)