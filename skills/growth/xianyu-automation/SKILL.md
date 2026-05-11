---
name: xianyu-automation
description: Xianyu (闲鱼) second-hand marketplace automation — message polling, deal-signal
  detection, buyer conversation pipeline, and cron health patrol with listener restart.
  Use when managing Xianyu seller conversations, detecting purchase/refund intent,
  processing incoming messages, running scheduled patrol inspections, or setting up
  automated reply workflows.
version: 1.1.0
tags:
- xianyu
- xianyu
- ecommerce
- automation
- second-hand-market
- deal-detection
- message-pipeline
category: productivity
source: molin-ai-intelligent-system/integrations/xianyu/listener.py (v6.6)
metadata:
  hermes:
    molin_owner: 墨商销售（闲鱼实业）
min_hermes_version: 0.13.0
---

## Xianyu Automation — 闲鱼接单自动化

### Overview

This skill encodes the Molin XianyuListener v6.6 architecture as an agent-executable workflow. You act as the Xianyu message-processing pipeline: poll for incoming messages, maintain per-conversation memory, detect buy/refund signals in buyer messages, and route each message through the appropriate response pipeline.

The core loop mirrors the production listener: poll → detect → route → notify. Every message is classified into one of four pipelines based on signal detection and conversation state.

### When to Use

- User asks you to process incoming Xianyu buyer messages
- User needs deal-signal detection on buyer chat messages
- User wants automated first-contact replies for Xianyu listings
- User asks to set up message polling with 30-second intervals
- User needs refund/escalation detection in buyer conversations
- User wants a structured conversation memory across multi-turn chats
- **Cron patrol**: running scheduled health checks on the Xianyu message pipeline

**Don't use for:** Other marketplace platforms (Taobao, JD, Pinduoduo have different message formats). Don't use for outbound marketing campaigns — this is an inbound message handler.

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

## 5. AUTOMATION PATTERN — 轮询自动化模式

### Polling Loop (30-second interval)

```
WHILE running:
    1. Pop next message from incoming queue (xianyu:incoming_queue)
    2. If message exists:
        a. Parse into XianyuMessage { msg_id, from_user, to_user, content, item_id, item_title, timestamp, conversation_id }
        b. Run process_message(msg) → get result dict
        c. Publish result to processed queue (xianyu:processed)
        d. If result.needs_approval or result.needs_bd_quote:
            → Send Feishu/Lark notification to operator
    3. Sleep 30 seconds
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

### State Persistence

In production, conversation memory lives in-memory during the listener's lifecycle. For agent usage:
- Track conversations in the current session's working memory
- If a session spans many conversations, persist to a JSON file at `~/.hermes/state/xianyu_conversations.json`
- Reload on session start if the file exists

---

## 6. CRON PATROL — 定时巡检与自动恢复

The cron patrol job runs periodically to verify the health of the Xianyu message pipeline. Unlike the polling loop (Section 5) which handles individual messages, the patrol handles **infrastructure health** — detecting hung processes, token expiry, and silent failures.

See `references/diagnostic-commands.md` for copy-pasteable command recipes.

### Patrol Checklist (execute in order)

```
1. API HEALTH CHECK
   python /Users/moye/.hermes/scripts/xianyu_check.py
   → If token_ok=false → classify error (see below), attempt recovery
   → If token_ok=true → proceed

2. LISTENER LIVENESS CHECK
   Read ~/.hermes/xianyu_bot/state.json → ws_listener_pid
   Then THREE checks on that PID:
     a. ps -p <pid> → is process alive?
     b. lsof -p <pid> -a -i → are there open network sockets?
     c. tail ws.log → last log entry within last 5 minutes?

   ALL THREE must pass. If process is alive but has NO sockets
   and no recent log entries → FAKE-ALIVE (hung). Kill and restart.

3. MESSAGE STATS
   Read state.json for messages_handled, replies_sent
   Check for deal signals and pending approvals

