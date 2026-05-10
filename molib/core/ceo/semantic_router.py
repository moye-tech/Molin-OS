"""
语义路由器 v1.0
替代 IntentProcessor 的关键词匹配路由。
四层架构：轻量过滤 → CEO语义决策 → 向量历史召回 → 能力画像兜底
"""

from __future__ import annotations

import json
import time
import asyncio
import hashlib
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from loguru import logger


# ── 数据结构 ──────────────────────────────

@dataclass
class RouteDecision:
    """单次路由决策结果"""
    dispatch_plan:   List[Dict[str, Any]]  # [{agency, task, priority, depends_on}]
    confidence:      float                  # 0-1
    route_source:    str                    # "ceo_llm" | "vector_cache" | "capability_match" | "trivial_filter"
    thinking:        str = ""
    ceo_response:    str = ""
    latency_ms:      float = 0.0
    is_trivial:      bool = False
    trivial_reply:   Optional[str] = None

@dataclass
class RouteHistoryEntry:
    """路由历史记录（写入 Qdrant）"""
    user_input:    str
    dispatch_plan: List[Dict]
    outcome:       str         # "success" | "partial" | "failure"
    agencies_used: List[str]
    timestamp:     float = field(default_factory=time.time)


# ── Layer 0：轻量 Trivial 过滤（纯规则，<1ms）──────────────────

_TRIVIAL_PATTERNS = [
    (re.compile(r'^(你好|hi|hello|hey|嗨|早|晚安)', re.I), "你好！有什么需要帮忙的？"),
    (re.compile(r'^(谢谢|感谢|thx|thanks)', re.I),          "不客气，随时为您服务！"),
    (re.compile(r'^(再见|拜|bye)', re.I),                   "再见，有问题随时找我！"),
    (re.compile(r'^[？?！!。.]{1,3}$'),                     "请描述您的需求，我来帮您安排。"),
]

def _check_trivial(message: str) -> Optional[str]:
    """返回直接回复文本，或 None（需要进入 CEO 决策）"""
    msg = message.strip()
    for pattern, reply in _TRIVIAL_PATTERNS:
        if pattern.match(msg):
            return reply
    if len(msg) <= 2:
        return "请描述您的具体需求，我来为您安排执行。"
    return None


# ── Layer 2：向量历史召回（Qdrant，~50ms）────────────────────

class RouteVectorCache:
    """
    把历史成功路由存入 Qdrant，新请求先向量检索。
    命中置信度 > 0.92：直接复用历史 dispatch_plan（跳过 CEO LLM）
    命中置信度 0.75-0.92：作为 CEO Prompt 的参考上下文
    """
    COLLECTION = "routing_history"
    CONFIDENCE_REUSE   = 0.92
    CONFIDENCE_CONTEXT = 0.75

    def __init__(self):
        self._memory = None
        self._collection_ready = False

    async def _ensure_collection(self):
        if self._collection_ready:
            return
        try:
            from molib.infra.memory.qdrant_client import MolinMemory
            from qdrant_client.models import VectorParams, Distance
            self._memory = MolinMemory()
            existing = [c.name for c in self._memory.client.get_collections().collections]
            if self.COLLECTION not in existing:
                self._memory.client.create_collection(
                    self.COLLECTION,
                    vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
                )
                logger.info(f"[SemanticRouter] 创建向量集合: {self.COLLECTION}")
            self._collection_ready = True
        except Exception as e:
            logger.warning(f"[SemanticRouter] Qdrant 不可用 ({e})，Layer 2 禁用")

    async def search_similar(self, user_input: str, top_k: int = 3) -> List[Tuple[RouteHistoryEntry, float]]:
        await self._ensure_collection()
        if not self._memory:
            return []
        try:
            vec = self._memory._embed(user_input)
            results = self._memory.client.search(
                collection_name=self.COLLECTION,
                query_vector=vec,
                limit=top_k,
                score_threshold=self.CONFIDENCE_CONTEXT,
                with_payload=True,
            )
            entries = []
            for r in results:
                payload = r.payload or {}
                entry = RouteHistoryEntry(
                    user_input=payload.get("user_input", ""),
                    dispatch_plan=payload.get("dispatch_plan", []),
                    outcome=payload.get("outcome", "success"),
                    agencies_used=payload.get("agencies_used", []),
                )
                entries.append((entry, r.score))
            return entries
        except Exception as e:
            logger.warning(f"[RouteVectorCache] 搜索失败: {e}")
            return []

    async def record_success(self, user_input: str, dispatch_plan: List[Dict], agencies_used: List[str]):
        await self._ensure_collection()
        if not self._memory:
            return
        try:
            from qdrant_client.models import PointStruct
            vec = self._memory._embed(user_input)
            entry_id = int(hashlib.md5(f"{user_input}{time.time()}".encode()).hexdigest()[:8], 16) % (10 ** 9)
            self._memory.client.upsert(
                collection_name=self.COLLECTION,
                points=[PointStruct(
                    id=entry_id,
                    vector=vec,
                    payload={
                        "user_input":    user_input,
                        "dispatch_plan": dispatch_plan,
                        "agencies_used": agencies_used,
                        "outcome":       "success",
                        "timestamp":     time.time(),
                    }
                )]
            )
            logger.debug(f"[RouteVectorCache] 路由历史已记录: {agencies_used}")
        except Exception as e:
            logger.warning(f"[RouteVectorCache] 记录失败: {e}")


