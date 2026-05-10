#!/usr/bin/env python3
"""
Molin-OS-Ultra v7.0 — 系统完整性检查
验证融合后所有组件是否就绪
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

def check_integrity():
    """全面完整性检查"""
    print("🔍 Molin-OS-Ultra v7.0 完整性检查\n")
    print("=" * 60)

    total_checks = 0
    passed = 0
    warnings = 0
    errors = 0

    # ── 1. 配置文件检查 ──
    print("\n📋 [1/8] 配置文件")
    config_files = {
        "subsidiaries.toml": "子公司唯一权威配置",
        "managers.toml": "Manager调度层配置",
        "models.toml": "模型路由配置",
        "governance.yaml": "4级治理规则",
        "routing.toml": "路由配置",
        "memory.toml": "记忆系统配置",
        "channels.yaml": "渠道配置",
    }
    for fname, desc in config_files.items():
        total_checks += 1
        path = PROJECT_ROOT / "config" / fname
        if path.exists():
            passed += 1
            print(f"  🟢 {fname} — {desc}")
        else:
            warnings += 1
            print(f"  🟡 {fname} — {desc} (缺失)")

    # ── 2. 认知框架检查 ──
    print("\n🧠 [2/8] 认知框架")
    for fname in ["SOUL.md", "AGENTS.md"]:
        total_checks += 1
        if (PROJECT_ROOT / fname).exists():
            passed += 1
            print(f"  🟢 {fname}")
        else:
            errors += 1
            print(f"  🔴 {fname} (关键文件缺失!)")

    # ── 3. 核心引擎检查 ──
    print("\n⚙️ [3/8] 核心引擎 (来自 AI-System)")
    core_files = [
        "core/ceo/ceo.py", "core/ceo/main.py", "core/ceo/intent_processor.py",
        "core/ceo/model_router.py", "core/ceo/ceo_reasoning.py",
        "core/managers/base_manager.py", "core/managers/manager_dispatcher.py",
        "core/managers/quality_gate.py",
    ]
    for f in core_files:
        total_checks += 1
        if (PROJECT_ROOT / f).exists():
            passed += 1
            print(f"  🟢 {f}")
        else:
            errors += 1
            print(f"  🔴 {f}")

    # ── 4. Agency 层检查 ──
    print("\n🏢 [4/8] Agency 层")
    agency_files = ["agencies/base.py", "agencies/worker.py", "agencies/dispatcher.py"]
    for f in agency_files:
        total_checks += 1
        if (PROJECT_ROOT / f).exists():
            passed += 1
            print(f"  🟢 {f}")
        else:
            errors += 1
            print(f"  🔴 {f}")

    # 子公司目录
    agency_dirs = [d.name for d in (PROJECT_ROOT / "agencies").iterdir()
                   if d.is_dir() and d.name not in ("workers", "__pycache__")]
    print(f"  📊 子公司目录: {len(agency_dirs)} 个 — {', '.join(sorted(agency_dirs)[:10])}...")

    # ── 5. Bot 脚本检查 (来自 Molin-OS) ──
    print("\n🤖 [5/8] Bot 脚本 (来自 Molin-OS)")
    bot_dir = PROJECT_ROOT / "bots"
    if bot_dir.exists():
        bots = list(bot_dir.glob("*.py"))
        total_checks += 1
        passed += 1
        print(f"  🟢 {len(bots)} 个 Bot 脚本")
        key_bots = ["xianyu_bot.py", "xhs_bot.py", "flywheel_content.py",
                     "daily_briefing.py", "daily_hot_report.py"]
        for b in key_bots:
            total_checks += 1
            if (bot_dir / b).exists():
                passed += 1
                print(f"    🟢 {b}")
            else:
                warnings += 1
                print(f"    🟡 {b}")

    # ── 6. 飞书集成检查 (来自 AI-System) ──
    print("\n💬 [6/8] 飞书集成")
    feishu_dir = PROJECT_ROOT / "integrations" / "feishu"
    if feishu_dir.exists():
        feishu_files = list(feishu_dir.glob("*.py"))
        total_checks += 1
        passed += 1
        print(f"  🟢 {len(feishu_files)} 个飞书模块")
    else:
        total_checks += 1
        errors += 1
        print(f"  🔴 飞书集成目录缺失")

    # ── 7. 基础设施检查 ──
    print("\n🏗️ [7/8] 基础设施")
    infra_modules = {
        "infra/memory/memory_manager.py": "5层记忆管理器",
        "infra/memory/qdrant_client.py": "Qdrant向量存储",
        "infra/memory/sqlite_client.py": "SQLite事务存储",
        "infra/self_healing/": "自愈引擎",
        "infra/monitoring/": "Prometheus监控",
        "infra/scheduler/": "APScheduler定时",
        "infra/event_bus.py": "事件总线",
        "sop/engine.py": "SOP引擎",
        "strategy/": "战略引擎",
    }
    for path_str, desc in infra_modules.items():
        total_checks += 1
        path = PROJECT_ROOT / path_str
        if path.exists():
            passed += 1
            print(f"  🟢 {desc} ({path_str})")
        else:
            warnings += 1
            print(f"  🟡 {desc} ({path_str})")

    # ── 8. 商业方案检查 (来自 Molin-OS) ──
    print("\n💰 [8/8] 商业方案")
    biz_dir = PROJECT_ROOT / "business"
    if biz_dir.exists():
        biz_files = list(biz_dir.glob("*.md"))
        total_checks += 1
        passed += 1
        print(f"  🟢 {len(biz_files)} 个商业方案文档")
    else:
        total_checks += 1
        warnings += 1
        print(f"  🟡 商业方案目录缺失")

    # ── 汇总 ──
    print("\n" + "=" * 60)
    print(f"\n📊 检查汇总:")
    print(f"  ✅ 通过: {passed}/{total_checks}")
    print(f"  ⚠️ 警告: {warnings}")
    print(f"  ❌ 错误: {errors}")

    if errors == 0:
        print(f"\n🟢 Molin-OS-Ultra v7.0 融合系统完整性检查通过!")
    else:
        print(f"\n🔴 有 {errors} 个关键错误需要修复")

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(check_integrity())