4. RECOVER if needed (see Recovery Procedures below)
```

### Key File Paths

| File | Purpose |
|------|---------|
| `~/.hermes/scripts/xianyu_check.py` | API health check (uses xianyu venv + TLS 1.2 fix) |
| `~/.hermes/xianyu_bot/ws_listener.py` | WebSocket listener entry point |
| `~/.hermes/xianyu_bot/ws.log` | Listener runtime log |
| `~/.hermes/xianyu_bot/state.json` | Current state (pid, stats, last activity) |
| `~/.hermes/xianyu_bot/activity.log` | Historical patrol results |
| `~/.hermes/xianyu_bot/cookies.json` | Xianyu session cookies |

### Correct Venv

The xianyu scripts MUST use the xianyu venv with TLS 1.2 fix:
```
/Users/moye/Molin-OS/molib/xianyu/.venv/bin/python3
```

The default Hermes venv may work for API calls but the TLS fix is in the xianyu venv. Always prefer it when restarting the listener.

### Error Classification

| API Response | Meaning | Action |
|-------------|---------|--------|
| `FAIL_SYS_USER_VALIDATE` + `被挤爆啦` | Server-side rate limit or outage | Wait 5 min, retry. If persists >1h → escalate to manual cookie refresh |
| `FAIL_SYS_USER_VALIDATE` alone | Token/cookie expired | Manual re-login needed — notify operator |
| SSL/TLS errors (`SSLEOFError`, `UNEXPECTED_EOF`) | TLS version mismatch | Ensure xianyu venv is used |

### Recovery Procedures

**Restart hung listener:**
```bash
# Kill the old PID
kill <old_pid> 2>/dev/null; sleep 1

# Start new listener with correct venv (use terminal background=true)
cd /Users/moye/Molin-OS/molib/xianyu
/Users/moye/Molin-OS/molib/xianyu/.venv/bin/python3 \
  /Users/moye/.hermes/xianyu_bot/ws_listener.py

# Verify after 5 seconds:
lsof -p <new_pid> -a -i          # must show open sockets
tail -3 ~/.hermes/xianyu_bot/ws.log   # must show "Token OK"
```

**Token validation failure loop:**
The ws_listener.py has NO retry logic — it calls `sys.exit(1)` immediately
on `FAIL_SYS_USER_VALIDATE`. If restart keeps failing:
1. Run xianyu_check.py every 60 seconds for up to 5 attempts
2. If all fail: the pipeline is DOWN. Log to activity.log and notify operator
3. If any succeed: restart the listener immediately

### Cron Output Format

Patrol results follow the feishu-message-formatter cron card template:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [status emoji] 闲鱼巡检 · YYYY-MM-DD HH:MM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 本轮结果
• API Token：状态
• WebSocket：状态（PID、连接情况）
• 消息处理：N 条
• 自动回复：N 条
• 成交信号：N 条
• 待审批项：N 条

⚠️ 需关注（only if issues exist）
• 事项 — 简述 + 操作建议

✅ 已自动完成
• 项目1
• 项目2

🔜 建议操作（only if manual action needed）
• 步骤

[if error] ❌ 简述，原因：一句话
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Key rules for cron output:
- NEVER use Markdown tables/headers/bold/code blocks
- Use separator lines + emoji sections + bullet lists
- "Fake-alive" listener → flag as alert, not silent
- Token invalid → flag as error with suggested next action
- If genuinely nothing new AND system healthy → respond `[SILENT]`

---

## Pitfalls

### Fake-Alive WebSocket Listener
The most dangerous failure mode: `ps` shows the process running, but it has
no open network sockets and no recent log entries. The process appears healthy
but is completely non-functional.

**Detection:** `lsof -p <pid> -a -i` returns empty output
**Cause:** WebSocket silently disconnected without triggering the reconnect loop;
           the asyncio event loop is stuck or the connection was dropped by the OS
**Fix:** Kill and restart the listener (see Section 6 Recovery)
**Real case:** 2026-05-11, PID 79907 ran for ~2h with zero sockets. ws.log
              showed last entry "初始化完成: None" at 10:50, then silence.

### ws_listener.py Has No Retry Logic
The listener calls `sys.exit(1)` immediately when `api.get_token()` returns
anything other than `SUCCESS`. This means any transient server error
(rate limit, "被挤爆啦") kills the process instantly with no retry.

**Workaround:** The cron patrol must handle the restart loop. If the listener
               exits, the patrol retries from xianyu_check.py first.
**Future fix:** Add exponential backoff retry to ws_listener.py main()

### Token Degradation Window
The API token can validate successfully at one moment and fail minutes later.
The "被挤爆啦" (server overloaded) error uses the same `FAIL_SYS_USER_VALIDATE`
code as real token expiry. Always distinguish by checking for "被挤爆啦" in the
error message — server overload recovers on its own; real expiry needs manual
cookie refresh.

### Wrong Venv = TLS Failures
The xianyu module requires custom TLS 1.2 patches in its venv. Using any other
Python (including the Hermes venv) may work sporadically but will eventually
hit `SSLEOFError` / `UNEXPECTED_EOF_WHILE_READING` errors on Xianyu's API.

---

## 6. CRON HEALTH CHECK — 定时巡检诊断

The cron job (schedule: `15,45 9-21 * * *`, cron_id: `1a6bd56a00cc`) runs a health check every 30 minutes during business hours. This section documents the diagnostic workflow for when the agent is invoked as a cron task.

### Diagnostic Script

Run the token check script in its own venv (TLS 1.2 fix):

```
/Users/moye/Molin-OS/molib/xianyu/.venv/bin/python3 /Users/moye/.hermes/scripts/xianyu_check.py
```

Output JSON: `{"status": "ok|token_invalid|api_error|no_cookies", "token_ok": bool, "cookies_ok": bool, "error": null|string}`

### WebSocket Listener Health Check

The WebSocket listener runs as a persistent process. Key diagnostic commands:

```bash
# 1. Check if process exists
ps aux | grep ws_listener.py | grep -v grep

