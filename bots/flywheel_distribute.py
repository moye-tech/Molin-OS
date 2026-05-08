#!/usr/bin/env python3.12
"""
墨麟 · 飞轮第三棒：分发策略评估 v1.0

功能：
- 读取 relay/content_flywheel.json（第二棒内容草稿）
- 评估每条内容的最佳分发渠道、优先级、时间窗口
- 写入 relay/distribution_plan.json（供执行层调度）

输出格式：
{
  "timestamp": "ISO格式时间戳",
  "items": [
    {
      "title": "内容标题",
      "platform": "xhs",        // 分发平台
      "priority": 1,            // 优先级 1-5
      "time_slot": "09:30",     // 最佳发布时间
      "cta": "引导关注"          // 行动号召策略
    }
  ]
}

子公司参与：墨测数据(分发策略) → 墨域私域(触达)
涉及时区：北京时间 (UTC+8)
"""

import json
import os
import random
from datetime import datetime


# ============================================================
# 配置区
# ============================================================

RELAY_DIR = os.path.expanduser("~/hermes-os/relay")
INPUT_FILE = os.path.join(RELAY_DIR, "content_flywheel.json")
OUTPUT_FILE = os.path.join(RELAY_DIR, "distribution_plan.json")
LOG_DIR = os.path.expanduser("~/.hermes/daily_reports")

# 平台分发配置
PLATFORM_CONFIG = {
    "xhs": {
        "name": "小红书",
        "best_times": ["07:30", "12:00", "18:30", "20:30", "22:00"],
        "best_days": ["周一", "周二", "周三", "周四", "周日"],
        "cta_options": [
            "引导关注",
            "引导收藏",
            "引导评论",
            "引导点赞+收藏",
            "引导进群"
        ],
        "content_types_preferred": ["教程型", "合集型", "经验分享型"],
    },
    "wechat_article": {
        "name": "公众号",
        "best_times": ["08:00", "12:30", "21:00"],
        "best_days": ["周二", "周三", "周四"],
        "cta_options": [
            "引导关注",
            "引导在看",
            "引导加微信",
            "引导进社群"
        ],
        "content_types_preferred": ["人设IP型", "商业分析型"],
    },
    "wechat_moments": {
        "name": "朋友圈",
        "best_times": ["08:00", "12:00", "18:00", "21:00"],
        "best_days": ["周一", "周二", "周三", "周四", "周五"],
        "cta_options": [
            "引导私聊",
            "引导点赞",
            "引导评论",
            "引导扫码",
        ],
        "content_types_preferred": ["经验分享型", "人设IP型"],
    }
}

# 品类→分发策略权重
CATEGORY_STRATEGY = {
    "AI工具": {
        "primary_platform": "xhs",
        "priority_base": 5,
        "primary_cta": "引导收藏",
        "time_slot": "12:00"
    },
    "AI副业": {
        "primary_platform": "xhs",
        "priority_base": 4,
        "primary_cta": "引导评论",
        "time_slot": "20:30"
    },
    "一人公司 AI": {
        "primary_platform": "xhs",
        "priority_base": 5,
        "primary_cta": "引导关注",
        "time_slot": "18:30"
    },
    "AI教程": {
        "primary_platform": "xhs",
        "priority_base": 5,
        "primary_cta": "引导收藏",
        "time_slot": "07:30"
    },
    "AI创业": {
        "primary_platform": "xhs",
        "priority_base": 4,
        "primary_cta": "引导关注",
        "time_slot": "22:00"
    },
    "AI自动化": {
        "primary_platform": "xhs",
        "priority_base": 3,
        "primary_cta": "引导收藏",
        "time_slot": "12:00"
    },
    "AI编程": {
        "primary_platform": "xhs",
        "priority_base": 3,
        "primary_cta": "引导收藏",
        "time_slot": "18:30"
    },
    "AI设计": {
        "primary_platform": "xhs",
        "priority_base": 4,
        "primary_cta": "引导收藏",
        "time_slot": "20:30"
    }
}

# 默认策略（当品类匹配不到时使用）
DEFAULT_STRATEGY = {
    "primary_platform": "xhs",
    "priority_base": 3,
    "primary_cta": "引导收藏",
    "time_slot": "12:00"
}


# ============================================================
# 数据加载模块
# ============================================================

def load_content() -> dict:
    """读取第二棒的内容草稿"""
    if not os.path.exists(INPUT_FILE):
        print(f"[⚠] 未检测到 {INPUT_FILE}，生成占位内容数据")
        return generate_placeholder_content()
    
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"[✓] 成功读取 {INPUT_FILE}")
        return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"[⚠] 读取 {INPUT_FILE} 失败 ({e})，使用占位数据")
        return generate_placeholder_content()


