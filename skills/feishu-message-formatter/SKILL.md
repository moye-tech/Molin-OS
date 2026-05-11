---
name: feishu-message-formatter
description: 飞书消息输出格式化 — 噪声过滤 + 结构化卡片 + 分级透明。Hermes OS 发给用户（尹建业）的所有消息必须经过此规范。
version: 1.0.0
tags:
- feishu
- ux
- message
- format
- noise-filter
- card
related_skills:
- molin-ceo-persona
- molin-governance
- feishu-cli
metadata:
  hermes:
    molin_owner: CEO
    source: Hermes OS × 飞书 UX 整改方案 (2026-05-04)
min_hermes_version: 0.13.0
---

# 飞书消息格式化规范

> 给用户（尹建业）的飞书消息，必须经过噪声过滤 + 结构化输出。

## 核心原则

1. **结果导向** — 只发送「任务完成/失败/需要你决策」三种状态。执行过程（terminal 命令、文件读写、中间步骤）全部静默。
2. **卡片优先** — 结构化输出用分隔线卡片格式（见下方模板）。
3. **分级透明** — L0 自动完成 → 简洁卡片。L2 人工确认 → 含"待你审批"标注。
4. **长短分流** — 短内容（<500字）→ 直接飞书纯文本。长内容或含表格/图表 → 写入 Markdown → `feishu-cli doc import` 导入为飞书文档 → 只发文档链接 + 一句话摘要。
5. **不修改 Hermes 配置** — 此规范只约束终端输出内容格式，不改变 Hermes 的 config.yaml/.env/skills 结构。

## 权威来源

此规范源自 Molin-OS SOUL.md（`~/Molin-OS/SOUL.md` § 飞书消息输出格式，第 213-217 行）。
SOUL.md 是飞书输出规范的单一真相源，本技能是其在 Hermes 中的执行映射。

## 噪声过滤规则

每次生成回复给用户前，自动过滤以下内容：

| 噪声类型 | 处理方式 | 示例 |
|:---------|:---------|:-----|
| terminal 命令原文 | **完全移除** | `terminal: "cd /tmp/..."` |
| 文件读写操作 | **完全移除** | `read_file: "/path/..."` |
| 中间验证步骤 | **完全移除** | `来验证一下仓库当前状态` |
| Hermes 内部元数据 | **完全移除** | `iteration 12/60`, `running: delegate_task` |
| 技术幻影/已编辑标注 | **完全移除** | `(已编辑)` |
| 临时路径 | **完全移除** | `/tmp/`, `~/.cache/` |
| 冗余解释性前言 | **提炼为字段** | 超过2句的铺垫 → 精简 |

## 3 消息有序发送流水线 ⭐ v2.2

> **来源: molin_reply_upgrade_v68.html — 飞书回复体验升级方案**
> 
> 本技能的核心架构已从「单卡片 ASCII 分隔线」升级为「3 消息有序发送」。
> 
> 原理: CEO 响应不再是一张大卡片，而是拆为 3 条独立消息，有序发送。

### 流水线结构

```
消息① 思维链卡片（最先发送，小字折叠）
  ├─ 紫色 header "🧠 CEO 推理过程"
  ├─ 三层分析: L1字面需求 · L2真实目标 · L3隐含约束
  ├─ 调度决策: 哪些子公司 · 几路并发
  └─ 底部 note: ⏱耗时 · ¥成本 · 信心度%

消息② 主回复卡片（核心，结构化 interactive card）
  ├─ header: ✅/⚠️/❌ + 任务状态
  ├─ 执行摘要: 子公司 · 质量评分
  ├─ 核心结果: section × N（每个子公司产出）
  ├─ 风险提示: 高/中风险单独标出
  ├─ 操作按钮: "📋 导出报告" / "💬 继续提问"
  └─ 底部 note: 版本 · SOP ID · N子公司协作

消息③ 子公司详情卡片（按需展开，每个子公司一张）
  ├─ header: 📊 子公司名 · 完整报告
  ├─ 详细产出: section × N
  └─ 底部 note: 质量评分
```

### 代码实现

```python
from molib.infra.gateway.feishu_reply_pipeline import FeishuReplyPipeline

pipeline = FeishuReplyPipeline()
messages = pipeline.build(user_query, ceo_result)
# → [thinking_card, main_card, detail_card_1, detail_card_2, ...]
```

