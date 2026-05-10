# 闲鱼 SSL/TLS 故障排除指南

> 会话日期: 2026-05-10 | 修复者: Hermes Agent

## 问题: SSLEOFError 握手超时

### 症状
```
requests.exceptions.SSLError: HTTPSConnectionPool(host='h5api.m.goofish.com', port=443):
Max retries exceeded (Caused by SSLError(SSLEOFError(8,
'[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol')))
```

### 环境
- Python 3.12.13 (Homebrew, macOS 26.4.1)
- OpenSSL 3.6.2
- venv: `~/Molin-OS/molib/xianyu/.venv/`
- 目标: `h5api.m.goofish.com:443`

### 调试过程

**尝试1: certifi 证书包** — 失败
使用 certifi 的 CA bundle (`certifi.where()`) 替代系统证书，仍然超时。说明不是证书链问题。

**尝试2: 禁用证书验证** — 成功
`verify_mode = ssl.CERT_NONE` 可以连接，说明服务器可达但 TLS 握手有问题。

**尝试3: 强制 TLS 1.2** — 成功 ✅
```python
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ctx.minimum_version = ssl.TLSVersion.TLSv1_2
ctx.maximum_version = ssl.TLSVersion.TLSv1_2
sock = socket.create_connection(('h5api.m.goofish.com', 443), timeout=10)
ssock = ctx.wrap_socket(sock, server_hostname='h5api.m.goofish.com')
# TLS version: TLSv1.2, Cipher: ECDHE-ECDSA-AES128-GCM-SHA256
```

### 根因
闲鱼 `h5api.m.goofish.com` 服务器的 TLS 1.3 实现与 Python 3.12 + OpenSSL 3.6.2 不兼容。`curl` 可以连接是因为它默认使用了 TLS 1.2。

### 最终修复

在 `goofish_apis.py` 中添加自定义 `HTTPAdapter`，强制所有到 goofish.com 的连接使用 TLS 1.2：

```python
import ssl as _ssl
from requests.adapters import HTTPAdapter

class _GoofishAdapter(HTTPAdapter):
    """Force TLS 1.2 for goofish.com — server TLS 1.3 incompatible with OpenSSL 3.6"""
    def init_poolmanager(self, *args, **kwargs):
        ctx = _ssl.create_default_context()
        ctx.minimum_version = _ssl.TLSVersion.TLSv1_2
        ctx.maximum_version = _ssl.TLSVersion.TLSv1_2
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        ctx = _ssl.create_default_context()
        ctx.minimum_version = _ssl.TLSVersion.TLSv1_2
        ctx.maximum_version = _ssl.TLSVersion.TLSv1_2
        kwargs['ssl_context'] = ctx
        return super().proxy_manager_for(*args, **kwargs)

def _ssl_session() -> requests.Session:
    s = requests.Session()
    s.mount('https://', _GoofishAdapter())
    return s
```

所有 `requests.Session()` 替换为 `_ssl_session()`。

### 验证
```bash
cd ~/Molin-OS/molib/xianyu
PYTHONPATH=. .venv/bin/python3 -c "
from goofish_apis import XianyuApis
from utils.goofish_utils import trans_cookies, generate_device_id
# ... load cookies ...
api = XianyuApis(cookies, device_id)
print(api.get_token()['ret'])  # ['SUCCESS::调用成功']
"
```

### 关键教训

1. **先测 TLS 版本** — 用裸 socket + SSL context 测试不同 TLS 版本，比盲目换证书快得多
2. **curl ≠ Python** — curl 可能用了不同的 TLS 版本/密码套件
3. **venv 隔离** — Hermes cron 的 Python ≠ xianyu venv 的 Python。修复只在 xianyu venv 生效
4. **健康检查脚本模式** — cron 作业应使用带 shebang 的独立脚本指向正确的 venv
