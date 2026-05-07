"""
墨域OS — L2 CEO语义路由引擎
=====================================
将意图路由从"关键词匹配"升级为"LLM语义理解+历史缓存"。

架构：
- Layer 0: 纯规则拦截问候/问候语 (Trivial) — 零成本
- Layer 1: CEO LLM 基于子公司能力画像进行语义路由 → output dispatch_plan
- Layer 2: 历史成功路由缓存 → 相似请求直接复用，降低延迟
- Layer 3: 兜底 — 关键词匹配

依赖：
- LLMClient (真实 DeepSeek API)
- 本地 JSON 缓存 (零新依赖)
"""

import json
import hashlib
import time
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


# ── 子公司能力画像 ──────────────────────────────────────────────
# 供 LLM 判断路由的依据

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

# ── Layer 0: 问候/闲聊拦截 ─────────────────────────────────────

TRIVIAL_PATTERNS = [
    r"^(你好|hi|hello|早上好|下午好|晚上好|你好吗|在吗|在不在|吃了没|在忙吗)",
    r"^(good morning|good afternoon|good evening|hey|yo)",
    r"^(你是谁|你叫什么|who are you)",
    r"^(谢谢|谢谢了|谢谢啦|ok|好的|好滴|好的吧|收到)",
    r"^(再见|拜拜|see you|bye|明天见)",
]


def is_trivial(text: str) -> bool:
    """Layer 0: 检测是否为问候/闲聊"""
    import re
    for p in TRIVIAL_PATTERNS:
        if re.search(p, text.strip(), re.IGNORECASE):
            return True
    return False


# ── 路由缓存 ────────────────────────────────────────────────────

CACHE_DIR = Path.home() / ".hermes" / "semantic_routes"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE = CACHE_DIR / "route_cache.json"
SIMILARITY_THRESHOLD = 0.75  # 语义相似度阈值


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
    """通过简单编辑距离 + 关键词重叠找缓存中的相似请求"""
    text_lower = text.lower()
    words = set(text_lower.split())

    best_match = None
    best_score = 0.0

    for entry in cache.values():
        cached_text = entry.get("text", "").lower()
        cached_words = set(cached_text.split())
        if not words or not cached_words:
            continue
        # Jaccard 相似度
        intersection = words & cached_words
        union = words | cached_words
        score = len(intersection) / len(union) if union else 0

        if score > best_score and score >= SIMILARITY_THRESHOLD:
            best_score = score
            best_match = entry

    return best_match


# ── 路由结果 ────────────────────────────────────────────────────


@dataclass
class RouteResult:
    """路由结果"""
    subsidiaries: list[str]           # 匹配的子公司名称列表
    confidence: float                 # 置信度 0-1
    source: str                       # "cache" | "llm" | "keyword" | "trivial"
    complexity: float                 # 复杂度 0-100
    note: str = ""                    # 备注
    vp_targets: list[str] = field(default_factory=list)


# ── 语义路由引擎 ────────────────────────────────────────────────


class SemanticRouter:
    """
    CEO 语义路由引擎 — 四层架构。

    使用示例：
        router = SemanticRouter(llm_client)
        result = await router.route("帮我写一篇小红书文案")
    """

    def __init__(self, llm_client=None):
        self._llm = llm_client
        self._cache = _load_cache()

    def set_llm_client(self, llm_client):
        """注入 LLMClient 实例"""
        self._llm = llm_client

    async def route(self, user_input: str) -> RouteResult:
        """
        四层语义路由。

        1. Layer 0: 问候拦截
        2. Layer 1 (cache): 查找历史缓存
        3. Layer 2 (LLM): CEO LLM 语义判断
        4. Layer 3 (keyword): 关键词兜底

        Args:
            user_input: 用户输入

        Returns:
            RouteResult
        """
        if not user_input or not user_input.strip():
            return RouteResult(
                subsidiaries=[],
                confidence=0.0,
                source="empty",
                complexity=0,
                note="输入为空",
            )

        text = user_input.strip()

        # ── Layer 0: 问候拦截 ──
        if is_trivial(text):
            return RouteResult(
                subsidiaries=[],
                confidence=1.0,
                source="trivial",
                complexity=0,
                note="问候/闲聊 — 无需调度子公司",
            )

        # ── Layer 1: 缓存命中 ──
        cached = _find_similar(text, self._cache)
        if cached:
            return RouteResult(
                subsidiaries=cached.get("subsidiaries", []),
                confidence=cached.get("confidence", 0.85),
                source="cache",
                complexity=cached.get("complexity", 30),
                note=f"命中历史路由缓存 (相似度: {cached.get('_similarity', '?')})",
                vp_targets=cached.get("vp_targets", []),
            )

        # ── Layer 2: LLM 语义路由 ──
        if self._llm:
            try:
                return await self._route_by_llm(text)
            except Exception as e:
                # LLM 失败，降级到关键词
                pass

        # ── Layer 3: 关键词兜底 ──
        return self._route_by_keywords(text)

    async def _route_by_llm(self, text: str) -> RouteResult:
        """Layer 2: 用 LLM 做语义路由"""
        # 构建子公司能力描述
        profile_lines = []
        for name, profile in SUBSIDIARY_PROFILES.items():
            caps = "、".join(profile["capabilities"])
            examples = "、".join(profile["examples"])
            profile_lines.append(f"- {name}（{profile['role']}）: 能力={caps}，示例请求={examples}")

        profile_text = "\n".join(profile_lines)

        system_prompt = f"""你是墨域OS的CEO意图分析员。分析用户输入，判断应该调度哪些子公司。

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
        import re
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if not json_match:
            return self._route_by_keywords(text)

        try:
            data = json.loads(json_match.group(0))
        except json.JSONDecodeError:
            return self._route_by_keywords(text)

        subsidiaries = data.get("subsidiaries", [])
        confidence = min(float(data.get("confidence", 0.7)), 1.0)
        complexity = float(data.get("complexity", 30))
        reason = data.get("reason", "")

        # 验证子公司名称是否在能力范围内
        valid = [s for s in subsidiaries if s in SUBSIDIARY_PROFILES]
        if not valid:
            return self._route_by_keywords(text)

        # 缓存结果
        hash_key = _text_hash(text)
        self._cache[hash_key] = {
            "text": text,
            "subsidiaries": valid,
            "confidence": confidence,
            "complexity": complexity,
            "reason": reason,
            "vp_targets": [],
            "cached_at": time.time(),
        }
        _save_cache(self._cache)

        return RouteResult(
            subsidiaries=valid,
            confidence=confidence,
            source="llm",
            complexity=complexity,
            note=reason,
        )

    def _route_by_keywords(self, text: str) -> RouteResult:
        """Layer 3: 关键词兜底"""
        text_lower = text.lower()
        matches = []

        for name, profile in SUBSIDIARY_PROFILES.items():
            for kw in profile["keywords"]:
                if kw.lower() in text_lower:
                    if name not in matches:
                        matches.append(name)
                    break

        if not matches:
            return RouteResult(
                subsidiaries=[],
                confidence=0.0,
                source="keyword",
                complexity=5,
                note="未匹配到任何子公司",
            )

        return RouteResult(
            subsidiaries=matches,
            confidence=0.6,
            source="keyword",
            complexity=10 + len(matches) * 5,
            note=f"关键词匹配到: {', '.join(matches)}",
        )

    def list_profiles(self) -> dict:
        """列出所有子公司能力画像（供CEO主流程使用）"""
        return dict(SUBSIDIARY_PROFILES)
