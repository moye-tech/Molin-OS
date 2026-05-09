"""墨麟OS — 思维链实时卡片

从 thinking_card.py 整合而来，提供 CEO 思维链实时卡片 & 进度条卡片。

使用方式：
    from molib.ceo.cards import ThinkingCardManager, ProgressCardManager
"""
import json
import logging
import time

from molib.ceo.cards.sender import FeishuCardSender, API_BASE

logger = logging.getLogger("molin.ceo.cards.thinking")

# ── 思维链步骤定义 ──
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


def _build_thinking_card(steps: list[dict], is_done: bool = False,
                          summary: str = "", cost_cny: float = 0, elapsed: float = 0) -> dict:
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
    elements.append({"tag": "note", "elements": [{"tag": "plain_text", "content": f"推理链 · {time.strftime('%H:%M:%S')}"}]})

    return {
        "config": {"wide_screen_mode": True, "update_multi": True},
        "header": {"title": {"tag": "plain_text", "content": title}, "template": template},
        "elements": elements,
    }


def _build_progress_card(task_title: str, current_step: int,
                          agencies: list[str] | None = None,
                          step_results: dict[str, str] | None = None, elapsed: float = 0) -> dict:
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
        {"tag": "div", "text": {"tag": "lark_md", "content": f"`{bar}` {pct}%\n\n当前：**{label}**\n剩余：{eta_text}"}},
        {"tag": "hr"},
    ]
    if agency_lines:
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": "\n".join(agency_lines)}})
    elements.append({"tag": "note", "elements": [{"tag": "plain_text", "content": f"执行进度 · {time.strftime('%H:%M:%S')}"}]})

    return {
        "config": {"wide_screen_mode": True, "update_multi": True},
        "header": {
            "title": {"tag": "plain_text",
                      "content": f"⚡ 执行中 {pct}% — {task_title[:25]}" if not done else f"✅ 已完成 — {task_title[:25]}"},
            "template": "green" if done else "blue",
        },
        "elements": elements,
    }


class ThinkingCardManager:
    """思维链实时卡片管理器"""

    def __init__(self, chat_id: str, token: str):
        self.chat_id = chat_id
        self.token = token
        self.message_id: str | None = None
        self.started_at = time.time()
        self.steps = [
            {"key": k, "name": n, "desc": d, "status": "pending", "detail": ""}
            for k, n, d in CEO_THINKING_STEPS
        ]

    def start(self) -> str | None:
        """发送初始思维链卡片"""
        self.steps[0]["status"] = "active"
        card = _build_thinking_card(self.steps)
        sender = FeishuCardSender()
        try:
            r = sender.send_card(card, self.chat_id)
            if r.get("code") == 0:
                self.message_id = r["data"]["message_id"]
                return self.message_id
        except Exception as e:
            logger.warning("[ThinkingCard] 发送异常: %s", e)
        return None

    def advance(self, step_key: str, detail: str = "") -> bool:
        """推进到指定步骤"""
        for s in self.steps:
            if s["status"] == "active":
                s["status"] = "done"
            if s["key"] == step_key:
                s["status"] = "active"
                s["detail"] = detail
        return self._patch()

    def finish(self, summary: str = "", cost_cny: float = 0) -> bool:
        """任务完成"""
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
        import requests
        try:
            token = FeishuCardSender()._get_token()
            r = requests.patch(
                f"{API_BASE}/im/v1/messages/{self.message_id}",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"content": json.dumps(card)},
                timeout=10,
            )
            d = r.json()
            if d.get("code") == 0:
                return True
            logger.warning("[ThinkingCard] 更新失败: %s", d)
        except Exception as e:
            logger.warning("[ThinkingCard] 更新异常: %s", e)
        return False


class ProgressCardManager:
    """进度条卡片管理器"""

    def __init__(self, chat_id: str, token: str):
        self.chat_id = chat_id
        self.token = token
        self.message_id: str | None = None
        self.task_title = ""
        self.agencies: list[str] = []
        self.started_at = time.time()

    def start(self, task_title: str, agencies: list[str] | None = None) -> str | None:
        """发送初始进度卡片"""
        self.task_title = task_title
        self.agencies = agencies or []
        self.started_at = time.time()
        card = _build_progress_card(task_title, 0, agencies)
        sender = FeishuCardSender()
        try:
            r = sender.send_card(card, self.chat_id)
            if r.get("code") == 0:
                self.message_id = r["data"]["message_id"]
                return self.message_id
        except Exception as e:
            logger.warning("[ProgressCard] 发送异常: %s", e)
        return None

    def update(self, current_step: int, step_results: dict[str, str] | None = None) -> bool:
        """更新进度条"""
        if not self.message_id:
            return False
        elapsed = time.time() - self.started_at
        card = _build_progress_card(self.task_title, current_step, self.agencies, step_results, elapsed)
        import requests
        try:
            token = FeishuCardSender()._get_token()
            r = requests.patch(
                f"{API_BASE}/im/v1/messages/{self.message_id}",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"content": json.dumps(card)},
                timeout=10,
            )
            return r.json().get("code") == 0
        except Exception as e:
            logger.warning("[ProgressCard] 更新异常: %s", e)
            return False

    def done(self) -> bool:
        TOTAL = len(PROGRESS_STEPS)
        return self.update(TOTAL - 1)


__all__ = [
    "ThinkingCardManager",
    "ProgressCardManager",
    "CEO_THINKING_STEPS",
    "STEP_ICONS",
    "PROGRESS_STEPS",
]
