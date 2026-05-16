#!/usr/bin/env python3
"""
墨镜数据 → 爆款标题公式库 反馈回路
数据驱动迭代：内容效果数据 → 标题公式权重更新 → 公式库增量优化

工作流：
  1. 读取墨镜数据输出的 analytics_feedback.json（来自数据回收11:00）
  2. 读取现有的 title_formulas.json
  3. 按平台+公式对照，计算每类公式的实际表现
  4. 更新公式权重（weight），高效公式提升权重，低效公式降低权重
  5. 如果样本量足够，自动启用/禁用公式
  6. 记录全局洞察（最佳发布时间、整体互动率趋势）
  7. 写回 title_formulas.json

用法：
  python3 update_title_formulas.py [--feedback path] [--formulas path]
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# ─── 路径配置 ────────────────────────────────────────────────────

RELAY_DIR = Path("/Users/laomo/.hermes/profiles/media/relay")
DEFAULT_FEEDBACK_PATH = RELAY_DIR / "analytics_feedback.json"
DEFAULT_FORMULAS_PATH = RELAY_DIR / "title_formulas.json"
INTELLIGENCE_PATH = RELAY_DIR / "intelligence.json"

# ─── 反馈数据结构 ────────────────────────────────────────────────

"""
analytics_feedback.json 结构（由墨镜数据产出）：
{
  "version": "1.0.0",
  "analysis_date": "2026-05-15T11:00:00",
  "period": {"start": "2026-05-08", "end": "2026-05-15"},
  "total_posts_analyzed": 30,
  "by_platform": {
    "小红书": {
      "posts_analyzed": 15,
      "top_performers": [
        {
          "title": "3天学会AI写爆款文案",
          "formula_id": "xhs_f1",
          "formula_name": "数字+痛点+解决方案",
          "engagement_rate": 12.5,
          "hook_type": "bold_claim"
        }
      ],
      "worst_performers": [...],
      "formula_performance": {
        "xhs_f1": {"uses": 3, "avg_rate": 11.2, "best_rate": 15.0},
        "xhs_f2": {"uses": 2, "avg_rate": 8.5, "best_rate": 10.2}
      },
      "hook_performance": {
        "question": {"uses": 4, "avg_rate": 10.1},
        "bold_claim": {"uses": 3, "avg_rate": 9.8}
      },
      "best_posting_times": ["08:00", "12:00"]
    }
  },
  "global_best_formulas": ["xhs_f1", "gzh_f3"],
  "global_worst_formulas": ["xhs_f8"],
  "key_insights": ["数字+痛点+解决方案 在小红书表现最好"],
  "quality_notes": "样本量30，置信度中等"
}
"""


def load_json(path: Path, default=None) -> dict:
    """安全加载 JSON 文件"""
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        return default or {}


def save_json(path: Path, data: dict, indent: int = 2):
    """安全保存 JSON 文件"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=indent, default=str),
        encoding="utf-8",
    )


