"""
墨麟OS — L1 CEO意图路由器 (合并版)
======================================
整合关键词路由 + LLM语义路由 + 缓存 + 问候拦截 的四层架构。

路由层级：
  Layer 0: 问候/闲聊拦截 (Trivial) — 零成本
  Layer 1: 历史路由缓存 — Jaccard相似度匹配
  Layer 2: LLM语义路由 — 基于子公司能力画像的DeepSeek推理
  Layer 3: 关键词兜底 — 原 intent_router.py 完整关键词匹配

CEOOrchestrator 继续使用 IntentRouter 接口（不变）。
弃用 molib/ceo/ceo_reasoning.py — 多轮对话LLM推理已废弃。
"""

import json
import hashlib
import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("molin.ceo.intent_router")


# ═══════════════════════════════════════════════════════════════════
# Layer 0: 问候/闲聊拦截 (from semantic_router.py)
# ═══════════════════════════════════════════════════════════════════

TRIVIAL_PATTERNS = [
    r"^(你好|hi|hello|早上好|下午好|晚上好|你好吗|在吗|在不在|吃了没|在忙吗)",
    r"^(good morning|good afternoon|good evening|hey|yo)",
    r"^(你是谁|你叫什么|who are you)",
    r"^(谢谢|谢谢了|谢谢啦|ok|好的|好滴|好的吧|收到)",
    r"^(再见|拜拜|see you|bye|明天见)",
]


def is_trivial(text: str) -> bool:
    """Layer 0: 检测是否为问候/闲聊"""
    for p in TRIVIAL_PATTERNS:
        if re.search(p, text.strip(), re.IGNORECASE):
            return True
    return False


# ═══════════════════════════════════════════════════════════════════
# Layer 1: 路由缓存 (from semantic_router.py)
# ═══════════════════════════════════════════════════════════════════

CACHE_DIR = Path.home() / ".hermes" / "semantic_routes"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE = CACHE_DIR / "route_cache.json"
SIMILARITY_THRESHOLD = 0.75


def _text_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:16]


def _load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_cache(cache: dict):
    CACHE_FILE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _find_similar(text: str, cache: dict) -> Optional[dict]:
    """通过 Jaccard 相似度找缓存中的相似请求"""
    text_lower = text.lower()
    words = set(text_lower.split())
    best_match = None
    best_score = 0.0
    for entry in cache.values():
        cached_text = entry.get("text", "").lower()
        cached_words = set(cached_text.split())
        if not words or not cached_words:
            continue
        intersection = words & cached_words
        union = words | cached_words
        score = len(intersection) / len(union) if union else 0
        if score > best_score and score >= SIMILARITY_THRESHOLD:
            best_score = score
            best_match = entry
    return best_match


# ═══════════════════════════════════════════════════════════════════
# 子公司能力画像 (from semantic_router.py — 供LLM语义路由使用)
# ═══════════════════════════════════════════════════════════════════

