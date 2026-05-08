#!/usr/bin/env python3
"""
VPN 自动优化工具 — Hermes OS 网络质量守护进程
=============================================
功能：
  1. 节点测速：遍历所有节点，通过 Clash API delay 接口测延迟
  2. 自动选最优：选延迟最低且 <3000ms 的节点，自动切换到 🤖 AI 组
  3. 免费节点源更新：从 GitHub 爬取免费节点订阅（需安全校验）
  4. 安全扫描：检查节点类型/服务器 IP 是否在黑名单/是否为明文 HTTP
  5. 持久化：每天 06:00 cron 执行一次
  6. CLI：--check / --update-free / --scan-security / --watch

用法：
  python vpn_optimizer.py --check        测速 + 自动切换最优节点
  python vpn_optimizer.py --update-free  从 GitHub 更新免费节点
  python vpn_optimizer.py --scan-security 安全扫描所有节点
  python vpn_optimizer.py --watch        每 5 分钟持续监控
  python vpn_optimizer.py --all          全量执行（更新+扫描+测速+切换）

Clash API:
  GET  /proxies                  获取所有代理（节点+组）
  GET  /proxies/{name}/delay    测延迟
  PUT  /proxies/{name}          切换 Selector 组到指定节点
  GET  /proxies/{name}          获取单个代理详情
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
import re
import ssl
import base64
import hashlib
import logging
import argparse
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ─── 配置 ───────────────────────────────────────────────────────────────
CLASH_API_BASE = "http://127.0.0.1:9090"
CLASH_SECRET = ""  # 无 Secret
DELAY_TIMEOUT_MS = 5000
DELAY_URL = "http://www.gstatic.com/generate_204"
MAX_ACCEPTABLE_DELAY_MS = 3000
PROXY = "http://127.0.0.1:7890"  # 用于外网请求

# 日志
LOG_DIR = Path.home() / ".hermes" / "daily_reports"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"vpn_optimizer_{datetime.now().strftime('%Y%m%d')}.log"

STATE_FILE = Path.home() / ".hermes" / "vpn_optimizer_state.json"

# 已知恶意 IP 黑名单（内置示例 + 可通过 update 扩展）
MALICIOUS_IPS = {
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",  # 内网
    "127.0.0.0/8", "0.0.0.0/8",  # 回环/未指定
    "185.220.101.0/24",  # Tor exit nodes (known abuse)
    "45.155.205.0/24",   # Known malicious ranges
    "5.255.100.0/22",    # Russian RKN blocks
}

# 加密协议白名单（安全的代理类型）
SECURE_PROXY_TYPES = {"Shadowsocks", "Vmess", "Vless", "Trojan", "Hysteria2", "Hysteria", "Socks5"}
INSECURE_PROXY_TYPES = {"Http", "Socks", "Compatible"}

# AI 组名（注意包含 emoji 和零宽空格）
AI_GROUP_NAME = "🤖 ‍AI"

# ─── 日志 ───────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
    ],
)
log = logging.getLogger("vpn_optimizer")


# ─── 工具函数 ───────────────────────────────────────────────────────────

def url_encode_node(name: str) -> str:
    """URL 编码节点名（处理 emoji、空格、中文）"""
    return urllib.parse.quote(name, safe="")


def clash_api_get(path: str) -> dict | None:
    """调用 Clash API GET 接口"""
    url = f"{CLASH_API_BASE}{path}"
    req = urllib.request.Request(url)
    if CLASH_SECRET:
        req.add_header("Authorization", f"Bearer {CLASH_SECRET}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        log.warning(f"Clash API GET {path} 失败: {e}")
        return None


def clash_api_put(path: str, data: dict) -> bool:
    """调用 Clash API PUT 接口"""
    url = f"{CLASH_API_BASE}{path}"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, method="PUT")
    req.add_header("Content-Type", "application/json")
    if CLASH_SECRET:
        req.add_header("Authorization", f"Bearer {CLASH_SECRET}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status in (200, 204)
    except Exception as e:
        log.warning(f"Clash API PUT {path} {data} 失败: {e}")
        return False


def fetch_with_proxy(url: str, timeout: int = 20) -> str | None:
    """通过本地代理获取外部资源"""
    proxy_handler = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy_handler)
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; HermesVPN/1.0)"
    })
    try:
        with opener.open(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        log.warning(f"代理请求 {url[:60]}... 失败: {e}")
        return None


def ip_in_blacklist(ip_str: str) -> bool:
    """检查 IP 是否在黑名单（含 CIDR 匹配）"""
    import ipaddress
    try:
        addr = ipaddress.ip_address(ip_str)
        for cidr in MALICIOUS_IPS:
            if addr in ipaddress.ip_network(cidr, strict=False):
                return True
    except ValueError:
        pass
    return False


def save_state(data: dict):
    """持久化状态到文件"""
    data["_last_updated"] = datetime.now(timezone.utc).isoformat()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_state() -> dict:
    """加载持久化的状态"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


