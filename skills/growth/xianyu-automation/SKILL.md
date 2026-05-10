---
name: xianyu-automation
description: "Xianyu (闲鱼) second-hand marketplace automation — message polling, deal-signal detection, and buyer conversation pipeline. Use when managing Xianyu seller conversations, detecting purchase/refund intent, processing incoming messages, or setting up automated reply workflows."
version: 1.1.0
tags: [xianyu, xianyu, ecommerce, automation, second-hand-market, deal-detection, message-pipeline]
category: productivity
source: molin-ai-intelligent-system/integrations/xianyu/listener.py (v6.6)
metadata:
  hermes:
    molin_owner: 墨商销售（闲鱼实业）
---

## Xianyu Automation — 闲鱼接单自动化

### Prerequisites & Setup

Before the message pipeline can function, these must be in place:

| Item | Check | Detail |
|------|-------|--------|
| **Python 3.12 venv** | `~/xianyu_agent/.venv/bin/python3 --version` | Required for asyncio features. `brew install python@3.12` then create venv. |
| **XianyuApis project** | `~/xianyu_agent/` symlink → `Molin-OS/molib/xianyu/` | Must contain `goofish_apis.py`, `goofish_live.py`, `utils/goofish_utils.py`, `static/goofish_js_version_2.js` |
| **Cookies file** | `~/.xianyu_cookies_new.txt` | **Must be semicolon-separated `key=value` format**, NOT JSON. See pitfall below. |
| **Token valid** | Run `xianyu_bot.py cron` | Verifies cookies → token → API connectivity. |

**⚠️ Cookies format pitfall:** `trans_cookies()` in `goofish_utils.py` parses cookies by splitting on `"; "` and expects `key1=val1; key2=val2` format. If cookies are saved as JSON (`{"key": "val"}`), the API call will fail with an opaque cookie-parsing error. Convert JSON cookies to `key=value; key=value` format before saving. See `references/cookies-format-fix.md` for the exact conversion script.

### Running Modes

The xianyu_bot.py has two distinct modes — know which one you're using:

| Mode | Command | Purpose | Duration |
|------|---------|---------|----------|
| **cron** | `python3.12 xianyu_bot.py cron` | Health check: validate token, report state. Does NOT poll messages. | ~3s, exits |
| **ws** | `python3.12 xianyu_bot.py ws` | WebSocket listener: real-time message polling, deal-signal detection, auto-reply. | Long-running daemon |

**For cron jobs (every 15-30 min):** Run `cron` mode for connectivity health check. The ws listener should already be running as a background daemon — cron mode just verifies it's healthy.

**To start real-time message handling:** Launch the ws listener as a daemon:
```bash
cd ~/xianyu_agent && nohup .venv/bin/python3 ~/.hermes/molin/bots/xianyu_bot.py ws > ~/.hermes/xianyu_bot/ws.log 2>&1 &
```

### Overview

This skill encodes the Molin XianyuListener v6.6 architecture as an agent-executable workflow. You act as the Xianyu message-processing pipeline: poll for incoming messages, maintain per-conversation memory, detect buy/refund signals in buyer messages, and route each message through the appropriate response pipeline.

The core loop mirrors the production listener: poll → detect → route → notify. Every message is classified into one of four pipelines based on signal detection and conversation state.

### When to Use

- User asks you to process incoming Xianyu buyer messages
- Running as a **scheduled cron job** for Xianyu message detection (every 30 min, 09:00-21:00)
- User needs deal-signal detection on buyer chat messages
- User wants automated first-contact replies for Xianyu listings
- User asks to set up message polling with 30-second intervals (live WebSocket mode)
- User needs refund/escalation detection in buyer conversations
- User wants a structured conversation memory across multi-turn chats

**Don't use for:** Other marketplace platforms (Taobao, JD, Pinduoduo have different message formats). Don't use for outbound marketing campaigns — this is an inbound message handler.

---

## 0. PREREQUISITES & SETUP — 前置条件（首次运行必检）

Before running any message detection, verify these three prerequisites. If any are missing, generate a diagnostic report (see format below) and stop — do not attempt API calls.

### Required Infrastructure

| # | Requirement | Check | Fix |
|---|------------|-------|-----|
| 1 | **Xianyu Cookies** | `~/.xianyu_cookies_new.txt` exists | 扫码登录 goofish.com，导出完整Cookies保存至此文件 |
| 2 | **Python 3.12+** | `python3.12 --version` succeeds | `brew install python@3.12`（xianyu_bot.py 需要3.12+的asyncio特性） |
| 3 | **Goofish项目** | `~/xianyu_agent/` 包含 `goofish_apis.py`, `utils/goofish_utils.py`, `static/goofish_js_version_2.js`, `message/types.py` | Clone完整的XianYuApis项目到 `~/xianyu_agent/`，安装requirements.txt |

### State Directory

