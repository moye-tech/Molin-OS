---
name: feishu-message-formatter
description: 飞书消息输出格式化 — 噪声过滤 + 结构化卡片 + 分级透明。Hermes OS 发给用户（尹建业）的所有消息必须经过此规范。
version: 2.0.0
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

## ⚠️ Cron 兼容性警告

**本技能不适合 cron 定时任务。** 其 SKILL.md 中的代码示例（FeishuCardBuilder、FeishuCardSender、
API 调用）包含 `Authorization: Bearer` 等模式，当 cron scheduler 加载本技能时会触发
Hermes 的 `exfil_curl_auth_header` 安全过滤器，导致任务被拒绝。

**Cron 任务应使用 [`cron-output-formatter`](cron-output-formatter/SKILL.md)**
— 纯规则无代码示例的 cron-safe 版本。
```
# 正确做法：cron 任务的 skills 列表
skills: ["molin-governance", "cron-output-formatter"]    ✅

# 错误做法：在 cron 任务中加载含代码示例的技能
skills: ["molin-governance", "feishu-message-formatter"] ❌ → Blocked: exfil_curl_auth_header
```

本技能仅用于交互式对话输出格式约束。

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

> 实战案例参见 [`references/cron-output-examples.md`](references/cron-output-examples.md) — 含 2026-05-10 闲鱼作业违规→修正的完整对照。

> 完整19任务审计参见 [`references/cron-system-audit-2026-05-11.md`](references/cron-system-audit-2026-05-11.md) — 含飞轮三级接力链、HTTP 402 fallback修复方案、六大待修问题。

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

### ⚠️ 不可用于 Cron 定时任务

本技能包含大量代码示例（curl、API key、Python 代码），当被 cron job 作为 skill 加载时，这些示例中的 `Authorization: Bearer` 等模式会触发 Hermes 安全过滤器（`exfil_curl_auth_header`），导致 cron job 被拦截。

**Cron 定时任务请使用 `cron-output-formatter` 技能替代**，该技能是纯规则版本，不含任何代码示例，cron-safe。

## ⚡ 强制发送管线（v3.2 新增 — 终极执法）

> 所有飞书发送操作**必须**通过 `FeishuOutputEnforcer`，不直接调用 `FeishuCardSender`。

```python
# ✅ 正确 — 通过 Enforcer 发送（自动验证+路由+降级）
from molib.infra.gateway import create_enforcer
enforcer = create_enforcer(chat_id="oc_xxx")
enforcer.send("今日简报: 3 篇新内容", context={"field_count": 3})

# ❌ 错误 — 裸调 sender（跳过所有安全检查）
from molib.ceo.cards.sender import FeishuCardSender
sender = FeishuCardSender()
sender.send_text(chat_id, message)  # 绕过了 Router！
```

**Enforcer 自动做的 5 件事:**
1. ✅ Pre-send 验证: 检测 thinking 前缀/Markdown残留/噪声/长度
2. ✅ CardRouter 路由: 检测关键词 → 自动选 T0/T1/T2/T3/T4 格式
3. ✅ 长消息降级: >1500字 → 自动 `feishu-cli doc import`
4. ✅ 卡片构建: 自动调用 CardBuilder 生成原生飞书卡片
5. ✅ 违规拦截: ERROR 级别违规 → 拒绝发送，返回 violation 列表

**使用场景:**
- Cron 作业: `enforcer.send_briefing(title, fields)` → T1 数据简报卡片
- 系统告警: `enforcer.send_alert(title, what, impact, action)` → T4 告警卡片
- 内容预览: `enforcer.send(message, context={"has_draft": True})` → T3 内容预览
- 审批请求: `enforcer.send(message, context={"governance_level": "L2"})` → T2 审批

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
| `💭 Reasoning:` 前缀泄漏 | 模型 thinking text 进入回复 | 网关/Agent 层必须先 regex 截断再发送 |
| 裸 Markdown 表格给网关兜底 | 依赖网关 `_strip_markdown_to_plain_text()` → 产出 `• # •` 乱码 | **必须主动调 FeishuCardRouter.render() 或用 CardBuilder.table()** — 网关兜底是救火，不是美化 |
| 回复无卡片/分隔线层级 | 标题和正文全是同等纯文字 | 用 ━━━━ 分隔线或 CardBuilder section 建立视觉层次 |
| 超长消息不降级 | 超过飞书长度上限 → 截断 | 预检消息长度 >1500字 → 自动走 `feishu-cli doc import` |

**自检方法**：把回复内容粘贴到微信输入框，如果看起来奇怪/有格式破损，就是违规。

## v3.1 三合一升级的 5 个遗漏 · 2026-05-11 实战发现 → 2026-05-11 全部闭环 ✅

> 来源: 墨烨审查三合一升级后的首次回复，发现输出比升级前更差。
> 详细分析: [`references/triple-upgrade-gaps.md`](references/triple-upgrade-gaps.md)

三合一升级（CardRouter + FlywheelGuard + DARE模型）的代码实现正确，输出管线 5 个断层**已全部修复**：

**✅ 遗漏① — 模型思考泄漏（P0）** → 已修复
- `FeishuPreSendValidator.strip_thinking_prefix()` — 5 种 thinking 前缀正则截断
- 模式: `💭 Reasoning:` / `💭 推理过程:` / `<thinking>` / `thinking\n\n` / `<reasoning>`
- 集成点: `FeishuReplyPipeline._validate_all()` 自动调用
- 文件: `molib/infra/gateway/feishu_pre_send_validator.py`
  + `molib/infra/gateway/feishu_reply_pipeline.py`

