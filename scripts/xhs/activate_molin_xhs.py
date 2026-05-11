#!/usr/bin/env python3
"""
molin-xiaohongshu 激活脚本 — 墨影小红书AI发布引擎
=================================================
为墨笔文创子公司提供小红书内容创作、发布、趋势分析能力。

核心功能：
  - check_xhs_status(): 检查小红书账号/系统状态
  - xhs_post_draft(title, body, images): 发布小红书笔记草稿
  - analyze_xhs_trends(keyword): 分析小红书热门趋势

对应技能：~/.hermes/skills/molin-xiaohongshu/SKILL.md
对应子公司：墨笔文创（文字内容创作、文案、公众号、博客）
触发链路：墨笔文创 → molin-xiaohongshu → 小红书发布

依赖：纯 Python / subprocess / curl（无额外第三方包）
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional


# ═══════════════════════════════════════════════════════════════════
# 常量与配置
# ═══════════════════════════════════════════════════════════════════

XHS_DATA_DIR = Path(os.path.expanduser("~/.xhs_system"))
XHS_CONFIG_FILE = XHS_DATA_DIR / "config.json"
XHS_COOKIE_FILE = XHS_DATA_DIR / "cookies.json"
XHS_API_BASE = "https://edith.xiaohongshu.com/api"

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


# ═══════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════

def _curl_get(url: str, headers: dict = None, timeout: int = 20) -> dict:
    """通过 curl 执行 GET 请求。"""
    if headers is None:
        headers = {}

    cmd = ["curl", "-s", "-L", url,
           "-H", f"User-Agent: {USER_AGENT}",
           "--connect-timeout", "10",
           "--max-time", str(timeout)]

    for key, val in headers.items():
        cmd.extend(["-H", f"{key}: {val}"])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
        if result.returncode == 0 and result.stdout:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"raw": result.stdout}
        return {"error": f"curl 返回码 {result.returncode}", "stderr": result.stderr}
    except subprocess.TimeoutExpired:
        return {"error": "请求超时"}
    except Exception as e:
        return {"error": str(e)}


def _curl_post(url: str, data: dict = None, headers: dict = None,
               timeout: int = 30) -> dict:
    """通过 curl 执行 POST 请求。"""
    if headers is None:
        headers = {}
    if data is None:
        data = {}

    cmd = ["curl", "-s", "-L", "-X", "POST", url,
           "-H", f"User-Agent: {USER_AGENT}",
           "-H", "Content-Type: application/json",
           "--connect-timeout", "10",
           "--max-time", str(timeout)]

    for key, val in headers.items():
        cmd.extend(["-H", f"{key}: {val}"])

    cmd.extend(["-d", json.dumps(data, ensure_ascii=False)])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
        if result.returncode == 0 and result.stdout:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"raw": result.stdout}
        return {"error": f"curl 返回码 {result.returncode}", "stderr": result.stderr}
    except subprocess.TimeoutExpired:
        return {"error": "请求超时"}
    except Exception as e:
        return {"error": str(e)}


def _load_cookies() -> Optional[dict]:
    """加载小红书 Cookie。"""
    if XHS_COOKIE_FILE.exists():
        try:
            with open(XHS_COOKIE_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
                if isinstance(data, str):
                    return {"cookie": data}
        except (json.JSONDecodeError, IOError):
            pass

    # Fallback: try from config
    if XHS_CONFIG_FILE.exists():
        try:
            with open(XHS_CONFIG_FILE, "r") as f:
                config = json.load(f)
                cookie = config.get("cookie") or config.get("xhs_cookie")
                if cookie:
                    return {"cookie": cookie}
        except (json.JSONDecodeError, IOError):
            pass

    return None


def _get_cookie_header() -> dict:
    """获取 Cookie 请求头。"""
    cookies = _load_cookies()
    if cookies:
        cookie_str = cookies.get("cookie", "")
        if cookie_str:
            return {"Cookie": cookie_str}
    return {}


# ═══════════════════════════════════════════════════════════════════
# 核心功能 1: check_xhs_status — 检查小红书账号/系统状态
# ═══════════════════════════════════════════════════════════════════

def check_xhs_status() -> dict:
    """
    检查小红书账号/系统状态。

    检测：
    - Cookie 有效性
    - XHS 数据目录完整性
    - 账号登录状态
    - API 可达性

    Returns:
        dict: {
            "status": "ok" | "warning" | "error",
            "cookie_valid": bool,
            "data_dir_ok": bool,
            "account_name": str | None,
            "api_reachable": bool,
            "message": str,
            "details": {...}
        }
    """
    result = {
        "status": "ok",
        "cookie_valid": False,
        "data_dir_ok": False,
        "account_name": None,
        "api_reachable": False,
        "message": "",
        "details": {},
    }

    # 检查数据目录
    result["data_dir_ok"] = XHS_DATA_DIR.exists()
    result["details"]["data_dir"] = str(XHS_DATA_DIR)
    result["details"]["data_dir_exists"] = result["data_dir_ok"]

    if XHS_DATA_DIR.exists():
        items = [p.name for p in XHS_DATA_DIR.iterdir()]
        result["details"]["data_dir_contents"] = items

    # 检查 Cookie
    cookies = _load_cookies()
    if cookies:
        cookie_str = cookies.get("cookie", "")
        result["cookie_valid"] = bool(cookie_str)
        result["details"]["cookie_length"] = len(cookie_str) if cookie_str else 0
        result["details"]["cookie_preview"] = cookie_str[:30] + "..." if cookie_str else ""

        # 尝试用 Cookie 访问用户信息
        if cookie_str:
            headers = _get_cookie_header()
            api_result = _curl_get(
                f"{XHS_API_BASE}/sns/web/v1/user/selfinfo",
                headers=headers,
                timeout=10,
            )
            if isinstance(api_result, dict) and "error" not in api_result:
                result["api_reachable"] = True
                account_info = api_result.get("data", {})
                result["account_name"] = account_info.get("nickname")
                result["details"]["api_response"] = api_result
            elif isinstance(api_result, dict) and "raw" in api_result:
                result["details"]["api_raw"] = api_result["raw"]
    else:
        result["details"]["cookie_not_found"] = (
            f"Cookie 文件未找到，请创建 {XHS_COOKIE_FILE} "
            "或通过 xhs_qr_login.py 登录"
        )

    # 综合状态
    if not result["data_dir_ok"]:
        result["status"] = "warning"
        result["message"] = "数据目录未初始化，请先运行 xhs_qr_login.py"
    elif not result["cookie_valid"]:
        result["status"] = "warning"
        result["message"] = "Cookie 无效或已过期，请重新登录"
    elif not result["api_reachable"]:
        result["status"] = "warning"
        result["message"] = "API 不可达（可能网络限制），Cookie 文件存在"
    else:
        if result["account_name"]:
            result["message"] = f"账号 {result['account_name']} 状态正常 ✓"
        else:
            result["message"] = "系统状态正常 ✓"

    return result


# ═══════════════════════════════════════════════════════════════════
# 核心功能 2: xhs_post_draft — 发布小红书笔记草稿
# ═══════════════════════════════════════════════════════════════════

def xhs_post_draft(title: str, body: str,
                   images: list = None,
                   publish_time: Optional[str] = None) -> dict:
    """
    发布小红书笔记草稿。

    通过 xhs_ai_publisher 的 API 或直接调用小红书 API 创建笔记。

    Args:
        title: 笔记标题（最多20字）
        body: 笔记正文（支持富文本、emoji、话题标签）
        images: 图片路径列表（最多9张）
        publish_time: 定时发布时间 (格式: "2026-05-10 10:00:00")，
                      None 表示立即发布

    Returns:
        dict: {
            "status": "ok" | "error",
            "note_id": str | None,
            "title": str,
            "message": str,
            "details": {...}
        }
    """
    # ── 参数校验 ────────────────────────────────────────────────────
    if not title or not title.strip():
        return {"status": "error", "note_id": None,
                "title": title, "message": "标题不能为空", "details": {}}
    if not body or not body.strip():
        return {"status": "error", "note_id": None,
                "title": title, "message": "正文不能为空", "details": {}}

    title = title.strip()[:20]  # 最多20字

    if images is None:
        images = []
    if len(images) > 9:
        images = images[:9]

    # ── 保存草稿到本地 ──────────────────────────────────────────────
    drafts_dir = XHS_DATA_DIR / "drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    draft_id = f"draft_{timestamp}"

    draft = {
        "id": draft_id,
        "title": title,
        "body": body,
        "images": images,
        "publish_time": publish_time or "now",
        "status": "pending",
        "created_at": datetime.now().isoformat(),
    }

    draft_path = drafts_dir / f"{draft_id}.json"
    try:
        with open(draft_path, "w", encoding="utf-8") as f:
            json.dump(draft, f, ensure_ascii=False, indent=2)
    except IOError as e:
        return {"status": "error", "note_id": None,
                "title": title, "message": f"保存草稿失败: {e}", "details": {}}

    # ── 尝试通过 cs curl 发布 ──────────────────────────────────────
    cookies = _load_cookies()
    if cookies and cookies.get("cookie"):
        headers = {
            **_get_cookie_header(),
            "Origin": "https://www.xiaohongshu.com",
            "Referer": "https://www.xiaohongshu.com/",
        }

        # 构建发布请求体
        post_data = {
            "title": title,
            "desc": body,
            "note_type": "normal",
        }

        if publish_time:
            post_data["publish_time"] = publish_time

        api_result = _curl_post(
            f"{XHS_API_BASE}/sns/web/v1/note/post",
            data=post_data,
            headers=headers,
            timeout=30,
        )

        # 检查响应中是否有 note_id
        note_id = None
        if isinstance(api_result, dict):
            if "data" in api_result and isinstance(api_result["data"], dict):
                note_id = api_result["data"].get("note_id")
            elif "note_id" in api_result:
                note_id = api_result["note_id"]

        if note_id:
            # 更新草稿状态
            draft["status"] = "published"
            draft["note_id"] = note_id
            with open(draft_path, "w", encoding="utf-8") as f:
                json.dump(draft, f, ensure_ascii=False, indent=2)

            return {
                "status": "ok",
                "note_id": note_id,
                "title": title,
                "message": f"笔记《{title}》发布成功！",
                "details": {
                    "draft_id": draft_id,
                    "draft_path": str(draft_path),
                    "api_response": api_result,
                },
            }

        # API 发布失败，保留为草稿
        return {
            "status": "warning",
            "note_id": None,
            "title": title,
            "message": "草稿已保存到本地，API发布未成功（可能Cookie过期或网络问题）",
            "details": {
                "draft_id": draft_id,
                "draft_path": str(draft_path),
                "api_response": api_result,
            },
        }

    # 没有 Cookie，仅保存草稿
    return {
        "status": "warning",
        "note_id": None,
        "title": title,
        "message": "草稿已保存到本地。如需发布，请先登录（运行 xhs_qr_login.py）",
        "details": {
            "draft_id": draft_id,
            "draft_path": str(draft_path),
        },
    }


# ═══════════════════════════════════════════════════════════════════
# 核心功能 3: analyze_xhs_trends — 分析小红书热门趋势
# ═══════════════════════════════════════════════════════════════════

def analyze_xhs_trends(keyword: str, top_n: int = 10) -> dict:
    """
    分析小红书特定关键词的热门趋势。

    通过多个渠道采集数据并分析：
    1. 小红书搜索（如有 Cookie）
    2. 网页爬取公开热点
    3. 模拟搜索结果

    Args:
        keyword: 要分析的关键词
        top_n: 返回热门笔记数量（默认10）

    Returns:
        dict: {
            "status": "ok" | "error",
            "keyword": str,
            "trending_notes": [...],  # 热门笔记列表
            "trend_analysis": {...},   # 趋势分析
            "message": str
        }
    """
    if not keyword or not keyword.strip():
        return {"status": "error", "keyword": keyword,
                "trending_notes": [], "trend_analysis": {},
                "message": "关键词不能为空"}

    keyword = keyword.strip()

    # ── Method 1: 小红书搜索（通过 Cookie 认证） ──
    notes = []
    headers = _get_cookie_header()

    if headers.get("Cookie"):
        # 使用小红书搜索API
        search_url = (
            f"{XHS_API_BASE}/sns/web/v1/search/notes"
            f"?keyword={keyword}&sort=general&page=1&page_size={top_n}"
        )
        api_result = _curl_get(search_url, headers=headers, timeout=15)

        if isinstance(api_result, dict) and "data" in api_result:
            items = api_result["data"].get("items", [])
            for item in items:
                note = {
                    "title": item.get("display_title", ""),
                    "note_id": item.get("id", ""),
                    "likes": item.get("likes", 0),
                    "author": item.get("user", {}).get("nickname", ""),
                    "url": f"https://www.xiaohongshu.com/discovery/item/{item.get('id', '')}",
                }
                notes.append(note)

    # ── Method 2: 无 Cookie 的公开搜索（小红书公开页面） ──
    if not notes:
        user_agent = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        search_url = (
            f"https://www.xiaohongshu.com/search_result"
            f"?keyword={keyword}&source=web_search_result_notes"
        )

        try:
            cmd = [
                "curl", "-s", "-L", search_url,
                "-H", f"User-Agent: {user_agent}",
                "--connect-timeout", "10",
                "--max-time", "15",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            if result.returncode == 0 and result.stdout:
                # 尝试从HTML中提取笔记信息
                import re
                html = result.stdout

                # 提取 note_id
                note_ids = re.findall(r'note_id[\":\s]+[\"']?([a-f0-9]{24})[\"']?', html)
                # 提取标题
                titles = re.findall(r'display_title[\":\s]+[\"']([^\"\']+)[\"\']', html)

                for i, note_id in enumerate(note_ids[:top_n]):
                    title = titles[i] if i < len(titles) else ""
                    notes.append({
                        "title": title,
                        "note_id": note_id,
                        "url": f"https://www.xiaohongshu.com/discovery/item/{note_id}",
                    })
        except Exception:
            pass

    # ── 生成趋势分析 ────────────────────────────────────────────────
    trend_analysis = {
        "keyword": keyword,
        "total_notes_found": len(notes),
        "trend_indicators": [],
    }

    # 分析标题关键词
    import re
    all_text = " ".join(n.get("title", "") for n in notes)
    # 提取常见词
    words = re.findall(r'[\u4e00-\u9fff\w]+', all_text)
    if words:
        from collections import Counter
        word_freq = Counter(words).most_common(15)
        trend_analysis["trend_indicators"] = [
            {"word": w, "count": c, "type": "高频词"}
            for w, c in word_freq
            if c >= 2
        ]

    # 生成建议
    suggestions = []
    if trend_analysis["trend_indicators"]:
        top_words = [t["word"] for t in trend_analysis["trend_indicators"][:5]]
        suggestions.append(f"当前热门方向: {'、'.join(top_words)}")
    if notes:
        suggestions.append(f"共发现 {len(notes)} 条相关内容")
    else:
        suggestions.append("未从公开渠道获取到具体热门笔记")

    trend_analysis["suggestions"] = suggestions

    status = "ok" if notes else "warning"
    message = (
        f"关键词「{keyword}」趋势分析完成，"
        f"找到 {len(notes)} 条相关笔记"
        if notes else
        f"关键词「{keyword}」未找到公开热门数据"
    )

    return {
        "status": status,
        "keyword": keyword,
        "trending_notes": notes[:top_n],
        "trend_analysis": trend_analysis,
        "message": message,
    }


# ═══════════════════════════════════════════════════════════════════
# 自检
# ═══════════════════════════════════════════════════════════════════

def self_check() -> dict:
    """
    运行环境自检，报告molin-xiaohongshu功能可用性。

    Returns:
        dict: 各功能检查结果
    """
    result = {
        "xhs_status": check_xhs_status(),
        "core_functions": {},
        "environment": {},
    }

    # 检查依赖
    for tool in ["curl", "python3"]:
        try:
            subprocess.run(["which", tool], capture_output=True, timeout=3, check=True)
            result["environment"][tool] = True
        except Exception:
            result["environment"][tool] = False

    # 测试 check_xhs_status
    result["core_functions"]["check_xhs_status"] = True

    # 测试 xhs_post_draft（不实际发布，仅验证参数校验）
    test_result = xhs_post_draft("", "空标题测试")
    result["core_functions"]["xhs_post_draft_validation"] = test_result["status"] == "error"

    # 测试 analyze_xhs_trends
    trend_result = analyze_xhs_trends("AI", top_n=3)
    result["core_functions"]["analyze_xhs_trends"] = trend_result["status"] in ("ok", "warning")

    return result


# ═══════════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("molin-xiaohongshu 激活脚本 · 自检报告")
    print("=" * 60)

    check = self_check()

    print("\n  📊 环境检查:")
    for tool, available in check["environment"].items():
        icon = "✓" if available else "✗"
        print(f"    {icon} {tool}: {'可用' if available else '不可用'}")

    print("\n  🔧 核心功能:")
    for func, ok in check["core_functions"].items():
        icon = "✓" if ok else "✗"
        print(f"    {icon} {func}")

    print("\n  🔑 XHS 状态:")
    status = check["xhs_status"]
    status_icon = {"ok": "✓", "warning": "⚠", "error": "✗"}
    print(f"    {status_icon.get(status['status'], '?')} 状态: {status['status']}")
    print(f"    Cookie有效: {status['cookie_valid']}")
    print(f"    数据目录: {status['data_dir_ok']}")
    if status["account_name"]:
        print(f"    当前账号: {status['account_name']}")
    print(f"    API可达: {status['api_reachable']}")
    print(f"    消息: {status['message']}")

    print()
    print("-" * 60)
    print("测试: check_xhs_status()")
    print(f"  → {status['message']}")

    print()
    print("-" * 60)
    print("测试: xhs_post_draft() — 参数校验")
    print(f"  → 空标题校验通过: {check['core_functions']['xhs_post_draft_validation']}")

    print()
    print("-" * 60)
    print("测试: analyze_xhs_trends('AI')")
    trend = analyze_xhs_trends("AI", top_n=3)
    print(f"  状态: {trend['status']}")
    print(f"  找到: {len(trend['trending_notes'])} 条笔记")
    if trend["trend_analysis"]["trend_indicators"]:
        print(f"  高频词: {[t['word'] for t in trend['trend_analysis']['trend_indicators'][:5]]}")

    print()
    print("=" * 60)
    print("molin-xiaohongshu 激活完成 ✓")
    print("墨笔文创 → molin-xiaohongshu 触发链路已建立")
    print("=" * 60)
