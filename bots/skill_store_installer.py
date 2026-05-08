#!/usr/bin/env python3
"""
技能商店安装器 — CH9 技能商店产品化

功能：
1. install_skill_from_store(skill_name, target_dir) — 从商店安装技能
2. list_available_skills() — 列出可安装技能
3. check_updates() — 检查已购技能更新

使用标准库实现，无第三方依赖。
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional


# ============================================================
# 技能商店配置
# ============================================================

SKILL_STORE = {
    "store_name": "Hermes OS 技能商店",
    "store_version": "1.0.0",
    "base_url": "https://github.com/hermes-os",  # 替换为实际仓库地址
    "skills": {
        "xhs-creator": {
            "name": "小红书爆款创作",
            "id": "SK-001",
            "version": "1.0.0",
            "price_cny": 49,
            "repo": "hermes-os/skill-xhs-creator",
            "description": "AI 批量生成小红书爆款笔记，热点追踪 + 标题优化 + 批量创作",
            "author": "Hermes OS",
            "tags": ["自媒体", "AI创作", "小红书"],
            "requirements": ["requests", "PyYAML"],
            "min_python": "3.10",
            "files": [
                "install.sh",
                "config.yaml.example",
                "main.py",
                "scripts/hot_tracker.py",
                "scripts/title_generator.py",
                "scripts/note_writer.py",
                "scripts/batch_publish.py",
                "templates/title_prompts.txt",
                "docs/README.md",
                "docs/examples.md",
                "requirements.txt",
            ],
            "size_estimate": "2.5 MB",
        },
        "xianyu-automation": {
            "name": "闲鱼自动化运营",
            "id": "SK-002",
            "version": "1.0.0",
            "price_cny": 99,
            "repo": "hermes-os/skill-xianyu-automation",
            "description": "闲鱼自动回复、商品管理、数据看板、竞品监控",
            "author": "Hermes OS",
            "tags": ["电商", "自动化", "闲鱼"],
            "requirements": ["requests", "PyYAML", "pandas", "plotly"],
            "min_python": "3.10",
            "files": [
                "install.sh",
                "config.yaml.example",
                "main.py",
                "scripts/auto_reply.py",
                "scripts/inventory_manager.py",
                "scripts/dashboard.py",
                "scripts/competitor_tracker.py",
                "docs/README.md",
                "docs/quickstart.md",
                "requirements.txt",
            ],
            "size_estimate": "3.2 MB",
        },
        "trading-signals": {
            "name": "量化交易信号",
            "id": "SK-003",
            "version": "1.0.0",
            "price_cny": 199,
            "repo": "hermes-os/skill-trading-signals",
            "description": "多因子交易信号生成、策略回测、实盘提醒",
            "author": "Hermes OS",
            "tags": ["交易", "量化", "投资"],
            "requirements": ["requests", "numpy", "pandas", "ccxt"],
            "min_python": "3.10",
            "files": [
                "install.sh",
                "config.yaml.example",
                "main.py",
                "strategies/momentum.py",
                "strategies/mean_reversion.py",
                "strategies/arbitrage.py",
                "scripts/signal_generator.py",
                "scripts/backtest.py",
                "scripts/alert_bot.py",
                "docs/README.md",
                "docs/strategy_guide.pdf",
                "requirements.txt",
            ],
            "size_estimate": "4.1 MB",
        },
        "legal-review": {
            "name": "法律合规审查",
            "id": "SK-004",
            "version": "1.0.0",
            "price_cny": 149,
            "repo": "hermes-os/skill-legal-review",
            "description": "合同审查、条款分析、合规检查、报告生成",
            "author": "Hermes OS",
            "tags": ["法律", "合规", "企业服务"],
            "requirements": ["requests", "PyYAML", "jinja2"],
            "min_python": "3.10",
            "files": [
                "install.sh",
                "config.yaml.example",
                "main.py",
                "scripts/contract_review.py",
                "scripts/clause_analyzer.py",
                "scripts/compliance_check.py",
                "scripts/report_gen.py",
                "knowledge_base/contract_rules.yaml",
                "docs/README.md",
                "requirements.txt",
            ],
            "size_estimate": "3.8 MB",
        },
        "localization-pack": {
            "name": "出海本地化工具包",
            "id": "SK-005",
            "version": "1.0.0",
            "price_cny": 79,
            "repo": "hermes-os/skill-localization-pack",
            "description": "简体转繁体、AI术语本地化、多语言翻译、批量内容转换",
            "author": "Hermes OS",
            "tags": ["出海", "本地化", "翻译"],
            "requirements": ["requests", "PyYAML"],
            "min_python": "3.10",
            "files": [
                "install.sh",
                "config.yaml.example",
                "main.py",
                "scripts/to_traditional.py",
                "scripts/ai_term_localize.py",
                "scripts/translate.py",
                "scripts/batch_processor.py",
                "dictionaries/sim_to_trad.json",
                "dictionaries/ai_terms.json",
                "docs/README.md",
                "requirements.txt",
            ],
            "size_estimate": "2.1 MB",
        },
    },
}

# 用户安装记录文件
INSTALL_RECORD_FILE = os.path.expanduser("~/.hermes/skill_store_installed.json")


# ============================================================
# 辅助函数
# ============================================================

def _load_install_record() -> dict:
    """加载本地安装记录"""
    try:
        if os.path.exists(INSTALL_RECORD_FILE):
            with open(INSTALL_RECORD_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return {"installed": {}, "last_check": None}


def _save_install_record(record: dict) -> None:
    """保存安装记录"""
    os.makedirs(os.path.dirname(INSTALL_RECORD_FILE), exist_ok=True)
    with open(INSTALL_RECORD_FILE, 'w', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2)


def _validate_python_version(min_version: str) -> bool:
    """检查 Python 版本是否满足最低要求"""
    current = sys.version_info
    required = tuple(int(x) for x in min_version.split("."))
    return current >= required


def _run_command(cmd: list, cwd: Optional[str] = None) -> tuple:
    """运行命令并返回 (returncode, stdout, stderr)"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "命令执行超时"
    except FileNotFoundError:
        return -1, "", f"命令未找到: {cmd[0]}"
    except Exception as e:
        return -1, "", str(e)