### 与旧模板的关系

旧 ASCII 分隔线模板（`━━━━`）仍可用于 cron 报告和简单信息——它们不涉及 CEO 调度。但所有 CEO 任务响应必须使用新流水线。

## 消息类型模板（旧版 — cron/简单信息仍使用）

### 深度结构化报告（长篇策略/方案输出）

当输出超长策略方案时，使用三层分隔线体系：

```
═══════════════════════════════════════   ← 主章节
🔍  章节标题
═══════════════════════════════════════

━━━━━━━━━━━━━━━━━━━━━━   ← 子章节
S1 · 子章节标题 · ⚡ 优先级
━━━━━━━━━━━━━━━━━━━━━━

  • 要点使用缩进 + 空行分组
  • 每个要点 ≤ 2 行
  • 数字序号用 → 连接子项
```

分隔线规则：
- ════════ 双线 = 顶层章节（诊断/竞品/策略/时间表/指标）
- ━━━━━━ 单线 = 二级子章节（S1-S6 策略线、时间阶段）
- • 缩进 = 三级内容要点
- 章节间留一个空行

实战案例：火花思维 6 线策略第一版被批"文本排版不够结构化"→ 改用三层分隔线体系后通过。

### Cron 报告卡片

## Cron 定时作业输出模板

所有 cron 作业投递到自动化控制群时，必须使用此模板格式。
严禁在 cron 输出中使用 Markdown 表格、粗体、链接或代码块。

实战案例参见 [`references/cron-output-examples.md`](references/cron-output-examples.md) — 含 2026-05-10 闲鱼作业违规→修正的完整对照。

### 📡 标准 cron 报告卡片
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [emoji] [作业名] · [日期 时间]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 本轮结果
• 指标1：数值
• 指标2：数值
• 指标3：数值

⚠️ 需关注（有则填，无则省略整段）
• 事项1 — 简述 + 操作建议
• 事项2 — 简述 + 操作建议

✅ 已就绪/自动完成
• 项目1
• 项目2

🔜 下次执行：[时间]

[如有异常] ❌ [异常简述]，原因：[一句话]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Cron 输出铁律
- 禁止 Markdown 表格（| col | col |）→ 改为 • 列表
- 禁止 **粗体** → 用纯文本，靠位置强调
- 禁止 [文字](链接) → 直接写 URL 或省略链接
- 禁止 # 标题 → 用 emoji + 文字
- 禁止 `代码块` → 直接写纯文本
- 禁止 ┌─┐ 框线表格 → 用卡片格式
- 数值为空时标注「0」或「暂无」，不写「N/A」
- 无异常时省略 ⚠️ 和 ❌ 段落，不留空白
- 总长度控制在 20 行以内

## 文案规范

### ✕ 禁止出现
- 「让我验证一下……」「来检查一下……」
- 「已经推送成功了！来验证一下」
- 「我正在执行 delegate_task……」
- 任何文件路径（`/tmp/`、`~/.hermes/`）
- 任何 shell 命令原文
- 过长的解释性前言（超过2句的铺垫）

### ✓ 正确表达
- 结果优先：直接说做了什么、结果是什么
- 数字具体：「5 处改动」而非「做了一些修改」
- 行动清晰：按钮标注「查看→」「批准」，不用省略号
- 异常直说：「推送失败，原因：网络超时」
- 简报克制：每日简报最多 5 行数据

## 使用时机

任何时候我回复用户消息，在最终输出前自动应用此规范：
1. 先完成实际任务（正常的工具调用）
2. 在组织最终回复时，过滤所有噪声
3. 将结果转换为上述卡片格式
4. 只发送最终卡片，不透传过程

## 验证标准

- ✅ 回复中无 terminal: 或 read_file: 等工具调用痕迹
- ✅ 结构化信息用分隔线卡片包裹
- ✅ L2 事项明确标注"待你审批"
- ✅ 异常场景直接说问题，不绕弯子

## ✅ 网关层已修复（2026-05-10）

**`FeishuAdapter.format_message()` 已挂接 `_strip_markdown_to_plain_text()`**
（`hermes-agent/gateway/platforms/feishu.py:2193`）。

现在网关层会自动剥离所有 Markdown 格式（粗体、斜体、标题、表格、代码块、链接、引用），
Agent 层的遗漏不再直接暴露给飞书用户。表格也会被转换为 `•` 列表格式。

