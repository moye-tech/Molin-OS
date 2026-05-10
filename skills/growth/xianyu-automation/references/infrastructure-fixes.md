# 闲鱼基础设施修复记录

## TLS 1.2 强制（Python 3.12 + OpenSSL 3.6）

### 问题
Python 3.12.13 + OpenSSL 3.6.2 与闲鱼 `h5api.m.goofish.com` 服务器的 TLS 1.3 握手不兼容，导致 `SSLEOFError: [SSL: UNEXPECTED_EOF_WHILE_READING]`。

curl 和 Python 3.11（OpenSSL 3.5.6）可正常连接，但 Python 3.12 venv 必定超时。

### 根因
闲鱼 h5api 服务器在 TLS 1.3 握手阶段发送 EOF，OpenSSL 3.6.x 的 TLS 1.3 实现与此不兼容。降级到 TLS 1.2 可正常通信。

### 修复
在 `goofish_apis.py` 中添加 `_GoofishAdapter`，覆盖 `HTTPAdapter.init_poolmanager()` 强制 TLS 1.2：

```python
import ssl as _ssl
from requests.adapters import HTTPAdapter

class _GoofishAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = _ssl.create_default_context()
        ctx.minimum_version = _ssl.TLSVersion.TLSv1_2
        ctx.maximum_version = _ssl.TLSVersion.TLSv1_2
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)

def _ssl_session() -> requests.Session:
    s = requests.Session()
    s.mount('https://', _GoofishAdapter())
    return s
```

所有 `requests.Session()` 替换为 `_ssl_session()`：
- `build_initial_cookies()` 第 70 行
- `XianyuApis.__init__()` 第 290 行

### 验证
```bash
cd ~/Molin-OS/molib/xianyu && PYTHONPATH=. .venv/bin/python3 -c "
from goofish_apis import XianyuApis, _ssl_session
# ... load cookies ...
token = api.get_token()
# 应返回 ['SUCCESS::调用成功']
"
```

或直接测试原始 SSL 连接：
```python
import socket, ssl
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ctx.minimum_version = ssl.TLSVersion.TLSv1_2
ctx.maximum_version = ssl.TLSVersion.TLSv1_2
sock = socket.create_connection(('h5api.m.goofish.com', 443), timeout=10)
ssock = ctx.wrap_socket(sock, server_hostname='h5api.m.goofish.com')
print(ssock.version())  # 应输出 TLSv1.2
```

---

## WebSocket API 迁移（websockets v16）

### 问题
websockets v16.0 废弃了 `extra_headers` 参数，改为 `additional_headers`。
调用 `websockets.connect(url, extra_headers=headers)` 抛出：
```
TypeError: BaseEventLoop.create_connection() got an unexpected keyword argument 'extra_headers'
```

### 修复
三个文件中全局替换 `extra_headers` → `additional_headers`：
- `xianyu_auto_service.py` 第 156 行
- `goofish_live.py` 第 38、278 行
- `xianyu_helper.py` 第 215 行

---

## Cookie 加载模式

### cookies.json 格式
`~/.hermes/xianyu_bot/cookies.json` 以 JSON 对象存储单个 cookie 字段：

```json
{
  "_m_h5_tk": "f88c8655...",
  "_m_h5_tk_enc": "bfe880a...",
  "_samesite_flag_": "true",
  "_tb_token_": "537b14...",
  "cookie2": "1c5f43c...",
  ...
}
```

### 构建 Cookie 字符串
```python
import json
with open('~/.hermes/xianyu_bot/cookies.json') as f:
    data = json.load(f)
cookie_str = '; '.join(f'{k}={v}' for k, v in data.items() if not k.startswith('_meta'))
```

注意：不包含 `cookie_string` 字段，需从各字段重建。

---

## WebSocket 监听器启动

### 脚本位置
`~/.hermes/xianyu_bot/ws_listener.py`

### 启动命令
```bash
cd ~/Molin-OS/molib/xianyu
PYTHONPATH=. .venv/bin/python3 -B ~/.hermes/xianyu_bot/ws_listener.py
```

### 重要注意事项
- 必须清除 `__pycache__` 后再启动（`-B` 标志可跳过字节码缓存）
- PYTHONPATH 必须包含 xianyu 模块目录
- WebSocket 连接超时后自动重连（5 秒间隔）
- 日志写入 `~/.hermes/xianyu_bot/ws.log`

### 健康检查
```bash
tail -5 ~/.hermes/xianyu_bot/ws.log
# 应看到 "✅ WebSocket 已连接" 和 "初始化完成"
```