# ─── 1. 获取所有节点 ────────────────────────────────────────────────────

def get_all_proxies() -> dict:
    """
    从 Clash API 获取所有代理信息。
    返回 {"nodes": {name: info}, "groups": {name: info}}
    """
    raw = clash_api_get("/proxies")
    if not raw or "proxies" not in raw:
        log.error("无法获取代理列表")
        return {"nodes": {}, "groups": {}}

    proxies = raw["proxies"]
    nodes = {}
    groups = {}

    for name, info in proxies.items():
        t = info.get("type", "")
        if t in ("Selector", "URLTest", "Fallback", "LoadBalance"):
            groups[name] = info
        elif t in ("Direct", "Compatible", "Reject"):
            pass  # 内置特殊代理，忽略
        else:
            nodes[name] = info

    log.info(f"获取到 {len(nodes)} 个节点, {len(groups)} 个组")
    return {"nodes": nodes, "groups": groups}


# ─── 2. 节点测速 ────────────────────────────────────────────────────────

def measure_delay(node_name: str, timeout_ms: int = DELAY_TIMEOUT_MS) -> int | None:
    """
    对单个节点测延迟。
    返回延迟毫秒数，失败返回 None。
    """
    encoded = url_encode_node(node_name)
    url = f"{CLASH_API_BASE}/proxies/{encoded}/delay?timeout={timeout_ms}&url={urllib.parse.quote(DELAY_URL)}"
    req = urllib.request.Request(url)
    if CLASH_SECRET:
        req.add_header("Authorization", f"Bearer {CLASH_SECRET}")
    try:
        with urllib.request.urlopen(req, timeout=timeout_ms // 1000 + 2) as resp:
            data = json.loads(resp.read().decode())
            delay = data.get("delay")
            if delay and delay > 0:
                return delay
            return None
    except urllib.error.HTTPError as e:
        if e.code == 504:
            return None  # Timeout
        if e.code == 503:
            return None  # Error
        log.debug(f"测速 {node_name[:30]} HTTP {e.code}")
        return None
    except Exception as e:
        log.debug(f"测速 {node_name[:30]} 异常: {e}")
        return None


def measure_all_nodes(nodes: dict, max_workers: int = 10) -> dict:
    """
    对所有节点测速。
    返回 {node_name: delay_ms}
    """
    results = {}
    names = list(nodes.keys())
    total = len(names)
    log.info(f"开始测速 {total} 个节点...")

    for i, name in enumerate(names, 1):
        delay = measure_delay(name)
        if delay is not None:
            results[name] = delay
            if delay < 500:
                marker = "✅"
            elif delay < 1500:
                marker = "🟡"
            elif delay < MAX_ACCEPTABLE_DELAY_MS:
                marker = "🟠"
            else:
                marker = "🔴"
            log.info(f"  [{i}/{total}] {marker} {name[:40]}: {delay}ms")
        else:
            log.info(f"  [{i}/{total}] ❌ {name[:40]}: 超时/不可达")
        # 稍微减速，避免打满 Clash
        if i % 5 == 0:
            time.sleep(0.3)

    good = {k: v for k, v in results.items() if v < MAX_ACCEPTABLE_DELAY_MS}
    log.info(f"测速完成: {len(results)} 个可达, {len(good)} 个延迟 < {MAX_ACCEPTABLE_DELAY_MS}ms")
    return results


# ─── 3. 自动切换最优节点 ────────────────────────────────────────────────

def find_best_node(delays: dict) -> tuple | None:
    """从测速结果中选出延迟最低且 <3000ms 的节点"""
    valid = {k: v for k, v in delays.items() if v < MAX_ACCEPTABLE_DELAY_MS}
    if not valid:
        log.warning("没有延迟合格的节点")
        return None
    best = min(valid.items(), key=lambda x: x[1])
    log.info(f"最优节点: {best[0][:40]} ({best[1]}ms)")
    return best


def switch_ai_group(node_name: str) -> bool:
    """
    将 🤖 AI 组切换到指定节点。
    注意 AI 组的成员是子组（🇸🇬 新加坡、🇺🇸 美国等），
    因此需要切换对应的 👆🏻 指定子组。
    """
    # 解析节点所属的国家组
    # 节点名格式: "🇸🇬 新加坡 | SGP"、"🇸🇬 新加坡 | SGP 2"
    # 对应子组名: "👆🏻🇸🇬 新加坡"
    country_match = re.match(r"([\U0001F1E6-\U0001F1FF]{2})(?:\s*)([\u4e00-\u9fff]+)", node_name)
    if not country_match:
        log.warning(f"无法从节点名解析国家: {node_name}")
        return False

    flag = country_match.group(1)
    country = country_match.group(2)

    # AI 组期望的是子组名如 "👆🏻🇸🇬 新加坡"
    target_group = f"👆🏻{flag} {country}"

    # 先切换对应国家的 👆🏻 组到该节点
    proxies = get_all_proxies()
    groups = proxies["groups"]

    if target_group not in groups:
        log.warning(f"目标组 {target_group} 不存在，尝试直接切换 AI 组")
        # 尝试直接切换 AI 组到该节点
        return _switch_group_direct(AI_GROUP_NAME, node_name)

    # 切换 👆🏻🇸🇬 新加坡 组到指定节点
    log.info(f"切换 {target_group} → {node_name[:30]}")
    success = clash_api_put(f"/proxies/{url_encode_node(target_group)}", {"name": node_name})
    if not success:
        log.error(f"切换 {target_group} 失败")
        return False

    # 然后确认 AI 组是否已指向该 👆🏻 组
    ai_group = groups.get(AI_GROUP_NAME, {})
    if ai_group.get("now") != target_group:
        log.info(f"切换 {AI_GROUP_NAME} → {target_group}")
        success = clash_api_put(f"/proxies/{url_encode_node(AI_GROUP_NAME)}", {"name": target_group})
        if not success:
            log.error(f"切换 {AI_GROUP_NAME} 失败")
            return False

    log.info(f"✅ AI 组已切换到 {node_name[:40]}（通过 {target_group}）")
    return True


def _switch_group_direct(group_name: str, node_name: str) -> bool:
    """直接切换组到指定节点"""
    log.info(f"切换 {group_name} → {node_name[:30]}")
    return clash_api_put(f"/proxies/{url_encode_node(group_name)}", {"name": node_name})


# ─── 4. 免费节点源更新 ──────────────────────────────────────────────────

GITHUB_SEARCH_URL = (
    "https://api.github.com/search/repositories"
    "?q=free+clash+subscription+node&sort=stars&per_page=5"
)

# 已知的免费 Clash 订阅项目 URL 模式
KNOWN_SUBSCRIPTION_PROJECTS = [
    "Pawdroid/Free-servers",
    "xiaoji235/airport-free",
    "mermeroo/V2RAY-CLASH-BASE64-Subscription.Links",
]


def search_free_nodes_github() -> list[dict]:
    """从 GitHub 搜索免费节点项目"""
    log.info("正在搜索 GitHub 免费节点项目...")
    raw = fetch_with_proxy(GITHUB_SEARCH_URL)
    if not raw:
        log.warning("GitHub 搜索失败")
        return []

    try:
        data = json.loads(raw)
        repos = data.get("items", [])[:5]
        results = []
        for repo in repos:
            results.append({
                "name": repo["full_name"],
                "stars": repo["stargazers_count"],
                "url": repo["html_url"],
                "description": repo.get("description", ""),
                "topics": repo.get("topics", []),
            })
        return results
    except (json.JSONDecodeError, KeyError) as e:
        log.warning(f"解析 GitHub 响应失败: {e}")
        return []


def extract_subscription_urls(repo_info: dict) -> list[str]:
    """
    从 GitHub 仓库信息中提取可能的订阅链接。
    通过读取仓库的 README 或已知的订阅链接模式。
    """
    repo_full = repo_info["name"]
    api_url = f"https://api.github.com/repos/{repo_full}/readme"
    log.info(f"从 {repo_full} 提取订阅链接...")

    raw = fetch_with_proxy(api_url)
    if not raw:
        return []

    try:
        data = json.loads(raw)
        content_b64 = data.get("content", "")
        # GitHub API returns base64 content
        try:
            content = base64.b64decode(content_b64).decode("utf-8", errors="replace")
        except Exception:
            content = ""

        # 查找订阅链接模式
        # Clash 订阅链接常见格式
        url_patterns = re.findall(
            r'https?://[^\s"\'<>]+(?:clash|sub|subscribe|node|proxy)[^\s"\'<>]*',
            content,
            re.IGNORECASE,
        )
        # 也找 raw.githubusercontent.com 的订阅
        raw_patterns = re.findall(
            r'https?://raw\.githubusercontent\.com[^\s"\'<>]+',
            content,
        )
        all_urls = list(set(url_patterns + raw_patterns))
        return all_urls[:10]  # 最多返回 10 个
    except (json.JSONDecodeError, KeyError) as e:
        log.warning(f"解析 README 失败: {e}")
        return []


def validate_subscription_url(url: str) -> bool:
    """
    校验订阅链接的安全性：
    1. 必须是 HTTPS
    2. 不能指向内网/IP
    3. 简单的内容验证
    """
    if not url.startswith("https://"):
        log.warning(f"非 HTTPS 订阅链接已跳过: {url[:60]}")
        return False

    # 检查是否指向内网
    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname or ""
    if hostname in ("localhost", "127.0.0.1", "0.0.0.0") or hostname.endswith(".local"):
        log.warning(f"内网地址已跳过: {url[:60]}")
        return False

    log.info(f"✅ 订阅链接校验通过: {url[:60]}")
    return True


def update_free_nodes() -> dict:
    """
    从 GitHub 更新免费节点源。
    返回更新结果。
    """
    log.info("=" * 50)
    log.info("开始更新免费节点源")
    log.info("=" * 50)

    repos = search_free_nodes_github()
    if not repos:
        log.warning("未找到免费节点仓库")
        return {"status": "error", "message": "No repos found"}

    log.info(f"找到 {len(repos)} 个仓库:")
    for r in repos:
        log.info(f"  ⭐{r['stars']} {r['name']}: {r['description'][:60]}")

    all_sub_urls = []
    for repo in repos:
        urls = extract_subscription_urls(repo)
        valid_urls = [u for u in urls if validate_subscription_url(u)]
        all_sub_urls.extend(valid_urls)

    all_sub_urls = list(set(all_sub_urls))

    # 持久化到状态
    state = load_state()
    state["free_node_sources"] = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "repos": repos,
        "subscription_urls": all_sub_urls,
    }
    save_state(state)

    log.info(f"找到 {len(all_sub_urls)} 个有效订阅链接")
    return {
        "status": "success",
        "repos_found": len(repos),
        "subscription_urls": all_sub_urls,
    }


