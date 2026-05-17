#!/usr/bin/env python3
"""墨麟OS 实时记忆同步引擎 v5.1 — 规范文件名 + 结构化内容 + 去重 + Agent chatter 过滤"""
from __future__ import annotations
import json, os, re, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional

HOME = Path.home()
BEIJING_TZ = timezone(timedelta(hours=8))
NOW = datetime.now(BEIJING_TZ)
DATE_STR = NOW.strftime("%Y-%m-%d")

VAULT = Path(os.environ.get(
    "OBSIDIAN_VAULT_PATH",
    f"{HOME}/Library/Mobile Documents/iCloud~md~obsidian/Documents"
))

CATEGORIES = {
    "决策": "不可逆的选择（技术选型、架构定稿、战略方向）",
    "知识": "沉淀积累（研究、架构理解、思维模型）",
    "流程": "可执行步骤（SOP、配置、操作手册、检查清单）",
    "成果": "可交付物（报告、产出物、数据）",
}

AGENTS = {
    "edu": "元瑶教育", "global": "梅凝出海",
    "media": "银月传媒", "shared": "玄骨中枢", "side": "宋玉创业",
}

SUPERMEMORY_API_KEY = os.environ.get("SUPERMEMORY_API_KEY", "")
SUPERMEMORY_TAGS = {
    "edu": "edu", "global": "molin-global", "media": "molin-media",
    "shared": "molin-shared", "side": "molin-side",
}

# ─── v5 分类器（保持 v4 规则）───
CLASSIFIER_RULES = [
    (r"决定|选择|改用|采用|放弃|定稿|选型|切换|migrate.*to|switch.*to|replace.*with|弃用", "决策"),
    (r"架构|方案|选型|技术栈|方向|战略|roadmap|trade.?off", "决策"),
    (r"学习|研究|分析|笔记|总结|沉淀|架构|设计|pattern|方法论|知识|领域|认知|理解|洞察", "知识"),
    (r"learn|research|study|note|knowledge|base|architecture|pattern|方法论|思维模型", "知识"),
    (r"调研|对比|评估|分析|趋势|洞察|发现|conclusion|insight", "知识"),
    (r"步骤|流程|操作|方法|how.to|指南|教程|tutorial|workflow|checklist|规范|SOP", "流程"),
    (r"配置|设置|setup|install|config|环境变量|token|apikey|\.env|toolchain|依赖|安装", "流程"),
    (r"操作手册|指引|protocol|标准|template|模板", "流程"),
    (r"日报|周报|报告|数据|统计|trending|analytics|metrics|指标|mirofish|预测|趋势|简报", "成果"),
    (r"产出|文章|文案|稿件|脚本|design|封面|生图|cove|图片|设计|作品|交付|deliverable", "成果"),
]

# ─── 噪声过滤 ───
NOISE_PREFIXES = [
    r"\[IMPORTANT:",
    r"\[SYSTEM",
    r"\[INSTALL",
    r"\[NOTE:",
    r"You are running as",
    r"<system",
    r"<\|",
    r"# Profile:",
]

# ─── v5 文件名净化 ───
FILENAME_STRIP_CHARS = r'[\[\](){}#·*|:<>"\'!?@$%^&=+\\/]+'
FILENAME_COLLAPSE_SPACES = re.compile(r'\s+')
FILENAME_MAX_LEN = 24
FILENAME_MIN_MEANINGFUL = 2  # 最少有意义的字符数