def update_formula_weights(formulas: dict, feedback: dict) -> dict:
    """
    核心更新逻辑：
    1. 遍历每个平台的公式表现数据
    2. 按实际互动率调整公式权重
    3. 样本量够时自动启用/禁用公式
    """
    modified = False
    by_platform = feedback.get("by_platform", {})

    for platform_name, platform_data in by_platform.items():
        platform_key = platform_name  # 小红书/抖音/公众号/B站
        if platform_key not in formulas.get("platforms", {}):
            continue

        formula_perf = platform_data.get("formula_performance", {})
        formulas_list = formulas["platforms"][platform_key].get("formulas", [])

        # 构建 formula_id → formula 索引
        formula_map = {f["id"]: f for f in formulas_list}

        for f_id, perf in formula_perf.items():
            if f_id not in formula_map:
                continue

            formula = formula_map[f_id]
            uses = perf.get("uses", 0)
            avg_rate = perf.get("avg_rate", 0)

            if uses == 0:
                continue

            # 更新统计
            old_sample_count = formula.get("sample_count", 0)
            new_sample_count = old_sample_count + uses
            old_score = formula.get("score", 0)

            # 加权平均更新 score
            if old_sample_count > 0:
                new_score = (old_score * old_sample_count + avg_rate * uses) / new_sample_count
            else:
                new_score = avg_rate

            formula["score"] = round(new_score, 2)
            formula["sample_count"] = new_sample_count

            # 基于互动率调整权重（±0.2/次，最大1.5，最小0.1）
            baseline = 8.0  # 基准互动率
            rate_diff = avg_rate - baseline
            weight_adjust = rate_diff / 10.0  # 每1%互动率差异调整0.1权重
            new_weight = formula.get("weight", 1.0) + weight_adjust
            new_weight = max(0.1, min(1.5, new_weight))
            formula["weight"] = round(new_weight, 2)

            # 自动启用/禁用：如果样本≥5且score<2.0，禁用
            if new_sample_count >= 5 and new_score < 2.0:
                formula["enabled"] = False
                modified = True
            elif new_sample_count >= 5 and new_score > 5.0 and not formula.get("enabled", True):
                formula["enabled"] = True
                modified = True

            modified = True

        # 更新钩子权重（如果有）
        hook_perf = platform_data.get("hook_performance", {})
        hooks_list = formulas["platforms"][platform_key].get("hooks", {}).get("top_types", [])
        for hook in hooks_list:
            h_id = hook.get("id")
            if h_id in hook_perf:
                perf = hook_perf[h_id]
                uses = perf.get("uses", 0)
                avg_rate = perf.get("avg_rate", 0)
                if uses > 0:
                    baseline = 8.0
                    adjust = (avg_rate - baseline) / 10.0
                    new_weight = hook.get("weight", 1.0) + adjust
                    hook["weight"] = round(max(0.1, min(1.5, new_weight)), 2)

        # 更新平台最佳发布时间
        best_times = platform_data.get("best_posting_times", [])
        if best_times and "timing" in formulas.get("platforms", {}).get(platform_key, {}):
            formulas["platforms"][platform_key]["timing"] = {
                "best_time": best_times[0],
                "second_best": best_times[1] if len(best_times) > 1 else None,
            }

    # 更新全局最佳标题
    global_best = feedback.get("global_best_formulas", [])
    global_insights = formulas.get("global_insights", {})
    if global_best:
        # 更新到前3
        current_best = global_insights.get("overall_best_titles", [])
        for f_id in global_best:
            if f_id not in current_best:
                current_best.insert(0, f_id)
        global_insights["overall_best_titles"] = current_best[:5]

    # 更新全局最差标题
    global_worst = feedback.get("global_worst_formulas", [])
    if global_worst:
        current_worst = global_insights.get("overall_worst_titles", [])
        for f_id in global_worst:
            if f_id not in current_worst:
                current_worst.insert(0, f_id)
        global_insights["overall_worst_titles"] = current_worst[:5]

    # 更新总体互动率
    total_posts = feedback.get("total_posts_analyzed", 0)
    if total_posts > 0:
        existing_total = formulas.get("total_analyzed_posts", 0)
        formulas["total_analyzed_posts"] = existing_total + total_posts

        # 更新平均互动率
        by_platform_data = feedback.get("by_platform", {})
        total_rate = 0
        platform_count = 0
        for pname, pdata in by_platform_data.items():
            for _, perf in pdata.get("formula_performance", {}).items():
                total_rate += perf.get("avg_rate", 0)
                platform_count += 1
        if platform_count > 0:
            overall_avg = total_rate / platform_count
            global_insights["avg_engagement_rate"] = round(overall_avg, 2)

    formulas["last_updated"] = datetime.now().isoformat()
    formulas["global_insights"] = global_insights

    return modified


def write_feedback_to_intelligence(feedback: dict):
    """将反馈写入 intelligence.json 的 feedback_loop 字段"""
    intel = load_json(INTELLIGENCE_PATH)
    if not intel:
        return

    intel["feedback_loop"] = {
        "last_feedback_at": datetime.now().isoformat(),
        "previous_recommendations": feedback.get("global_best_formulas", []),
        "total_posts_analyzed": feedback.get("total_posts_analyzed", 0),
        "accuracy_summary": {
            "global_best": feedback.get("global_best_formulas", []),
            "global_worst": feedback.get("global_worst_formulas", []),
            "key_insights": feedback.get("key_insights", []),
        },
    }
    intel["ready_for_consumption"] = True
    save_json(INTELLIGENCE_PATH, intel)


