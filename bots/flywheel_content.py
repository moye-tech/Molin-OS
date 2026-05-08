#!/usr/bin/env python3.12
"""
墨麟 · 飞轮第二棒：内容草稿生成 v1.0

功能：
- 读取 relay/intelligence_morning.json（第一棒情报）
- 基于情报趋势，AI生成3篇内容草稿
- 写入 relay/content_flywheel.json（供第三棒分发）

内容格式：
{
  "timestamp": "ISO格式时间戳",
  "topics": [
    {
      "title": "标题",
      "body": "正文内容",
      "tags": ["标签1", "标签2"],
      "platform": "xhs",
      "cover_prompt": "封面AI提示词"
    }
  ],
  "analysis": {
    "summary": "今日内容策略分析摘要"
  }
}

子公司参与：墨笔文创(内容生成) → 墨图设计(封面参考)
涉及时区：北京时间 (UTC+8)
"""

import json
import os
import random
import time
from datetime import datetime


# ============================================================
# 配置区
# ============================================================

RELAY_DIR = os.path.expanduser("~/hermes-os/relay")
INPUT_FILE = os.path.join(RELAY_DIR, "intelligence_morning.json")
OUTPUT_FILE = os.path.join(RELAY_DIR, "content_flywheel.json")
LOG_DIR = os.path.expanduser("~/.hermes/daily_reports")

# 品类→内容模板映射
CONTENT_TEMPLATES = {
    "AI工具": {
        "title_prefix": ["2026必看！", "亲测好用！", "效率翻倍的"],
        "title_suffix": ["合集，收藏就够", "推荐，第3个绝了", "清单，建议收藏"],
        "style": "合集型",
        "hook": "你是不是也在找好用的AI工具？"
    },
    "AI副业": {
        "title_prefix": ["用AI搞钱", "副业月入", "AI让你"],
        "title_suffix": ["，我实操了一个月", "，小白也能做", "，真实收入曝光"],
        "style": "经验分享型",
        "hook": "分享一个我用AI赚到第一桶金的方法"
    },
    "一人公司 AI": {
        "title_prefix": ["一人公司", "一个人+AI", "零成本创业"],
        "title_suffix": ["，我的日常流程", "，如何同时做10件事", "，效率是团队的10倍"],
        "style": "人设IP型",
        "hook": "一个人怎么撑起一家公司？答案：AI"
    },
    "AI教程": {
        "title_prefix": ["零基础学", "手把手教你", "保姆级教程"],
        "title_suffix": ["，10分钟上手", "，从入门到精通", "，建议收藏反复看"],
        "style": "教程型",
        "hook": "今天教大家一个超实用的AI技巧"
    },
    "AI创业": {
        "title_prefix": ["2026 AI创业", "下一个风口", "我靠AI创业"],
        "title_suffix": ["方向，现在入场还来得及", "，月入5万的真实经历", "，这3个坑千万别踩"],
        "style": "商业分析型",
        "hook": "AI创业的黄金时代，普通人怎么抓住？"
    },
    "AI自动化": {
        "title_prefix": ["自动化工作流", "AI自动搞定", "一键自动化"],
        "title_suffix": ["，从此不用加班", "，每天省出3小时", "，效率提升10倍"],
        "style": "技术流型",
        "hook": "别再手动重复了，让AI帮你自动处理"
    },
    "AI编程": {
        "title_prefix": ["AI编程神器", "不会代码也能", "用AI写代码"],
        "title_suffix": ["，效率翻倍的秘密", "，Cursor vs Copilot实测", "，小白也能做项目"],
        "style": "技术教程型",
        "hook": "有了AI，编程不再是程序员的专利"
    },
    "AI设计": {
        "title_prefix": ["AI设计大师", "用AI做设计", "Midjourney玩出花"],
        "title_suffix": ["，封面图一键生成", "，我的Prompt配方公开", "，从入门到接单"],
        "style": "设计教程型",
        "hook": "不会PS也能做设计，AI就是你的设计师"
    }
}