def generate_placeholder_content() -> dict:
    """生成占位内容数据"""
    return {
        "timestamp": datetime.now().isoformat(),
        "source": "placeholder (无真实内容)",
        "topics": [
            {
                "title": "占位内容：AI效率工具合集，收藏就够",
                "body": "占位正文：这是一篇关于AI效率工具的内容...",
                "tags": ["AI工具", "效率工具"],
                "platform": "xhs",
                "cover_prompt": "占位封面提示词"
            },
            {
                "title": "占位内容：零基础学AI教程，10分钟上手",
                "body": "占位正文：这是一篇AI教程...",
                "tags": ["AI教程", "AI学习"],
                "platform": "xhs",
                "cover_prompt": "占位封面提示词"
            },
            {
                "title": "占位内容：AI副业月入过万，真实经历",
                "body": "占位正文：这是一篇AI副业经验分享...",
                "tags": ["AI副业", "搞钱"],
                "platform": "xhs",
                "cover_prompt": "占位封面提示词"
            }
        ],
        "analysis": {
            "summary": "占位分析摘要"
        }
    }


# ============================================================
# 分发策略评估模块
# ============================================================

def evaluate_distribution(content_data: dict) -> list:
    """评估每条内容的分发策略"""
    
    topics = content_data.get("topics", [])
    if not topics:
        print("[⚠] 内容草稿为空，无法生成分发策略")
        return []
    
    items = []
    
    for i, topic in enumerate(topics):
        title = topic.get("title", "无标题")
        tags = topic.get("tags", [])
        
        # 通过标签识别品类
        category = identify_category(tags)
        
        # 获取品类分发策略
        strategy = CATEGORY_STRATEGY.get(category, DEFAULT_STRATEGY)
        
        # 计算优先级（基于品类基准 + 位置权重）
        priority = calculate_priority(strategy, i, len(topics))
        
        # 确定最佳时间窗口
        time_slot = determine_time_slot(strategy, category)
        
        # 确定行动号召
        cta = determine_cta(strategy, category)
        
        # 确定平台（目前统一xhs，以后可扩展）
        platform = strategy.get("primary_platform", "xhs")
        
        items.append({
            "title": title,
            "platform": platform,
            "priority": priority,
            "time_slot": time_slot,
            "cta": cta
        })
    
    return items


def identify_category(tags: list) -> str:
    """通过标签识别内容品类"""
    category_map = {
        "AI工具": ["AI工具", "效率工具", "工具推荐"],
        "AI副业": ["AI副业", "副业赚钱", "搞钱"],
        "一人公司 AI": ["一人公司", "AI创业", "数字游民"],
        "AI教程": ["AI教程", "AI学习", "技能提升"],
        "AI创业": ["AI创业", "商业思维", "创业"],
        "AI自动化": ["自动化", "工作流", "AI自动化"],
        "AI编程": ["AI编程", "编程工具", "程序员"],
        "AI设计": ["AI设计", "设计工具", "Midjourney"],
    }
    
    for tag in tags:
        for cat, keywords in category_map.items():
            if any(kw in tag for kw in keywords):
                return cat
    
    # fallback：用第一个标签或默认
    return tags[0] if tags else "AI工具"


def calculate_priority(strategy: dict, index: int, total: int) -> int:
    """计算分发优先级 1-5"""
    base = strategy.get("priority_base", 3)
    
    # 第一篇权重高一点
    if index == 0:
        boost = 1
    elif index == 1:
        boost = 0
    else:
        boost = -1
    
    priority = min(5, max(1, base + boost))
    return priority


def determine_time_slot(strategy: dict, category: str) -> str:
    """确定最佳发布时间"""
    # 优先使用策略配置的时间
    configured_time = strategy.get("time_slot")
    if configured_time:
        return configured_time
    
    # 否则从品类默认取
    cat_default = CATEGORY_STRATEGY.get(category, {})
    return cat_default.get("time_slot", "12:00")


def determine_cta(strategy: dict, category: str) -> str:
    """确定行动号召方式"""
    configured_cta = strategy.get("primary_cta")
    if configured_cta:
        return configured_cta
    
    cat_default = CATEGORY_STRATEGY.get(category, {})
    return cat_default.get("primary_cta", "引导关注")


# ============================================================
# 分析报告生成
# ============================================================

