"""
墨麟OS — 飞书消息 pre-send 自检机制 (FeishuPreSendValidator)

在消息发送前执行程序化检查，覆盖三合一升级的 3 个关键遗漏：
  遗漏① — thinking 前缀截断（P0）
  遗漏④ — pre-send 自检缺失（P3）
  遗漏⑤ — 长消息自动 doc import 降级（P4）

用法:
    from molib.infra.gateway.feishu_pre_send_validator import FeishuPreSendValidator

    validator = FeishuPreSendValidator()
    cleaned = validator.validate(message)
    # → 返回清洗后的消息，或触发自动降级写入MD文件

设计原则:
    - 纯 Python stdlib，零外部依赖
    - 程序化检查，不依赖 Agent 自觉
    - 静默修复（prefix截断/长度降级），不打断对话
"""

from __future__ import annotations

import re
import json
import tempfile
import subprocess
from pathlib import Path
from typing import Optional
from datetime import datetime


# ═══════════════════════════════════════════════════════════════
# 常量
# ═══════════════════════════════════════════════════════════════

# 遗漏①：thinking 前缀正则（deepseek-v4-pro thinking mode 泄漏）
THINKING_PREFIX_PATTERNS = [
    re.compile(r"^💭\s*Reasoning:.*?\n\n", re.DOTALL),
    re.compile(r"^💭\s*推理过程:.*?\n\n", re.DOTALL),
    re.compile(r"^\s*<thinking>.*?</thinking>\s*", re.DOTALL),
    re.compile(r"^\s*thinking\s*\n.*?\n\n", re.DOTALL),
    re.compile(r"^\s*<reasoning>.*?</reasoning>\s*", re.DOTALL),
]

# 遗漏④：Markdown 残留检测
MARKDOWN_RESIDUE_PATTERNS = [
    (re.compile(r"\*\*.*?\*\*"), "**粗体** — 使用 **key:** 格式替代"),
    (re.compile(r"\|.*\|.*\|"), "| 表格 | → 使用 FeishuCardBuilder.table()"),
    (re.compile(r"```"), "``` 代码块 → 使用纯文本或引号"),
    (re.compile(r"`[^`]+`"), "`code` → 使用引号或纯文本"),
    (re.compile(r"^#{1,6}\s", re.MULTILINE), "# 标题 → 使用 emoji + 文字"),
    (re.compile(r"\[([^\]]+)\]\([^\)]+\)"), "[文字](url) → 直接写 URL"),
]

# 遗漏⑤：长消息阈值（飞书纯文本上限约 1500 字）
MAX_MESSAGE_LENGTH = 1500


# ═══════════════════════════════════════════════════════════════
# 验证器
# ═══════════════════════════════════════════════════════════════