SUBSIDIARY_PROFILES = {
    "墨笔文创": {
        "role": "内容创作",
        "keywords": ["文案", "写作", "文章", "内容", "稿件", "选题", "推文", "blog"],
        "capabilities": ["品牌内容创作", "SEO文章", "软文", "文创产品文案", "小红书/公众号/知乎内容"],
        "examples": ["写一篇产品推广文案", "帮我写一篇小红书笔记", "写一篇SEO文章"],
    },
    "墨韵IP": {
        "role": "IP孵化与管理",
        "keywords": ["IP", "版权", "授权", "衍生", "企划", "知识产权"],
        "capabilities": ["IP企划", "IP授权", "IP衍生开发", "品牌联名企划"],
        "examples": ["做一个IP孵化方案", "怎么给我的角色做版权授权"],
    },
    "墨图设计": {
        "role": "视觉设计",
        "keywords": ["设计", "视觉", "封面", "海报", "logo", "banner", "排版", "美工", "作图"],
        "capabilities": ["UI设计", "海报设计", "封面图", "品牌视觉", "LOGO设计", "排版"],
        "examples": ["帮我设计一张海报", "给这篇文章配封面图", "设计一个logo"],
    },
    "墨播短视频": {
        "role": "短视频制作与增长",
        "keywords": ["视频", "短视频", "抖音", "剪辑", "直播", "快手", "视频号"],
        "capabilities": ["短视频脚本", "视频剪辑方案", "抖音运营", "投流策略", "直播方案"],
        "examples": ["写一个短视频脚本", "帮我分析抖音账号怎么涨粉"],
    },
    "墨声配音": {
        "role": "音频制作与配音",
        "keywords": ["配音", "音频", "语音", "旁白", "声优", "TTS", "有声书", "播客", "音效"],
        "capabilities": ["AI配音", "旁白录制", "播客制作", "有声书制作", "音效设计"],
        "examples": ["给这段文字配音", "制作一期播客", "配一段旁白"],
    },
    "墨域私域": {
        "role": "私域运营与CRM",
        "keywords": ["私域", "CRM", "客户管理", "用户运营", "会员", "粉丝", "社群", "企微"],
        "capabilities": ["私域运营方案", "用户分层", "自动化营销流程", "社群SOP", "RFM分析"],
        "examples": ["帮我设计私域运营方案", "写一个社群日常SOP"],
    },
    "墨声客服": {
        "role": "智能客服",
        "keywords": ["客服", "售后", "工单", "FAQ", "投诉", "咨询", "帮助中心"],
        "capabilities": ["客服应答设计", "FAQ体系建设", "工单SOP", "满意度追踪"],
        "examples": ["设计一个FAQ系统", "写客服应答话术模板"],
    },
    "墨链电商": {
        "role": "电商运营",
        "keywords": ["电商", "商城", "商品", "上架", "闲鱼", "售卖", "订单"],
        "capabilities": ["商品上架", "店铺运营", "闲鱼商品管理", "订单管理"],
        "examples": ["帮我上架一个商品到闲鱼", "写一个商品描述"],
    },
    "墨学教育": {
        "role": "在线教育",
        "keywords": ["教育", "课程", "培训", "学习", "教学", "考试", "课件"],
        "capabilities": ["课程设计", "学习路径规划", "课件生成", "测验设计", "个性化辅导"],
        "examples": ["设计一门Python课程大纲", "生成一份测验试卷"],
    },
    "墨码开发": {
        "role": "软件外包开发",
        "keywords": ["开发", "编程", "代码", "API", "后端", "前端", "全栈", "Python"],
        "capabilities": ["Python开发", "Web开发", "API对接", "自动化脚本", "技术咨询"],
        "examples": ["帮我开发一个API接口", "写一个Python自动化脚本"],
    },
    "墨维运维": {
        "role": "基础设施运维",
        "keywords": ["部署", "运维", "服务器", "Docker", "K8s", "监控", "CI/CD"],
        "capabilities": ["部署方案", "Docker化", "K8s集群管理", "监控搭建", "CI/CD流水线"],
        "examples": ["帮我部署这个项目", "搭建一个监控系统"],
    },
    "墨安安全": {
        "role": "信息安全",
        "keywords": ["安全", "漏洞", "渗透", "防火墙", "审计", "加密"],
        "capabilities": ["安全审计", "渗透测试", "漏洞扫描", "权限方案"],
        "examples": ["做一次安全审计", "检查这个网站的漏洞"],
    },
    "墨算财务": {
        "role": "财务核算",
        "keywords": ["财务", "预算", "成本", "收入", "报表", "对账"],
        "capabilities": ["预算规划", "成本分析", "财务报表", "ROI分析", "子公司P&L追踪"],
        "examples": ["做月度财务分析报告", "帮我做预算规划"],
    },
    "墨商BD": {
        "role": "商务拓展",
        "keywords": ["商务", "合作", "BD", "招商", "渠道", "投标", "销售"],
        "capabilities": ["招投标方案", "商业计划书", "商务合作方案", "客户谈判"],
        "examples": ["写一份投标方案", "帮我写商业计划书"],
    },
    "墨海出海": {
        "role": "出海本地化",
        "keywords": ["出海", "海外", "全球化", "英文", "翻译", "跨境", "本地化"],
        "capabilities": ["多语言翻译", "英文文案", "海外社媒运营", "跨境合规"],
        "examples": ["翻译成英文", "写一个英文产品介绍"],
    },
    "墨研竞情": {
        "role": "行业研究",
        "keywords": ["调研", "研究", "竞品", "行业", "趋势", "报告", "分析"],
        "capabilities": ["行业研究报告", "竞品分析", "趋势洞察", "技术情报"],
        "examples": ["做一份竞品分析报告", "研究AI行业趋势"],
    },
    "墨律法务": {
        "role": "法务合规",
        "keywords": ["法务", "法律", "合同", "合规", "NDA", "隐私政策", "条款"],
        "capabilities": ["合同审查", "NDA生成", "隐私政策", "合规审计", "风险评估"],
        "examples": ["审查这份合同", "帮我生成一份NDA"],
    },
    "墨脑知识": {
        "role": "知识管理",
        "keywords": ["知识", "文档", "搜索", "知识库", "知识图谱"],
        "capabilities": ["知识库搭建", "文档管理方案", "企业搜索", "知识沉淀"],
        "examples": ["帮我整理知识库架构", "怎么搭建知识管理系统"],
    },
    "墨测数据": {
        "role": "数据与测试",
        "keywords": ["数据", "报表", "分析", "测试", "BI", "仪表盘"],
        "capabilities": ["数据分析报告", "BI仪表盘", "可视化", "自动化测试"],
        "examples": ["做一份数据分析", "设计一个BI仪表盘"],
    },
    "墨梦AutoDream": {
        "role": "AI自动化",
        "keywords": ["AI", "自动化", "Agent", "智能体", "模型", "机器学习"],
        "capabilities": ["AI工作流搭建", "Agent设计", "Prompt工程", "模型微调"],
        "examples": ["帮我搭建AI工作流", "设计一个Agent系统"],
    },
}