The cron job maintains state at `~/.hermes/xianyu_bot/`:
- `config.json` — notification settings (notify_chat_id, auto_reply flag)
- `state.json` — counters (messages_handled, replies_sent, last_activity)
- `activity.log` — timestamped activity log

On first run, initialize these files if they don't exist. Default `notify_chat_id` is `oc_94c87f141e118b68c2da9852bf2f3bda`.

### Cron Mode Diagnostic Report Format

When invoked as a cron job and prerequisites are missing, generate this report structure:

```json
{
  "job": "闲鱼消息检测",
  "executed_at": "<timestamp>",
  "status": "blocked",
  "api_connected": false,
  "new_messages": 0,
  "blockers": [
    {"item": "Xianyu Cookies", "action": "...", "owner": "创始人"},
    {"item": "Python 3.12", "action": "brew install python@3.12", "owner": "创始人"}
  ],
  "infra_initialized": true,
  "next_run": "<next cron time>"
}
```

Write this report to `~/.hermes/state/xianyu_cron_report_latest.json` for downstream relay consumption.

### Known Pitfalls

1. **Goofish module import fails at module level**: `goofish_utils.py` compiles JS (`static/goofish_js_version_2.js`) with `execjs` at import time using relative paths. This breaks when not run from the `~/xianyu_agent/` directory. Fix: ensure the full XianYuApis project is cloned to `~/xianyu_agent/`, not just symlinked.

2. **Missing `message/types.py`**: `goofish_apis.py` imports `from message.types import Price, DeliverySettings`. This module is part of the original XianYuApis project and is NOT included in the Molin-OS molib/xianyu directory. You need the full upstream project.

3. **pip dependencies**: In addition to `requests`, the goofish project needs `blackboxprotobuf`, `PyExecJS`, `websockets`. Install with `pip install blackboxprotobuf PyExecJS websockets`.

4. **Python 3.9 vs 3.12**: The xianyu_bot.py uses `asyncio` features (TaskGroup, timeout contexts) only available in Python 3.11+. System Python on macOS may be 3.9 — install 3.12 via brew.

### Production Scripts

The actual production bot scripts live at `~/.hermes/molin/bots/`:
- **`xianyu_bot.py`** — WebSocket real-time listener + AI auto-reply (via 千问) + cron check. Run modes: `ws` (live), `cron` (status check), `test` (Feishu connection test).
- **`xianyu_enhanced.py`** — CH5 enhancements: browsing detection (48h follow-up), auto review requests, dynamic pricing, dashboard.

When prerequisites are met, prefer running `python3.12 ~/.hermes/molin/bots/xianyu_bot.py cron` for the cron check path.

### Full setup checklist → `references/setup.md`

---

## Core Architecture

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│  Message In  │ ──▶ │ Pipeline Router │ ──▶ │    Action    │
│  (poll 30s)  │     │  detect+state   │     │  + Notify    │
└──────────────┘     └─────────────────┘     └──────────────┘
                            │
               ┌────────────┼────────────┐
               ▼            ▼            ▼
          Conversation   DealSignal    Message
           Memory        Detector     Pipeline
