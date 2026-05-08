"""
墨麟OS — 数据备份脚本
====================
备份路径：
  ~/hermes-os/config/     — 配置文件（28K）
  ~/hermes-os/docs/       — 系统文档（524K）
  ~/hermes-os/relay/      — 飞轮接力数据（44K）
  ~/.hermes/memory/       — 向量记忆（384K）
  ~/.hermes/*.db          — SQLite数据库（~20K）
  ~/.hermes/.env          — 密钥文件（19K）
  ~/.hermes/config.yaml   — Hermes配置（11K）

非备份：
  ~/hermes-os/molib/      — 代码已通过 git 托管在 GitHub
  ~/.hermes/hermes-agent/ — 原始框架代码（可从 GitHub 重建）

用法：
    python3 bots/backup.py              # 执行备份
    python3 bots/backup.py --list       # 列出备份快照
    python3 bots/backup.py --clean      # 清理过期快照（保留7天）
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import tarfile
from datetime import datetime, timedelta
from pathlib import Path

BACKUP_DIR = Path.home() / ".hermes" / "backups"
RETENTION_DAYS = 7

# 要备份的源路径（相对于 HOME）
BACKUP_SOURCES = [
    "hermes-os/config",
    "hermes-os/docs",
    "hermes-os/relay",
    ".hermes/memory",
]

DB_GLOB = str(Path.home() / ".hermes" / "state.db")

# 小文件（直接复制）
FILE_SOURCES = [
    Path.home() / ".hermes" / ".env",
    Path.home() / ".hermes" / "config.yaml",
]

logger = logging.getLogger("molin.backup")


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def list_backups() -> list[dict]:
    """列出所有备份快照"""
    if not BACKUP_DIR.exists():
        return []
    backups = []
    for f in sorted(BACKUP_DIR.glob("hermes-os-backup-*.tar.gz"), reverse=True):
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        size = f.stat().st_size
        backups.append({
            "name": f.name,
            "date": mtime.strftime("%Y-%m-%d %H:%M:%S"),
            "size": f"{size / 1024:.0f} KB",
            "age": (datetime.now() - mtime).days,
        })
    return backups


def do_backup() -> str:
    """执行备份，返回备份文件路径"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"hermes-os-backup-{timestamp}.tar.gz"
    backup_path = BACKUP_DIR / backup_name

    home = Path.home()
    files_to_backup = []

    # 收集目录下的文件
    for rel_path in BACKUP_SOURCES:
        src = home / rel_path
        if src.exists() and src.is_dir():
            for f in src.rglob("*"):
                if f.is_file():
                    files_to_backup.append((str(f), str(f.relative_to(home))))
        elif src.exists():
            files_to_backup.append((str(src), str(src.relative_to(home))))

    # 收集 .db 文件
    db_parent = Path.home() / ".hermes"
    for f in db_parent.glob("*.db"):
        if f.is_file() and f.stat().st_size > 100:  # 忽略空db
            files_to_backup.append((str(f), str(f.relative_to(home))))

    # 收集小文件
    for src in FILE_SOURCES:
        if src.exists():
            files_to_backup.append((str(src), str(src.relative_to(home))))

    # 去重
    seen = set()
    unique_files = []
    for abs_path, rel_path in files_to_backup:
        if rel_path not in seen:
            seen.add(rel_path)
            unique_files.append((abs_path, rel_path))

    # 创建 tar.gz
    with tarfile.open(backup_path, "w:gz") as tar:
        for abs_path, rel_path in unique_files:
            tar.add(abs_path, arcname=rel_path)

    # 清理过期备份
    _cleanup()

    return str(backup_path)


def _cleanup():
    """删除过期备份"""
    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
    for f in BACKUP_DIR.glob("hermes-os-backup-*.tar.gz"):
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        if mtime < cutoff:
            f.unlink()
            logger.info("清理过期备份: %s", f.name)


def parse_args():
    parser = argparse.ArgumentParser(description="墨麟OS数据备份")
    parser.add_argument("--list", action="store_true", help="列出备份快照")
    parser.add_argument("--clean", action="store_true", help="清理过期备份")
    return parser.parse_args()


def main():
    setup_logging()
    args = parse_args()

    if args.list:
        backups = list_backups()
        if not backups:
            print("📦 暂无备份文件")
        else:
            print(f"📦 备份快照列表 (保留{RETENTION_DAYS}天):")
            for b in backups:
                age_str = "今天" if b["age"] == 0 else f"{b['age']}天前"
                print(f"  · {b['name']}  [{b['size']}]  {b['date']} ({age_str})")
        return

    if args.clean:
        removed = 0
        cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
        for f in BACKUP_DIR.glob("hermes-os-backup-*.tar.gz"):
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if mtime < cutoff:
                f.unlink()
                removed += 1
        print(f"🧹 已清理 {removed} 个过期备份 (保留{RETENTION_DAYS}天)")
        return

    # 执行备份
    path = do_backup()
    size = os.path.getsize(path) / 1024
    print(f"✅ 备份完成: {path}")
    print(f"   大小: {size:.1f} KB")
    print(f"   位置: {Path(path).parent}")


if __name__ == "__main__":
    main()
