# 飞书"回调服务不在线"修复手册

## 诊断日期
2026-05-10

## 现象
飞书聊天窗口持续出现系统提示「回调服务不在线」，但消息收发正常。

## 根因

Hermes 网关的 `gateway/platforms/feishu.py` 中，`_connect_websocket()` 方法只建立 WebSocket 长连接，**不调用** `_connect_webhook()` 启动 HTTP 回调服务器。

飞书平台有两套独立的消息通道：

| 通道 | 用途 | 协议 | Hermes 状态 |
|------|------|------|------------|
| WebSocket 长连接 | 实时消息收发 | WSS | ✅ 正常 |
| HTTP 事件回调 | 事件推送 + **健康检查** | HTTPS POST | ❌ 未启动 |

飞书后台定期对配置的「事件回调 URL」做健康检查（`url_verification` challenge），若不可达则显示「回调服务不在线」警告。

两个连接模式在原始代码中互斥——走 WebSocket 就不走 HTTP 回调。

## 修复方案 A：WebSocket + HTTP 回调双模（已采用）

在 `_connect_websocket()` 方法末尾追加 aiohttp HTTP 服务器启动逻辑。

### 修改位置

文件：`~/.hermes/hermes-agent/gateway/platforms/feishu.py`

在 `_connect_websocket()` 方法中，`self._ws_future = loop.run_in_executor(...)` 之后，`_connect_webhook()` 定义之前。

### 修改内容

```python
# === HTTP callback server (for Feishu URL verification health checks) ===
# Added 2026-05-10: Feishu requires HTTP callback URL to be reachable
# even when using WebSocket mode. Start a minimal aiohttp server.
if FEISHU_WEBHOOK_AVAILABLE:
    try:
        from aiohttp import web
        
        async def _handle_feishu_webhook(request):
            body = await request.json()
            if body.get("type") == "url_verification":
                return web.json_response({"challenge": body.get("challenge", "")})
            return web.json_response({"code": 0})
        
        self._webhook_app = web.Application()
        self._webhook_app.router.add_post(self._webhook_path, _handle_feishu_webhook)
        self._webhook_runner = web.AppRunner(self._webhook_app)
        await self._webhook_runner.setup()
        self._webhook_site = web.TCPSite(self._webhook_runner, self._webhook_host, self._webhook_port)
        await self._webhook_site.start()
        logger.info(f"HTTP callback server started on {self._webhook_host}:{self._webhook_port}{self._webhook_path}")
    except Exception as e:
        logger.warning(f"Failed to start HTTP callback server: {e}")
```

### 默认参数

| 参数 | 值 | 来源 |
|------|-----|------|
| host | 127.0.0.1 | `FeishuAdapterSettings._DEFAULT_WEBHOOK_HOST` |
| port | 8765 | `FeishuAdapterSettings._DEFAULT_WEBHOOK_PORT` |
| path | /feishu/webhook | `FeishuAdapterSettings._DEFAULT_WEBHOOK_PATH` |

### 设计要点

- **最小干扰**：HTTP 服务器只处理 `url_verification` challenge，实际事件仍走 WebSocket
- **复用现有配置**：端口/路径复用 FeishuAdapterSettings 中的默认值
- **清理兼容**：`disconnect()` 方法已有 `_stop_webhook_server()` 逻辑，无需额外修改

## 本地验证

```bash
# 验证回调服务器响应
curl -X POST http://localhost:8765/feishu/webhook \
  -H 'Content-Type: application/json' \
  -d '{"type":"url_verification","challenge":"ping"}'
# 预期输出: {"challenge":"ping"}
```

## ⚠️ 隧道穿透（待完成）

本地回调修好后，飞书服务器仍无法访问 `127.0.0.1:8765`。

需要在飞书开发者后台「事件订阅」中将「请求网址」设为公网地址。

隧道方案（优先级排序）：

| 方案 | 要求 | Mac M2 网络状态 |
|------|------|---------------|
| ngrok | 免费注册 authtoken | ❌ API 可达但 authtoken 无效 |
| cloudflared | `brew install cloudflared` | ❌ trycloudflare.com API 超时 |
| serveo.net | SSH `ssh -R` | ❌ 连接挂起 |
| localhost.run | SSH `ssh -R` | ❌ exit code 255 |

需要用户提供有效的 ngrok authtoken 或替代隧道方案。

## 相关文件

- 修改文件：`~/.hermes/hermes-agent/gateway/platforms/feishu.py`
- 日志文件：`~/.hermes/logs/agent.log`
- 环境变量：`~/.hermes/.env`（`FEISHU_APP_ID`, `FEISHU_APP_SECRET` 等）

## 网关稳定性

原始网关进程会意外退出。修复后需确认网关稳定运行：

```bash
# 查看网关进程
pgrep -fl "hermes.*gateway"

# 查看最近日志
tail -30 ~/.hermes/logs/agent.log
```