# 2. Check TCP connections (process may be alive but log silent)
lsof -p <pid> 2>/dev/null | grep -i tcp
```

**CRITICAL PITFALL:** A silent ws.log does NOT mean the listener is dead. The log only writes on connect/disconnect/error events. If the WebSocket is stable with no messages, the log will be silent. Always verify with `lsof` for ESTABLISHED TCP before concluding the listener is down.

**Log file:** `~/.hermes/xianyu_bot/ws.log` — last modified timestamp is the best proxy for "last activity" when no log entries exist.

### Key File Locations

| File | Purpose |
|------|---------|
| `~/.hermes/scripts/xianyu_check.py` | Token/cookie validation script |
| `~/.hermes/xianyu_bot/config.json` | Notification chat_id, auto_reply toggle |
| `~/.hermes/xianyu_bot/state.json` | Listener PID, messages handled, replies sent |
| `~/.hermes/xianyu_bot/ws.log` | WebSocket connect/disconnect/error log |
| `~/.hermes/xianyu_bot/activity.log` | Cron execution history (append-only) |
| `~/.hermes/xianyu_bot/cookies.json` | Xianyu session cookies (17 fields) |
| `~/.hermes/state/xianyu_cron_report_latest.json` | Latest cron report snapshot |
| `~/.hermes/state/xianyu_conversations.json` | Conversation memory (if exists) |
| `~/.hermes/state/xianyu_setup_checklist.md` | One-time setup blockers |

### Cron Card Output

Use `CardBuilder` (blue, `"📋 闲鱼消息巡检 · {datetime}"`) with sections: API余额 → Token状态 → WebSocket监听 → 新消息处理 → 成交信号 → 巡检结论. Each section separated by `add_hr()`. Footer via `add_note()` with next execution time.

Send to: `oc_94c87f141e118b68c2da9852bf2f3bda`

**Iron rule:** After `FeishuCardSender.send_card()`, final response MUST be empty or a single emoji (suppressed double-delivery sentinel). The cron scheduler's text-delivery pipe must not fire.

### Balance Check

DeepSeek balance via `curl -s https://api.deepseek.com/user/balance -H "Authorization: Bearer $DEEPSEEK_API_KEY"` (key from `~/.hermes/.env`). Alert threshold: < ¥50.

### State Update

After each cron run, update:
1. `~/.hermes/state/xianyu_cron_report_latest.json` — full snapshot
2. `~/.hermes/xianyu_bot/activity.log` — append one-line summary `[timestamp] [CRON] 巡检完成 | ...`

---

## Execution Checklist

When processing Xianyu messages as the agent, follow this exact order:

1. **Load state:** If `~/.hermes/state/xianyu_conversations.json` exists, load it into conversation memory.
2. **For each incoming message:**
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

## 6. CRON PATROL — 定时巡检

When running as a scheduled cron job (not interactive user session), perform a health-check patrol rather than the full message-processing loop. The listener handles real-time messages; the cron job's job is to ensure the listener is alive and report status.

### Patrol Workflow

```
1. TOKEN CHECK → python ~/.hermes/scripts/xianyu_check.py
2. PROCESS CHECK → ps aux | grep ws_listener
3. LOG CHECK → tail ws.log for last-5-min activity
4. STATE READ → read state.json + activity.log
5. HEAL → restart listener if dead (token must be ok first)
6. REPORT → generate patrol card per feishu-message-formatter
```

### Step 1: Token Check

Run the dedicated check script (uses xianyu venv with TLS 1.2 fix):
```bash
python ~/.hermes/scripts/xianyu_check.py
```
Returns `{"status": "ok", "token_ok": true/false, ...}`.

**If token_ok=false:** Do NOT attempt restart. Report API异常 and stop.

