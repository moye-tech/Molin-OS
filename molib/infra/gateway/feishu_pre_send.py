"""
墨麟OS — 飞书消息预发送自检器 (Pre-Send Validator)

在飞书消息发送前执行程序化检查，拦截 5 类常见输出管线问题：
  P0 — 思考模式前缀泄漏（💭 Reasoning:）
  P1 — Markdown 残留（表格/粗体/代码块）
  P2 — CardRouter 绕过（含表格/多字段/告警时未走 Router）
  P3 — 噪声信息泄漏（终端命令/文件路径/traceback）
  P4 — 长消息截断风险（>1500字未走 doc import）

用法:
    from molib.infra.gateway.feishu_pre_send import validate, quick_check

    result = validate(message, context={})
    if result.clean:
        send(message)          # 可以直接发
    else:
        cleaned = result.cleaned  # 修复后的消息
        if result.needs_doc_import:
            doc_url = import_to_doc(cleaned)
            send(f"📄 完整报告: {doc_url}")
        else:
            send(cleaned)

设计原则:
  - 零外部依赖，纯 stdlib
  - 快速（所有检查在 ms 级完成，无需 LLM 调用）
  - 非破坏性（返回修复建议而非直接修改上游代码）
  - 分层告警（ERROR 拦截 / WARNING 修复 / INFO 记录）
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ═══════════════════════════════════════════════════════════════
# 违规严重级别
# ═══════════════════════════════════════════════════════════════

class Severity(Enum):
    ERROR = "error"       # 必须修复才能发送
    WARNING = "warning"   # 自动修复后发送
    INFO = "info"         # 记录但不拦截


# ═══════════════════════════════════════════════════════════════
# 检测规则集
# ═══════════════════════════════════════════════════════════════

# P0 — 思考模式前缀
THINKING_RE = re.compile(
    # deepseek-v4-pro thinking mode: "💭 Reasoning:..."
    # Three patterns:
    #   1. Multiline with double-newline separator: 💭 Reasoning:\n...\n\n
    #   2. Multiline with content-start on next line: 💭 Reasoning:\n...\n(not whitespace)
    #   3. Single-line compressed: 💭 Reasoning: text. (before emoji response)
    r"^💭\s*Reasoning:.*?(?:\n\n|\n(?=[^\n\s])|(?=\s*[✅⚠️❌📊🚨📋📝📄🔗]))",
    re.DOTALL,
)
THINKING_TAG_RE = re.compile(
    r"\n\n\s*thinking\s*\n\n",  # 孤立  thinking 标签
    re.DOTALL,
)

# P1 — Markdown 残留
MARKDOWN_TABLE_RE = re.compile(r"^\|.+\|.+$", re.MULTILINE)  # 表格行
MARKDOWN_BOLD_RE = re.compile(r"\*\*[^*]+\*\*")               # **粗体**
MARKDOWN_ITALIC_RE = re.compile(r"(?<!\*)\*[^*]+\*(?!\*)")    # *斜体*
MARKDOWN_CODE_RE = re.compile(r"```[\s\S]*?```")              # 代码块
MARKDOWN_INLINE_CODE_RE = re.compile(r"`[^`]+`")              # 行内代码
MARKDOWN_HEADING_RE = re.compile(r"^#{1,6}\s", re.MULTILINE)  # 标题
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")       # 链接
MARKDOWN_HR_RE = re.compile(r"^---+$", re.MULTILINE)          # 水平分割线

# P3 — 噪声信息
NOISE_TERMINAL_RE = re.compile(r"terminal:\s*[\"'].*?[\"']", re.IGNORECASE)
NOISE_PATH_RE = re.compile(r"(?:/tmp/|~\\.cache/|\\.hermes/cache/)")
NOISE_TRACEBACK_RE = re.compile(r"Traceback\s*\(most recent call last\)")
NOISE_FILEREAD_RE = re.compile(r"read_file:\s*[\"'].*?[\"']", re.IGNORECASE)
NOISE_DELEGATE_RE = re.compile(r"delegate_task", re.IGNORECASE)

# P4 — 长度阈值（飞书纯文本约 15000 字节，保守阈值 1500 字）
LENGTH_THRESHOLD = 1500

# 飞书纯文本最大字节数（含 JSON 序列化开销约 300 字节）
FEISHU_TEXT_MAX_BYTES = 29500

# P2 — 需要 CardRouter 的关键词
ROUTER_REQUIRED_KW = {
    "失败", "错误", "异常", "超限", "402", "断连", "预警",
    "审批", "确认发布", "报价", "待审",
    "草稿", "文案", "脚本", "大纲", "预览", "内容已生成", "已就绪",
    "简报", "报表", "统计", "日报", "周报", "产出", "数据汇总", "竞品监控",
}


# ═══════════════════════════════════════════════════════════════
# 违规记录
# ═══════════════════════════════════════════════════════════════

@dataclass
class Violation:
    """单条违规记录"""
    code: str           # 违规代码（P0/P1/P2/P3/P4）
    severity: Severity  # 严重级别
    message: str        # 人类可读描述
    suggestion: str     # 修复建议
    location: str = ""  # 违规位置（行号或片段）


# ═══════════════════════════════════════════════════════════════
# 验证结果
# ═══════════════════════════════════════════════════════════════

@dataclass
class PreSendResult:
    """预发送自检结果"""
    clean: bool = True                  # 全部通过，可直接发送
    original: str = ""                  # 原始消息
    cleaned: str = ""                   # 自动修复后的消息
    violations: list[Violation] = field(default_factory=list)
    needs_thinking_strip: bool = False  # 需要剥离思考前缀
    needs_doc_import: bool = False      # 需要走 doc import
    needs_card_router: bool = False     # 需要走 CardRouter
    suggested_action: str = ""          # 建议操作

    def has_errors(self) -> bool:
        return any(v.severity == Severity.ERROR for v in self.violations)


# ═══════════════════════════════════════════════════════════════
# 核心验证函数
# ═══════════════════════════════════════════════════════════════

def validate(
    message: str,
    context: Optional[dict] = None,
    auto_fix: bool = True,
) -> PreSendResult:
    """对飞书消息执行完整的预发送自检。

    Args:
        message: 待发送的消息文本
        context: 上下文（可选）:
            - card_router_called: bool — 是否已调用 CardRouter
            - governance_level: str — 治理级别
            - is_cron: bool — 是否定时任务
            - field_count: int — 数据字段数
        auto_fix: 是否自动修复可修复的违规

    Returns:
        PreSendResult: 包含违规列表、修复后消息、建议操作
    """
    ctx = context or {}
    violations: list[Violation] = []
    cleaned = message

    # ── P0: 思考模式前缀检查 ──
    thinking_stripped = THINKING_RE.sub("", cleaned)
    thinking_stripped = THINKING_TAG_RE.sub("", thinking_stripped)
    if thinking_stripped != cleaned:
        violations.append(Violation(
            code="P0",
            severity=Severity.WARNING,
            message="检测到思考模式前缀（💭 Reasoning:）",
            suggestion="已自动剥离。根本修复：网关 format_message() 前增加 regex 截断",
        ))
        cleaned = thinking_stripped

    # ── P1: Markdown 残留检查 ──
    md_violations = _check_markdown_residue(cleaned)
    violations.extend(md_violations)

    # ── P2: CardRouter 绕过检查 ──
    if not ctx.get("card_router_called"):
        router_violations = _check_router_bypass(cleaned, ctx)
        violations.extend(router_violations)

    # ── P3: 噪声信息检查 ──
    noise_violations = _check_noise(cleaned)
    violations.extend(noise_violations)

    # ── P4: 长度检查 ──
    length_violations, needs_doc = _check_length(cleaned)
    violations.extend(length_violations)

    # ── 汇总结果 ──
    has_errors = any(v.severity == Severity.ERROR for v in violations)
    needs_thinking = thinking_stripped != message
    needs_router = any(
        v.code == "P2" and v.severity == Severity.ERROR
        for v in violations
    )

    if has_errors:
        action = "BLOCKED — 修复违规后重试"
    elif needs_doc:
        action = "DOC_IMPORT — 消息过长，走 feishu-cli doc import"
    elif needs_router:
        action = "CARD_ROUTER — 需要走 FeishuCardRouter.render()"
    elif needs_thinking:
        action = "STRIPPED — 思考前缀已剥离，可以发送"
    else:
        action = "SEND — 可以直接发送"

    return PreSendResult(
        clean=not has_errors and not needs_doc and not needs_router,
        original=message,
        cleaned=cleaned,
        violations=violations,
        needs_thinking_strip=needs_thinking,
        needs_doc_import=needs_doc,
        needs_card_router=needs_router,
        suggested_action=action,
    )


def quick_check(message: str) -> bool:
    """快速检查消息是否可以直接发送（无违规）。

    用于 cron 等高性能场景，不做完整分析。
    """
    # 检查最严重的违规
    if THINKING_RE.search(message):
        return False
    if NOISE_TRACEBACK_RE.search(message):
        return False
    if len(message) > LENGTH_THRESHOLD:
        return False
    return True


# ═══════════════════════════════════════════════════════════════
# 内部检查函数
# ═══════════════════════════════════════════════════════════════

def _check_markdown_residue(text: str) -> list[Violation]:
    """检查 Markdown 格式残留"""
    violations = []

    if MARKDOWN_TABLE_RE.search(text):
        violations.append(Violation(
            code="P1",
            severity=Severity.ERROR,
            message="检测到 Markdown 表格残留（| col | col |）",
            suggestion="禁止写 Markdown 表格。用 CardBuilder.table() 或 CardRouter.render() 生成原生飞书卡片",
        ))

    if MARKDOWN_CODE_RE.search(text):
        violations.append(Violation(
            code="P1",
            severity=Severity.WARNING,
            message="检测到代码块（```）",
            suggestion="飞书不支持代码块渲染，改用引用或纯文本",
        ))

    if MARKDOWN_HEADING_RE.search(text):
        violations.append(Violation(
            code="P1",
            severity=Severity.WARNING,
            message="检测到 Markdown 标题（# Title）",
            suggestion="用 emoji + 空行分段替代，如「📊 标题名」",
        ))

    if MARKDOWN_HR_RE.search(text):
        violations.append(Violation(
            code="P1",
            severity=Severity.INFO,
            message="检测到 Markdown 水平线（---）",
            suggestion="用 ━━━━ 全角分隔线替代",
        ))

    return violations


def _check_router_bypass(text: str, ctx: dict) -> list[Violation]:
    """检查是否绕过了 CardRouter"""
    violations = []

    # 检查是否包含需要 Router 的关键词
    for kw in ROUTER_REQUIRED_KW:
        if kw in text:
            violations.append(Violation(
                code="P2",
                severity=Severity.ERROR,
                message=f"消息含关键词「{kw}」但未调用 CardRouter",
                suggestion=f"必须调用 FeishuCardRouter.render() 而非裸写文本",
            ))
            break  # 一条就够了

    # 检查是否有 3+ 字段（数据简报场景）
    if ctx.get("field_count", 0) >= 3:
        violations.append(Violation(
            code="P2",
            severity=Severity.ERROR,
            message=f"消息含 {ctx['field_count']} 个数据字段但未调用 CardRouter",
            suggestion="数据简报必须走 FeishuCardRouter.render() → CARD_DATA",
        ))

    return violations


def _check_noise(text: str) -> list[Violation]:
    """检查噪声信息泄漏"""
    violations = []

    if NOISE_TERMINAL_RE.search(text):
        violations.append(Violation(
            code="P3",
            severity=Severity.WARNING,
            message="检测到 terminal 命令原文泄漏",
            suggestion="移除 terminal: 引用，只保留执行结果",
        ))

    if NOISE_PATH_RE.search(text):
        violations.append(Violation(
            code="P3",
            severity=Severity.INFO,
            message="检测到临时文件路径泄漏",
            suggestion="移除 /tmp/、~/.cache/ 等临时路径",
        ))

    if NOISE_TRACEBACK_RE.search(text):
        violations.append(Violation(
            code="P3",
            severity=Severity.ERROR,
            message="检测到 traceback 泄漏",
            suggestion="告警卡片只能用 3 句话（发生什么/影响什么/做什么），禁止堆积 traceback",
        ))

    if NOISE_FILEREAD_RE.search(text):
        violations.append(Violation(
            code="P3",
            severity=Severity.INFO,
            message="检测到 read_file 调用泄漏",
            suggestion="移除工具调用痕迹",
        ))

    if NOISE_DELEGATE_RE.search(text):
        violations.append(Violation(
            code="P3",
            severity=Severity.INFO,
            message="检测到 delegate_task 引用泄漏",
            suggestion="移除内部调度细节",
        ))

    return violations


def _check_length(text: str) -> tuple[list[Violation], bool]:
    """检查消息长度，判断是否需要走 doc import"""
    violations = []
    needs_doc = False

    char_count = len(text)
    byte_count = len(text.encode("utf-8"))

    if char_count > LENGTH_THRESHOLD:
        needs_doc = True
        violations.append(Violation(
            code="P4",
            severity=Severity.ERROR,
            message=f"消息过长（{char_count} 字 > {LENGTH_THRESHOLD} 阈值）",
            suggestion="写入 Markdown 文件 → feishu-cli doc import → 只发文档链接 + 一句话摘要",
        ))

    if byte_count > FEISHU_TEXT_MAX_BYTES:
        needs_doc = True
        violations.append(Violation(
            code="P4",
            severity=Severity.ERROR,
            message=f"消息超过飞书长度限制（{byte_count} bytes > {FEISHU_TEXT_MAX_BYTES}）",
            suggestion="写入 Markdown 文件 → feishu-cli doc import → 只发文档链接 + 一句话摘要",
        ))

    return violations, needs_doc


# ═══════════════════════════════════════════════════════════════
# 带路由的便捷发送函数
# ═══════════════════════════════════════════════════════════════

def send_with_validation(
    message: str,
    chat_id: str,
    context: Optional[dict] = None,
    sender=None,
) -> dict:
    """一站式：验证 → 路由 → 发送。

    如果验证通过，直接发送。
    如果消息过长，自动走 doc import。
    如果违反 CardRouter 规则，强制走 Router。

    Args:
        message: 消息文本
        chat_id: 飞书会话 ID
        context: 上下文（同 validate()）
        sender: FeishuCardSender 实例（可选）

    Returns:
        {"status": "sent"|"doc_imported"|"blocked", "message": str, ...}
    """
    result = validate(message, context)

    if result.has_errors():
        return {
            "status": "blocked",
            "violations": [
                {"code": v.code, "message": v.message, "suggestion": v.suggestion}
                for v in result.violations
                if v.severity == Severity.ERROR
            ],
        }

    # P4: 需要 doc import
    if result.needs_doc_import:
        try:
            from molib.ceo.cards.sender import FeishuCardSender
            s = sender or FeishuCardSender()

            # 写入临时 Markdown 文件
            import tempfile
            from pathlib import Path

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".md", delete=False, encoding="utf-8",
            ) as f:
                f.write(result.cleaned)
                md_path = f.name

            doc_result = s.doc_create(
                title=f"墨麟OS · 长消息 ({_timestamp()})",
                content_path=md_path,
            )

            # 清理临时文件
            Path(md_path).unlink(missing_ok=True)

            doc_url = doc_result.get("url", doc_result.get("data", {}).get("url", ""))
            summary = result.cleaned[:200] + "…"

            return {
                "status": "doc_imported",
                "doc_url": doc_url,
                "summary": summary,
            }
        except Exception as e:
            return {"status": "error", "message": f"doc import 失败: {e}"}

    # P2: 需要 CardRouter
    if result.needs_card_router:
        try:
            from molib.shared.publish.feishu_card_router import FeishuCardRouter
            payload = FeishuCardRouter.render(
                message=result.cleaned,
                ctx=context or {},
            )
            return {
                "status": "routed",
                "format": payload.get("msg_type", "unknown"),
                "payload": payload,
            }
        except Exception as e:
            return {"status": "error", "message": f"CardRouter 失败: {e}"}

    # 可以直接发送
    return {
        "status": "send_ready",
        "message": result.cleaned,
    }


def _timestamp() -> str:
    from datetime import datetime
    return datetime.now().strftime("%m-%d %H:%M")


# ═══════════════════════════════════════════════════════════════
# 命令行接口
# ═══════════════════════════════════════════════════════════════

def main():
    """CLI 入口：python -m molib validate <message>"""
    import sys

    if len(sys.argv) < 2:
        print("用法: python -m molib validate <message>")
        sys.exit(1)

    message = " ".join(sys.argv[1:])
    result = validate(message)

    print(f"结果: {'✅ 通过' if result.clean else '❌ 未通过'}")
    print(f"建议: {result.suggested_action}")
    print(f"违规数: {len(result.violations)}")

    for v in result.violations:
        sev = "🔴" if v.severity == Severity.ERROR else "🟡" if v.severity == Severity.WARNING else "🔵"
        print(f"  {sev} [{v.code}] {v.message}")
        print(f"      → {v.suggestion}")

    if result.needs_thinking_strip:
        print(f"\n修复后消息:\n{result.cleaned[:200]}...")


if __name__ == "__main__":
    main()