```

---

## 1. CONVERSATION MEMORY — 上下文记忆

Maintain a per-conversation context store. This is the foundation for multi-turn intelligence — without it, every message looks like first contact.

### Data Structure

```
conversations: Dict[conversation_id, List[turn]]
```

Each **turn** is:
```json
{
  "role": "buyer" | "system",
  "content": "<message text>",
  "time": <unix timestamp>
}
```

### Rules

| Rule | Value | Detail |
|------|-------|--------|
| **Max history** | 20 turns | Keep only the last 20 turns per conversation. When a 21st turn arrives, drop the oldest. |
| **Conversation ID** | `{from_user}:{item_id}` | Derived from buyer ID + listing item ID. If a native `conversation_id` is available, prefer that. |
| **Content truncation** | 200 chars | When retrieving context for display/injection, truncate each message to 200 characters. |

### is_first_contact()

Before processing any message, check:
```
conv_id not in conversations OR len(conversations[conv_id]) == 0 → True
```
When `True`: the buyer has never messaged about this item before. Trigger first-contact template.

### Context Retrieval

When injecting conversation context (e.g., for follow-up reply generation), retrieve the last **10** turns formatted as:
```
买家: <content[:200]>
买家: <content[:200]>
系统: <content[:200]>
```

---

## 2. DEAL SIGNAL DETECTION — 成交信号检测

Scan every buyer message for purchase-intent and refund-intent keywords. Refund signals are checked **first** (higher priority) because an escalating issue takes precedence over a purchase.

### BUY SIGNALS — 成交关键词 (30+ keywords)

```
成交, 好的, 怎么交易, 怎么付款, 我要了,
多少钱, 最低多少, 便宜点, 包邮吗,
发链接, 拍下, 下单, 链接给我,
ok, OK, 好, 行, 可以,
how much, buy, purchase
```

**Match:** Case-insensitive substring match. `"ok"` matches `"OK"`, `"好的"`, `"好的呢～"`, etc.

**Signal type:** `purchase_intent`
**Confidence:** `0.75`
**Suggested action:** `quote_or_close`

### REFUND SIGNALS — 退款/投诉关键词

```
退款, 退钱, 不要了, 退货, 取消,
有问题, 不满意, 投诉
```

**Match:** Case-insensitive substring match. Checked **before** buy signals.
**Signal type:** `refund_request`
**Confidence:** `0.90`
**Suggested action:** `escalate_to_approval`

### Detection Output

For every message, produce a DealSignal result:

```json
{
  "detected": true|false,
  "signal_type": "purchase_intent" | "refund_request" | "",
  "confidence": 0.0-1.0,
  "suggested_action": "quote_or_close" | "escalate_to_approval" | ""
}
```

If no signal matches, `detected` is `false` and all other fields are empty/zero.

---

## 3. MESSAGE PIPELINE — 消息处理流水线

Every incoming message follows this exact priority-ordered dispatch:

```
INCOMING MESSAGE
    │
    ├── 1. REFUND SIGNAL? ──▶ action: escalate
    │       signal_type == "refund_request"
    │       → Notify: "⚠️ 退款请求，需审批介入"
    │       → Output: { action: "escalate", needs_approval: true, ... }
    │
    ├── 2. FIRST CONTACT? ──▶ action: first_respond
    │       is_first_contact(conv_id) == True
    │       → Use first-reply template (Section 4)
    │       → Output: { action: "first_respond", suggested_reply: "...", ... }
    │
    ├── 3. DEAL SIGNAL? ──▶ action: quote_or_close
    │       deal.detected == True AND signal_type == "purchase_intent"
    │       → Trigger quote/close workflow
    │       → Output: { action: "quote_or_close", needs_bd_quote: true, ... }
    │
    └── 4. NORMAL FOLLOW-UP ──▶ action: follow_up
            No signals, not first contact
            → Generate smart follow-up reply
            → Output: { action: "follow_up", suggested_reply: "...", ... }
```

### Pipeline Step Detail

#### Step 1: Refund Escalation
```json
{
  "action": "escalate",
  "reason": "refund_detected",
  "conversation_id": "...",
  "message": "<buyer message, truncated to 200 chars>",
  "needs_approval": true
}
```
**Do not auto-reply to refund requests.** Flag for human (boss/operator) approval. Send a Feishu notification with the conversation context.

#### Step 2: First Contact Template
```json
{
  "action": "first_respond",
  "conversation_id": "...",
  "item_id": "...",
  "suggested_reply": "你好，关于「{item}」有什么可以帮你的？..."
}
```
Use the first-reply template from Section 4. Add the reply to conversation memory with `role: "system"`.

#### Step 3: Deal Signal — Quote/Close
```json
{
  "action": "quote_or_close",
  "conversation_id": "...",
  "deal_signal": "purchase_intent",
  "confidence": 0.75,
  "needs_bd_quote": true
}
```
This signals that a business-development (BD) quote or deal-closing flow should be triggered. The agent should prepare pricing info, shipping details, and payment instructions for this conversation.

#### Step 4: Normal Follow-Up
```json
{
  "action": "follow_up",
  "conversation_id": "...",
  "suggested_reply": "收到你的消息。关于这个问题，让我帮你确认一下～"
}
```
Acknowledge receipt. If conversation context (last 10 turns) provides enough information, generate a context-aware reply. Otherwise, use the default acknowledgment.

---

## 4. FIRST REPLY TEMPLATE — 首回复模板

Always use this exact template (with item name substitution) for first-contact messages:

```
你好，关于「{item}」有什么可以帮你的？
可以直接告诉我你的需求，我会尽快回复～
```

**Rules:**
- `{item}` is replaced with `msg.item_title` truncated to **20 characters**
- If `item_title` is empty, use `"商品"` as fallback
- The reply is added to conversation memory as `{ role: "system", ... }` after sending

---

## 5. API CONNECTION — goofish_apis 集成

The Xianyu API is accessed through the XianYuApis project (symlinked at `~/xianyu_agent` → `Molin-OS/molib/xianyu`). This is the **only supported way** to fetch messages and send replies.

### Project Structure

```
~/xianyu_agent/
├── goofish_apis.py          # XianyuApis class — REST API (login, messages, publish)
├── goofish_live.py          # XianyuLive class — WebSocket real-time message listener
├── xianyu_auto_service.py   # LLM-driven auto-reply service (OpenRouter + DeepSeek)
├── xianyu_helper.py         # Helper functions for listing management
├── message/
│   ├── __init__.py
│   └── types.py             # Message, Price, DeliverySettings models (pydantic)
├── utils/
│   ├── goofish_utils.py     # trans_cookies, generate_sign, generate_device_id
│   ├── gen_tfstk.js         # Node.js script for token generation
│   └── ...
├── static/
│   └── goofish_js_version_2.js  # JS engine for signature/MID/UUID generation
└── .venv/                   # Python 3.12 virtual environment
```

### Dependency Chain

| Layer | Component | Check |
|-------|-----------|-------|
| Runtime | Python 3.12+ | `/opt/homebrew/bin/python3.12 --version` |
| Virtual env | `~/xianyu_agent/.venv/` | Must exist with all packages |
| Python deps | requests, loguru, websockets, Pillow, execjs, blackboxprotobuf, pydantic, typing_extensions | `pip list` in venv |
| JS Engine | Node.js (v24+) | `node --version` — needed for `execjs` to run signature/MID generation |
| Auth | Cookie file | `~/.xianyu_cookies_new.txt` — exported from goofish.com browser session |

### Cookie File

The cookie file is the **single authentication mechanism**. Without it, the API cannot be initialized.

**How to obtain (founder action required):**
1. Open https://www.goofish.com in Chrome
2. Scan QR code with Xianyu app to login
3. Open DevTools → Application → Cookies → goofish.com
4. Copy all cookies as `key=value; key=value; ...` format
5. Save to `~/.xianyu_cookies_new.txt`

**Expected format:** `cookie2=xxx; _m_h5_tk=xxx; _m_h5_tk_enc=xxx; ...`

### API Initialization

```python
import sys; sys.path.insert(0, os.path.expanduser('~/xianyu_agent'))
from goofish_apis import XianyuApis
from goofish_live import XianyuLive

