# 闲鱼自动化 — 完整安装与初始化指南

> 本文档记录 2026-05-10 首次 cron 执行时诊断出的完整依赖链和初始化步骤。
> 当系统从零开始或在新机器上部署时，按此清单操作。

## 前置条件总览

```
✅ = 已完成  ❌ = 待处理

[❌] 1. Python 3.12     — brew install python@3.12
[❌] 2. Xianyu Cookies  — 扫码导出 → ~/.xianyu_cookies_new.txt  
[❌] 3. Goofish 项目    — clone XianYuApis → ~/xianyu_agent/
[✅] 4. 状态目录        — ~/.hermes/xianyu_bot/ (自动初始化)
[✅] 5. pip 依赖        — blackboxprotobuf, PyExecJS, websockets
[✅] 6. 飞书通知通道    — oc_94c87f141e118b68c2da9852bf2f3bda
```

## 详细步骤

### Step 1: Python 3.12

```bash
brew install python@3.12
# 验证
python3.12 --version
```

**为什么需要**: `xianyu_bot.py` 使用了 `asyncio.TaskGroup` 和 `asyncio.timeout()` 上下文管理器，这些是 Python 3.11+ 的特性。macOS 自带的 Python 3.9 不支持。

### Step 2: Xianyu Cookies

1. 打开 Chrome/Edge，访问 https://www.goofish.com
2. 用闲鱼 App 扫码登录你的卖家账号
3. F12 → Application → Cookies → goofish.com
4. 导出所有 cookies（确保包含 `_m_h5_tk`, `unb`, `cookie2` 等关键字段）
5. 保存为纯文本文件：`~/.xianyu_cookies_new.txt`

**Cookie 格式**: 一行一个 `name=value`，或标准 Netscape cookie 格式。

### Step 3: Goofish 项目 (XianYuApis)

```bash
cd ~
git clone <XianYuApis仓库URL> xianyu_agent
cd xianyu_agent
pip install -r requirements.txt
```

**必需的目录结构**:
```
~/xianyu_agent/
├── goofish_apis.py          # 闲鱼 API 封装
├── goofish_live.py          # 实时监控
├── message/
│   └── types.py             # Price, DeliverySettings (必须)
├── utils/
│   └── goofish_utils.py     # trans_cookies, generate_sign, generate_device_id
└── static/
    └── goofish_js_version_2.js  # JS 加密逻辑 (goofish_utils 模块级加载)
```

**关键**: `goofish_utils.py` 在 `import` 时就会用 `execjs` 编译 `static/goofish_js_version_2.js`。如果目录结构不对，import 就会失败。

### Step 4: pip 依赖

```bash
pip install blackboxprotobuf PyExecJS websockets protobuf
```

这些是 goofish 项目的运行时依赖，不在标准的 requirements.txt 中。

### Step 5: 状态目录初始化

状态目录由 cron job 首次运行时自动创建，无需手动操作：
- `~/.hermes/xianyu_bot/config.json`
- `~/.hermes/xianyu_bot/state.json`
- `~/.hermes/xianyu_bot/activity.log`

默认 `notify_chat_id` 为 `oc_94c87f141e118b68c2da9852bf2f3bda`（飞书自动化控制群）。

## 验证就绪

```bash
# 测试飞书连接
cd ~/.hermes/molin/bots
python3.12 xianyu_bot.py test

# 测试 API 连接
python3.12 xianyu_bot.py cron
```

成功输出应包含 `✅ 闲鱼Token有效`。

## 生产运行模式

### WebSocket 实时监听（推荐）
```bash
python3.12 ~/.hermes/molin/bots/xianyu_bot.py ws
```
- 长连接，实时接收消息
- AI 自动回复（通过千问 API）
- 断线自动重连

### Cron 定时检测
由 Hermes cron 自动调度（15,45 9-21 * * *），执行：
```bash
python3.12 ~/.hermes/molin/bots/xianyu_bot.py cron
```
- 检测 token 状态 + 汇报统计
- 不拉取消息（消息由 WS 监听处理）

### 增强模块（CH5）
```bash
python3.12 xianyu_enhanced.py all        # 全部功能
python3.12 xianyu_enhanced.py schedule   # 定时任务
python3.12 xianyu_enhanced.py dashboard  # 仪表盘
```

## 常见问题

### Q: `ModuleNotFoundError: No module named 'message'`
**A**: goofish_apis.py 需要 `message/types.py`。确保完整的 XianYuApis 项目 clone 到了 `~/xianyu_agent/`，不能只用 Molin-OS 的 molib/xianyu 目录（那个目录缺少 message 模块）。

### Q: `FileNotFoundError: static/goofish_js_version_2.js`
**A**: goofish_utils.py 使用相对路径加载 JS 文件。必须从 `~/xianyu_agent/` 目录运行，或确保 `static/` 子目录存在。

### Q: `execjs._exceptions.ProgramError`
**A**: 需要安装 Node.js：`brew install node`。execjs 需要一个 JS 运行时。

### Q: Token 过期怎么办
**A**: 删除 `~/.xianyu_cookies_new.txt`，重新扫码登录导出新的 cookies。Token 有效期通常几小时到一天。