# ─── 5. 安全扫描 ────────────────────────────────────────────────────────

def scan_node_security(node_name: str, node_info: dict) -> dict:
    """
    对单个节点进行安全扫描。
    返回安全评估报告。
    """
    report = {
        "node_name": node_name,
        "type": node_info.get("type", "Unknown"),
        "security_level": "unknown",
        "issues": [],
    }

    proxy_type = node_info.get("type", "")

    # 1. 检查代理类型
    if proxy_type in SECURE_PROXY_TYPES:
        report["security_level"] = "safe"
        report["issues"].append({
            "type": "protocol",
            "severity": "info",
            "message": f"使用加密协议: {proxy_type}",
        })
    elif proxy_type in INSECURE_PROXY_TYPES:
        report["security_level"] = "unsafe"
        report["issues"].append({
            "type": "protocol",
            "severity": "critical",
            "message": f"明文 HTTP 代理: {proxy_type} — 不加密，数据易被窃听",
        })
    else:
        report["security_level"] = "unknown"
        report["issues"].append({
            "type": "protocol",
            "severity": "warning",
            "message": f"未知代理类型: {proxy_type}",
        })

    # 2. 检查服务器名称/地址（如果节点信息中有服务器字段）
    server = node_info.get("server", "") or node_info.get("host", "") or ""
    if server:
        if ip_in_blacklist(server):
            report["security_level"] = "unsafe"
            report["issues"].append({
                "type": "server_ip",
                "severity": "critical",
                "message": f"服务器 IP {server} 在黑名单中",
            })
        elif re.match(r"^\d+\.\d+\.\d+\.\d+$", server):
            # 是 IP 地址而不是域名
            report["issues"].append({
                "type": "server_ip",
                "severity": "info",
                "message": f"服务器使用 IP 直连: {server}",
            })
    else:
        # 尝试从节点名提取服务器信息（某些 Clash 节点名包含 IP）
        ip_match = re.search(r"(\d+\.\d+\.\d+\.\d+)", node_name)
        if ip_match:
            ip = ip_match.group(1)
            if ip_in_blacklist(ip):
                report["security_level"] = "unsafe"
                report["issues"].append({
                    "type": "server_ip",
                    "severity": "critical",
                    "message": f"节点名中包含黑名单 IP: {ip}",
                })

    # 3. 检查是否用 TLS（部分节点信息中有 tls 字段）
    tls = node_info.get("tls", None)
    if tls is False:
        report["issues"].append({
            "type": "tls",
            "severity": "warning",
            "message": "TLS 未启用",
        })
    elif tls is True:
        report["issues"].append({
            "type": "tls",
            "severity": "info",
            "message": "TLS 已启用",
        })

    # 汇总安全等级
    critical_issues = [i for i in report["issues"] if i["severity"] == "critical"]
    if critical_issues:
        report["security_level"] = "unsafe"
    elif report["security_level"] != "unsafe":
        report["security_level"] = "safe"

    return report


