# 墨域OS · MCP 服务器配置中心

本文档列出系统中注册的所有 MCP (Model Context Protocol) 服务器，
作为 Agent 能力外挂的标准化接口。

---

## 已注册 MCP Server

| 名称 | 技术栈 | 用途 | 状态 |
|:-----|:-------|:-----|:-----|
| molin-mcp-server | FastMCP (Python) | 将高频子公司能力暴露为 MCP 工具 | ✅ 已创建 |
| feishu-mcp | 飞书开放平台 | 消息发送/卡片/文档操作 | ⏳ 配置中 |

---

## 注册规范

MCP Server 统一管理模式：

```yaml
# ~/.hermes/config.yaml (MCP servers 段)
mcp_servers:
  molin-mcp:
    command: python3
    args: ["-m", "molib.mcp.server"]
    transport: stdio
  feishu:
    command: python3  
    args: ["-m", "molib.mcp.feishu_server"]
    transport: stdio
```

---

## 每个 Server 提供的工具

### molin-mcp-server

| 工具名 | 功能 | 字段 |
|:-------|:-----|:-----|
| content_generate | 按主题生成内容 | topic, platform, tone |
| trend_analyze | 分析趋势数据 | source, days |
| memory_upsert | 写入记忆 | key, value, namespace |
| memory_query | 检索记忆 | query, limit |
| trading_signal | 交易信号分析 | symbol, interval |
| system_health | 系统健康检查 | — |

---

## 安全

- 所有 MCP Server 本地运行，不对公网暴露端口
- 敏感 API Key 通过环境变量注入，不写入配置文件
- 单个工具超时上限 120 秒

---

## 故障排查

```bash
# 测试 MCP Server 是否可启动
echo '{"jsonrpc":"2.0","method":"ping","id":1}' | python3 -m molib.mcp.server

# 查看日志
tail -f ~/.hermes/logs/mcp-*.log
```

---

*更新于 2026-05-06 — 对应墨域OS v1.0*
