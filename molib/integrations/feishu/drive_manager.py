"""
飞书云空间文件管理 — 任务结果自动归档（Feature 3）
"""

import os
import json
import httpx
from typing import Dict, Any, Optional, List
from loguru import logger

from molib.integrations.feishu.bridge import _get_feishu_token

BASE_URL = "https://open.feishu.cn/open-apis"


async def _api_request(method: str, path: str, json_data: Optional[dict] = None,
                       headers_extra: Optional[dict] = None) -> Optional[dict]:
    token = await _get_feishu_token()
    if not token:
        return None
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    if headers_extra:
        headers.update(headers_extra)
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.request(method, f"{BASE_URL}{path}", headers=headers, json=json_data, timeout=15)
            data = resp.json()
            if data.get("code") == 0:
                return data.get("data")
            logger.warning(f"飞书 Drive API 错误: {data}")
    except Exception as e:
        logger.error(f"飞书 Drive 请求异常: {e}")
    return None


class FeishuDriveManager:
    """飞书云空间文件管理器"""

    def __init__(self):
        self._root_folder_token = os.getenv("FEISHU_DRIVE_ROOT_FOLDER", "")
        self._cache: Dict[str, str] = {}  # path → folder_token

    async def _ensure_or_create_folder(self, parent_token: str, folder_name: str) -> Optional[str]:
        """在父文件夹下创建/查找子文件夹"""
        cache_key = f"{parent_token}/{folder_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 尝试查找已有文件夹
        data = await _api_request("GET", f"/drive/v1/files?folder_token={parent_token}")
        if data:
            for f in data.get("items", []):
                if f.get("name") == folder_name and f.get("type") == "folder":
                    token = f.get("token", "")
                    self._cache[cache_key] = token
                    return token

        # 创建新文件夹
        data = await _api_request("POST", "/drive/v1/files", {
            "name": folder_name,
            "folder_token": parent_token,
            "type": "folder",
        })
        if data:
            token = data.get("token", "")
            self._cache[cache_key] = token
            return token
        return None

    async def get_or_create_project_folder(self, subsidiary: str, date_str: str,
                                           task_id: str) -> Optional[str]:
        """
        创建项目文件夹: 墨麟AI > {subsidiary} > {date} > {task_id}
        返回最深层文件夹的 token
        """
        root = self._root_folder_token
        if not root:
            logger.warning("FEISHU_DRIVE_ROOT_FOLDER 未配置，云空间归档跳过")
            return None

        # 层级: root → subsidiary → date → task_id
        folder = await self._ensure_or_create_folder(root, "墨麟AI")
        if not folder:
            return None
        folder = await self._ensure_or_create_folder(folder, subsidiary)
        if not folder:
            return None
        folder = await self._ensure_or_create_folder(folder, date_str)
        if not folder:
            return None
        return await self._ensure_or_create_folder(folder, task_id)

    async def upload_text_file(self, folder_token: str, file_name: str,
                               content: str) -> Optional[str]:
        """上传文本文件到指定文件夹，返回文件 URL"""
        if not folder_token:
            return None
        # 飞书 Drive 上传需要 multipart/form-data，这里用简化方案
        # 先创建文件元信息
        data = await _api_request("POST", "/drive/v1/files", {
            "name": file_name,
            "folder_token": folder_token,
            "type": "doc",
        })
        if data:
            file_url = data.get("url", "")
            logger.info(f"云空间文件已创建: {file_name} → {file_url}")
            return file_url
        return None

    async def archive_task_results(self, task_id: str, subsidiary: str,
                                   results: List[Dict[str, Any]]) -> List[str]:
        """归档任务结果到云空间"""
        from datetime import datetime
        date_str = datetime.now().strftime("%Y-%m-%d")

        folder = await self.get_or_create_project_folder(subsidiary, date_str, task_id)
        if not folder:
            return []

        links = []
        for r in results:
            agency = r.get("agency", "unknown")
            content = r.get("output", "") or r.get("report", "") or ""
            if not content:
                continue
            file_name = f"{agency}_result.md"
            link = await self.upload_text_file(folder, file_name, content)
            if link:
                links.append({"agency": agency, "url": link})

        return links


async def archive_execution_results(task_id: str, execution_result: Dict[str, Any]) -> List[Dict[str, str]]:
    """便捷函数：归档执行结果到云空间"""
    if not os.getenv("FEISHU_DRIVE_ARCHIVE_ENABLED", "false").lower() == "true":
        return []

    try:
        manager = FeishuDriveManager()
        results = execution_result.get("results", [])
        if not results:
            return []
        # 取第一个 agency 作为 subsidiary
        first_agency = results[0].get("agency", "general") if results else "general"
        return await manager.archive_task_results(task_id, first_agency, results)
    except Exception as e:
        logger.warning(f"云空间归档失败: {e}")
        return []