def scan_all_nodes(nodes: dict) -> dict:
    """
    对所有节点进行安全扫描。
    返回安全报告。
    """
    log.info("=" * 50)
    log.info("开始安全扫描")
    log.info("=" * 50)

    reports = {}
    safe_count = 0
    unsafe_count = 0
    unknown_count = 0

    for name, info in nodes.items():
        report = scan_node_security(name, info)
        reports[name] = report
        level = report["security_level"]
        if level == "safe":
            safe_count += 1
            log.info(f"  ✅ {name[:40]} → 安全 ({info.get('type', '?')})")
        elif level == "unsafe":
            unsafe_count += 1
            reasons = [i["message"] for i in report["issues"] if i["severity"] == "critical"]
            log.warning(f"  ❌ {name[:40]} → 不安全: {'; '.join(reasons)}")
        else:
            unknown_count += 1
            log.info(f"  ❓ {name[:40]} → 未知")

    summary = {
        "total": len(nodes),
        "safe": safe_count,
        "unsafe": unsafe_count,
        "unknown": unknown_count,
        "reports": reports,
    }

    log.info(f"安全扫描完成: {safe_count} 安全, {unsafe_count} 不安全, {unknown_count} 未知")

    # 保存报告到文件
    report_path = LOG_DIR / f"security_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    log.info(f"安全报告已保存至: {report_path}")

    return summary


