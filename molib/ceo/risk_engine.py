"""
墨域OS — L1 CEO风险引擎
=========================
对意图分析结果进行4类风险评估：
1. 资金风险 (Financial)
2. 合规风险 (Compliance)
3. 法律风险 (Legal)
4. 隐私风险 (Privacy)

评分规则：
- score > 80 → 直接拒绝
- score > 60 → 需要Plan Mode审批
- score ≤ 60 → 自动放行
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("molin.ceo.risk_engine")


@dataclass
class RiskAssessment:
    """风险评估结果"""
    risk_score: float  # 0-100，综合风险评分
    requires_approval: bool  # 是否需要审批
    flags: list[dict] = field(default_factory=list)  # 触发的风险标记列表
    reason: str = ""  # 综合说明
    financial_risk: float = 0.0
    compliance_risk: float = 0.0
    legal_risk: float = 0.0
    privacy_risk: float = 0.0


# ── 各维度风险模式 ──────────────────────────────────────────────────

FINANCIAL_PATTERNS: list[tuple[str, float, str]] = [
    (r"转账\s*\d+[万亿千万百万]?", 30.0, "大额转账操作"),
    (r"投资\s*\d+[万亿千万百万]?", 35.0, "大额投资决策"),
    (r"融资.*\d+[万亿千万百万]?", 40.0, "融资活动"),
    (r"预算.*(调整|追加|变更)", 25.0, "预算变更"),
    (r"单价?[超额超限]?\d+[万亿千万百万]?", 20.0, "大额采购"),
    (r"资金.*(调拨|挪用|转移)", 50.0, "资金调拨"),
    (r"汇率|外汇|换汇", 30.0, "外汇操作"),
    (r"财务.*(报告|报表).*(审计|核查)", 15.0, "财务审计"),
    (r"成本.*(削减|优化|降低).*\d+%", 10.0, "大幅度成本削减"),
    (r"抵押|担保|借贷|贷款", 45.0, "借贷担保"),
]

COMPLIANCE_PATTERNS: list[tuple[str, float, str]] = [
    (r"资质|许可证|牌照|备案", 30.0, "资质许可相关"),
    (r"税务|纳税|发票.*(合规|审核)", 30.0, "税务合规"),
    (r"进出口|报关|海关", 35.0, "进出口合规"),
    (r"反洗钱|AML|KYC", 50.0, "反洗钱/实名合规"),
    (r"行业.*(监管|合规|标准)", 30.0, "行业合规"),
    (r"安全.*(评估|审查|备案)", 25.0, "安全合规"),
    (r"数据.*(跨境|出境|transfer)", 45.0, "数据跨境合规"),
    (r"上市|IPO|证券|股票", 40.0, "上市合规"),
    (r"环保|碳排放|esg", 20.0, "ESG合规"),
    (r"出口管制|制裁|embargo", 55.0, "出口管制"),
]

LEGAL_PATTERNS: list[tuple[str, float, str]] = [
    (r"合同.*(签署|审核|变更|终止)", 25.0, "合同事务"),
    (r"诉讼|仲裁|纠纷|争议", 50.0, "法律纠纷"),
    (r"侵权|抄袭|盗用|盗版", 45.0, "知识产权侵权"),
    (r"并购|收购|兼并|重组", 55.0, "并购重组"),
    (r"专利|商标|著作权|版权.*(申请|维权)", 30.0, "知识产权申请"),
    (r"劳动.*(合同|纠纷|仲裁|法)", 30.0, "劳动法律"),
    (r"保密协议|NDA|竞业|禁业", 25.0, "保密与竞业"),
    (r"合资|合营|合伙协议", 35.0, "合资合作"),
    (r"法律.*(意见|审查|顾问)", 20.0, "法律咨询"),
    (r"赔偿|违约金|索赔", 40.0, "赔偿索赔"),
]

PRIVACY_PATTERNS: list[tuple[str, float, str]] = [
    (r"用户.*数据|个人.*信息|PII", 40.0, "个人数据处理"),
    (r"隐私.*(政策|策略|声明)", 25.0, "隐私政策"),
    (r"数据.*(采集|收集|抓取|爬虫)", 35.0, "数据采集"),
    (r"数据.*(共享|分享|出售|提供.*第三方)", 50.0, "数据共享"),
    (r"生物.*(识别|特征|信息)|指纹|人脸|声纹", 45.0, "生物识别信息"),
    (r"监控|监听|跟踪|追踪.*用户", 50.0, "用户监控"),
    (r"儿童.*(数据|隐私|信息)", 55.0, "未成年人数据"),
    (r"GDPR|CCPA|个人信息保护法|个保法|网安法|数安法", 45.0, "数据保护法规"),
    (r"数据.*(泄露|泄漏|外泄|泄露)", 60.0, "数据泄露风险"),
    (r"cookie|SDK.*(数据|采集)", 20.0, "SDK数据采集"),
]


class RiskEngine:
    """
    CEO风险引擎。

    async assess(intent) 对意图分析结果进行4类风险评估，
    返回综合风险评分及审批建议。
    """

    def __init__(self):
        self._compiled: dict[str, list[tuple[re.Pattern, float, str]]] = {
            "financial": [(re.compile(p, re.IGNORECASE), s, d) for p, s, d in FINANCIAL_PATTERNS],
            "compliance": [(re.compile(p, re.IGNORECASE), s, d) for p, s, d in COMPLIANCE_PATTERNS],
            "legal": [(re.compile(p, re.IGNORECASE), s, d) for p, s, d in LEGAL_PATTERNS],
            "privacy": [(re.compile(p, re.IGNORECASE), s, d) for p, s, d in PRIVACY_PATTERNS],
        }

    def assess(self, intent: Any) -> RiskAssessment:
        """
        对意图进行风险评估。

        intent 可以是 IntentResult 对象或包含 raw_text 的 dict。
        """
        # 统一获取文本
        if hasattr(intent, "raw_text"):
            text = intent.raw_text
        elif isinstance(intent, dict):
            text = intent.get("raw_text", intent.get("text", ""))
        else:
            text = str(intent)

        if not text:
            return RiskAssessment(
                risk_score=0.0,
                requires_approval=False,
                flags=[],
                reason="无文本内容，无风险",
            )

        # 逐维度检查
        dimension_results: dict[str, tuple[float, list[dict]]] = {}
        for dim_name in ("financial", "compliance", "legal", "privacy"):
            score, flags = self._check_dimension(text, dim_name)
            dimension_results[dim_name] = (score, flags)

        # 汇总
        all_flags: list[dict] = []
        total_score = 0.0
        for dim_name, (score, flags) in dimension_results.items():
            all_flags.extend(flags)
            # 各维度加权
            weights = {
                "financial": 0.25,
                "compliance": 0.25,
                "legal": 0.25,
                "privacy": 0.25,
            }
            total_score += score * weights[dim_name]

        # 如果有任一维度极高，总分应提高
        max_dim_score = max((s for s, _ in dimension_results.values()), default=0.0)
        if max_dim_score > 70:
            total_score = max(total_score, max_dim_score * 0.7)

        risk_score = round(min(total_score, 100.0), 1)
        requires_approval = risk_score > 60
        is_rejected = risk_score > 80

        # 生成理由
        reasons = []
        if is_rejected:
            reasons.append("⚠️ 风险评分 > 80 — 系统自动拒绝")
        elif requires_approval:
            reasons.append("⚠️ 风险评分 > 60 — 需要Plan Mode审批")

        for dim_name, (score, flags) in dimension_results.items():
            if flags:
                dim_label = {"financial": "资金", "compliance": "合规", "legal": "法律", "privacy": "隐私"}[dim_name]
                reasons.append(f"  [{dim_label}] 评分 {score:.1f}: {', '.join(f['detail'] for f in flags[:3])}")

        if not reasons:
            reasons.append("✅ 无显著风险，自动放行")

        return RiskAssessment(
            risk_score=risk_score,
            requires_approval=requires_approval or is_rejected,
            flags=all_flags,
            reason=" | ".join(reasons),
            financial_risk=round(dimension_results["financial"][0], 1),
            compliance_risk=round(dimension_results["compliance"][0], 1),
            legal_risk=round(dimension_results["legal"][0], 1),
            privacy_risk=round(dimension_results["privacy"][0], 1),
        )

    def _check_dimension(self, text: str, dim: str) -> tuple[float, list[dict]]:
        """检查单一风险维度"""
        flags: list[dict] = []
        score = 0.0

        patterns = self._compiled.get(dim, [])
        for pattern, severity, detail in patterns:
            matches = pattern.findall(text)
            if matches:
                # 多次命中累加，但有限度
                contribution = severity * min(len(matches), 3)
                score += contribution
                flags.append({
                    "dimension": dim,
                    "detail": detail,
                    "severity": severity,
                    "matches": matches[:3],
                })

        return min(score, 100.0), flags
