"""
火花思维文案矩阵 → 飞书互动卡片 · 批量发送
CardRouter 管线：墨麟OS T3 内容预览卡片
"""
import re
import sys
from pathlib import Path

# ── 解析文案矩阵 markdown ──
md_path = Path("/Users/moye/火花思维营销文案矩阵_墨笔文创.md")
text = md_path.read_text()

# 按 ## 角度 分割
angles = []
current = None
for line in text.split("\n"):
    m = re.match(r"^## 角度([一二三四五六七八九十]+)：(.+)$", line)
    if m:
        if current:
            angles.append(current)
        current = {"num": m.group(1), "topic": m.group(2).strip(), "lines": []}
    elif current:
        current["lines"].append(line)
if current:
    angles.append(current)

# ── 提取每个角度的结构化字段 ──
def parse_angle(angle):
    body = "\n".join(angle["lines"])
    result = {
        "num": angle["num"],
        "topic": angle["topic"],
        "title": "",
        "subtitle": "",
        "tags": [],
        "trust": "",
        "cta": "",
    }
    # 主标题
    m = re.search(r"\*\*主标题\*\*\s*\|\s*(.+?)\s*\|", body)
    if m:
        result["title"] = m.group(1).strip()
    # 副标题
    m = re.search(r"\*\*副标题\*\*\s*\|\s*(.+?)\s*\|", body)
    if m:
        result["subtitle"] = m.group(1).strip()
    # 卖点标签
    for m in re.finditer(r"[-*]\s*`([^`]+)`", body):
        tag = m.group(1).strip()
        if tag not in result["tags"]:
            result["tags"].append(tag)
    # 信任锚点
    m = re.search(r"\*\*信任锚点\*\*[：:]\s*(.+)", body)
    if m:
        result["trust"] = m.group(1).strip()
    # CTA
    m = re.search(r"\*\*CTA\*\*[：:]\s*(.+)", body)
    if m:
        result["cta"] = m.group(1).strip()
    return result

parsed = [parse_angle(a) for a in angles]

# ── 构建卡片并发送 ──
from molib.ceo.cards.builder import CardBuilder, TURQUOISE, BLUE, GREEN
from molib.infra.gateway.feishu_output_enforcer import FeishuOutputEnforcer

TARGET = "oc_94c87f141e118b68c2da9852bf2f3bda"
enforcer = FeishuOutputEnforcer(chat_id=TARGET)

num_map = {"一": "1", "二": "2", "三": "3", "四": "4", "五": "5", "六": "6",
           "七": "7", "八": "8", "九": "9", "十": "10", "十一": "11", "十二": "12"}

sent = 0
failed = []

for i, p in enumerate(parsed):
    n = num_map.get(p["num"], str(i + 1))
    color = GREEN if i < 3 else (TURQUOISE if i < 10 else BLUE)

    # 构建卡片
    card = CardBuilder(
        title=f"📋 角度{n}：{p['topic']}",
        color=color,
    )

    # 主标题 + 副标题
    card.add_div(f"**{p['title']}**")
    card.add_div(p['subtitle'])
    card.add_hr()

    # 卖点标签
    card.add_div(f"**卖点标签**")
    for tag in p["tags"][:3]:
        card.add_div(f"· {tag}")
    card.add_hr()

    # 信任锚点
    card.add_div(f"🔒 {p['trust']}")
    card.add_hr()

    # CTA
    card.add_div(f"👉 {p['cta']}")

    # 脚注
    card.add_note(f"墨笔文创 · 墨迹内容 | 角度{n}/12 | 火花思维项目")

    # 发送
    try:
        card_dict = card.build()
        result = enforcer.send_card(card_dict)
        if result.get("status") == "blocked":
            failed.append(f"角度{n}: blocked - {result.get('violations')}")
        else:
            sent += 1
            print(f"✅ 角度{n} ({p['topic']}) 已发送")
    except Exception as e:
        failed.append(f"角度{n}: {e}")
        print(f"❌ 角度{n} 发送失败: {e}")

print(f"\n发送完成: {sent}/{len(parsed)} 成功")
if failed:
    for f in failed:
        print(f"  ❌ {f}")
