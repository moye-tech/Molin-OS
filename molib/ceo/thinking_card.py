"""
墨麟OS — 思维链实时卡片 & 进度条卡片
======================================
从 molin-os-ultra/integrations/feishu/ 吸收的实时卡片机制。

核心机制：
1. 首次发送卡片 → 记录 message_id
2. 后续调用 PATCH /im/v1/messages/{message_id} 更新同一卡片（不产生新消息）
3. 卡片 config 设置 "update_multi": true 支持多次更新
"""

import json
import logging
import time
import requests
from typing import Any, Optional

logger = logging.getLogger("molin.ceo.thinking_card")

# ── 思维链步骤定义 ─────────────────────────────────────
CEO_THINKING_STEPS = [
    ("intent",     "意图识别",   "理解用户真实诉求"),
    ("decompose",  "任务拆解",   "拆分为可执行子任务"),
    ("route",      "调度决策",   "选择最优子公司组合"),
    ("cost",       "成本预估",   "ROI评估与预算检查"),
    ("dispatch",   "并发分发",   "下发子任务给各Worker"),
    ("monitor",    "执行监控",   "实时监控各子公司进度"),
    ("review",     "质量审查",   "LLM门控评分与重试"),
    ("synthesize", "CEO综合",    "整合生成最终回复"),
]

STEP_ICONS = {
    "pending": "⏳",
    "active":  "🔄",
    "done":    "✅",
    "error":   "❌",
    "skip":    "⏭️",
}

# ── 进度条步骤 ─────────────────────────────────────────
PROGRESS_STEPS = [
    "🔍 意图识别",
    "📋 任务拆解",
    "🚀 派发子公司",
    "⚙️ Worker 开始执行",
    "⚙️ Worker 执行 1/3",
    "⚙️ Worker 执行 2/3",
    "⚙️ Worker 执行 3/3",
    "🔗 结果聚合",
    "🧠 CEO 综合",
    "✅ 完成",
]


def _build_thinking_card(
    steps: list[dict],
    is_done: bool = False,
    summary: str = "",
    cost_cny: float = 0,
    elapsed: float = 0,
) -> dict:
    """构建思维链飞书交互卡片"""
    active_idx = next((i for i, s in enumerate(steps) if s["status"] == "active"), -1)
    done_count = sum(1 for s in steps if s["status"] == "done")
    total = len(steps)

    if is_done:
        title = f"✅ 推理完成 · {int(elapsed)}s · ¥{cost_cny:.4f}"
        template = "green"
    else:
        current_name = steps[active_idx]["name"] if active_idx >= 0 else "启动中"
        title = f"🧠 CEO推理中 · {current_name} ({done_count}/{total})"
        template = "blue"

    lines = []
    for s in steps:
        icon = STEP_ICONS.get(s["status"], "⏳")
        detail = f" — {s['detail']}" if s.get("detail") else ""
        bold_s = "**" if s["status"] == "active" else ""
        bold_e = "**" if s["status"] == "active" else ""
        lines.append(f"{icon} {bold_s}{s['name']}{bold_e}{detail}")

    elements = [
        {"tag": "div", "text": {"tag": "lark_md", "content": "\n".join(lines)}},
        {"tag": "hr"},
    ]

    if is_done and summary:
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**📌 决策摘要：** {summary}"}})

    elements.append({"tag": "note", "elements": [{
        "tag": "plain_text",
        "content": f"推理链 · {time.strftime('%H:%M:%S')}"
    }]})

    return {
        "config": {"wide_screen_mode": True, "update_multi": True},
        "header": {"title": {"tag": "plain_text", "content": title}, "template": template},
        "elements": elements,
    }


def _build_progress_card(
    task_title: str,
    current_step: int,
    agencies: list[str] | None = None,
    step_results: dict[str, str] | None = None,
    elapsed: float = 0,
) -> dict:
    """构建进度条卡片"""
    TOTAL = len(PROGRESS_STEPS)
    cur = min(current_step, TOTAL - 1)
    pct = cur * 100 // (TOTAL - 1) if cur > 0 else 0
    pct = min(pct, 100)
    filled = min(10, pct // 10)
    bar = "█" * filled + "░" * (10 - filled)
    label = PROGRESS_STEPS[cur]
    done = cur >= TOTAL - 1
    eta_text = "即将完成" if done else f"约 {(TOTAL - cur) * 10}秒"

    agency_lines = []
    if agencies:
        for ag in agencies:
            st = (step_results or {}).get(ag, "⏳ 等待中...")
            icon = "✅" if "完成" in st or "done" in st else "⏳"
            agency_lines.append(f"{icon} **{ag}**: {st}")

    elements = [
        {"tag": "div", "text": {"tag": "lark_md",
                                "content": f"`{bar}` {pct}%\n\n当前：**{label}**\n剩余：{eta_text}"}},
        {"tag": "hr"},
    ]
    if agency_lines:
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": "\n".join(agency_lines)}})
    elements.append({"tag": "note", "elements": [
        {"tag": "plain_text", "content": f"执行进度 · {time.strftime('%H:%M:%S')}"}
    ]})

    return {
        "config": {"wide_screen_mode": True, "update_multi": True},
        "header": {
            "title": {"tag": "plain_text",
                      "content": f"⚡ 执行中 {pct}% — {task_title[:25]}" if not done else f"✅ 已完成 — {task_title[:25]}"},
            "template": "green" if done else "blue",
        },
        "elements": elements,
    }


# ── PATCH 发送工具 ──────────────────────────────────────

API_BASE = "https://open.feishu.cn/open-apis"


def _send_card(chat_id: str, card_dict: dict, token: str) -> Optional[str]:
    """发送卡片，返回 message_id"""
    try:
        r = requests.post(
            f"{API_BASE}/im/v1/messages?receive_id_type=chat_id",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"receive_id": chat_id, "msg_type": "interactive",
                  "content": json.dumps(card_dict)},
            timeout=10,
        )
        d = r.json()
        if d.get("code") == 0:
            mid = d["data"]["message_id"]
            logger.info("[ThinkingCard] 发送成功 %s", mid[-12:])
            return mid
        logger.warning("[ThinkingCard] 发送失败: %s", d)
    except Exception as e:
        logger.warning("[ThinkingCard] 发送异常: %s", e)
    return None


