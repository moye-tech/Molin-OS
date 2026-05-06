"""
墨麟AIOS — DataCollector (数据采集器)
参考 apify/crawlee-python (8.8K⭐) 爬虫架构设计模式：
1. 请求队列 + 自动重试 + 代理轮换
2. 可配置的 Router — 不同URL模式→不同handler
3. 数据持久化 + 自动去重
4. Autoscaling池 — 动态调节并发爬虫数

核心能力:
1. create_collector — 创建采集任务（配置目标站点、路由规则）
2. add_target     — 添加采集目标URL + handler类型
3. run            — 运行采集（模拟多并发、重试、去重）
4. get_data       — 获取采集结果（支持过滤）
5. stats          — 采集统计
"""

import os
import json
import time
import uuid
import hashlib
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# ── 模拟代理池（Crawlee 代理轮换模式） ──────────────────────────

_PROXY_POOL = [
    "proxy-ams-001.example.com:8080",
    "proxy-ams-002.example.com:8080",
    "proxy-sgp-001.example.com:3128",
    "proxy-sgp-002.example.com:3128",
    "proxy-fra-001.example.com:8080",
]

# 模拟站点配置（对应 Crawlee Router 的路由模式）
_SITE_HANDLERS: dict[str, dict[str, Any]] = {
    "xiaoHongShu": {
        "label": "小红书",
        "base_url": "https://www.xiaohongshu.com",
        "handler": "content_feed",
        "rate_limit": 1.5,       # 秒/请求
        "retry_max": 3,
        "page_depth": 2,
    },
    "weChat": {
        "label": "微信公众号",
        "base_url": "https://mp.weixin.qq.com",
        "handler": "article_mp",
        "rate_limit": 2.0,
        "retry_max": 2,
        "page_depth": 1,
    },
    "weiBo": {
        "label": "微博",
        "base_url": "https://weibo.com",
        "handler": "hot_search",
        "rate_limit": 1.0,
        "retry_max": 4,
        "page_depth": 3,
    },
    "dyKuaishou": {
        "label": "抖音/快手",
        "base_url": "https://www.douyin.com",
        "handler": "video_feed",
        "rate_limit": 2.5,
        "retry_max": 3,
        "page_depth": 2,
    },
    "bilibili": {
        "label": "B站",
        "base_url": "https://www.bilibili.com",
        "handler": "video_detail",
        "rate_limit": 1.0,
        "retry_max": 2,
        "page_depth": 2,
    },
    "zhihu": {
        "label": "知乎",
        "base_url": "https://www.zhihu.com",
        "handler": "question_answer",
        "rate_limit": 1.2,
        "retry_max": 3,
        "page_depth": 1,
    },
}

# 数据去重存储器（内存版Crawlee Dataset去重）
_DEDUP_STORE: dict[str, set[str]] = {}

# 跨请求的模拟种子——保证结果可复现但每次有差异
_SEED_COUNTER: dict[str, int] = {}


