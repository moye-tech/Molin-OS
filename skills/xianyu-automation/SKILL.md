---
name: xianyu-automation
description: Xianyu (闲鱼) second-hand marketplace automation — message polling, deal-signal
  detection, and buyer conversation pipeline. Use when managing Xianyu seller conversations,
  detecting purchase/refund intent, processing incoming messages, or setting up automated
  reply workflows.
version: 1.0.0
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

---
name: xianyu-automation
description: "Manage Xianyu seller conversations with an automated message pipeline: conversation memory, deal-signal detection (30+ keywords), first-contact templates, and refund escalation. Based on Molin's XianyuListener v6.6 architecture."
---

## Xianyu Automation — 闲鱼接单自动化

### 🔗 SOUL_SIDE.md 身份对齐

此 skill 是 **side Agent** (SOUL_SIDE.md) 的执行层。每次处理消息时必须参考以下锚点：

**定价体系**（报价时自动参考）:
  - AI Agent定制: 500-2000, 3-7天
  - Prompt工程优化: 200-800, 1-3天
  - RAG知识库搭建: 800-3000, 5-14天
  - 自动化流程设计: 300-1500, 2-7天
  - 数据爬取清洗: 200-600, 1-3天

**消息分级 & 通知规则**:
  - L0 (普通询价) → 自动回复（3分钟内）
  - L1 (有成交意向, purchase_intent detected) → 飞书通知墨烨
  - L2 (报价 > 1000) → T2审批卡, 确认后发报价
  - 退款/纠纷 (refund_request) → 立刻上报, 不自动处理

**订单管理**: 使用 order_manager.py 记录每笔成交/线索
  cd scripts/
  python3 order_manager.py add <平台> <产品类型> <价格> [状态]
  python3 order_manager.py stats
  python3 order_manager.py lead <平台> <用户> <内容> [意向等级]
  python3 order_manager.py list [状态]

**记忆同步**: 每次处理完消息后自动执行
  python3 scripts/memory_sync.py --store "lead/用户"="内容" "order/状态"="xxx"
  双通道: SupeMemory (容器: hermes-side) + Obsidian (agent-outputs/side/)

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

#### Step 3: Deal Signal — Quote/Close (L1/L2 分级)

```json
{
  "action": "quote_or_close",
  "conversation_id": "...",
  "deal_signal": "purchase_intent",
  "confidence": 0.75,
  "needs_bd_quote": true,
  "level": "L1"  // 或 "L2" 按报价金额
}
```

**处理流程:**
1. 识别产品类型 (从对话上下文推断 → AI Agent定制/Prompt优化/RAG知识库/自动化流程/数据爬取)
2. 对照定价表给出报价范围
3. 若报价 > ¥1000 → 标记为 L2，生成审批卡等待确认
4. 若报价 ≤ ¥1000 → 标记为 L1，通知墨烨有成交意向
5. **自动记录线索**: `python3 order_manager.py lead <平台> <用户> <内容> <意向等级>`
6. 报价确认后 → `python3 order_manager.py add <平台> <产品> <价格> pending`

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

### Notification Triggers (对齐 SOUL_SIDE.md L0/L1/L2 分级)

  - 退款 (needs_approval) →  紧急, Feishu 通知墨烨, 优先级 HIGH
  - L2 (deal_signal + 报价>1000) →  生成审批卡等待确认, 优先级 MEDIUM
  - L1 (deal_signal + 报价<=1000) →  Feishu 通知墨烨有成交意向, 优先级 MEDIUM
  - L0 (first contact) →  自动回复模板，仅日志, 优先级 LOW

### State Persistence

In production, conversation memory lives in-memory during the listener's lifecycle. For agent usage:
- Track conversations in the current session's working memory
- If a session spans many conversations, persist to a JSON file at `~/.hermes/state/xianyu_conversations.json`
- Reload on session start if the file exists

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

## Reference: Production Integration

This skill is derived from `/integrations/xianyu/listener.py` in the Molin AI Intelligent System. In production:
- Messages are queued via **Redis** (`xianyu:incoming_queue` and `xianyu:processed` pub/sub)
- The listener runs as an **async coroutine** with `asyncio.sleep(30)`
- The `XianyuListener` class is a **singleton** accessed via `get_xianyu_listener()`
- Logging uses **loguru** at INFO/ERROR levels

For the agent, these are replaced with equivalent in-session patterns (described in Section 5) without requiring Redis or async infrastructure.