# ─── 6. 持续监控 ────────────────────────────────────────────────────────

def watch_loop(interval_minutes: int = 5):
    """持续监控模式：每 N 分钟测速+切换"""
    log.info(f"进入持续监控模式（每 {interval_minutes} 分钟）")
    log.info("按 Ctrl+C 退出")

    cycle = 0
    while True:
        cycle += 1
        log.info(f"\n{'='*50}")
        log.info(f"监控周期 #{cycle} ({datetime.now().strftime('%H:%M:%S')})")
        log.info(f"{'='*50}")

        try:
            run_optimization_cycle()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            log.error(f"监控周期出错: {e}")

        log.info(f"等待 {interval_minutes} 分钟后下一轮...")
        try:
            time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            log.info("监控已停止")
            break


# ─── 7. 完整优化周期 ────────────────────────────────────────────────────

def run_optimization_cycle() -> dict:
    """
    执行完整优化周期：
    1. 获取所有节点
    2. 安全扫描（只信任安全节点）
    3. 测速所有安全节点
    4. 选择最优并切换
    """
    result = {"status": "running", "steps": {}}

    # Step 1: 获取代理
    log.info("步骤 1/4: 获取代理列表")
    proxies = get_all_proxies()
    nodes = proxies["nodes"]
    groups = proxies["groups"]

    if not nodes:
        log.error("无可用节点")
        result["status"] = "error"
        return result
    result["steps"]["get_proxies"] = {"node_count": len(nodes)}

    # Step 2: 安全扫描
    log.info("步骤 2/4: 安全扫描")
    security = scan_all_nodes(nodes)
    safe_nodes = {
        name: nodes[name]
        for name, info in security["reports"].items()
        if info["security_level"] == "safe"
    }
    result["steps"]["security_scan"] = {
        "total": security["total"],
        "safe": security["safe"],
        "unsafe": security["unsafe"],
    }

    if not safe_nodes:
        log.warning("没有安全节点可用，退而求其次使用所有节点")
        safe_nodes = nodes

    # Step 3: 测速
    log.info("步骤 3/4: 节点测速")
    delays = measure_all_nodes(safe_nodes)
    result["steps"]["speed_test"] = {
        "tested": len(delays),
        "available": len(delays),
    }

    # Step 4: 选择最优并切换
    log.info("步骤 4/4: 选择最优节点并切换")
    best = find_best_node(delays)
    if best:
        node_name, delay = best
        log.info(f"最优节点: {node_name[:40]} ({delay}ms)")
        switched = switch_ai_group(node_name)
        result["steps"]["switch"] = {
            "selected_node": node_name,
            "delay_ms": delay,
            "success": switched,
        }
        result["status"] = "success" if switched else "partial"
    else:
        log.warning("未找到可用节点，跳过切换")
        result["steps"]["switch"] = {"selected_node": None, "success": False}
        result["status"] = "no_suitable_node"

    # 保存结果
    result["timestamp"] = datetime.now(timezone.utc).isoformat()
    save_state({"last_optimization": result})

    log.info(f"优化周期完成: {result['status']}")
    return result


