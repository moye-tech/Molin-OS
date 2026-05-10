"""
墨麟OS — n8n REST 直连模块 (⭐65k)
===================================
补全 SwarmBridge 缺少的 10%：直接调用 n8n REST API 管理
workflow 的触发、状态查询、执行历史。

SwarmBridge 已覆盖 90%（Swarm 编排 + Webhook 触发），
本模块补全剩余的 workflow CRUD + execution history。

用法:
    from molib.infra.external.n8n_rest import trigger_workflow, list_workflows

前置: n8n 已通过 npx 可用 (npx n8n start)

集成点:
    CRM Worker: 自动化序列触发
    BD Worker: LinkedIn私信自动化
    CustomerService Worker: 多渠道消息路由
"""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Optional

N8N_BASE = os.environ.get("N8N_API_URL", "http://127.0.0.1:5678/api/v1")
N8N_KEY = os.environ.get("N8N_API_KEY", "")


def _headers() -> dict:
    h = {"Content-Type": "application/json"}
    if N8N_KEY:
        h["X-N8N-API-KEY"] = N8N_KEY
    return h


def _request(method: str, path: str, data: dict = None) -> dict:
    """通用 n8n REST 请求。"""
    try:
        import urllib.request

        url = f"{N8N_BASE}{path}"
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=_headers(), method=method)

        resp = urllib.request.urlopen(req, timeout=30)
        return {"data": json.loads(resp.read()), "status": "success"}
    except Exception as e:
        return {"error": str(e), "status": "n8n_unavailable"}


def list_workflows(active_only: bool = False) -> dict:
    """列出所有 workflow。"""
    result = _request("GET", "/workflows")
    if result.get("status") != "success":
        return result

    workflows = []
    for w in result.get("data", {}).get("data", []):
        if active_only and not w.get("active"):
            continue
        workflows.append({
            "id": w.get("id"),
            "name": w.get("name"),
            "active": w.get("active"),
            "updated_at": w.get("updatedAt"),
        })

    return {"workflows": workflows, "count": len(workflows), "source": "n8n"}


def trigger_workflow(workflow_id: str, payload: dict = None) -> dict:
    """
    触发指定 workflow（通过 Webhook 节点）。

    前提：workflow 中已配置 Webhook 触发器节点。
    """
    return _request("POST", f"/workflows/{workflow_id}/activate", {})


def get_executions(workflow_id: str = "", limit: int = 10) -> dict:
    """查询执行历史。"""
    path = "/executions"
    if workflow_id:
        path += f"?workflowId={workflow_id}"
    path += f"&limit={limit}"

    result = _request("GET", path)
    if result.get("status") != "success":
        return result

    executions = []
    for e in result.get("data", {}).get("data", []):
        executions.append({
            "id": e.get("id"),
            "workflow_name": e.get("workflowName", ""),
            "status": e.get("status"),
            "started_at": e.get("startedAt"),
            "stopped_at": e.get("stoppedAt"),
        })

    return {"executions": executions, "count": len(executions), "source": "n8n"}


def health_check() -> dict:
    """检查 n8n 是否可达。"""
    try:
        import urllib.request
        req = urllib.request.Request(f"{N8N_BASE}/health", headers=_headers())
        resp = urllib.request.urlopen(req, timeout=5)
        return {"healthy": True, "data": json.loads(resp.read()), "source": "n8n"}
    except Exception as e:
        return {"healthy": False, "error": str(e), "hint": "npx n8n start"}


def create_webhook_workflow(name: str, webhook_path: str, http_method: str = "POST") -> dict:
    """
    以编程方式创建简单的 Webhook workflow。

    这是 SwarmBridge 不覆盖的部分：直接通过 n8n REST API 创建 workflow JSON。
    """
    workflow_json = {
        "name": name,
        "nodes": [
            {
                "parameters": {"path": webhook_path, "httpMethod": http_method},
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "position": [250, 300],
            },
            {
                "parameters": {"content": "## Workflow triggered by Molin-OS"},
                "name": "Note",
                "type": "n8n-nodes-base.stickyNote",
                "position": [600, 300],
            },
        ],
        "connections": {},
    }

    return _request("POST", "/workflows", workflow_json)
