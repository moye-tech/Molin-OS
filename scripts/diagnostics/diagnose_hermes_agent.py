"""
诊断hermes-agent安装状态
"""

import sys
import os
import subprocess
import pkgutil
import importlib

def check_python_environment():
    """检查Python环境"""
    print("=" * 60)
    print("Python环境检查")
    print("=" * 60)

    print(f"Python可执行文件: {sys.executable}")
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.prefix}")
    print(f"虚拟环境: {'是' if hasattr(sys, 'real_prefix') or sys.prefix != sys.base_prefix else '否'}")

def check_pip_installation():
    """检查pip安装状态"""
    print("\n" + "=" * 60)
    print("pip安装检查")
    print("=" * 60)

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "hermes-agent"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print("✓ hermes-agent已通过pip安装")
            for line in result.stdout.split('\n'):
                if line.strip():
                    print(f"  {line}")
        else:
            print("✗ hermes-agent未通过pip安装")
            print(f"  错误: {result.stderr}")
    except Exception as e:
        print(f"✗ pip检查失败: {e}")

def check_module_imports():
    """检查模块导入"""
    print("\n" + "=" * 60)
    print("模块导入检查")
    print("=" * 60)

    modules_to_check = [
        'hermes_agent',
        'agent',
        'hermes_cli',
        'run_agent',
        'skills',
    ]

    for module_name in modules_to_check:
        try:
            # 首先尝试直接导入
            module = importlib.import_module(module_name)
            print(f"✓ 成功导入模块: {module_name}")
            print(f"  位置: {getattr(module, '__file__', '未知')}")
        except ImportError as e:
            print(f"✗ 导入模块失败: {module_name}")
            print(f"  错误: {e}")

def check_upstream_directory():
    """检查上游目录"""
    print("\n" + "=" * 60)
    print("上游目录检查")
    print("=" * 60)

    upstream_path = os.path.join(os.path.dirname(__file__), 'upstream', 'hermes-agent')

    if os.path.exists(upstream_path):
        print(f"✓ 上游目录存在: {upstream_path}")

        # 检查关键文件
        key_files = [
            ('pyproject.toml', '项目配置'),
            ('run_agent.py', '主运行脚本'),
            ('agent/__init__.py', 'agent模块'),
            ('hermes_cli/__init__.py', 'hermes_cli模块'),
            ('skills/', '技能目录'),
        ]

        for file_path, description in key_files:
            full_path = os.path.join(upstream_path, file_path)
            if os.path.exists(full_path):
                print(f"  ✓ {description}: {file_path}")
            else:
                print(f"  ✗ {description}: {file_path} (不存在)")
    else:
        print(f"✗ 上游目录不存在: {upstream_path}")

def check_editable_installation():
    """检查可编辑安装"""
    print("\n" + "=" * 60)
    print("可编辑安装检查")
    print("=" * 60)

    # 检查是否有可编辑安装的hermes-agent
    import site
    import pkg_resources

    editable_packages = []

    try:
        for dist in pkg_resources.working_set:
            if dist.location and 'hermes' in dist.key:
                editable_packages.append({
                    'name': dist.key,
                    'version': dist.version,
                    'location': dist.location,
                    'editable': dist.editable
                })
    except:
        pass

    if editable_packages:
        print("✓ 找到hermes相关包:")
        for pkg in editable_packages:
            print(f"  {pkg['name']}=={pkg['version']}")
            print(f"    位置: {pkg['location']}")
            print(f"    可编辑: {pkg['editable']}")
    else:
        print("✗ 未找到hermes相关包")

def check_entry_points():
    """检查入口点"""
    print("\n" + "=" * 60)
    print("入口点检查")
    print("=" * 60)

    entry_points = [
        ('hermes', '主CLI命令'),
        ('hermes-agent', 'agent命令'),
        ('hermes-acp', 'ACP命令'),
    ]

    for cmd, description in entry_points:
        try:
            result = subprocess.run(
                ['which', cmd],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                print(f"✓ {description} ({cmd}): {result.stdout.strip()}")
            else:
                print(f"✗ {description} ({cmd}): 未找到")
        except Exception as e:
            print(f"✗ 检查{cmd}失败: {e}")

def check_skill_system():
    """检查技能系统"""
    print("\n" + "=" * 60)
    print("技能系统检查")
    print("=" * 60)

    upstream_path = os.path.join(os.path.dirname(__file__), 'upstream', 'hermes-agent')
    skills_path = os.path.join(upstream_path, 'skills')

    if os.path.exists(skills_path):
        print(f"✓ 技能目录存在: {skills_path}")

        # 统计技能数量
        skill_categories = []
        for item in os.listdir(skills_path):
            item_path = os.path.join(skills_path, item)
            if os.path.isdir(item_path):
                skill_categories.append(item)

        print(f"  技能类别数量: {len(skill_categories)}")
        print(f"  前5个类别: {', '.join(skill_categories[:5])}")

        # 检查是否有BaseSkill或技能基类
        base_skill_files = []
        for root, dirs, files in os.walk(upstream_path):
            for file in files:
                if 'base' in file.lower() and 'skill' in file.lower() and file.endswith('.py'):
                    base_skill_files.append(os.path.relpath(os.path.join(root, file), upstream_path))

        if base_skill_files:
            print(f"  找到技能基类文件:")
            for file in base_skill_files[:3]:
                print(f"    - {file}")
        else:
            print(f"  未找到技能基类文件")
    else:
        print(f"✗ 技能目录不存在")

def check_configuration():
    """检查配置"""
    print("\n" + "=" * 60)
    print("配置检查")
    print("=" * 60)

    config_path = os.path.join(os.path.dirname(__file__), 'config', 'hermes-agent', 'config.yaml')

    if os.path.exists(config_path):
        print(f"✓ 配置文件存在: {config_path}")

        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if 'skills' in config:
                print(f"  配置中包含 {len(config['skills'])} 个技能")
                for skill_name in list(config['skills'].keys())[:5]:
                    skill = config['skills'][skill_name]
                    print(f"    - {skill.get('name', skill_name)}: {skill.get('description', '无描述')}")
        except Exception as e:
            print(f"  ✗ 配置文件解析失败: {e}")
    else:
        print(f"✗ 配置文件不存在: {config_path}")

def main():
    """主诊断函数"""
    print("墨麟AI安装状态诊断")
    print("=" * 60)

    checks = [
        check_python_environment,
        check_pip_installation,
        check_module_imports,
        check_upstream_directory,
        check_editable_installation,
        check_entry_points,
        check_skill_system,
        check_configuration,
    ]

    for check_func in checks:
        try:
            check_func()
        except Exception as e:
            print(f"\n检查函数{check_func.__name__}失败: {e}")

    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)

if __name__ == "__main__":
    main()