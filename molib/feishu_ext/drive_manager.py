"""飞书云空间文件管理 — 任务结果自动归档
适配自 molin-os-ultra v6.6.0 integrations/feishu/drive_manager.py
"""
from __future__ import annotations

import os
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")

_token: Optional[str] = None


async def _get_drive_token() -> Optional[str]:
    global _token
    if _token:
        return _token
    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        return None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET},
            )
            data = resp.json()
            if data.get("code") == 0:
                _token = data.get("tenant_access_token")
                return _token
    except Exception as e:
        logger.error(f"Drive token 异常: {e}")
    return None


async def _api_request(method: str, path: str, json_data: Optional[dict] = None) -> Optional[dict]:
    token = await _get_drive_token()
    if not token:
        return None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method,
                f"https://open.feishu.cn/open-apis{path}",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=json_data,
                timeout=15,
            )
            data = resp.json()
            if data.get("code") == 0:
                return data.get("data")
    except Exception as e:
        logger.warning(f"Drive 请求异常: {e}")
    return None


class FeishuDriveManager:
    """飞书云空间文件管理器"""
    def __init__(self):
        self._root_folder_token = os.getenv("FEISHU_DRIVE_ROOT_FOLDER", "")
        self._cache: Dict[str, str] = {}

    async def _ensure_or_create_folder(self, parent_token: str, folder_name: str) -> Optional[str]:
        cache_key = f"{parent_token}/{folder_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        data = await _api_request("GET", f"/drive/v1/files?folder_token={parent_token}")
        if data:
            for f in data.get("items", []):
                if f.get("name") == folder_name and f.get("type") == "folder":
                    token = f.get("token", "")
                    self._cache[cache_key] = token
                    return token

        data = await _api_request("POST", "/drive/v1/files", {
            "name": folder_name, "folder_token": parent_token, "type": "folder",
        })
        if data:
            token = data.get("token", "")
            self._cache[cache_key] = token
            return token
        return None

    async def archive_task_results(self, task_id: str, subsidiary: str,
                                   results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """归档任务结果到飞书云空间"""
        root = self._root_folder_token
        if not root:
            logger.warning("FEISHU_DRIVE_ROOT_FOLDER 未配置，跳过")
            return []

        date_str = datetime.now().strftime("%Y-%m-%d")
        folder = root
        for part in ["墨麟AI", subsidiary, date_str, task_id]:
            if part:
                folder = await self._ensure_or_create_folder(folder, part)
                if not folder:
                    return []

        links = []
        for r in results:
            agency = r.get("agency", "unknown")
            content = r.get("output", "") or r.get("report", "") or ""
            if not content:
                continue
            file_name = f"{agency}_result.md"
            data = await _api_request("POST", "/drive/v1/files", {
                "name": file_name, "folder_token": folder, "type": "doc",
            })
            if data:
                links.append({"agency": agency, "url": data.get("url", "")})
        return links


async def archive_execution_results(task_id: str, execution_result: Dict[str, Any]) -> List[Dict[str, str]]:
    """便捷函数：归档执行结果到云空间"""
    if os.getenv("FEISHU_DRIVE_ARCHIVE_ENABLED", "false").lower() != "true":
        return []
    try:
        manager = FeishuDriveManager()
        results = execution_result.get("results", [])
        if not results:
            return []
        first_agency = results[0].get("agency", "general") if results else "general"
        return await manager.archive_task_results(task_id, first_agency, results)
    except Exception as e:
        logger.warning(f"云空间归档失败: {e}")
        return []
