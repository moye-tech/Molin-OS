"""
工具风险评分器 (Tool Risk Scorer)
CEO 路由层在执行工具调用前自动查询此模块，根据工具名+命令判断风险级别，
决定是否上报审批、推送飞书卡片或自动放行。
"""
from typing import Optional

# ═══════════════════════════════════════════════════════════════
# 工具风险映射表 — (tool_name, command) → risk_level
# 所有新工具接入时必须在此注册风险级别
# ═══════════════════════════════════════════════════════════════
TOOL_RISK_MAP: dict[tuple[str, str], str] = {
    # ── xiaohongshu-cli / social_hub ──
    ("xiaohongshu_cli", "post_note"):          "HIGH",
    ("xiaohongshu_cli", "monitor_trends"):      "LOW",

    # ── OpenCLI / cli_hub ──
    ("opencli_hub", "run_safe_command"):        "HIGH",

    # ── Lightpanda Browser / web_browser ──
    ("lightpanda_browser", "fetch_page"):       "LOW",
    ("lightpanda_browser", "extract_text"):     "LOW",

    # ── seomachine / market_radar ──
    ("market_radar", "analyze_seo"):            "LOW",
    ("market_radar", "gather_intelligence"):    "LOW",

    # ── Deep-Live-Cam / vision_engine ──
    ("deep_live_cam", "generate_avatar_video"): "HUMAN_REQUIRED",

    # ── GenericAgent / generic_agent ──
    ("generic_agent", "delegate_complex_task"): "MEDIUM",

    # ── agent-skills / agent_skills ──
    ("agent_skills", "invoke_skill"):            "LOW",

    # ── video_tool / MoneyPrinterTurbo ──
    ("video_tool", "generate_video"):            "MEDIUM",
    ("video_tool", "get_status"):                "LOW",

    # ── claw_code_tool / claw-code ──
    ("claw_code_tool", "run_code_review"):       "LOW",
    ("claw_code_tool", "run_refactor"):          "HIGH",

    # ── trading_tool / TradingAgents-CN ──
    ("trading_tool", "analyze_market"):          "LOW",
    ("trading_tool", "execute_order"):           "HUMAN_REQUIRED",
    ("trading_tool", "portfolio_review"):        "LOW",

    # ── pm_skills / phuryn/pm-skills ──
    ("pm_skills", "generate_prd"):               "LOW",
    ("pm_skills", "user_interview"):             "LOW",
    ("pm_skills", "competitive_analysis"):       "LOW",
}

# ═══════════════════════════════════════════════════════════════
# 审批超时策略 — risk_level → 超时秒数
# LOW / MEDIUM: 自动放行（None = 无需等待）
# HIGH:         30 分钟超时，自动取消
# HUMAN_REQUIRED: 永不超时，必须人工确认
# ═══════════════════════════════════════════════════════════════
APPROVAL_TIMEOUTS: dict[str, Optional[int]] = {
    "LOW":              None,           # 自动放行
    "MEDIUM":           None,           # 自动放行 + 飞书通知
    "HIGH":             1800,           # 30 分钟超时
    "HUMAN_REQUIRED":   0,              # 永不自动取消，必须人工
}

# 风险级别显示名称
RISK_LABELS: dict[str, str] = {
    "LOW":              "低风险",
    "MEDIUM":           "中风险",
    "HIGH":             "高风险",
    "HUMAN_REQUIRED":   "强制人工",
}


def get_risk_level(tool_name: str, command: str) -> str:
    """
    查询工具的风险级别。
    未在 TOOL_RISK_MAP 中注册的工具默认返回 MEDIUM。
    """
    return TOOL_RISK_MAP.get((tool_name, command), "MEDIUM")


def get_approval_timeout(risk_level: str) -> Optional[int]:
    """
    获取对应风险级别的审批超时秒数。
    None = 无需审批；0 = 永不超时。
    """
    return APPROVAL_TIMEOUTS.get(risk_level, 1800)


def get_risk_label(risk_level: str) -> str:
    """获取风险级别的中文显示名称"""
    return RISK_LABELS.get(risk_level, risk_level)


def requires_approval(tool_name: str, command: str) -> bool:
    """判断工具调用是否需要人工审批"""
    level = get_risk_level(tool_name, command)
    return level in ("HIGH", "HUMAN_REQUIRED")


def is_auto_released(tool_name: str, command: str) -> bool:
    """判断工具调用是否自动放行（无需审批）"""
    level = get_risk_level(tool_name, command)
    return level in ("LOW", "MEDIUM")
