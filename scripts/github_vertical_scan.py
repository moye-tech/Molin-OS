#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
墨麟OS — GitHub 垂直学习扫描脚本
scripts/github_vertical_scan.py

用途：
  被 Cron learn_a1_github_vertical_scan 调用，
  按 config/learning/agent_learning_subscriptions.yaml 中各Agent的关键词表，
  扫描过去7天 stars≥50 的新项目，输出到 relay/learning/{agent_id}_scan_{date}.json。

调用方式：
  python3 scripts/github_vertical_scan.py
  python3 scripts/github_vertical_scan.py --agent mobi_edu  # 单个Agent
  python3 scripts/github_vertical_scan.py --dry-run         # 不写文件，仅打印

环境变量：
  GITHUB_TOKEN    — 必须，否则API限速60次/小时（有Token则5000次/小时）
  MOLIN_ROOT      — 项目根目录，默认 ~/Molin-OS
  OBSIDIAN_VAULT  — Obsidian Vault路径，用于检查已读项目
"""

import os
import sys
import json
import time
import logging
import argparse
import datetime
import hashlib
from pathlib import Path
from typing import Optional
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote_plus

# ──────────────────────────────────────────────
# 配置
# ──────────────────────────────────────────────
MOLIN_ROOT = Path(os.environ.get("MOLIN_ROOT", Path.home() / "Molin-OS"))
OBSIDIAN_VAULT = Path(os.environ.get("OBSIDIAN_VAULT", Path("/Users/laomo/Library/Mobile Documents/iCloud~md~obsidian/Documents")))
RELAY_DIR = MOLIN_ROOT / "relay" / "learning"
CONFIG_PATH = MOLIN_ROOT / "config" / "learning" / "agent_learning_subscriptions.yaml"
GITHUB_TOKEN=os.env...EN", "")
GITHUB_API = "https://api.github.com/search/repositories"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("github_vertical_scan")


# ──────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────
def load_yaml_simple(path: Path) -> dict:
    """
    极简YAML解析（只处理本配置文件的简单结构）。
    生产环境请用 pip install pyyaml 后 import yaml。
    """
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except ImportError:
        log.warning("pyyaml 未安装，使用简化解析。建议: pip install pyyaml")
        # 降级：直接返回空配置，调用方需处理
        return {}


def github_search(query: str, min_stars: int, lookback_days: int,
                  languages: list[str], max_results: int = 8) -> list[dict]:
    """
    调用 GitHub Search API，返回项目列表。
    自动处理限速（403/429时等待后重试）。
    """
    since_date = (datetime.datetime.utcnow() -
                  datetime.timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    lang_filter = ""
    if languages:
        # 取前2个语言以避免查询过长
        lang_filter = " ".join(f"language:{l}" for l in languages[:2])

    q = f"{query} stars:>={min_stars} created:>{since_date} {lang_filter}".strip()

    params = urlencode({
        "q": q,
        "sort": "stars",
        "order": "desc",
        "per_page": max_results,
    })
    url = f"{GITHUB_API}?{params}"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "MolinOS-LearningScanner/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    else:
        log.warning("GITHUB_TOKEN 未设置，API限速60次/小时，建议配置Token")

    for attempt in range(3):
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                items = data.get("items", [])
                return [
                    {
                        "name": item["name"],
                        "full_name": item["full_name"],
                        "url": item["html_url"],
                        "stars": item["stargazers_count"],
                        "description": item.get("description", ""),
                        "topics": item.get("topics", []),
                        "language": item.get("language", ""),
                        "created_at": item.get("created_at", ""),
                        "updated_at": item.get("updated_at", ""),
                        "homepage": item.get("homepage", ""),
                    }
                    for item in items
                ]
        except HTTPError as e:
            if e.code in (403, 429):
                wait = 60 * (attempt + 1)
                log.warning(f"GitHub API 限速 ({e.code})，等待 {wait}s 后重试...")
                time.sleep(wait)
            else:
                log.error(f"GitHub API HTTP错误 {e.code}: {url}")
                return []
        except (URLError, Exception) as e:
            log.error(f"GitHub API 请求失败 (attempt {attempt+1}): {e}")
            if attempt < 2:
                time.sleep(10)
    return []


def get_already_read_repos(agent_id: str) -> set[str]:
    """
    检查 Obsidian Vault 中该Agent已有精读记录的项目（通过文件名推断）。
    避免重复精读已学习的项目。
    """
    # v3.0 flat vault: 学习档案/ 下同名文件
    read_path = OBSIDIAN_VAULT / "学习档案"
    if not read_path.exists():
        return set()

    read_repos = set()
    for md_file in read_path.glob("*.md"):
        # 文件名格式：{repo_name}_{YYYYMMDD}.md
        # 提取 repo_name 部分
        stem = md_file.stem
        # 去掉末尾的日期部分（_YYYYMMDD）
        parts = stem.rsplit("_", 1)
        if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) == 8:
            read_repos.add(parts[0].lower().replace("-", "").replace("_", ""))
    return read_repos


def deduplicate_projects(projects: list[dict], already_read: set[str]) -> list[dict]:
    """
    去重：移除已精读项目，移除内容重复的项目（按URL去重）。
    """
    seen_urls = set()
    result = []
    for p in projects:
        # 归一化repo名用于与已读集合比较
        normalized_name = p["name"].lower().replace("-", "").replace("_", "")
        url = p["url"]
        if url in seen_urls:
            continue
        if normalized_name in already_read:
            log.debug(f"跳过已读项目: {p['full_name']}")
            continue
        seen_urls.add(url)
        result.append(p)
    return result


def apply_global_excludes(projects: list[dict], excludes: dict) -> list[dict]:
    """
    应用全局排除规则（awesome-list、tutorial等低价值项目）。
    """
    exclude_topics = set(excludes.get("topics", []))
    exclude_langs = set(excludes.get("languages_exclude", []))
    result = []
    for p in projects:
        # 排除特定topic
        project_topics = set(p.get("topics", []))
        if project_topics & exclude_topics:
            log.debug(f"排除（topic命中）: {p['full_name']}")
            continue
        # 排除特定语言
        if p.get("language", "") in exclude_langs:
            log.debug(f"排除（语言不兼容）: {p['full_name']}")
            continue
        # 排除awesome-* 系列
        if p["name"].lower().startswith("awesome-"):
            log.debug(f"排除（awesome列表）: {p['full_name']}")
            continue
        result.append(p)
    return result


def scan_agent(agent_id: str, agent_cfg: dict,
               global_cfg: dict, dry_run: bool = False) -> dict:
    """
    扫描单个Agent的GitHub学习订阅，返回结构化结果。
    """
    log.info(f"\n{'='*50}")
    log.info(f"🔍 开始扫描: {agent_cfg.get('display_name', agent_id)}")

    global_settings = global_cfg.get("global_settings", {})
    global_excludes = global_cfg.get("global_excludes", {})

    min_stars = agent_cfg.get("min_stars", global_settings.get("min_stars", 50))
    max_projects = global_settings.get("max_projects_per_agent", 8)
    lookback_days = global_settings.get("lookback_days", 7)
    preferred_languages = agent_cfg.get("preferred_languages", [])

    # 合并全局+Agent级排除topic
    agent_exclude_topics = set(agent_cfg.get("exclude_topics", []))
    agent_exclude_topics.update(global_excludes.get("topics", []))

    # 获取已精读项目（避免重复）
    already_read = get_already_read_repos(agent_id)
    log.info(f"  已精读项目数（跳过）: {len(already_read)}")

    # 构建搜索关键词列表
    github_topics = agent_cfg.get("github_topics", {})
    github_keywords = agent_cfg.get("github_keywords", [])

    queries = []
    # 核心topic查询
    for topic in github_topics.get("core", []):
        queries.append(f"topic:{topic}")
    # 延伸topic查询
    for topic in github_topics.get("extended", []):
        queries.append(f"topic:{topic}")
    # 关键词查询
    queries.extend(github_keywords)

    # 去重并限制查询数量（避免API耗尽）
    queries = list(dict.fromkeys(queries))[:10]

    all_projects = []
    for query in queries:
        log.info(f"  搜索: {query}")
        projects = github_search(
            query=query,
            min_stars=min_stars,
            lookback_days=lookback_days,
            languages=preferred_languages,
            max_results=5,
        )
        all_projects.extend(projects)
        # 礼貌性延迟，避免触发限速
        time.sleep(1.5)

    # 应用排除规则 + 去重
    all_projects = apply_global_excludes(all_projects, global_excludes)
    all_projects = deduplicate_projects(all_projects, already_read)

    # 按stars降序排序，取Top N
    all_projects.sort(key=lambda x: x["stars"], reverse=True)
    all_projects = all_projects[:max_projects]

    log.info(f"  ✅ 找到候选项目: {len(all_projects)} 个")
    for p in all_projects:
        log.info(f"     ⭐{p['stars']:,} — {p['full_name']}: {p['description'][:60]}")

    # 构建输出结构
    today = datetime.datetime.now().strftime("%Y%m%d")
    result = {
        "schema_version": "1.0",
        "agent_id": agent_id,
        "display_name": agent_cfg.get("display_name", agent_id),
        "scan_date": today,
        "scan_timestamp": datetime.datetime.now().isoformat(),
        "queries_executed": queries,
        "projects_found": len(all_projects),
        "already_read_skipped": len(already_read),
        "projects": all_projects,
        "intel_feeds": agent_cfg.get("intel_feeds", []),
        "learning_focus": agent_cfg.get("learning_focus_this_quarter", []),
    }

    # 写入relay文件
    if not dry_run:
        RELAY_DIR.mkdir(parents=True, exist_ok=True)
        output_path = RELAY_DIR / f"{agent_id}_scan_{today}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        log.info(f"  💾 已写入: {output_path}")
    else:
        log.info("  [DRY-RUN] 不写入文件")

    return result


def update_scan_manifest(scan_results: dict[str, dict], dry_run: bool = False):
    """
    更新 relay/learning/latest_scan_manifest.json，
    供下游 Cron learn_a2 读取，知道本次扫描完成了哪些Agent。
    """
    today = datetime.datetime.now().strftime("%Y%m%d")
    manifest = {
        "scan_date": today,
        "scan_timestamp": datetime.datetime.now().isoformat(),
        "agents_scanned": list(scan_results.keys()),
        "total_projects_found": sum(
            r["projects_found"] for r in scan_results.values()
        ),
        "files": {
            agent_id: str(RELAY_DIR / f"{agent_id}_scan_{today}.json")
            for agent_id in scan_results
        },
        "status": "completed",
    }

    if not dry_run:
        manifest_path = RELAY_DIR / "latest_scan_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        log.info(f"\n📋 Manifest更新: {manifest_path}")

    return manifest


def build_feishu_summary(manifest: dict, scan_results: dict) -> str:
    """
    构建推送飞书的通知文本摘要。
    """
    lines = ["📡 本周垂直学习扫描完成\n"]
    for agent_id, result in scan_results.items():
        name = result.get("display_name", agent_id)
        count = result.get("projects_found", 0)
        top3 = result.get("projects", [])[:3]
        lines.append(f"**{name}**：找到 {count} 个候选项目")
        for p in top3:
            lines.append(f"  · [{p['full_name']}]({p['url']}) ⭐{p['stars']:,}")

    total = manifest.get("total_projects_found", 0)
    lines.append(f"\n总计：{total} 个待精读项目")
    lines.append("→ AutoDream将于07:00开始精读内化")
    return "\n".join(lines)


# ──────────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="墨麟OS GitHub垂直学习扫描脚本"
    )
    parser.add_argument(
        "--agent", type=str, default=None,
        help="只扫描指定Agent（如：mobi_edu），不填则扫描全部"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="不写入文件，仅打印结果"
    )
    parser.add_argument(
        "--config", type=str, default=str(CONFIG_PATH),
        help="学习订阅配置文件路径"
    )
    args = parser.parse_args()

    # 加载配置
    config_path = Path(args.config)
    if not config_path.exists():
        log.error(f"配置文件不存在: {config_path}")
        log.error("请确认 config/learning/agent_learning_subscriptions.yaml 已就位")
        sys.exit(1)

    log.info(f"📂 加载配置: {config_path}")
    config = load_yaml_simple(config_path)

    if not config:
        log.error("配置文件加载失败或为空，退出")
        sys.exit(1)

    agents_config = config.get("agents", {})
    if not agents_config:
        log.error("配置中没有 agents 定义，退出")
        sys.exit(1)

    # 筛选要扫描的Agent
    if args.agent:
        if args.agent not in agents_config:
            log.error(f"Agent '{args.agent}' 不在配置中")
            log.error(f"可用Agent: {list(agents_config.keys())}")
            sys.exit(1)
        agents_to_scan = {args.agent: agents_config[args.agent]}
    else:
        agents_to_scan = agents_config

    log.info(f"🚀 开始扫描，共 {len(agents_to_scan)} 个Agent")
    log.info(f"   Token状态: {'✅ 已配置' if GITHUB_TOKEN else '⚠️ 未配置（限速60次/小时）'}")
    log.info(f"   Dry-run: {args.dry_run}")

    # 执行扫描
    scan_results = {}
    failed_agents = []

    for agent_id, agent_cfg in agents_to_scan.items():
        try:
            result = scan_agent(
                agent_id=agent_id,
                agent_cfg=agent_cfg,
                global_cfg=config,
                dry_run=args.dry_run,
            )
            scan_results[agent_id] = result
        except Exception as e:
            log.error(f"❌ Agent {agent_id} 扫描失败: {e}")
            failed_agents.append(agent_id)
            # 单Agent失败不阻断其他Agent
            continue

    # 更新Manifest
    manifest = update_scan_manifest(scan_results, dry_run=args.dry_run)

    # 输出汇总
    total = manifest["total_projects_found"]
    log.info(f"\n{'='*50}")
    log.info(f"✅ 扫描完成")
    log.info(f"   成功: {len(scan_results)} 个Agent")
    log.info(f"   失败: {len(failed_agents)} 个Agent {failed_agents if failed_agents else ''}")
    log.info(f"   总计候选项目: {total} 个")

    # 打印飞书通知文本（供Cron发送）
    if scan_results:
        summary = build_feishu_summary(manifest, scan_results)
        print("\n── 飞书通知内容 ──")
        print(summary)

    # 如果有失败，以非零码退出（Cron可以检测到）
    if failed_agents:
        log.warning(f"部分Agent扫描失败，但已完成其余Agent：{failed_agents}")
        sys.exit(2)   # 退出码2：部分成功

    sys.exit(0)


if __name__ == "__main__":
    main()