api = XianyuApis(cookie_file=os.path.expanduser('~/.xianyu_cookies_new.txt'))
# Test connectivity:
user_info = api.get_login_user_info()  # Returns user profile if auth works
```

### Message Fetching (REST)

For cron-job mode (no persistent WebSocket), use the REST API to check for new messages:

```python
# Get unread conversations / messages
messages = api.get_unread_messages()  # Returns list of message dicts
```

### Message Sending

```python
from message import make_text
api.send_message(to_user_id='xxx', content=make_text('回复内容'), item_id='xxx')
```

### LLM Auto-Reply

The `xianyu_auto_service.py` provides LLM-driven replies via OpenRouter + DeepSeek:

```python
from xianyu_auto_service import get_auto_reply_llm
reply = await get_auto_reply_llm(user_message_text)
```

Requires `OPENROUTER_API_KEY` in environment. Falls back to keyword-matching templates on LLM failure.

---

## 5. AUTOMATION PATTERN — 运行模式

### Two-Tier Architecture

闲鱼自动化采用双层架构。消息只能通过 WebSocket 获取，闲鱼 REST API 不提供消息端点。

### Tier 1: WebSocket 监听模式（实时消息处理）

这是**唯一能检测并回复消息**的模式。必须作为常驻守护进程运行。

```
启动: cd ~/xianyu_agent && python3.12 ~/Molin-OS/bots/xianyu_bot.py ws

WebSocket 生命周期:
    1. 初始化 API (cookies → trans_cookies → token → device_id)
    2. 连接 wss://wss-goofish.dingtalk.com/
    3. 注册 + 同步状态初始化
    4. 循环接收消息:
        a. /s/chat → 新消息 → AI 生成回复(千问 qwen-plus) → WS 发回闲鱼 → 飞书通知
        b. /s/sync → ACK 回复
        c. /!    → 心跳(每 15 秒发送)
    5. 断开 → 5 秒后自动重连
    6. Token 每 600 秒自动刷新
```

WS 模式功能：实时消息检测、AI 自动回复、飞书卡片通知、自动重连。

### Tier 2: Cron 巡检模式（健康检查）

Cron 只能验证 API 连通性和汇报统计，**不能拉取消息**。

```
启动: python3.12 ~/Molin-OS/bots/xianyu_bot.py cron
功能: Token 验证 + 读取状态文件汇报统计
限制: 无消息检测能力，无自动回复能力
```

巡检报告必须遵循 feishu-message-formatter cron 模板（纯文本 + emoji + ━━━ 分隔，禁止 Markdown）。

### 治理级别映射

| 操作 | 级别 | 说明 |
|------|------|------|
| AI 自动回复（正常消息） | L0 自动 | 千问生成回复，直接通过 WS 发回闲鱼 |
| 首次联系通知 | L1 通知 | 发送飞书卡片告知有新买家 |
| 成交信号 / BD 报价 | L2 审批 | 需要老板确认价格/承诺后报价 |
| 退款/投诉 | L2 审批 | 绝不自动回复，上报等待老板决策 |
| 涉及真实现金/支付 | L4 禁止 | 直接拒绝 |

### Polling Loop (30-second interval)

In the Hermes agent context, Xianyu automation uses two tiers:

**Tier 1: WS Listener (long-running daemon)**
```
cd ~/xianyu_agent && .venv/bin/python3 ~/.hermes/molin/bots/xianyu_bot.py ws
```
- Connects to Xianyu WebSocket for real-time message events
- Runs deal-signal detection on every incoming message
- Auto-replies via LLM (DeepSeek) or fallback templates
- Sends Feishu notifications for L2 escalations
- This is the **actual message processor** — must run as background daemon

**Tier 2: Cron Health Check (every 15-30 min)**
```
cd ~/xianyu_agent && .venv/bin/python3 ~/.hermes/molin/bots/xianyu_bot.py cron
```
- Validates Xianyu token is still fresh
- Reports `messages_handled` / `replies_sent` from state.json
- Alerts if token expired or cookies missing
- Does NOT poll messages — just verifies the WS listener is healthy

> See `references/cookies-format-fix.md` for the cookies JSON→semicolon conversion pitfall.

### Production Polling Loop (reference)

In full production (Redis-backed, not current agent mode):

When running as a scheduled cron job (no interactive user), the agent MUST first perform the pre-flight health check (Section 0), then attempt message fetching only if the API is ready.

```
CRON TICK (every 30 min):
    0. RUN pre-flight health check → determine api_ready (bool)
    1. IF api_ready == false:
        a. Produce patrol report card with blocker details
        b. Save state to ~/.hermes/state/xianyu_cron_report_latest.json
        c. STOP (do not attempt polling)
    2. IF api_ready == true:
        a. Initialize XianyuApis with cookie_file
        b. Fetch unread messages via REST API
        c. FOR each message: run pipeline (Section 3)
        d. Save conversation state
        e. Produce patrol report card with message stats
