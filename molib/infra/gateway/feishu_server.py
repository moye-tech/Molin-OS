"""
飞书网关 — 已废弃（v6.6）

飞书消息处理已统一迁移到独立 feishu-bot 容器（integrations/feishu/bot_main.py），
使用 lark-oapi WebSocket 长连接，不再需要此 Webhook 处理器。

历史：此文件曾嵌入 Hermes CEO API 进程，提供 /webhook/feishu/webhook 端点。
原因：用户要求"所有端口和界面统一通过飞书完成"，Webhook 模式需要公网 IP，
      而 WebSocket 长连接无需公网暴露。

保留此空文件仅为了避免 ImportError（如有其他模块间接引用）。
"""
