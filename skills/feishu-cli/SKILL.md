---
name: feishu-cli
description: "飞书开放平台 CLI — Markdown 双向转换、文档读写、消息发送、多维表格、日历任务等全功能操控。当用户请求操作飞书文档、发送消息、管理知识库、创建表格、查看日历、搜索文件、管理权限等功能时加载。"
version: 1.0.0
author: Hermes Agent (integrated from riba2534/feishu-cli v1.23.0)
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [feishu, lark, document, messaging, integration]
related_skills: [feishu-message-formatter, molin-ceo-persona]
---

# feishu-cli — 飞书深度集成

feishu-cli 是飞书开放平台的命令行全能工具，通过 Hermes terminal 工具调用。
同时整合 Molin-OS 自带的飞书模块（bitable_sync / drive_manager / official_approval / feishu_send_image）。

**凭证**: 复用 `~/.hermes/.env` 中的 `FEISHU_APP_ID` + `FEISHU_APP_SECRET`。
**凭证提取**: 参考 `references/credential-extraction-pattern.md` 了解如何发现并迁移硬编码密钥。

## ⚠️ 飞书消息输出格式 — 必须遵守

> 来源：Molin-OS SOUL.md § 飞书消息输出格式

飞书消息中**禁止使用**以下 Markdown 格式：

- ❌ `# ## ###` 标题
- ❌ `---` 水平分隔线
- ❌ `**粗体**` / `*斜体*`
- ❌ ASCII 框线（`┌─┐` 之类）
- ❌ Markdown 表格（`| col | col |`）

**只能使用**：

- ✅ 纯文本段落，以空行分隔
- ✅ `•` 无序列表（不是 `-` 或 `*`）
- ✅ 数字列表（`1. 2. 3.`）
- ✅ 表情符号分节（🟢🔴🟡📊📝🔧）
- ✅ 状态指示（✅ ❌ ⏳）

**判断标准**：粘到微信发出去不奇怪，飞书就没问题。

**长短分流**：
- 💬 短内容（<500字）→ 直接飞书消息，遵守上述纯文本规则
- 📄 长内容（>500字或含表格/图表）→ 写入 Markdown → `feishu-cli doc import` 导入为飞书文档 → 发送链接

## 安装与配置

### 安装 feishu-cli 二进制

推荐方法（VPN 环境）：

```bash
curl -fsSL https://raw.githubusercontent.com/riba2534/feishu-cli/main/install.sh | bash
```

### 安装陷阱

- **GitHub 直连极慢**：国内直连 GitHub Releases 下载速度 < 50KB/s，10MB 文件需 5-10 分钟且频繁断连
- **必须开 VPN**：不开 VPN 基本下不动
- **ghproxy/jsdelivr 不可用**：ghproxy SSL 错误，jsdelivr 不代理 GitHub Releases 二进制
- **凭证即插即用**：feishu-cli 读取 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET` 环境变量，与 Hermes `~/.hermes/.env` 共用
- **不需要额外 config init**：有环境变量即可直接用，无需 `feishu-cli config init`

### 大文档导入注意事项

- 飞书 API 有 **429 频率限制**，大文档（含多个表格）导入时表格填充阶段可能触发
- feishu-cli 内置了重试机制（最多 5 次），表格 429 错误会自动恢复
- 批量导入建议用 `--verbose` 观察进度
- 导入完成后应立即授权：`feishu-cli perm add <doc_id> --doc-type docx --member-type email --member-id fengye940708@gmail.com --perm full_access --notification`

### ⚠️ doc import vs content-update（重要）

**永远用 `doc import`，不要用 `doc content-update` 导入大文档。**

```bash
# ✅ 正确：三阶段流水线，图表自动转画板，表格智能填充
feishu-cli doc import /tmp/report.md --document-id <doc_id> --verbose

# ❌ 错误：单线程逐块写入，大文档（>5000字/含表格）必定超时
feishu-cli doc content-update <doc_id> --mode overwrite --markdown-file /tmp/report.md
```

`doc import` 的优势：
- 三阶段流水线：顺序创建块 → 并发填充表格 → 降级容错
- Mermaid/PlantUML 自动转换为飞书画板
- 表格并发填充（3并发），大表格自动拆分
- 429 限流自动重试

`content-update` 的陷阱：
- `--mode overwrite` 需要 `--selection-by-title` 或 `--selection-with-ellipsis`
- `--mode replace_all` 同样需要定位参数
- 逐块写入，无并发，大内容必然超时
- 表格不支持，图表不转换

```bash
feishu-cli <module> <command> [args]
```

### 文档 (doc)

```bash
# 创建空白文档
feishu-cli doc create --title "标题" --output json

# Markdown → 飞书文档（支持 Mermaid/PlantUML 转画板）
feishu-cli doc import file.md --title "标题" --verbose

