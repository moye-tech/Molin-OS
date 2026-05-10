"""
墨麟AIOS 夸克网盘云备份 — QuarkDrive
======================================

通过夸克网盘 WebDAV 协议实现目录增量备份。对比文件修改时间，
仅上传变更文件，减少带宽与 API 调用。

环境变量配置：
    QUARK_WEBDAV_URL   夸克 WebDAV 服务地址（如 https://webdav.quark.cn/...）
    QUARK_WEBDAV_USER  用户名
    QUARK_WEBDAV_PASS  密码 / 应用令牌

降级策略：
    若未配置上述任一环境变量，backup_directory() 返回 "skipped" 状态，
    不抛出异常，保障调用方无需判断配置是否存在。

依赖：Python 标准库 + requests

参考项目：
- 夸克网盘 WebDAV 协议文档
- rclone WebDAV backend
"""

from __future__ import annotations

import logging
import os
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 环境变量键名
# ═══════════════════════════════════════════════════════════════

_ENV_URL  = "QUARK_WEBDAV_URL"
_ENV_USER = "QUARK_WEBDAV_USER"
_ENV_PASS = "QUARK_WEBDAV_PASS"

# 请求超时（秒）
_DEFAULT_TIMEOUT = 30


# ═══════════════════════════════════════════════════════════════
# 公共 API
# ═══════════════════════════════════════════════════════════════