def _content_hash(url: str, handler: str) -> str:
    """生成内容指纹，用于自动去重（Crawlee Dataset 去重模式）。"""
    raw = f"{url}|{handler}|{datetime.now().strftime('%Y%m%d%H')}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _simulated_fetch(url: str, handler_type: str, proxy: str) -> dict[str, Any]:
    """
    模拟网络请求与数据采集。
    对应 Crawlee Router 中不同 handler 的分派逻辑。
    """
    seed_key = f"{handler_type}:{url}"
    _SEED_COUNTER[seed_key] = _SEED_COUNTER.get(seed_key, 0) + 1
    counter = _SEED_COUNTER[seed_key]

    # 模拟各类 handler 的采集结果
    if handler_type == "content_feed":
        titles = [
            "春季穿搭指南 | 5件基础款穿出高级感",
            "减脂餐一周食谱｜好吃不胖",
            "周末探店｜藏在胡同里的日式咖啡馆",
            "护肤Routine｜干皮换季维稳方案",
            "家居好物｜提升幸福感的10件小物",
        ]
        return {
            "_type": "feed_item",
            "title": titles[counter % len(titles)],
            "author": f"博主_{hashlib.md5(url.encode()).hexdigest()[:6]}",
            "likes": 1200 + counter * 37,
            "comments": 85 + counter * 5,
            "collections": 320 + counter * 12,
            "tags": ["穿搭", "日常"],
            "fetched_via": proxy,
        }

    elif handler_type == "article_mp":
        return {
            "_type": "article",
            "title": f"深度分析：{url.split('/')[-1][:20]}行业趋势报告",
            "author": f"机构号_{uuid.uuid4().hex[:4]}",
            "reads": 8500 + counter * 210,
            "likes": 210 + counter * 8,
            "word_count": 2800 + counter * 50,
            "is_original": counter % 3 != 0,
            "fetched_via": proxy,
        }

    elif handler_type == "hot_search":
        topics = [
            "科技早报｜AI芯片突破新节点",
            "热搜第一｜城市文旅出圈密码",
            "热议｜年轻人反向消费趋势",
            "体育｜国家队集训名单公布",
            "娱乐｜年度口碑剧集TOP10",
        ]
        return {
            "_type": "hot_topic",
            "topic": topics[counter % len(topics)],
            "heat_index": 850000 + counter * 12000,
            "discussion_count": 32000 + counter * 800,
            "rank": (counter % 10) + 1,
            "fetched_via": proxy,
        }

    elif handler_type == "video_feed":
        return {
            "_type": "video",
            "title": f"Vlog #{counter} | {url.split('/')[-1][:15]}日常记录",
            "author": f"UP主_{uuid.uuid4().hex[:4]}",
            "views": 35000 + counter * 1500,
            "likes": 1800 + counter * 90,
            "duration_sec": 180 + (counter % 5) * 30,
            "fetched_via": proxy,
        }

    elif handler_type == "video_detail":
        return {
            "_type": "video_detail",
            "title": f"【深度解析】{url.split('/')[-1][:20]}背后的故事",
            "author": f"创作者_{uuid.uuid4().hex[:4]}",
            "views": 120000 + counter * 5000,
            "danmaku_count": 4500 + counter * 120,
            "coins": 3200 + counter * 80,
            "duration_sec": 600 + (counter % 8) * 30,
            "fetched_via": proxy,
        }

    elif handler_type == "question_answer":
        return {
            "_type": "qa_item",
            "title": f"如何评价{url.split('/')[-1][:20]}？",
            "answers": 45 + counter * 3,
            "followers": 1200 + counter * 50,
            "views": 85000 + counter * 3000,
            "top_answer_likes": 2300 + counter * 70,
            "fetched_via": proxy,
        }

    else:
        return {
            "_type": "generic",
            "url": url,
            "title": f"通用采集结果 {counter}",
            "fetched_via": proxy,
        }


def _simulated_retry_policy(attempt: int, max_retries: int) -> float:
    """
    模拟 Crawlee 的指数退避重试策略。
    返回下一次重试前的等待秒数。
    """
    if attempt >= max_retries:
        return -1  # 放弃
    return 1.0 * (2 ** attempt) + 0.5  # 1.5s, 2.5s, 4.5s, ...


