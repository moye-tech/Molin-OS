"""
墨域OS — 飞书消息输出格式化层
噪声过滤 + 结构化卡片 + 分级透明。

每次发给用户的消息经过此层处理：
1. 过滤技术噪声（terminal命令、文件路径、中间步骤）
2. 结构化输出为分隔线卡片格式
3. 分级标注（L0自动完成 / L2待审批）
"""

import re
from typing import Optional


# ── 噪声模式 ──────────────────────────────────────────────────────
NOISE_PATTERNS = [
    # terminal 命令
    r"terminal\([^)]*\)",
    r"```(?:bash|shell|sh)\s*\n.*?\n```",
    # 工具调用痕迹
    r"read_file\([^)]*\)",
    r"write_file\([^)]*\)",
    r"patch\([^)]*\)",
    r"search_files\([^)]*\)",
    r"execute_code\([^)]*\)",
    r"delegate_task\([^)]*\)",
    r"browser_.*?\([^)]*\)",
    # 临时路径
    r"/tmp/[^\s,)\]]+",
    r"~/?\.hermes/[^\s,)\]]+",
    # Hermes 内部状态
    r"\[\d+/\d+\] Running .*",
    r"📝 Task List.*?(?=\n\n|\Z)",
    r"📝 Updated Task.*?(?=\n\n|\Z)",
    # 幻觉标注
    r"\(已编辑\)",
    r"\[Edited\]",
    # 冗余前言
    r"^(让我来|让我先|让我看看|我来检查|我来验证|让我验证|让我确认).*?(?=\n)",
    r"^(首先|好的，我来|好的，先|先让我|我们来).*?(?=\n)",
    # 中间验证步骤
    r"来验证一下.*?(?=\n)",
    r"验证一下.*?(?=\n)",
    r"检查.*?是否正常.*?(?=\n)",
    r"确认.*?成功.*?(?=\n)",
    # 技术名词噪音
    r"iteration \d+/\d+",
    r"running: delegate_task",
    r"status: \w+",
]


def strip_noise(text: str) -> str:
    """过滤所有技术噪声"""
    for pattern in NOISE_PATTERNS:
        text = re.sub(pattern, "", text)
    # 清理多余的空行
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"^\s*\n", "", text, flags=re.MULTILINE)
    return text.strip()


def format_card(title: str, fields: list = None, items: list = None,
                status: str = "✅", level: str = "L0",
                error: str = None, action: str = None) -> str:
    """
    生成结构化卡片。

    Args:
        title: 卡片标题（如"CEO配置修复"）
        fields: 键值对列表 [("字段名", "值"), ...]
        items: 要点列表 ["要点1", "要点2", ...]
        status: 状态表情 ✅ ❌ 🔔
        level: 审批级别 L0/L1/L2/L3
        error: 错误信息（可选）
        action: 需要用户做的事（可选）

    Returns:
        str: 格式化后的卡片文本
    """
    parts = []
    parts.append("━" * 20)

    # 标题行
    level_tag = ""
    if level == "L2":
        level_tag = " · 待你审批"
    elif level == "L3":
        level_tag = " · 需董事会决策"

    parts.append(f"  {status} {title}{level_tag}")
    parts.append("━" * 20)
    parts.append("")

    # 键值字段
    if fields:
        for name, value in fields:
            parts.append(f"· {name}：{value}")
        parts.append("")

    # 要点列表
    if items:
        for item in items:
            parts.append(f"· {item}")
        parts.append("")

    # 错误信息
    if error:
        parts.append(f"⚠️ 错误：{error}")
        parts.append("")

    # 操作提示
    if action:
        parts.append(f"⚡ 操作：{action}")

    parts.append("━" * 20)

    return "\n".join(parts)


def format_error(title: str, reason: str) -> str:
    """生成错误卡片"""
    return format_card(
        title=title,
        status="❌",
        error=reason,
        action="重试 / 查看详情",
    )


def format_approval(title: str, fields: list = None, items: list = None,
                    action: str = "批准 / 拒绝 / 修改方案") -> str:
    """生成审批卡片（L2+）"""
    return format_card(
        title=title,
        fields=fields,
        items=items,
        status="🔔",
        level="L2",
        action=action,
    )


def format_section_header(emoji: str, title: str) -> str:
    """生成简洁的分隔标题"""
    return f"\n{emoji} **{title}**"


def clean_response(text: str) -> str:
    """
    完整的输出清洗流程：
    1. 噪声过滤
    2. 空行压缩
    3. 确保以卡片格式结尾
    """
    text = strip_noise(text)
    # 如果内容太少没必要加卡片
    if len(text) < 20:
        return text
    return text


__all__ = [
    "strip_noise", "format_card", "format_error",
    "format_approval", "format_section_header", "clean_response",
]
