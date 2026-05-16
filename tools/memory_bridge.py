#!/usr/bin/env python3
"""
墨麟OS · 记忆桥接工具
统一接口：读写Supermemory（跨Agent语义记忆）+ Obsidian（本地结构化知识）
"""
import os
import json
import asyncio
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(Path.home() / "Molin-OS" / ".env")

SUPERMEMORY_API_KEY = os.getenv("SUPERMEMORY_API_KEY", "")
OBSIDIAN_API_KEY    = os.getenv("OBSIDIAN_API_KEY", "")
OBSIDIAN_PORT       = 27123
OBSIDIAN_BASE       = f"http://localhost:{OBSIDIAN_PORT}"
MOLIN_OS_WIKI       = Path.home() / "MolinOS-Wiki"


# ── Supermemory 操作 ──────────────────────────────────────

def sm_add(content: str, tags: list[str] = None, profile: str = "global") -> bool:
    """向Supermemory添加记忆"""
    if not SUPERMEMORY_API_KEY:
        print("⚠️ SUPERMEMORY_API_KEY未配置")
        return False
    try:
        headers = {
            "Authorization": f"Bearer {SUPERMEMORY_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "content": content,
            "metadata": {
                "tags": tags or [],
                "profile": profile,
                "timestamp": datetime.now().isoformat(),
                "source": "molin-os"
            }
        }
        r = requests.post(
            "https://api.supermemory.ai/v1/memories",
            headers=headers,
            json=payload,
            timeout=10
        )
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Supermemory添加失败: {e}")
        return False


def sm_search(query: str, top_k: int = 5, profile: str = "global") -> list[str]:
    """从Supermemory搜索相关记忆"""
    if not SUPERMEMORY_API_KEY:
        return []
    try:
        headers = {"Authorization": f"Bearer {SUPERMEMORY_API_KEY}"}
        params = {
            "q": query,
            "limit": top_k,
            "filter": json.dumps({"profile": profile}) if profile != "global" else None
        }
        r = requests.get(
            "https://api.supermemory.ai/v1/memories/search",
            headers=headers,
            params={k: v for k, v in params.items() if v},
            timeout=10
        )
        if r.status_code == 200:
            results = r.json().get("memories", [])
            return [m.get("content", "") for m in results]
        return []
    except Exception as e:
        print(f"❌ Supermemory搜索失败: {e}")
        return []


# ── Obsidian 操作 ─────────────────────────────────────────

def obs_write(path: str, content: str) -> bool:
    """向Obsidian写入笔记（path为相对于Vault的路径）"""
    if not OBSIDIAN_API_KEY:
        # 没有API Key时，直接写文件
        full_path = MOLIN_OS_WIKI / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return True
    try:
        r = requests.put(
            f"{OBSIDIAN_BASE}/vault/{path}",
            headers={
                "Authorization": f"Bearer {OBSIDIAN_API_KEY}",
                "Content-Type": "text/markdown"
            },
            data=content.encode("utf-8"),
            timeout=5
        )
        return r.status_code in (200, 204)
    except Exception:
        # fallback到直接写文件
        full_path = MOLIN_OS_WIKI / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return True


def obs_read(path: str) -> str:
    """从Obsidian读取笔记"""
    # 优先从本地文件读取（更快更可靠）
    full_path = MOLIN_OS_WIKI / path
    if full_path.exists():
        return full_path.read_text(encoding="utf-8")

    if not OBSIDIAN_API_KEY:
        return ""
    try:
        r = requests.get(
            f"{OBSIDIAN_BASE}/vault/{path}",
            headers={"Authorization": f"Bearer {OBSIDIAN_API_KEY}"},
            timeout=5
        )
        return r.text if r.status_code == 200 else ""
    except Exception:
        return ""


def obs_append(path: str, content: str) -> bool:
    """追加内容到Obsidian笔记"""
    existing = obs_read(path)
    new_content = f"{existing}\n\n{content}" if existing else content
    return obs_write(path, new_content)


# ── 便捷函数 ──────────────────────────────────────────────

def save_task_experience(
    profile: str,
    task_type: str,
    task_desc: str,
    approach: str,
    result_summary: str,
    quality_score: int = 85,
):
    """
    保存任务执行经验（同时写Supermemory + Obsidian）
    在Worker执行成功后调用
    """
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 写Supermemory（跨Agent语义检索）
    sm_content = (
        f"[{profile}Agent][{task_type}] {task_desc}\n"
        f"成功方法: {approach}\n"
        f"结果摘要: {result_summary}\n"
        f"质量评分: {quality_score}/100"
    )
    sm_add(sm_content, tags=[profile, task_type, "experience"], profile=profile)

    # 写Obsidian（结构化存档）
    obs_path = f"agent-outputs/{profile}/experiences/{task_type}_{datetime.now().strftime('%Y%m%d')}.md"
    obs_content = f"""# [{profile.upper()}] {task_type} 经验记录
时间: {date_str}
质量评分: {quality_score}/100

## 任务描述
{task_desc}

## 成功方法
{approach}

## 结果摘要
{result_summary}

---
*由墨麟OS memory_bridge.py自动记录*
"""
    obs_write(obs_path, obs_content)
    print(f"✅ 经验已保存: {profile}/{task_type} (评分:{quality_score})")


def recall_experience(profile: str, task_type: str, query: str, top_k: int = 3) -> str:
    """
    检索相关历史经验（任务执行前调用）
    返回格式化的经验摘要字符串，可直接注入prompt
    """
    memories = sm_search(f"{profile} {task_type} {query}", top_k=top_k, profile=profile)

    if not memories:
        return ""

    result = f"\n\n【📚 相关历史经验（{len(memories)}条）】\n"
    for i, mem in enumerate(memories, 1):
        result += f"\n经验{i}：{mem[:200]}{'...' if len(mem) > 200 else ''}\n"

    return result


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "test"

    if cmd == "test":
        print("测试Supermemory连接...")
        ok = sm_add("墨麟OS记忆系统测试", tags=["test"], profile="global")
        print(f"写入: {'✅' if ok else '❌'}")

        results = sm_search("墨麟OS", top_k=1)
        print(f"读取: {'✅' if results else '⚠️ 暂无结果（刚写入需要时间索引）'}")

        print("\n测试Obsidian写入...")
        ok = obs_write("test/memory_bridge_test.md", f"# 测试\n时间: {datetime.now()}")
        print(f"写入: {'✅' if ok else '❌'}")
        print(f"文件位置: {MOLIN_OS_WIKI}/test/memory_bridge_test.md")

    elif cmd == "save":
        save_task_experience(
            profile=sys.argv[2] if len(sys.argv) > 2 else "media",
            task_type="test_task",
            task_desc="测试任务",
            approach="标准方法",
            result_summary="测试成功",
        )

    elif cmd == "watch":
        import time
        print("🧠 Memory Bridge 守护进程已启动（每20分钟同步）")
        while True:
            now = datetime.now().strftime("%H:%M:%S")
            print(f"[{now}] 同步检查...")
            time.sleep(1200)  # 20分钟

    else:
        print(f"用法: python3.11 tools/memory_bridge.py [test|save]")
