#!/usr/bin/env python3
"""
内容飞轮编排器 — 墨麟全媒体运营的核心指挥官

串联完整飞轮：
  情报层(08:00) → 内容层(09:20) → 分发层(10:30) → 数据回收(11:00)

铁律：
  - 第二棒必须等第一棒产出 relay/media/intelligence.json
  - 任何一棒失败立刻发T4告警（red header，3句话原则）
  - 数据回收结果必须反哺下一轮情报层选题
  - 支持 --quick 模式跳过某些阶段用于快速调试

用法：
  # 全流程运行
  python3 orchestrate_flywheel.py
  
  # 只跑情报层（测试）
  python3 orchestrate_flywheel.py --stages intelligence
  
  # 从指定阶段开始跑（接力场景）
  python3 orchestrate_flywheel.py --from intelligence
  
  # 快速模式（跳过分发层）
  python3 orchestrate_flywheel.py --quick
"""

import json
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

# ─── 路径 ────────────────────────────────────────────────────────

MEDIA_ROOT = "/Users/laomo/.hermes/profiles/media"
RELAY_DIR = Path(f"{MEDIA_ROOT}/relay")
SCRIPTS_DIR = Path(f"{MEDIA_ROOT}/scripts")
HERMES_SCRIPTS = Path("/Users/laomo/.hermes/scripts")

INTELLIGENCE_PATH = RELAY_DIR / "intelligence.json"
COPYWRITER_OUTPUT = RELAY_DIR / "copywriter_output.json"
DESIGNER_OUTPUT = RELAY_DIR / "designer_output.json"
VIDEO_OUTPUT = RELAY_DIR / "video_producer_output.json"
VOICEOVER_OUTPUT = RELAY_DIR / "voiceover_output.json"
ANALYTICS_FEEDBACK = RELAY_DIR / "analytics_feedback.json"
TITLE_FORMULAS = RELAY_DIR / "title_formulas.json"
TRENDING_REPORT = RELAY_DIR / "trending_topics.md"

# ─── 阶段定义 ────────────────────────────────────────────────────

STAGES = {
    "intelligence": {
        "label": "情报层",
        "time": "08:00",
        "description": "采集热词、竞品分析、选题推荐",
        "check": INTELLIGENCE_PATH,
        "depends_on": [],
        "scripts": [
            {"name": "collect_intelligence.py",
             "path": HERMES_SCRIPTS / "collect_intelligence.py",
             "timeout": 120},
        ],
        "fallback": "使用缓存数据，标记数据未更新",
    },
    "content": {
        "label": "内容层",
        "time": "09:20",
        "description": "文案创作、配图设计、视频脚本",
        "check": [COPYWRITER_OUTPUT, DESIGNER_OUTPUT, VIDEO_OUTPUT],
        "depends_on": ["intelligence"],
        "scripts": [
            {"name": "content_producer.py",
             "path": HERMES_SCRIPTS / "content_producer.py",
             "timeout": 30,
             "note": "生成小红书+抖音+公众号+B站四平台内容"},
        ],
        "fallback": "生成基础文案，跳过配图生成",
    },
    "distribution": {
        "label": "分发层",
        "time": "10:30",
        "description": "增长策略、投放优化、私域引流",
        "check": [],
        "depends_on": ["content"],
        "scripts": [
            {"name": "触发墨增引擎（AI Agent）",
             "path": None, "timeout": 0,
             "note": "由Hermes Agent自动加载 墨增引擎 SKILL.md 执行"},
        ],
        "fallback": "延后分发，等待内容层完成",
    },
    "analytics": {
        "label": "数据回收",
        "time": "11:00",
        "description": "内容效果分析、爆款归因、反馈闭环",
        "check": [],
        "depends_on": ["content"],
        "scripts": [
            {"name": "update_title_formulas.py",
             "path": HERMES_SCRIPTS / "update_title_formulas.py",
             "timeout": 30},
        ],
        "fallback": "跳过数据分析，标记数据回收未完成",
    },
}

STAGE_ORDER = ["intelligence", "content", "distribution", "analytics"]


# ─── 工具函数 ────────────────────────────────────────────────────

def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stage_file_exists(paths) -> bool:
    """检查阶段产出文件是否存在"""
    if isinstance(paths, Path):
        return paths.exists()
    if isinstance(paths, list):
        return all(p.exists() for p in paths if p)
    return False


def load_json_safe(path: Path) -> dict:
    """安全加载JSON"""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        return {}