### Step 2: Process Check

```bash
ps aux | grep -i ws_listener | grep -v grep
```
If no process found → listener is DOWN.

### Step 3: Log Check

```bash
stat -f%m ~/.hermes/xianyu_bot/ws.log  # last modification timestamp
```
If last modification > 5 minutes ago → listener is STALE (may be hung).

### Step 4: State Read

Key files:
| File | Content |
|------|---------|
| `~/.hermes/xianyu_bot/state.json` | ws_listener_pid, ws_connected, api_status, messages_handled, replies_sent |
| `~/.hermes/xianyu_bot/activity.log` | Historical cron patrol entries |
| `~/.hermes/xianyu_bot/ws.log` | WebSocket listener runtime log |

### Step 5: Restart Listener

**CRITICAL — must use correct working directory.** The script imports from `goofish_apis` which internally opens `static/goofish_js_version_2.js` via relative path. The working directory MUST be:

```
/Users/moye/Molin-OS/molib/xianyu/
```

Correct restart command:
```bash
# Use terminal(background=true) — never nohup/disown/setsid
cd /Users/moye/Molin-OS/molib/xianyu && python /Users/moye/.hermes/xianyu_bot/ws_listener.py
```

**Pitfall:** `nohup`, `disown`, and `setsid` are REJECTED by Hermes terminal tool. Always use `terminal(background=true)` for persistent processes.

After starting, wait 5 seconds then check ws.log for:
```
✅ WebSocket 已连接
初始化完成
```

If the process exits immediately with `FileNotFoundError: static/goofish_js_version_2.js` → wrong working directory.

### Step 6: Update State Files

After successful restart, update:
- `state.json` — set pid, ws_connected=true, api_status="ok"
- `activity.log` — append cron entry
- `~/.hermes/state/xianyu_cron_report_latest.json` — full patrol report

### Known Error Patterns

| Error | Symptom | Cause | Recovery |
|-------|---------|-------|----------|
| **"被挤爆啦"** | `FAIL_SYS_USER_VALIDATE` / `RGV587_ERROR::SM::哎哟喂,被挤爆啦,请稍后重试` | Xianyu server congestion | Auto-recovers within 1-2 hours. Token check script will report `token_ok=true` when server clears. Restart listener after recovery. |
| **SSL EOF** | `SSLEOFError: EOF occurred in violation of protocol` | TLS mismatch | Use `xianyu_check.py` (has TLS 1.2 fix). If persists, cookies may need refresh. |
| **ws_listener FileNotFoundError** | `static/goofish_js_version_2.js` not found | Wrong working directory | Must run from `Molin-OS/molib/xianyu/` |
| **Token expired** | `token_ok=false` persistently | Cookies stale (>7 days) | Escalate to user: re-login on Xianyu web, export cookies to `cookies.json` |

### Patrol Card Output

Follow `feishu-message-formatter` cron template exactly (Section "Cron 报告卡片"). Key fields:
- API Token status
- WebSocket listener PID + connection time
- Messages/replies/deal-signals/escalations count
- ⚠️ section for anomalies (if any)
- ✅ section for auto-resolved items
- 🔜 next execution time

**When nothing to report (all green, zero messages):** Still generate the card — silence is itself a signal that monitoring is alive.

See `references/cron-patrol-example.md` for a worked example with the "被挤爆啦" recovery pattern.

---

## Reference: Production Integration

This skill is derived from `/integrations/xianyu/listener.py` in the Molin AI Intelligent System. In production:
- Messages are queued via **Redis** (`xianyu:incoming_queue` and `xianyu:processed` pub/sub)
- The listener runs as an **async coroutine** with `asyncio.sleep(30)`
- The `XianyuListener` class is a **singleton** accessed via `get_xianyu_listener()`
- Logging uses **loguru** at INFO/ERROR levels

For the agent, these are replaced with equivalent in-session patterns (described in Section 5) without requiring Redis or async infrastructure.

## Pitfalls & Known Limitations

### goofish_apis has no search_items method
`XianyuApis` only supports token verification and message operations — there is NO `search_items()` or similar keyword-search method. Do not attempt to use it for product/price discovery. For competitive pricing research, use `web_search` or `Scrapling` as fallbacks.

### molib intel trending is not production-ready
`python -m molib intel trending` returns "功能仍在建设中". Use `web_search` for trending data instead.

### Pricing data is directional, not real-time
Web search results provide price bands (low/median/high), not exact competitor quotes. This is sufficient for trend detection and anomaly flagging, but not for order-book pricing decisions.