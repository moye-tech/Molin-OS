---
name: molin-relay-protocol
description: 子公司间接力协议 — 定义标准化的数据接力格式，让 Hermes 知道每个接力点在什么时候读什么、写什么。
version: 1.1.0
author: Hermes Agent
category: meta
metadata:
  hermes:
    tags:
    - relay
    - protocol
    - pipeline
    - handoff
    - molin
    related_skills:
    - molin-daily-briefing
    - molin-ceo-persona
    molin_owner: CEO
min_hermes_version: 0.13.0
---

# 子公司接力协议

## 概述

Hermes OS 的 19 个 cron 作业中有 3-5 个核心飞轮作业通过接力格式传递数据。没有标准格式时，Hermes 只能猜「墨思接力数据」在哪。

本协议定义了所有接力点的**存储位置、数据格式、读取方式**。

## 接力存储

接力数据有两个可能的存储位置（按优先级）：

**主位置（当前活跃）：`~/Molin-OS/relay/`**

```
~/Molin-OS/relay/
├── intelligence_morning_YYYY-MM-DD.json   # 墨思情报银行 (08:00)
├── content_flywheel_YYYY-MM-DD.json       # 墨迹内容工厂 (09:00)
├── growth_flywheel_YYYY-MM-DD.json        # 墨增增长引擎 (10:00)
├── distribution_plan_YYYY-MM-DD.json      # 墨测数据分发 (09:30)
├── briefing_daily.md                      # CEO 每日简报
└── _archive_YYYYMMDD_HHMMSS/              # 归档目录
```

**备选位置（协议目标）：`~/.molin/relay/`** — 尚未创建，为协议定义的未来目标路径。

**回落逻辑**：先读 `~/Molin-OS/relay/`，若不存在则读 `~/.molin/relay/`，均不存在则从 `~/.hermes/cron/output/` 各 job 子目录中找当日相关 `.md` 文件（注意：cron 输出在 `<job_id>/` 子目录中，不是直接在 `output/` 下）。

## 通用数据结构

每个接力文件是 JSON，格式：

```json
{
  "origin": "墨思 | 墨迹 | 墨增 | CEO | 墨盾",
  "timestamp": "YYYY-MM-DDTHH:mm:ss+08:00",
  "summary": "一句话总结（20字以内）",
  "detail": "详细描述（支持 markdown 格式）",
  "data": {
    "key_metrics": { ... },
    "decisions_made": ["...", "..."],
    "next_actions": ["...", "..."]
  },
  "downstream_skills": ["skill-name-1", "skill-name-2"],
  "errors": []
}
```

## 各接力点详细规范

### 1. 墨思情报接力 (08:00)

```
文件: intelligence_morning_YYYY-MM-DD.json
写入方: 墨思情报 cron job
读取方: 墨迹内容工厂 (09:00), CEO简报 (09:00)
```

```json
{
  "origin": "墨思",
  "timestamp": "...",
  "summary": "今日趋势: AI coding 热度+12%",
  "detail": "详见情报明细...",
  "data": {
    "hot_topics": ["AI coding tools", "...
3D generation"],
    "trending_projects": [{"name": "...", "stars": 15000}],
    "keyword_suggestions": ["AI 办公", "编程助手"]
  },
  "downstream_skills": ["content-strategy", "claude-seo"],
  "errors": []
}
```

### 2. 墨迹内容接力 (09:00)

```
文件: content_flywheel_YYYY-MM-DD.json
写入方: 墨迹内容工厂 cron job
读取方: 墨增增长引擎 (10:00), CEO简报 (09:00)
```

```json
{
  "origin": "墨迹",
  "timestamp": "...",
  "summary": "完成3篇小红书+1篇知乎",
  "detail": "...",
  "data": {
    "pieces_created": 4,
    "platforms": ["小红书", "知乎"],
    "content_titles": ["...", "..."],
    "scheduled_posts": [{"platform": "小红书", "time": "14:00"}]
  },
  "downstream_skills": ["social-push-publisher", "analytics-tracking"],
  "errors": []
}
```

