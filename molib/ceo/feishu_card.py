"""
墨域OS — 飞书原生 Interactive 卡片构建器 & 发送器
=================================================
生成飞书 Open API msg_type: interactive 格式的卡片 JSON，
并通过飞书 Open API 直接发送（独立于 Hermes 的发送管道）。

两种使用方式：
    1. 生成卡片 JSON：CardBuilder().build() → 由 Hermes send_message 或自定义管道发送
    2. 直接发送：FeishuCardSender().send_card(card_dict, chat_id) → 独立发送

飞书卡片规范: https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/card-components
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("molin.ceo.feishu_card")


# ── 颜色模板常量 ─────────────────────────────────────
BLUE = "blue"
WATARI = "watari"
INDIGO = "indigo"
PURPLE = "purple"
RED = "red"
ORANGE = "orange"
YELLOW = "yellow"
GREEN = "green"
TURQUOISE = "turquoise"
GREY = "grey"


# ── 内部辅助 ────────────────────────────────────────


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _header(title: str, color: str = BLUE) -> dict:
    return {"title": {"tag": "plain_text", "content": title}, "template": color}


def _md(content: str) -> dict:
    return {"tag": "lark_md", "content": content}


def _div(content: str) -> dict:
    return {"tag": "div", "text": _md(content)}


def _row(fields: list[dict]) -> dict:
    return {"tag": "column_set", "flex_mode": "none", "background_style": "default", "columns": fields}


def _field(key: str, value: str, width: str = "weighted", weight: int = 1) -> dict:
    return {
        "tag": "column",
        "width": width,
        "weight": weight,
        "vertical_align": "top",
        "elements": [
            {"tag": "div", "text": {"tag": "lark_md", "content": f"**{key}**"}},
            {"tag": "div", "text": {"tag": "lark_md", "content": value}},
        ],
    }


def _hr() -> dict:
    return {"tag": "hr"}


def _note(text: str) -> dict:
    return {"tag": "note", "text": {"tag": "plain_text", "content": text}}


# ── 卡片构建器 ─────────────────────────────────────


class CardBuilder:
    """飞书卡片构建器基类"""

    def __init__(self, title: str, color: str = BLUE):
        self.title = title
        self.color = color
        self.elements: list[dict] = []

    def add_div(self, content: str) -> "CardBuilder":
        self.elements.append(_div(content))
        return self

    def add_hr(self) -> "CardBuilder":
        self.elements.append(_hr())
        return self

    def add_field(self, key: str, value: str) -> "CardBuilder":
        self.elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**{key}**  {value}"}})
        return self

    def add_fields_row(self, fields: list[tuple[str, str]]) -> "CardBuilder":
        """添加行内多列字段（最多4列）"""
        columns = [_field(k, v) for k, v in fields]
        self.elements.append(_row(columns))
        return self

    def add_section(self, title: str, items: list[str]) -> "CardBuilder":
        self.elements.append(_div(f"**{title}**"))
        for item in items:
            self.elements.append(_div(f"· {item}"))
        return self

    def add_button(self, text: str, url: str = "", type_: str = "default") -> "CardBuilder":
        btn: dict[str, Any] = {"tag": "action", "actions": [{"tag": "button", "text": {"tag": "plain_text", "content": text}, "type": type_}]}
        if url:
            btn["actions"][0]["url"] = url
        self.elements.append(btn)
        return self

    def add_note(self, text: str) -> "CardBuilder":
        self.elements.append(_note(text))
        return self

    def build(self) -> dict:
        return {"config": {"wide_screen_mode": True}, "header": _header(self.title, self.color), "elements": self.elements}

    def build_json(self) -> str:
        return json.dumps(self.build(), ensure_ascii=False)


# ── 专用卡片工厂 ────────────────────────────────────


def build_status_card(title: str, status_items: list[tuple[str, str]], alerts: list[str] | None = None, actions: list[str] | None = None, color: str = INDIGO) -> dict:
    """系统状态概览卡片"""
    card = CardBuilder(title, color)
    card.add_fields_row(status_items[:4])
    for k, v in status_items[4:]:
        card.add_field(k, v)
    if alerts:
        card.add_hr()
        card.add_section("⚠️ 需关注", alerts)
    if actions:
        card.add_hr()
        card.add_section("🎯 建议行动", actions)
    card.add_hr()
    card.add_note(f"墨域OS · {_timestamp()}")
    return card.build()


def build_approval_card(task_id: str, description: str, risk_score: float, risk_reason: str, intent_type: str, target_vps: list[str], target_subsidiaries: list[str] | None = None, budget_estimate: float = 0.0) -> dict:
    """审批卡片（带风险颜色）"""
    color = RED if risk_score > 80 else (ORANGE if risk_score > 60 else BLUE)
    risk_icon = "🔴" if risk_score > 80 else "🟡"
    card = CardBuilder(f"{risk_icon} Plan Mode — 需要你审批", color)
    card.add_field("📋 任务", description or "（无描述）")
    card.add_fields_row([("风险评分", f"{risk_score:.1f}/100"), ("意图类型", intent_type)])
    card.add_field("⚠️ 风险原因", risk_reason[:200])
    card.add_field("🎯 目标 VP", ", ".join(target_vps) if target_vps else "未指定")
    if target_subsidiaries:
        card.add_field("🏢 目标子公司", ", ".join(target_subsidiaries))
    if budget_estimate > 0:
        card.add_field("💰 预算估算", f"¥{budget_estimate:.0f}")
    card.add_field("🔑 任务 ID", f"`{task_id}`")
    card.add_hr()
    card.add_div(f"✅ 回复 **批准 {task_id}** 或 **拒绝 {task_id} [原因]**")
    card.add_note("此消息由墨麟OS PlanMode 引擎自动发送")
    return card.build()


def build_daily_briefing_card(date: str, stats: dict[str, Any], highlights: list[str], warnings: list[str] | None = None, color: str = BLUE) -> dict:
    """每日简报卡片"""
    card = CardBuilder(f"☀️ CEO 每日简报 · {date}", color)
    if stats:
        items = list(stats.items())
        card.add_fields_row(items[:4])
        for k, v in items[4:]:
            card.add_field(k, str(v))
    if highlights:
        card.add_hr()
        card.add_section("✨ 亮点", highlights)
    if warnings:
        card.add_hr()
        card.add_section("⚠️ 需关注", warnings)
    card.add_note(f"墨域OS CEO引擎 · {_timestamp()}")
    return card.build()


def build_report_card(report_type: str, content: str, meta: dict[str, str] | None = None, color: str = PURPLE) -> dict:
    """报告型卡片"""
    card = CardBuilder(f"📋 {report_type}", color)
    card.add_div(content)
    if meta:
        card.add_hr()
        for k, v in meta.items():
            card.add_field(k, v)
    card.add_note(f"墨域OS · {_timestamp()}")
    return card.build()


def build_task_card(task_id: str, description: str, status: str, assignee: str = "", priority: str = "medium", color: str = BLUE) -> dict:
    """任务状态卡片"""
    icons = {"completed": "✅", "in_progress": "🔄", "pending": "⏳", "blocked": "🚫", "cancelled": "❌"}
    icon = icons.get(status, "📋")
    card = CardBuilder(f"{icon} 任务 {task_id}", color)
    card.add_field("📋 描述", description)
    card.add_fields_row([("状态", status), ("优先级", priority)])
    if assignee:
        card.add_field("👤 负责人", assignee)
    card.add_note(f"墨域OS · {_timestamp()}")
    return card.build()


def build_simple_card(title: str, lines: list[str], color: str = BLUE) -> dict:
    """简易卡片：传入行列表，自动识别分割线和加粗"""
    card = CardBuilder(title, color)
    for line in lines:
        if line.startswith("---"):
            card.add_hr()
        elif line.startswith("## "):
            card.add_div(f"**{line[3:]}**")
        else:
            card.add_div(line)
    card.add_note(f"墨域OS · {_timestamp()}")
    return card.build()


# ── 消息封装 ─────────────────────────────────────────


def card_payload(card_dict: dict) -> dict:
    """将卡片嵌入飞书 interactive 消息格式"""
    return {"msg_type": "interactive", "content": json.dumps(card_dict, ensure_ascii=False)}


# ── 独立发送器 ───────────────────────────────────────


class FeishuCardSender:
    """通过飞书 Open API 直接发送互动卡片（独立发送器）

    用法:
        sender = FeishuCardSender()
        sender.send_card(card_dict, chat_id="oc_xxx")
    """

    API_BASE = "https://open.feishu.cn/open-apis"

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
        r = requests.post(f"{self.API_BASE}/auth/v3/tenant_access_token/internal", json={"app_id": self.app_id, "app_secret": self.app_secret}, timeout=10)
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

    # ── feishu-cli 集成 ────────────────────────────────────────────

    @staticmethod
    def send_via_cli(chat_id: str, text: str) -> dict:
        """通过 feishu-cli 发送文本消息（优先走 CLI）"""
        import subprocess, json
        try:
            r = subprocess.run(
                ["feishu-cli", "msg", "send",
                 "--receive-id", chat_id,
                 "--receive-id-type", "chat_id",
                 "--text", text,
                 "-o", "json"],
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
        import subprocess, json, tempfile
        try:
            # feishu-cli 的 --content-file 只需 card JSON（不含外层 msg_type）
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(card_dict, f, ensure_ascii=False)
                fpath = f.name
            r = subprocess.run(
                ["feishu-cli", "msg", "send",
                 "--receive-id", chat_id,
                 "--receive-id-type", "chat_id",
                 "--msg-type", "interactive",
                 "--content-file", fpath,
                 "-o", "json"],
                capture_output=True, text=True, timeout=15,
            )
            import os; os.unlink(fpath)
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
                    ["feishu-cli", "doc", "import", content_path,
                     "--title", title, "--upload-images", "-o", "json"],
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
    def send_status_card(cls, chat_id: str, title: str = "", status_items: list[tuple[str, str]] | None = None, alerts: list[str] | None = None, actions: list[str] | None = None) -> dict:
        """一键发送状态概览卡片"""
        sender = cls()
        card = build_status_card(title=title or "系统状态概览", status_items=status_items or [], alerts=alerts, actions=actions)
        return sender.send_card(card, chat_id)


# ── 兼容层：Hermes send_message 降级路径 ──────────────


def card_to_text(card_dict: dict) -> str:
    """将卡片字典转为纯文本（供 Hermes send_message 降级使用）"""
    title = card_dict.get("header", {}).get("title", {}).get("content", "")
    lines = [f"━━━ {title} ━━━", ""]
    for el in card_dict.get("elements", []):
        tag = el.get("tag")
        if tag == "div":
            lines.append(el.get("text", {}).get("content", ""))
        elif tag == "hr":
            lines.append("───")
        elif tag == "column_set":
            for col in el.get("columns", []):
                vals = [e.get("text", {}).get("content", "").replace("**", "") for e in col.get("elements", [])]
                lines.append(" | ".join(vals))
        elif tag == "note":
            lines.append(el.get("text", {}).get("content", ""))
        elif tag == "action":
            for act in el.get("actions", []):
                lines.append(f"[ {act.get('text', {}).get('content', '')} ]")
    return "\n".join(lines)


# ── 测试 ─────────────────────────────────────────────

if __name__ == "__main__":
    card = build_status_card("✅ 测试", [("SKILL", "336"), ("Worker", "22"), ("状态", "正常")], ["无"], ["继续"])
    print(json.dumps(card, ensure_ascii=False, indent=2))
    print("\n--- 纯文本 ---")
    print(card_to_text(card))

    sender = FeishuCardSender()
    if sender.app_id:
        print(f"\n✅ 飞书凭证已配置: {sender.app_id[:12]}...")
    else:
        print("\n⚠️ 未配置飞书凭证（仅卡片构建器模式可用）")
