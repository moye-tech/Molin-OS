"""
墨麟 — HAR 解析器 (HarParser)
从 HAR (HTTP Archive) 文件中提取 HTTP 请求和响应。
纯标准库，零外部依赖。

从 Integuru (Integuru-AI/Integuru) 提取的设计模式：
- Request 值对象：与具体序列化格式解耦
- Minified curl：去除 cookie/referer 头部减少 LLM 幻觉
- 自动过滤跟踪/分析类头部

用法:
    from molib.shared.network.har_parser import parse_har_file, HarRequest
    requests = parse_har_file("network_requests.har")
    for req_id, req in requests.items():
        print(req.to_minified_curl_command())
"""

import json
import re
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional, List
from datetime import datetime


# ── 过滤规则 ─────────────────────────────────────────────────────

# 应过滤的请求头部（分析/跟踪类）
_FILTERED_HEADERS = {
    "referer", "referrer", "origin",
    "cookie", "set-cookie",
    "sec-fetch-dest", "sec-fetch-mode", "sec-fetch-site", "sec-fetch-user",
    "sec-ch-ua", "sec-ch-ua-mobile", "sec-ch-ua-platform",
    "user-agent",
    "accept-encoding", "accept-language", "accept",
    "dnt", "te", "upgrade-insecure-requests",
    "pragma", "cache-control",
    "content-length",
}


# ── 值对象 ───────────────────────────────────────────────────────


@dataclass
class HarRequest:
    """HTTP 请求值对象 — 与序列化格式解耦"""

    method: str
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    query_params: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    timestamp: Optional[str] = None

    def to_curl_command(self) -> str:
        """将请求转为完整的 cURL 命令字符串"""
        parts = [f"curl -X {self.method}"]

        for key, val in sorted(self.headers.items()):
            parts.append(f"-H '{key}: {val}'")

        if self.query_params:
            query_str = "&".join(f"{k}={v}" for k, v in self.query_params.items())
            base = self.url.split("?")[0]
            parts.append(f"'{base}?{query_str}'")
        else:
            parts.append(f"'{self.url}'")

        if self.body:
            escaped = self.body.replace("'", "'\\''")
            parts.append(f"-d '{escaped}'")

        return " ".join(parts)

    def to_minified_curl_command(self) -> str:
        """去除 cookie/referer 等干扰头部的精简 curl 命令"""
        minified_headers = {
            k: v for k, v in self.headers.items()
            if k.lower() not in _FILTERED_HEADERS
        }
        parts = [f"curl -X {self.method}"]

        for key, val in sorted(minified_headers.items()):
            parts.append(f"-H '{key}: {val}'")

        if self.query_params:
            query_str = "&".join(f"{k}={v}" for k, v in self.query_params.items())
            base = self.url.split("?")[0]
            parts.append(f"'{base}?{query_str}'")
        else:
            parts.append(f"'{self.url}'")

        if self.body:
            escaped = self.body.replace("'", "'\\''")
            parts.append(f"-d '{escaped}'")

        return " ".join(parts)

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "method": self.method,
            "url": self.url,
            "headers": self.headers,
            "query_params": self.query_params,
            "body": self.body,
            "response_status": self.response_status,
            "response_body": self.response_body,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HarRequest":
        """从字典反序列化"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ── 解析逻辑 ──────────────────────────────────────────────────────


def _parse_query_string(url: str) -> Dict[str, str]:
    """从 URL 中提取查询参数"""
    if "?" not in url:
        return {}
    query = url.split("?", 1)[1]
    params = {}
    for pair in query.split("&"):
        if "=" in pair:
            k, v = pair.split("=", 1)
            params[k] = v
    return params


def _filter_headers(raw_headers: List[dict]) -> Dict[str, str]:
    """过滤并格式化请求头部"""
    filtered = {}
    for h in raw_headers:
        name = h.get("name", "").lower()
        if name not in _FILTERED_HEADERS:
            filtered[h["name"]] = h["value"]
    return filtered


def parse_har_file(har_path: str) -> Dict[str, HarRequest]:
    """
    解析 HAR 文件，返回请求标识符到 HarRequest 的映射。

    参数:
        har_path: HAR 文件路径

    返回:
        Dict[str, HarRequest] — key 为自动生成的请求标识符
    """
    with open(har_path, "r", encoding="utf-8") as f:
        har_data = json.load(f)

    entries = har_data.get("log", {}).get("entries", [])
    result: Dict[str, HarRequest] = {}

    for entry in entries:
        req = entry.get("request", {})
        resp = entry.get("response", {})

        url = req.get("url", "")
        method = req.get("method", "GET")

        request = HarRequest(
            method=method,
            url=url,
            headers=_filter_headers(req.get("headers", [])),
            query_params=_parse_query_string(url),
            body=req.get("postData", {}).get("text") if "postData" in req else None,
            response_status=resp.get("status"),
            response_body=resp.get("content", {}).get("text"),
            timestamp=entry.get("startedDateTime"),
        )

        req_id = f"{method}_{uuid.uuid4().hex[:8]}"
        result[req_id] = request

    return result


def parse_har_to_curl_list(har_path: str, minified: bool = True) -> List[str]:
    """
    快捷函数：将 HAR 文件解析为 cURL 命令列表。

    参数:
        har_path: HAR 文件路径
        minified: 是否使用精简版（去除干扰头部）

    返回:
        List[str] — cURL 命令列表
    """
    requests = parse_har_file(har_path)
    commands = []
    for req in requests.values():
        if minified:
            commands.append(req.to_minified_curl_command())
        else:
            commands.append(req.to_curl_command())
    return commands