```

### Live Polling Mode (WebSocket, 30-second interval)

For interactive sessions with long-running listener:

```
WHILE running:
    1. Connect XianyuLive WebSocket
    2. On message received:
        a. Parse into XianyuMessage
        b. Run process_message(msg) → get result dict
        c. If result.needs_approval or result.needs_bd_quote:
            → Send Feishu/Lark notification to operator
    3. On disconnect: reconnect after 30s
```

### Message Model

```json
{
  "msg_id": "string (unique message ID)",
  "from_user": "string (buyer ID)",
  "to_user": "string (seller ID / your account)",
  "content": "string (message body text)",
  "item_id": "string (listing ID, can be empty)",
  "item_title": "string (listing title, can be empty)",
  "timestamp": 1234567890.0,
  "conversation_id": "string (platform conversation ID, can be empty)"
}
```

### Notification Triggers

| Condition | Channel | Priority |
|-----------|---------|----------|
| `needs_approval == true` (refund) | Feishu @boss | HIGH — immediate |
| `needs_bd_quote == true` (deal signal) | Feishu @bd_team | MEDIUM |
| First contact | Log only | LOW |

### State Persistence

In production, conversation memory lives in-memory during the listener's lifecycle. For agent usage:
- Track conversations in the current session's working memory
- If a session spans many conversations, persist to a JSON file at `~/.hermes/state/xianyu_conversations.json`
- Reload on session start if the file exists

### Cron Mode Execution（无消息 / API未就绪处理）

When invoked as a cron job (no user present, no interactive mode), follow this execution path:

```
1. CHECK PREREQUISITES (Section 0)
   ├── All met → proceed to Step 2
   └── Any missing → generate diagnostic report, STOP

2. TRY API CONNECTION
   ├── Token valid → proceed to Step 3
   └── Token expired / API unavailable → report status, STOP

3. POLL MESSAGES
   ├── New messages found → process with L0/L1/L2 pipeline
   └── No new messages → report "0 messages", STOP

4. PROCESS & NOTIFY
   ├── L0 auto-reply: send template + add to memory
   ├── L1 deal signal: log, notify BD via Feishu
   └── L2 escalation: flag for approval, do NOT auto-reply

5. SAVE & REPORT
   ├── Update state.json counters
   ├── Write relay file: ~/.hermes/state/xianyu_cron_report_latest.json
   └── Push summary to Feishu notify_chat_id
```

**Silent skip rule**: If this is a cron run and prerequisites are missing (no cookies), the response should still contain a clear diagnostic report — do NOT silently return "[SILENT]". The founder needs to know what's blocking activation.

### Governance Levels (L0/L1/L2) for Cron Pipeline

| Level | Trigger | Action | Auto? |
|-------|---------|--------|-------|
| **L0** | Normal inquiry, first contact, price ask | Template reply or AI-generated follow-up | ✅ Auto |
| **L1** | Purchase intent detected (deal signal) | Log + notify BD via Feishu | ✅ Auto (notification only) |
| **L2** | Refund request, complaint, >20% price cut | Escalate to founder for approval | ❌ Hold — do NOT reply |

---

## 0. PRE-FLIGHT HEALTH CHECK — 启动前自检

**Always run this FIRST** before attempting any message polling. In cron-job mode, the health check determines whether to enter the message pipeline or produce a blocker report.

### Step-by-step

```
0.1 Python 3.12
    /opt/homebrew/bin/python3.12 --version
    → Expected: Python 3.12.x
    → If missing: blocker "Python 3.12 未安装 — brew install python@3.12"

