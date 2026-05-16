#!/usr/bin/env python3
"""
墨麟OS · 跨线请求轮询 Worker
共享层 Agent D 使用，定期扫描 relay/shared/cross_request.json
发现有新请求时，调用对应技能执行，结果写回指定路径

用法:
  python3 ~/Molin-OS/tools/cross_request_worker.py           # 执行一次（供cron调用）
  python3 ~/Molin-OS/tools/cross_request_worker.py --watch    # 持续轮询模式

请求格式 (relay/shared/cross_request.json):
{
  "id": "uuid",
  "requester": "media|edu|side|global",
  "service": "research|finance|legal|data|arxiv",
  "task": "具体任务描述",
  "priority": "L0|L1|L2",
  "callback_path": "relay/shared/results/{id}.json",
  "created_at": "ISO时间戳",
  "processed": false
}
"""
import json
import os
import sys
import time
import uuid
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path.home() / "Molin-OS"
RELAY_DIR = BASE_DIR / "relay" / "shared"
REQUEST_FILE = RELAY_DIR / "cross_request.json"
CACHE_FILE = RELAY_DIR / "cache.json"

# 确保目录存在
RELAY_DIR.mkdir(parents=True, exist_ok=True)
(RELAY_DIR / "results").mkdir(exist_ok=True)
(RELAY_DIR / "cache").mkdir(exist_ok=True)


def load_requests():
    """读取跨线请求队列"""
    if not REQUEST_FILE.exists():
        return []
    try:
        data = json.loads(REQUEST_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return [data]
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, Exception):
        return []


def save_requests(requests):
    """写回请求队列"""
    REQUEST_FILE.write_text(
        json.dumps(requests, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def get_cached_result(service: str, task: str) -> dict | None:
    """检查缓存（相同query 24h内复用）"""
    if not CACHE_FILE.exists():
        return None
    try:
        cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        key = f"{service}::{task[:100]}"
        entry = cache.get(key)
        if entry:
            cached_at = datetime.fromisoformat(entry["cached_at"])
            age_hours = (datetime.now(timezone.utc) - cached_at).total_seconds() / 3600
            if age_hours < 24:
                return entry["result"]
    except Exception:
        pass
    return None


def set_cache_result(service: str, task: str, result: dict):
    """写入缓存"""
    try:
        cache = {}
        if CACHE_FILE.exists():
            cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        key = f"{service}::{task[:100]}"
        cache[key] = {
            "result": result,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }
        CACHE_FILE.write_text(
            json.dumps(cache, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except Exception:
        pass


def execute_service(service: str, task: str) -> dict:
    """执行对应服务"""
    # 检查缓存
    cached = get_cached_result(service, task)
    if cached:
        print(f"  [cache HIT] {service}: {task[:60]}...")
        return cached

    print(f"  [execute] {service}: {task[:60]}...")

    if service == "research":
        # 调用 gpt-researcher
        try:
            sys.path.insert(0, str(BASE_DIR / "tools"))
            from research_engine import research_sync
            result = research_sync(task)
            set_cache_result(service, task, result)
            return result
        except Exception as e:
            return {"status": "error", "error": str(e)}

    elif service == "arxiv":
        # 调用 arxiv 脚本
        import subprocess
        try:
            r = subprocess.run(
                [sys.executable, str(BASE_DIR / "skills" / "arxiv" / "scripts" / "search_arxiv.py"), task],
                capture_output=True, text=True, timeout=60,
            )
            result = {"status": "success", "output": r.stdout[:3000]}
            set_cache_result(service, task, result)
            return result
        except Exception as e:
            return {"status": "error", "error": str(e)}

    elif service == "finance":
        return {"status": "info", "message": "finance-report：需人工对接 molib CLI"}

    elif service == "legal":
        return {"status": "info", "message": "legal-review 需调用 molin-legal skill"}

    elif service == "data":
        return {"status": "info", "message": "data-analysis 需指定数据集路径"}

    return {"status": "error", "error": f"未知 service: {service}"}


def process_pending():
    """处理队列中所有待处理的请求"""
    requests = load_requests()
    if not requests:
        return 0

    processed = 0
    for req in requests:
        if req.get("processed", False):
            continue

        req_id = req.get("id", str(uuid.uuid4()))
        service = req.get("service", "")
        task = req.get("task", "")

        print(f"\n📋 处理请求 [{req_id}] {req.get('requester','?')} → {service}")

        result = execute_service(service, task)

        # 写回结果
        callback = req.get("callback_path")
        if callback:
            callback_path = Path(callback)
            if not callback_path.is_absolute():
                callback_path = RELAY_DIR / "results" / callback_path
            callback_path.parent.mkdir(parents=True, exist_ok=True)
            callback_path.write_text(
                json.dumps(result, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            print(f"  ✅ 结果写入 {callback_path}")

        req["processed"] = True
        req["processed_at"] = datetime.now(timezone.utc).isoformat()
        req["result_summary"] = result.get("status", "unknown")
        processed += 1

    save_requests(requests)
    return processed


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--watch":
        print("🔁 持续轮询模式 (每60秒)...")
        while True:
            count = process_pending()
            if count:
                print(f"  本次处理 {count} 个请求")
            time.sleep(60)
    else:
        count = process_pending()
        if count:
            print(f"✅ 处理完成: {count} 个请求")
        else:
            print("📭 无待处理请求")


if __name__ == "__main__":
    main()