# 飞书文档 → Markdown
feishu-cli doc export <document_id> -o output.md --download-images

# 读取文档内容
feishu-cli doc read <document_id>

# content-update（7种模式：replace/insert/prepend/append/delete/overwrite/section）
feishu-cli doc content-update <document_id> --mode replace --content "新内容" --selector "旧文本"
```

### 消息 (msg)

```bash
# 发送文本消息
feishu-cli msg send <receive_id> --msg-type text --content "内容"

# 发送富文本
feishu-cli msg send <receive_id> --msg-type post --content '{"zh_cn":...}'

# 发送 Interactive 卡片（先用 feishu-cli-card 构造 JSON）
feishu-cli msg send <receive_id> --msg-type interactive --content card.json

# 回复消息
feishu-cli msg reply <message_id> --content "回复"

# 转发/合并转发
feishu-cli msg forward <message_id> --receive-id <target>
feishu-cli msg merge-forward --message-ids id1,id2 --receive-id <target>
```

### 消息互动 (chat)

```bash
# 查看历史
feishu-cli msg history <chat_id> --page-size 20
feishu-cli msg history --user-email user@example.com  # P2P 私聊

# 搜索群聊
feishu-cli msg search-chats --query "群名"

# 消息详情
feishu-cli msg get <message_id>

# Reaction / Pin
feishu-cli msg reaction <message_id> --emoji "+1"
feishu-cli msg pin <message_id>
```

### 多维表格 (bitable)

```bash
# base 操作
feishu-cli bitable base list
feishu-cli bitable base info <app_token>

# 数据表 CRUD
feishu-cli bitable table list <app_token>
feishu-cli bitable record list <app_token> <table_id>
feishu-cli bitable record create <app_token> <table_id> --fields '{"名称":"值"}'

# 视图
feishu-cli bitable view list <app_token> <table_id>
```

### 电子表格 (sheet)

```bash
feishu-cli sheet read <spreadsheet_token> <sheet_id>
feishu-cli sheet write <spreadsheet_token> <sheet_id> --range "A1:C3" --values '[["a","b"]]'
feishu-cli sheet export <spreadsheet_token> -o output.xlsx
```

### 知识库 (wiki)

```bash
feishu-cli wiki space list
feishu-cli wiki node list <space_id>
feishu-cli wiki node create <space_id> --title "节点名" --parent-id <parent>
```

### 日历 (calendar)

```bash
feishu-cli calendar list
feishu-cli calendar event list <calendar_id>
feishu-cli calendar event create <calendar_id> --summary "会议" --start "2026-01-01T10:00+08:00"
feishu-cli calendar agenda  # 日程视图
```

### 任务 (task)

```bash
feishu-cli task create --summary "任务名" --due-date "2026-01-15"
feishu-cli task list
feishu-cli task complete <task_id>
```

### 权限 (perm)

```bash
feishu-cli perm add <doc_id> --doc-type docx --member-type email --member-id u@e.com --perm full_access
feishu-cli perm list <doc_id> --doc-type docx
```

### 文件/云盘 (drive)

```bash
feishu-cli file list --folder-token <token>
feishu-cli file upload --parent-token <token> --file path/to/file.pdf
```

### 搜索 (search)

```bash
feishu-cli search doc --query "关键词"
feishu-cli search msg --query "关键词"
```

### 其他

```bash
# 妙记 (video conference)
feishu-cli vc list --query "关键词"
feishu-cli vc minutes <meeting_id>

# 审批
feishu-cli approval list --status pending