> 诊断历史：[`references/gateway-formatting-pipeline.md`](references/gateway-formatting-pipeline.md)

### 修复内容
| 位置 | 修改 |
|------|------|
| `feishu.py:2193` — `format_message()` | `str.strip()` → `_strip_markdown_to_plain_text()` |
| `feishu.py:527` — `_strip_markdown_to_plain_text()` | 新增表格→列表转换 |
| `~/.hermes/SOUL.md` | 新增飞书格式约束（persona 层） |

### 当前状态
- 网关层：**防线就绪** — 自动剥离所有 Markdown
- Persona 层：**约束明确** — Agent 知道飞书不支持 Markdown
- Agent 层：尽力遵守 persona 约束，网关兜底

> 详见 [`references/gateway-formatting-pipeline.md`](references/gateway-formatting-pipeline.md) — 完整管道诊断、关键代码行号、修复方向。

## 常见违规与纠正

以下是在实际使用中发现的违规模式，**每次违规都是高优先级的学习信号**：

| 违规 | 犯法 | 正确做法 |
|:-----|:-----|:---------|
| `# 标题` / `## 副标题` | 用了 Markdown 标题 | 用 `📊 标题名` + 空行分段 |
| `---` 水平线 | 用了 Markdown 分隔线 | 用 `━━━━━━` 分隔线卡片 |
| `**粗体**` | 用了 Markdown 加粗 | 直接用纯文本，靠位置和 emoji 强调 |
| `| col | col |` | 用了 Markdown 表格 | 改用 • 列表或飞书文档导入 |
| `\\`code\\`` | 用了行内代码 | 直接用引号或纯文本 |
| 带 ASCII 框线的表格（`┌─┐`） | 用了框线字符 | 纯文本缩进或卡片格式 |
| 长篇 Markdown 回复 | 超过 500 字用 Markdown | 写入 Markdown 文件 → `feishu-cli doc import` → 只发链接 |
| 用 doc content-update 导大文档 | 容易超时+格式混乱 | **必须用 `feishu-cli doc import`**（三阶段流水线，支持并发表格） |
| 用 doc add 逐块写入 | 500块需几百次API调用 | 用 `doc import` 一次性导入 |
| 扁平 • 列表输出复杂策略 | CEO批\"太表面\"、\"不够结构化\" | 改用 ═══/━━━/ 三层层级分隔线 + 缩进分层 |
| 过度压缩子任务输出 | 压缩损失细节 → 用户感知浅 | CEO 汇编时只去重+排版，不删减实质内容 |

**自检方法**：把回复内容粘贴到微信输入框，如果看起来奇怪/有格式破损，就是违规。

## SOUL.md 三层需求拆解模型

> 来源: SOUL.md v2.2 更新

每次 CEO 调度前必须完成:

- **L1 字面需求** — 用户说出来了什么？（关键词匹配）→ 命中的子公司必选
- **L2 真实目标** — 用户真正想要什么结果？（推理）→ 命中的子公司必选，最重要
- **L3 隐含约束** — 用户没说但必须满足的边界？（假设检验）→ 按风险等级决定

禁止行为:
- ❌ 因关键词"开发"就调 dev，必须判断是否真需要写代码
- ❌ 只调用 1 个子公司处理复杂任务
- ❌ 遗漏 legal/secure 审查（涉及金钱/发布必选）
- ❌ 调度超过 6 个子公司（并发太多会遗漏重要内容）

## 程序化 API 模块

本规范有对应的代码实现模块（2026-05-10 创建，v2.1 升级到 CardBuilder JSON API）：

### `molib.infra.gateway.feishu_card_builder` — 飞书互动卡片 ⭐ 推荐

```python
from molib.infra.gateway.feishu_card_builder import FeishuCardBuilder, ceo_brief_card, alert_card

card = FeishuCardBuilder()
card.header("标题", template="turquoise")  # 11种颜色
card.section("段落标题", "Lark MD 内容")
card.divider()                              # 原生分割线，替代 ASCII ━━
card.table([{"列1": "值", "列2": "值"}])     # 原生表格
card.columns("列1\n**值1**", "列2\n**值2**") # 多列布局
card.actions([{"text": "确认", "type": "primary", "url": "..."}])  # 交互按钮
card.note("脚注")
json_output = card.build()  # 飞书 Card JSON API 格式
```