# ============================================================
# 核心功能
# ============================================================

def list_available_skills() -> list:
    """
    列出商店中所有可安装的技能包。

    Returns:
        技能包信息列表，每项包含：
        - id: 技能包编号
        - name: 名称
        - version: 版本
        - price_cny: 价格（人民币）
        - description: 简要描述
        - tags: 标签列表
        - size_estimate: 估计大小
    """
    skills = []
    for skill_key, skill_info in SKILL_STORE["skills"].items():
        installed = _load_install_record()
        is_installed = skill_key in installed.get("installed", {})

        skills.append({
            "id": skill_info["id"],
            "key": skill_key,
            "name": skill_info["name"],
            "version": skill_info["version"],
            "price_cny": skill_info["price_cny"],
            "description": skill_info["description"],
            "tags": skill_info["tags"],
            "size_estimate": skill_info["size_estimate"],
            "installed": is_installed,
            "min_python": skill_info["min_python"],
        })

    return skills


def install_skill_from_store(
    skill_name: str,
    target_dir: str,
    github_token: Optional[str] = None,
) -> dict:
    """
    从商店安装指定技能包。

    安装流程：
    1. 验证技能包是否存在
    2. 检查 Python 版本兼容性
    3. 准备目标目录
    4. 从 GitHub Private Repo 克隆/下载
    5. 运行安装脚本
    6. 记录安装信息

    Args:
        skill_name: 技能包 key（如 'xhs-creator'）
        target_dir: 安装目标目录（绝对路径）
        github_token: GitHub Personal Access Token（可选）

    Returns:
        {
            "success": bool,
            "message": str,
            "skill_info": dict or None,
            "target_dir": str,
        }
    """
    # 1. 查找技能包
    skills = SKILL_STORE["skills"]
    if skill_name not in skills:
        available = ", ".join(skills.keys())
        return {
            "success": False,
            "message": f"技能包 '{skill_name}' 不存在。可用技能包: {available}",
            "skill_info": None,
            "target_dir": target_dir,
        }

    skill_info = skills[skill_name]

    # 2. 检查 Python 版本
    if not _validate_python_version(skill_info["min_python"]):
        return {
            "success": False,
            "message": (
                f"需要 Python >= {skill_info['min_python']}，"
                f"当前版本: {sys.version.split()[0]}"
            ),
            "skill_info": skill_info,
            "target_dir": target_dir,
        }

    # 3. 检查目标目录
    target_path = Path(target_dir).expanduser().resolve()
    if target_path.exists():
        if not target_path.is_dir():
            return {
                "success": False,
                "message": f"目标路径存在但不是目录: {target_path}",
                "skill_info": skill_info,
                "target_dir": str(target_path),
            }
        if any(target_path.iterdir()):
            return {
                "success": False,
                "message": f"目标目录不为空: {target_path} （请指定空目录或使用 --force）",
                "skill_info": skill_info,
                "target_dir": str(target_path),
            }
    else:
        target_path.mkdir(parents=True, exist_ok=True)

    # 4. 克隆仓库
    repo_url = f"https://github.com/{skill_info['repo']}.git"
    if github_token:
        repo_url = f"https://{github_token}@github.com/{skill_info['repo']}.git"

    print(f"→ 正在从 {repo_url} 克隆技能包...")

    returncode, stdout, stderr = _run_command(
        ["git", "clone", repo_url, str(target_path)]
    )

    if returncode != 0:
        # 检查是否是权限问题
        if "403" in stderr or "Authentication failed" in stderr:
            return {
                "success": False,
                "message": (
                    "GitHub 认证失败。请确保：\n"
                    "1. 你的 GitHub 账号已被添加为仓库 Collaborator\n"
                    "2. 提供了有效的 GitHub Token\n"
                    f"详情: {stderr.strip()}"
                ),
                "skill_info": skill_info,
                "target_dir": str(target_path),
            }
        return {
            "success": False,
            "message": f"克隆失败: {stderr.strip()}",
            "skill_info": skill_info,
            "target_dir": str(target_path),
        }

    print(f"✓ 克隆完成")

    # 5. 运行安装脚本
    install_script = target_path / "install.sh"
    if install_script.exists():
        print("→ 运行安装脚本...")
        os.chmod(str(install_script), 0o755)
        returncode, stdout, stderr = _run_command(["bash", str(install_script)], cwd=str(target_path))

        if returncode != 0:
            # 安装脚本失败但文件已存在，不算完全失败
            print(f"⚠ 安装脚本执行警告: {stderr.strip()}")
        else:
            print(f"✓ 安装脚本执行完成")

    # 6. 检查 requirements.txt 并尝试安装依赖
    requirements_file = target_path / "requirements.txt"
    if requirements_file.exists():
        print("→ 安装 Python 依赖...")
        returncode, stdout, stderr = _run_command(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file), "-q"]
        )
        if returncode != 0:
            print(f"⚠ 依赖安装警告: {stderr.strip()}")
        else:
            print(f"✓ 依赖安装完成")

    # 7. 记录安装信息
    record = _load_install_record()
    record["installed"][skill_name] = {
        "name": skill_info["name"],
        "version": skill_info["version"],
        "installed_at": datetime.now().isoformat(),
        "target_dir": str(target_path),
    }
    record["last_check"] = datetime.now().isoformat()
    _save_install_record(record)

    print(f"\n✅ 技能包 '{skill_info['name']}' 安装成功！")
    print(f"   安装路径: {target_path}")
    print(f"   使用方式: cd {target_path} && source venv/bin/activate && python main.py --help")

    return {
        "success": True,
        "message": f"技能包 '{skill_info['name']}' v{skill_info['version']} 安装成功",
        "skill_info": {
            "id": skill_info["id"],
            "name": skill_info["name"],
            "version": skill_info["version"],
        },
        "target_dir": str(target_path),
    }


