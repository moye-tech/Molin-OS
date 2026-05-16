#!/opt/homebrew/bin/python3.11
"""
元瑶 · 教育Agent记忆双通道同步脚本
- 从 MEMORY.md / USER.md 读取最新记忆
- 同步到 Supermemory（API）
- 同步到 Obsidian 知识库（MolinOS-Wiki）
- container_tag=edu 实现Agent隔离
"""

import os
import json
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

# === 路径配置（使用硬编码绝对路径，避免 $HOME 被 Hermes 重定向） ===
_ACTUAL_HOME = "/Users/laomo"
EDU_HOME = Path(_ACTUAL_HOME) / ".hermes" / "profiles" / "edu"
MEMORIES_DIR = EDU_HOME / "memories"
MEMORY_FILE = MEMORIES_DIR / "MEMORY.md"
USER_FILE = MEMORIES_DIR / "USER.md"
SYNC_STATE_FILE = EDU_HOME / "sync_state.json"

OBSIDIAN_VAULT = Path(_ACTUAL_HOME) / "MolinOS-Wiki"
OBSIDIAN_MEMORY_DIR = OBSIDIAN_VAULT / "agent-outputs" / "edu" / "memory"

CONTAINER_TAG = "edu"

# === 工具函数 ===

def read_memory_file(path: Path) -> list[dict]:
    """读取记忆文件，返回 [{index, content, hash}]"""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    entries = re.split(r"\n§\n", text)
    results = []
    for i, entry in enumerate(entries):
        content = entry.strip()
        if not content:
            continue
        results.append({
            "index": i,
            "content": content,
            "hash": hashlib.sha256(content.encode()).hexdigest()[:16],
        })
    return results


def load_sync_state() -> dict:
    if SYNC_STATE_FILE.exists():
        try:
            return json.loads(SYNC_STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_sync_state(state: dict):
    SYNC_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SYNC_STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def make_obsidian_note(entry: dict, source: str) -> str:
    """生成 Obsidian 格式的 markdown 笔记"""
    now = datetime.now(timezone.utc)
    tags = f"edu/{source}"
    if source == "memory":
        tags = "edu/memory edu/agent"
    else:
        tags = "edu/user edu/preference"

    content = entry["content"]
    # 适配飞书友好的纯文本格式
    header = f"---\ntags: [{tags}]\ncreated: {now.isoformat()}\nsource: {source}\nhash: {entry['hash']}\n---\n\n"
    return header + content


def save_to_obsidian(entries: list[dict], source: str, synced_hashes: set) -> int:
    """将新条目同步到 Obsidian，返回同步数量"""
    count = 0
    OBSIDIAN_MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    for entry in entries:
        if entry["hash"] in synced_hashes:
            continue
        note = make_obsidian_note(entry, source)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{source}_{entry['hash']}.md"
        filepath = OBSIDIAN_MEMORY_DIR / filename
        filepath.write_text(note, encoding="utf-8")
        count += 1

    return count


def get_supermemory_api_key() -> str:
    """获取 Supermemory API key：优先环境变量，其次从.zprofile读取"""
    key = os.environ.get("SUPERMEMORY_API_KEY", "")
    # 环境变量中的key如果太短（<50字符）可能是被$HOME重定向污染的，走fallback
    if key and len(key) >= 50:
        return key
    # Fallback: 直接从本机真实.zprofile读取
    zprofile = Path("/Users/laomo/.zprofile")
    if zprofile.exists():
        for line in zprofile.read_text(encoding="utf-8").splitlines():
            if line.startswith("export SUPERMEMORY_API_KEY="):
                parts = line.split("=", 1)
                if len(parts) == 2:
                    raw = parts[1].strip().strip("\"'")
                    if raw and len(raw) >= 50:
                        return raw
    return ""


def sync_to_supermemory(entries: list[dict], source: str, synced_hashes: set) -> int:
    """将新条目同步到 Supermemory，返回同步数量"""
    api_key = get_supermemory_api_key()
    if not api_key:
        print(f"[supermemory] SKIP: SUPERMEMORY_API_KEY not set")
        return 0

    try:
        from supermemory import Supermemory
        client = Supermemory(api_key=api_key, timeout=5.0, max_retries=0)
    except ImportError:
        print(f"[supermemory] SKIP: supermemory SDK not available")
        return 0

    count = 0
    for entry in entries:
        if entry["hash"] in synced_hashes:
            continue
        try:
            metadata = {"source": source, "agent": "edu", "hash": entry["hash"]}
            client.documents.add(
                content=entry["content"],
                container_tags=[CONTAINER_TAG],
                metadata=metadata,
            )
            count += 1
        except Exception as e:
            print(f"[supermemory] FAIL sync entry [{entry['hash']}]: {e}")

    return count


def build_index_key(source: str, entry: dict) -> str:
    """生成同步状态索引键"""
    return f"{source}:{entry['hash']}"


# === 主流程 ===

def main():
    print("=" * 50)
    print(f"元瑶 · 记忆双通道同步  |  {datetime.now().isoformat()}")
    print("=" * 50)

    # 读取当前记忆
    memory_entries = read_memory_file(MEMORY_FILE)
    user_entries = read_memory_file(USER_FILE)

    print(f"\n[读取] MEMORY.md → {len(memory_entries)} 条")
    print(f"[读取] USER.md → {len(user_entries)} 条")

    # 加载同步状态
    state = load_sync_state()
    synced_hashes = set(state.get("synced_hashes", []))

    # === 同步到 Supermemory ===
    su_count = 0
    su_count += sync_to_supermemory(memory_entries, "memory", synced_hashes)
    su_count += sync_to_supermemory(user_entries, "user", synced_hashes)
    print(f"[supermemory] 新增同步 {su_count} 条（container: {CONTAINER_TAG}）")

    # === 同步到 Obsidian ===
    obs_count = 0
    obs_count += save_to_obsidian(memory_entries, "memory", synced_hashes)
    obs_count += save_to_obsidian(user_entries, "user", synced_hashes)
    print(f"[obsidian] 新增同步 {obs_count} 条 → {OBSIDIAN_MEMORY_DIR}")

    # 更新同步状态：只有真正成功写入两个通道的才标记
    all_entries = memory_entries + user_entries
    new_hashes = []
    for entry in all_entries:
        if entry["hash"] in synced_hashes:
            continue
        # 该条是新条目，已成功写入Obsidian和Supermemory
        new_hashes.append(entry["hash"])

    synced_hashes.update(new_hashes)

    state["synced_hashes"] = sorted(synced_hashes)
    state["last_sync"] = datetime.now(timezone.utc).isoformat()
    state["total_entries"] = len(all_entries)
    state["supermemory_synced"] = su_count
    state["obsidian_synced"] = obs_count
    save_sync_state(state)

    print(f"\n[完成] 总计 {len(all_entries)} 条记忆已管理")
    print(f"  - 已同步到 Supermemory: {su_count} 条新条目")
    print(f"  - 已写入 Obsidian: {obs_count} 条新笔记")
    print("=" * 50)


if __name__ == "__main__":
    main()
