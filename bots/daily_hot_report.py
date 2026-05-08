#!/usr/bin/env python3.12
"""
墨麟 · 每日AI热点日报 v2.0

数据源：
1. 微博热搜 (AI相关检测)
2. 小红书AI品类搜索 (xhs-cli)
3. GitHub Trending (AI projects)
4. 百度热搜 (fallback)

输出：
- 飞书控制台群推送（结构化卡片）
- 本地日志存档
- 每日选题建议

子公司参与：墨研竞情(情报) → 墨笔文创(选题) → 墨梦AutoDream(分析)

涉及时区：北京时间 (UTC+8)
"""
import json
import subprocess
import sys
import os
import re
from datetime import datetime
import urllib.request
from typing import Optional

# ============================================================
# 配置区
# ============================================================
NOTIFY_CHAT_ID = "oc_94c87f141e118b68c2da9852bf2f3bda"
LOG_DIR = os.path.expanduser("~/.hermes/daily_reports")
XHS_COOKIE_PATH = os.path.expanduser("~/.xiaohongshu-cli/cookies.json")

# AI关键词检测列表（权重分三级）
AI_KEYWORDS_HIGH = ['ai', '人工智能', 'gpt', 'deepseek', 'chatgpt', 'claude', '大模型', 'sora']
AI_KEYWORDS_MED = ['大语言模型', '机器人', '算法', '算力', '神经', '机器学习', '深度学习', 'llm', 'openai']
AI_KEYWORDS_LOW = ['数据', '芯片', '模型', '代码', '编程', '无人', '智能', '自动化', 'agent', 'copilot']

# 小红书品类搜索策略
XHS_SEARCH_KEYWORDS = [
    "AI工具",          # 工具合集
    "AI副业",          # 副业搞钱
    "一人公司 AI",     # 创业商业
    "AI教程",          # 教程实操
    "AI创业",          # 创业
    "AI自动化",        # 自动化效率
    "AI编程",          # 程序员方向
    "AI设计",          # 设计创作
]

XHS_CATEGORY_MAP = {
    "AI工具": ("🔧 工具合集", "收藏率高，适合做合集型内容", "墨笔文创"),
    "AI副业": ("💰 副业搞钱", "互动量大，评论区活跃，易引争议", "墨域私域"),
    "一人公司 AI": ("🏢 一人公司", "涨粉快，人设型内容，IP化最佳方向", "墨笔文创"),
    "AI教程": ("📚 教程实操", "收藏率最高(>100%)，长尾流量稳定", "墨学教育"),
    "AI创业": ("🚀 创业商业", "信任度高，适合做深度IP", "墨商BD"),
    "AI自动化": ("⚡ 自动化效率", "技术流，差异化强，竞争少", "墨码开发"),
    "AI编程": ("💻 AI编程", "程序员关注度高，转评活跃", "墨码开发"),
    "AI设计": ("🎨 AI设计", "视觉内容，小红书天然受众", "墨图设计"),
}

# ============================================================
# 数据采集模块
# ============================================================

