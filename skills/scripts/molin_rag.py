"""
墨麟 RAG 注入脚本 — molin_rag.py
被 molin-xxx skill 在执行前调用，自动注入子公司相关记忆

用法:
  python3 molin_rag.py <子公司名> "<任务描述>"
  返回上下文文本（可空）
"""
import sys, json, pathlib, re

SCRIPT_DIR = pathlib.Path(__file__).parent
MEMORY_SCRIPT = SCRIPT_DIR / "molin_memory.py"

# 子公司名 → 标准拼音 collection 名 映射
SUBSIDIARY_EN_MAP = {
    "墨智": "mozhi", "墨码": "moma", "墨商BD": "moshang_bd", "墨影": "moying",
    "墨增": "mozeng", "墨声": "mosheng", "墨域": "moyu", "墨单": "modan",
    "墨算": "mosuan", "墨思": "mosi", "墨律": "molv", "墨盾": "modun",
    "墨品": "mopin", "墨数": "moshu", "墨维": "mowei", "墨育": "moyu_edu",
    "墨海": "mohai", "墨脑": "monao", "墨迹": "moji", "墨投": "motou",
    "墨商销售": "moshang_sale", "墨工": "mogong",
}

# Skill → 子公司 映射
SKILL_SUBSIDIARY = {
    "molin-legal": "墨律", "molin-trading": "墨投", "molin-trading-agents": "墨投",
    "molin-xiaohongshu": "墨影", "molin-vizro": "墨数",
    "molin-customer-service": "墨声", "molin-global": "墨海",
    "molin-memory": "墨脑",
}


def get_subsidiary(skill_or_name: str) -> str:
    """从 skill 名或子公司名获取标准子公司名"""
    if skill_or_name in SKILL_SUBSIDIARY:
        return SKILL_SUBSIDIARY[skill_or_name]
    if skill_or_name in SUBSIDIARY_EN_MAP:
        return skill_or_name
    # Try to match 墨X pattern
    for cn in SUBSIDIARY_EN_MAP:
        if cn in skill_or_name:
            return cn
    return None


def inject_context(subsidiary: str, task: str, top_k: int = 3) -> str:
    """生成带记忆的上下文，供子公司 Agent 注入"""
    import subprocess
    result = subprocess.run(
        [sys.executable, str(MEMORY_SCRIPT), "context", subsidiary, task, str(top_k)],
        capture_output=True, text=True, timeout=15
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return ""


def store_result(subsidiary: str, task: str, summary: str, metadata: dict = None):
    """执行完成后，将结果存入记忆"""
    import subprocess
    meta_json = json.dumps(metadata or {}, ensure_ascii=False)
    result = subprocess.run(
        [sys.executable, str(MEMORY_SCRIPT), "store", subsidiary, summary[:500], meta_json],
        capture_output=True, text=True, timeout=15
    )
    return result.returncode == 0


def main():
    if len(sys.argv) < 3:
        print("用法:")
        print("  python3 molin_rag.py context <子公司/技能名> \"<任务描述>\"  # 注入上下文")
        print("  python3 molin_rag.py store <子公司> \"<摘要>\"           # 存储记忆")
        print("  python3 molin_rag.py resolve <技能名>                  # 解析子公司名")
        return

    cmd = sys.argv[1]

    if cmd == "context":
        name = sys.argv[2]
        task = sys.argv[3] if len(sys.argv) > 3 else ""
        sub = get_subsidiary(name)
        if not sub:
            print(f"⚠ 未知子公司/技能: {name}")
            return
        ctx = inject_context(sub, task)
        if ctx:
            print(ctx)
        else:
            print("")
        return

    if cmd == "store":
        sub = sys.argv[2]
        summary = sys.argv[3] if len(sys.argv) > 3 else ""
        meta = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
        success = store_result(sub, "auto_store", summary, meta)
        print("✅" if success else "❌")
        return

    if cmd == "resolve":
        name = sys.argv[2]
        sub = get_subsidiary(name)
        if sub:
            en = SUBSIDIARY_EN_MAP.get(sub, sub)
            print(f"{sub}|{en}")
        else:
            print("")


if __name__ == "__main__":
    main()