def send_t4_alert(stage: str, reason: str):
    """发送飞书T4告警"""
    alert = (
        f"[T4] 内容飞轮中断\n"
        f"  阶段: {STAGES[stage]['label']} ({stage})\n"
        f"  时间: {now_str()}\n"
        f"  原因: {reason}\n"
        f"  降级: {STAGES[stage]['fallback']}"
    )
    print(f"\n🚨 T4 ALERT\n{alert}\n")
    # 这里可以集成飞书消息推送


def orchestrate_stage(stage_name: str, dry_run: bool = False, 
                       skip_checks: bool = False) -> bool:
    """
    执行单个飞轮阶段
    
    Returns:
        True = 成功, False = 失败（触发降级）
    """
    stage = STAGES[stage_name]
    print(f"\n{'='*60}")
    print(f"  [{stage['time']}] ▶ {stage['label']}: {stage['description']}")
    print(f"{'='*60}")

    # 检查依赖
    if not skip_checks:
        for dep in stage["depends_on"]:
            dep_stage = STAGES[dep]
            dep_check = dep_stage["check"]
            if dep_check and not stage_file_exists(dep_check):
                msg = f"依赖阶段 {dep_stage['label']} 的产出文件缺失: {dep_check}"
                print(f"  ✗ {msg}")
                send_t4_alert(stage_name, msg)
                return False

    # 执行脚本
    all_success = True
    for script in stage["scripts"]:
        script_path = script.get("path")
        script_name = script.get("name")
        note = script.get("note", "")

        if script_path is None:
            # Agent脚本（需要Hermes人工或技能加载）
            print(f"  ⏳ {script_name}")
            if note:
                print(f"     说明: {note}")
            continue

        if not script_path.exists():
            print(f"  ✗ 脚本不存在: {script_path}")
            all_success = False
            continue

        if dry_run:
            print(f"  🔷 DRY RUN: 跳过执行 {script_path.name}")
            continue

        try:
            print(f"  ⏳ 执行 {script_path.name}...")
            start = time.time()
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True, text=True,
                timeout=script.get("timeout", 60),
                cwd=str(MEDIA_ROOT),
            )
            elapsed = time.time() - start

            if result.returncode == 0:
                print(f"  ✓ {script_path.name} 完成 ({elapsed:.1f}s)")
                # 输出摘要
                for line in result.stdout.strip().split("\n"):
                    if line.startswith("SUMMARY:") or line.startswith("✅") or line.startswith("📊"):
                        print(f"    {line}")
            else:
                print(f"  ✗ {script_path.name} 失败 (exit={result.returncode}, {elapsed:.1f}s)")
                if result.stderr:
                    for line in result.stderr.strip().split("\n")[:5]:
                        print(f"     {line}")
                all_success = False

        except subprocess.TimeoutExpired:
            print(f"  ✗ {script_name} 超时 ({script.get('timeout', 60)}s)")
            all_success = False
        except Exception as e:
            print(f"  ✗ {script_name} 异常: {e}")
            all_success = False

    # 检查产出
    if stage["check"] and not skip_checks:
        if not stage_file_exists(stage["check"]):
            print(f"  ⚠ 阶段产出文件未生成: {stage['check']}")
            all_success = False

    summary = "✓ 完成" if all_success else "✗ 失败（触发降级）"
    print(f"\n  {stage['label']}: {summary}")

    return all_success


def print_flywheel_status():
    """打印飞轮各阶段状态"""
    print("\n📊 内容飞轮状态检查")
    print("-" * 40)
    
    status_items = []
    for stage_name in STAGE_ORDER:
        stage = STAGES[stage_name]
        check = stage["check"]
        if check:
            exists = stage_file_exists(check)
            icon = "✅" if exists else "⬜"
            paths = check if isinstance(check, list) else [check]
            names = [str(p.name) for p in paths]
            status_items.append(f"  {icon} {stage['label']}: {', '.join(names)}")
        else:
            status_items.append(f"  ➖ {stage['label']}: 无前置检查")

    for item in status_items:
        print(item)
    print()

    # 检查intelligence.json内容
    intel = load_json_safe(INTELLIGENCE_PATH)
    if intel.get("ready_for_consumption"):
        topics_count = len(intel.get("hot_topics", []))
        print(f"  📋 intelligence.json: {topics_count} 条热词, 状态可用")
    else:
        print(f"  📋 intelligence.json: 数据未就绪或不存在")

    # 检查标题公式库
    formulas = load_json_safe(TITLE_FORMULAS)
    if formulas.get("total_analyzed_posts", 0) > 0:
        print(f"  📝 title_formulas.json: {formulas['total_analyzed_posts']} 条内容分析记录")
    else:
        print(f"  📝 title_formulas.json: 初始状态")