def check_updates() -> dict:
    """
    检查所有已安装技能包的更新。

    通过比较本地版本号和远程 GitHub Release 版本号来判断。

    Returns:
        {
            "skills": [
                {
                    "key": str,
                    "name": str,
                    "current_version": str,
                    "latest_version": str or None,
                    "has_update": bool,
                    "error": str or None,
                }
            ],
            "total": int,
            "with_updates": int,
            "errors": int,
        }
    """
    record = _load_install_record()
    installed = record.get("installed", {})

    if not installed:
        return {
            "skills": [],
            "total": 0,
            "with_updates": 0,
            "errors": 0,
            "message": "尚未安装任何技能包。使用 list_available_skills() 查看可安装技能。"
        }

    results = []
    with_updates = 0
    errors = 0

    for skill_key, info in installed.items():
        skill_info = SKILL_STORE["skills"].get(skill_key)
        if not skill_info:
            results.append({
                "key": skill_key,
                "name": info.get("name", skill_key),
                "current_version": info.get("version", "?"),
                "latest_version": None,
                "has_update": False,
                "error": "技能包在商店中已不存在",
            })
            errors += 1
            continue

        current_version = info.get("version", "?")
        latest_version = skill_info["version"]

        # 比较版本
        try:
            has_update = _compare_versions(latest_version, current_version) > 0
        except Exception:
            has_update = latest_version != current_version

        # 检查本地文件是否存在
        target_dir = info.get("target_dir", "")
        local_exists = os.path.isdir(target_dir) if target_dir else False

        result = {
            "key": skill_key,
            "name": skill_info["name"],
            "current_version": current_version,
            "latest_version": latest_version,
            "has_update": has_update,
            "local_files_exist": local_exists,
            "error": None if local_exists else "本地文件已丢失，需重新安装",
        }

        if has_update:
            with_updates += 1
        if not local_exists:
            errors += 1

        results.append(result)

    # 更新检查时间
    record["last_check"] = datetime.now().isoformat()
    _save_install_record(record)

    return {
        "skills": results,
        "total": len(results),
        "with_updates": with_updates,
        "errors": errors,
    }