# 封面Prompt模板（基于SOUL.md爆款封面3大类型）
COVER_TEMPLATES = {
    "干货拼贴型": {
        "type": "A",
        "prompt": "小红书封面图，白色/浅灰色背景，亮色占比80%以上，暖色调为主，多张界面截图拼贴排列，顶部覆盖大号粗体标题文字，文字清晰简洁，风格干净利落，排版紧凑，适合教程/工具推荐类"
    },
    "情绪金句型": {
        "type": "B",
        "prompt": "小红书封面图，纯色浅背景（浅蓝/浅粉/米白），亮色占比90%以上，中央大号情感化标题文字，文字对比度柔和，留白多，画面干净简约，像公众号封面风格"
    },
    "产品场景型": {
        "type": "C",
        "prompt": "小红书封面图，单一产品/场景大图展示，杂志风格构图，画面精致，产品居中或左置，右侧或底部覆盖文字，文字简洁有力，视觉焦点明确"
    }
}


# ============================================================
# 数据加载模块
# ============================================================

def load_intelligence() -> dict:
    """读取第一棒的情报数据"""
    if not os.path.exists(INPUT_FILE):
        print(f"[⚠] 未检测到 {INPUT_FILE}，生成占位情报数据")
        return generate_placeholder_intel()
    
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"[✓] 成功读取 {INPUT_FILE}")
        return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"[⚠] 读取 {INPUT_FILE} 失败 ({e})，使用占位数据")
        return generate_placeholder_intel()


def generate_placeholder_intel() -> dict:
    """生成占位情报数据"""
    return {
        "timestamp": datetime.now().isoformat(),
        "source": "placeholder (无真实情报)",
        "hot_categories": [
            {"category": c, "heat": 5000, "collect_ratio": 120, "suggestion": "占位数据"}
            for c in ["AI工具", "AI教程", "AI副业"]
        ],
        "suggestions": [
            {"category": "🔧 工具合集", "reason": "占位：品类热度持续", "action": "跟风产出", "owner": "墨笔文创"},
            {"category": "📚 教程实操", "reason": "占位：收藏率稳定", "action": "跟风产出", "owner": "墨学教育"},
        ],
        "weibo_summary": "占位数据：无微博热点",
        "github_hot": []
    }


# ============================================================
# 内容草稿生成模块
# 实际部署时取消注释下方 LLMClient 调用，替换 print() 草稿输出
# 参考: molib/ceo/llm_client.py — async def simple_chat(prompt, system, model)
# ============================================================

def generate_content_drafts(intel: dict) -> list:
    """基于情报数据生成3篇内容草稿"""
    
    # 从情报中提取热点品类
    hot_categories = []
    for cat in intel.get("hot_categories", []):
        name = cat.get("category", "")
        heat = cat.get("heat", 0)
        if name and heat > 0:
            hot_categories.append((name, heat, cat.get("collect_ratio", 0)))
    
    # 按热度排序
    hot_categories.sort(key=lambda x: x[1], reverse=True)
    
    # 从suggestions中提取选题方向
    suggestions = intel.get("suggestions", [])
    
    # 如果没有热点数据，使用默认
    if not hot_categories:
        hot_categories = [
            ("AI工具", 5000, 120),
            ("AI教程", 5000, 150),
            ("AI副业", 4000, 110),
        ]
    
    drafts = []
    
    # 确定选题品类（取前3个热门品类）
    selected_categories = []
    for cat, heat, cr in hot_categories:
        if len(selected_categories) >= 3:
            break
        if cat not in [s[0] for s in selected_categories]:
            selected_categories.append((cat, heat, cr))
    
    # 如果不够3个，从suggestions补
    while len(selected_categories) < 3 and suggestions:
        sug = suggestions.pop(0)
        cat_name = sug.get("category", "").replace("🔧 ", "").replace("📚 ", "").replace("💰 ", "").replace("🚀 ", "").replace("⚡ ", "").replace("💻 ", "").replace("🎨 ", "").replace("🏢 ", "")
        # 找对应的category名
        matched = None
        for template_name in CONTENT_TEMPLATES:
            if template_name in cat_name or cat_name in template_name:
                matched = template_name
                break
        if matched and matched not in [s[0] for s in selected_categories]:
            selected_categories.append((matched, 3000, 100))
    
    # 还是不够，补默认
    defaults = [("AI工具", 3000, 120), ("AI教程", 3000, 150), ("AI副业", 3000, 110)]
    while len(selected_categories) < 3 and defaults:
        d = defaults.pop(0)
        if d[0] not in [s[0] for s in selected_categories]:
            selected_categories.append(d)
    
    # 为每个品类生成一篇内容
    for cat_name, heat, collect_ratio in selected_categories[:3]:
        draft = generate_single_draft(cat_name, heat, collect_ratio, intel)
        if draft:
            drafts.append(draft)
    
    return drafts


