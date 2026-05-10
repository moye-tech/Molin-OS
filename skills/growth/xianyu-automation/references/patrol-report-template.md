# Xianyu Cron Patrol Report Template

> Referenced by: xianyu-automation §7 Cron Patrol Report
> Format compliance: feishu-message-formatter cron 模板规范

## Template

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🐟 闲鱼状态巡检 · M月D日 HH:MM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 本轮结果
• 新消息：N 条
• 自动回复：N 条
• 成交信号：N 条
• 待审批：N 条

⚠️ 需关注
• 阻塞项简述 — 操作建议（谁处理）

✅ 已就绪/正常运行
• 状态项
• 状态项

🔜 下次巡检：时间

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Compliance Rules (Iron Law)

These are checked by automated validation. Any violation causes the message to be rejected.

| Rule | Wrong | Right |
|------|-------|-------|
| No Markdown headings | `# 标题` / `## 副标题` | `🐟 闲鱼状态巡检 · ...` |
| No horizontal rules | `---` | `━━━━━━━━━━...` |
| No bold | `**text**` | plain text, position / emoji for emphasis |
| No tables | `\| col \| col \|` | `• 字段：值` bullet list |
| No inline code | `` `code` `` | plain text or quotes |
| No links | `[text](url)` | full URL or omit |
| No box-drawing tables | `┌─┐` characters | card format |
| Empty = "0" or "暂无" | `N/A` | `0 条` or `暂无` |
| Omit empty sections | empty ⚠️ block | delete entire ⚠️ block + its content |
| Max 20 lines | overflow | condense |

## Section Rules

### 📊 本轮结果 (always present)
- Always show 4 metrics even when all zero
- New messages: count of messages received this cycle
- Auto replies: count of L0 auto-replies sent
- Deal signals: count of purchase_intent signals detected
- Pending approval: count of L2 escalations needing founder review

### ⚠️ 需关注 (conditional — only when issues exist)
- Each item: short problem description + required action + who handles it
- Format: `• 问题简述 — 操作建议（处理人）`
- Delete entire section when empty

### ✅ 已就绪/正常运行 (always present)
- List everything confirmed working in this cycle
- Include infrastructure status items (venv, dependencies, JS runtime, project imports)
- Include config items (auto_reply toggle, governance rules loaded)
- Think of this as the "good news" section — build confidence

### 🔜 下次巡检 (always present)
- Human-readable: `今天 17:15` or `明天 09:15`
- Calculated from cron schedule: every 30 min, 09:00-21:00

## Real Example: Blocked State (2026-05-10 16:45)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🐟 闲鱼状态巡检 · 5月10日 16:45
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 本轮结果
• 新消息：0 条
• 自动回复：0 条
• 成交信号：0 条
• 待审批：0 条

⚠️ 需关注
• 闲鱼 Cookies 缺失 — 扫码登录 goofish.com 后导出 cookies 到 ~/.xianyu_cookies_new.txt，API 即可连通
• 仅剩此 1 项阻塞（上次 2 项：Python 3.12 + 依赖已全部就绪）

✅ 已就绪/正常运行
• Python 3.12 venv 运行正常（~/xianyu_agent/.venv/）
• 全部依赖安装完毕（goofish_apis / goofish_live 导入成功）
• Node.js v24.14.0 JS 运行时可用
• 项目符号链接就位（~/xianyu_agent → Molin-OS/molib/xianyu）
• 自动化配置就位（auto_reply=true, L0/L2 分级规则已加载）

🔜 下次巡检：今天 17:15

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