def generate_summary_report(formulas: dict, modified: bool) -> str:
    """生成摘要报告"""
    last = formulas.get("last_updated", "从未")
    total = formulas.get("total_analyzed_posts", 0)
    platforms = formulas.get("platforms", {})

    lines = []
    lines.append(f"📊 标题公式库更新报告")
    lines.append(f"   最后更新: {last}")
    lines.append(f"   累计分析内容数: {total}")
    lines.append(f"   内容已更新: {'是' if modified else '否'}")
    lines.append("")

    for pname, pdata in platforms.items():
        formulas_list = pdata.get("formulas", [])
        enabled = [f for f in formulas_list if f.get("enabled", True)]
        disabled = [f for f in formulas_list if not f.get("enabled", True)]

        lines.append(f"  {pname}: {len(enabled)} 个活跃公式")
        if enabled:
            # 按权重排序显示TOP3
            sorted_f = sorted(enabled, key=lambda x: x.get("weight", 1.0), reverse=True)
            for f in sorted_f[:3]:
                score = f.get("score", 0)
                samples = f.get("sample_count", 0)
                weight = f.get("weight", 1.0)
                lines.append(f"    {f['name']}: 评分={score}, 样本={samples}, 权重={weight}")
        if disabled:
            lines.append(f"    ❌ 已禁用: {', '.join(f['name'] for f in disabled)}")

        # 最佳钩子
        hooks = pdata.get("hooks", {}).get("top_types", [])
        if hooks:
            sorted_h = sorted(hooks, key=lambda x: x.get("weight", 1.0), reverse=True)
            best_hook = sorted_h[0]
            lines.append(f"    最佳钩子类型: {best_hook['name']} (权重: {best_hook['weight']})")

        lines.append("")

    # 全局洞察
    insights = formulas.get("global_insights", {})
    if insights.get("avg_engagement_rate"):
        lines.append(f"  全局平均互动率: {insights['avg_engagement_rate']}%")

    best_titles = insights.get("overall_best_titles", [])
    if best_titles:
        lines.append(f"  🏆 历史最佳公式: {', '.join(best_titles[:3])}")

    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="墨镜数据 → 标题公式库 反馈回路")
    parser.add_argument("--feedback", default=str(DEFAULT_FEEDBACK_PATH),
                        help=f"feedback 文件路径 (默认 {DEFAULT_FEEDBACK_PATH})")
    parser.add_argument("--formulas", default=str(DEFAULT_FORMULAS_PATH),
                        help=f"公式库路径 (默认 {DEFAULT_FORMULAS_PATH})")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅测试，不写入文件")
    parser.add_argument("--create-feedback-template", action="store_true",
                        help="创建 feedback 模板文件（供墨镜数据参考）")

    args = parser.parse_args()

    feedback_path = Path(args.feedback)
    formulas_path = Path(args.formulas)

    # 创建 feedback 模板
    if args.create_feedback_template:
        template = {
            "version": "1.0.0",
            "analysis_date": None,
            "period": {"start": None, "end": None},
            "total_posts_analyzed": 0,
            "by_platform": {
                "小红书": {
                    "posts_analyzed": 0,
                    "top_performers": [],
                    "worst_performers": [],
                    "formula_performance": {},
                    "hook_performance": {},
                    "best_posting_times": [],
                }
            },
            "global_best_formulas": [],
            "global_worst_formulas": [],
            "key_insights": [],
            "quality_notes": "",
        }
        save_json(feedback_path, template)
        print(f"✅ feedback 模板创建完成: {feedback_path}")
        return

    # 加载数据
    feedback = load_json(feedback_path)
    formulas = load_json(formulas_path)

    if not feedback:
        print(f"⚠️ 未找到 feedback 文件: {feedback_path}")
        print(f"   先运行 --create-feedback-template 创建模板")
        return 1

    if not formulas:
        print(f"⚠️ 未找到公式库文件: {formulas_path}")
        return 1

    # 执行更新
    modified = update_formula_weights(formulas, feedback)

    if not args.dry_run:
        save_json(formulas_path, formulas)
        write_feedback_to_intelligence(feedback)
        print(f"✅ 公式库已更新: {formulas_path}")
        print(f"✅ 反馈已同步到 intelligence.json")
    else:
        print("🔷 DRY RUN 模式，未写入文件")

    # 输出报告
    print()
    print(generate_summary_report(formulas, modified))

    return 0


if __name__ == "__main__":
    sys.exit(main())