# ═══════════════════════════════════════════════════════════════════
# 20家子公司的关键词映射表 (from intent_router.py — Layer 3 兜底)
# ═══════════════════════════════════════════════════════════════════

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
        "自主AI实验", "模型训练", "机器学习",
        "深度学习", "自动流程", "RPA", "提示词工程",
        "autodream", "Agent开发", "智能体开发",
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
        "分析", "研究", "深度研究", "报告", "白皮书",
        "热点", "趋势分析", "爆款", "洞察", "前瞻",
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

# 子公司worker_id → 中文名称映射
WORKER_ID_TO_NAME = {
    "content_writer": "墨笔文创",
    "ip_manager": "墨韵IP",
    "designer": "墨图设计",
    "short_video": "墨播短视频",
    "voice_actor": "墨声配音",
    "crm": "墨域私域",
    "customer_service": "墨声客服",
    "ecommerce": "墨链电商",
    "education": "墨学教育",
    "developer": "墨码开发",
    "ops": "墨维运维",
    "security": "墨安安全",
    "auto_dream": "墨梦AutoDream",
    "finance": "墨算财务",
    "bd": "墨商BD",
    "global_marketing": "墨海出海",
    "research": "墨研竞情",
    "legal": "墨律法务",
    "knowledge": "墨脑知识",
    "data_analyst": "墨测数据",
}

# 中文名称 → worker_id 反向映射
NAME_TO_WORKER_ID = {v: k for k, v in WORKER_ID_TO_NAME.items()}

# 风险关键词（用于快速粗估）
HIGH_RISK_KEYWORDS = [
    "资金", "转账", "投资", "融资", "大额", "签约", "合同",
    "法律", "诉讼", "合规审查", "数据导出", "用户隐私",
    "敏感数据", "跨境数据", "上市", "并购", "重大决策",
]


# ═══════════════════════════════════════════════════════════════════
# IntentResult — 意图分析结果 (兼容原 intent_router.IntentResult)
# ═══════════════════════════════════════════════════════════════════

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
    # 新增字段（来自语义路由）
    confidence: float = 1.0   # 路由置信度 0-1
    route_source: str = "keyword"  # "trivial" | "cache" | "llm" | "keyword" | "empty"


# ═══════════════════════════════════════════════════════════════════
# IntentRouter — 四层意图路由引擎
# ═══════════════════════════════════════════════════════════════════