def sanitize_filename(raw: str) -> str:
    """净化文件名：去特殊字符、规范化空白、限制长度"""
    # 去特殊字符
    cleaned = re.sub(FILENAME_STRIP_CHARS, '', raw)
    # 压缩连续空白为单个空格
    cleaned = FILENAME_COLLAPSE_SPACES.sub(' ', cleaned).strip()
    # 去掉纯数字/纯符号
    cleaned = cleaned.strip('. 。，,；;、')
    if len(cleaned) < FILENAME_MIN_MEANINGFUL:
        return "对话记录"
    # 截断（在 UTF-8 字符边界）
    if len(cleaned) > FILENAME_MAX_LEN:
        # 尝试在中文词边界截断
        truncated = cleaned[:FILENAME_MAX_LEN]
        # 如果在中文字符中间截断，回退一个字符
        while truncated and ord(truncated[-1]) > 127 and len(truncated.encode('utf-8')) % 3 != 0:
            truncated = truncated[:-1]
        if not truncated:
            truncated = cleaned[:FILENAME_MAX_LEN]
        cleaned = truncated.rstrip()
    return cleaned or "对话记录"


def extract_topic(title: str, body: str) -> str:
    """
    v5 话题提取：多层次回退，保证有意义且干净。

    优先级：
    1. 从标题/正文匹配已知专有名词
    2. 从正文匹配中文关键名短语
    3. 取标题的前几个有意义字符
    4. 回退"对话记录"
    """
    combined = f"{title}\n{body}"

    # Tier 1: 专有名词
    proper_nouns = [
        "CloakServe", "Shopify", "GitHub", "AWS", "阿里云",
        "Stripe", "TTS", "CDP", "Feishu", "Obsidian", "Supermemory",
        "Molin-OS", "墨麟OS", "MiroFish",
        "小红书", "抖音", "TikTok", "跨境电商", "Shopee", "Lazada",
        "vLLM", "llama", "HuggingFace",
    ]
    for noun in proper_nouns:
        if noun.lower() in combined.lower():
            return noun

    # Tier 2: 有意义的中文动作/主题词
    topic_words = [
        "选型", "方案定稿", "架构设计", "部署", "迁移", "集成",
        "调研", "测试", "报告", "日报", "周报",
        "配置", "安装", "调试", "优化",
        "封面生成", "生图", "设计规范",
        "记忆同步", "管道", "profile",
        "身份框架", "核心配置",
        "创业", "出海", "教育",
    ]
    for word in topic_words:
        if word in combined:
            return word

    # Tier 2.5: 提取中英文混合标题中的关键英文词（GitHub 仓库名、项目名）
    # 例如 "学习 freestylefly/awesome-prompt" → "freestylefly"
    # 例如 "分析 freeCodeCamp 平台技术栈" → "freeCodeCamp"
    en_extract = re.findall(r'([A-Za-z][A-Za-z0-9_-]{3,})', title)
    if en_extract:
        # 取最长的非噪声英文词
        noise_en = {'import', 'from', 'with', 'this', 'that', 'have', 'been', 'will', 'would', 'should', 'about'}
        meaningful = [w for w in en_extract if w.lower() not in noise_en and len(w) > 3]
        if meaningful:
            return sanitize_filename(meaningful[0])

    # Tier 3: 取标题的前 18 个字符（跳过噪声词），尝试删出完整短语
    stripped = re.sub(r'^(首先[，,]?|然后|另外|这个|帮我|问一下|请问)\s*', '', title)
    if len(stripped) >= 6:
        return sanitize_filename(stripped[:18])

    # Tier 4: 回退
    return "对话记录"


def filter_noise(text: str) -> str:
    """过滤系统提示词和噪声行"""
    lines = text.split("\n")
    clean = []
    skip_mode = False
    for line in lines:
        # 检测噪声前缀
        is_noise = False
        for prefix in NOISE_PREFIXES:
            if re.match(prefix, line.strip(), re.I):
                is_noise = True
                skip_mode = True  # 进入跳过模式（处理多行系统提示）
                break
        if skip_mode:
            # 遇到空行或非系统行则退出跳过模式
            if line.strip() and not is_noise and not line.startswith(" ") and not line.startswith("\t"):
                skip_mode = False
            elif not line.strip():
                skip_mode = False
            else:
                continue
        if is_noise:
            continue
        clean.append(line)
    result = "\n".join(clean).strip()
    return result