0.2 Virtual Environment
    ls ~/xianyu_agent/.venv/bin/python3.12
    → If missing: create it:
      /opt/homebrew/bin/python3.12 -m venv ~/xianyu_agent/.venv

0.3 Dependencies
    cd ~/xianyu_agent && .venv/bin/python3.12 -c "
    for p in ['requests','loguru','websockets','PIL','execjs','blackboxprotobuf','pydantic','typing_extensions']:
        __import__(p)
    "
    → If any fail: .venv/bin/pip install <package>
    → Full install line:
      .venv/bin/pip install requests loguru websockets Pillow PyExecJS blackboxprotobuf pydantic typing_extensions

0.4 Node.js (JS engine for signature generation)
    node --version
    → Expected: v24.x or similar
    → If missing: blocker "Node.js 未安装 — brew install node"

0.5 Cookie File
    ls ~/.xianyu_cookies_new.txt
    → If missing: blocker "需要扫码登录 goofish.com 后导出 cookies"
    → This step requires founder action — cannot be automated

0.6 Project Imports
    cd ~/xianyu_agent && .venv/bin/python3.12 -c "
    from goofish_apis import XianyuApis
    from goofish_live import XianyuLive
    from message import Message
    print('ALL_IMPORTS_OK')
    "
    → If any fail: check project files are intact

0.7 API Connectivity (only if cookie file exists)
    cd ~/xianyu_agent && .venv/bin/python3.12 -c "
    import os; from goofish_apis import XianyuApis
    api = XianyuApis(cookie_file=os.path.expanduser('~/.xianyu_cookies_new.txt'))
    print(api.get_login_user_info())
    "
    → Success: login user info returned → api_ready = true
    → Failure: cookies may be expired → blocker "Cookies 过期或无效，需重新导出"