# ── Layer 3：子公司能力画像匹配（兜底）─────────────────────

class CapabilityProfileMatcher:
    """
    每个子公司的能力画像 = 自然语言能力描述向量化。
    新任务找不到高置信度路由时，计算与各子公司能力向量的余弦相似度。
    """

    INITIAL_PROFILES = {
        "ip":       "撰写小红书文案、公众号推文、抖音脚本、品牌内容、创意标题",
        "research": "市场调研、平台分析、竞品研究、行业报告、需求评估、机会挖掘",
        "dev":      "代码开发、技术架构、API设计、Bug修复、系统搭建、自动化脚本",
        "data":     "数据分析、指标计算、ROI分析、漏斗分析、用户行为数据、报表",
        "growth":   "用户增长、裂变活动、获客策略、A/B测试、转化优化、渠道运营",
        "product":  "产品规划、需求文档、功能设计、SaaS化、产品标准化、MVP",
        "ai":       "AI方案、Prompt工程、RAG系统、Agent设计、知识库、大模型应用",
        "order":    "外包接单、项目报价、能力评估、交付方案、客户承接、工作量估算",
        "ads":      "广告投放、付费获客、素材创意、CAC优化、投放策略、广告数据",
        "finance":  "财务分析、成本核算、预算管理、利润计算、现金流分析",
        "legal":    "合同审查、版权保护、知识产权、法律合规、协议起草",
        "crm":      "私域运营、复购策略、用户生命周期、会员体系、用户分层",
        "secure":   "安全合规、审批流程、风险评估、广告法合规、内容审核",
        "edu":      "教育产品、课程设计、招生策略、训练营、知识付费运营",
        "cs":       "客户服务、投诉处理、售后支持、FAQ设计、用户答疑",
        "knowledge": "知识管理、文档整理、SOP建设、Wiki、复盘归档",
        "bd":       "商务拓展、合作谈判、渠道合作、资源置换、商务方案",
        "global_market": "出海业务、海外市场、本地化、多语言内容、台湾市场",
        "devops":   "运维部署、监控告警、CI/CD、服务器管理、故障排查",
        "shop":     "私域销售、成交话术、电商运营、转化优化、价格策略",
    }

    def __init__(self):
        self._memory = None

    def _get_memory(self):
        if not self._memory:
            try:
                from molib.infra.memory.qdrant_client import MolinMemory
                self._memory = MolinMemory()
            except Exception as e:
                logger.warning(f"[CapabilityMatcher] Qdrant 不可用: {e}")
        return self._memory

    async def top_matches(self, user_input: str, top_n: int = 3) -> List[Tuple[str, float]]:
        mem = self._get_memory()
        if not mem:
            return []
        try:
            user_vec = mem._embed(user_input)
            scores = []
            for agency_id, desc in self.INITIAL_PROFILES.items():
                agency_vec = mem._embed(desc)
                dot = sum(a * b for a, b in zip(user_vec, agency_vec))
                norm_u = sum(x ** 2 for x in user_vec) ** 0.5
                norm_a = sum(x ** 2 for x in agency_vec) ** 0.5
                score = dot / (norm_u * norm_a) if norm_u * norm_a > 0 else 0.0
                scores.append((agency_id, score))
            scores.sort(key=lambda x: x[1], reverse=True)
            return scores[:top_n]
        except Exception as e:
            logger.warning(f"[CapabilityMatcher] 匹配失败: {e}")
            return []


