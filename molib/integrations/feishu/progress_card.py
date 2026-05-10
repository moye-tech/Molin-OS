"""
飞书任务进度卡片 — v6.6 10步平滑版
"""
import os, json, time, httpx
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger

# 10 步渐进式进度
STEPS = [
    "🔍 意图识别",          # 0→10%
    "📋 任务拆解",          # 10→20%
    "🚀 派发子公司",        # 20→30%
    "⚙️ Worker 开始执行",   # 30→40%
    "⚙️ Worker 执行 1/3",   # 40→50%
    "⚙️ Worker 执行 2/3",   # 50→60%
    "⚙️ Worker 执行 3/3",   # 60→70%
    "🔗 结果聚合",          # 70→80%
    "🧠 CEO 综合",          # 80→90%
    "✅ 完成",              # 90→100%
]
TOTAL = len(STEPS)

_started: Dict[str, float] = {}

def _mark(task_id: str):
    if task_id not in _started:
        _started[task_id] = time.time()

def _eta(task_id: str, cur: int) -> int:
    if task_id not in _started or cur <= 1:
        return max(1, (TOTAL - cur) * 1)
    elapsed = time.time() - _started[task_id]
    if elapsed < 5:
        return max(1, (TOTAL - cur) * 1)
    return max(1, int(((elapsed / cur) * (TOTAL - cur)) / 60 + 0.5))

def _bar(cur: int) -> Tuple[str, int]:
    pct = cur * 100 // (TOTAL - 1) if cur > 0 else 0
    pct = min(pct, 100)
    filled = min(10, pct // 10)
    return "█" * filled + "░" * (10 - filled), pct


def build_progress_card(task_id: str, description: str, current_step: int,
                        agencies: List[str] = None,
                        step_results: Dict[str, str] = None) -> Dict[str, Any]:
    bar, pct = _bar(current_step)
    label = STEPS[min(current_step, TOTAL - 1)]
    done = current_step >= TOTAL - 1
    eta_text = "即将完成" if done else f"约 {_eta(task_id, current_step)} 分钟"

    agency_lines = []
    if agencies:
        for ag in agencies:
            st = (step_results or {}).get(ag, "⏳ 等待中...")
            icon = "✅" if "完成" in st else "⏳"
            agency_lines.append(f"{icon} **{ag}**: {st}")

    return {
        "config": {"wide_screen_mode": True, "update_multi": True},
        "header": {
            "title": {"tag": "plain_text",
                      "content": f"⚡ 任务执行中{' ✅已完成' if done else f' {pct}%'} — {description[:25]}"},
            "template": "green" if done else "blue",
        },
        "elements": [
            {"tag": "div", "text": {"tag": "lark_md",
                                    "content": f"`{bar}` {pct}%\n\n当前：**{label}**\n剩余：{eta_text}"}},
            {"tag": "hr"},
        ] + ([{"tag": "div", "text": {"tag": "lark_md",
                                       "content": "\n".join(agency_lines)}}] if agency_lines else []) + [
            {"tag": "note", "elements": [
                {"tag": "plain_text", "content": f"ID:{task_id[-12:]} · {time.strftime('%H:%M:%S')}"}]},
        ],
    }


async def send_progress_card(chat_id: str, task_id: str, description: str,
                              agencies: List[str] = None,
                              token: str = None) -> Optional[str]:
    if not token:
        from molib.integrations.feishu.bridge import _get_feishu_token
        token = await _get_feishu_token()
    if not token: return None
    _mark(task_id)
    card = build_progress_card(task_id, description, 0, agencies=agencies)
    try:
        async with httpx.AsyncClient() as cli:
            r = await cli.post(
                "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
                headers={"Authorization": f"Bearer {token}"},
                json={"receive_id": chat_id, "msg_type": "interactive", "content": json.dumps(card)},
                timeout=10)
            d = r.json()
            if d.get("code") == 0:
                mid = d["data"]["message_id"]
                logger.info(f"进度卡已发送: {task_id[-12:]} → {mid[-16:]}")
                return mid
            logger.error(f"进度卡发送失败: {d}")
    except Exception as e:
        logger.error(f"进度卡发送异常: {e}")
    return None


async def update_progress_card(message_id: str, current_step: int, task_id: str, description: str,
                                agencies: List[str] = None,
                                step_results: Dict[str, str] = None,
                                token: str = None,
                                eta_minutes: int = 2, total_steps: int = TOTAL) -> bool:
    # v2.0: 统一从 token_manager 获取 Token（修复 BUG-04 Token 来源不一致）
    if not token:
        from molib.integrations.feishu.token_manager import get_feishu_token
        token = await get_feishu_token()
    if not token: return False
    card = build_progress_card(task_id, description, current_step, agencies, step_results)
    # 确保卡片支持 update_multi（飞书交互卡片要求）
    card.setdefault("config", {})["update_multi"] = True
    try:
        async with httpx.AsyncClient() as cli:
            r = await cli.patch(
                f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}",
                headers={"Authorization": f"Bearer {token}",
                         "Content-Type": "application/json"},
                json={"content": json.dumps(card)},
                timeout=10)
            d = r.json()
            if d.get("code") == 0:
                logger.info(f"进度卡已更新: {task_id[-12:]} step={current_step}")
                return True
            logger.warning(f"进度卡更新失败: {d}")
    except Exception as e:
        logger.error(f"进度卡更新异常: {e}")
    return False


def publish_progress_event(task_id: str, message_id: str, current_step: int,
                            agency: str = "", status: str = "executing",
                            eta_seconds: int = 120, total_steps: int = TOTAL) -> None:
    try:
        import redis
        r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"),
                        port=int(os.getenv("REDIS_PORT", "6379")),
                        password=os.getenv("REDIS_PASSWORD", ""),
                        decode_responses=True)
        r.publish("feishu_progress", json.dumps({
            "task_id": task_id, "message_id": message_id, "current_step": current_step,
            "total_steps": total_steps, "agency": agency, "status": status,
            "eta_seconds": eta_seconds,
        }))
        r.setex(f"feishu_msg:{task_id}", 3600, message_id)
    except Exception as e:
        logger.warning(f"进度事件发布失败: {e}")
