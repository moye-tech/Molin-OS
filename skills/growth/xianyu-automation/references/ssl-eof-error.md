# SSL EOF Error — h5api.m.goofish.com

## 症状

Python `requests` 调用闲鱼 Token API 时抛出：

```
HTTPSConnectionPool(host='h5api.m.goofish.com', port=443):
Max retries exceeded with url: /h5/mtop.taobao.idlemessage.pc.login.token/1.0/...
(Caused by SSLError(SSLEOFError(8, '[SSL: UNEXPECTED_EOF_WHILE_READING]
EOF occurred in violation of protocol (_ssl.c:1016)')))
```

## 诊断步骤

### 1. 排除网络不通

```bash
curl -sI --connect-timeout 5 https://h5api.m.goofish.com/
# 正常返回: HTTP/1.1 404 Not Found (Server: Tengine)
# 这说明服务器可达，问题在 Python SSL 握手层
```

### 2. 排除主站故障

```bash
curl -sI --connect-timeout 5 https://www.goofish.com/
# 正常返回: HTTP/2 200
```

### 3. 检查 Python SSL 版本

```python
import ssl
print(ssl.OPENSSL_VERSION)
# macOS 3.12+ 常见: LibreSSL 3.3.6
```

## 已知环境

| 环境 | 出现频率 | 恢复方式 |
|:-----|:---------|:---------|
| macOS 26.4.1 + Python 3.12 | 偶发（约 10-20% 的 cron 轮次） | 等待 15-30 分钟自动恢复 |
| Ubuntu + Python 3.12 | 未观察到 | — |

## 根因推测

- 阿里系 API（mtop.taobao.idlemessage）的 TLS 实现与 macOS LibreSSL 的特定握手阶段存在兼容性问题
- `curl` 使用系统级 SecureTransport/OpenSSL，路径不同，不受影响
- 可能是阿里侧对非标准 TLS ClientHello 的间歇性拒绝

## 恢复动作

1. **等待下一轮 cron 重试** — 通常 15-30 分钟后自动恢复，无需人工介入
2. **如果连续 3+ 轮失败** — 检查 Cookies 是否过期：
   ```bash
   ls -la ~/.xianyu_cookies_new.txt
   # 如果超过 24 小时未更新，需要重新扫码登录
   ```
3. **如果 Cookies 有效但仍持续失败** — 检查 requests/urllib3 版本：
   ```bash
   python3.12 -c "import requests; print(requests.__version__)"
   python3.12 -c "import urllib3; print(urllib3.__version__)"
   ```

## 历史记录

| 时间 | 状态 | 恢复 |
|:-----|:-----|:-----|
| 2026-05-10 16:45 | Token 有效 | — |
| 2026-05-10 17:18 | SSL EOF 错误 | — |
| 2026-05-10 17:18:49 | Token 有效 | 自动恢复（~1分钟） |
| 2026-05-10 17:55 | Token 有效 | — |
| 2026-05-10 18:17 | SSL EOF 错误 | 待下一轮重试 |