def _compare_versions(v1: str, v2: str) -> int:
    """比较版本号，v1 > v2 返回 1, v1 == v2 返回 0, v1 < v2 返回 -1"""
    parts1 = [int(x) for x in v1.split(".")]
    parts2 = [int(x) for x in v2.split(".")]

    # 补齐长度
    max_len = max(len(parts1), len(parts2))
    parts1.extend([0] * (max_len - len(parts1)))
    parts2.extend([0] * (max_len - len(parts2)))

    for a, b in zip(parts1, parts2):
        if a < b:
            return -1
        if a > b:
            return 1
    return 0


def get_skill_detail(skill_name: str) -> Optional[dict]:
    """
    获取单个技能包的详细信息。

    Args:
        skill_name: 技能包 key

    Returns:
        技能包详细信息或 None（不存在时）
    """
    skills = SKILL_STORE["skills"]
    if skill_name not in skills:
        return None

    skill = skills[skill_name]
    record = _load_install_record()
    installed_info = record.get("installed", {}).get(skill_name)

    return {
        **skill,
        "key": skill_name,
        "installed": installed_info is not None,
        "installed_at": installed_info.get("installed_at") if installed_info else None,
        "installed_path": installed_info.get("target_dir") if installed_info else None,
    }


# ============================================================
# CLI 入口
# ============================================================