class DataCollector:
    """
    数据采集器 —— 参考 Crawlee 爬虫架构设计。

    核心设计模式（来自 apify/crawlee-python 8.8K⭐）:
    1. **请求队列** — add_target() 将目标加入内部队列
    2. **自动重试** — run() 中按 retry_max + 指数退避重试
    3. **代理轮换** — 每次请求从代理池轮换
    4. **Router 模式** — handler_type 决定请求的路由转发
    5. **数据持久化 + 去重** — 写入本地 JSON，基于内容指纹去重
    6. **Autoscaling 池** — parallelism 参数动态控制并发数
    """

    def __init__(self, storage_path: str = "~/.hermes/data/"):
        """
        Args:
            storage_path: 采集数据持久化存储根路径
        """
        self.storage_path = Path(storage_path).expanduser()
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # 采集任务注册表（对应 Crawlee 的 RequestQueue）
        self._collections: dict[str, dict[str, Any]] = {}

        # 内部统计
        self._stats_data: dict[str, Any] = {
            "total_collectors_created": 0,
            "total_targets_added": 0,
            "total_runs": 0,
            "total_items_collected": 0,
            "total_dedup_skipped": 0,
            "total_retries": 0,
            "total_errors": 0,
            "proxy_usage": {p: 0 for p in _PROXY_POOL},
            "handler_usage": {h: 0 for h in _SITE_HANDLERS},
            "started_at": time.time(),
        }

    # ───────── 采集任务管理 ─────────

    def create_collector(self, name: str, config: Optional[dict] = None) -> dict:
        """
        创建采集任务（对应 Crawlee 的 Crawler 实例创建）。

        一个 collector 是一个独立的爬取任务，包含：
        - 名称标识
        - 目标队列（内部 requests 列表）
        - 路由配置（决定 handler 分派）
        - 持久化数据集目录

        Args:
            name:   采集任务名称（唯一标识）
            config: 任务配置字典，支持:
                    - site: str — 指定目标站点（可选）
                    - handler: str — 默认 handler 类型
                    - rate_limit: float — 请求间隔（秒）
                    - retry_max: int — 最大重试次数
                    - dedup_enabled: bool — 是否启用去重

        Returns:
            dict: {
                id, name, config, targets_count, created_at, status
            }
        """
        if not name:
            return {"error": "采集任务名称不能为空"}

        collection_id = f"col_{uuid.uuid4().hex[:12]}"
        safe_name = name.strip().replace(" ", "_")

        default_config = {
            "site": "all",
            "handler": "auto",
            "rate_limit": 1.0,
            "retry_max": 3,
            "dedup_enabled": True,
            "proxy_rotation": True,
        }
        if config:
            default_config.update(config)

        now = datetime.now().isoformat()
        self._collections[collection_id] = {
            "id": collection_id,
            "name": safe_name,
            "config": default_config,
            "targets": [],            # 请求队列
            "results": [],            # 采集结果
            "created_at": now,
            "updated_at": now,
            "status": "created",      # created | running | completed | failed
            "run_count": 0,
        }

        # 初始化去重存储
        _DEDUP_STORE[collection_id] = set()

        self._stats_data["total_collectors_created"] += 1

        return {
            "id": collection_id,
            "name": safe_name,
            "config": default_config,
            "targets_count": 0,
            "created_at": now,
            "status": "created",
        }

    def add_target(self, url: str, handler_type: str) -> dict:
        """
        添加采集目标到最近创建的采集任务（或指定 collection_id）。

        对应 Crawlee 的 RequestQueue.addRequest() 模式。
        每个目标包含：
        - URL + handler 类型 → Router 分派
        - 唯一标识（用于去重）
        - 重试状态追踪

        Args:
            url:          采集目标 URL
            handler_type: 处理器类型，决定路由到哪个 handler:
                          - "content_feed"  — 内容流
                          - "article_mp"    — 公众号文章
                          - "hot_search"    — 热搜
                          - "video_feed"    — 视频流
                          - "video_detail"  — 视频详情
                          - "question_answer" — 问答
                          - 任意自定义类型

        Returns:
            dict: {
                target_id, url, handler_type, collection_id,
                dedup_key, status
            }
        """
        if not self._collections:
            # 如果没有采集任务，自动创建一个默认任务
            collector = self.create_collector("default")
            collection_id = collector["id"]
        else:
            # 使用最近创建的活跃任务
            collection_id = list(self._collections.keys())[-1]

        collection = self._collections[collection_id]
        target_id = f"tgt_{uuid.uuid4().hex[:10]}"
        dedup_key = _content_hash(url, handler_type)

        target = {
            "target_id": target_id,
            "url": url,
            "handler_type": handler_type,
            "collection_id": collection_id,
            "dedup_key": dedup_key,
            "status": "pending",     # pending | running | completed | failed
            "retry_count": 0,
            "max_retries": collection["config"]["retry_max"],
            "added_at": datetime.now().isoformat(),
        }

        collection["targets"].append(target)
        collection["updated_at"] = datetime.now().isoformat()
        self._stats_data["total_targets_added"] += 1

        return {
            "target_id": target_id,
            "url": url,
            "handler_type": handler_type,
            "collection_id": collection_id,
            "dedup_key": dedup_key,
            "status": "pending",
            "queue_position": len(collection["targets"]) - 1,
        }

    # ───────── 运行采集 ─────────

    def run(self, parallelism: int = 3) -> dict:
        """
        运行采集任务。

        对应 Crawlee 的 AutoscalingPool 模式：
        - parallelism 控制并发数（模拟线程池）
        - 每个目标经历：fetch → dedup → retry loop → persist
        - 代理自动轮换
        - 去重过滤重复内容

        Args:
            parallelism: 并发爬虫数（3~10 推荐，类似 Crawlee 的 autoscaling）

        Returns:
            dict: {
                collection_id, status, total_targets,
                succeeded, failed, skipped_dedup, retries,
                items_collected, run_time_seconds,
                parallelism, proxy_used
            }
        """
        if not self._collections:
            return {"error": "没有采集任务可执行，请先 create_collector()"}

        # 取最近活跃的采集任务执行
        collection_id = list(self._collections.keys())[-1]
        collection = self._collections[collection_id]

        if collection["status"] == "running":
            return {"error": f"采集任务 {collection_id} 正在运行中"}

        collection["status"] = "running"
        collection["run_count"] += 1
        self._stats_data["total_runs"] += 1

        targets = collection["targets"]
        config = collection["config"]
        parallelism = max(1, min(parallelism, 10))
        dedup_enabled = config.get("dedup_enabled", True)
        retry_max = config.get("retry_max", 3)
        proxy_rotation = config.get("proxy_rotation", True)
        rate_limit = config.get("rate_limit", 1.0)

        results: list[dict] = []
        succeeded = 0
        failed = 0
        skipped_dedup = 0
        total_retries = 0
        target_index = 0
        total_targets = len(targets)

        start_time = time.time()

        # 模拟 Autoscaling 并发池
        # 将 targets 分片，每个分片由一个 worker 处理
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def _worker(target: dict) -> list[dict]:
            """单个采集 worker 的执行逻辑。"""
            nonlocal succeeded, failed, skipped_dedup, total_retries

            worker_results: list[dict] = []

            # 去重检查（Crawlee Dataset 去重模式）
            if dedup_enabled:
                dedup_set = _DEDUP_STORE.get(collection_id, set())
                if target["dedup_key"] in dedup_set:
                    skipped_dedup += 1
                    target["status"] = "skipped_dedup"
                    self._stats_data["total_dedup_skipped"] += 1
                    return worker_results  # 跳过

            # 代理选择（轮换）
            if proxy_rotation:
                proxy_idx = hash(target["target_id"]) % len(_PROXY_POOL)
                proxy = _PROXY_POOL[proxy_idx]
                self._stats_data["proxy_usage"][proxy] += 1
            else:
                proxy = _PROXY_POOL[0]

            # 重试循环（Crawlee 自动重试 + 指数退避）
            for attempt in range(retry_max + 1):
                try:
                    # 模拟请求间隔（rate limiting）
                    time.sleep(rate_limit * 0.01)  # 毫秒级模拟

                    # 执行采集（Router 分派到对应 handler）
                    handler_type = target["handler_type"]
                    self._stats_data["handler_usage"][handler_type] = (
                        self._stats_data["handler_usage"].get(handler_type, 0) + 1
                    )

                    fetch_result = _simulated_fetch(
                        url=target["url"],
                        handler_type=handler_type,
                        proxy=proxy,
                    )

                    # 构建结果记录
                    result_record = {
                        "_id": target["target_id"],
                        "_collection_id": collection_id,
                        "_url": target["url"],
                        "_handler": handler_type,
                        "_dedup_key": target["dedup_key"],
                        "_proxy": proxy,
                        "_attempt": attempt + 1,
                        "_collected_at": datetime.now().isoformat(),
                        **fetch_result,
                    }

                    worker_results.append(result_record)

                    # 标记去重（将内容指纹加入去重集合）
                    if dedup_enabled:
                        _DEDUP_STORE.setdefault(collection_id, set()).add(target["dedup_key"])

                    succeeded += 1
                    target["status"] = "completed"
                    self._stats_data["total_items_collected"] += 1

                    # 成功，跳出重试循环
                    break

                except Exception as e:
                    total_retries += 1
                    self._stats_data["total_retries"] += 1

                    if attempt < retry_max - 1:
                        wait_time = _simulated_retry_policy(attempt, retry_max)
                        time.sleep(wait_time * 0.01)  # 毫秒级
                        target["retry_count"] = attempt + 1
                        continue
                    else:
                        # 重试耗尽
                        failed += 1
                        target["status"] = "failed"
                        self._stats_data["total_errors"] += 1
                        worker_results.append({
                            "_id": target["target_id"],
                            "_collection_id": collection_id,
                            "_url": target["url"],
                            "_handler": target["handler_type"],
                            "_error": f"重试 {retry_max} 次后失败",
                            "_collected_at": datetime.now().isoformat(),
                        })

            return worker_results

        # 使用线程池模拟并发采集（Autoscaling 池模式）
        run_results: list[dict] = []
        with ThreadPoolExecutor(max_workers=parallelism) as executor:
            future_map = {executor.submit(_worker, t): t for t in targets}
            for future in as_completed(future_map):
                try:
                    batch = future.result()
                    run_results.extend(batch)
                except Exception:
                    pass

        # 持久化采集结果
        collection["results"].extend(run_results)

        # 将结果写入磁盘（Crawlee 数据持久化模式）
        persist_dir = self.storage_path / collection_id
        persist_dir.mkdir(parents=True, exist_ok=True)
        for record in run_results:
            doc_id = record.get("_id", uuid.uuid4().hex)
            file_path = persist_dir / f"{doc_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False, indent=2)

        # 写入采集任务元数据
        meta = {
            "collection_id": collection_id,
            "name": collection["name"],
            "config": config,
            "run_count": collection["run_count"],
            "total_targets": total_targets,
            "succeeded": succeeded,
            "failed": failed,
            "skipped_dedup": skipped_dedup,
            "total_retries": total_retries,
            "results_stored": len(run_results),
            "run_at": datetime.now().isoformat(),
            "run_time_seconds": round(time.time() - start_time, 3),
            "parallelism": parallelism,
        }
        meta_path = persist_dir / "_run_meta.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        collection["status"] = "completed"
        collection["updated_at"] = datetime.now().isoformat()

        return {
            "collection_id": collection_id,
            "name": collection["name"],
            "status": "completed",
            "total_targets": total_targets,
            "succeeded": succeeded,
            "failed": failed,
            "skipped_dedup": skipped_dedup,
            "total_retries": total_retries,
            "items_collected": len(run_results),
            "run_time_seconds": round(time.time() - start_time, 3),
            "parallelism": parallelism,
            "proxy_used": list(self._stats_data["proxy_usage"].keys())[:3],
        }

    # ───────── 获取采集数据 ─────────

    def get_data(self, collection_id: str, filters: Optional[dict] = None) -> list[dict]:
        """
        获取采集结果数据，支持过滤。

        对应 Crawlee 的 Dataset.getData() 模式。
        从持久化存储中读取结果，支持字段过滤和查询。

        Args:
            collection_id: 采集任务ID
            filters:       过滤条件字典，支持:
                           - 精确匹配: {"_handler": "video_feed"}
                           - 范围过滤: {"likes": {"$gt": 1000}}
                           - 多条件:   {"_handler": "hot_search", "rank": {"$lte": 5}}

        Returns:
            list[dict]: 采集结果列表
        """
        filters = filters or {}

        # 先从内存读取
        collection = self._collections.get(collection_id)
        if collection and collection.get("results"):
            results = collection["results"]
        else:
            # 从磁盘读取持久化数据
            persist_dir = self.storage_path / collection_id
            if not persist_dir.exists():
                return []
            results = []
            for json_file in sorted(persist_dir.glob("*.json")):
                if json_file.name == "_run_meta.json":
                    continue
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        results.append(json.load(f))
                except (json.JSONDecodeError, OSError):
                    continue

        if not filters:
            return results

        # 过滤逻辑
        filtered = []
        for item in results:
            match = True
            for field, condition in filters.items():
                value = item.get(field)

                if isinstance(condition, dict):
                    # 运算符过滤
                    for op, expected in condition.items():
                        if op == "$gt":
                            if not (isinstance(value, (int, float)) and value > expected):
                                match = False
                        elif op == "$gte":
                            if not (isinstance(value, (int, float)) and value >= expected):
                                match = False
                        elif op == "$lt":
                            if not (isinstance(value, (int, float)) and value < expected):
                                match = False
                        elif op == "$lte":
                            if not (isinstance(value, (int, float)) and value <= expected):
                                match = False
                        elif op == "$eq":
                            if value != expected:
                                match = False
                        elif op == "$ne":
                            if value == expected:
                                match = False
                        elif op == "$in":
                            if not (isinstance(expected, list) and value in expected):
                                match = False
                        elif op == "$nin":
                            if isinstance(expected, list) and value in expected:
                                match = False
                        elif op == "$exists":
                            if expected and value is None:
                                match = False
                            elif not expected and value is not None:
                                match = False
                        else:
                            if value != expected:
                                match = False
                else:
                    # 精确匹配
                    if value != condition:
                        match = False

                if not match:
                    break

            if match:
                filtered.append(item)

        return filtered

    # ───────── 采集统计 ─────────

    def stats(self) -> dict:
        """
        获取采集统计信息。

        对应 Crawlee 的 AutoscalingPool.stats() 模式。
        统计内容包括各任务状态、代理使用、去重效果、吞吐量等。

        Returns:
            dict: {
                total_collectors,
                total_targets,
                total_items,
                total_dedup_skipped,
                total_retries,
                total_errors,
                collections: [...],
                proxy_usage: {...},
                handler_usage: {...},
                throughput,
                uptime,
                storage_path
            }
        """
        total_targets = sum(len(c["targets"]) for c in self._collections.values())
        total_items = sum(len(c["results"]) for c in self._collections.values())

        collections_info = []
        for cid, col in self._collections.items():
            collections_info.append({
                "id": cid,
                "name": col["name"],
                "status": col["status"],
                "targets": len(col["targets"]),
                "results": len(col["results"]),
                "run_count": col["run_count"],
                "created_at": col["created_at"],
                "updated_at": col["updated_at"],
            })

        uptime = round(time.time() - self._stats_data["started_at"], 2)
        total_run_time = sum(
            c.get("run_count", 0) * 0.5 for c in self._collections.values()
        ) or 1.0
        throughput = round(total_items / total_run_time, 2) if total_run_time > 0 else 0.0

        return {
            "total_collectors": len(self._collections),
            "total_targets": total_targets,
            "total_items_collected": total_items,
            "total_dedup_skipped": self._stats_data["total_dedup_skipped"],
            "total_retries": self._stats_data["total_retries"],
            "total_errors": self._stats_data["total_errors"],
            "collections": collections_info,
            "proxy_usage": self._stats_data["proxy_usage"],
            "handler_usage": self._stats_data["handler_usage"],
            "throughput_items_per_sec": throughput,
            "uptime_seconds": uptime,
            "storage_path": str(self.storage_path),
        }