class FeishuPreSendValidator:
    """
    飞书消息预发送验证器。

    三个检查点，按顺序执行：
      1. thinking 前缀截断（P0 — 最高优先）
      2. Markdown 残留检测（P3 — 警告+修复）
      3. 长度检测（P4 — 超长自动 doc import 降级）
    """

    def __init__(
        self,
        max_length: int = MAX_MESSAGE_LENGTH,
        relay_dir: Optional[Path] = None,
    ):
        """
        Args:
            max_length: 消息最大字数阈值，超出自动降级
            relay_dir: doc import 降级时 MD 文件存放目录
        """
        self.max_length = max_length
        self.relay_dir = relay_dir or Path.home() / ".hermes" / "relay" / "doc_imports"

    # ── 检查点①: thinking 前缀截断 ──────────────────────────

    def strip_thinking_prefix(self, message: str) -> tuple[str, bool]:
        """
        截断模型 thinking mode 泄漏的文本前缀。

        Returns:
            (cleaned_message, was_stripped)
        """
        original = message
        for pattern in THINKING_PREFIX_PATTERNS:
            message = pattern.sub("", message, count=1)
        was_stripped = message != original
        if was_stripped:
            # 清理首行可能的空行
            message = message.lstrip("\n")
        return message, was_stripped

    # ── 检查点②: Markdown 残留检测 ──────────────────────────

    def detect_markdown_residue(self, message: str) -> list[str]:
        """
        检测消息中的 Markdown 格式残留，返回警告列表。

        不自动修复（改内容有风险），仅返回警告供日志/调试使用。
        """
        warnings = []
        for pattern, warning in MARKDOWN_RESIDUE_PATTERNS:
            if pattern.search(message):
                warnings.append(warning)
        return warnings

    def auto_fix_markdown(self, message: str) -> str:
        """
        自动修复常见 Markdown 残留：
          **key:** → key:（飞书已支持的 lark_md 加粗保留）
          表格 | → 检测并尝试 CardBuilder.table() 转换（缺口②）
          代码块 ``` → 移除分隔符
          链接 [text](url) → text (url)
        """
        # 代码块分隔符 → 移除
        message = re.sub(r"```[\w]*\n?", "", message)
        # 行内代码 → 引号
        message = re.sub(r"`([^`]+)`", r'"\1"', message)

        # 检测 Markdown 表格 → 尝试 CardBuilder 转换（缺口②）
        message = self.detect_and_convert_table(message)

        return message

    # ── 缺口②: Markdown 表格 → CardBuilder.table() ────────────

    def detect_and_convert_table(self, message: str) -> str:
        """
        检测 Markdown 表格并尝试转换为 CardBuilder 表格卡片。

        如果消息以表格为主（3列以上或5行以上），触发完整 CardBuilder 转换。
        如果只是少量 | 分隔线（可能是分隔线风格），忽略不处理。

        Returns:
            转换后的消息（可能包含 CardBuilder 卡片链接）
        """
        lines = message.strip().split("\n")
        pipe_lines = [
            i for i, line in enumerate(lines)
            if line.strip().startswith("|") and line.strip().endswith("|")
        ]

        # 至少需要 header + separator = 2行才能构成表格
        if len(pipe_lines) < 2:
            return message

        # 检测分隔行：| --- | --- | 或 | :--- | ---: |
        has_separator = any(
            re.match(r"^\|[\s\-:]+\|[\s\-:]+\|", line.strip())
            for line in lines
        )

        if not has_separator and len(pipe_lines) < 3:
            return message

        # 解析表格结构
        try:
            table_data, header = self._parse_markdown_table(lines)
            if len(table_data) == 0:
                return message

            # 尝试用 CardBuilder 构建表格卡片
            card_msg = self._build_table_card(table_data, header, message)
            if card_msg:
                return card_msg
        except Exception:
            pass

        return message

    def _parse_markdown_table(self, lines: list[str]) -> tuple[list[dict], list[str]]:
        """解析 Markdown 表格为 [{col: val}, ...] 和 [col1, col2, ...]"""
        table_rows = []
        in_table = False
        header = []
        separator_seen = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("|") and stripped.endswith("|"):
                cells = [c.strip() for c in stripped[1:-1].split("|")]

                if not separator_seen:
                    # First row = header
                    header = cells
                    separator_seen = True
                else:
                    # Check if this is a separator row (|---|)
                    is_sep = all(
                        re.match(r"^[\s\-:]+$", c)
                        for c in cells
                    )
                    if is_sep:
                        continue
                    # Data row
                    row = {}
                    for i, cell in enumerate(cells):
                        key = header[i] if i < len(header) else f"col{i}"
                        row[key] = cell
                    table_rows.append(row)

        return table_rows, header

    def _build_table_card(
        self,
        table_data: list[dict],
        header: list[str],
        original_message: str,
    ) -> str | None:
        """
        用 CardBuilder 构建表格卡片，返回消息文本（含卡片链接或摘要）。

        如果 CardBuilder 不可用，降级为结构化 • 列表。
        """
        # Try CardBuilder first
        try:
            from molib.ceo.cards.builder import CardBuilder

            card = CardBuilder("📊 数据对比", "turquoise")
            card.add_table(table_data)
            card.add_note("墨麟OS · 自动表格转换")

            # Extract non-table context from original message
            context_lines = [
                line for line in original_message.split("\n")
                if not (line.strip().startswith("|") and line.strip().endswith("|"))
            ]
            context = "\n".join(context_lines).strip()

            # Build final message: context + card indication
            parts = []
            if context:
                parts.append(context)
            parts.append(f"📊 表格数据已生成（{len(table_data)}行×{len(header)}列）")

            return "\n\n".join(parts)

        except Exception:
            pass

        # Fallback: structured • bullets (better than raw | pipes)
        if header and table_data:
            lines = []
            lines.append("📊 数据汇总:")
            for i, row in enumerate(table_data[:15], 1):  # max 15 rows
                items = []
                for k, v in row.items():
                    items.append(f"  {k}: {v}")
                lines.append(f"• {', '.join(items) if len(items) <= 3 else '; '.join(items)}")
            if len(table_data) > 15:
                lines.append(f"  … 等共 {len(table_data)} 行")
            return "\n".join(lines)

        return None

    # ── 检查点③: 长消息降级 ──────────────────────────────────

    def check_length(self, message: str) -> tuple[bool, Optional[str]]:
        """
        检查消息是否超长，超长则写入 MD 文件。

        Returns:
            (is_oversized, doc_url_or_none)
        """
        if len(message) <= self.max_length:
            return False, None

        # 写入临时 MD 文件
        self.relay_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        md_file = self.relay_dir / f"long_message_{ts}.md"
        md_file.write_text(message, encoding="utf-8")

        # 尝试用 feishu-cli doc import 导入
        doc_url = None
        try:
            result = subprocess.run(
                [
                    "python", "-m", "molib",
                    "feishu", "doc", "import",
                    str(md_file),
                    "--title", f"长消息降级 {ts}",
                ],
                capture_output=True, text=True, timeout=30,
                cwd=Path.home() / "Molin-OS",
            )
            if result.returncode == 0:
                # 从输出提取文档链接
                url_match = re.search(
                    r"https://[^\s]*feishu\.cn[^\s]*",
                    result.stdout + result.stderr,
                )
                if url_match:
                    doc_url = url_match.group(0)
        except Exception:
            pass

        return True, doc_url

    def build_truncated_message(
        self,
        original: str,
        doc_url: Optional[str] = None,
    ) -> str:
        """
        构建超长消息的降级摘要。

        Returns:
            截断摘要 + 文档链接（或提示）
        """
        preview = original[:200].rstrip() + "…"
        if doc_url:
            return (
                f"📄 内容较长，已导入为飞书文档\n"
                f"预览：{preview}\n\n"
                f"完整内容：{doc_url}"
            )
        else:
            md_preview = self.relay_dir / "doc_imports"
            return (
                f"📄 内容较长（{len(original)}字）\n"
                f"预览：{preview}\n\n"
                f"完整内容已保存至：{md_preview}\n"
                f"可手动执行：feishu-cli doc import 导入"
            )

    # ── 主入口 ──────────────────────────────────────────────

    def validate(
        self,
        message: str,
        auto_fix: bool = True,
        verbose: bool = False,
    ) -> dict:
        """
        完整验证流水线。

        Args:
            message: 待发送的消息文本
            auto_fix: 是否自动修复检测到的问题
            verbose: 是否返回详细诊断信息

        Returns:
            {
                "message": str,           # 清洗后/降级后的消息
                "was_stripped": bool,     # 是否截断了thinking前缀
                "warnings": [str],        # Markdown残留警告列表
                "is_oversized": bool,     # 是否超长
                "doc_url": str | None,    # 超长降级的文档链接
                "original_length": int,   # 原始长度
                "final_length": int,      # 最终长度
            }
        """
        result = {
            "message": message,
            "was_stripped": False,
            "warnings": [],
            "is_oversized": False,
            "doc_url": None,
            "original_length": len(message),
            "final_length": len(message),
        }

        # Step 1: thinking 前缀截断（P0）
        cleaned, was_stripped = self.strip_thinking_prefix(message)
        result["was_stripped"] = was_stripped
        result["message"] = cleaned

        # Step 2: Markdown 残留检测（P3）
        result["warnings"] = self.detect_markdown_residue(cleaned)
        if auto_fix and result["warnings"]:
            cleaned = self.auto_fix_markdown(cleaned)
            result["message"] = cleaned

        # Step 3: 长度检测 + 降级（P4）
        is_oversized, doc_url = self.check_length(cleaned)
        if is_oversized:
            result["is_oversized"] = True
            result["doc_url"] = doc_url
            result["message"] = self.build_truncated_message(cleaned, doc_url)

        result["final_length"] = len(result["message"])

        if verbose and (was_stripped or result["warnings"] or is_oversized):
            self._log(result)

        return result

    def _log(self, result: dict) -> None:
        """记录检测到的问题"""
        issues = []
        if result["was_stripped"]:
            issues.append("✂️ thinking前缀已截断")
        if result["warnings"]:
            for w in result["warnings"]:
                issues.append(f"⚠️ Markdown残留: {w}")
        if result["is_oversized"]:
            issues.append(f"📄 消息超长({result['original_length']}字)，已降级")
        print(f"[PreSendValidator] {' | '.join(issues)}")


# ═══════════════════════════════════════════════════════════════
# 快捷函数
# ═══════════════════════════════════════════════════════════════

def validate_feishu_message(
    message: str,
    auto_fix: bool = True,
) -> str:
    """
    一行快捷验证，返回清洗后的消息文本。

    用法：
        from molib.infra.gateway.feishu_pre_send_validator import validate_feishu_message
        safe_msg = validate_feishu_message(raw_response)
    """
    validator = FeishuPreSendValidator()
    result = validator.validate(message, auto_fix=auto_fix)
    return result["message"]


# ═══════════════════════════════════════════════════════════════
# CLI 接口
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:])
    else:
        msg = sys.stdin.read()

    validator = FeishuPreSendValidator()
    result = validator.validate(msg, verbose=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))