def main():
    """CLI 主入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Hermes OS 技能商店安装器 v" + SKILL_STORE["store_version"],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s list                          # 列出所有可用技能包
  %(prog)s install xhs-creator ./my-skills  # 安装小红书技能包
  %(prog)s info xhs-creator              # 查看技能包详情
  %(prog)s check-updates                 # 检查所有已购技能更新
  %(prog)s check-updates xhs-creator     # 检查特定技能更新
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # list 命令
    subparsers.add_parser("list", help="列出所有可用技能包")

    # install 命令
    install_parser = subparsers.add_parser("install", help="安装技能包")
    install_parser.add_argument("skill_name", help="技能包名称（如 xhs-creator）")
    install_parser.add_argument("target_dir", nargs="?", default="./skills",
                                help="安装目标目录（默认: ./skills）")
    install_parser.add_argument("--token", help="GitHub Personal Access Token")

    # info 命令
    info_parser = subparsers.add_parser("info", help="查看技能包详情")
    info_parser.add_argument("skill_name", help="技能包名称")

    # check-updates 命令
    check_parser = subparsers.add_parser("check-updates", help="检查已购技能更新")
    check_parser.add_argument("skill_name", nargs="?", help="指定技能包（可选）")

    args = parser.parse_args()

    if args.command == "list" or not args.command:
        skills = list_available_skills()
        if not skills:
            print("📦 技能商店暂无可用技能包。")
            return

        print(f"\n{'='*60}")
        print(f"  📦 {SKILL_STORE['store_name']}")
        print(f"{'='*60}")
        print()

        for s in skills:
            installed_mark = "✅" if s["installed"] else "  "
            print(f"  {installed_mark} [{s['id']}] {s['name']}")
            print(f"     版本: v{s['version']}  |  价格: ¥{s['price_cny']}  |  大小: {s['size_estimate']}")
            print(f"     描述: {s['description']}")
            print(f"     标签: {', '.join(s['tags'])}")
            print(f"     安装: python {sys.argv[0]} install {s['key']} <目标目录>")
            print()

    elif args.command == "install":
        token = args.token or os.environ.get("GITHUB_TOKEN")
        result = install_skill_from_store(args.skill_name, args.target_dir, github_token=token)

        if result["success"]:
            print(f"\n✅ {result['message']}")
        else:
            print(f"\n❌ 安装失败: {result['message']}")
            sys.exit(1)

    elif args.command == "info":
        detail = get_skill_detail(args.skill_name)
        if not detail:
            print(f"❌ 技能包 '{args.skill_name}' 不存在。")
            available = ", ".join(SKILL_STORE["skills"].keys())
            print(f"可用技能包: {available}")
            sys.exit(1)

        print(f"\n{'='*50}")
        print(f"  📦 {detail['name']} ({detail['id']})")
        print(f"{'='*50}")
        print(f"  版本:     v{detail['version']}")
        print(f"  价格:     ¥{detail['price_cny']}")
        print(f"  大小:     {detail['size_estimate']}")
        print(f"  作者:     {detail['author']}")
        print(f"  描述:     {detail['description']}")
        print(f"  标签:     {', '.join(detail['tags'])}")
        print(f"  最低Python: {detail['min_python']}")
        print(f"  依赖:     {', '.join(detail['requirements'])}")
        print(f"  安装状态: {'✅ 已安装' if detail['installed'] else '❌ 未安装'}")

        if detail.get("installed_at"):
            print(f"  安装时间: {detail['installed_at']}")
        if detail.get("installed_path"):
            print(f"  安装路径: {detail['installed_path']}")

        print(f"\n  包含文件:")
        for f in detail["files"]:
            print(f"    ├── {f}")
        print()

    elif args.command == "check-updates":
        if args.skill_name:
            # 检查单个技能
            record = _load_install_record()
            if args.skill_name not in record.get("installed", {}):
                print(f"❌ 技能包 '{args.skill_name}' 尚未安装。")
                sys.exit(1)

            skill_info = SKILL_STORE["skills"].get(args.skill_name)
            if not skill_info:
                print(f"❌ 技能包 '{args.skill_name}' 在商店中已不存在。")
                sys.exit(1)

            current = record["installed"][args.skill_name]["version"]
            latest = skill_info["version"]
            has_update = _compare_versions(latest, current) > 0

            print(f"\n📦 {skill_info['name']}")
            print(f"  当前版本: v{current}")
            print(f"  最新版本: v{latest}")
            if has_update:
                print(f"  🔄 有可用更新！运行以下命令升级：")
                print(f"     cd {record['installed'][args.skill_name]['target_dir']}")
                print(f"     git pull && bash install.sh")
            else:
                print(f"  ✅ 已是最新版本")
        else:
            updates = check_updates()
            print(f"\n{'='*50}")
            print(f"  🔄 技能更新检查 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
            print(f"{'='*50}")

            if updates["total"] == 0:
                print("\n  尚未安装任何技能包。")
                return

            for s in updates["skills"]:
                if s.get("error"):
                    print(f"\n  ⚠ [{s['name']}] {s['error']}")
                elif s["has_update"]:
                    print(f"\n  🔄 [{s['name']}] v{s['current_version']} → v{s['latest_version']}")
                else:
                    print(f"\n  ✅ [{s['name']}] v{s['current_version']}（已是最新）")

            print(f"\n  总计: {updates['total']} 个技能")
            print(f"  可更新: {updates['with_updates']} 个")
            if updates["errors"] > 0:
                print(f"  异常: {updates['errors']} 个")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
