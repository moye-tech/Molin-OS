#!/usr/bin/env python3
"""
内容情报管线 - 定时采集入口
每天 08:00 由 cron 触发，执行以下步骤：
  1. 运行注册的 Source Adapter 采集数据
  2. 合并采集结果到 relay/media/intelligence.json
  3. 生成 trending_topics.md 人工可读报告
  4. 返回采集摘要（供 cron 输出）

用法：
  python3 collect_intelligence.py [--sources xiaohongshu,douyin] [--output-dir relay]
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# ─── 配置 ─────────────────────────────────────────────────────────

# 使用硬编码路径避免 ~ 扩展歧义
MEDIA_ROOT = "/Users/laomo/.hermes/profiles/media"
MEDIA_DIR = Path(MEDIA_ROOT)
RELAY_DIR = MEDIA_DIR / "relay"
ADAPTERS_DIR = MEDIA_DIR / "adapters"

# 确保 Python 能找到 adapters 模块
sys.path.insert(0, MEDIA_ROOT)
DEFAULT_SOURCES = ["xiaohongshu", "douyin", "bilibili"]  # 小红书 + 抖音 + B站

INTELLIGENCE_PATH = RELAY_DIR / "intelligence.json"
TRENDING_REPORT_PATH = RELAY_DIR / "trending_topics.md"


# ─── 适配器注册表 ────────────────────────────────────────────────

def get_adapter(source_name: str):
    """根据源名称加载相应的 Adapter"""
    adapters = {
        "xiaohongshu": {
            "module": "adapters.xiaohongshu.adapter",
            "class_name": "XiaoHongShuAdapter",
        },
        "douyin": {
            "module": "adapters.douyin.adapter",
            "class_name": "DouYinAdapter",
        },
        "bilibili": {
            "module": "adapters.bilibili.adapter",
            "class_name": "BiliBiliAdapter",
        },
    }
    config = adapters.get(source_name)
    if not config:
        raise ValueError(f"未知数据源: {source_name}")

    import importlib
    module = importlib.import_module(config["module"])
    cls = getattr(module, config["class_name"])
    return cls()


# ─── 数据合并 ────────────────────────────────────────────────────

def merge_results(existing: dict, result) -> dict:
    """将采集结果合并到 intelligence.json"""
    if not existing:
        existing = {
            "meta": {"collected_at": None, "duration_ms": 0, "sources_used": 0,
                     "sources_failed": 0, "total_items_collected": 0, "version": "1.1.0"},
            "hot_topics": [],
            "competitor_analysis": [],
            "trending_formats": {},
            "platform_timing": {},
            "ready_for_consumption": False,
            "feedback_loop": {},
        }

    # 更新 meta
    existing["meta"]["sources_used"] = existing["meta"].get("sources_used", 0) + 1
    existing["meta"]["total_items_collected"] += len(result.get("items", []))

    for item in result.get("items", []):
        # SourceItem 转热词条目
        topic_entry = {
            "keyword": item.get("title", "")[:50],
            "source": result.get("source", "unknown"),
            "engagement_score": item.get("engagement_score", 0),
            "url": item.get("url", ""),
            "tags": item.get("tags", []),
            "collected_at": result.get("collected_at", ""),
        }
        existing["hot_topics"].append(topic_entry)

    # 标记 faulty sources
    for error in result.get("errors", []):
        if error.get("severity") == "error":
            existing["meta"]["sources_failed"] += 1

    # 更新时间
    existing["meta"]["collected_at"] = datetime.now().isoformat()
    existing["ready_for_consumption"] = True

    return existing


# ─── 报告生成 ────────────────────────────────────────────────────

def generate_report(intelligence: dict) -> str:
    """生成人可读的趋势简报"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    hot_topics = intelligence.get("hot_topics", [])

    lines = []
    lines.append(f"每日热点简报 | {now}")
    lines.append("━" * 40)
    lines.append("")

    # 热词TOP
    if hot_topics:
        lines.append(f"📊 今日热词 ({len(hot_topics)} 条)")
        lines.append("")
        for i, topic in enumerate(hot_topics[:10], 1):
            keyword = topic.get("keyword", "未知")
            source = topic.get("source", "")
            score = topic.get("engagement_score", 0)
            lines.append(f"  {i}. [{source}] {keyword} (评分: {score})")
        lines.append("")
    else:
        lines.append("📊 今日热词: 暂无数据（数据源正在接入中）")
        lines.append("")

    # 平台状态
    lines.append("🔄 数据源状态")
    lines.append("")
    meta = intelligence.get("meta", {})
    lines.append(f"  启用数据源: {meta.get('sources_used', 0)}")
    lines.append(f"  失败数据源: {meta.get('sources_failed', 0)}")
    lines.append(f"  采集内容数: {meta.get('total_items_collected', 0)}")
    lines.append(f"  最后采集: {meta.get('collected_at', '从未')}")
    lines.append("")

    # 发布时段
    timing = intelligence.get("platform_timing", {})
    if timing:
        lines.append("⏰ 最佳发布时段")
        lines.append("")
        for platform, times in timing.items():
            best = times.get("best_time", "未知")
            second = times.get("second_best", "")
            lines.append(f"  {platform}: {best} {' / ' + second if second else ''}")
        lines.append("")

    # 反馈
    feedback = intelligence.get("feedback_loop", {})
    if feedback.get("last_feedback_at"):
        lines.append("📈 上次反馈: " + feedback["last_feedback_at"])

    return "\n".join(lines)


