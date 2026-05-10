#!/usr/bin/env python3
"""
安全模块导入测试
验证所有安全模块能否正确导入和初始化
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """测试模块导入"""
    print("测试安全模块导入...")

    try:
        # 测试导入各个模块
        from molib.infra.security import SecurityEngine, get_security_engine
        from molib.infra.security import EncryptionManager, AccessController, AuditLogger, DataProtector

        print("✓ 所有模块导入成功")
        return True
    except Exception as e:
        print(f"✗ 模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_security_engine_initialization():
    """测试安全引擎初始化"""
    print("\n测试安全引擎初始化...")

    try:
        # 创建一个临时的安全配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
version: "1.0"
enabled: true

encryption:
  algorithm: "AES-256-GCM"
  key_rotation_days: 30
  key_storage: "env"
  env_key_name: "ENCRYPTION_KEY"

access_control:
  api:
    rate_limit:
      enabled: true
      requests_per_minute: 60

audit_logging:
  enabled: true
  level: "info"

data_protection:
  data_masking:
    enabled: true
    fields_to_mask: ["password", "api_key"]
            """)
            temp_config_path = f.name

        try:
            # 初始化安全引擎
            engine = SecurityEngine(config_path=temp_config_path)

            print(f"✓ 安全引擎初始化成功，启用状态: {engine.is_enabled()}")
            print(f"✓ 安全组件: {engine.get_security_metrics()}")

            # 测试基本功能
            if engine.is_enabled():
                # 测试记录安全事件
                engine.log_security_event(
                    event_type="test_event",
                    event_data={"test": "data"},
                    user_id="test_user"
                )
                print("✓ 安全事件记录测试完成")

                # 测试数据掩码
                test_data = {"password": "secret123", "email": "test@example.com"}
                masked_data = engine.mask_sensitive_data(test_data)
                print(f"✓ 数据掩码测试完成: {masked_data}")

                # 测试访问控制（禁用安全时应该返回True）
                user_context = {"user_id": "test_user", "roles": ["user"]}
                access_allowed = engine.check_access("test_resource", "read", user_context)
                print(f"✓ 访问控制测试完成: {access_allowed}")

            return True

        finally:
            # 清理临时文件
            os.unlink(temp_config_path)

    except Exception as e:
        print(f"✗ 安全引擎初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_individual_components():
    """测试各个组件"""
    print("\n测试各个安全组件...")

    try:
        # 测试加密管理器
        encryption_config = {
            "algorithm": "AES-256-GCM",
            "key_rotation_days": 30,
            "key_storage": "env",
            "env_key_name": "ENCRYPTION_KEY"
        }

        # 设置一个测试加密密钥（仅用于测试）
        os.environ["ENCRYPTION_KEY"] = "test_encryption_key_1234567890abcdef"

        encryption = EncryptionManager(encryption_config)
        print("✓ 加密管理器初始化成功")

        # 测试加密解密
        plaintext = "敏感数据123"
        encrypted = encryption.encrypt(plaintext, "test")
        print(f"  - 加密测试: {plaintext[:10]}... -> {encrypted[:30]}...")

        if encrypted:
            decrypted = encryption.decrypt(encrypted, "test")
            if decrypted == plaintext:
                print("  - 解密测试: 成功")
            else:
                print(f"  - 解密测试: 失败，得到: {decrypted}")

        # 测试访问控制器
        access_config = {
            "api": {
                "rate_limit": {
                    "enabled": True,
                    "requests_per_minute": 60
                }
            }
        }

        access_control = AccessController(access_config)
        print("✓ 访问控制器初始化成功")

        # 测试审计日志器
        audit_config = {
            "enabled": True,
            "level": "info",
            "storage": {
                "type": "memory"
            }
        }

        audit_logger = AuditLogger(audit_config)
        print("✓ 审计日志器初始化成功")

        # 测试数据保护器
        data_protection_config = {
            "data_masking": {
                "enabled": True,
                "fields_to_mask": ["password", "api_key"]
            }
        }

        data_protector = DataProtector(data_protection_config, encryption)
        print("✓ 数据保护器初始化成功")

        return True

    except Exception as e:
        print(f"✗ 组件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("墨麟AI智能系统 安全模块测试")
    print("=" * 60)

    # 保存原始环境变量
    original_env = os.environ.copy()

    try:
        # 设置测试环境变量
        os.environ["ENVIRONMENT"] = "test"
        os.environ["SECURITY_ENABLED"] = "true"

        # 运行测试
        all_passed = True

        if not test_imports():
            all_passed = False

        if not test_security_engine_initialization():
            all_passed = False

        if not test_individual_components():
            all_passed = False

        print("\n" + "=" * 60)
        if all_passed:
            print("✅ 所有安全模块测试通过！")
        else:
            print("❌ 部分安全模块测试失败")

        return all_passed

    finally:
        # 恢复原始环境变量
        os.environ.clear()
        os.environ.update(original_env)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)