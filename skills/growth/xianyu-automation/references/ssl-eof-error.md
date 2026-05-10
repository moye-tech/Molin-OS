# 闲鱼 API SSL 握手超时问题诊断与修复

## 问题

```
SSLEOFError(8, '[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1016)')
```

- 出现环境：Python 3.12 + OpenSSL 3.6.2 连接 `h5api.m.goofish.com`
- curl 可连通，但 Python requests 库握手超时
- Python 3.11 + OpenSSL 3.5.6 同样有此问题

## 根因

Python 3.12 的 TLS 1.3 握手与闲鱼 h5api 服务器不兼容，服务器在 TLS 1.3 握手阶段断开连接。

## 修复

在 `goofish_apis.py` 中强制 TLS 1.2：

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

所有 `requests.Session()` 替换为 `_ssl_session()`。

## WebSocket 兼容性

- `websockets` v16 废弃 `extra_headers` 参数
- 改为 `additional_headers`
- 影响文件：`xianyu_auto_service.py`, `goofish_live.py`, `xianyu_helper.py`

## Cookie 加载

- `~/.hermes/xianyu_bot/cookies.json` 存储为独立 JSON 字段，不是 cookie string
- 构建 cookie string：`'; '.join(f'{k}={v}' for k, v in data.items())`

## 健康检查脚本

`~/.hermes/scripts/xianyu_check.py`：
- 使用 xianyu venv Python（3.12 + 已修复的 goofish_apis）
- shebang 明确指定 venv Python 路径
- os.chdir 到 xianyu 目录以解析相对路径
- 返回 JSON：`{"status":"ok","token_ok":true}`

## WebSocket 监听器

`~/.hermes/xianyu_bot/ws_listener.py`：
- 常驻进程，从 cron 独立运行
- 日志写入 `~/.hermes/xianyu_bot/ws.log`
- Token OK → 连接 WebSocket → listen_forever 循环
- `additional_headers` 兼容 websockets v16