# ── 语义路由器主类（四层整合）──────────────────────────

class SemanticRouter:
    """
    四层语义路由器，替代 IntentProcessor.AGENCY_KEYWORDS 关键词路由。
    集成到 CEOReasoningLoop，在 CEO LLM 决策前/后使用。
    """

    def __init__(self):
        self._cache   = RouteVectorCache()
        self._matcher = CapabilityProfileMatcher()

    async def route(
        self,
        user_input:    str,
        session_context: str = "",
        history:       List[Dict] = None,
    ) -> RouteDecision:
        """四层路由主入口"""
        start = time.time()
        history = history or []

        # ── Layer 0：Trivial 过滤 ──
        trivial_reply = _check_trivial(user_input)
        if trivial_reply:
            return RouteDecision(
                dispatch_plan=[], confidence=1.0,
                route_source="trivial_filter",
                is_trivial=True, trivial_reply=trivial_reply,
                latency_ms=(time.time()-start)*1000,
            )

        # ── Layer 2：向量历史召回（先查缓存）──
        similar = await self._cache.search_similar(user_input, top_k=3)
        cache_context = ""
        if similar:
            best_entry, best_score = similar[0]
            if best_score >= RouteVectorCache.CONFIDENCE_REUSE:
                logger.info(f"[SemanticRouter] 路由缓存命中 score={best_score:.3f}，直接复用")
                return RouteDecision(
                    dispatch_plan=best_entry.dispatch_plan,
                    confidence=best_score,
                    route_source="vector_cache",
                    ceo_response=f"根据历史相似案例，为您安排：{', '.join(best_entry.agencies_used)}",
                    latency_ms=(time.time()-start)*1000,
                )
            elif best_score >= RouteVectorCache.CONFIDENCE_CONTEXT:
                cache_context = "参考历史相似案例：\n"
                for entry, score in similar[:2]:
                    agencies = ", ".join(entry.agencies_used)
                    cache_context += f"- 「{entry.user_input[:40]}」→ 使用了 {agencies}\n"

        # ── Layer 3：能力画像兜底 ──
        capability_hints = await self._matcher.top_matches(user_input, top_n=3)
        hints_text = ""
        if capability_hints:
            hints_text = "能力向量匹配参考（供你决策参考，不强制）：\n"
            for agency_id, score in capability_hints:
                hints_text += f"  {agency_id}: {score:.3f}\n"

        # ── Layer 1：CEO LLM 语义路由决策（核心）──
        decision = await self._ceo_semantic_decision(
            user_input, session_context, history, cache_context, hints_text,
        )
        decision.latency_ms = (time.time()-start)*1000
        return decision

    async def _ceo_semantic_decision(
        self, user_input: str, session_context: str,
        history: List[Dict], cache_context: str, hints_text: str,
    ) -> RouteDecision:
        """CEO LLM 做语义路由决策"""
        from molib.core.ceo.model_router import ModelRouter
        router = ModelRouter()

        context_block = ""
        if cache_context:
            context_block += f"\n## 历史相似路由参考\n{cache_context}\n"
        if hints_text:
            context_block += f"\n## 能力匹配参考\n{hints_text}\n"
        if session_context:
            context_block += f"\n## 当前会话上下文\n{session_context}\n"

        history_block = ""
        if history:
            history_block = "\n## 对话历史\n"
            for turn in history[-4:]:
                history_block += f"用户: {turn.get('user','')}\nCEO: {turn.get('ceo','')}\n"

        full_prompt = (
            f"{context_block}{history_block}\n## 当前用户输入\n{user_input}\n\n"
            "请分析用户意图，输出 JSON 格式的路由决策（包含 dispatch_plan）。"
        )

        result = await router.call_async(
            prompt=full_prompt,
            system=_ROUTING_SYSTEM_PROMPT,
            task_type="ceo_decision",
        )
        parsed = self._parse_ceo_output(result.get("text", "{}"))
        dispatch_plan = parsed.get("dispatch_plan", [])
        return RouteDecision(
            dispatch_plan=dispatch_plan,
            confidence=0.85 if dispatch_plan else 0.3,
            route_source="ceo_llm",
            thinking=parsed.get("thinking", ""),
            ceo_response=parsed.get("response", ""),
        )

    @staticmethod
    def _parse_ceo_output(text: str) -> Dict:
        try:
            match = re.search(r'```(?:json)?\s*([\s\S]+?)\s*```', text)
            raw = match.group(1) if match else text
            return json.loads(raw)
        except Exception:
            return {"dispatch_plan": [], "thinking": text[:200]}

    async def record_route_outcome(
        self, user_input: str, dispatch_plan: List[Dict],
        agencies_used: List[str], outcome: str = "success",
    ):
        if outcome == "success":
            await self._cache.record_success(user_input, dispatch_plan, agencies_used)


