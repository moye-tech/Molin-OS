"""
墨麟OS — 飞书输出网关

提供完整的飞书消息发送管线：
  1. feishu_pre_send — 预发送自检器（5 类违规检测）
  2. feishu_output_enforcer — 强制执行器（路由+验证+降级）
  3. feishu_reply_pipeline — 3 消息有序回复流水线
  4. feishu_card_builder — 互动卡片构建器
"""

from molib.infra.gateway.feishu_pre_send import (
    validate,
    quick_check,
    PreSendResult,
    Violation,
    Severity,
)

from molib.infra.gateway.feishu_output_enforcer import (
    FeishuOutputEnforcer,
    create_enforcer,
    send_safe,
)

__all__ = [
    # Pre-send validator
    "validate",
    "quick_check",
    "PreSendResult",
    "Violation",
    "Severity",
    # Output enforcer
    "FeishuOutputEnforcer",
    "create_enforcer",
    "send_safe",
]