**✅ 遗漏② — 网关兜底优化（P1）** → 已修复
- `FeishuPreSendValidator.detect_and_convert_table()` — Markdown表格→CardBuilder自动转换
- `CardBuilder.add_table()` — 新增方法，`[{col: val}]` → 飞书原生结构化表格
- 文件: `molib/infra/gateway/feishu_pre_send_validator.py`
  + `molib/ceo/cards/builder.py`

**✅ 遗漏③ — CardRouter 强制执行（P2）** → 已修复
- SOUL.md 增加「发送前自检管线」强制铁律
- `FeishuReplyPipeline._validate_all()` — 响应管线中间件
- 铁律: 任何含 `| 表头 |` 的 Markdown 表格禁止依赖网关兜底
- 文件: `Molin-OS/SOUL.md` § 发送前自检管线

**✅ 遗漏④ — pre-send 自检机制（P3）** → 已修复
- `FeishuPreSendValidator.validate()` — 全覆盖程序化自检（320行）
- 三道关卡: ① thinking 前缀截断 → ② Markdown 残留检测+自动修复 → ③ 长消息降级
- 文件: `molib/infra/gateway/feishu_pre_send_validator.py`

**✅ 遗漏⑤ — 长消息自动降级（P4）** → 已修复
- `FeishuPreSendValidator.check_length()` — >1500字自动→写入MD→`feishu-cli doc import`→只发链接
- `FeishuReplyPipeline._validate_all()` 集成调用

## 定时任务 Prompt 安全约束

> 实战发现: 2026-05-11 — cron prompt 中嵌入 `curl -H "Authorization: Bearer $KEY"` 会触发
> Hermes 的 `exfil_curl_auth_header` 安全过滤器，导致 prompt 更新被拒绝。

**Cron prompt 编写铁律:**
- ❌ 禁止在 prompt 中嵌入 curl + Authorization header 命令
- ❌ 禁止在 prompt 中引用环境变量 `$DEEPSEEK_API_KEY` 或 `$OPENAI_API_KEY`
- ✅ 使用自然语言描述：「用 terminal 检查 DeepSeek 余额是否 ≥ ¥50」
- ✅ 余额检查、API 调用等工作交给 Agent 的 terminal 工具自行完成

## HTTP 402 调试模式

> 实战发现: 2026-05-11 — 5个 cron 任务同时报 `HTTP 402: Insufficient Balance`，
> 但余额 API 返回 ¥77.40（充足），直接 API 调用返回 HTTP 200。
> 根因: DeepSeek `v4-pro` 模型的计费系统在 07:00-09:15 CST 出现临时故障，
> 10:00 后自愈。解决: config.yaml 添加 `fallback_model: deepseek-v4-flash`。

**402 排查清单:**
1. 先调 `https://api.deepseek.com/user/balance` 确认真实余额
2. 用同 provider 的 flash 模型测试（`deepseek-v4-flash`）
3. 确认是否只在特定时间窗口出现（可能是 provider 临时故障）
4. 配置 `fallback_model` 做自动降级，避免飞轮断裂
5. 不要看到 402 就假设账户欠费 — 先验证余额

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

### FeishuCardRouter — 5 种卡片场景决策树（v3.0 · 2026-05-11 升级）

> 代码实现: `~/Molin-OS/molib/shared/publish/feishu_card_router.py`
> 详细规范: `~/Molin-OS/molib-os-triple-upgrade.html` → Part ①

发送飞书消息前调用 `FeishuCardRouter.route()` 自动选择格式。**路由优先级（从高到低）：告警 > 审批 > 内容预览 > 数据报表 > 纯文字。**

```
P1 — 告警优先（最高优先级）
   触发: is_error=True 或 含「失败/错误/异常/超限/402/断连/预警」
   → T4 告警卡片 · red header · 3句话原则（发生什么/影响什么/做什么）
   
P2 — 治理审批
   触发: governance_level∈{L2,L3} 或 含「审批/确认发布/报价/待审」
   → T2 审批卡片 · orange header · 批准/修改/拒绝

P3 — 内容草稿预览
   触发: has_draft=True 或 含「草稿/文案/脚本/大纲/内容已生成/已就绪」
   → T3 内容预览卡片 · blue header · 200字折叠

P4 — 数据简报
   触发: field_count≥3 或 含「简报/报表/统计/日报/周报/竞品监控」
   → T1 数据卡片 · turquoise header · 数据表格

P5 — 默认纯文字
   T0 — 80%+ 的日常消息应走这里，≤3行纯文字 + emoji
```

**关键变更（v2.5→v3.0）**:
- T5 重命名为 T0（纯文字是默认，不是"第5选择"）
- 告警优先级从 P2 提升到 P1（系统错误必须最优先通知）
- 新增 `is_error` context key（比关键词匹配更直接）
- 新增 `render()` 一站式方法：路由 + 构建飞书 card payload
- 关键词集合精简：_ALERT 增加「402」「断连」；_CONTENT 增加「已就绪」；_DATA 增加「竞品监控」

路由代码（含 render）:
```python
from molib.shared.publish.feishu_card_router import FeishuCardRouter, Fmt

# 仅路由
fmt = FeishuCardRouter.route(message, {"governance_level": "L0"})
if fmt == Fmt.TEXT:
    bot.send_text(msg)  # 80%+ 消息走这里

# 一站式路由+构建card payload
payload = FeishuCardRouter.render(
    message="API 402 错误：余额不足",
    data={"alert_title": "飞轮断裂: 内容工厂"},
    ctx={"is_error": True}
)
# → 返回 T4 告警卡片的飞书 JSON payload
```

### 与 feishu-cli 协作
长内容（>500字或含表格/图表）→ 写入 Markdown → `feishu-cli doc import` 导入为飞书文档
短内容 → 本规范的卡片/纯文本格式

详见: [references/feishu-doc-import.md](references/feishu-doc-import.md) — 正确使用 doc import 而非 content-update