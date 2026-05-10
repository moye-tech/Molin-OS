# Molin-OS 飞书模块集成清单

审计日期：2026-05-10 | 来源：~/Molin-OS/

## 已集成模块

| 模块 | 路径 | 状态 | 依赖 |
|------|------|------|------|
| bitable_sync | molib/feishu_ext/bitable_sync.py | ⏳ 待配置 | BITABLE_BASE_TOKEN, BITABLE_TABLE_ID |
| drive_manager | molib/feishu_ext/drive_manager.py | ⏳ 待配置 | FEISHU_DRIVE_ROOT_FOLDER, FEISHU_DRIVE_ARCHIVE_ENABLED=true |
| official_approval | molib/feishu_ext/official_approval.py | ⏳ 待配置 | FEISHU_USE_OFFICIAL_APPROVAL=true |
| feishu_send_image | tools/feishu_send_image.py | ✅ 立即可用 | chat_id 已硬编码 |
| feishu-cli binary | riba2534/feishu-cli v1.23.0 | ⏳ 安装中 | 需 Go 或预编译二进制 |

## 飞书输出格式规范

来源：Molin-OS SOUL.md § 飞书消息输出格式

🚫 禁止：
- `# ## ###` 标题
- `---` 分隔线
- `**粗体**` `*斜体*`
- ASCII 框线字符
- Markdown 表格

✅ 允许：
- 纯文本段落
- `•` 无序列表
- `1. 2. 3.` 数字列表
- 表情符号分节和状态标识

## 环境变量需求

已在 `~/.hermes/.env` 中：
- FEISHU_APP_ID ✅
- FEISHU_APP_SECRET ✅
- FEISHU_ENCRYPT_KEY ✅
- FEISHU_VERIFICATION_TOKEN ✅

需要添加：
- BITABLE_BASE_TOKEN — 飞书多维表格 base token
- BITABLE_TABLE_ID — 飞书多维表格 table ID
- FEISHU_DRIVE_ROOT_FOLDER — 云空间根目录 folder token
- FEISHU_DRIVE_ARCHIVE_ENABLED=true — 启用自动归档
- FEISHU_USE_OFFICIAL_APPROVAL=true — 启用审批流
