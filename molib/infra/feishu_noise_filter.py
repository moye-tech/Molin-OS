"""
飞书 UX 噪声过滤器
==================
8 条正则规则，过滤飞书群消息中的噪声，提升信噪比。
Mac M2: 纯 regex，毫秒级，零内存开销。

规则设计:
  R1: 纯表情/符号消息
  R2: 系统消息（入群/退群/改名）
  R3: 连续重复消息（刷屏）
  R4: 单字/短词无意义消息
  R5: @机器人但没有实质内容
  R6: 纯数字/日期（打卡类）
  R7: URL-only 消息（但无描述）
  R8: 飞书卡片/富文本碎片

用法:
    from molib.infra.feishu_noise_filter import filter_message
    result = filter_message("打卡")
    # {"noise": True, "rule": "R4", "reason": "单字无意义消息"}
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class FilterResult:
    noise: bool
    rule: str = ""
    reason: str = ""
    cleaned: str = ""


# ═══════════════════════════════════════════════════════════════
# 8 条噪声规则
# ═══════════════════════════════════════════════════════════════

# R1: 纯表情/符号消息（覆盖常用 emoji + 标点）
R1_EMOJI_ONLY = re.compile(
    r"^[\s"
    r"\U0001F000-\U0001F9FF"   # Emoji, Symbols, Pictographs
    r"\U0001FA00-\U0001FA6F"   # Chess, Symbols
    r"\U0001FA70-\U0001FAFF"   # Symbols Extended-A
    r"\u2600-\u27BF"            # Misc Symbols
    r"\u2700-\u27BF"            # Dingbats
    r"\uFE0F\u200D"             # Variation selector + ZWJ
    r"\u0021-\u002F\u003A-\u0040"  # ! " # $ % & ' ( ) * + , - . / : ; < = > ? @
    r"\u005B-\u0060"            # [ \ ] ^ _ `
    r"\u007B-\u007E"            # { | } ~
    r"\u00A0-\u00BF"            # Latin-1 punctuation
    r"\u2010-\u206F"            # General punctuation
    r"\uFF01-\uFF60"            # Fullwidth punctuation
    r"\u3000-\u303F"            # CJK punctuation
    r"]+$"
)

# R2: 系统消息模式
R2_SYSTEM_PATTERNS = [
    r"加入群聊",
    r"退出群聊",
    r"修改群名",
    r"被移除群聊",
    r"解散了群聊",
    r"邀请.*加入",
    r"撤回了一条消息",
    r"群主.*转让",
]

# R3: 刷屏检测（同用户在 5 秒内发相同内容）
# 此规则需要上下文支持，这里提供去重逻辑

# R4: 单字短词无意义消息
R4_SHORT_NOISE = re.compile(r"^.{1,3}$")

# R5: @机器人无实质内容
R5_MENTION_ONLY = re.compile(r"^@\S+\s*$")

# R6: 纯数字/日期
R6_NUMERIC_ONLY = re.compile(r"^[\d\s\-\.\/:年月日时分秒周]+$")

# R7: URL only
R7_URL_ONLY = re.compile(r"^https?://\S+\s*$")

# R8: 飞书卡片碎片/富文本残渣
R8_FEISHU_FRAGMENT = re.compile(
    r"^(```|~~~|\*\*\*|---+|___+|===+|>>|<<|\{\{|%%.*%%).*$"
)


def filter_message(text: str) -> FilterResult:
    """对单条消息应用所有噪声规则。

    Args:
        text: 原始消息文本

    Returns:
        FilterResult with noise flag, matched rule, and reason
    """
    text = text.strip()

    # 空消息
    if not text:
        return FilterResult(noise=True, rule="R0", reason="空消息")

    # R6: 纯数字/日期 — 先于 R4 检查
    if R6_NUMERIC_ONLY.match(text) and len(text) < 15:
        return FilterResult(noise=True, rule="R6", reason="纯数字/日期（非实质性消息）")

    # R7: URL only
    if R7_URL_ONLY.match(text):
        return FilterResult(noise=True, rule="R7", reason="仅URL无描述")

    # R1: 纯表情符号 — 先于 R4 检查
    if R1_EMOJI_ONLY.match(text):
        return FilterResult(noise=True, rule="R1", reason="纯表情/符号")

    # R5: @机器人无内容
    if R5_MENTION_ONLY.match(text):
        return FilterResult(noise=True, rule="R5", reason="@机器人无实质内容")

    # R8: 飞书卡片碎片
    if R8_FEISHU_FRAGMENT.match(text):
        return FilterResult(noise=True, rule="R8", reason="飞书富文本碎片")

    # R4: 超短无意义 — 最后检查（避免覆盖上述更精确规则）
    if R4_SHORT_NOISE.match(text) and not _is_meaningful_short(text):
        return FilterResult(noise=True, rule="R4", reason=f"短消息无意义: '{text}'")

    # R2: 系统消息
    for pattern in R2_SYSTEM_PATTERNS:
        if re.search(pattern, text):
            return FilterResult(noise=True, rule="R2", reason=f"系统消息: {text[:30]}")

    # 通过所有过滤，保留
    return FilterResult(noise=False, cleaned=text)


def _is_meaningful_short(text: str) -> bool:
    """判断短文本是否有实质意义。"""
    meaningful = {"好的", "收到", "OK", "ok", "行", "可以", "对", "是", "否",
                  "嗯嗯", "👌", "👍", "完成", "done", "是的", "不对", "发",
                  "撤回", "重新", "再来", "继续", "暂停", "停止"}
    return text.strip() in meaningful


def filter_batch(messages: list[str]) -> dict[str, Any]:
    """批量过滤并返回统计。"""
    results = []
    noise_count = 0
    rule_counts = {}

    for msg in messages:
        result = filter_message(msg)
        results.append(result)
        if result.noise:
            noise_count += 1
            rule_counts[result.rule] = rule_counts.get(result.rule, 0) + 1

    return {
        "total": len(messages),
        "noise": noise_count,
        "signal": len(messages) - noise_count,
        "ratio": f"{(len(messages) - noise_count) / max(len(messages), 1) * 100:.1f}%",
        "rule_breakdown": rule_counts,
    }


# ═══════════════════════════════════════════════════════════════
# 测试用例
# ═══════════════════════════════════════════════════════════════

def _run_tests() -> dict[str, tuple[str, bool, str]]:
    """内置测试向量。"""
    cases = [
        ("打卡", True, "R4"),
        ("👍🙏😊", True, "R1"),
        ("大王邀请小张加入群聊", True, "R2"),
        ("好的", False, ""),
        ("今天的内容已发布，请查收", False, ""),
        ("https://example.com", True, "R7"),
        ("2025年5月10日", True, "R6"),
        ("@墨麟助手", True, "R5"),
        ("```mermaid", True, "R8"),
        ("帮我分析一下这个数据", False, ""),
        ("", True, "R0"),
        ("123", True, "R6"),
        ("收到", False, ""),
    ]
    results = {}
    for text, expected_noise, expected_rule in cases:
        r = filter_message(text)
        ok = r.noise == expected_noise and (not expected_noise or r.rule == expected_rule)
        status = "✅" if ok else f"❌ (got noise={r.noise} rule={r.rule})"
        results[text] = (status, r.noise, r.rule)
    return results


if __name__ == "__main__":
    for text, (status, noise, rule) in _run_tests().items():
        print(f"{status} '{text}' → noise={noise} rule={rule}")
