"""
墨麟OS — 飞书原生 Interactive 卡片构建器 & 发送器（弃用存根）
=======================================================

此文件已弃用，所有功能已拆分至 molib/ceo/cards/ 包。

请改用：
    from molib.ceo.cards import (
        CardBuilder, FeishuCardSender,
        ThinkingCardManager, ProgressCardManager,
        build_status_card, build_approval_card, ...
    )

此文件保留仅为向后兼容。
"""

import warnings as _warnings

_warnings.warn(
    "feishu_card.py 已弃用，请从 molib.ceo.cards 导入相应模块。",
    DeprecationWarning,
    stacklevel=2,
)

from molib.ceo.cards import *

# 兼容旧模块导入（_timestamp 是 builder 中的内部函数）
from molib.ceo.cards.builder import _timestamp

# 保持旧模块的全部公开API
__all__ = [
    "CardBuilder", "FeishuCardSender",
    "ThinkingCardManager", "ProgressCardManager",
    "build_status_card", "build_approval_card", "build_daily_briefing_card",
    "build_report_card", "build_task_card", "build_simple_card",
    "card_to_text", "card_payload",
    "feishu_cli_available", "feishu_send_card", "feishu_import_markdown",
    "feishu_bitable_record_write", "feishu_check_health",
    "BLUE", "WATARI", "INDIGO", "PURPLE", "RED", "ORANGE",
    "YELLOW", "GREEN", "TURQUOISE", "GREY",
    "CEO_THINKING_STEPS", "STEP_ICONS", "PROGRESS_STEPS",
]

# ── feishu-cli 集成函数 — 保留在旧文件中保持完全兼容 ──
import json
import logging
import os
import subprocess

logger = logging.getLogger("molin.ceo.cards.cli")


def feishu_cli_available() -> bool:
    """检查 feishu-cli 是否已安装且已登录"""
    try:
        r = subprocess.run(["feishu-cli", "auth", "status", "-o", "json"],
                          capture_output=True, text=True, timeout=5)
        if r.returncode != 0:
            return False
        return '"access_token_valid": true' in r.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def feishu_send_card(card_dict: dict, chat_id: str = None) -> dict:
    """用 feishu-cli 发送原生 interactive 卡片"""
    import tempfile
    if chat_id is None:
        chat_id = "oc_94c87f141e118b68c2da9852bf2f3bda"
    card_json = json.dumps(card_dict, ensure_ascii=False)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(card_json)
        card_file = f.name
    try:
        r = subprocess.run(
            ["feishu-cli", "msg", "send",
             "--receive-id-type", "chat_id",
             "--receive-id", chat_id,
             "--msg-type", "interactive", "--content-file", card_file],
            capture_output=True, text=True, timeout=15)
        return {"success": r.returncode == 0, "output": r.stdout or r.stderr}
    finally:
        os.unlink(card_file)


def feishu_import_markdown(md_content: str, title: str = None) -> dict:
    """将 Markdown 内容导入为飞书文档"""
    import tempfile
    if title is None:
        title = "墨麟OS 导入文档"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(md_content)
        md_file = f.name
    try:
        r = subprocess.run(
            ["feishu-cli", "doc", "import", md_file, "--title", title, "-o", "json"],
            capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            return {"success": False, "output": r.stderr}
        data = json.loads(r.stdout)
        return {
            "success": True,
            "doc_token": data.get("doc_token", ""),
            "url": data.get("url", ""),
            "output": r.stdout,
        }
    finally:
        os.unlink(md_file)


def feishu_bitable_record_write(base_token: str, table_id: str, fields: dict) -> dict:
    """向多维表格写入一条记录"""
    import tempfile
    payload = {"fields": fields}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(payload, f, ensure_ascii=False)
        cfg_file = f.name
    try:
        r = subprocess.run(
            ["feishu-cli", "bitable", "record", "upsert",
             "--base-token", base_token,
             "--table-id", table_id,
             "--config-file", cfg_file],
            capture_output=True, text=True, timeout=15)
        return {"success": r.returncode == 0, "output": r.stdout or r.stderr}
    finally:
        os.unlink(cfg_file)


def feishu_check_health() -> dict:
    """检查 feishu-cli 整体健康状态"""
    try:
        r = subprocess.run(["feishu-cli", "auth", "status", "-o", "json"],
                          capture_output=True, text=True, timeout=5)
        if r.returncode != 0:
            return {"available": False, "error": r.stderr}
        data = json.loads(r.stdout)
        return {
            "available": data.get("logged_in", False),
            "user": data.get("cached_user", {}).get("name", "?"),
            "expires_at": data.get("expires_at", "?"),
            "scopes": data.get("scope", "").split(),
        }
    except Exception as e:
        return {"available": False, "error": str(e)}


if __name__ == "__main__":
    import sys
    if "--health" in sys.argv:
        health = feishu_check_health()
        print(json.dumps(health, ensure_ascii=False, indent=2))
        sys.exit(0)

    from molib.ceo.cards.templates import build_status_card
    card = build_status_card("✅ 测试", [("SKILL", "336"), ("Worker", "22"), ("状态", "正常")], ["无"], ["继续"])
    print(json.dumps(card, ensure_ascii=False, indent=2))
    print("\n--- 纯文本 ---")
    print(card_to_text(card))

    sender = FeishuCardSender()
    if sender.app_id:
        print(f"\n✅ 飞书凭证已配置: {sender.app_id[:12]}...")
    else:
        print("\n⚠️ 未配置飞书凭证（仅卡片构建器模式可用）")

    health = feishu_check_health()
    cli_status = "✅ 已登录" if health.get("available") else "❌ 未登录"
    print(f"\n📎 feishu-cli: {cli_status} (用户: {health.get('user', '?')}, 有效期至: {health.get('expires_at', '?')})")
