---
name: email-newsletter
description: AI情报日报邮件列表 — 使用 Buttondown 免费版进行每日简报自动生成与发送，含邮件序列设计和转化漏斗
version: 0.1.0
tags:
- email
- newsletter
- automation
- marketing
- crm
- buttondown
metadata:
  hermes:
    molin_owner: 墨域私域
    service: Buttondown (buttondown.email)
    worker_ref: crm.py (墨域私域)
min_hermes_version: 0.13.0
---

# 邮件列表 — AI 情报日报

## 概述

AI 情报日报邮件列表系统，自动收集每日 AI 情报、生成简报内容，通过 Buttondown 免费版发送给订阅用户。可与 Hermes 飞轮管线（墨研竞情→墨笔文创）集成。

- **物主**: 墨域私域（crm.py Worker）
- **邮件服务**: Buttondown（免费版支持 1000 订阅者）
- **情报来源**: Hermes 每日热点日报管线

## Buttondown 免费版 API 配置

### 注册与 API Key

1. 访问 https://buttondown.email 注册账号
2. 进入 Settings → API Key，生成 API Token
3. 免费版限制：最多 1000 订阅者、每日最多 1 封邮件

### API 配置

```bash
# 环境变量
export BUTTONDOWN_API_TOKEN="your-api-token-here"
export BUTTONDOWN_NEWSLETTER_SLUG="ai-daily-briefing"
```

### 核心 API 端点

```python
import requests

API_BASE = "https://api.buttondown.email/v1"
HEADERS = {
    "Authorization": f"Token {BUTTONDOWN_API_TOKEN}",
    "Content-Type": "application/json",
}

# 发送邮件
def send_newsletter(subject: str, body: str):
    """发送邮件简报"""
    resp = requests.post(
        f"{API_BASE}/emails",
        headers=HEADERS,
        json={
            "subject": subject,
            "body": body,
            "status": "sent",  # 直接发送；设为 "draft" 则为草稿
        }
    )
    return resp.json()

# 创建草稿
def create_draft(subject: str, body: str):
    """创建邮件草稿"""
    resp = requests.post(
        f"{API_BASE}/emails",
        headers=HEADERS,
        json={
            "subject": subject,
            "body": body,
            "status": "draft",
        }
    )
    return resp.json()

# 列出订阅者
def list_subscribers():
    """获取订阅者列表"""
    resp = requests.get(f"{API_BASE}/subscribers", headers=HEADERS)
    return resp.json()

# 获取统计数据
def get_stats():
    """获取邮件统计"""
    resp = requests.get(f"{API_BASE}/stats", headers=HEADERS)
    return resp.json()
```

## 每日简报自动生成流程

### 飞轮管线集成

```
08:00 墨研竞情 → 扫描情报 → relay/intelligence_morning.json
     ↓
09:00 简报引擎 → 读取情报 + 生成简报 → relay/newsletter_daily.json
     ↓
09:30 墨域私域 → 调用 Buttondown API → 发送给订阅者
```

### 简报生成脚本

```python
#!/usr/bin/env python3
"""每日 AI 简报生成器"""

import json, os
from datetime import datetime
from pathlib import Path

def generate_daily_briefing() -> str:
    """从情报文件生成 HTML 简报"""
    relay_dir = Path("/home/ubuntu/hermes-os/relay")
    
    # 读取当日情报
    intel_file = relay_dir / "intelligence_morning.json"
    if not intel_file.exists():
        return "今日暂无情报数据"
    
    with open(intel_file) as f:
        intel = json.load(f)
    
    # 构建 HTML 简报
    today = datetime.now().strftime("%Y-%m-%d")
    html = f"""
    <h1>🤖 AI 情报日报 — {today}</h1>
    <hr>
    """
    
    for item in intel.get("items", []):
        html += f"""
        <h3>{item.get('title', '未命名')}</h3>
        <p>{item.get('summary', '暂无摘要')}</p>
        <p><a href="{item.get('url', '#')}">阅读全文 →</a></p>
        <hr>
        """
    
    html += """
    <p style="color: #888; font-size: 12px;">
      由 Hermes AI 自动生成 · <a href="%unsubscribe_url%">取消订阅</a>
    </p>
    """
    
    return html

def send_briefing():
    """生成并发送简报"""
    body = generate_daily_briefing()
    subject = f"AI 情报日报 {datetime.now().strftime('%Y-%m-%d')}"
    
    result = send_newsletter(subject, body)
    return result
```

### Cron 配置

