"""
墨麟AI思维链卡片 v1.0
CEO 推理过程实时可视化，独立于正文回复
特性：
  - 首次发送即建立卡片，后续 patch 更新（不产生新消息）
  - 完成后自动折叠，提供「展开」按钮
"""
import json, time
from typing import List, Optional, Dict, Any
from loguru import logger
import httpx
from molib.integrations.feishu.token_manager import get_feishu_token

# ── 思维链步骤定义 ───────────────────────────────────────────────
CEO_THINKING_STEPS = [
    ("intent",    "意图识别",   "理解用户真实诉求"),
    ("decompose", "任务拆解",   "拆分为可执行子任务"),
    ("route",     "调度决策",   "选择最优子公司组合"),
    ("cost",      "成本预估",   "ROI评估与预算检查"),
    ("dispatch",  "并发分发",   "下发子任务给各Worker"),
    ("monitor",   "执行监控",   "实时监控各子公司进度"),
    ("review",    "质量审查",   "LLM门控评分与重试"),
    ("synthesize","CEO综合",    "整合生成最终回复"),
]

STEP_ICONS = {
    "pending": "⏳",
    "active":  "🔄",
    "done":    "✅",
    "error":   "❌",
    "skip":    "⏭️",
}


def _build_thinking_card(
    task_id: str,
    steps: List[Dict],
    is_done: bool = False,
    summary: str = "",
    cost_cny: float = 0,
    elapsed: float = 0,
) -> Dict[str, Any]:
    """构建思维链飞书交互卡片"""

    active_idx = next((i for i, s in enumerate(steps) if s["status"] == "active"), -1)
    done_count = sum(1 for s in steps if s["status"] == "done")

    # 标题
    if is_done:
        title = f"✅ 推理完成 · {int(elapsed)}s · ¥{cost_cny:.4f}"
        template = "green"
    else:
        current_name = steps[active_idx]["name"] if active_idx >= 0 else "启动中"
        title = f"🧠 CEO推理中 · {current_name} ({done_count}/{len(steps)})"
        template = "blue"

    # 步骤列表（lark_md 格式）
    lines = []
    for s in steps:
        icon = STEP_ICONS.get(s["status"], "⏳")
        detail = f" — {s['detail']}" if s.get("detail") else ""
        bold = "**" if s["status"] == "active" else ""
        lines.append(f"{icon} {bold}{s['name']}{bold}{detail}")

    elements = [
        {"tag": "div", "text": {"tag": "lark_md", "content": "\n".join(lines)}},
        {"tag": "hr"},
    ]

    if is_done and summary:
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**📌 决策摘要：** {summary}"}})

    elements.append({"tag": "note", "elements": [{
        "tag": "plain_text",
        "content": f"推理链 · ID:{task_id[-8:]} · {time.strftime('%H:%M:%S')}"
    }]})

    return {
        "config": {"wide_screen_mode": True, "update_multi": True},
        "header": {"title": {"tag": "plain_text", "content": title}, "template": template},
        "elements": elements,
    }


class ThinkingCardManager:
    """管理单次任务的思维链卡片生命周期"""

    def __init__(self, chat_id: str, task_id: str):
        self.chat_id = chat_id
        self.task_id = task_id
        self.message_id: Optional[str] = None
        self.started_at = time.time()
        self.steps = [
            {"key": k, "name": n, "desc": d, "status": "pending", "detail": ""}
            for k, n, d in CEO_THINKING_STEPS
        ]

    async def start(self):
        """发送初始思维链卡片"""
        self.steps[0]["status"] = "active"
        token = await get_feishu_token()
        if not token: return
        card = _build_thinking_card(self.task_id, self.steps)
        try:
            async with httpx.AsyncClient() as cli:
                r = await cli.post(
                    "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"receive_id": self.chat_id, "msg_type": "interactive",
                          "content": json.dumps(card)},
                    timeout=10
                )
                d = r.json()
                if d.get("code") == 0:
                    self.message_id = d["data"]["message_id"]
                    logger.info(f"[ThinkingCard] 发送成功 {self.message_id[-12:]}")
        except Exception as e:
            logger.warning(f"[ThinkingCard] 发送失败: {e}")

    async def advance(self, step_key: str, detail: str = ""):
        """推进到指定步骤（上一步标记完成）"""
        for s in self.steps:
            if s["status"] == "active":
                s["status"] = "done"
            if s["key"] == step_key:
                s["status"] = "active"
                s["detail"] = detail
        await self._patch()

    async def finish(self, summary: str = "", cost_cny: float = 0):
        """任务完成，所有步骤标记完成"""
        for s in self.steps:
            if s["status"] in ("pending", "active"):
                s["status"] = "done"
        elapsed = time.time() - self.started_at
        card = _build_thinking_card(self.task_id, self.steps,
                                    is_done=True, summary=summary,
                                    cost_cny=cost_cny, elapsed=elapsed)
        await self._patch(card)

    async def _patch(self, card=None):
        if not self.message_id: return
        token = await get_feishu_token()
        if not token: return
        if card is None:
            card = _build_thinking_card(self.task_id, self.steps)
        try:
            async with httpx.AsyncClient() as cli:
                await cli.patch(
                    f"https://open.feishu.cn/open-apis/im/v1/messages/{self.message_id}",
                    headers={"Authorization": f"Bearer {token}",
                             "Content-Type": "application/json"},
                    json={"content": json.dumps(card)},
                    timeout=10
                )
        except Exception as e:
            logger.warning(f"[ThinkingCard] 更新失败: {e}")
