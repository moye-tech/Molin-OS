#!/usr/bin/env python3.12
"""
墨麟 · CH4-E 每日AI情报简报 v1.0

功能：
- 读取 relay/intelligence_morning.json（第一棒情报）
- 生成排版好的Markdown简报
- 输出至 relay/briefing_daily.md（可直接发飞书/邮件）

输出格式：标准Markdown，排版美观，适合直接复制到飞书/邮件发送

子公司参与：墨研竞情(情报整合) → 墨笔文创(简报润色)
涉及时区：北京时间 (UTC+8)
"""

import json
import os
from datetime import datetime


# ============================================================
# 配置区
# ============================================================

RELAY_DIR = os.path.expanduser("~/hermes-os/relay")
INPUT_FILE = os.path.join(RELAY_DIR, "intelligence_morning.json")
OUTPUT_FILE = os.path.join(RELAY_DIR, "briefing_daily.md")
LOG_DIR = os.path.expanduser("~/.hermes/daily_reports")

# 品类中文映射
CATEGORY_CN = {
    "AI工具": "🔧 AI工具合集",
    "AI副业": "💰 AI副业搞钱",
    "一人公司 AI": "🏢 一人公司",
    "AI教程": "📚 AI教程实操",
    "AI创业": "🚀 AI创业商业",
    "AI自动化": "⚡ AI自动化效率",
    "AI编程": "💻 AI编程",
    "AI设计": "🎨 AI设计",
}


# ============================================================
# 数据加载模块
# ============================================================

def load_intelligence() -> dict:
    """读取第一棒的情报数据"""
    if not os.path.exists(INPUT_FILE):
        print(f"[⚠] 未检测到 {INPUT_FILE}，使用占位数据生成简报")
        return generate_placeholder_intel()
    
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"[✓] 成功读取 {INPUT_FILE}")
        return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"[⚠] 读取失败 ({e})，使用占位数据")
        return generate_placeholder_intel()


def generate_placeholder_intel() -> dict:
    """生成占位情报数据"""
    return {
        "timestamp": datetime.now().isoformat(),
        "source": "placeholder (无真实情报数据)",
        "hot_categories": [
            {"category": "AI工具", "heat": 5000, "collect_ratio": 120, "suggestion": "占位热度数据"},
            {"category": "AI教程", "heat": 4500, "collect_ratio": 150, "suggestion": "占位热度数据"},
            {"category": "AI副业", "heat": 4000, "collect_ratio": 110, "suggestion": "占位热度数据"},
        ],
        "top_notes": [
            {"title": "占位爆款笔记1", "likes": 5000, "category": "🔧 工具合集"},
            {"title": "占位爆款笔记2", "likes": 4000, "category": "📚 教程实操"},
        ],
        "suggestions": [
            {"category": "🔧 工具合集", "reason": "占位建议", "action": "适合跟风产出", "owner": "墨笔文创"},
        ],
        "weibo_summary": "数据采集中...",
        "github_hot": []
    }


# ============================================================
# 简报生成模块
# ============================================================