# 邮箱
feishu-cli mail send --to u@e.com --subject "主题" --body "内容"
```

---

## Molin-OS 原生飞书模块

除了 feishu-cli 二进制，Molin-OS 自带 Python 飞书模块（`molib/feishu_ext/`），可直接在 Hermes 中调用：

### bitable_sync — 任务执行记录同步
- `python -m molib` 内部调用，自动将每次任务执行同步到飞书多维表格
- 需要环境变量：`BITABLE_BASE_TOKEN`、`BITABLE_TABLE_ID`
- 函数：`sync_task_execution(session_id, user_input, agencies, ...)`
- 函数：`build_dashboard_summary_card(dashboard_data)` — 生成飞书交互卡片

### drive_manager — 云空间自动归档
- 按层级 `墨麟AI/子公司/日期/任务ID/` 自动在飞书云空间创建文件夹
- 每个子公司的执行结果保存为独立 Markdown 文档
- 需要：`FEISHU_DRIVE_ROOT_FOLDER`（云空间根目录 token）
- 启用：`FEISHU_DRIVE_ARCHIVE_ENABLED=true`

### official_approval — 飞书官方审批流
- L2 级别操作可推送到飞书官方审批
- `push_official_approval(title, description, task_type, agency_id)`
- 需要：`FEISHU_USE_OFFICIAL_APPROVAL=true`
- 可选：`FEISHU_DEFAULT_APPROVAL_CODE`

### feishu_send_image — 图片直发
- `python3 tools/feishu_send_image.py <图片路径> [说明文字]`
- chat_id 已硬编码当前对话

## 墨麟自动化控制平台

墨麟OS 有一个统一的飞书自动化通知群，所有定时作业结果推送至此：

**自动化控制群 chat_id**: `oc_94c87f141e118b68c2da9852bf2f3bda`

此 chat_id 硬编码在项目中：
- `bots/daily_hot_report.py` → `NOTIFY_CHAT_ID`
- `bots/xianyu_bot.py` → `notify_chat_id`
- `bots/xhs/xhs_qr_login.py` → `NOTIFY_CHAT_ID`
- `bots/xhs/xhs_qr_send.py` → `NOTIFY_CHAT_ID`
- `bots/xhs/xhs_bot.py` → `notify_chat_id`（元瑶小红书）

**Hermes cron 投递格式**：`deliver: "feishu:oc_94c87f141e118b68c2da9852bf2f3bda"`

**CEO 私聊 chat_id**: `oc_16b4568be8c63c198b2cd6c4d3d11b85`（创始人的 DM）

## ⚠️ 文档评论回复陷阱 — 内容被剥离

当用户在飞书文档中**回复评论**时，Hermes 收到的是：

```
[Replying to: "fc-parent-comment-id"]
fc-new-comment-id
```

**评论的实际文字内容被完全剥离**，只转发父评论 ID 和新评论 ID。

这意味着：
- ❌ 用户无法通过「回复文档评论」向 Hermes 传递信息（包括 API Key、指令等）
- ❌ agent 无法用 `feishu_drive_list_comments` 读取评论内容 — 因为没有 `doc_token`
- ✅ 让用户直接在当前对话中发送文字，或发送文档链接（含 doc_token）

**实战案例**：用户将 Firecrawl API Key 作为文档评论回复粘贴，Hermes 收到的是 `fc-2d4f2ef37ece4acd9ddae434f22e9bb2`（只有评论 ID，没有实际 key）。经过多轮追问 doc_token 后才确认字符串本身就是 key。

## 内容输出策略

遵循 SOUL.md 的"聊天还是委托"原则 + 长短分流：

1. 💬 聊天/短回复 → 飞书纯文本格式（遵守 feishu-message-formatter 输出规范）
2. 📄 长文档/报告 → 写入 `/tmp/hermes_reply.md` → `feishu-cli doc import` 导入为飞书文档 → 只发链接
3. 📊 数据密集 → `feishu-cli bitable` 多维表格
4. 🏗️ 架构/流程 → Mermaid 图表（`feishu-cli doc import` 自动转飞书画板，可编辑矢量图）
5. 🔔 L2 审批 → `push_official_approval()` 飞书官方审批流
6. 📁 任务归档 → `archive_execution_results()` 自动云空间归档（`墨麟AI/子公司/日期/任务ID/` 结构）
7. 📈 执行监控 → `sync_task_execution()` 自动同步到多维表格
8. 🤖 自动化通知 → Hermes cron → `feishu:oc_94c87f141e118b68c2da9852bf2f3bda`

### 大文档导入实战

写入 → 导入 → 授权 三步流程：

```bash
# 1. 写 Markdown
write_file path=/tmp/hermes_report.md content="..."

# 2. 导入飞书（Mermaid 图表自动转画板，表格智能处理）
feishu-cli doc import /tmp/hermes_report.md --title "标题" --verbose

# 3. 授权创始人
feishu-cli perm add <doc_id> --doc-type docx --member-type email \
  --member-id fengye940708@gmail.com --perm full_access --notification
```

---

## 飞书文档兼容性速查

生成导入飞书的 Markdown 前遵循：

| # | 规则 |
|---|------|
| 1 | Mermaid flowchart 必须声明方向 (`flowchart TD`/`LR`) |
| 2 | 时序图 `sequenceDiagram` 参与者 ≤ 8 |
| 3 | 状态图必须用 `stateDiagram-v2`（不是 v1） |
| 4 | 表格每块 ≤ 9行 × 9列（超限自动拆分） |
| 5 | PlantUML 用 ` ```plantuml ` 或 ` ```puml ` |
| 6 | Callout 支持 6 种：info/tip/warning/note/success/danger |
| 7 | 图片用本地绝对路径或可访问 URL |
| 8 | 嵌套列表无深度限制 |
| 9 | 图表失败自动降级为代码块 |
| 10 | 中文列宽 14px/字，英文 8px/字 |