def extract_user_intent(messages: list[dict]) -> str:
    """提取用户的真实意图（第一条有意义的消息）"""
    for m in messages:
        if m["role"] != "user":
            continue
        text = filter_noise(m["content"])
        # 跳过纯系统指令
        if not text or len(text) < 10:
            continue
        # 取前 100 字符作为意图摘要
        return text[:100].replace("\n", " ").strip()
    return "对话摘要"


# ─── Agent 内部操作语言过滤 ───
# 这些是 agent 在执行任务时的自言自语，不是面向用户的知识结论
AGENT_CHATTER_PATTERNS = [
    r"^Let me (start|begin|explore|check|see|examine|look|fetch|read|clone|try|get|find|grab|pull)",
    r"^I('ll| will) (clone|read|check|look|start|try|need|fetch|examine|explore|get|grab)",
    r"^Now I (have|understand|see|know|need|want|can)",
    r"^I need to ",
    r"^Let's (start|begin|check|see|try|look)",
    r"^First,? (let me|I('ll| will))",
    r"^(First|Next|Then|Finally|Now),? (let me|I('ll| will))", 
    r"^(好[，,]?|好的[，,]?|明白[了，,]?|嗯[，,]?)我先",
    r"^(现在|让我|我先|我来|我看看|我查|我搜|我找|我去)",
    r"^(找到了|拿到了|看到了|读完了|了解了|知道了)[，,，]?",
    r"^(先|再|然后|接着)(让我|我来|查看|检查|搜索|读取)",
    r"^\[Replying to",
    r"^Replying to:",
    r"^I see (the|that|you|this|your|we|an? )",
    r"^Let me look at ",
    r"^Let me examine ",
    r"^Let me read ",
    r"^Let me check ",
    r"^(Step|Phase) \\d",
    r"^#+ (Task|Step|Phase|Todo|Plan)",
    r"^I have (read|examined|checked|looked|reviewed) ",
    r"^(The|This) (file|code|repo|project|script|function) ",
    r"^```",  # Code blocks at start are planning, not conclusions
]


def is_agent_chatter(text: str) -> bool:
    """检测是否为 agent 内部操作语言"""
    for pattern in AGENT_CHATTER_PATTERNS:
        if re.match(pattern, text.strip()):
            return True
    return False


def extract_conclusions(messages: list[dict]) -> list[str]:
    """
    提取 assistant 的真实结论，跳过内部操作语言。
    
    策略：
    1. 优先取 LATER 消息（agent 在最后做的总结通常最好）
    2. 跳过以 agent chatter 开头的消息
    3. 偏好中文开头或包含 结论/总结/发现 的消息
    """
    conclusions = []
    # 从后往前扫，后面的回复通常包含总结
    for m in reversed(messages):
        if m["role"] != "assistant":
            continue
        text = filter_noise(m["content"])
        if not text or len(text) < 20:
            continue
        
        lines = text.split("\n")
        meaningful_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped in ("---", "***", "===", "```"):
                continue
            if len(stripped) < 3 and any(ord(c) > 127 for c in stripped):
                continue
            meaningful_lines.append(stripped)
            if len(meaningful_lines) >= 3:
                break
        
        if not meaningful_lines:
            continue
        
        # 检查第一条有意义的行是否是 agent chatter
        first_line = meaningful_lines[0]
        if is_agent_chatter(first_line):
            continue
        
        # 偏好：中文开头 或 包含结论关键词
        is_chinese = any('\u4e00' <= c <= '\u9fff' for c in first_line[:3])
        has_conclusion_marker = any(kw in text[:200] for kw in 
            ['结论', '总结', '发现', '核心', '学到', '关键', '完成', '方案'])
        
        conclusion = " ".join(meaningful_lines[:3])[:300]
        
        if conclusion not in conclusions and len(conclusion) > 15:
            conclusions.append(conclusion)
    
    # 如果所有消息都被过滤了，回退到原始行为（去掉 chatter 前缀）
    if not conclusions:
        for m in reversed(messages):
            if m["role"] != "assistant":
                continue
            text = filter_noise(m["content"])
            if not text or len(text) < 20:
                continue
            lines = text.split("\n")
            meaningful_lines = []
            for line in lines:
                stripped = line.strip()
                if not stripped or stripped in ("---", "***", "===", "```"):
                    continue
                # 跳过 chatter 行
                if is_agent_chatter(stripped):
                    continue
                if len(stripped) < 3 and any(ord(c) > 127 for c in stripped):
                    continue
                meaningful_lines.append(stripped)
                if len(meaningful_lines) >= 3:
                    break
            if meaningful_lines:
                conclusion = " ".join(meaningful_lines[:3])[:300]
                if conclusion not in conclusions and len(conclusion) > 15:
                    conclusions.append(conclusion)
    
    return conclusions