def build_briefing(intel: dict) -> str:
    """生成排版好的Markdown简报"""
    
    now = datetime.now()
    today_str = now.strftime("%Y年%m月%d日")
    
    parts = []
    
    # ====== 头部 ======
    parts.append(f"# 📊 墨麟 AI 每日情报简报")
    parts.append(f"")
    parts.append(f"**日期：{today_str}**")
    parts.append(f"**来源：墨研竞情 · AI情报监控系统**")
    parts.append(f"**状态：{'✅ 实时数据' if intel.get('source') and 'placeholder' not in intel.get('source', '') else '⚠️ 占位数据'}**")
    parts.append(f"")
    parts.append(f"---")
    parts.append(f"")
    
    # ====== 一、今日全景概览 ======
    parts.append(f"## 一、今日全景概览")
    parts.append(f"")
    
    hot_categories = intel.get("hot_categories", [])
    if hot_categories:
        parts.append(f"| 品类 | 热度🔥 | 收藏率⭐ | 策略建议 |")
        parts.append(f"|------|--------|----------|----------|")
        for cat in hot_categories:
            cat_cn = CATEGORY_CN.get(cat.get("category", ""), cat.get("category", "未知"))
            heat = cat.get("heat", 0)
            cr = cat.get("collect_ratio", 0)
            sug = cat.get("suggestion", "")
            # 热度条形图
            bar = "█" * min(heat // 1000 + 1, 15)
            parts.append(f"| {cat_cn} | {heat} {bar} | {cr}% | {sug} |")
    else:
        parts.append(f"暂无品类热度数据。")
    
    parts.append(f"")
    parts.append(f"---")
    parts.append(f"")
    
    # ====== 二、今日爆款笔记 ======
    parts.append(f"## 二、🔥 今日爆款笔记 TOP3")
    parts.append(f"")
    
    top_notes = intel.get("top_notes", [])
    if top_notes:
        for i, note in enumerate(top_notes, 1):
            title = note.get("title", "无标题")[:35]
            likes = note.get("likes", 0)
            category = note.get("category", "未分类")
            parts.append(f"**{i}. {title}**")
            parts.append(f"   - ❤️ 点赞：{likes} | 📂 分类：{category}")
            parts.append(f"")
    else:
        parts.append(f"暂无爆款笔记数据。")
        parts.append(f"")
    
    # ====== 三、微博热搜动态 ======
    parts.append(f"## 三、📡 微博热搜动态")
    parts.append(f"")
    
    weibo_summary = intel.get("weibo_summary", "数据采集中...")
    parts.append(f"> {weibo_summary}")
    parts.append(f"")
    
    parts.append(f"---")
    parts.append(f"")
    
    # ====== 四、GitHub AI趋势 ======
    parts.append(f"## 四、🐙 GitHub AI 趋势项目")
    parts.append(f"")
    
    github_hot = intel.get("github_hot", [])
    if github_hot:
        for proj in github_hot:
            name = proj.get("name", "未知项目")
            stars = proj.get("stars", 0)
            parts.append(f"- ⭐ **{name}** — {stars} stars")
        parts.append(f"")
    else:
        parts.append(f"暂无 GitHub 趋势数据。")
        parts.append(f"")
    
    parts.append(f"---")
    parts.append(f"")
    
    # ====== 五、今日选题建议 ======
    parts.append(f"## 五、💡 今日选题建议")
    parts.append(f"")
    
    suggestions = intel.get("suggestions", [])
    if suggestions:
        for s in suggestions:
            category = s.get("category", "其他")
            action = s.get("action", "观察")
            reason = s.get("reason", "")
            owner = s.get("owner", "待定")
            parts.append(f"### {category}")
            parts.append(f"- **行动**：{action}")
            parts.append(f"- **理由**：{reason}")
            parts.append(f"- **负责**：{owner}")
            parts.append(f"")
    else:
        parts.append(f"暂无选题建议。")
        parts.append(f"")
    
    # ====== 六、今日飞轮执行状态 ======
    parts.append(f"## 六、🔄 飞轮管线状态")
    parts.append(f"")
    
    # 检查各 relay 文件状态
    relay_files = {
        "intelligence_morning.json": "📡 情报采集（墨研竞情）",
        "content_flywheel.json": "✏️ 内容生成（墨笔文创）",
        "distribution_plan.json": "📋 分发策略（墨测数据）",
        "briefing_daily.md": "📊 简报生成（本脚本）",
    }
    
    for filename, description in relay_files.items():
        filepath = os.path.join(RELAY_DIR, filename)
        if os.path.exists(filepath):
            filetime = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%H:%M")
            parts.append(f"- ✅ **{description}** — {filetime} 更新")
        else:
            parts.append(f"- ⭕ **{description}** — 等待中")
    
    parts.append(f"")
    parts.append(f"---")
    parts.append(f"")
    
    # ====== 尾部 ======
    parts.append(f"## ℹ️ 关于本简报")
    parts.append(f"")
    parts.append(f"- **生成时间**：{now.strftime('%Y-%m-%d %H:%M')}")
    parts.append(f"- **数据范围**：小红书 AI 品类搜索 | 微博热搜 | GitHub Trending")
    parts.append(f"- **数据来源**：墨研竞情(daily_hot_report.py) → 墨笔文创(flywheel_content.py) → 墨测数据(flywheel_distribute.py)")
    parts.append(f"- **飞书推送**：可复制至飞书群/邮件发送")
    parts.append(f"- **自动更新**：每日 08:00 定时生成")
    parts.append(f"")
    
    return "\n".join(parts)


# ============================================================
# 主流程
# ============================================================

def main():
    os.makedirs(RELAY_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    
    now = datetime.now()
    print(f"📊 [CH4-E 每日AI情报简报] {now.strftime('%Y-%m-%d %H:%M')} 开始生成...")
    print(f"📥 输入: {INPUT_FILE}")
    
    # Step 1: 加载情报
    intel = load_intelligence()
    source = intel.get('source', '未知')
    print(f"[📊] 情报来源: {source}")
    
    # Step 2: 生成简报
    print(f"[✏️] 墨研竞情整理简报内容...")
    briefing = build_briefing(intel)
    
    # Step 3: 输出简报
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(briefing)
    
    print(f"[✓] 简报已写入: {OUTPUT_FILE}")
    
    # 预览前几行
    preview_lines = briefing.split("\n")[:15]
    print(f"\n📋 简报预览:")
    print("=" * 40)
    print("\n".join(preview_lines))
    print("...")
    print("=" * 40)
    print(f"[📝] 简报共 {len(briefing.split(chr(10)))} 行，{len(briefing)} 字符")
    
    # 保存日志副本
    log_path = os.path.join(LOG_DIR, f"briefing_{now.strftime('%Y%m%d')}.md")
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(briefing)
    print(f"[📝] 简报日志已保存: {log_path}")
    print(f"[✓] 简报生成完成，可直接复制发布至飞书或邮件。")
    
    # ── 可选飞书推送 ─────────────────────────────────
    try:
        from molib.ceo.feishu_card import feishu_send_card, build_daily_briefing_card
        
        # 提取核心数据
        hot_cats = intel.get("hot_categories", [])
        top_notes = intel.get("top_notes", [])
        suggestions = intel.get("suggestions", [])
        github_hot = intel.get("github_hot", [])
        weibo_summary = intel.get("weibo_summary", "")
        
        # 构建 stats
        stats = {}
        if hot_cats:
            hottest = max(hot_cats, key=lambda x: x.get("heat", 0))
            stats["🔥 最热品类"] = f"{hottest.get('category','')} ({hottest.get('heat',0)})"
            stats["📊 品类数"] = f"{len(hot_cats)}个"
        if top_notes:
            stats["🏆 爆款数"] = f"{len(top_notes)}篇"
        if github_hot:
            stats["🐙 GitHub"] = f"{len(github_hot)}个项目"
        stats["📡 数据状态"] = "✅ 实时" if "placeholder" not in intel.get("source", "") else "⚠️ 占位"
        
        # 构建 highlights
        highlights = []
        if top_notes:
            for n in top_notes[:3]:
                highlights.append(f"🔥 {n.get('title','')[:30]} — ❤️{n.get('likes',0)} ({n.get('category','')})")
        if hot_cats:
            for c in hot_cats[:2]:
                highlights.append(f"📈 {c.get('category','')} 热度{c.get('heat',0)} · 收藏率{c.get('collect_ratio',0)}%")
        
        # 构建 warnings
        warnings = []
        if "placeholder" in intel.get("source", ""):
            warnings.append("⚠️ 情报数据为占位数据，未从真实数据源采集")
        if not github_hot:
            warnings.append("📡 GitHub趋势数据为空")
        if suggestions:
            top_sug = suggestions[0]
            warnings.append(f"💡 {top_sug.get('category','')}: {top_sug.get('action','')} — {top_sug.get('owner','')}")
        
        card = build_daily_briefing_card(
            date=now.strftime("%Y-%m-%d"),
            stats=stats,
            highlights=highlights,
            warnings=warnings,
            color="blue"
        )
        feishu_send_card(card)
        print(f"[✅ 飞书推送] 简报卡片已发送")
    except ImportError:
        print(f"[ℹ️ 飞书推送] molib.ceo.feishu_card 不可用，跳过")
    except Exception as e:
        print(f"[⚠️ 飞书推送] 发送失败: {e}")

if __name__ == "__main__":
    main()