def backup_directory(
    local_path: str,
    remote_path: str = "/",
    *,
    dry_run: bool = False,
    timeout: int = _DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """将本地目录增量同步到夸克网盘。

    增量逻辑：
    1. 遍历本地目录，收集所有文件及其 mtime
    2. 通过 PROPFIND 获取远程目录清单（含 getlastmodified）
    3. 仅上传 mtime 更新的文件（或远程不存在的文件）
    4. 上传使用 PUT 请求

    Args:
        local_path:  本地目录绝对路径
        remote_path: 远程根路径（WebDAV 路径，默认 "/"）
        dry_run:     仅列出待上传文件，不实际执行上传
        timeout:     HTTP 请求超时秒数

    Returns:
        {
            "status": "ok" | "skipped" | "partial" | "error",
            "local_path": str,
            "remote_path": str,
            "files_scanned": int,       # 扫描到的本地文件数
            "files_uploaded": int,      # 实际/计划上传数
            "files_skipped": int,       # 跳过（无需更新）文件数
            "files_failed": int,        # 上传失败数
            "details": [...],           # 每个文件的操作明细
            "error": str | None,
        }
    """
    result: Dict[str, Any] = {
        "status": "ok",
        "local_path": str(local_path),
        "remote_path": str(remote_path),
        "files_scanned": 0,
        "files_uploaded": 0,
        "files_skipped": 0,
        "files_failed": 0,
        "details": [],
        "error": None,
    }

    # ── 1. 检查环境变量 ────────────────────────────────
    base_url = os.getenv(_ENV_URL, "").rstrip("/")
    username = os.getenv(_ENV_USER, "")
    password = os.getenv(_ENV_PASS, "")

    if not base_url or not username or not password:
        logger.info("夸克 WebDAV 未配置，跳过备份。请设置 %s / %s / %s",
                     _ENV_URL, _ENV_USER, _ENV_PASS)
        result["status"] = "skipped"
        result["error"] = "WebDAV credentials not configured"
        return result

    # ── 2. 校验本地目录 ────────────────────────────────
    local = Path(local_path).resolve()
    if not local.exists():
        result["status"] = "error"
        result["error"] = f"Local path does not exist: {local}"
        return result
    if not local.is_dir():
        result["status"] = "error"
        result["error"] = f"Local path is not a directory: {local}"
        return result

    # ── 3. 扫描本地文件（含 mtime） ────────────────────
    local_files: Dict[str, float] = {}
    for f in local.rglob("*"):
        if f.is_file():
            rel = str(f.relative_to(local))
            # 统一使用正斜杠作为路径分隔符（WebDAV 标准）
            rel_normalized = rel.replace("\\", "/")
            local_files[rel_normalized] = f.stat().st_mtime

    result["files_scanned"] = len(local_files)
    if not local_files:
        logger.info("本地目录为空，无文件可备份: %s", local)
        return result

    # ── 4. 获取远程清单 ────────────────────────────────
    remote_mtimes: Dict[str, float] = _fetch_remote_files(
        base_url, username, password, remote_path, timeout
    )

    # ── 5. 确定待上传列表 ──────────────────────────────
    to_upload: List[str] = []
    for rel_path, local_mtime in local_files.items():
        remote_mtime = remote_mtimes.get(rel_path)
        if remote_mtime is None:
            # 远程不存在 → 上传
            to_upload.append(rel_path)
        elif local_mtime > remote_mtime:
            # 本地更新 → 上传
            to_upload.append(rel_path)
        else:
            result["files_skipped"] += 1
            result["details"].append({
                "file": rel_path,
                "action": "skipped",
                "reason": "remote is up-to-date",
            })

    if not to_upload:
        logger.info("所有文件已是最新，无需上传")
        return result

    # ── 6. 上传（或 dry_run） ──────────────────────────
    if dry_run:
        for rel_path in to_upload:
            result["details"].append({
                "file": rel_path,
                "action": "would_upload",
                "reason": "dry_run",
            })
        result["files_uploaded"] = len(to_upload)
        result["status"] = "ok"
        return result

    for rel_path in to_upload:
        local_file = local / rel_path
        remote_url = _build_remote_url(base_url, remote_path, rel_path)
        upload_result = _upload_file(
            remote_url, username, password, str(local_file), timeout
        )
        detail = {
            "file": rel_path,
            "action": "uploaded" if upload_result["ok"] else "failed",
            "error": upload_result.get("error"),
        }
        result["details"].append(detail)
        if upload_result["ok"]:
            result["files_uploaded"] += 1
        else:
            result["files_failed"] += 1

    # ── 7. 汇总状态 ────────────────────────────────────
    if result["files_failed"] > 0:
        result["status"] = "partial" if result["files_uploaded"] > 0 else "error"
        result["error"] = f"{result['files_failed']} file(s) failed to upload"
    else:
        result["status"] = "ok"

    logger.info(
        "夸克备份完成: scanned=%d uploaded=%d skipped=%d failed=%d",
        result["files_scanned"], result["files_uploaded"],
        result["files_skipped"], result["files_failed"],
    )
    return result


# ═══════════════════════════════════════════════════════════════
# 私有辅助函数
# ═══════════════════════════════════════════════════════════════

def _build_remote_url(base_url: str, remote_root: str, rel_path: str) -> str:
    """构建完整的远程文件 URL。

    Args:
        base_url:    WebDAV 基础地址（如 https://webdav.quark.cn/dav）
        remote_root: 远程根路径（如 /backups）
        rel_path:    相对路径（如 subdir/file.txt）

    Returns:
        https://webdav.quark.cn/dav/backups/subdir/file.txt
    """
    root = remote_root.rstrip("/")
    path = rel_path.lstrip("/")
    if root:
        return f"{base_url}/{root}/{path}"
    return f"{base_url}/{path}"


def _fetch_remote_files(
    base_url: str,
    username: str,
    password: str,
    remote_path: str,
    timeout: int,
) -> Dict[str, float]:
    """通过 PROPFIND 获取远程目录中的文件列表及其最后修改时间。

    Returns:
        {relative_path: mtime_timestamp, ...}
    """
    url = _build_remote_url(base_url, remote_path, "")
    url = url.rstrip("/") + "/"

    headers = {
        "Depth": "1",
        "Content-Type": "application/xml; charset=utf-8",
    }
    # 精简 PROPFIND body — 只请求 getlastmodified
    body = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<D:propfind xmlns:D="DAV:">'
        "<D:prop>"
        "<D:getlastmodified/>"
        "<D:getcontentlength/>"
        "</D:prop>"
        "</D:propfind>"
    )

    try:
        resp = requests.request(
            "PROPFIND", url,
            auth=(username, password),
            headers=headers,
            data=body,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        logger.warning("PROPFIND 请求失败: %s", exc)
        return {}

    if resp.status_code not in (200, 207):
        logger.warning("PROPFIND 返回非预期状态码: %d", resp.status_code)
        return {}

    return _parse_propfind_response(resp.text, remote_path)


def _parse_propfind_response(xml_text: str, remote_root: str) -> Dict[str, float]:
    """用正则解析 PROPFIND 响应（避免引入 xml 库依赖）。

    提取 <D:href> 路径与 <D:getlastmodified> 时间，转为 Unix 时间戳。
    """
    import re

    result: Dict[str, float] = {}

    # 匹配每个 <D:response> 块
    blocks = re.split(r"<D:response>|</D:response>", xml_text)
    root_clean = remote_root.strip("/")

    for block in blocks:
        # 提取 href
        href_match = re.search(r"<D:href>([^<]+)</D:href>", block)
        if not href_match:
            continue
        href = href_match.group(1)

        # 解码 URL 编码
        from urllib.parse import unquote
        href = unquote(href)

        # 转为相对路径
        if root_clean:
            prefix = f"/{root_clean}/"
            if href.startswith(prefix):
                href = href[len(prefix):]
            else:
                continue
        else:
            href = href.lstrip("/")

        if not href or href.endswith("/"):
            continue  # 跳过目录

        # 提取 lastmodified
        lm_match = re.search(
            r"<D:getlastmodified>([^<]+)</D:getlastmodified>", block
        )
        if not lm_match:
            continue
        lm_str = lm_match.group(1).strip()

        # 解析时间（RFC 1123 格式: Mon, 02 Jan 2006 15:04:05 GMT）
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(lm_str)
            result[href] = dt.timestamp()
        except (ValueError, TypeError):
            logger.debug("无法解析远程文件时间: %s -> %s", href, lm_str)
            continue

    return result


def _upload_file(
    remote_url: str,
    username: str,
    password: str,
    local_file_path: str,
    timeout: int,
) -> Dict[str, Any]:
    """上传单个文件到 WebDAV。

    Args:
        remote_url:      完整远程文件 URL
        username:        WebDAV 用户名
        password:        WebDAV 密码
        local_file_path: 本地文件路径
        timeout:         HTTP 超时

    Returns:
        {"ok": True/False, "error": str|None}
    """
    try:
        file_size = os.path.getsize(local_file_path)
        with open(local_file_path, "rb") as fh:
            resp = requests.put(
                remote_url,
                data=fh,
                auth=(username, password),
                timeout=timeout,
                headers={
                    "Content-Type": "application/octet-stream",
                    "Content-Length": str(file_size),
                },
            )
        if resp.status_code in (200, 201, 204):
            return {"ok": True}
        else:
            logger.warning("文件上传失败 (%d): %s", resp.status_code, remote_url)
            return {"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except requests.RequestException as exc:
        logger.error("文件上传异常: %s -> %s", local_file_path, exc)
        return {"ok": False, "error": str(exc)}
    except OSError as exc:
        logger.error("读取本地文件失败: %s -> %s", local_file_path, exc)
        return {"ok": False, "error": str(exc)}