def run_flywheel(stages: list = None, from_stage: str = None,
                  dry_run: bool = False, quick: bool = False):
    """运行内容飞轮"""
    if stages is None:
        stages = STAGE_ORDER

    if from_stage:
        if from_stage in stages:
            start_idx = stages.index(from_stage)
            stages = stages[start_idx:]
        else:
            print(f"✗ 未知阶段: {from_stage}")
            return False

    if quick:
        stages = [s for s in stages if s != "distribution"]
        print("🔷 快速模式: 跳过分发层")
        print()

    print(f"🚀 内容飞轮启动 | {now_str()}")
    print(f"   阶段: {' → '.join(STAGES[s]['label'] for s in stages)}")
    print(f"   模式: {'Dry Run' if dry_run else 'Live'}")

    results = {}
    all_passed = True

    for stage_name in stages:
        success = orchestrate_stage(stage_name, dry_run=dry_run)
        results[stage_name] = success
        if not success:
            all_passed = False
            # 如果某阶段失败，执行降级策略
            print(f"\n  ⚠ 执行降级: {STAGES[stage_name]['fallback']}")
            # 但不中断后续阶段（flywheel允许降级继续）
            print()

    # 总结
    print()
    print("=" * 60)
    print(f"  🚀 飞轮运行完成 | {now_str()}")
    print("=" * 60)
    
    for stage_name in STAGE_ORDER:
        if stage_name in results:
            icon = "✅" if results[stage_name] else "⚠️"
            print(f"  {icon} {STAGES[stage_name]['label']}")
        else:
            print(f"  ⏭ {STAGES[stage_name]['label']} (跳过)")

    print()
    if all_passed:
        print("  ✅ 内容飞轮完整运行，所有阶段成功")
    else:
        failed = [STAGES[s]['label'] for s, v in results.items() if not v]
        print(f"  ⚠️ 部分阶段有异常: {', '.join(failed)}")
        print(f"  ℹ️ 已触发降级策略，飞轮继续运行")

    # 如果是全流程完成，打印数据回收总结
    if "analytics" in results:
        formulas = load_json_safe(TITLE_FORMULAS)
        if formulas.get("total_analyzed_posts", 0) > 0:
            print()
            print("  📈 数据回收摘要:")
            print(f"     累计分析内容数: {formulas['total_analyzed_posts']}")
            if formulas.get("global_insights", {}).get("avg_engagement_rate"):
                print(f"     平均互动率: {formulas['global_insights']['avg_engagement_rate']}%")
            best = formulas.get("global_insights", {}).get("overall_best_titles", [])
            if best:
                print(f"     最佳公式: {', '.join(best[:3])}")

    return all_passed


# ─── 命令行入口 ──────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="墨麟全媒体内容飞轮编排器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
阶段说明:
  intelligence   08:00 - 情报采集（自动执行 collect_intelligence.py）
  content        09:20 - 内容创作（需加载 墨笔文创/墨图设计 技能）
  distribution   10:30 - 分发优化（需加载 墨增引擎/墨流广投 技能）
  analytics      11:00 - 数据回收（自动执行 update_title_formulas.py）

使用示例:
  # 全流程
  python3 orchestrate_flywheel.py

  # 从指定阶段开始
  python3 orchestrate_flywheel.py --from content

  # 只跑数据回收
  python3 orchestrate_flywheel.py --stages analytics

  # 检查飞轮状态
  python3 orchestrate_flywheel.py --status
        """
    )
    parser.add_argument("--stages", nargs="+", default=None,
                        choices=STAGE_ORDER,
                        help="指定要执行的阶段（默认全流程）")
    parser.add_argument("--from", dest="from_stage", default=None,
                        choices=STAGE_ORDER,
                        help="从指定阶段开始执行")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅打印执行计划，不实际执行脚本")
    parser.add_argument("--quick", action="store_true",
                        help="快速模式（跳过分发层）")
    parser.add_argument("--status", action="store_true",
                        help="检查飞轮状态，不执行任何操作")
    parser.add_argument("--fix-file", type=str,
                        help="创建缺失的期望文件（修复依赖）")

    args = parser.parse_args()

    if args.status:
        print_flywheel_status()
        return 0

    if args.fix_file:
        file_path = RELAY_DIR / args.fix_file
        file_path.parent.mkdir(parents=True, exist_ok=True)
        placeholder = {
            "created_by": "flywheel-orchestrator",
            "created_at": now_str(),
            "note": f"占位文件 - 由 --fix-file 创建",
        }
        file_path.write_text(
            json.dumps(placeholder, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"✅ 已创建: {file_path}")
        return 0

    run_flywheel(
        stages=args.stages,
        from_stage=args.from_stage,
        dry_run=args.dry_run,
        quick=args.quick,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