```

### Health Check Output

After running the check, produce a summary:

```
api_ready: true | false
blockers: [list of failing checks]
resolved: [items fixed since last check]
```

### State File

Results persist to `~/.hermes/state/xianyu_cron_report_latest.json`:

```json
{
  "api_connected": true|false,
  "blocker_count": N,
  "blockers": [{"item": "...", "action": "...", "owner": "创始人"}],
  "resolved_since_last": [{"item": "...", "detail": "..."}],
  "infra_initialized": true|false,
  "last_run": "ISO timestamp",
  "next_run": "human readable"
}
```

Additional state files:
- `~/.hermes/xianyu_bot/config.json` — auto_reply toggle, notify chat ID, daily stats
- `~/.hermes/xianyu_bot/state.json` — messages_handled, replies_sent counters
- `~/.hermes/xianyu_bot/activity.log` — timestamped cron run log
- `~/.hermes/state/xianyu_conversations.json` — per-conversation memory (Section 1)

### Pitfalls

- **Pip externally-managed error**: Python 3.12 from Homebrew requires a virtual environment. Never use `pip install --break-system-packages`. Always install into `~/xianyu_agent/.venv/`.
- **Import path**: The project uses relative imports (`from message.types import ...`). Always `cd ~/xianyu_agent` before running Python, or `sys.path.insert(0, ...)`.
- **JS file path**: `goofish_utils.py` uses `open('static/goofish_js_version_2.js')` — only works when CWD is the project root.
- **Cookie expiration**: Xianyu cookies expire after ~7 days of inactivity. If API calls return auth errors, cookies need re-export.

---

## Execution Checklist

## Execution Checklist

When processing Xianyu messages as the agent, follow this exact order:

1. **Load state:** If `~/.hermes/state/xianyu_conversations.json` exists, load it into conversation memory.
2. **Verify connectivity (cron mode):** Run `xianyu_bot.py cron` to validate token. If it fails with a cookie-parsing error, the cookies file is likely in JSON format — convert to `key=value; key=value` (see `references/cookies-format-fix.md`).
3. **For each incoming message:**
   - [ ] Derive `conversation_id` (use native ID or `{from_user}:{item_id}`)
   - [ ] Check `is_first_contact(conversation_id)`
   - [ ] Run deal signal detection (refund keywords first, then buy keywords)
   - [ ] If refund → escalate, notify, STOP
   - [ ] If first contact → template reply, add to memory
   - [ ] If deal signal → route to quote/close, notify BD
   - [ ] Otherwise → follow-up reply, add to memory
   - [ ] Append turn to conversation memory (max 20)
3. **Save state:** Write conversation memory to `~/.hermes/state/xianyu_conversations.json`.
4. **Wait:** 30 seconds before next poll cycle.

## Setup Prerequisites（三项前置条件）

闲鱼自动化必须先满足以下三项，缺一不可：

### ① Python 3.12+
```bash
brew install python@3.12
```
系统自带 Python 3.9 不满足 xianyu_bot.py 的 asyncio 要求。

### ② XianYuApis 项目
```bash
cd ~ && git clone <XianYuApis仓库URL> xianyu_agent
```
必须包含：`message/types.py`、`static/goofish_js_version_2.js`（20KB）、`utils/goofish_utils.py`、`utils/build_cookies.py`。

### ③ 闲鱼 Cookies（17个关键字段）
从浏览器登录 goofish.com 后导出，保存到 `~/.xianyu_cookies_new.txt`（JSON格式）：

```json
{
  "_m_h5_tk": "...",
  "_m_h5_tk_enc": "...",
  "_tb_token_": "...",
  "cookie2": "...",
  "csg": "...",
  "mtop_partitioned_detect": "1",
  "sgcookie": "...",
  "t": "...",
  "tfstk": "...",
  "tracknick": "...",
  "unb": "...",
  "xlly_s": "1",
  "_samesite_flag_": "true",
  "havana_lgc_exp": "...",
  "havana_lgc2_77": "...",
  "sdkSilent": "...",
  "vn_lgc_77": "..."
}
```

**Cookie 刷新机制**：goofish_apis.py 自动处理 `_m_h5_tk` 刷新和签名生成（`generate_sign()`），不需要手动更新。

**自动生成**：`utils/build_cookies.py` 可生成基础 Cookie（不需要浏览器），但需要 Node.js 环境运行 `gen_tfstk.js`。

---

## Example: Full Message Processing

**Input message:**
```json
{
  "msg_id": "msg_001",
  "from_user": "buyer_zhang",
  "to_user": "seller_molin",
  "content": "这个最低多少钱？能包邮吗",
  "item_id": "item_8823",
  "item_title": "索尼 WH-1000XM5 头戴式降噪耳机 95新",
  "conversation_id": "conv_zhang_8823"
}
```

**Pipeline execution:**
1. `conv_id = "conv_zhang_8823"`
2. `is_first_contact("conv_zhang_8823")` → `True`
3. DealSignal detection:
   - Check refund keywords → no match
   - Check buy keywords: `"最低多少"` ✓, `"多少钱"` ✓, `"包邮吗"` ✓
   - Result: `{ detected: true, signal_type: "purchase_intent", confidence: 0.75, suggested_action: "quote_or_close" }`
4. Pipeline dispatch:
   - Not refund → skip Step 1
   - **IS first contact** → Step 2 fires first
   - Output: `{ action: "first_respond", suggested_reply: "你好，关于「索尼 WH-1000XM5 头戴式降噪耳机 95新」有什么可以帮你的？\n可以直接告诉我你的需求，我会尽快回复～" }`
5. Add buyer turn to memory: `{ role: "buyer", content: "这个最低多少钱？能包邮吗", time: ... }`
6. Add system reply to memory: `{ role: "system", content: "你好，关于「索尼 WH-1000XM5...」...", time: ... }`

**Note:** First contact takes priority over deal signal in the pipeline. The deal signal is still logged/published so BD is aware, but the first reply goes out immediately. On the **next** message from the same buyer, the deal signal pipeline (Step 3) will fire since it's no longer first contact.

---

## 7. CRON PATROL REPORT — 巡检卡片输出

When running as a cron job, the final output MUST be a patrol report card following the `feishu-message-formatter` cron template. The system delivers this to the automation control group.

### Required Format

See `references/patrol-report-template.md` for the exact template and compliance rules.

Key rules:
- No Markdown syntax (no `#`, `**`, tables, `[links]`, code blocks)
- Use `━━━` card separators with emoji section headers
- `•` bullet lists only
- `⚠️` section only present when blockers exist — omit entirely if none
- `✅` section lists everything that's working correctly
- Empty values: write `0` or `暂无`, never `N/A`
- Total card length: ≤20 lines
- If API is not ready (blocked), `📊 本轮结果` shows all zeros

### Patrol Card Template

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🐟 闲鱼状态巡检 · M月D日 HH:MM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 本轮结果
• 新消息：N 条
• 自动回复：N 条
• 成交信号：N 条
• 待审批：N 条

⚠️ 需关注
• 阻塞项 — 操作建议（需创始人处理）

✅ 已就绪/正常运行
• 状态项
• 状态项

🔜 下次巡检：时间

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### State Files Updated

| File | Content |
|------|---------|
| `~/.hermes/state/xianyu_cron_report_latest.json` | Full structured report (api_connected, blockers, resolved, stats) |
| `~/.hermes/xianyu_bot/activity.log` | Appended timestamped log line |
| `~/.hermes/xianyu_bot/state.json` | Cumulative counters (messages_handled, replies_sent) |
## 6. CRON MODE VS WEBSOCKET MODE — 两种运行模式

闲鱼消息系统有两种截然不同的运行模式，混用会导致功能缺失。

### WebSocket 模式（实时处理）

消息通过 WebSocket 长连接实时推送。这是**唯一能真正检测和回复消息**的模式。

