import os, httpx
from loguru import logger

WEBHOOK = os.getenv("FEISHU_WEBHOOK_URL", "")

async def send_feishu_alert(title: str, content: str, level: str = "warning"):
    if not WEBHOOK:
        return
    color = {"info": "green", "warning": "yellow", "error": "red"}.get(level, "yellow")
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {"title": {"tag": "plain_text",
                        "content": f"[{level.upper()}] {title}"}, "template": color},
            "elements": [{"tag": "div",
                          "text": {"tag": "lark_md", "content": content}}]
        }
    }
    try:
        async with httpx.AsyncClient() as c:
            r = await c.post(WEBHOOK, json=payload, timeout=10)
            logger.info(f"Feishu alert: {title} → {r.status_code}")
    except Exception as e:
        logger.error(f"Feishu alert failed: {e}")
