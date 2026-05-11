"""墨麟OS — 飞书卡片发送器

提供 FeishuCardSender 类和消息封装函数。
"""
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from molib.ceo.cards.templates import build_status_card

logger = logging.getLogger("molin.ceo.cards.sender")

API_BASE = "https://open.feishu.cn/open-apis"

# ── Cron 双重投递抑制（sentinel 标记文件机制）────────────────────────────
# FeishuCardSender 直接调用飞书 Open API 发送卡片，与 Hermes cron 调度器的
# 文本投递管道完全独立。为避免 Agent 发完卡片后 cron 又投递一份 final response
# 纯文本（造成群内一张卡片+一条文本的重复输出），send_card() 成功后在
# ~/.hermes/cron/card_sent/ 写入一个标记文件。cron 调度器在投递文本前检查此
# 标记，如存在则跳过文本投递。
_CARD_SENT_DIR = Path.home() / ".hermes" / "cron" / "card_sent"


def _write_card_sentinel(chat_id: str) -> None:
    """发送卡片成功后写入 sentinel 标记文件，通知 cron 调度器跳过文本投递。"""
    # 仅 cron 会话需要（交互会话没有双重投递问题）
    if os.environ.get("HERMES_CRON_SESSION") != "1":
        return
    try:
        _CARD_SENT_DIR.mkdir(parents=True, exist_ok=True)
        sentinel = _CARD_SENT_DIR / chat_id
        sentinel.write_text(str(time.time()))
        logger.debug("sentinel 写入: %s", sentinel)
    except OSError:
        pass  # 静默降级：标记文件写入失败不影响卡片发送


def card_payload(card_dict: dict) -> dict:
    """将卡片嵌入飞书 interactive 消息格式"""
    return {"msg_type": "interactive", "content": json.dumps(card_dict, ensure_ascii=False)}


