# ngrok 免费版 "Visit Site" 警告页排障

> 2026-05-11 实战诊断

## 症状

通过 ngrok 免费版公网 URL 访问 Web 服务时，浏览器显示一个警告页：
- "You are about to visit: xxx.ngrok-free.dev"
- 需要点击 "Visit Site" 按钮才能进入实际页面
- 点击后页面可能"数据为空"——因为警告页拦截了正常的 JS/CSS/API 请求

## 根因

ngrok 免费版为防滥用，在浏览器首次访问时注入一个 interstitial 页面。
该页面通过 ngrok 代理注入，不在你的服务器响应中。

## 正确解法

### 方法一：点击 "Visit Site"（一次性）

浏览器点击按钮后，ngrok 设置 cookie（有效期约 7 天），
同一浏览器后续访问不再显示警告页。

### 方法二：ngrok-skip-browser-warning 请求头

⚠️ 关键认知：这个头必须是 **请求头**（浏览器 → ngrok），不是响应头。

- ❌ 错误做法：在服务器响应中添加 `ngrok-skip-browser-warning: 1`（无效）
- ❌ 错误做法：在反向代理中添加该响应头（同样无效）
- ✅ 正确做法：在 curl/API 请求中添加：
  `curl -H "ngrok-skip-browser-warning: 1" https://xxx.ngrok-free.dev`

浏览器无法控制请求头 → 方法二不适用于浏览器访问。

### 方法三：升级付费

付费 ngrok 计划不显示警告页。

### 方法四：切换隧道服务（推荐）

ngrok 免费版对浏览器 User-Agent 强制注入 interstitial，无法从服务器端绕过。换用无广告页的免费隧道：

**localhost.run**（SSH 隧道，零配置）
```bash
ssh -R 80:localhost:8080 nokey@localhost.run
# → https://<id>.lhr.life
```
- ✅ 无广告页、无需账号
- ⚠️ URL 每次重启变化；有速率限制（429）；注册免费账号可获得固定域名

**cloudflared TryCloudflare**
```bash
cloudflared tunnel --url http://localhost:8080
```
- ✅ 无广告页、已通过 brew 安装（`/opt/homebrew/bin/cloudflared`）
- ⚠️ TryCloudflare API 偶尔 500 错误（2026-05-11 实测）

### 方法五：升级付费（ngrok）

付费 ngrok 计划不显示警告页，支持自定义域名。

## Hermes Web UI 访问令牌

hermes-web-ui (v0.5.16) 登录页面需要"访问令牌"：

- 令牌位置：`~/.hermes-web-ui/.token`（首次启动自动生成，64 字符 hex）
- 自定义：`AUTH_TOKEN` 环境变量
- 禁用认证：`AUTH_DISABLED=1`
- 服务端口：8648（Node.js 进程）
- 安装路径：`~/.npm-global/lib/node_modules/hermes-web-ui/`
