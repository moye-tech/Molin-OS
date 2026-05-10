import asyncio
import os
from enum import Enum
from loguru import logger

FEISHU_WEBHOOK = os.getenv('FEISHU_WEBHOOK_URL', '')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

import httpx


class AlertLevel(Enum):
    CRITICAL = "critical"    # 🔴 API错误率>5%、余额<10元、安全告警 → 飞书+Telegram，5分钟内
    IMPORTANT = "important"  # 🟠 新订单、学员逾期未付 → 飞书Bot，30分钟内
    NORMAL = "normal"        # 🟡 每日简报、SOP优化 → 飞书卡片（可折叠），当天
    INFO = "info"            # ⚪ 执行日志、记忆更新 → 仅写入Grafana


async def _send_feishu(title: str, content: str, level: str = "info", actions: list = None):
    if not FEISHU_WEBHOOK:
        return
    colors = {"critical": "red", "important": "orange", "normal": "blue", "info": "grey"}
    elements = [{'tag': 'div', 'text': {'tag': 'lark_md', 'content': content}}]
    if actions:
        elements.append({'tag': 'action', 'actions': actions})
    payload = {
        'msg_type': 'interactive',
        'card': {
            'config': {'wide_screen_mode': True},
            'header': {'title': {'tag': 'plain_text', 'content': title},
                       'template': colors.get(level, "blue")},
            'elements': elements,
        },
    }
    try:
        async with httpx.AsyncClient() as client:
            await client.post(FEISHU_WEBHOOK, json=payload, timeout=10)
    except Exception as exc:
        logger.error(f'Feishu alert failed: {exc}')


async def _send_telegram(title: str, content: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    text = f'**{title}**\n{content}'
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage',
                json={'chat_id': TELEGRAM_CHAT_ID, 'text': text, 'parse_mode': 'Markdown'},
                timeout=10,
            )
    except Exception as exc:
        logger.error(f'Telegram alert failed: {exc}')


async def send_alert(title: str, content: str, level: str = 'info', actions: list = None) -> None:
    """分级通知：根据级别推送到不同渠道

    Args:
        title: 告警标题
        content: 告警内容（支持 Markdown）
        level: 告警级别 (critical/important/normal/info)
        actions: 飞书交互按钮列表，例如：
            [{"tag": "button", "text": {"tag": "plain_text", "content": "查看详情"},
              "type": "primary", "value": {"action": "view_detail"}}]
    """
    alert_level = AlertLevel(level)

    if alert_level == AlertLevel.CRITICAL:
        # 🔴 同时推送到飞书和Telegram
        await asyncio.gather(
            _send_feishu(f"🔴 {title}", content, "critical", actions),
            _send_telegram(f"🔴 {title}", content),
        )
    elif alert_level == AlertLevel.IMPORTANT:
        # 🟠 飞书Bot
        await _send_feishu(f"🟠 {title}", content, "important", actions)
    elif alert_level == AlertLevel.NORMAL:
        # 🟡 飞书卡片（可折叠）
        await _send_feishu(f"🟡 {title}", content, "normal", actions)
    else:
        # ⚪ 仅记录日志（写入 Grafana）
        logger.debug(f"[INFO] {title}: {content}")