class FeishuCardSender:
    """通过飞书 Open API 直接发送互动卡片（独立发送器）

    用法:
        sender = FeishuCardSender()
        sender.send_card(card_dict, chat_id="oc_xxx")
    """

    API_BASE = API_BASE

    def __init__(self):
        self._token: str | None = None
        self._token_expire: float = 0.0
        self.app_id = ""
        self.app_secret = ""
        self._load_credentials()

    def _load_credentials(self):
        env_paths = [Path.home() / ".hermes" / ".env", Path.cwd() / ".env"]
        for path in env_paths:
            if path.exists():
                for line in path.read_text().splitlines():
                    line = line.strip()
                    if line.startswith("FEISHU_APP_ID="):
                        self.app_id = line.split("=", 1)[1].strip().strip('"').strip("'")
                    elif line.startswith("FEISHU_APP_SECRET="):
                        self.app_secret = line.split("=", 1)[1].strip().strip('"').strip("'")
        self.app_id = os.environ.get("FEISHU_APP_ID", self.app_id)
        self.app_secret = os.environ.get("FEISHU_APP_SECRET", self.app_secret)
        if not self.app_id or not self.app_secret:
            logger.warning("FeishuCardSender: 未配置 FEISHU_APP_ID / FEISHU_APP_SECRET")

    def _get_token(self) -> str:
        if self._token and time.time() < self._token_expire:
            return self._token
        import requests
        r = requests.post(f"{self.API_BASE}/auth/v3/tenant_access_token/internal",
                          json={"app_id": self.app_id, "app_secret": self.app_secret}, timeout=10)
        data = r.json()
        if data.get("code") != 0:
            raise RuntimeError(f"飞书 token 获取失败: {data}")
        self._token = data["tenant_access_token"]
        self._token_expire = time.time() + data.get("expire", 7200)
        return self._token

    def send_card(self, card_dict: dict, chat_id: str, receive_id_type: str = "chat_id") -> dict:
        """发送互动卡片到指定会话"""
        import requests
        token = self._get_token()
        payload = card_payload(card_dict)
        r = requests.post(
            f"{self.API_BASE}/im/v1/messages?receive_id_type={receive_id_type}",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"receive_id": chat_id, "msg_type": payload["msg_type"], "content": payload["content"]},
            timeout=10,
        )
        result = r.json()
        if result.get("code") != 0:
            logger.error("飞书卡片发送失败: %s", result)
        else:
            # 写入 sentinel 标记文件，防止 cron 调度器重复投递纯文本
            _write_card_sentinel(chat_id)
        return result

    def send_text(self, chat_id: str, text: str, receive_id_type: str = "chat_id") -> dict:
        """发送纯文本消息（备用）"""
        import requests
        token = self._get_token()
        r = requests.post(
            f"{self.API_BASE}/im/v1/messages?receive_id_type={receive_id_type}",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"receive_id": chat_id, "msg_type": "text", "content": json.dumps({"text": text}, ensure_ascii=False)},
            timeout=10,
        )
        return r.json()

    def send_post(self, chat_id: str, title: str, content_lines: list[str], receive_id_type: str = "chat_id") -> dict:
        """发送富文本 post 消息"""
        import requests
        token = self._get_token()
        post_content = []
        for line in content_lines:
            if not line.strip():
                post_content.append([{"tag": "text", "text": " "}])
                continue
            stripped = line.strip()
            if stripped.startswith("```"):
                continue
            if stripped.startswith("---"):
                post_content.append([{"tag": "text", "text": "─────────────────────"}])
            else:
                post_content.append([{"tag": "text", "text": stripped}])
        content = json.dumps({"zh_cn": {"title": title, "content": post_content}}, ensure_ascii=False)
        r = requests.post(
            f"{self.API_BASE}/im/v1/messages?receive_id_type={receive_id_type}",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"receive_id": chat_id, "msg_type": "post", "content": content},
            timeout=15,
        )
        return r.json()

    @staticmethod
    def send_via_cli(chat_id: str, text: str) -> dict:
        """通过 feishu-cli 发送文本消息"""
        import subprocess, json
        try:
            r = subprocess.run(
                ["feishu-cli", "msg", "send", "--receive-id", chat_id,
                 "--receive-id-type", "chat_id", "--text", text, "-o", "json"],
                capture_output=True, text=True, timeout=15,
            )
            if r.returncode == 0:
                return json.loads(r.stdout)
            return {"error": r.stderr[:200]}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def send_card_via_cli(chat_id: str, card_dict: dict) -> dict:
        """通过 feishu-cli 发送原生 interactive 卡片"""
        import subprocess, json, tempfile, os
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(card_dict, f, ensure_ascii=False)
                fpath = f.name
            r = subprocess.run(
                ["feishu-cli", "msg", "send", "--receive-id", chat_id,
                 "--receive-id-type", "chat_id", "--msg-type", "interactive",
                 "--content-file", fpath, "-o", "json"],
                capture_output=True, text=True, timeout=15,
            )
            os.unlink(fpath)
            if r.returncode == 0:
                return json.loads(r.stdout)
            return {"error": r.stderr[:300]}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def doc_create(title: str, content_path: str = "") -> dict:
        """通过 feishu-cli 创建文档或导入 Markdown"""
        import subprocess, json
        try:
            if content_path:
                r = subprocess.run(
                    ["feishu-cli", "doc", "import", content_path, "--title", title, "--upload-images", "-o", "json"],
                    capture_output=True, text=True, timeout=60,
                )
            else:
                r = subprocess.run(
                    ["feishu-cli", "doc", "create", "--title", title, "-o", "json"],
                    capture_output=True, text=True, timeout=15,
                )
            if r.returncode == 0:
                return json.loads(r.stdout)
            return {"error": r.stderr[:300]}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def bitable_create(name: str) -> dict:
        """通过 feishu-cli 创建多维表格"""
        import subprocess, json
        try:
            r = subprocess.run(
                ["feishu-cli", "bitable", "create", name, "--json"],
                capture_output=True, text=True, timeout=15,
            )
            if r.returncode == 0:
                return json.loads(r.stdout)
            return {"error": r.stderr[:300]}
        except Exception as e:
            return {"error": str(e)}

    @classmethod
    def send_status_card(cls, chat_id: str, title: str = "",
                         status_items: list[tuple[str, str]] | None = None,
                         alerts: list[str] | None = None,
                         actions: list[str] | None = None) -> dict:
        """一键发送状态概览卡片"""
        sender = cls()
        card = build_status_card(
            title=title or "系统状态概览",
            status_items=status_items or [],
            alerts=alerts, actions=actions,
        )
        return sender.send_card(card, chat_id)


__all__ = [
    "FeishuCardSender",
    "card_payload",
    "API_BASE",
]