class IntentRouter:
    """
    意图路由器 — 四层架构。

    路由层级（按优先级）：
      Layer 0: 问候/闲聊拦截 (Trivial) — 零成本
      Layer 1: 历史路由缓存 — Jaccard相似度匹配
      Layer 2: LLM语义路由 — 基于子公司能力画像的DeepSeek推理
      Layer 3: 关键词兜底 — 原 intent_router.py 完整关键词匹配

    CEOOrchestrator 接口不变：
        result = await router.analyze(text) -> IntentResult
    """

    def __init__(self, llm_client=None):
        # Layer 3 预备：编译关键词正则
        self._subsidiary_patterns: dict[str, re.Pattern] = {}
        for sid, keywords in SUBSIDIARY_KEYWORDS.items():
            pattern = "|".join(re.escape(kw) for kw in keywords)
            self._subsidiary_patterns[sid] = re.compile(pattern, re.IGNORECASE)

        self._high_risk_pattern = re.compile(
            "|".join(re.escape(kw) for kw in HIGH_RISK_KEYWORDS),
            re.IGNORECASE,
        )

        # Layer 2 LLM 客户端
        self._llm = llm_client

        # Layer 1 缓存
        self._cache = _load_cache()

    def set_llm_client(self, llm_client):
        """注入 LLMClient 实例（Layer 2 使用）"""
        self._llm = llm_client

    async def analyze(self, text: str) -> IntentResult:
        """
        异步分析用户输入 — 四层路由。

        Args:
            text: 用户输入文本

        Returns:
            IntentResult
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
                confidence=0.0,
                route_source="empty",
            )

        text = text.strip()

        # ── Layer 0: 问候拦截 ──
        if is_trivial(text):
            return IntentResult(
                intent_type="chat",
                complexity_score=0.0,
                entities={},
                target_vps=[],
                target_subsidiaries=[],
                risk_level="low",
                raw_text=text,
                confidence=1.0,
                route_source="trivial",
            )

        # ── Layer 1: 缓存命中 ──
        cached = _find_similar(text, self._cache)
        if cached:
            subsidiaries_cn = cached.get("subsidiaries", [])
            worker_ids = [NAME_TO_WORKER_ID.get(s, s) for s in subsidiaries_cn]
            vps = self._worker_ids_to_vps(worker_ids)
            return IntentResult(
                intent_type=self._classify_intent(vps, worker_ids, text),
                complexity_score=float(cached.get("complexity", 30)),
                entities={},
                target_vps=vps,
                target_subsidiaries=worker_ids,
                risk_level=self._calc_risk_level(text),
                raw_text=text,
                confidence=float(cached.get("confidence", 0.85)),
                route_source="cache",
            )

        # ── Layer 2: LLM 语义路由 ──
        if self._llm:
            try:
                llm_result = await self._route_by_llm(text)
                if llm_result is not None:
                    return llm_result
            except Exception as e:
                logger.warning("[IntentRouter] LLM路由失败，降级到关键词: %s", e)

        # ── Layer 3: 关键词兜底 (原 intent_router.py 完整逻辑) ──
        return self._route_by_keywords_fallback(text)

    async def _route_by_llm(self, text: str) -> Optional[IntentResult]:
        """Layer 2: 用 LLM 做语义路由"""
        # 构建子公司能力描述
        profile_lines = []
        for name, profile in SUBSIDIARY_PROFILES.items():
            caps = "、".join(profile["capabilities"])
            examples = "、".join(profile["examples"])
            profile_lines.append(f"- {name}（{profile['role']}）: 能力={caps}，示例请求={examples}")

        profile_text = "\n".join(profile_lines)

        system_prompt = f"""你是墨麟OS的CEO意图分析员。分析用户输入，判断应该调度哪些子公司。

子公司能力清单：
{profile_text}

输出严格的JSON格式，不要带markdown：
{{
    "subsidiaries": ["子公司名1", "子公司名2"],
    "confidence": 0.95,
    "complexity": 50,
    "reason": "选这些子公司的原因"
}}

