"""
墨麟OS — 飞轮依赖检查守卫 (Flywheel Guard)

在内容工厂和增长引擎任务开头调用，检查上游产出是否就绪。
防止飞轮断链时下游静默空转或使用过期数据。

用法:
    from molib.shared.flywheel_guard import check_upstream, flywheel_abort_if_broken

    # 内容工厂开头
    flywheel_abort_if_broken("intelligence_morning.json", "内容工厂飞轮")

    # 增长引擎开头
    flywheel_abort_if_broken("content_flywheel.json", "增长引擎飞轮")
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta


# 默认 relay 目录
RELAY_DIR = Path.home() / ".hermes" / "relay"


def check_upstream(
    relay_file: str,
    max_age_minutes: int = 90,
    relay_dir: Path | None = None,
) -> tuple[bool, str]:
    """
    检查飞轮上游产出是否就绪且足够新鲜。

    Args:
        relay_file: relay 目录下的文件名（如 "intelligence_morning.json"）
        max_age_minutes: 文件最大允许年龄（分钟），默认90分钟
        relay_dir: relay 目录路径，默认 ~/.hermes/relay/

    Returns:
        (ok: bool, reason: str)
    """
    base = relay_dir or RELAY_DIR
    path = base / relay_file

    if not path.exists():
        return False, (
            f"⚠️ 上游文件不存在: {relay_file}。"
            f"上游任务可能因余额不足而未执行。"
        )

    age = (datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)).total_seconds() / 60
    if age > max_age_minutes:
        return False, (
            f"⚠️ 上游数据过期: {relay_file} 已 {age:.0f} 分钟前生成"
            f"（阈值 {max_age_minutes}min）。"
        )

    return True, "ok"


def flywheel_abort_if_broken(
    relay_file: str,
    task_name: str,
    max_age_minutes: int = 90,
    relay_dir: Path | None = None,
) -> None:
    """
    上游断链时主动发送飞书告警并退出，而非静默空转。

    用法（在各定时任务 prompt 开头）:
        flywheel_abort_if_broken("intelligence_morning.json", "内容工厂飞轮")

    Args:
        relay_file: relay 目录下的文件名
        task_name: 任务名称（用于告警消息）
        max_age_minutes: 文件最大允许年龄（分钟）
        relay_dir: relay 目录路径
    """
    ok, reason = check_upstream(relay_file, max_age_minutes, relay_dir)

    if not ok:
        # 构建 T4 告警消息
        try:
            from molib.shared.publish.feishu_card_router import FeishuCardRouter

            payload = FeishuCardRouter.render(
                message=reason,
                data={"alert_title": f"飞轮断裂: {task_name} 无法启动"},
                ctx={"is_error": True},
            )
            # 记录告警消息（实际发送由调用方处理）
            print(f"[FLYWHEEL ABORT] {reason}")
            print(f"[FLYWHEEL PAYLOAD] {json.dumps(payload, ensure_ascii=False)}")
        except ImportError:
            print(f"[FLYWHEEL ABORT] {reason}")

        raise SystemExit(f"[FLYWHEEL ABORT] {reason}")


def flywheel_health_check() -> dict:
    """
    检查整个飞轮链路健康状态。

    Returns:
        {
            "intelligence_morning": {"exists": bool, "age_minutes": float, "status": str},
            "content_flywheel": {"exists": bool, "age_minutes": float, "status": str},
            "growth_flywheel": {"exists": bool, "age_minutes": float, "status": str},
            "overall": "healthy" | "degraded" | "broken",
        }
    """
    files = {
        "intelligence_morning": "intelligence_morning.json",
        "content_flywheel": "content_flywheel.json",
        "growth_flywheel": "growth_flywheel.json",
    }

    result = {}
    all_healthy = True
    any_exists = False

    for name, filename in files.items():
        ok, reason = check_upstream(filename, max_age_minutes=90)
        path = RELAY_DIR / filename
        age = 0

        if path.exists():
            any_exists = True
            age = (datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)).total_seconds() / 60

        result[name] = {
            "exists": path.exists(),
            "age_minutes": round(age, 1) if path.exists() else None,
            "status": "ok" if ok else reason,
        }

        if not ok and path.exists():
            all_healthy = False

    if not any_exists:
        result["overall"] = "broken"
    elif all_healthy:
        result["overall"] = "healthy"
    else:
        result["overall"] = "degraded"

    return result
