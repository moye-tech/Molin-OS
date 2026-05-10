---
name: molin-daily-briefing
description: CEO每日简报技能 — 自动采集系统数据、子公司状态、预算水位，生成结构化日报告用户。
version: 1.0.0
author: Hermes Agent
category: meta
metadata:
  hermes:
    tags: [ceo, briefing, daily, report, molin]
    related_skills: [molin-ceo-persona, molin-goals, molin-governance, molin-relay-protocol]
    molin_owner: CEO
---

# CEO 每日简报

## 概述

每天早上 9:00 执行，为老板生成一份「一口能读完」的日报告。不废话、不罗列无意义数据，只说「今天该知道什么、今天该干什么」。

## 执行顺序

### 第 1 步：采集数据（并行）

用标准 Hermes 工具收集以下数据：

**系统状态：**
- cron 活跃数：`cat ~/.hermes/cron/jobs.json` → 统计 enabled=true 的作业数
- 技能总数：`ls ~/.hermes/skills/**/SKILL.md | wc -l`

**子公司接力数据：**
- 读取接力协议格式的接力消息
  - 墨思情报银行：`cat ~/.molin/relay/intelligence_morning_*.json` 或 `~/.hermes/cron/output/` 中最近一篇 intelligence 相关输出
  - 墨迹内容工厂：`cat ~/.molin/relay/content_*.json` 或最近 content 相关输出
- 如果 relay 文件不存在，从 cron output 目录获取最近的相关输出：`ls -t ~/.hermes/cron/output/*.md | head -5`

**预算水位：**
- 读取 governance.yaml：monthly_cap, categories
- 读取 company.yaml：budget_monthly, revenue_target
- 从 molin-governance skill 获取各部门预算分配

**目标进度：**
- 从 molin-goals skill 读取 Q2 OKR + 本周任务

### 第 2 步：生成简报

格式必须严格如下：

```markdown
## 📋 墨麟日报 | YYYY-MM-DD (周X)

### 今日系统状态
├─ 技能总数: N
├─ 活跃任务: N 个
└─ 系统健康度: ✅ | ⚠️ | ❌

### 今日接力流
┌─ 08:00 [墨思情报] → [摘要20字]
├─ 09:00 [墨迹内容] → [摘要20字]
├─ 10:00 [墨增增长] → [摘要20字]
└─ 今日总接力点数: 3/3

### 预算水位
├─ 运营预算: ¥X / ¥1,360 (X%)
├─ 子公司预算: ¥X / ¥2,440 (X%)
└─ 收入进度: ¥X / ¥48,000 (X%)

### 目标进度（Q2）
├─ O1 闲鱼: KR1 [0/6] KR2 [0/20] KR3 [—]
├─ O2 小红书: KR1 [0/15] KR2 [0/500] KR3 [—]
└─ O3 猪八戒: KR1 [0/10] KR2 [0/2] KR3 [—]

### 本周任务
- [ ] 任务1
- [ ] 任务2
- [ ] 任务3

### 今日推荐动作
1. [优先级最高的1件事]
2. [次优先的1件事]

### 📊 一句话总结
[不超过50字，让老板一眼知道今天要关注什么]
```

### 第 3 步：输出

将简报同时：
1. 输出到终端（标准 stdout）
2. 写入接力协议：`~/.molin/relay/briefing_YYYY-MM-DD.json`（如果 relay 目录存在）

### 注意事项

- 如果某数据源不可用（文件不存在/报错），直接写 `N/A` 并备注原因，不要卡住简报生成
- 简报目标是一分钟读完，不要写超过 30 行的内容
- 推荐动作不超过 2 条，多则无效