规则：
- 可以同时匹配多家子公司（并发执行）
- 如果用户输入无法匹配合适的子公司，返回空列表
- 复杂度：简单任务0-30，中等30-60，复杂60-100
- 置信度：非常确定0.9+，基本确定0.7-0.9，不确定0.5-0.7"""

        response = self._llm.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ], model="deepseek-v4-flash")  # Flash 就够做路由了

        # 解析 JSON
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if not json_match:
            return None

        try:
            data = json.loads(json_match.group(0))
        except json.JSONDecodeError:
            return None

        subsidiaries_cn = data.get("subsidiaries", [])
        confidence = min(float(data.get("confidence", 0.7)), 1.0)
        complexity = float(data.get("complexity", 30))

        # 验证子公司名称是否在能力范围内
        valid_cn = [s for s in subsidiaries_cn if s in SUBSIDIARY_PROFILES]
        if not valid_cn:
            return None

        # 中文名 → worker_id 映射
        worker_ids = [NAME_TO_WORKER_ID.get(s, s) for s in valid_cn]
        vps = self._worker_ids_to_vps(worker_ids)

        # 缓存结果
        hash_key = _text_hash(text)
        self._cache[hash_key] = {
            "text": text,
            "subsidiaries": valid_cn,
            "confidence": confidence,
            "complexity": complexity,
            "reason": data.get("reason", ""),
            "vp_targets": vps,
            "cached_at": time.time(),
        }
        _save_cache(self._cache)

        return IntentResult(
            intent_type=self._classify_intent(vps, worker_ids, text),
            complexity_score=complexity,
            entities={},
            target_vps=vps,
            target_subsidiaries=worker_ids,
            risk_level=self._calc_risk_level(text),
            raw_text=text,
            confidence=confidence,
            route_source="llm",
        )

    def _route_by_keywords_fallback(self, text: str) -> IntentResult:
        """
        Layer 3: 关键词兜底 — 原 intent_router.py 完整逻辑。
        保留 intent_type, complexity, entities, risk_level 等全部原有行为。
        """
        text_lower = text.lower()
        matched_subsidiaries: list[str] = []
        matched_vp_set: set[str] = set()

        # 1. 匹配子公司 (worker_id 级别)
        for sid, pattern in self._subsidiary_patterns.items():
            if pattern.search(text):
                matched_subsidiaries.append(sid)
                vp_name = SUBSIDIARY_TO_VP.get(sid)
                if vp_name:
                    matched_vp_set.add(vp_name)

        # 2. 直接VP关键词匹配
        vp_direct_keywords = {
            "营销": "VP营销", "市场": "VP营销", "品牌": "VP营销", "内容": "VP营销",
            "运营": "VP运营", "客服": "VP运营", "教育": "VP运营", "电商": "VP运营",
            "技术": "VP技术", "开发": "VP技术", "研发": "VP技术", "架构": "VP技术",
            "财务": "VP财务", "会计": "VP财务", "预算": "VP财务",
            "战略": "VP战略", "商业": "VP战略", "研究": "VP战略",
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
            target_vps=target_vps if target_vps else ["VP战略"],
            target_subsidiaries=target_subsidiaries,
            risk_level=risk_level,
            raw_text=text,
            confidence=0.6,
            route_source="keyword",
        )

    # ═══════════════════════════════════════════════════════════════
    # 辅助方法 (from intent_router.py)
    # ═══════════════════════════════════════════════════════════════

    def _classify_intent(
        self, vps: list[str], subsidiaries: list[str], text: str,
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
        return "综合"

    def _calc_complexity(self, text: str, subsidiaries: list[str]) -> float:
        """计算复杂度 (0-100)"""
        score = 0.0
        length = len(text)
        if length > 200:
            score += 20
        elif length > 100:
            score += 10
        else:
            score += 5
        score += min(len(subsidiaries) * 10, 30)
        amounts = re.findall(r"\d+[万亿千万百万]?\s*元", text)
        if amounts:
            score += 15
        if re.search(r"(计划|方案|规划|路线图|roadmap|strategy)", text, re.IGNORECASE):
            score += 15
        if re.search(r"(协作|协同|联动|联合|结合|整合)", text):
            score += 10
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
        amounts = re.findall(r"(\d+(?:\.\d+)?)\s*(万亿|千万|百万|万|亿|元|美元|人民币)", text)
        if amounts:
            entities["amounts"] = [{"value": a[0], "unit": a[1]} for a in amounts]
        dates = re.findall(
            r"(\d{4}年\d{1,2}月\d{1,2}日|\d{4}年\d{1,2}月|本月|下月|今年|明年|上季度|下季度)",
            text,
        )
        if dates:
            entities["dates"] = dates
        platforms = re.findall(
            r"(抖音|快手|微信|小红书|微博|B站|bilibili|淘宝|京东|拼多多|闲鱼|亚马逊|shopify|tiktok|youtube|instagram|facebook)",
            text, re.IGNORECASE,
        )
        if platforms:
            entities["platforms"] = list(set(p.lower() for p in platforms))
        langs = re.findall(r"(中文|英语|日语|韩语|法语|西班牙语|多语种|zh|en|ja|ko)", text.lower())
        if langs:
            entities["languages"] = list(set(langs))
        return entities

    def _worker_ids_to_vps(self, worker_ids: list[str]) -> list[str]:
        """worker_id列表 → VP列表"""
        vp_set: set[str] = set()
        for wid in worker_ids:
            vp_name = SUBSIDIARY_TO_VP.get(wid)
            if vp_name:
                vp_set.add(vp_name)
        return list(vp_set)

    def list_profiles(self) -> dict:
        """列出所有子公司能力画像（供CEO主流程使用）"""
        return dict(SUBSIDIARY_PROFILES)
