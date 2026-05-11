---
name: cron-output-formatter
description: Cron 定时作业飞书卡片输出规范 v2.2。所有 cron 输出必须使用飞书原生互动卡片，加粗标题 + 结构化分区 + hr 分割线。包含双重投递抑制机制（Agent 侧最佳实践 + 管道级 sentinel 标记文件兜底）。
version: 2.2.0
tags:
- cron
- feishu
- card
- format
metadata:
  hermes:
    molin_owner: CEO
    cron_safe: true
---

# Cron 定时作业飞书卡片输出规范 v2.0

## 核心原则

1. **卡片优先** — 所有 cron 输出必须使用飞书原生互动卡片。绝对禁止纯文本。
2. **加粗标题** — 每个分区标题和指标名使用 lark_md 加粗 `**标题:**`。
3. **hr 分割线** — 用 `card.add_hr()` 分隔不同板块。
4. **note 脚注** — 用 `card.add_note()` 标注下次执行时间。
5. **颜色语义** — turquoise=正常报告 / orange=需关注 / red=告警 / blue=信息通知。

## 标准代码模板（v2.1 — 强制使用 Enforcer）

> **必须使用 `FeishuOutputEnforcer`，不要直接调 `FeishuCardSender`。** 原因：Enforcer 自动完成验证、路由、降级，绕过它等于跳过所有安全检查。

```python
from molib.infra.gateway import create_enforcer

enforcer = create_enforcer(chat_id="oc_94c87f141e118b68c2da9852bf2f3bda")

# 方式1: 数据简报
result = enforcer.send_briefing(
    title="📊 作业名 · 日期",
    fields={"指标1": "数值", "指标2": "数值"},
    color="turquoise",
    note="墨麟OS · 下次执行: 明天 08:00",
)

# 方式2: 通用消息（自动路由）
result = enforcer.send(
    message="📊 作业名\n指标1: 数值\n指标2: 数值",
    context={"field_count": 2, "is_cron": True},
)

# 方式3: 告警（P1 优先）
result = enforcer.send_alert(
    alert_title="飞轮断裂: 内容工厂",
    what_happened="上游情报银行未产出数据",
    impact="内容工厂无法生成内容，增长引擎也将受影响",
    action_needed="检查 API 余额并手动触发情报银行",
)
```

**为什么要用 Enforcer？**
- 自动检测 thinking 前缀泄漏 → 拦截
- 自动检测 Markdown 残留 → 拦截或修复
- 自动路由到正确卡片格式（T1/T2/T3/T4）
- 长消息自动走 doc import 降级
- 防止裸调 send_card/send_text 绕过规则

## 卡片结构要求

- 每个卡片必须有 header（含 emoji + 作业名 + 日期时间）
- 每个指标标题必须加粗
- 不同主题板块之间用 `card.add_hr()` 分隔
- 结尾用 `card.add_note()` 写下次执行时间
- 没有数据或异常的板块直接省略，不留空

## 颜色规则

| 场景 | 颜色 | emoji |
|------|------|-------|
| 正常运行/数据报告 | turquoise | 📊 |
| 需关注/异常但未中断 | orange | ⚡ |
| 告警/失败/断链 | red | 🚨 |
| 信息通知/巡检 | blue | 📋 |
| 任务成功完成 | green | ✅ |

## ⚠️ 双重投递抑制

Cron 作业有两条独立的发送管道，互不知情：
- 管道①：Hermes cron 调度器将 Agent 的 final response 投递到目标群
- 管道②：Agent 通过 `FeishuCardSender.send_card()` 直接调用飞书 API 发送互动卡片

### Agent 侧最佳实践（尽力，不依赖）

**final response 尽量返回空字符串或单个 emoji。** 如果 final response 包含文本，群内可能出现一张卡片+一条文本的重复输出。Agent 应在 `send_card()` 后将最终回复设为空。

> ⚠️ 此规则仅作为 Agent 行为指引，**不能作为可靠保障**。Agent 可能因模型行为不稳定而未遵守。真正的可靠保障由管道级的 sentinel 标记文件机制提供（见下）。

### 管道级保障：Sentinel 标记文件机制（可靠）

当 `FeishuCardSender.send_card()` 成功发送卡片且处于 cron 会话（`HERMES_CRON_SESSION=1`）时，自动在 `~/.hermes/cron/card_sent/{chat_id}` 写入时间戳标记文件。

Cron 调度器的 `_process_job()` 在投递文本前调用 `_check_card_sentinels()` 检查标记文件。如发现 5 分钟内的标记，跳过文本投递并清理标记。此检查位于投递管道的必经路径，不依赖 Agent 行为。

详见 `references/cron-card-sentinel.md`。

## 禁止项

- 禁止纯文本输出（必须用 CardBuilder + send_card）
- 禁止发送卡片后保留有意义的 final response（最佳实践：尽量空或单 emoji；管道级 sentinel 机制兜底）
- 禁止 ━━━ ASCII 分隔线（用 add_hr() 原生分割线）
- 禁止不加粗的扁平列表（每个键必须用 **键:** 值格式）
- 禁止技术日志、traceback、文件路径（告警卡片只说 3 句话）
- 禁止超过 10 行的卡片（超出的数据写入 relay/ 文件，卡片只发摘要）

## Cron Prompt 安全约束（关键 — 违反即被过滤器拦截）

Cron 任务 Prompt 会被 Hermes 安全过滤器扫描。详见 `references/cron-security-filter.md`。

速查：禁止 curl/auth、禁止 `python -m/路径`、禁止 terminal引用、禁止 API key。Prompt 全部用纯自然语言。

| 禁止模式 | 原因 | 替代方案 |
|---------|------|---------|
| curl 命令 + Authorization header | exfil_curl_auth_header 拦截 | 用自然语言「检查余额」 |
| `python -m molib xxx` 路径 | 命令注入拦截 | 用自然语言「执行财务报告」 |
| `python /path/to/script.py` | 命令注入拦截 | 用自然语言「运行健康检查」 |
| `terminal` 引用 | 敏感词拦截 | 省略，agent 自行判断工具 |
| API key、token 字符串 | 密钥泄露拦截 | 绝不在 prompt 中写密钥 |

**正确做法**：Prompt 全部用纯自然语言描述要做什么，不指定如何做。Agent 会自行选择合适的工具。

## 与其他技能的关系

- `feishu-message-formatter`：交互式对话的飞书格式规范。**不可用于 cron**，因其代码示例会触发安全过滤器。
- `cron-output-formatter`（本技能）：cron 专用的卡片输出规范，无代码示例，cron-safe。