6 种预设模板：`ceo_brief()` / `system_alert()` / `content_preview()` / `finance_report()` / `intel_summary()` / `make_text_card()`

**思维链卡片**（v2.2 新增 — CEO 推理过程独立展示）：

```python
card = FeishuCardBuilder()
card.thinking_card(
    user_query="帮我看看闲鱼有哪些可以接的单子",
    understanding={"L1": "闲鱼接单", "L2": "快速变现", "L3": "平台合规"},
    agencies=["research", "shop", "ip", "data", "legal"],
    confidence=0.94,
    duration_s=87,
)
```

思维链卡片使用紫色 `template="purple"` header，底部 note 显示 ⏱耗时 · ¥成本 · 子公司数 · 信心度%。

**ASCII 分隔线（`━━━━`）为旧方案，新代码优先使用 CardBuilder。**

### `molib.infra.feishu_noise_filter` — UX 噪声过滤器

```python
from molib.infra.feishu_noise_filter import filter_message, filter_batch

result = filter_message("打卡")  # {"noise": True, "rule": "R4", "reason": "..."}
stats = filter_batch(messages)   # {"total": N, "noise": M, "rule_breakdown": {...}}
```

8 条正则规则（优先级排序）：R0 空消息 → R6 纯数字日期 → R7 URL only → R1 纯表情符号 → R5 @无内容 → R8 富文本碎片 → R4 超短无意义 → R2 系统消息。全部 13 个内置测试用例通过。

### 语气切换
回复语气应与内容类型匹配：
- 系统操作结果 → 客观陈述，emoji状态标识
- CEO简报 → 结构化卡片，数据优先
- 日常对话 → 自然轻松，但保持格式规范

### 卡片适度使用

卡片格式用于结构化信息（操作结果/简报/审批），
日常对话和简单确认不需要卡片，保持自然。

### FeishuCardRouter — 5 种卡片场景决策树（v2.5）

> 代码实现: `molib/shared/publish/feishu_card_router.py`

发送飞书消息前，按以下决策树自动选择格式：

```
1. 消息目的是什么？
   → 闲聊/简单确认 → T5 纯文字 (≤3行)
   → 通知一件事 → 简单文字 + emoji
   → 汇报任务结果/数据 → 进入第2步
   → 需要审批/决策 → T2 审批卡片 (待审批·orange header)
   → 系统异常/警报 → T4 告警卡片 (🚨 red header)

2. 数据量/结构是？
   → 1-3个数字 → 简洁文字 (不用卡片)
   → 3-8个字段 → T1 数据卡片 (turquoise header)
   → 综合报告 → 富卡片 (多列+图表+按钮)
   → 内容草稿 → T3 内容预览卡片 (📝 blue header)
```

**T1 数据卡片**: `field_count≥3` 或含"简报/报表/统计/数据/产出/日报"关键词 → turquoise header + 数据表格
**T2 审批卡片**: `governance_level∈{L2,L3}` 或含"审批/确认/报价/待决定"关键词 → orange header + 批准/修改/拒绝按钮
**T3 内容预览卡片**: `has_draft=True` 或含"草稿/文案/脚本/大纲"关键词 → blue header + 内容preview + 发布按钮
**T4 告警卡片**: 含"失败/异常/错误/超限"关键词或 `error_type` 存在 → red header + 异常描述 + 影响范围
**T5 纯文字**: 默认 — 80%+ 的日常消息应走这里，禁止滥用卡片

路由代码:
```python
from molib.shared.publish.feishu_card_router import FeishuCardRouter, OutputFormat

fmt = FeishuCardRouter.route(message, {"governance_level": "L0"})
if fmt == OutputFormat.TEXT:
    bot.send_text(msg)  # 80%+ 消息走这里
elif fmt == OutputFormat.CARD_ALERT:
    card = FeishuCardBuilder().header("异常", "red").section(msg)...
```

### 与 feishu-cli 协作
长内容（>500字或含表格/图表）→ 写入 Markdown → `feishu-cli doc import` 导入为飞书文档
短内容 → 本规范的卡片/纯文本格式

详见: [references/feishu-doc-import.md](references/feishu-doc-import.md) — 正确使用 doc import 而非 content-update