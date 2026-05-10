"""
墨域 CRM Worker 升级 — 从定义骨架到真实引擎 (twenty CRM 替代)
===========================================================
对标 twenty.com (20K★): 客户管理 · 销售管道 · 任务追踪
Mac M2: MolibDB 后端, SQLite 存证, <10MB 内存。

用法:
    python -m molib crm create --name "张三" --company "XX科技" --stage "leads"
    python -m molib crm list --stage negotiation
    python -m molib crm pipeline
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("molin.crm")

# MolibDB 作为 CRM 后端
DB = None


def _get_db():
    global DB
    if DB is None:
        from molib.infra.molib_db import MolibDB
        DB = MolibDB()
        # 确保集合存在
        existing = [c["name"] for c in DB.list_collections()]
        if "crm_contacts" not in existing:
            DB.create_collection("crm_contacts", {
                "name": "text", "company": "text", "email": "text",
                "phone": "text", "stage": "text", "notes": "text",
                "assigned_to": "text", "source": "text",
            })
            # 创建示例数据
            DB.create_record("crm_contacts", {
                "name": "张三", "company": "XX科技", "email": "zhang@xx.com",
                "stage": "leads", "source": "闲鱼",
            })
        if "crm_tasks" not in existing:
            DB.create_collection("crm_tasks", {
                "title": "text", "contact_id": "integer",
                "due_date": "text", "status": "text", "priority": "text",
            })
    return DB


PIPELINE_STAGES = [
    ("leads", "线索"),
    ("contacted", "已联系"),
    ("negotiation", "洽谈中"),
    ("proposal", "已报价"),
    ("won", "成交"),
    ("lost", "丢失"),
]

STAGE_FLOW = {
    "leads": ["contacted", "lost"],
    "contacted": ["negotiation", "lost"],
    "negotiation": ["proposal", "lost"],
    "proposal": ["won", "lost"],
    "won": [],
    "lost": [],
}


class CRM:
    """墨域 CRM — 真实客户管理引擎。"""

    def create_contact(self, name: str, company: str = "", email: str = "",
                       phone: str = "", stage: str = "leads", source: str = "") -> dict:
        db = _get_db()
        return db.create_record("crm_contacts", {
            "name": name, "company": company, "email": email,
            "phone": phone, "stage": stage, "source": source,
            "assigned_to": "", "notes": "",
        })

    def list_contacts(self, stage: str = "", limit: int = 50) -> list[dict]:
        db = _get_db()
        records = db.list_records("crm_contacts", limit)
        if stage:
            return [r for r in records if r.get("stage") == stage]
        return records

    def update_stage(self, contact_id: int, new_stage: str) -> dict:
        db = _get_db()
        contact = db.list_records("crm_contacts", 1)
        contact = next((r for r in contact if r["id"] == contact_id), None)
        if not contact:
            return {"error": "联系人不存在"}

        current = contact.get("stage", "leads")
        allowed = STAGE_FLOW.get(current, [])
        if new_stage not in allowed:
            return {"error": f"不允许 {current} → {new_stage}，允许: {allowed}"}

        return db.update_record("crm_contacts", contact_id, {"stage": new_stage})

    def pipeline(self) -> dict:
        """销售管道概览。"""
        db = _get_db()
        all_contacts = db.list_records("crm_contacts", 1000)

        stages_count = {}
        for stage_key, stage_name in PIPELINE_STAGES:
            stages_count[stage_key] = {
                "name": stage_name,
                "count": sum(1 for c in all_contacts if c.get("stage") == stage_key),
            }

        total = len(all_contacts)
        won = stages_count.get("won", {}).get("count", 0)
        conversion = f"{(won / max(total, 1)) * 100:.0f}%" if total > 0 else "N/A"

        return {
            "total_contacts": total,
            "conversion_rate": conversion,
            "pipeline": stages_count,
            "sources": list(set(c.get("source", "") for c in all_contacts if c.get("source"))),
        }

    def add_task(self, title: str, contact_id: int = 0, priority: str = "medium") -> dict:
        db = _get_db()
        return db.create_record("crm_tasks", {
            "title": title, "contact_id": contact_id,
            "due_date": datetime.now().isoformat()[:10],
            "status": "pending", "priority": priority,
        })


def cmd_crm_create(name: str, company: str = "", email: str = "", stage: str = "leads") -> dict:
    return CRM().create_contact(name, company, email, stage=stage)


def cmd_crm_list(stage: str = "") -> list:
    return CRM().list_contacts(stage)


def cmd_crm_pipeline() -> dict:
    return CRM().pipeline()