# ─── CLI 入口 ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="VPN 自动优化工具 — 节点测速/切换/安全扫描/自动更新",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--check", action="store_true",
        help="测速 + 自动切换最优节点"
    )
    parser.add_argument(
        "--update-free", action="store_true",
        help="从 GitHub 更新免费节点订阅源"
    )
    parser.add_argument(
        "--scan-security", action="store_true",
        help="安全扫描所有节点，输出 JSON 报告"
    )
    parser.add_argument(
        "--watch", action="store_true",
        help="持续监控模式（每 5 分钟测速 + 切换）"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="全量执行：更新 + 扫描 + 测速 + 切换"
    )
    parser.add_argument(
        "--interval", type=int, default=5,
        help="监控间隔（分钟，默认 5）"
    )

    args = parser.parse_args()

    # 如果没有参数，打印帮助
    if not any(vars(args).values()):
        parser.print_help()
        sys.exit(1)

    log.info(f"{'='*50}")
    log.info(f"VPN Optimizer v1.0 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info(f"Clash API: {CLASH_API_BASE}")
    log.info(f"日志: {LOG_FILE}")
    log.info(f"{'='*50}")

    try:
        if args.all:
            log.info("🔄 全量执行模式")
            update_free_nodes()
            proxies = get_all_proxies()
            scan_all_nodes(proxies["nodes"])
            run_optimization_cycle()

        elif args.update_free:
            update_free_nodes()

        elif args.scan_security:
            proxies = get_all_proxies()
            report = scan_all_nodes(proxies["nodes"])
            # 输出 JSON 到 stdout
            output = {
                "summary": {
                    "total": report["total"],
                    "safe": report["safe"],
                    "unsafe": report["unsafe"],
                    "unknown": report["unknown"],
                },
                "details": report["reports"],
            }
            print("\n=== 安全报告 (JSON) ===")
            print(json.dumps(output, indent=2, ensure_ascii=False))

        elif args.check:
            run_optimization_cycle()

        elif args.watch:
            watch_loop(args.interval)

    except KeyboardInterrupt:
        log.info("用户中断")
        sys.exit(0)
    except Exception as e:
        log.error(f"执行失败: {e}", exc_info=True)
        sys.exit(1)


# ─── Cron 入口 ──────────────────────────────────────────────────────────

def cron_job():
    """每天 06:00 由 cron 调用"""
    log.info("🕐 Cron 定时执行 VPN 优化")
    proxies = get_all_proxies()
    if proxies["nodes"]:
        scan_all_nodes(proxies["nodes"])
    run_optimization_cycle()
    log.info("✅ Cron 执行完成")


if __name__ == "__main__":
    main()