def generate_distribution_analysis(items: list) -> dict:
    """生成分发策略分析"""
    if not items:
        return {
            "summary": "无内容需分发",
            "total_items": 0
        }
    
    # 统计优先级分布
    high_priority = [i for i in items if i.get("priority", 0) >= 4]
    mid_priority = [i for i in items if i.get("priority", 0) == 3]
    low_priority = [i for i in items if i.get("priority", 0) <= 2]
    
    # 统计时间窗口
    time_slots = {}
    for item in items:
        ts = item.get("time_slot", "未知")
        time_slots[ts] = time_slots.get(ts, 0) + 1
    
    time_display = []
    for ts in sorted(time_slots.keys()):
        time_display.append(f"{ts}({time_slots[ts]}篇)")
    
    summary = (
        f"共分发{len(items)}篇内容，"
        f"高优先级{len(high_priority)}篇，"
        f"中优先级{len(mid_priority)}篇，"
        f"低优先级{len(low_priority)}篇。"
        f"发布时间分布：{', '.join(time_display)}。"
    )
    
    return {
        "summary": summary,
        "total_items": len(items),
        "priority_distribution": {
            "high": len(high_priority),
            "mid": len(mid_priority),
            "low": len(low_priority)
        },
        "time_slots": time_slots
    }


# ============================================================
# 主流程
# ============================================================

def main():
    os.makedirs(RELAY_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    
    now = datetime.now()
    print(f"🔄 [飞轮第三棒] {now.strftime('%Y-%m-%d %H:%M')} 开始...")
    print(f"📥 输入: {INPUT_FILE}")
    
    # Step 1: 加载内容草稿
    content_data = load_content()
    topics = content_data.get("topics", [])
    print(f"[📊] 待分发内容数: {len(topics)}")
    
    for i, t in enumerate(topics, 1):
        print(f"  {i}. {t.get('title', '无标题')[:40]}")
    
    # Step 2: 评估分发策略
    print(f"[📋] 墨测数据分析分发策略...")
    items = evaluate_distribution(content_data)
    
    # Step 3: 生成分析
    analysis = generate_distribution_analysis(items)
    
    # Step 4: 写入输出
    output = {
        "timestamp": now.isoformat(),
        "source": "flywheel_distribute.py v1.0",
        "input_source": content_data.get("source", "unknown"),
        "items": items,
        "analysis": analysis
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"[✓] 输出已写入: {OUTPUT_FILE}")
    print(f"[📋] 分发策略摘要: {analysis.get('summary', '')}")
    print(f"\n📋 详细分发计划:")
    for item in items:
        stars = "⭐" * item.get("priority", 0)
        print(f"  [{stars}] {item.get('title', '')[:30]}...")
        print(f"      平台: {item.get('platform', '?')} | 时间: {item.get('time_slot', '?')} | CTA: {item.get('cta', '?')}")
    
    print(f"\n[🔄] 飞轮第三棒完成，等待执行层调度...")
    
    # 保存日志
    log_path = os.path.join(LOG_DIR, f"distribution_plan_{now.strftime('%Y%m%d')}.json")
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"[📝] 日志已保存: {log_path}")
    
    # ── 可选飞书推送 ─────────────────────────────────
    try:
        from molib.ceo.feishu_card import feishu_send_card, build_report_card
        
        # 构建摘要
        plan_lines = []
        for item in items:
            stars = "⭐" * item.get("priority", 0)
            plan_lines.append(
                f"· {stars} **{item.get('title','')[:30]}** → {item.get('platform','?')} @ {item.get('time_slot','?')} | {item.get('cta','?')}"
            )
        
        summary_lines = [
            f"**{analysis.get('summary','')}**",
            "",
            "**分发明细**:",
        ]
        summary_lines.extend(plan_lines)
        summary_text = "\n".join(summary_lines)
        
        card = build_report_card(
            report_type="📋 飞轮第三棒·分发策略",
            content=summary_text,
            meta={
                "⏰ 评估时间": now.strftime("%H:%M"),
                "📄 总篇数": f"{analysis.get('total_items',0)}篇",
                "🔝 高优先级": f"{analysis.get('priority_distribution',{}).get('high',0)}篇",
                "⏳ 时间窗口": ", ".join(sorted(analysis.get('time_slots',{}).keys())[:3]),
            },
            color="indigo"
        )
        feishu_send_card(card)
        print(f"[✅ 飞书推送] 分发策略卡片已发送")
    except ImportError:
        print(f"[ℹ️ 飞书推送] molib.ceo.feishu_card 不可用，跳过")
    except Exception as e:
        print(f"[⚠️ 飞书推送] 发送失败: {e}")

if __name__ == "__main__":
    main()