def generate_single_draft(category: str, heat: int, collect_ratio: int, intel: dict) -> dict:
    """为单个品类生成内容草稿"""
    template = CONTENT_TEMPLATES.get(category, CONTENT_TEMPLATES["AI工具"])
    
    # 生成标题
    title = generate_title(template, category, heat)
    
    # 根据风格生成正文
    body = generate_body(template, category, heat, collect_ratio, intel)
    
    # 生成标签
    tags = generate_tags(category)
    
    # 生成封面提示词
    cover_type = template.get("style", "干货拼贴型")
    cover_prompt = generate_cover_prompt(cover_type, category, title)
    
    return {
        "title": title,
        "body": body,
        "tags": tags,
        "platform": "xhs",
        "cover_prompt": cover_prompt
    }


def generate_title(template: dict, category: str, heat: int) -> str:
    """生成爆款标题"""
    prefix = random.choice(template["title_prefix"])
    suffix = random.choice(template["title_suffix"])
    
    # 品类关键词映射
    category_keywords = {
        "AI工具": "AI效率工具",
        "AI副业": "AI副业项目",
        "一人公司 AI": "AI一人公司",
        "AI教程": "AI教程",
        "AI创业": "AI创业项目",
        "AI自动化": "团队工作流",
        "AI编程": "AI编程",
        "AI设计": "AI设计工具"
    }
    
    keyword = category_keywords.get(category, category)
    
    # 有时使用情绪化标题
    if random.random() < 0.3:
        emotional_titles = [
            f"后悔没早点知道的{keyword}",
            f"用了{keyword}，我再也不加班了",
            f"靠{keyword}月入过万，我的真实经历",
            f"别划走！这个{keyword}你一定要知道",
        ]
        return random.choice(emotional_titles)
    
    return f"{prefix}{keyword}{suffix}"