def fetch_weibo_hot() -> dict:
    """获取微博热搜，含AI相关性分析"""
    req = urllib.request.Request(
        "https://weibo.com/ajax/side/hotSearch",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://weibo.com/"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        return {"error": str(e), "total": 0, "categories": {}, "ai_related": [], "top_10": []}
    
    realtime = data.get('data', {}).get('realtime', [])
    categories = {}
    ai_related = []
    top_10_list = []
    
    for item in realtime:
        cat = item.get('category', '其他')
        word = item.get('word', '')
        hot = item.get('raw_hot', 0) or item.get('num', 0)
        rank = item.get('rank', 0)
        entry = {"word": word, "hot": hot, "rank": rank}
        categories.setdefault(cat, []).append(entry)
        
        # AI相关性打分
        ai_score = 0
        word_lower = word.lower()
        for kw in AI_KEYWORDS_HIGH:
            if kw in word_lower: ai_score += 3
        for kw in AI_KEYWORDS_MED:
            if kw in word_lower: ai_score += 2
        for kw in AI_KEYWORDS_LOW:
            if kw in word_lower: ai_score += 1
        
        if ai_score > 0:
            entry['ai_score'] = ai_score
            ai_related.append(entry)
    
    # 取前10
    for item in realtime[:10]:
        top_10_list.append({
            "word": item.get('word', ''),
            "hot": item.get('raw_hot', 0) or item.get('num', 0),
            "rank": item.get('rank', 0)
        })
    
    return {
        "total": len(realtime),
        "categories": categories,
        "ai_related": sorted(ai_related, key=lambda x: x.get('ai_score', 0), reverse=True),
        "top_10": top_10_list
    }


def fetch_xhs_trending() -> dict:
    """通过xhs-cli搜索多个AI关键词"""
    results = {}
    
    for kw in XHS_SEARCH_KEYWORDS:
        try:
            out = subprocess.run(
                ["xhs", "search", kw, "--json"],
                capture_output=True, text=True, timeout=20
            ).stdout
            data = json.loads(out)
            items = data.get('data', {}).get('items', []) or data.get('items', [])
            notes = []
            for item in items[:5]:
                nc = item.get('note_card', {})
                interact = nc.get('interact_info', {})
                title = (nc.get('display_title', '') or nc.get('title', '')).strip()
                if not title:
                    continue
                notes.append({
                    "title": title[:50],
                    "likes": int(interact.get('liked_count', 0) or 0),
                    "collects": int(interact.get('collected_count', 0) or 0),
                    "comments": int(interact.get('comment_count', 0) or 0),
                    "author": nc.get('user', {}).get('nick_name', '?'),
                    "collect_ratio": 0  # calculated below
                })
            # 计算收藏率
            for n in notes:
                if n['likes'] > 0:
                    n['collect_ratio'] = round(n['collects'] / n['likes'] * 100)
            
            results[kw] = notes
        except Exception as e:
            results[kw] = []
    
    return results


def fetch_github_trending() -> list:
    """获取GitHub AI相关趋势项目"""
    try:
        out = subprocess.run(
            ["curl", "-s", 
             "https://api.github.com/search/repositories?q=AI+created:>2026-04-01&sort=stars&order=desc&per_page=10",
             "-H", "Accept: application/vnd.github+json"],
            capture_output=True, text=True, timeout=15
        ).stdout
        data = json.loads(out)
        items = data.get('items', [])
        return [{
            "name": item['full_name'],
            "stars": item['stargazers_count'],
            "desc": (item.get('description') or '')[:60],
            "lang": item.get('language') or '未知'
        } for item in items[:8]]
    except:
        return []


# ============================================================
# 分析模块
# ============================================================

def analyze_trends(xhs_data: dict, weibo_data: dict) -> dict:
    """深度分析趋势方向"""
    
    # 1. 找出今日热点品类
    category_heat = {}
    for kw, notes in xhs_data.items():
        if notes:
            total_likes = sum(n['likes'] for n in notes)
            total_collects = sum(n['collects'] for n in notes)
            category_heat[kw] = {
                "total_likes": total_likes,
                "total_collects": total_collects,
                "avg_collect_ratio": round(total_collects / total_likes * 100) if total_likes > 0 else 0,
                "count": len(notes)
            }
    
    # 2. 找爆款笔记
    all_notes = []
    for kw, notes in xhs_data.items():
        for n in notes:
            n['category'] = kw
            all_notes.append(n)
    
    top_by_likes = sorted(all_notes, key=lambda x: x['likes'], reverse=True)[:5]
    top_by_collect = sorted(all_notes, key=lambda x: x['collect_ratio'], reverse=True)[:3]
    
    # 3. 今日差异化选题建议
    suggestions = []
    
    # 看哪个品类均赞最高且笔记数少（蓝海）
    for kw, heat in sorted(category_heat.items(), key=lambda x: x[1]['total_likes'], reverse=True):
        cat_info = XHS_CATEGORY_MAP.get(kw, ("", "", ""))
        if heat['count'] >= 3 and heat['total_likes'] > 2000:
            suggestions.append({
                "category": cat_info[0] or kw,
                "reason": f"今日{heat['count']}条笔记均赞{heat['total_likes']//heat['count']}，收藏率{heat['avg_collect_ratio']}%",
                "action": "适合跟风产出",
                "owner": cat_info[2] or "墨笔文创"
            })
    
    # 蓝海品类：均赞高但笔记数少
    for kw, heat in sorted(category_heat.items(), key=lambda x: x[1]['avg_collect_ratio'], reverse=True):
        cat_info = XHS_CATEGORY_MAP.get(kw, ("", "", ""))
        if heat['count'] <= 2 and heat['total_likes'] > 500:
            suggestions.append({
                "category": cat_info[0] or kw,
                "reason": f"笔记数少({heat['count']})但收藏率{heat['avg_collect_ratio']}% → 蓝海",
                "action": "抢先入场，差异化切入",
                "owner": cat_info[2] or "墨研竞情"
            })
    
    return {
        "category_heat": category_heat,
        "top_by_likes": top_by_likes,
        "top_by_collect": top_by_collect,
        "suggestions": suggestions[:4]
    }


# ============================================================
# 报告生成模块
# ============================================================

def build_report(weibo_data: dict, xhs_data: dict, github_data: list, analysis: dict) -> str:
    """生成可展示的报告文本"""
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    parts = []
    
    parts.append(f"📊 墨麟 AI 热点日报 | {today}")
    parts.append("=" * 40)
    parts.append("")
    
    # --- 微博热搜 ---
    parts.append("🔥 微博热搜")
    parts.append("-" * 30)
    if "error" in weibo_data:
        parts.append(f"⚠️ {weibo_data['error']}")
    else:
        parts.append(f"今日热搜共 {weibo_data['total']} 条")
        ai_items = weibo_data['ai_related']
        if ai_items:
            high_ai = [x for x in ai_items if x.get('ai_score', 0) >= 3]
            if high_ai:
                parts.append(f"🤖 高置信AI相关 ({len(high_ai)}条):")
                for item in high_ai[:3]:
                    parts.append(f"  #{item['rank']} {item['word']} (AI分:{item['ai_score']})")
            else:
                parts.append(f"🤖 今日暂无AI上热搜")
        else:
            parts.append(f"🤖 今日暂无AI上热搜")
        
        # 热搜分类概览
        cats_count = {k: len(v) for k, v in sorted(weibo_data['categories'].items(), key=lambda x: len(x[1]), reverse=True)[:5]}
        parts.append(f"\n📋 热搜分类: {' | '.join(f'{k}({v})' for k,v in cats_count.items())}")
        parts.append(f"📋 前10:")
        for item in weibo_data['top_10'][:10]:
            parts.append(f"  {item['rank']+1 if isinstance(item['rank'], int) else '?'}. {item['word']}")
    
    parts.append("")
    
    # --- 小红书AI热榜 ---
    parts.append("🤖 小红书 AI 趋势")
    parts.append("-" * 30)
    
    for kw in XHS_SEARCH_KEYWORDS:
        notes = xhs_data.get(kw, [])
        cat_name, cat_desc, owner = XHS_CATEGORY_MAP.get(kw, (kw, "", ""))
        if notes:
            best = max(notes, key=lambda n: n['likes'])
            parts.append(f"\n{cat_name}  [📌 {owner}]")
            parts.append(f"  🔥 热: 「{best['title']}」 ❤{best['likes']} ⭐{best['collects']} 💬{best['comments']}")
            if len(notes) > 1:
                avg = sum(n['likes'] for n in notes) // len(notes)
                avg_col = sum(n['collects'] for n in notes) // len(notes)
                parts.append(f"  📈 均赞{avg} 均收{avg_col}")
                # 收藏率分析
                best_ratio = max(notes, key=lambda n: n['collect_ratio'])
                if best_ratio['collect_ratio'] > 100:
                    parts.append(f"  ⭐ 最佳收藏率: 「{best_ratio['title'][:25]}」 {best_ratio['collect_ratio']}%")
        else:
            parts.append(f"\n{cat_name} 📡 数据采集中...")
    
    parts.append("")
    
    # --- GitHub AI热门项目 ---
    if github_data:
        parts.append("🐙 GitHub AI 趋势")
        parts.append("-" * 30)
        for proj in github_data[:5]:
            parts.append(f"  ⭐{proj['stars']:>5} {proj['name'][:40]} [{proj['lang']}]")
            parts.append(f"     {proj['desc']}")
        parts.append("")
    
    # --- 深度分析 ---
    parts.append("📈 今日品类热力图")
    parts.append("-" * 30)
    
    for kw, heat in sorted(analysis['category_heat'].items(), key=lambda x: x[1]['total_likes'], reverse=True):
        cat_name = XHS_CATEGORY_MAP.get(kw, (kw, "", ""))[0]
        bar = "█" * min(heat['total_likes'] // 500 + 1, 20)
        parts.append(f"  {cat_name:12s} {bar} {heat['total_likes']}赞 {heat['avg_collect_ratio']}%收")
    
    parts.append("")
    
    # --- 爆款笔记排行榜 ---
    parts.append("🏆 今日爆款榜 TOP5")
    parts.append("-" * 30)
    for i, note in enumerate(analysis['top_by_likes'][:5]):
        cat_name = XHS_CATEGORY_MAP.get(note['category'], (note['category'], "", ""))[0]
        parts.append(f"  {i+1}. 「{note['title']}」")
        parts.append(f"     ❤{note['likes']} ⭐{note['collects']} 💬{note['comments']} | {cat_name} | {note['author']}")
    
    parts.append("")
    
    # --- 今日选题建议 ---
    parts.append("💡 今日选题建议")
    parts.append("-" * 30)
    for s in analysis['suggestions']:
        parts.append(f"  【{s['category']}】{s['action']}")
        parts.append(f"  → {s['reason']}")
        parts.append(f"  负责: {s['owner']}")
    
    parts.append("")
    parts.append("=" * 40)
    parts.append(f"🔔 数据采集于 Hermes | 元瑶·墨研竞情 监控中")
    parts.append(f"  日志: {LOG_DIR}/")
    
    return "\n".join(parts)


# ============================================================
# 主流程
# ============================================================

def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    now = datetime.now()
    print(f"🔍 [墨麟日报 v2.0] {now.strftime('%Y-%m-%d %H:%M')} 开始数据采集...")
    
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as exe:
        f_weibo = exe.submit(fetch_weibo_hot)
        f_xhs = exe.submit(fetch_xhs_trending)
        f_github = exe.submit(fetch_github_trending)
        
        weibo_data = f_weibo.result()
        xhs_data = f_xhs.result()
        github_data = f_github.result()
    
    # 分析
    analysis = analyze_trends(xhs_data, weibo_data)
    
    # 构建报告
    report_text = build_report(weibo_data, xhs_data, github_data, analysis)
    print(report_text)
    
    # 保存日志
    log_path = os.path.join(LOG_DIR, f"daily_{now.strftime('%Y%m%d')}.json")
    with open(log_path, 'w') as f:
        json.dump({
            "timestamp": now.isoformat(),
            "weibo": {
                "total": weibo_data.get('total', 0),
                "ai_count": len(weibo_data.get('ai_related', [])),
            },
            "xhs_summary": {
                kw: [{"title": n['title'], "likes": n['likes'], "collects": n['collects'], "collect_ratio": n['collect_ratio']} for n in notes]
                for kw, notes in xhs_data.items() if notes
            },
            "github_trending": [{"name": p['name'], "stars": p['stars']} for p in github_data],
            "analysis": {
                "top_categories": list(analysis['category_heat'].keys())[:5],
                "suggestions": analysis['suggestions']
            }
        }, f, ensure_ascii=False, indent=2)
    print(f"\n[📝 日志已保存] {log_path}")
    
    # 写入 relay 目录（飞轮接力）
    relay_dir = os.path.expanduser("~/hermes-os/relay")
    os.makedirs(relay_dir, exist_ok=True)
    relay_path = os.path.join(relay_dir, f"intelligence_morning.json")
    relay_data = {
        "timestamp": now.isoformat(),
        "source": "daily_hot_report.py v2.0",
        "hot_categories": [
            {"category": kw, 
             "heat": analysis['category_heat'].get(kw, {}).get('total_likes', 0),
             "collect_ratio": analysis['category_heat'].get(kw, {}).get('avg_collect_ratio', 0),
             "suggestion": XHS_CATEGORY_MAP.get(kw, ("","",""))[1]}
            for kw in XHS_SEARCH_KEYWORDS
            if analysis['category_heat'].get(kw)
        ],
        "top_notes": [{"title": n['title'][:30], "likes": n['likes'], "category": XHS_CATEGORY_MAP.get(n['category'], (n['category'],"",""))[0]}
                      for n in analysis.get('top_by_likes', [])[:3]],
        "suggestions": analysis.get('suggestions', []),
        "weibo_summary": f"共{weibo_data.get('total',0)}条热搜，AI相关{len(weibo_data.get('ai_related',[]))}条",
        "github_hot": [{"name": p['name'], "stars": p['stars']} for p in github_data[:3]]
    }
    with open(relay_path, 'w') as f:
        json.dump(relay_data, f, ensure_ascii=False, indent=2)
    print(f"[🔄 飞轮接力] relay/intelligence_morning.json 已写入")

if __name__ == "__main__":
    main()
