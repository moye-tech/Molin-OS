"""
Feishu Bitable — 飞书多维表格自动写入
=====================================
Three preset tables: 订单/内容/财务
Supports: create_record, batch_create, list_records, get_schema
Uses Feishu Open API + tenant_access_token.

Mac M2: API-based, zero local resource consumption.
Credentials from environment: FEISHU_APP_ID, FEISHU_APP_SECRET
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger("molin.feishu_bitable")

# ═══════════════════════════════════════════════════════════════
# 表结构定义
# ═══════════════════════════════════════════════════════════════

TABLE_SCHEMAS = {
    "orders": {
        "name": "订单表",
        "fields": [
            {"field_name": "order_id", "type": 1},       # 文本
            {"field_name": "customer", "type": 1},
            {"field_name": "product", "type": 1},
            {"field_name": "amount", "type": 6},          # 数字
            {"field_name": "status", "type": 3},           # 单选
            {"field_name": "created_at", "type": 5},       # 日期
            {"field_name": "platform", "type": 1},         # 文本
        ],
    },
    "content": {
        "name": "内容表",
        "fields": [
            {"field_name": "content_id", "type": 1},
            {"field_name": "title", "type": 1},
            {"field_name": "platform", "type": 1},
            {"field_name": "word_count", "type": 6},
            {"field_name": "status", "type": 3},
            {"field_name": "published_at", "type": 5},
            {"field_name": "url", "type": 17},             # 链接
        ],
    },
    "finance": {
        "name": "财务表",
        "fields": [
            {"field_name": "entry_id", "type": 1},
            {"field_name": "type", "type": 3},             # 收入/支出
            {"field_name": "amount", "type": 6},
            {"field_name": "category", "type": 1},
            {"field_name": "description", "type": 1},
            {"field_name": "date", "type": 5},
            {"field_name": "provider", "type": 1},
        ],
    },
}

# Field type mapping
FIELD_TYPE_NAMES = {
    1: "Text",
    2: "Number",
    3: "SingleSelect",
    4: "MultiSelect",
    5: "DateTime",
    6: "Number",
    7: "Checkbox",
    15: "Attachment",
    17: "Url",
    18: "Barcode",
    21: "Phone",
    22: "Email",
}

BASE_URL = "https://open.feishu.cn/open-apis"


class FeishuBitableClient:
    """飞书多维表格写入客户端。"""

    def __init__(self, app_id: str = "", app_secret: str = ""):
        self.app_id = app_id or os.getenv("FEISHU_APP_ID", "")
        self.app_secret = app_secret or os.getenv("FEISHU_APP_SECRET", "")
        self._token: Optional[str] = None
        self._token_expiry: float = 0

    @property
    def configured(self) -> bool:
        return bool(self.app_id and self.app_secret)

    # ── Auth ────────────────────────────────────────────────

    def _get_token(self) -> str:
        """获取 tenant_access_token（带缓存）。"""
        import time as _time
        if self._token and _time.time() < self._token_expiry:
            return self._token

        url = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
        data = json.dumps({"app_id": self.app_id, "app_secret": self.app_secret}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())
            if result.get("code") != 0:
                raise RuntimeError(f"Token error: {result.get('msg')}")
            self._token = result["tenant_access_token"]
            self._token_expiry = _time.time() + result.get("expire", 7200) - 300
            return self._token
        except Exception as e:
            logger.error(f"获取飞书token失败: {e}")
            raise

    # ── API 请求包装 ──────────────────────────────────────

    def _api(self, method: str, path: str, body: Optional[dict] = None) -> dict[str, Any]:
        """通用飞书 API 调用。"""
        token = self._get_token()
        url = f"{BASE_URL}{path}"
        data = json.dumps(body).encode() if body else None
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        }
        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read())
            if result.get("code") != 0:
                raise RuntimeError(f"API error [{path}]: {result.get('msg')} (code={result.get('code')})")
            return result.get("data", {})
        except Exception as e:
            logger.error(f"飞书API调用失败: {method} {path} - {e}")
            raise

    # ── Table Operations ────────────────────────────────────

    def get_table_meta(self, app_token: str, table_id: str) -> dict[str, Any]:
        """获取多维表格的字段元数据。"""
        return self._api("GET", f"/bitable/v1/apps/{app_token}/tables/{table_id}/fields")

    def create_record(self, app_token: str, table_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        """添加单条记录。"""
        body = {"fields": fields}
        return self._api("POST", f"/bitable/v1/apps/{app_token}/tables/{table_id}/records", body)

    def update_record(self, app_token: str, table_id: str, record_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        """更新单条记录。"""
        body = {"fields": fields}
        return self._api("PUT", f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}", body)

    def list_records(self, app_token: str, table_id: str, filter_str: str = "", page_size: int = 100) -> list[dict[str, Any]]:
        """查询记录列表。"""
        params = f"?page_size={page_size}"
        if filter_str:
            params += f"&filter={filter_str}"
        result = self._api("GET", f"/bitable/v1/apps/{app_token}/tables/{table_id}/records{params}")
        return result.get("items", [])

    def batch_create(self, app_token: str, table_id: str, records: list[dict[str, Any]]) -> dict[str, Any]:
        """批量添加记录。"""
        body = {"records": [{"fields": r} for r in records]}
        return self._api("POST", f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create", body)

    # ── Smart Write Helpers ─────────────────────────────────

    def write_order(self, app_token: str, table_id: str, order_data: dict[str, Any]) -> dict[str, Any]:
        """写入订单记录。自动将 dict 映射到 订单表 字段。"""
        fields = {
            "order_id": str(order_data.get("order_id", "")),
            "customer": str(order_data.get("customer", "")),
            "product": str(order_data.get("product", "")),
            "amount": float(order_data.get("amount", 0)),
            "status": str(order_data.get("status", "pending")),
            "created_at": int(order_data.get("created_at", datetime.now().timestamp()) * 1000),
            "platform": str(order_data.get("platform", "")),
        }
        return self.create_record(app_token, table_id, fields)

    def write_content(self, app_token: str, table_id: str, content_data: dict[str, Any]) -> dict[str, Any]:
        """写入内容记录。映射到 内容表 字段。"""
        fields = {
            "content_id": str(content_data.get("content_id", "")),
            "title": str(content_data.get("title", "")),
            "platform": str(content_data.get("platform", "")),
            "word_count": int(content_data.get("word_count", 0)),
            "status": str(content_data.get("status", "draft")),
            "published_at": int(content_data.get("published_at", 0) * 1000) if content_data.get("published_at") else int(datetime.now().timestamp() * 1000),
            "url": str(content_data.get("url", "")),
        }
        return self.create_record(app_token, table_id, fields)

    def write_finance(self, app_token: str, table_id: str, finance_data: dict[str, Any]) -> dict[str, Any]:
        """写入财务记录。映射到 财务表 字段。"""
        fields = {
            "entry_id": str(finance_data.get("entry_id", "")),
            "type": str(finance_data.get("type", "支出")),
            "amount": float(finance_data.get("amount", 0)),
            "category": str(finance_data.get("category", "")),
            "description": str(finance_data.get("description", "")),
            "date": int(finance_data.get("date", datetime.now().timestamp()) * 1000),
            "provider": str(finance_data.get("provider", "")),
        }
        return self.create_record(app_token, table_id, fields)


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def cmd_bitable_write(table: str, app_token: str = "", table_id: str = ""):
    """示范写入（需真实凭据）。"""
    client = FeishuBitableClient()
    if not client.configured:
        print("⚠️  FEISHU_APP_ID / FEISHU_APP_SECRET 未配置，无法调用真实API")
        print(f"   表结构已就绪: {list(TABLE_SCHEMAS.keys())}")
        return

    print(f"📋 准备写入 {TABLE_SCHEMAS.get(table, {}).get('name', table)}...")
    print(f"   App Token: {app_token}")
    print(f"   Table ID: {table_id}")
    print(f"   ⚠️ 请在配置环境变量后调用真实 API")


def cmd_bitable_list(table: str, app_token: str = "", table_id: str = ""):
    client = FeishuBitableClient()
    if not client.configured:
        print("⚠️  未配置")
        return
    records = client.list_records(app_token, table_id)
    print(f"📋 {table}: {len(records)} 条")
    for r in records[:10]:
        print(f"   {r}")


def cmd_bitable_schema():
    for key, schema in TABLE_SCHEMAS.items():
        print(f"\n📋 {schema['name']} ({key})")
        print(f"   字段数: {len(schema['fields'])}")
        for f in schema["fields"]:
            ftype = FIELD_TYPE_NAMES.get(f["type"], f"Type({f['type']})")
            print(f"   • {f['field_name']}: {ftype}")