def _patch_card(message_id: str, card_dict: dict, token: str) -> bool:
    """PATCH 更新已有卡片（不产生新消息）"""
    try:
        r = requests.patch(
            f"{API_BASE}/im/v1/messages/{message_id}",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"content": json.dumps(card_dict)},
            timeout=10,
        )
        d = r.json()
        if d.get("code") == 0:
            logger.debug("[ThinkingCard] 更新成功 %s", message_id[-12:])
            return True
        logger.warning("[ThinkingCard] 更新失败: %s", d)
    except Exception as e:
        logger.warning("[ThinkingCard] 更新异常: %s", e)
    return False


# ── ThinkingCardManager ─────────────────────────────────

class ThinkingCardManager:
    """思维链实时卡片管理器
    使用方式：
        mgr = ThinkingCardManager(chat_id, token)
        await mgr.start()
        await mgr.advance("decompose", "拆分为3个子任务")
        ...
        await mgr.finish("策略已产出")
    """

    def __init__(self, chat_id: str, token: str):
        self.chat_id = chat_id
        self.token = token
        self.message_id: Optional[str] = None
        self.started_at = time.time()
        self.steps = [
            {"key": k, "name": n, "desc": d, "status": "pending", "detail": ""}
            for k, n, d in CEO_THINKING_STEPS
        ]

    def start(self) -> Optional[str]:
        """发送初始思维链卡片"""
        self.steps[0]["status"] = "active"
        card = _build_thinking_card(self.steps)
        mid = _send_card(self.chat_id, card, self.token)
        if mid:
            self.message_id = mid
        return mid

    def advance(self, step_key: str, detail: str = "") -> bool:
        """推进到指定步骤（上一步标记完成），返回是否更新成功"""
        for s in self.steps:
            if s["status"] == "active":
                s["status"] = "done"
            if s["key"] == step_key:
                s["status"] = "active"
                s["detail"] = detail
        return self._patch()

    def finish(self, summary: str = "", cost_cny: float = 0) -> bool:
        """任务完成，所有步骤标记完成"""
        for s in self.steps:
            if s["status"] in ("pending", "active"):
                s["status"] = "done"
        elapsed = time.time() - self.started_at
        card = _build_thinking_card(self.steps, is_done=True, summary=summary,
                                     cost_cny=cost_cny, elapsed=elapsed)
        return self._patch(card)

    def _patch(self, card: dict | None = None) -> bool:
        if not self.message_id:
            return False
        if card is None:
            card = _build_thinking_card(self.steps)
        return _patch_card(self.message_id, card, self.token)


# ── ProgressCardManager ─────────────────────────────────

class ProgressCardManager:
    """进度条卡片管理器
    使用方式：
        mgr = ProgressCardManager(chat_id, token)
        mgr.start("分析股票走势", agencies=["增长部", "研究部"])
        mgr.update(3, step_results={"增长部": "执行中...", "研究部": "完成"})
        mgr.done()
    """

    def __init__(self, chat_id: str, token: str):
        self.chat_id = chat_id
        self.token = token
        self.message_id: Optional[str] = None
        self.task_title = ""
        self.agencies: list[str] = []
        self.started_at = time.time()

    def start(self, task_title: str, agencies: list[str] | None = None) -> Optional[str]:
        """发送初始进度卡片"""
        self.task_title = task_title
        self.agencies = agencies or []
        self.started_at = time.time()
        card = _build_progress_card(task_title, 0, agencies)
        mid = _send_card(self.chat_id, card, self.token)
        if mid:
            self.message_id = mid
        return mid

    def update(self, current_step: int, step_results: dict[str, str] | None = None) -> bool:
        """更新进度条"""
        if not self.message_id:
            return False
        elapsed = time.time() - self.started_at
        card = _build_progress_card(self.task_title, current_step, self.agencies, step_results, elapsed)
        return _patch_card(self.message_id, card, self.token)

    def done(self) -> bool:
        """标记完成"""
        TOTAL = len(PROGRESS_STEPS)
        return self.update(TOTAL - 1)
