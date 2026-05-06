"""
墨域OS — L1 CEO意图路由器
==========================
分析用户输入文本，识别意图类型、复杂度、提取实体，
并映射到5个VP管理层和20家子公司。
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("molin.ceo.intent_router")


# ── 20家子公司的关键词映射表 ──────────────────────────────────────────
# 格式: {子公司worker_id: [触发关键词列表]}
# 覆盖config/company.toml中所有20家子公司

SUBSIDIARY_KEYWORDS: dict[str, list[str]] = {
    # === VP营销 (5家) ===
    "content_writer": [
        "文案", "写作", "文章", "内容创作", "文创", "品牌内容",
        "blog", "seo文章", "软文", "推文", "稿件", "选题", "撰写",
    ],
    "ip_manager": [
        "ip", "IP孵化", "版权", "授权", "衍生", "企划",
        "知识产权", "ip运营", "ip管理", "IP开发",
    ],
    "designer": [
        "设计", "视觉", "封面图", "ui", "ux", "海报", "banner",
        "插画", "logo", "品牌视觉", "排版", "美工", "作图",
    ],
    "short_video": [
        "短视频", "抖音", "视频号", "快手", "视频制作", "剪辑",
        "增长", "流量", "投流", "曝光", "短视频运营", "直播",
    ],
    "voice_actor": [
        "配音", "音频", "语音", "旁白", "声优", "TTS",
        "有声书", "播客", "音效", "录音", "声音",
    ],
    # === VP运营 (4家) ===
    "crm": [
        "crm", "私域", "客户管理", "用户运营", "会员", "粉丝",
        "社群", "企微", "微信生态", "用户分层", "自动化营销",
    ],
    "customer_service": [
        "客服", "售后", "工单", "投诉", "咨询", "FAQ",
        "智能客服", "问答", "帮助中心", "客户支持",
    ],
    "ecommerce": [
        "电商", "商城", "交易", "订单", "商品", "上架",
        "支付", "物流", "供应链", "店铺", "闲鱼", "售卖",
    ],
    "education": [
        "教育", "课程", "培训", "学苑", "教学", "考试",
        "学习", "在线教育", "讲师", "课件", "证书",
    ],
    # === VP技术 (4家) ===
    "developer": [
        "开发", "编码", "代码", "编程", "程序", "功能开发",
        "api", "后端", "前端", "全栈", "bug修复", "软件开发",
    ],
    "ops": [
        "运维", "部署", "基础设施", "k8s", "docker", "服务器",
        "监控", "ci/cd", "发布", "上线", "稳定性", "k8s集群",
    ],
    "security": [
        "安全", "漏洞", "渗透", "合规安全", "防火墙", "审计",
        "数据安全", "加密", "零信任", "SOC", "DLP", "信息安全",
    ],
    "auto_dream": [
        "ai", "自动化", "智能体", "agent", "模型训练", "机器学习",
        "深度学习", "autodream", "自动流程", "RPA", "提示词工程",
    ],
    # === VP财务 (1家) ===
    "finance": [
        "财务", "预算", "成本", "收入", "利润", "核算",
        "报表", "税务", "发票", "对账", "投资", "融资", "资金",
    ],
    # === VP战略 (3家) ===
    "bd": [
        "商务", "合作", "bd", "招商", "渠道", "战略合作",
        "商务拓展", "签约", "合作伙伴", "对外合作",
    ],
    "global_marketing": [
        "出海", "海外", "全球化", "国际化", "跨境", "global",
        "海外市场", "本地化", "国外", "英语", "多语种",
    ],
    "research": [
        "调研", "行业研究", "竞品分析", "市场分析", "研究报告",
        "竞争情报", "趋势", "数据调研", "战略分析",
    ],
    # === 共同子公司 (3家) ===
    "legal": [
        "法务", "法律", "合同", "合规", "诉讼", "纠纷",
        "知识产权保护", "法律咨询", "条款", "协议",
    ],
    "knowledge": [
        "知识库", "知识管理", "知识图谱", "文档管理", "wiki",
        "企业知识", "搜索", "知识沉淀",
    ],
    "data_analyst": [
        "数据分析", "bi", "报表", "仪表盘", "数据测试",
        "数据质量", "数据仓库", "指标", "数据治理", "埋点",
    ],
}

# VP与子公司的映射关系
VP_SUBSIDIARY_MAP: dict[str, list[str]] = {
    "VP营销": ["content_writer", "ip_manager", "designer", "short_video", "voice_actor"],
    "VP运营": ["crm", "customer_service", "ecommerce", "education"],
    "VP技术": ["developer", "ops", "security", "auto_dream"],
    "VP财务": ["finance"],
    "VP战略": ["bd", "global_marketing", "research"],
}

# 共同子公司归属（所有VP共享）
SHARED_SUBSIDIARIES = ["legal", "knowledge", "data_analyst"]

# 反向映射：子公司 -> VP
SUBSIDIARY_TO_VP: dict[str, str] = {}
for vp_name, sub_ids in VP_SUBSIDIARY_MAP.items():
    for sid in sub_ids:
        SUBSIDIARY_TO_VP[sid] = vp_name
# 共同子公司暂不设默认VP，调用方指定

# 风险关键词（用于快速粗估）
HIGH_RISK_KEYWORDS = [
    "资金", "转账", "投资", "融资", "大额", "签约", "合同",
    "法律", "诉讼", "合规审查", "数据导出", "用户隐私",
    "敏感数据", "跨境数据", "上市", "并购", "重大决策",
]


@dataclass
class IntentResult:
    """意图分析结果"""
    intent_type: str
    complexity_score: float  # 0-100
    entities: dict[str, Any] = field(default_factory=dict)
    target_vps: list[str] = field(default_factory=list)
    target_subsidiaries: list[str] = field(default_factory=list)
    risk_level: str = "low"  # low | medium | high | critical
    raw_text: str = ""


class IntentRouter:
    """
    意图路由器。

    分析用户输入文本，识别：
    - intent_type: 意图类型（营销/运营/技术/财务/战略/综合）
    - complexity_score: 复杂度评分 (0-100)
    - entities: 提取的实体（金额、时间、目标等）
    - target_vps: 需要调度的VP列表
    - risk_level: 粗略风险等级
    """

    def __init__(self):
        # 编译关键词正则
        self._subsidiary_patterns: dict[str, re.Pattern] = {}
        for sid, keywords in SUBSIDIARY_KEYWORDS.items():
            # 构建正则：匹配任一关键词
            pattern = "|".join(re.escape(kw) for kw in keywords)
            self._subsidiary_patterns[sid] = re.compile(pattern, re.IGNORECASE)

        self._high_risk_pattern = re.compile(
            "|".join(re.escape(kw) for kw in HIGH_RISK_KEYWORDS),
            re.IGNORECASE,
        )

    async def analyze(self, text: str) -> IntentResult:
        """
        异步分析用户输入，返回意图分析结果。
        """
        if not text or not text.strip():
            return IntentResult(
                intent_type="unknown",
                complexity_score=0.0,
                entities={},
                target_vps=[],
                target_subsidiaries=[],
                risk_level="low",
                raw_text=text or "",
            )

        text_lower = text.lower()
        matched_subsidiaries: list[str] = []
        matched_vp_set: set[str] = set()

        # 1. 匹配子公司
        for sid, pattern in self._subsidiary_patterns.items():
            if pattern.search(text):
                matched_subsidiaries.append(sid)
                # 找对应VP
                vp_name = SUBSIDIARY_TO_VP.get(sid)
                if vp_name:
                    matched_vp_set.add(vp_name)

        # 2. 直接VP关键词匹配（如果子公司没匹配到，退而求其次）
        vp_direct_keywords = {
            "营销": "VP营销",
            "市场": "VP营销",
            "品牌": "VP营销",
            "内容": "VP营销",
            "运营": "VP运营",
            "客服": "VP运营",
            "教育": "VP运营",
            "电商": "VP运营",
            "技术": "VP技术",
            "开发": "VP技术",
            "研发": "VP技术",
            "架构": "VP技术",
            "财务": "VP财务",
            "会计": "VP财务",
            "预算": "VP财务",
            "战略": "VP战略",
            "商业": "VP战略",
            "研究": "VP战略",
        }
        for kw, vp_name in vp_direct_keywords.items():
            if kw in text_lower:
                matched_vp_set.add(vp_name)

        target_vps = list(matched_vp_set)
        target_subsidiaries = matched_subsidiaries

        # 3. 判断意图类型
        intent_type = self._classify_intent(target_vps, target_subsidiaries, text)

        # 4. 计算复杂度
        complexity_score = self._calc_complexity(text, target_subsidiaries)

        # 5. 风险等级
        risk_level = self._calc_risk_level(text)

        # 6. 提取实体
        entities = self._extract_entities(text)

        return IntentResult(
            intent_type=intent_type,
            complexity_score=complexity_score,
            entities=entities,
            target_vps=target_vps if target_vps else ["VP战略"],  # 默认战略兜底
            target_subsidiaries=target_subsidiaries,
            risk_level=risk_level,
            raw_text=text,
        )

    def _classify_intent(
        self,
        vps: list[str],
        subsidiaries: list[str],
        text: str,
    ) -> str:
        """根据匹配到的VP和文本判断意图类型"""
        if len(vps) >= 3:
            return "综合"
        if len(vps) == 1:
            vp_name = vps[0]
            if "营销" in vp_name:
                return "营销"
            if "运营" in vp_name:
                return "运营"
            if "技术" in vp_name:
                return "技术"
            if "财务" in vp_name:
                return "财务"
            if "战略" in vp_name:
                return "战略"
        # 没有匹配到任何VP
        return "综合"

    def _calc_complexity(self, text: str, subsidiaries: list[str]) -> float:
        """计算复杂度 (0-100)"""
        score = 0.0
        # 长度因子
        length = len(text)
        if length > 200:
            score += 20
        elif length > 100:
            score += 10
        else:
            score += 5

        # 子公司数量因子
        score += min(len(subsidiaries) * 10, 30)

        # 数字/金额因子
        amounts = re.findall(r"\d+[万亿千万百万]?\s*元", text)
        if amounts:
            score += 15

        # 时间规划因子
        if re.search(r"(计划|方案|规划|路线图|roadmap|strategy)", text, re.IGNORECASE):
            score += 15

        # 跨部门因子
        if re.search(r"(协作|协同|联动|联合|结合|整合)", text):
            score += 10

        # 技术术语因子
        tech_terms = re.findall(
            r"(架构|集群|数据库|算法|模型|api|微服务|容器|部署|k8s|docker|分布式)",
            text.lower(),
        )
        score += min(len(tech_terms) * 5, 20)

        return min(round(score, 1), 100.0)

    def _calc_risk_level(self, text: str) -> str:
        """粗略风险评估"""
        matches = self._high_risk_pattern.findall(text)
        count = len(matches)
        if count >= 3:
            return "critical"
        if count >= 2:
            return "high"
        if count >= 1:
            return "medium"
        return "low"

    def _extract_entities(self, text: str) -> dict[str, Any]:
        """提取常见实体"""
        entities: dict[str, Any] = {}

        # 金额
        amounts = re.findall(r"(\d+(?:\.\d+)?)\s*(万亿|千万|百万|万|亿|元|美元|人民币)", text)
        if amounts:
            entities["amounts"] = [{"value": a[0], "unit": a[1]} for a in amounts]

        # 时间
        dates = re.findall(
            r"(\d{4}年\d{1,2}月\d{1,2}日|\d{4}年\d{1,2}月|本月|下月|今年|明年|上季度|下季度)",
            text,
        )
        if dates:
            entities["dates"] = dates

        # 平台
        platforms = re.findall(
            r"(抖音|快手|微信|小红书|微博|B站|bilibili|淘宝|京东|拼多多|闲鱼|亚马逊|shopify|tiktok|youtube|instagram|facebook)",
            text,
            re.IGNORECASE,
        )
        if platforms:
            entities["platforms"] = list(set(p.lower() for p in platforms))

        # 语言
        langs = re.findall(r"(中文|英语|日语|韩语|法语|西班牙语|多语种|zh|en|ja|ko)", text.lower())
        if langs:
            entities["languages"] = list(set(langs))

        return entities