def classify_content(text: str) -> str:
    """MECE 分类器"""
    for pattern, category in CLASSIFIER_RULES:
        if re.search(pattern, text, re.I):
            return category
    return "知识"


def classify_content_deep(combined_text: str, messages: list[dict]) -> str:
    """
    深度分类：综合全文 + 对话意图。优先返回更准确的分类。
    """
    # 先尝试全文匹配
    cat = classify_content(combined_text)
    if cat != "知识":
        return cat
    # 如果是默认的"知识"，再检查一下是否应该是别的
    # 检查是否有明确的任务/产出标记
    if re.search(r"(生成|创建|写|制作|画|设计|产出一?篇|新建)", combined_text):
        return "成果"
    if re.search(r"(部署|安装|配置|启动|运行|设置|搭建)", combined_text):
        return "流程"
    return cat


# ═══════════════════════════════════════════════
# 去重追踪
# ═══════════════════════════════════════════════

def get_tracker_path(agent_id: str) -> Path:
    return HOME / ".hermes" / "profiles" / agent_id / "sync_tracker.json"


def load_tracker(agent_id: str) -> dict:
    tracker_path = get_tracker_path(agent_id)
    if tracker_path.exists():
        try:
            return json.loads(tracker_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_tracker(agent_id: str, tracker: dict):
    tracker_path = get_tracker_path(agent_id)
    tracker_path.parent.mkdir(parents=True, exist_ok=True)
    tracker_path.write_text(json.dumps(tracker, ensure_ascii=False, indent=2))


def is_already_synced(agent_id: str, session_path: Path) -> bool:
    """检查 session 是否已同步（按 mtime + size）"""
    tracker = load_tracker(agent_id)
    stat = session_path.stat()
    key = session_path.name
    if key in tracker:
        entry = tracker[key]
        if entry.get("mtime") == stat.st_mtime and entry.get("size") == stat.st_size:
            return True
    return False


def mark_synced(agent_id: str, session_path: Path):
    tracker = load_tracker(agent_id)
    stat = session_path.stat()
    tracker[session_path.name] = {
        "mtime": stat.st_mtime,
        "size": stat.st_size,
        "synced_at": NOW.isoformat(),
        "agent": agent_id,
    }
    # 清理 30 天前的记录
    cutoff = NOW - timedelta(days=30)
    stale = [k for k, v in tracker.items()
             if v.get("synced_at", "") < cutoff.isoformat()]
    for k in stale:
        del tracker[k]
    save_tracker(agent_id, tracker)


# ═══════════════════════════════════════════════
# Obsidian 写入（v5 — 完整结构化内容）
# ═══════════════════════════════════════════════

def write_to_obsidian(agent_id: str, category: str, topic: str,
                      entry_data: dict) -> Path:
    """
    写入 Obsidian — 活文档追加模式。
    entry_data 结构：
    {
        "conclusion": str,     # 一句话结论
        "background": str,     # 背景/上下文
        "details": list[str],  # 核心内容点
        "next_steps": str,     # 下一步
        "tags": list[str],
        "source": str,
    }
    """
    tags = entry_data.get("tags", [])
    source = entry_data.get("source", "实时同步")
    filename = f"{topic}.md"

    target_dir = VAULT / category
    target_dir.mkdir(parents=True, exist_ok=True)
    filepath = target_dir / filename

    # 构建追加内容块（金字塔格式）
    conclusion = entry_data.get("conclusion", "").strip()
    background = entry_data.get("background", "").strip()
    details = entry_data.get("details", [])
    next_steps = entry_data.get("next_steps", "").strip()

    block_lines = []
    if conclusion:
        block_lines.append(f"### 结论\n{conclusion}")
    if background:
        block_lines.append(f"\n### 背景\n{background}")
    if details:
        block_lines.append(f"\n### 核心内容")
        for d in details[:5]:
            d = d.strip()
            if d:
                block_lines.append(f"- {d}")
    if next_steps:
        block_lines.append(f"\n### 下一步\n{next_steps}")
    else:
        block_lines.append(f"\n### 下一步\n- [ ] 待补充")

    block = "\n".join(block_lines)

    if filepath.exists():
        existing = filepath.read_text(encoding="utf-8")
        # 追加
        append_content = f"\n\n---\n\n## {DATE_STR}\n\n{block}"
        filepath.write_text(existing + append_content, encoding="utf-8")
        _update_frontmatter_date(filepath)
        return filepath

    # 新文件
    tag_str = ", ".join(tags[:5])
    frontmatter = (
        "---\n"
        f"created: {DATE_STR}\n"
        f"updated: {DATE_STR}\n"
        f"agent: {agent_id}\n"
        f"category: {category}\n"
        f"status: 活跃\n"
        f"confidence: 待验证\n"
        f"importance: ⭐⭐\n"
        f"source: {source}\n"
        f"tags: [{tag_str}]\n"
        "---\n\n"
    )

    content = (
        f"{frontmatter}"
        f"# {topic}\n\n"
        f"## {DATE_STR}\n\n"
        f"{block}\n"
    )

    filepath.write_text(content, encoding="utf-8")
    return filepath


def _update_frontmatter_date(filepath: Path):
    """更新 frontmatter 的 updated 字段"""
    content = filepath.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return
    new_content = re.sub(
        r"^updated: \S+",
        f"updated: {DATE_STR}",
        content,
        count=1,
        flags=re.MULTILINE,
    )
    if new_content != content:
        filepath.write_text(new_content, encoding="utf-8")


# ═══════════════════════════════════════════════
# Supermemory 写入
# ═══════════════════════════════════════════════

def read_env_api_key() -> str:
    for env_path in [
        HOME / ".hermes" / ".env",
        HOME / ".hermes" / "profiles" / "media" / ".env",
    ]:
        if env_path.exists():
            for line in env_path.read_text().split("\n"):
                line = line.strip()
                if line.startswith("SUPERMEMORY_API_KEY="):
                    return line.split("=", 1)[1].strip().strip("'\"")
    return ""


def write_to_supermemory(agent_id: str, category: str, topic: str,
                         entry_data: dict) -> bool:
    """写入 Supermemory — 完整结构化内容"""
    api_key = SUPERMEMORY_API_KEY or read_env_api_key()
    if not api_key:
        return False
    try:
        from supermemory import Supermemory
    except ImportError:
        return False

    conclusion = entry_data.get("conclusion", "")
    background = entry_data.get("background", "")
    details = entry_data.get("details", [])
    next_steps = entry_data.get("next_steps", "")

    # 构建结构化正文
    parts = [f"# {topic}"]
    if conclusion:
        parts.append(f"\n## 结论\n{conclusion}")
    if background:
        parts.append(f"\n## 背景\n{background}")
    if details:
        parts.append(f"\n## 核心内容\n" + "\n".join(f"- {d}" for d in details[:5]))
    if next_steps:
        parts.append(f"\n## 下一步\n{next_steps}")

    content = "\n".join(parts)
    tag = SUPERMEMORY_TAGS.get(agent_id, agent_id)

    try:
        client = Supermemory(api_key=api_key, timeout=10, max_retries=1)
        client.documents.add(
            content=content[:3000],
            container_tags=[tag],
            metadata={
                "type": "molin_memory_v5",
                "category": category,
                "agent_id": agent_id,
                "agent_name": AGENTS.get(agent_id, ""),
                "topic": topic,
                "timestamp": NOW.isoformat(),
            },
        )
        return True
    except Exception as e:
        print(f"    ⚠️ Supermemory 写入失败: {e}")
        return False


# ═══════════════════════════════════════════════
# 对话处理（v5 重写）
# ═══════════════════════════════════════════════

def process_session(session_path: Path, agent_id: str) -> Optional[dict]:
    """
    分析单个对话 → 提取规范化结构化摘要。

    返回 None 表示无有效内容或已同步。
    返回 dict 包含完整结构化的 entry_data。
    """
    try:
        data = json.loads(session_path.read_text(errors="replace"))
    except (json.JSONDecodeError, OSError):
        return None

    # 解析消息
    messages = []
    if isinstance(data, dict):
        msgs = data.get("messages", data.get("conversation", []))
        if isinstance(msgs, str):
            try:
                msgs = json.loads(msgs)
            except:
                msgs = []
    elif isinstance(data, list):
        msgs = data
    else:
        msgs = []

    if not isinstance(msgs, list):
        msgs = []

    parsed = []
    for msg in msgs:
        if not isinstance(msg, dict):
            continue
        role = str(msg.get("role", "")).lower()
        content = str(msg.get("content", "") or msg.get("text", "") or "")
        if not content:
            continue
        # 过滤纯系统消息
        filtered = filter_noise(content)
        if not filtered:
            continue
        if role in ("user", "human"):
            parsed.append({"role": "user", "content": filtered})
        elif role in ("assistant", "model", "ai"):
            parsed.append({"role": "assistant", "content": filtered})

    if not parsed:
        return None

    # 检查是否有真实的用户消息
    user_msgs = [m for m in parsed if m["role"] == "user"]
    if not user_msgs:
        return None

    # ─── 提取结构化信息 ───
    combined_text = "\n".join(m["content"] for m in parsed)

    # 用户意图
    intent = extract_user_intent(parsed)

    # 助理结论
    conclusions = extract_conclusions(parsed)

    # 分类
    category = classify_content_deep(combined_text, parsed)

    # 话题
    topic = extract_topic(intent, "\n".join(conclusions[:2]))

    # 构建 entry
    conclusion_text = conclusions[0] if conclusions else intent
    background_text = intent if len(intent) > 20 else ""
    detail_points = [c for c in conclusions[1:4] if len(c) > 20]

    # 尝试提取下一步
    next_steps = ""
    next_match = re.search(
        r'(下一步|后续|接下来|follow.?up|next.?step)[:：]?\s*(.+)',
        combined_text, re.I
    )
    if next_match:
        next_steps = next_match.group(2)[:200].strip()
    else:
        next_steps = "- [ ] 待补充"

    entry_data = {
        "conclusion": conclusion_text[:300],
        "background": background_text[:200],
        "details": detail_points,
        "next_steps": next_steps,
        "tags": [category, agent_id],
        "source": f"对话: {session_path.stem}",
    }

    return {
        "agent_id": agent_id,
        "category": category,
        "topic": topic,
        "entry_data": entry_data,
    }


def process_agent(agent_id: str) -> int:
    name = AGENTS.get(agent_id, agent_id)
    sessions_dir = HOME / ".hermes" / "profiles" / agent_id / "sessions"
    if not sessions_dir.exists():
        return 0

    session_files = sorted(
        sessions_dir.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    # 过滤非 session 文件（sessions.json, request_dump_* 等）
    session_files = [
        f for f in session_files
        if f.name.startswith("session_")
    ]

    if not session_files:
        return 0

    # ─── 去重：只处理未同步的 session ───
    # 全量模式：处理所有 session；日常模式：只检查最近 10 个
    full_mode = os.environ.get("SYNC_FULL", "0") == "1"
    pending = []
    max_check = len(session_files) if full_mode else min(10, len(session_files))
    for sf in session_files[:max_check]:
        if not is_already_synced(agent_id, sf):
            pending.append(sf)

    if not pending:
        synced_count = len([f for f in session_files[:max_check] if is_already_synced(agent_id, f)])
        print(f"  {name}: 全部已同步 ({synced_count}/{max_check})")
        return 0

    # ─── 按话题分组合并 ───
    items_by_topic: dict[str, list[dict]] = {}
    for sf in pending:
        result = process_session(sf, agent_id)
        if result is None:
            continue
        key = f"{result['category']}:{result['topic']}"
        items_by_topic.setdefault(key, []).append(result)

    if not items_by_topic:
        return 0

    count = 0
    agent_name = AGENTS.get(agent_id, agent_id)

    for key, topic_items in items_by_topic.items():
        category = key.split(":", 1)[0]
        topic = key.split(":", 1)[1]

        # 合并同话题的多条结论
        all_conclusions = []
        all_details = []
        for item in topic_items:
            ed = item["entry_data"]
            c = ed.get("conclusion", "").strip()
            if c:
                all_conclusions.append(c)
            all_details.extend(ed.get("details", []))
        # 去重
        seen_c = set()
        unique_conclusions = []
        for c in all_conclusions:
            key_c = c[:60]
            if key_c not in seen_c:
                seen_c.add(key_c)
                unique_conclusions.append(c)

        seen_d = set()
        unique_details = []
        for d in all_details:
            key_d = d[:60]
            if key_d not in seen_d:
                seen_d.add(key_d)
                unique_details.append(d)

        # 合并后的 entry_data
        merged = topic_items[0]["entry_data"].copy()
        if len(unique_conclusions) > 1:
            merged["conclusion"] = unique_conclusions[0]
            # 把其他结论放入 details
            for c in unique_conclusions[1:]:
                if c not in unique_details:
                    unique_details.insert(0, f"补充结论：{c}")
        else:
            merged["conclusion"] = unique_conclusions[0] if unique_conclusions else topic
        merged["details"] = unique_details[:8]

        # 写入 Obsidian
        filepath = write_to_obsidian(agent_id, category, topic, merged)
        rel = filepath.relative_to(VAULT)
        already_exists = filepath.exists()
        action = "追加" if (count > 0 or already_exists) else "新建"
        print(f"  ✅ {name} → {rel}（{action}）")

        # 写入 Supermemory
        ok = write_to_supermemory(agent_id, category, topic, merged)
        if ok:
            print(f"     🧠 Supermemory [{SUPERMEMORY_TAGS.get(agent_id, agent_id)}]")
        count += 1

    # 标记所有已处理的 session
    for sf in pending:
        mark_synced(agent_id, sf)

    return count


def main():
    print(f"🔍 实时记忆同步引擎 v5")
    print(f"   Vault: {VAULT}")
    print(f"   分类: {' · '.join(CATEGORIES)}")
    print(f"   格式: 金字塔（结论→背景→核心内容→下一步）")
    print()

    total = 0
    for agent_id in AGENTS:
        count = process_agent(agent_id)
        total += count

    if total == 0:
        print("  ℹ️  没有新的对话需要处理")
    print(f"\n✅ 同步完成，共 {total} 条记忆（v5 规范化模式）")


if __name__ == "__main__":
    main()