def generate_body(template: dict, category: str, heat: int, collect_ratio: int, intel: dict) -> str:
    """生成正文内容"""
    hook = template.get("hook", "今天给大家分享一个实用内容")
    style = template.get("style", "合集型")
    
    # 从情报中提取数据佐证
    hot_items = intel.get("top_notes", [])
    hot_item_titles = [n.get("title", "") for n in hot_items[:3]]
    
    # 生成不同风格的正文
    if style == "合集型":
        body = f"""{hook} 📌

我花了一周时间，从市面上几十款{category}里筛选出这3个真正好用的，全都是亲测有效的👇

1️⃣ 第一个：效率神器，每天帮我省2小时
- 自动处理重复工作
- 一键生成周报/日报
- 支持主流AI模型

2️⃣ 第二个：内容创作利器
- 写小红书/公众号/朋友圈
- 智能配图+排版
- 批量生成不重样

3️⃣ 第三个：数据分析好帮手
- 自动整理Excel/CSV
- 可视化图表一键出
- 支持自然语言查询

💡 小贴士：建议先玩免费版，顺手了再升级Pro

📊 数据参考：今日该品类热度{heat}🔥，收藏率{collect_ratio}% ⭐

#一人公司 #AI工具 #效率提升"""

    elif style == "经验分享型":
        body = f"""{hook} 💰

直接说结论：{category}真的能赚钱，关键是要找对方法。

我总结了这个品类的3个变现路径👇

📌 路径一：内容变现
- 做教程类内容引流
- 靠收藏量和粉丝增长
- 积累到1000粉开蒲公英

📌 路径二：工具变现
- 打包自己的工具清单
- 做成PDF/Notion模板
- 定价9.9-49.9元

📌 路径三：咨询变现
- 1对1指导服务
- 社群会员制
- 定价199-999元

⚠️ 注意：不要一开始就想着变现，先做好内容价值。

🔥 今日该品类热度{heat}，建议把握窗口期"""

    elif style == "人设IP型":
        body = f"""{hook} 🏢

很多人问我：一个人怎么撑起一家公司？

答案很简单——AI就是你的团队。

我的日常流程👇
🕐 8:00 AI助手整理今日待办
🕐 9:00 用AI写第一篇内容
🕐 10:00 AI自动回复私信
🕐 14:00 AI分析数据出报表
🕐 16:00 AI生成设计图
🕐 18:00 AI复盘今日数据

一个人+AI = 团队的10倍效率

💡 关键不是用最多的AI工具，而是建好你的工作流。

📊 今日该品类热度{heat}🔥，收藏率{collect_ratio}% ⭐"""

    elif style == "教程型":
        body = f"""{hook} 📚

超详细教程，建议先收藏再看⭐

Step 1：准备工作
- 打开[工具名]官网
- 注册账号（有免费额度）
- 选择模板或新建

Step 2：核心操作
跟着下面这3步走，10分钟搞定👇
① 输入你的需求描述
② 选择输出格式（图文/视频/数据）
③ 点击生成，等待结果

Step 3：优化调整
- 不满意就换Prompt
- 加更多具体描述
- 多次生成选最好的

🎯 关键技巧：
"Prompt越具体，输出越精准"

📊 该品类今日收藏率{collect_ratio}%，说明大家都在学这个🔥"""

    elif style in ("技术流型", "技术教程型"):
        body = f"""{hook} ⚡

还在手动重复操作？太浪费时间了！

下面这套{category}工作流，建议直接抄👇

🔹 场景一：批量处理
以前：一个一个手动操作，花2小时
现在：AI一键批量处理，花3分钟
效果：效率提升40倍

🔹 场景二：数据分析
以前：复制粘贴到Excel，做图表半天
现在：直接问AI，秒出分析结果
效果：效率提升20倍

🔹 场景三：内容生产
以前：憋一篇文案要半天
现在：AI辅助写作，改改就能发
效果：效率提升10倍

💡 核心思路：找到你的重复劳动点，让AI去干。

#AI自动化 #效率提升 #工作流"""

    else:
        # 默认风格
        body = f"""{hook} 🔥

今天来聊聊{category}这个方向。

📊 先看数据：
今日该品类热度{heat}🔥
收藏率{collect_ratio}%
说明这个方向非常值得投入。

💡 我的建议：
1. 先关注3-5个该领域的大V
2. 学习他们的内容风格和选题
3. 找到差异化切入点
4. 坚持日更或者周更3篇

🚀 行动比完美更重要，先发出去再说！

#一人公司 #AI创业 #知识分享"""

    return body.strip()


def generate_tags(category: str) -> list:
    """生成内容标签"""
    base_tags = {
        "AI工具": ["AI工具", "效率工具", "生产力", "工具推荐", "一人公司"],
        "AI副业": ["AI副业", "副业赚钱", "搞钱", "被动收入", "一人公司"],
        "一人公司 AI": ["一人公司", "AI创业", "效率提升", "数字游民", "远程工作"],
        "AI教程": ["AI教程", "AI学习", "效率提升", "黑科技", "技能提升"],
        "AI创业": ["AI创业", "创业", "商业思维", "风口", "趋势"],
        "AI自动化": ["自动化", "工作流", "效率提升", "AI工具", "生产力"],
        "AI编程": ["AI编程", "编程工具", "效率", "程序员", "黑科技"],
        "AI设计": ["AI设计", "设计工具", "封面设计", "视觉", "Midjourney"],
    }
    tags = base_tags.get(category, ["AI工具", "效率工具", "一人公司"])
    
    # 偶尔混入随机热门标签
    if random.random() < 0.3:
        trending_tags = ["效率提升", "每天进步一点点", "干货分享", "实用技巧", "宝藏工具"]
        tags.append(random.choice(trending_tags))
    
    return tags


