"""墨麟OS — 接力核心模块

标准的接力文件读写实现。
所有接力文件存放在 ~/.molin/relay/
"""

import json
import os
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

RELAY_DIR = Path(os.path.expanduser("~/.molin/relay"))

# ── 接力前缀定义（与 cron 时间线对齐） ──
RELAY_PREFIXES = {
    "intelligence": "intelligence_morning",   # 墨思 08:00
    "content": "content_flywheel",            # 墨迹 09:00
    "briefing": "briefing",                   # CEO  09:00
    "growth": "growth_flywheel",             # 墨增 10:00
    "governance": "governance",              # 墨盾 10:00
    "crm": "crm_flywheel",                   # 墨域 11:00
    "order": "order_flywheel",               # 墨单 14:00
    "ceo_review": "ceo_review",              # CEO复盘 17:00
}


class RelayWriter:
    """接力文件写入器"""

    def __init__(self, prefix: str):
        if prefix not in RELAY_PREFIXES:
            valid = ", ".join(RELAY_PREFIXES.keys())
            raise ValueError(f"未知接力前缀: {prefix}。有效值: {valid}")
        self.prefix = prefix
        self.file_prefix = RELAY_PREFIXES[prefix]
        RELAY_DIR.mkdir(parents=True, exist_ok=True)

    def write(
        self,
        summary: str,
        data: Optional[dict] = None,
        detail: str = "",
        downstream_skills: Optional[list] = None,
        errors: Optional[list] = None,
    ) -> str:
        """写入接力文件

        Args:
            summary: 一句话摘要（20字以内）
            data: 结构化接力数据
            detail: 详细描述
            downstream_skills: 下游应加载的技能列表
            errors: 执行过程中的错误列表

        Returns:
            写入的文件路径
        """
        today = date.today().isoformat()
        now = datetime.now().astimezone().isoformat()

        # 补全 origin 映射
        origin_map = {
            "intelligence": "墨思",
            "content": "墨迹",
            "briefing": "CEO",
            "growth": "墨增",
            "governance": "墨盾",
            "crm": "墨域",
            "order": "墨单",
            "ceo_review": "CEO",
        }

        relay = {
            "origin": origin_map.get(self.prefix, self.prefix),
            "timestamp": now,
            "relay_date": today,
            "summary": summary,
            "detail": detail,
            "data": data or {},
            "downstream_skills": downstream_skills or [],
            "errors": errors or [],
        }

        filepath = RELAY_DIR / f"{self.file_prefix}_{today}.json"
        filepath.write_text(
            json.dumps(relay, ensure_ascii=False, indent=2)
        )
        return str(filepath)


class RelayReader:
    """接力文件读取器"""

    @staticmethod
    def read(prefix: str, date_str: Optional[str] = None) -> Optional[dict]:
        """读取指定前缀的接力文件

        Args:
            prefix: 接力前缀 (intelligence, content, briefing, growth, etc.)
            date_str: 日期 YYYY-MM-DD，默认今天

        Returns:
            接力数据字典，或 None（文件不存在）
        """
        date_str = date_str or date.today().isoformat()
        file_prefix = RELAY_PREFIXES.get(prefix)
        if not file_prefix:
            return None

        filepath = RELAY_DIR / f"{file_prefix}_{date_str}.json"
        if not filepath.exists():
            return None

        try:
            return json.loads(filepath.read_text())
        except (json.JSONDecodeError, OSError):
            return None

    @staticmethod
    def read_all(date_str: Optional[str] = None) -> dict[str, Optional[dict]]:
        """读取指定日期的所有接力文件"""
        date_str = date_str or date.today().isoformat()
        result = {}
        for prefix, file_prefix in RELAY_PREFIXES.items():
            filepath = RELAY_DIR / f"{file_prefix}_{date_str}.json"
            if filepath.exists():
                try:
                    result[prefix] = json.loads(filepath.read_text())
                except (json.JSONDecodeError, OSError):
                    result[prefix] = None
            else:
                result[prefix] = None
        return result

    @staticmethod
    def list_recent(days: int = 7) -> list[str]:
        """列出最近 N 天的接力文件"""
        cutoff = time.time() - days * 86400
        files = []
        for f in sorted(RELAY_DIR.glob("*.json"), reverse=True):
            if f.stat().st_mtime >= cutoff:
                files.append(f.name)
        return files


# ── 便捷函数 ──

def write_relay(
    prefix: str,
    summary: str,
    data: Optional[dict] = None,
    detail: str = "",
    downstream_skills: Optional[list] = None,
    errors: Optional[list] = None,
) -> str:
    """便捷写入接力文件"""
    writer = RelayWriter(prefix)
    return writer.write(summary, data, detail, downstream_skills, errors)


def read_relay(prefix: str, date_str: Optional[str] = None) -> Optional[dict]:
    """便捷读取接力文件"""
    return RelayReader.read(prefix, date_str)


def list_todays_relays() -> dict[str, Optional[dict]]:
    """获取今天所有接力数据"""
    return RelayReader.read_all()


def list_recent_relays(days: int = 7) -> list[str]:
    """列出最近接力文件"""
    return RelayReader.list_recent(days)


# ── CLI入口 ──

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 relay_core.py write <prefix> <summary> [--data '{}'] [--detail '']")
        print("  python3 relay_core.py read <prefix> [--date YYYY-MM-DD]")
        print("  python3 relay_core.py list [--days 7]")
        sys.exit(1)

    action = sys.argv[1]

    if action == "write":
        if len(sys.argv) < 4:
            print("用法: write <prefix> <summary> [--data '{}'] [--detail '']")
            sys.exit(1)
        prefix = sys.argv[2]
        summary = sys.argv[3]
        data = {}
        detail = ""
        if "--data" in sys.argv:
            idx = sys.argv.index("--data") + 1
            if idx < len(sys.argv):
                data = json.loads(sys.argv[idx])
        if "--detail" in sys.argv:
            idx = sys.argv.index("--detail") + 1
            if idx < len(sys.argv):
                detail = sys.argv[idx]
        path = write_relay(prefix, summary, data, detail)
        print(f"✅ 接力文件已写入: {path}")

    elif action == "read":
        if len(sys.argv) < 3:
            print("用法: read <prefix> [--date YYYY-MM-DD]")
            sys.exit(1)
        prefix = sys.argv[2]
        date_str = None
        if "--date" in sys.argv:
            idx = sys.argv.index("--date") + 1
            if idx < len(sys.argv):
                date_str = sys.argv[idx]
        result = read_relay(prefix, date_str)
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"⚠️ 接力文件未找到: {prefix}_{date_str or date.today().isoformat()}.json")
            sys.exit(1)

    elif action == "list":
        days = 7
        if "--days" in sys.argv:
            idx = sys.argv.index("--days") + 1
            if idx < len(sys.argv):
                days = int(sys.argv[idx])
        files = list_recent_relays(days)
        if files:
            print(f"📂 最近 {days} 天的接力文件 ({len(files)} 个):")
            for f in files:
                fpath = RELAY_DIR / f
                mtime = datetime.fromtimestamp(fpath.stat().st_mtime).strftime("%m-%d %H:%M")
                size = fpath.stat().st_size
                print(f"  {mtime}  {size:>5}B  {f}")
        else:
            print(f"⚠️ 最近 {days} 天没有接力文件")
