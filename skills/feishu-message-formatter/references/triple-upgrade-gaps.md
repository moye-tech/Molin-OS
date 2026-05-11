# 三合一升级的 5 个输出管线遗漏

日期: 2026-05-11
触发: 墨烨审查三合一升级后首次回复，发现输出质量比升级前更差
根因: 代码实现（CardRouter/FlywheelGuard/DAREReasoner）全部正确，但输出管线有 5 个关键断层未被升级方案覆盖

## 事件还原

墨烨收到的回复：

```
💭 Reasoning:
All 6 tasks are complete. Let me provide a comprehensive summary of everything that was done.
✅ 三合一升级方案 · 全部落地完成
变更总览
• # • 模块 • 文件 • 变更
• ① • CardRouter • molib/shared/publish/feishucardrouter.py • 重写 — 告警优先路由 + render() 一站式构建
• ② • Flywheel Guard • molib/shared/flywheelguard.py • 新建 — 上游依赖检查 + 断链T4告警 + 健康检查
• ③ • SOUL.md • SOUL.md • DARE 模型替代旧决策树 + 能力画像 + CEO不做事
• ④ • Cron 调度 • 19 个任务 • 错峰 (08:00→09:20→10:45) + 工作日感知 + 降频 (12→3次)
• ⑤ • Cron Prompt • 6 个关键任务 • 余额前置检查 + 飞轮依赖检查 + T4告
```

三类症状：
1. `💭 Reasoning:` 模型思考文本泄漏
2. `• # • 模块 • 文件 • 变更` — Markdown 表格→网关兜底转换后产出乱码
3. 标题「变更总览」与正文无视觉层次区分
4. 消息在「T4告」处截断

## 遗漏 ① — 思考模式泄漏（P0 最高优先）

- 症状: `💭 Reasoning:` 裸显在用户消息最开头
- 来源: deepseek-v4-pro 模型的 thinking mode 文本未与最终回复分离
- 方案覆盖: ❌ 完全没有 — 方案修了网关 Markdown 剥离，但没修 thinking 前缀
- 修复:
  - 网关 `format_message()` 前增加 regex 匹配
  - 模式: `^💭\s*Reasoning:.*?\n\n` 和 ` thinking\n\n`
  - 匹配到 → 截断，只保留后面的真实回复

## 遗漏 ② — 网关兜底是丑化不是美化（P1）

- 症状: Markdown 表格 `| # | 模块 | 文件 | 变更 |` 被网关转成 `• # • 模块 • 文件 • 变更`
- 机制: `_strip_markdown_to_plain_text()` → 表格检测 → 每行转 `•` 列表
- 问题: `#` 在纯文本里被误解为标题标记，视觉混乱
- 方案覆盖: 部分 — 方案说「网关兜底」，但没考虑兜底产出的可读性
- 根因: Agent 主动写了 Markdown 表格让网关兜底，而非用 FeishuCardBuilder.table()
- 修复:
  - 网关: 检测到表格 → 调用 FeishuCardBuilder.table() 生成原生飞书表格卡片（而非 `•` 列表）
  - Agent: persona 增加铁律「需要多列对比时，禁止写 Markdown 表格，必须调 CardRouter.render()」

## 遗漏 ③ — FeishuCardRouter 未被强制执行（P2）

- 症状: Agent 绕过 Router，直接裸写 Markdown 发给网关
- 代码现状: 路由代码正确（`feishu_card_router.py` 317行，含 `route()`/`render()`/`format_message()`）
- 集成现状: Router 是 opt-in 库 — Agent 可以调也可以不调
- 方案覆盖: 方案设计了 Router API 但没有设计「响应管线中间件」
- 修复:
  - Persona: 「回复含表格/多列/变更列表 → 必须调 FeishuCardRouter.render()」
  - 未来: 实现响应管线中间件，所有飞书消息强制经过 route()

## 遗漏 ④ — pre-send 自检缺失（P3）

- 症状: 有明显违规的消息直接发送，没有程序化拦截
- 方案覆盖: 只提到了人工自检「粘贴到微信输入框」，无程序化验证
- 修复方向:
  - 长度检测: 消息 > 1500 字 → 自动降级
  - thinking 前缀检测: regex 匹配到 → 截断
  - Markdown 残留检测: 含 `|`, `**`, `# `, `\`\`\`` → 警告或自动转换

## 遗漏 ⑤ — 长消息截断无降级（P4）

- 症状: 消息在「T4告」处截断
- 触发: 变更总览 6 项 + 正文超过飞书纯文本长度限制
- 方案覆盖: 方案有 `feishu-cli doc import` 能力，但没有自动长度检测触发
- 修复:
  - 发送前检查 `len(message) > 1500`
  - 超长 → 写入 Markdown → `feishu-cli doc import` → 只发文档链接 + 一句话摘要

## 根因总结

三合一升级方案设计了三层防线：
- ① CardRouter (选择格式) ← Agent 绕过 ❌
- ② CardBuilder (构建卡片) ← Agent 未调用 ❌
- ③ Gateway 兜底 (剥离 Markdown) ← 兜底丑陋 ❌

三层都没拦住，因为：
- 第一层 opt-in → Agent 不调
- 第二层需要主动构建 → Agent 偷懒写 Markdown
- 第三层是安全网不是美化器 → 产出 `• # •` 乱码

## 修复优先级

P0 — 网关加 thinking 前缀截断
P1 — 网关表格→CardBuilder.table() 而非 • 列表
P2 — Persona 强制 Router 调用规则
P3 — pre-send 自检机制
P4 — 长消息自动 doc import 降级
