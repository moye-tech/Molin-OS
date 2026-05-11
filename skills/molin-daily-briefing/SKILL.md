---
name: molin-daily-briefing
description: CEO每日简报技能 — 自动采集系统数据、子公司状态、预算水位，生成结构化日报告用户。
version: 1.1.0
author: Hermes Agent
category: meta
metadata:
  hermes:
    tags:
    - ceo
    - briefing
    - daily
    - report
    - molin
    related_skills:
    - molin-ceo-persona
    - molin-goals
    - molin-governance
    - molin-relay-protocol
    molin_owner: CEO
min_hermes_version: 0.13.0
---

# CEO 每日简报

## 概述

每天早上 9:00 执行，为老板生成一份「一口能读完」的日报告。不废话、不罗列无意义数据，只说「今天该知道什么、今天该干什么」。

## 执行顺序

### 第 1 步：采集数据（并行）

用标准 Hermes 工具收集以下数据：

**系统状态：**
- cron 活跃数：读取 `~/.hermes/cron/jobs.json`（结构 `{"jobs": [{"name": ..., "enabled": true/false, ...}]}`），统计 `enabled=true` 的作业数
- 技能总数：`find ~/.hermes/skills -name "SKILL.md" | wc -l`（注意：v5.0 有 300+ 技能，`ls **` glob 在非 bash 环境可能失败，用 find 更可靠）

**子公司接力数据：**
- 主位置（优先）：`~/Molin-OS/relay/` — 包含 `growth_flywheel_YYYY-MM-DD.json`、`intelligence_morning_YYYY-MM-DD.json`、`content_flywheel_YYYY-MM-DD.json` 等
- 备选位置：`~/.molin/relay/`（尚未创建，未来目标路径）
- 回退方案：从 cron output 目录获取最近的相关输出：`ls ~/.hermes/cron/output/<job_id>/2026-05-11_*.md`
  - 注意：cron 输出在子目录中（每个 job_id 一个目录），不是直接在 `output/` 下

**子公司活跃度（新增）：**
- 统计各 cron job 目录下当日执行次数来判断子公司活跃度
- 路径：`ls ~/.hermes/cron/output/<job_id>/2026-05-11_* | wc -l`
- 常见 job_id 映射见 `references/cron-job-mapping.md`

- 墨维运维有4个job（同步、备份、增量、快照），墨思研究有2个job（情报、竞品），统计时需合并
- 目前 relay 数据中仅墨增增长引擎写入当天新数据，墨思情报和墨迹内容的 relay 可能滞后（仅到旧日期），回落读取 cron output 子目录

**预算水位（v5.0 更新）：**
- governance.yaml `monthly_cap`：¥1,360（AI API + 工具 + 推广的实际花销）
- company 结构预算：¥3,210/月（L0 ¥500 + L1 ¥2,500 + L2 ¥210）
- 收入目标：¥39,000/月（v5.0 调整，原 v4.x 为 ¥48,000）
- ⚠️ governance.yaml 仍引用旧值 ¥3,490/¥52,000，以 molin-company-structure v5.0 为准

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
├─ 子公司预算: ¥X / ¥3,210 (X%)
└─ 收入进度: ¥X / ¥39,000 (X%)

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

**交互模式（用户在对话中）：**
1. 输出到终端（标准 stdout）
2. 写入接力协议：`~/Molin-OS/relay/briefing_daily.md`

**Cron 模式（定时自动执行）：**
- 使用 `CardBuilder` + `FeishuCardSender` 构建飞书互动卡片（遵循 `cron-output-formatter` 技能）
- 卡片颜色：turquoise · 分区：系统版本 → 活跃子公司 → 今日事件
- chat_id：`oc_94c87f141e118b68c2da9852bf2f3bda`（墨麟自动化控制群）
- 所有标题使用 `add_field` / `add_div` 的 `**加粗**` 格式
- 分区之间用 `add_hr()` 分隔
- 结尾用 `add_note()` 标注下次执行时间
- ⚠️ cron 模式下不要直接输出 markdown，不要调用 `send_message`，系统会自动投递响应

### 注意事项

- 如果某数据源不可用（文件不存在/报错），直接写 `N/A` 并备注原因，不要卡住简报生成
- 简报目标是一分钟读完，不要写超过 30 行的内容
- 推荐动作不超过 2 条，多则无效