# ─── 主流程 ──────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="内容情报采集管线")
    parser.add_argument("--sources", default=",".join(DEFAULT_SOURCES),
                        help="数据源列表，逗号分隔")
    parser.add_argument("--output-dir", default=str(RELAY_DIR),
                        help="输出目录")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅测试，不写入文件")
    args = parser.parse_args()

    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"🔍 内容情报采集开始 | 数据源: {sources}")
    print(f"   输出目录: {output_dir}")
    print()

    # 加载现有的intelligence.json
    intel_path = output_dir / "intelligence.json"
    existing = {}
    if intel_path.exists():
        try:
            existing = json.loads(intel_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
        count = len(existing.get('hot_topics', []))
        print(f"   已加载现有数据 ({count} 条历史热词)")
    print()

    # 每日快照：先清空热词，再逐个Adapter追加
    existing["hot_topics"] = []

    # 逐个执行Adapter
    overall_errors = []
    for source_name in sources:
        print(f"  ▶ 执行 {source_name} Adapter...")
        try:
            adapter = get_adapter(source_name)

            # 动态导入 adapter 模块获取 CollectionContext
            adapter_module = __import__(
                f"adapters.{source_name}.adapter",
                fromlist=["CollectionContext", "asdict"]
            )
            CollectionContext = adapter_module.CollectionContext
            asdict_func = adapter_module.asdict

            # 任务类型映射：小红书用 hot_topics，抖音用 hot_search
            task_map = {
                "xiaohongshu": "hot_topics",
                "douyin": "hot_search",
                "bilibili": "popular",
            }
            task_type = task_map.get(source_name, "hot_topics")

            context = CollectionContext(
                task=task_type,
                keywords=["AI一人公司", "AI工具", "自媒体创业", "副业"],
                max_items=30,
            )
            result = adapter.collect(context)
            result_dict = {
                "source": result.source,
                "items": [asdict_func(item) for item in result.items],
                "errors": [asdict_func(e) for e in result.errors],
                "collected_at": result.collected_at,
                "duration_ms": result.duration_ms,
            }

            existing = merge_results(existing, result_dict)
            print(f"     ✓ 完成: {len(result.items)} items, {result.duration_ms}ms")

        except Exception as e:
            overall_errors.append(f"{source_name}: {e}")
            print(f"     ✗ 失败: {e}")

    print()

    # 生成报告
    report = generate_report(existing)
    report_path = output_dir / "trending_topics.md"
    if not args.dry_run:
        report_path.write_text(report, encoding="utf-8")
        intel_path.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        print(f"✅ intelligence.json -> {intel_path}")
        print(f"✅ trending_topics.md -> {report_path}")
    else:
        print("🔷 DRY RUN 模式，未写入文件")
        print()
        print(report)

    print()
    if overall_errors:
        print(f"⚠️ {len(overall_errors)} 个数据源失败:")
        for err in overall_errors:
            print(f"   - {err}")
    else:
        print("✅ 全部数据源采集完成")

    # 输出摘要（供 cron 捕获）
    summary = {
        "status": "partial" if overall_errors else "success",
        "sources_used": len(sources),
        "sources_failed": len(overall_errors),
        "total_items": len(existing.get("hot_topics", [])),
        "collected_at": existing.get("meta", {}).get("collected_at"),
    }
    print()
    print(f"SUMMARY: {json.dumps(summary)}")

    return 1 if overall_errors else 0


if __name__ == "__main__":
    sys.exit(main())
