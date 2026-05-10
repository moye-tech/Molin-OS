"""
CEO 结果合成器
将多子公司的原始输出合成为自然语言摘要，
解决"原始 Markdown dump"问题的核心修复。
"""

import re
from typing import Dict, Any, List, Optional
from loguru import logger


SYNTHESIZE_SYSTEM = """你是墨麟AI系统的CEO（Hermes），你刚刚派发了一批任务给各子公司，
他们已经完成执行。现在你需要把多个子公司的执行结果整合成一个
简洁、专业、有价值的回复给老板（墨烨）。

【合成原则】
1. 老板最关心"结果是什么"，不是"过程是什么"
2. 用一句话总结核心结论，然后分点展开关键信息
3. 如果多个子公司说了同一件事，整合成一条，不要重复
4. 删除所有"好的，我已收到任务..."这类客套开头
5. 删除所有"综合以上..."这类总结套话
6. 保留数字、具体建议、可行动的步骤
7. 长度：200-400字（不要太短没价值，不要太长让人读不完）
8. 格式：用飞书 lark_md 格式，但不要用 ### 标题（用加粗替代），不要用 --- 分隔线
9. 如果内容里有具体的策略/数字/数据，必须保留

【禁止出现的内容】
- "好的，我来帮您..."
- "以下是...的分析报告"
- "综合以上各方面"
- "作为CEO/Manager..."
- 原始 Markdown 的 ### / --- / > 引用
"""

SYNTHESIZE_PROMPT_TEMPLATE = """老板的原始需求：
{user_input}

各子公司执行结果：
{agency_outputs}

请合成一个自然、专业的回复给老板。直接说结果，不要废话。"""


def _clean_agency_output(output: str, max_len: int = 800) -> str:
    """清理单个子公司输出，去掉套话和无意义的开头"""
    if not output:
        return ""

    # 去掉常见的开头客套话
    patterns_to_remove = [
        r'^好的[，,。].*?(?:以下|现在|我来|我将|我已|我为您)[^\n]*\n',
        r'^作为.*?Manager[，,，][^\n]*\n',
        r'^遵照您的指示.*?\n',
        r'^已收到任务.*?\n',
        r'^您好[，,，].*?\n',
    ]
    for p in patterns_to_remove:
        output = re.sub(p, '', output, flags=re.MULTILINE | re.DOTALL)

    # 去掉结尾的"如需进一步..."类收尾
    output = re.sub(r'\n*如.*?请.*?随时.*?$', '', output, flags=re.DOTALL)
    output = re.sub(r'\n*如有.*?告知.*?$', '', output, flags=re.DOTALL)

    output = output.strip()
    if len(output) > max_len:
        output = output[:max_len] + "…（详见完整报告）"
    return output


async def synthesize_results(
    user_input: str,
    execution_result: Dict[str, Any],
    model_router,
    understanding: str = "",
) -> str:
    """
    调用 LLM 将多子公司结果合成为自然语言摘要。
    这是解决"raw markdown dump"的核心函数。

    Returns:
        str: 已清理、可直接放入飞书卡片的 lark_md 格式文本
    """
    results = execution_result.get("results", [])
    if not results:
        return "任务已执行完成。"

    # 构建子公司输出摘要
    agency_output_blocks = []
    has_real_content = False

    for r in results:
        if not isinstance(r, dict):
            continue
        agency = r.get("agency", "unknown")
        status = r.get("status", "")
        output = r.get("output", "")
        error = r.get("error", "")

        if status == "pending_approval":
            agency_output_blocks.append(f"[{agency}] 已提交审批，等待确认")
        elif status in ("executed", "llm_executed", "success", "completed") and output:
            cleaned = _clean_agency_output(output)
            if cleaned:
                agency_output_blocks.append(f"[{agency}] {cleaned}")
                has_real_content = True
        elif status == "error":
            agency_output_blocks.append(f"[{agency}] 执行失败: {error[:100]}")

    if not has_real_content:
        return "各子公司已接收任务并开始执行，详细结果将在执行完成后汇报。"

    combined = "\n\n".join(agency_output_blocks)

    # 如果内容很短，不需要 LLM 合成，直接返回
    total_len = sum(len(b) for b in agency_output_blocks)
    if total_len < 300 and len(agency_output_blocks) == 1:
        return _strip_for_feishu(agency_output_blocks[0].split("] ", 1)[-1])

    prompt = SYNTHESIZE_PROMPT_TEMPLATE.format(
        user_input=user_input[:200],
        agency_outputs=combined[:3000],
    )

    try:
        result = await model_router.call_async(
            prompt=prompt,
            system=SYNTHESIZE_SYSTEM,
            task_type="synthesis",
        )
        synthesized = result.get("text", "").strip()
        if synthesized and len(synthesized) > 20:
            return _strip_for_feishu(synthesized)
    except Exception as e:
        logger.warning(f"合成器 LLM 调用失败，回退到拼接模式: {e}")

    # 降级：直接拼接清理后的输出
    fallback_parts = []
    if understanding:
        pass  # understanding 在卡片头部显示，不重复
    for block in agency_output_blocks:
        parts = block.split("] ", 1)
        if len(parts) > 1:
            fallback_parts.append(parts[1])
    return _strip_for_feishu("\n\n".join(fallback_parts[:3]))


def _strip_for_feishu(text: str) -> str:
    """最终清理：确保文本符合飞书 lark_md 规范"""
    if not text:
        return ""
    # ### 标题 → 加粗
    text = re.sub(r'^#{1,6}\s*(.+)$', r'**\1**', text, flags=re.MULTILINE)
    # --- 分隔线 → 去掉
    text = re.sub(r'^[-=]{3,}$', '', text, flags=re.MULTILINE)
    # > 引用 → 普通文字
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    # 多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()