def generate_cover_prompt(style: str, category: str, title: str) -> str:
    """生成封面AI提示词"""
    
    # 匹配封面类型
    if "合集" in style or "教程" in style:
        cover_key = "干货拼贴型"
    elif "IP" in style or "人设" in style or "商业" in style or "金句" in style:
        cover_key = "情绪金句型"
    else:
        cover_key = "产品场景型"
    
    cover_data = COVER_TEMPLATES.get(cover_key, COVER_TEMPLATES["干货拼贴型"])
    
    # 补充品类特定描述
    category_descriptions = {
        "AI工具": "多款AI工具界面截图拼贴，暖色调为主",
        "AI副业": "突出金钱/收益的视觉元素，数字金额醒目",
        "一人公司 AI": "一个人的办公桌/电脑场景，孤独但专注",
        "AI教程": "界面步骤截图，箭头标注，操作流程清晰",
        "AI创业": "商业图表/上升曲线，搭配产品模型",
        "AI自动化": "流程图/自动化管道图示，科技感蓝色调",
        "AI编程": "代码编辑器界面，彩色代码高亮",
        "AI设计": "精美设计作品展示，艺术感强",
    }
    extra_desc = category_descriptions.get(category, "")
    
    full_prompt = f"{cover_data['prompt']}。{extra_desc}。封面标题文字：'{title}'。小红书风格，3:4比例，清晰美观。"
    
    return full_prompt


def generate_analysis_summary(intel: dict, drafts: list) -> dict:
    """生成内容策略分析"""
    categories = [d.get("tags", [None])[0] if d.get("tags") else "未知" for d in drafts]
    
    # 从情报提取关键数据
    hot_cats = intel.get("hot_categories", [])
    top_cats_str = "、".join([c.get("category", "") for c in hot_cats[:3]]) if hot_cats else "暂无数据"
    
    suggestions = intel.get("suggestions", [])
    sug_str = "；".join([s.get("action", "") for s in suggestions[:2]]) if suggestions else "常规产出"
    
    summary = (
        f"今日热点品类：{top_cats_str}。"
        f"今日生成内容涵盖：{', '.join(categories)}。"
        f"策略建议：{sug_str}。"
        f"共生成{len(drafts)}篇内容草稿，均适配小红书平台。"
    )
    
    return {
        "summary": summary,
        "total_drafts": len(drafts),
        "top_categories": top_cats_str,
        "strategies": sug_str
    }


# ============================================================
# 主流程
# ============================================================

def main():
    os.makedirs(RELAY_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    
    now = datetime.now()
    print(f"🔄 [飞轮第二棒] {now.strftime('%Y-%m-%d %H:%M')} 开始...")
    print(f"📥 输入: {INPUT_FILE}")
    
    # Step 1: 加载情报
    intel = load_intelligence()
    print(f"[📊] 情报来源: {intel.get('source', '未知')}")
    print(f"[📊] 热点品类数: {len(intel.get('hot_categories', []))}")
    print(f"[📊] 选题建议数: {len(intel.get('suggestions', []))}")
    
    # Step 2: 生成内容草稿
    print(f"[✏️] 墨笔文创开始创作...")
    drafts = generate_content_drafts(intel)
    print(f"[✓] 共生成 {len(drafts)} 篇内容草稿")
    
    for i, d in enumerate(drafts, 1):
        print(f"  {i}. [{d.get('platform', '?')}] {d.get('title', '无标题')[:40]}")
    
    # Step 3: 生成分析摘要
    analysis = generate_analysis_summary(intel, drafts)
    
    # Step 4: 写入输出
    output = {
        "timestamp": now.isoformat(),
        "source": "flywheel_content.py v1.0",
        "input_source": intel.get("source", "unknown"),
        "topics": drafts,
        "analysis": analysis
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"[✓] 输出已写入: {OUTPUT_FILE}")
    print(f"[📝] 内容策略: {analysis['summary']}")
    print(f"[🔄] 飞轮第二棒完成，等待第三棒...")
    
    # 同时保存一份日志
    log_path = os.path.join(LOG_DIR, f"content_flywheel_{now.strftime('%Y%m%d')}.json")
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"[📝] 日志已保存: {log_path}")


if __name__ == "__main__":
    main()
