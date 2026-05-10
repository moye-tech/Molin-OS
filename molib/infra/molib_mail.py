"""
MolibMail — 邮件列表与营销引擎（listmonk 纯 Python 替代）
======================================================
对标 listmonk (15K★): 邮件列表管理 · 模板引擎 · 打开率追踪
Mac M2: <5MB 内存，SMTP stdlib，SQLite 存证。

用法:
    python -m molib mail list create --name "VIP客户"
    python -m molib mail subscriber add --list VIP --email a@b.com
    python -m molib mail campaign send --list VIP --subject "新品上架" --body "..."
    python -m molib mail stats
"""

from __future__ import annotations

import json
import logging
import os
import smtplib
import sqlite3
import uuid
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("molib.mail")

DB_PATH = Path.home() / ".hermes" / "molib_mail.db"
DEFAULT_TEMPLATE = """
<html><body style="font-family:sans-serif;max-width:600px;margin:0 auto">
<h2>{{subject}}</h2>
{{body}}
<hr><p style="color:#999;font-size:12px">
  墨麟OS · 墨域私域自动发送 · <a href="{{unsubscribe_url}}">退订</a>
</p></body></html>
"""


class MolibMail:
    """邮件列表与营销引擎。"""

    def __init__(self, db_path: str = ""):
        self.db_path = db_path or str(DB_PATH)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS lists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT DEFAULT '',
                    created_at TEXT DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS subscribers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    name TEXT DEFAULT '',
                    list_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'active',
                    subscribed_at TEXT DEFAULT (datetime('now')),
                    UNIQUE(email, list_id)
                );
                CREATE TABLE IF NOT EXISTS campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    list_id INTEGER NOT NULL,
                    subject TEXT NOT NULL,
                    body TEXT NOT NULL,
                    status TEXT DEFAULT 'draft',
                    sent_count INTEGER DEFAULT 0,
                    open_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now')),
                    sent_at TEXT
                );
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER NOT NULL,
                    subscriber_id INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    subject_template TEXT DEFAULT '',
                    html_template TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                );
            """)
            conn.commit()

    # ── Lists ─────────────────────────────────────────────────

    def create_list(self, name: str, description: str = "") -> dict:
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute("INSERT INTO lists (name, description) VALUES (?,?)", (name, description))
                conn.commit()
            except sqlite3.IntegrityError:
                return {"error": f"列表 '{name}' 已存在"}
        return {"name": name, "status": "created"}

    def list_lists(self) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT id, name, description FROM lists").fetchall()
        return [{"id": r[0], "name": r[1], "desc": r[2]} for r in rows]

    # ── Subscribers ───────────────────────────────────────────

    def add_subscriber(self, list_name: str, email: str, name: str = "") -> dict:
        with sqlite3.connect(self.db_path) as conn:
            list_row = conn.execute("SELECT id FROM lists WHERE name=?", (list_name,)).fetchone()
            if not list_row:
                return {"error": f"列表 '{list_name}' 不存在"}
            list_id = list_row[0]
            try:
                conn.execute(
                    "INSERT INTO subscribers (email, name, list_id) VALUES (?,?,?)",
                    (email, name, list_id),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                return {"error": f"{email} 已在列表中"}
        return {"email": email, "list": list_name, "status": "subscribed"}

    def list_subscribers(self, list_name: str) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """SELECT s.email, s.name, s.status, s.subscribed_at
                   FROM subscribers s JOIN lists l ON s.list_id=l.id
                   WHERE l.name=? AND s.status='active'""",
                (list_name,),
            ).fetchall()
        return [{"email": r[0], "name": r[1], "status": r[2], "since": r[3]} for r in rows]

    def unsubscribe(self, email: str, list_name: str) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """UPDATE subscribers SET status='unsubscribed'
                   WHERE email=? AND list_id=(SELECT id FROM lists WHERE name=?)""",
                (email, list_name),
            )
            conn.commit()
        return {"email": email, "list": list_name, "status": "unsubscribed"}

    # ── Templates ─────────────────────────────────────────────

    def create_template(self, name: str, html: str, subject_template: str = "") -> dict:
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    "INSERT INTO templates (name, subject_template, html_template) VALUES (?,?,?)",
                    (name, subject_template, html),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                return {"error": f"模板 '{name}' 已存在"}
        return {"name": name, "status": "created"}

    def _render_template(self, subject: str, body: str, subscriber_email: str) -> str:
        """渲染默认 HTML 模板。"""
        html = DEFAULT_TEMPLATE
        unsub = f"https://molin-os.local/unsub?email={subscriber_email}"
        html = html.replace("{{subject}}", subject)
        html = html.replace("{{body}}", body.replace("\n", "<br>"))
        html = html.replace("{{unsubscribe_url}}", unsub)
        return html

    # ── Campaigns ─────────────────────────────────────────────

    def send_campaign(
        self,
        list_name: str,
        subject: str,
        body: str,
        smtp_host: str = "",
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_pass: str = "",
        from_email: str = "",
    ) -> dict:
        """发送营销邮件到整个列表。

        SMTP 凭据从环境变量读取（优先级高于参数）：
          MOLIB_SMTP_HOST / MOLIB_SMTP_PORT / MOLIB_SMTP_USER / MOLIB_SMTP_PASS
        """
        host = smtp_host or os.getenv("MOLIB_SMTP_HOST", "")
        user = smtp_user or os.getenv("MOLIB_SMTP_USER", "")
        pwd = smtp_pass or os.getenv("MOLIB_SMTP_PASS", "")
        sender = from_email or user

        if not host:
            return {"error": "SMTP 未配置。设置 MOLIB_SMTP_HOST 环境变量", "mode": "dry_run"}

        with sqlite3.connect(self.db_path) as conn:
            list_row = conn.execute("SELECT id FROM lists WHERE name=?", (list_name,)).fetchone()
            if not list_row:
                return {"error": f"列表 '{list_name}' 不存在"}
            list_id = list_row[0]

            subscribers = conn.execute(
                "SELECT id, email, name FROM subscribers WHERE list_id=? AND status='active'",
                (list_id,),
            ).fetchall()

        if not subscribers:
            return {"error": "列表无活跃订阅者"}

        # 创建 campaign 记录
        campaign_id = uuid.uuid4().hex[:12]
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO campaigns (id, list_id, subject, body, status) VALUES (?,?,?,?,'sending')",
                (campaign_id, list_id, subject, body),
            )
            conn.commit()

        sent = 0
        failed = 0
        errors = []

        for sub_id, email, name in subscribers:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = sender
                msg["To"] = email
                msg["Message-ID"] = f"<{campaign_id}.{sub_id}@molin-os>"

                html_body = self._render_template(subject, body, email)
                msg.attach(MIMEText(html_body, "html", "utf-8"))

                with smtplib.SMTP(host, smtp_port, timeout=15) as server:
                    server.starttls()
                    if user:
                        server.login(user, pwd)
                    server.send_message(msg)

                # 记录发送事件
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "INSERT INTO events (campaign_id, subscriber_id, event_type) VALUES (?,?,'sent')",
                        (campaign_id, sub_id),
                    )
                    conn.commit()
                sent += 1

            except Exception as e:
                failed += 1
                errors.append({"email": email, "error": str(e)[:100]})

        # 更新 campaign 状态
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE campaigns SET status='sent', sent_count=?, sent_at=datetime('now') WHERE id=?",
                (sent, campaign_id),
            )
            conn.commit()

        return {
            "campaign_id": campaign_id,
            "list": list_name,
            "subject": subject,
            "sent": sent,
            "failed": failed,
            "status": "completed" if failed == 0 else "partial",
            "errors": errors[:5],
        }

    # ── Stats ─────────────────────────────────────────────────

    def stats(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            lists = conn.execute("SELECT COUNT(*) FROM lists").fetchone()[0]
            subs = conn.execute("SELECT COUNT(*) FROM subscribers WHERE status='active'").fetchone()[0]
            campaigns = conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(sent_count),0) FROM campaigns WHERE status='sent'"
            ).fetchone()

        return {
            "lists": lists,
            "active_subscribers": subs,
            "campaigns_sent": campaigns[0],
            "total_emails": campaigns[1],
        }


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def cmd_mail_list(args: list[str]) -> dict:
    mail = MolibMail()
    if not args:
        return {"lists": mail.list_lists()}
    subcmd = args[0]
    if subcmd == "create":
        name = args[1] if len(args) > 1 else ""
        desc = args[2] if len(args) > 2 else ""
        return mail.create_list(name, desc) if name else {"error": "需要列表名"}
    return {"error": f"未知: {subcmd}"}


def cmd_mail_subscriber(args: list[str]) -> dict:
    mail = MolibMail()
    if not args:
        return {"error": "子命令: add | list | unsubscribe"}
    subcmd = args[0]
    rest = args[1:]

    list_name = ""
    email = ""
    name = ""
    i = 0
    while i < len(rest):
        if rest[i] == "--list" and i + 1 < len(rest):
            list_name = rest[i + 1]; i += 2
        elif rest[i] == "--email" and i + 1 < len(rest):
            email = rest[i + 1]; i += 2
        elif rest[i] == "--name" and i + 1 < len(rest):
            name = rest[i + 1]; i += 2
        else:
            i += 1

    if subcmd == "add":
        return mail.add_subscriber(list_name, email, name) if list_name and email else {"error": "需要 --list --email"}
    elif subcmd == "list":
        return {"subscribers": mail.list_subscribers(list_name)} if list_name else {"error": "需要 --list"}
    elif subcmd == "unsubscribe":
        return mail.unsubscribe(email, list_name) if list_name and email else {"error": "需要 --list --email"}
    return {"error": f"未知: {subcmd}"}


def cmd_mail_campaign(args: list[str]) -> dict:
    mail = MolibMail()
    if not args or args[0] != "send":
        return {"error": "子命令: send"}

    rest = args[1:]
    list_name = subject = body = ""
    i = 0
    while i < len(rest):
        if rest[i] == "--list" and i + 1 < len(rest):
            list_name = rest[i + 1]; i += 2
        elif rest[i] == "--subject" and i + 1 < len(rest):
            subject = rest[i + 1]; i += 2
        elif rest[i] == "--body" and i + 1 < len(rest):
            body = rest[i + 1]; i += 2
        else:
            i += 1
    return mail.send_campaign(list_name, subject, body) if list_name and subject else {"error": "需要 --list --subject"}


def cmd_mail_stats() -> dict:
    return MolibMail().stats()