```
启动: cd ~/xianyu_agent && python3.12 bots/xianyu_bot.py ws
特点: 常驻进程，断线自动重连，AI 自动回复（千问 qwen-plus）
消息流: WebSocket (/s/chat) → 飞书通知 → AI 生成回复 → WebSocket 发回闲鱼
```

**WebSocket 模式功能：**
- 实时检测买家新消息
- AI 自动回复（千问 qwen-plus，扮演卖家宋玉）
- 飞书通知（卡片+文本）
- 自动 Token 刷新（每 600 秒）
- 断线自动重连

### Cron 模式（健康检查）

Cron 只能检查 API 连通性和运行状态。**不能拉取未读消息**，因为闲鱼 REST API 不提供消息端点（所有 `/imweb/im/*` 路径返回 404）。

```
cron 调用: python3.12 bots/xianyu_bot.py cron
功能: Token 验证 + 状态汇报
限制: 无消息检测能力，无自动回复能力
```

**Cron 巡检报告格式**（遵循 feishu-message-formatter）：
- 统计项：新消息数、自动回复数、成交信号数、待审批数
- 状态项：API 连通、Cookies 有效、WS 监听状态、依赖状态
- 当 WS 监听未运行时必须标注 ⚠️ 阻塞项

### 治理级别映射

| 操作 | 级别 | 说明 |
|------|------|------|
| AI 自动回复（正常消息） | L0 自动 | 千问生成回复，直接通过 WS 发回闲鱼 |
| 首次联系通知 | L1 通知 | 发送飞书卡片告知有新买家 |
| 成交信号 / BD 报价 | L2 审批 | 需要老板确认价格/承诺后报价 |
| 退款/投诉 | L2 审批 | 绝不自动回复，上报等待老板决策 |
| 涉及真实现金/支付 | L4 禁止 | 直接拒绝 |

---

## 7. DEPENDENCIES — 环境依赖

运行 xianyu_bot.py 需要以下 Python 包（Python 3.12+）：

```
# 核心依赖
pip install --break-system-packages \
    websockets \
    requests \
    pydantic \
    blackboxprotobuf \
    typing_extensions

# pyexecjs 运行环境需要 Node.js（用于闲鱼签名算法）
# goofish_js_version_2.js 需放在 xianyu_agent/static/ 目录
```

**常见缺失修复：**
```bash
pip3.12 install --break-system-packages blackboxprotobuf pydantic typing_extensions
```

---

## 8. PITFALLS — 常见坑

| 坑 | 现象 | 解决 |
|----|------|------|
| **REST API 无消息端点** | 任何 `/imweb/im/*` GET 请求返回 404 | 消息只能通过 WebSocket 获取，不能用 REST 轮询 |
| **cron 误以为能检测消息** | Cron 报告新消息始终为 0 | Cron 仅是健康检查，消息检测必须启动 WS 模式 |
| **WS 监听未运行** | 状态文件 `messages_handled=0` 持续不变 | `python3.12 bots/xianyu_bot.py ws` 启动监听 |
| **`ModuleNotFoundError: blackboxprotobuf`** | 导入 goofish_utils 时报错 | 安装缺失依赖（见 Section 7） |
| **`ModuleNotFoundError: pydantic`** | 导入 goofish_apis 时报错 | `pip3.12 install --break-system-packages pydantic` |
| **Cookies JSON 格式** | `trans_cookies()` 要求 `key=value; key=value` 格式 | 如果 cookies 存为 JSON，需先转换为分号分隔格式 |
| **Token 过期** | API 返回非 SUCCESS 状态 | 重新扫码登录获取新的 cookies |

---

## Reference: Production Integration

实际的闲鱼自动化实现位于：

| 文件 | 用途 |
|------|------|
| `~/Molin-OS/bots/xianyu_bot.py` | 主机器人：WS 监听 + 飞书通知 + AI 自动回复 + cron 检测 |
| `~/Molin-OS/bots/xianyu_enhanced.py` | 增强模块：浏览触达 + 催评 + 动态定价 + 仪表盘 |
| `~/Molin-OS/molib/xianyu/xianyu_helper.py` | 闲鱼工具：千问 AI + 图片生成 + 发布商品 |
| `~/Molin-OS/molib/publish/xianyu.py` | 发布管线 |
| `~/xianyu_agent/` | goofish SDK 目录（goofish_apis, utils, message） |

状态文件位置：
- `~/.hermes/xianyu_bot/state.json` — 消息处理统计
- `~/.hermes/xianyu_bot/config.json` — 飞书通知配置
- `~/.hermes/xianyu_bot/activity.log` — 运行日志
- `~/.hermes/xianyu_bot/cookies.json` — Cookies 缓存
- `~/.hermes/state/xianyu_cron_report_latest.json` — 最新 cron 巡检报告
- `~/.xianyu_cookies_new.txt` — 闲鱼登录 Cookies

The production bot scripts live at `~/.hermes/molin/bots/xianyu_bot.py` (WebSocket listener) and `xianyu_enhanced.py` (CH5 enhancements). See `references/setup.md` for full installation guide.