# ── 路由专用 System Prompt（轻量版，不含完整能力矩阵）──────

_ROUTING_SYSTEM_PROMPT = """你是墨麟AI智能系统的语义路由器。你的职责是：分析用户意图，决定需要哪些子公司协作。

## 子公司能力矩阵（按能力描述理解，不要按字面关键词匹配）

| 子公司ID | 核心能力 | 适合场景示例 |
|---------|---------|------------|
| ip | 内容创作、文案撰写、社媒内容、脚本、标题 | 小红书文案、公众号推文、抖音脚本、品牌故事 |
| research | 市场调研、竞品分析、行业情报、平台研究、机会评估 | 分析某平台需求、调研竞品动态、行业趋势报告 |
| dev | 技术开发、代码编写、系统架构、API设计、Bug修复 | 开发功能、写脚本、技术方案设计 |
| data | 数据分析、指标计算、报表、数据可视化、归因分析 | 分析转化率、计算ROI、生成数据报告 |
| growth | 增长策略、用户获取、营销活动、裂变设计、A/B测试 | 设计获客方案、策划裂变活动、优化转化漏斗 |
| product | 产品规划、功能设计、需求文档、产品标准化、SaaS化 | 写PRD、设计产品功能、产品路线图 |
| ai | AI方案咨询、Prompt工程、RAG系统、Agent设计、模型选型 | 设计AI工具、优化Prompt、搭建知识库 |
| edu | 教育产品、课程设计、招生策略、训练营、知识付费 | 课程规划、招生文案、训练营运营 |
| order | 外包接单、项目报价、交付方案、客户承接、工作量评估 | 评估能否接某项目、制定报价方案、交付计划 |
| shop | 私域销售、成交话术、电商运营、转化优化、价格策略 | 设计销售话术、优化成交流程 |
| secure | 安全合规、审批流程、风险评估、广告法合规 | 检查内容合规性、评估法律风险 |
| ads | 广告投放、付费获客、CAC优化、素材创意、投放策略 | 制定广告方案、优化投放ROI |
| finance | 财务分析、成本核算、预算管理、现金流、月度财报 | 分析项目利润、制定预算 |
| crm | 私域运营、用户生命周期、复购策略、会员体系 | 设计复购方案、用户分层运营 |
| knowledge | 知识管理、文档整理、SOP建设、Wiki、复盘归档 | 整理业务文档、建立SOP |
| cs | 客户服务、投诉处理、售后支持、FAQ、用户答疑 | 处理用户投诉、设计客服流程 |
| legal | 法律事务、合同审查、知识产权、版权保护 | 审查合同、处理版权问题 |
| bd | 商务拓展、合作谈判、资源置换、渠道合作 | 拓展合作渠道、准备商务方案 |
| global_market | 出海业务、台湾市场、海外本地化、多语言 | 开拓海外市场、本地化内容 |
| devops | 运维部署、监控告警、CI/CD、服务器管理 | 系统部署、性能监控、故障排查 |

## 路由决策规则
1. **理解意图，不要匹配关键词**：「猪八戒网需求梳理」→ 理解为「调研平台 + 评估接单能力 + 制定策略」→ research + order + product
2. **一个任务可以派给多个子公司**：复杂任务必须多路并发
3. **子公司协作关系**：在 task 描述中注明「基于research结果」等依赖关系
4. **不确定时派更多**：宁可多派一个协作，不要让任务缺失重要视角

## 输出格式（严格遵守 JSON）
```json
{
  "thinking": "分析用户意图和所需子公司的推理过程",
  "state_action": "dispatching",
  "response": "给用户的简洁回复",
  "dispatch_plan": [
    {
      "agency": "research",
      "task": "具体任务描述",
      "priority": "high",
      "depends_on": []
    }
  ]
}
```
"""

# 全局单例
_semantic_router: Optional[SemanticRouter] = None


def get_semantic_router() -> SemanticRouter:
    global _semantic_router
    if _semantic_router is None:
        _semantic_router = SemanticRouter()
    return _semantic_router
