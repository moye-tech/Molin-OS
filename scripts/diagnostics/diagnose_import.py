#!/usr/bin/env python3
"""
诊断hermes-agent导入问题
"""

import sys
import os

print("Python路径:", sys.executable)
print("Python版本:", sys.version)
print("\n系统路径:")
for i, p in enumerate(sys.path[:20]):
    print(f"  {i}: {p}")

print("\n元路径查找器:")
for i, finder in enumerate(sys.meta_path):
    print(f"  {i}: {finder}")

print("\n检查可编辑安装映射...")
finder_path = "/Users/moye/Downloads/molin-ai-pro/venv/lib/python3.12/site-packages/__editable___hermes_agent_0_10_0_finder.py"
if os.path.exists(finder_path):
    print(f"✓ 映射文件存在: {finder_path}")

    # 尝试导入映射文件
    import importlib.util
    spec = importlib.util.spec_from_file_location("editable_finder", finder_path)
    if spec and spec.loader:
        try:
            editable_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(editable_module)
            print("✓ 映射文件可加载")

            # 调用install方法
            if hasattr(editable_module, 'install'):
                editable_module.install()
                print("✓ 映射安装函数调用成功")
        except Exception as e:
            print(f"✗ 映射文件加载失败: {e}")
else:
    print(f"✗ 映射文件不存在")

print("\n尝试手动导入模块...")
try:
    # 检查hermes-agent目录
    hermes_agent_dir = "/Users/moye/Downloads/molin-ai-pro/upstream/hermes-agent"
    if os.path.exists(hermes_agent_dir):
        print(f"✓ hermes-agent目录存在: {hermes_agent_dir}")

        # 添加到Python路径
        sys.path.insert(0, hermes_agent_dir)

        # 尝试导入
        try:
            import hermes_agent
            print(f"✓ hermes_agent导入成功: {hermes_agent.__file__}")
        except ImportError as e:
            print(f"✗ hermes_agent导入失败: {e}")

        # 检查agent模块
        try:
            import agent
            print(f"✓ agent导入成功: {agent.__file__}")
        except ImportError as e:
            print(f"✗ agent导入失败: {e}")
    else:
        print(f"✗ hermes-agent目录不存在: {hermes_agent_dir}")
except Exception as e:
    print(f"诊断过程出错: {e}")

print("\n检查pip安装状态...")
import subprocess
result = subprocess.run([sys.executable, "-m", "pip", "show", "hermes-agent"],
                       capture_output=True, text=True)
if result.returncode == 0:
    print("✓ hermes-agent通过pip安装")
    print(result.stdout[:200])
else:
    print("✗ hermes-agent未通过pip安装")