### 3. 墨增增长接力 (10:00)

```
文件: growth_flywheel_YYYY-MM-DD.json
写入方: 墨增增长引擎 cron job
读取方: CEO简报 (09:00 — 注意这是 T+1 接力)
```

```json
{
  "origin": "墨增",
  "timestamp": "...",
  "summary": "SEO关键词优化+闲鱼商品更新",
  "detail": "...",
  "data": {
    "seo_optimizations": [{"keyword": "...", "action": "update title"}],
    "xianyu_updates": [{"item": "...", "status": "updated"}],
    "ab_test_results": null,
    "recommendations": ["关注 XX 关键词"]
  },
  "downstream_skills": ["analytics-tracking", "page-cro"],
  "errors": []
}
```

### 4. CEO简报接力 (09:00)

```
文件: briefing_YYYY-MM-DD.json
写入方: CEO简报 cron job
读取方: 无下游（写给用户看的）
```

CEO简报直接输出给人看，接力文件仅用于审计和重复运行检测。

## 读取接力数据的标准操作

在 cron job 中需要获取上游接力数据时，按以下优先级查找：

```python
import os, json, glob
from datetime import date

today = date.today().isoformat()
relay_dir = os.path.expanduser("~/Molin-OS/relay")  # 主位置
fallback_relay_dir = os.path.expanduser("~/.molin/relay")  # 备选
fallback_cron_dir = os.path.expanduser("~/.hermes/cron/output")

def get_relay(prefix, date_str=None):
    """获取指定前缀的接力数据"""
    date_str = date_str or today
    # 1. 优先主位置
    path = os.path.join(relay_dir, f"{prefix}_{date_str}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    # 2. 备选位置
    path = os.path.join(fallback_relay_dir, f"{prefix}_{date_str}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    # 3. Fallback: 从 cron output 子目录中找当日的相关文件
    pattern = os.path.join(fallback_cron_dir, "*", f"{date_str}_*.md")
    outputs = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    return {"fallback": True, "files": outputs[:5]}
```

## 初始化（首次使用）

**CRITICAL: relay 目录必须手动创建。** 当前系统（2026-05-11）`~/.molin/relay/` 目录不存在，接力协议仅定义但未部署。

```bash
# 创建接力目录
mkdir -p ~/.molin/relay

# 验证
ls -la ~/.molin/relay/
```

三个活跃 cron 作业（备份、闲鱼、同步）目前独立运行，未通过 relay 共享数据。初始化 relay 目录后，需要更新 cron 作业配置使其写入接力文件。

### 首次初始化后需要的 cron 更新

1. 墨思情报 cron (08:00) → 写入 `intelligence_morning_YYYY-MM-DD.json`
2. 墨迹内容 cron (09:00) → 读取墨思 + 写入 `content_flywheel_YYYY-MM-DD.json`
3. 墨增增长 cron (10:00) → 读取墨迹 + 写入 `growth_flywheel_YYYY-MM-DD.json`
4. CEO简报 cron (09:00) → 读取墨思 + 墨迹 → 写入 `briefing_YYYY-MM-DD.json`

## 接力失败处理

如果上游接力数据不存在（文件未找到），cron job 应该：
1. 记录到 errors: `"upstream_relay_not_found"`
2. 从其他可用数据源获取替代信息（如技能树、memory）
3. 继续执行，不要因缺失接力数据而停止
4. 如果 relay 文件不存在，回落读取 `~/.hermes/cron/output/<job_id>/` 子目录中当日的 `.md` 文件
5. 常见 relay 数据状态（2026-05）：墨增增长引擎已正常写入 `growth_flywheel_YYYY-MM-DD.json`；墨思情报和墨迹内容的 relay 可能滞后，需从 cron output 子目录获取代替数据