```yaml
# ~/hermes-os/cron/jobs.yaml
newsletter_daily:
  schedule: "30 9 * * 1-5"  # 工作日 09:30
  command: "python -m molib newsletter send"
  description: "发送每日 AI 情报简报"
```

## 邮件序列设计

### 欢迎序列（新订阅者自动触发）

| 邮件 | 时间 | 主题 | 内容 |
|------|------|------|------|
| 欢迎 #1 | 订阅后立即 | 「欢迎订阅 AI 情报日报 🎉」 | 介绍服务内容 + 期待管理 |
| 欢迎 #2 | 第 2 天 | 「AI 正在改变这 5 个行业」 | 精选内容展示价值 |
| 欢迎 #3 | 第 4 天 | 「如何用 AI 提升 10 倍效率」 | 实用技巧 + 案例 |
| 转化 #1 | 第 7 天 | 「加入 VIP 获取独家内容」 | 付费订阅转化 |
| 挽回 #1 | 第 14 天（未转化） | 「你的免费试用即将到期」 | 紧迫感 + 优惠 |

### 每日简报模板

```html
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto;">
  <div style="background: #f8f9fa; padding: 20px; text-align: center;">
    <h1>🤖 AI 情报日报</h1>
    <p style="color: #666;">{{DATE}}</p>
  </div>
  
  <div style="padding: 20px;">
    {{CONTENT}}
  </div>
  
  <div style="background: #333; color: #fff; padding: 20px; text-align: center; font-size: 12px;">
    <p>由 Hermes AI 自动生成 · <a href="%unsubscribe_url%" style="color: #aaa;">取消订阅</a></p>
  </div>
</body>
</html>
```

## 订阅→付费转化漏斗

```
曝光（Dcard/Vocus 等）
    │
    ▼
免费订阅（Buttondown）
    │
    ▼
欢迎序列（3 封免费邮件）
    │
    ▼ ┌──────────────────────┐
    ├─→ 转化邮件（第7天）─────→ ✅ 付费用户
    │   └──────────────────────┘
    │
    ├─→ 挽回邮件（第14天）
    │   └──────────────────────┘
    │
    └─→ 流失（保持免费订阅）
```

### 转化策略

| 步骤 | 操作 | 转化率预期 |
|------|------|-----------|
| 免费内容展示价值 | 7 天免费日报 | - |
| 限量优惠 | 「首月 NT$99」 | 5-10% |
| 独家内容 | VIP 每日深度分析 | 3-5% |
| 年度折扣 | 「年付 8 折」 | 2-3% |
| 总转化率 | - | **10-15%** |

## 追踪指标

### 关键指标

| 指标 | 健康值 | 计算公式 |
|------|--------|---------|
| 打开率 (Open Rate) | > 35% | 打开数 / 送达数 × 100% |
| 点击率 (CTR) | > 5% | 点击数 / 打开数 × 100% |
| 转化率 (Conversion) | > 10% | 付费用户 / 总订阅 × 100% |
| 退订率 (Unsubscribe) | < 1%/月 | 退订数 / 总订阅 × 100% |
| 送达率 (Deliverability) | > 97% | 送达数 / 发送数 × 100% |

### Buttondown 统计 API

```python
def get_campaign_stats(email_id: str) -> dict:
    """获取单封邮件的统计数据"""
    resp = requests.get(
        f"{API_BASE}/emails/{email_id}",
        headers=HEADERS
    )
    data = resp.json()
    return {
        "subject": data["subject"],
        "sent": data["total_sent"],
        "opens": data["total_opens"],
        "clicks": data["total_clicks"],
        "open_rate": data["total_opens"] / data["total_sent"] * 100,
        "click_rate": data["total_clicks"] / data["total_opens"] * 100,
    }
```

### 优化建议

- 标题 A/B 测试：不同风格标题影响打开率 20-40%
- 发送时间：工作日上午 9-11 点打开率最高
- 内容长度：300-500 字为最佳阅读长度
- 图片比例：1 张配图每 200 字，提升 CTR 30%
- 个性化：使用 `{{subscriber.first_name}}` 变量

## 前置条件

- Buttondown 账号（免费版）
- BUTTONDOWN_API_TOKEN 环境变量
- 每日情报管线正常运行（墨研竞情）
- HTML 邮件模板

## 注意事项

- 免费版每日仅限 1 封邮件
- 遵守 CAN-SPAM 法案（包含退订链接）
- 退订率 > 1%/月 需优化内容质量
- 不要购买邮件列表（影响送达率）
- 建议先用 3 封免费邮件建立信任后再转化