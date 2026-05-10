"""
墨麟AIOS 飞书UX噪声过滤器 — FeishuNoiseFilter
==============================================

在飞书（Lark）对话中，AI 输出常夹带终端命令原文、文件路径、
验证步骤、元数据、冗余说明等"开发噪声"。本模块提供 8 条正则
规则对输出进行清洗，确保推送给用户的消息干净、可读、专业。

规则列表：
  R1  终端命令原文          匹配 $ ... / > ... 等多行命令块
  R2  文件路径              匹配 /absolute/path/* 及 ./relative/path
  R3  中间验证步骤          匹配 "验证..."/"检查中..."/"Step N:"
  R4  技术元数据            匹配 "HTTP/1.1 200"/"Content-Type:"/"Status Code:"
  R5  冗余说明              匹配 "(注意:...)"快捷提示等括号冗余
  R6  临时路径              匹配 /tmp/... /var/folders/... 等系统临时目录
  R7  系统标注              匹配 "[INFO]"/"[WARN]"/"[DEBUG]" 及日志时间戳
  R8  多余空行              将连续 3+ 空行压缩为 2 空行

使用：
    from molib.shared.publish.feishu_noise_filter import clean_output

    raw = get_ai_output()
    cleaned = clean_output(raw)           # 一站式过滤
    # 或
    ok = is_clean(text)                   # 快速检查
    filtered = filter_noise(text)         # 仅执行规则

依赖：纯 Python 标准库，零外部依赖。
"""

from __future__ import annotations

import re
from typing import List, Tuple


# ═══════════════════════════════════════════════════════════════
# 8 条正则规则（名称 + 正则 + 替换内容）
# ═══════════════════════════════════════════════════════════════

_RULES: List[Tuple[str, str, str]] = [
    # R1: 终端命令原文 — $ / > 开头的命令块
    (
        "R1_command_block",
        # 匹配 $ 或 > 开头的命令行，及其后续输出行
        r"(?:^|\n)[$>]\s+[^\n]+(?:\n(?:[^\n]*[#$>]?\s*[^\n]*)){0,5}",
        "",
    ),

    # R2: 文件/目录路径 — 绝对路径与相对路径
    (
        "R2_file_paths",
        # 匹配 /absolute/path 或 ./relative/path
        r"(?:^|\s)(?:/[\w./\-]+|\./[\w./\-]+)(?:\s|$)",
        "",
    ),

    # R3: 中间验证步骤 — "验证..." / "Step N:" / "检查中..."
    (
        "R3_verification_steps",
        r"(?:^|\n)\s*(?:验证|检查|确认|校验|检测)(?:中|完成|通过|失败)?[：:]\s*[^\n]*\n?",
        "",
    ),

    # R4: 技术元数据 — HTTP 状态码、Content-Type、响应头等
    (
        "R4_tech_metadata",
        r"(?:^|\n)\s*(?:HTTP/\d\.\d\s+\d{3}|Content-Type:|Status\s*Code:|X-\w+:)\s*[^\n]*\n?",
        "",
    ),

    # R5: 冗余说明 — "(注意: ...)" "(提示: ...)" 括号冗余
    (
        "R5_redundant_notes",
        r"[(（]\s*(?:注意|提示|备注|说明|提醒)[：:]\s*[^)）]*[)）]",
        "",
    ),

    # R6: 临时路径 — /tmp/, /var/folders/, /private/var/ 等
    (
        "R6_temp_paths",
        r"(?:^|\s)(?:/tmp/|/var/folders/|/private/var/|/dev/shm/)[\w./\-]*",
        "",
    ),

    # R7: 系统日志标注 — [INFO] [WARN] [DEBUG] [ERROR] 及时间戳
    (
        "R7_sys_annotations",
        r"(?:^|\n)\s*\[(?:INFO|WARN|DEBUG|ERROR|TRACE)\]\s*[^\n]*\n?"
        r"|\d{4}[-/]\d{2}[-/]\d{2}\s+\d{2}:\d{2}:\d{2}[.,]\d{3}\s+\[[^\]]+\]\s+[^\n]*",
        "",
    ),

    # R8: 多余空行 — 3+ 连续空行压缩为 2 个
    (
        "R8_excess_blank_lines",
        r"\n{3,}",
        "\n\n",
    ),
]


# ═══════════════════════════════════════════════════════════════
# 公共 API
# ═══════════════════════════════════════════════════════════════

def filter_noise(text: str) -> str:
    """对文本依次应用 8 条正则规则进行噪声过滤。

    规则按 R1 → R8 顺序执行，每条规则会对文本做一次替换。
    注意：过滤是"有损"的，可能移除部分正常内容（尤其在规则边界模糊时）。
    建议先用 is_clean() 检查，或对重要内容保留原始副本。

    Args:
        text: 待过滤的原始文本

    Returns:
        过滤后的干净文本
    """
    result = text
    for name, pattern, replacement in _RULES:
        try:
            before = len(result)
            result = re.sub(pattern, replacement, result, flags=re.MULTILINE)
            after = len(result)
            if before != after:
                pass  # 调试时可开启: logger.debug("%s: removed %d chars", name, before - after)
        except re.error:
            # 规则异常不应中断整个过滤流程
            continue
    return result.strip()


def is_clean(text: str) -> bool:
    """检查文本是否已通过全部过滤规则（即无噪声可滤除）。

    对每条规则分别应用，若任一条匹配到内容则返回 False。

    Args:
        text: 待检查的文本

    Returns:
        True 表示文本干净，无需过滤；False 表示存在噪声
    """
    for name, pattern, _replacement in _RULES:
        try:
            if re.search(pattern, text, flags=re.MULTILINE):
                return False
        except re.error:
            continue
    return True


def clean_output(text: str) -> str:
    """一站式过滤：先检查，若干净则直接返回原文本，否则执行 filter_noise()。

    与直接调用 filter_noise() 的区别：
    - 文本已干净时避免不必要的正则替换，节省 CPU
    - 保留原始文本的精确性（过滤可能导致轻微失真）

    Args:
        text: 待清理的原始文本

    Returns:
        清理后的文本（若原文本干净则直接返回原文）
    """
    if not text:
        return text
    if is_clean(text):
        return text
    return filter_noise(text)
