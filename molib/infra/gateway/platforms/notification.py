"""轻量通知发送层 — 与现有 feishu.py 长连接网关共存"""
import os
import json
from loguru import logger

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


async def send_feishu_card(title: str, content: str, level: str = "info"):
    """发送飞书卡片消息"""
    if not FEISHU_WEBHOOK or not HTTPX_AVAILABLE:
        logger.debug("Feishu webhook/httpx not configured, skipping")
        return False
    colors = {"critical": "red", "important": "orange", "normal": "blue", "info": "grey"}
    card = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {"title": {"tag": "plain_text", "content": title},
                       "template": colors.get(level, "blue")},
            "elements": [{"tag": "markdown", "content": content}]
        }
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(FEISHU_WEBHOOK, json=card)
            if resp.status_code == 200:
                logger.info(f"Feishu card sent: {title}")
                return True
        logger.warning(f"Feishu card failed: {resp.status_code}")
        return False
    except Exception as e:
        logger.error(f"Feishu card send failed: {e}")
        return False


async def send_telegram(title: str, content: str):
    """发送 Telegram 消息"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID or not HTTPX_AVAILABLE:
        logger.debug("Telegram not configured, skipping")
        return False
    text = f"*{title}*\n\n{content}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "Markdown"
            })
            if resp.status_code == 200:
                logger.info(f"Telegram message sent: {title}")
                return True
        logger.warning(f"Telegram send failed: {resp.status_code}")
        return False
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False


async def send_email(subject: str, body: str):
    """发送 SMTP 邮件"""
    import smtplib
    from email.mime.text import MIMEText
    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")
    if not smtp_host or not smtp_user:
        logger.debug("SMTP not configured, skipping")
        return False
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = smtp_user  # 默认发给自己
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, smtp_user, msg.as_string())
        logger.info(f"Email sent: {subject}")
        return True
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False
