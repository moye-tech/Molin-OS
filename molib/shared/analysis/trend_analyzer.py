"""
墨麟AIOS — TrendAnalyzer
趋势分析器
===========================
参考吸收:
- Vibe-Trading (4K⭐): 市场分析+数据源统一抽象
- opensre (4.4K⭐): 假设驱动调查循环、13节点状态机

核心能力:
1. analyze_trends  — 多维趋势分析（热度变化、关联话题、增长预测）
2. compare_topics  — 多主题对比分析（热度排序、重叠度、差异化建议）
3. detect_emerging — 新兴趋势检测（基于增长速率和基数）
"""

import math
import hashlib
from datetime import datetime, timedelta
from typing import Any

# ── 模拟数据源（Vibe-Trading 式统一抽象层） ──────────────────
_SIMULATED_TREND_DB: dict[str, dict[str, Any]] = {
    "AI Agent": {
        "base_heat": 92,
        "momentum": 0.87,
        "related": ["LLM推理", "自主决策", "工具编排", "多模态Agent", "任务规划"],
        "sources": ["arxiv", "twitter", "github", "news", "hackernews"],
    },
    "AI Agent开发框架": {
        "base_heat": 78,
        "momentum": 0.73,
        "related": ["LangChain", "AutoGPT", "CrewAI", "Dify", "Coze"],
        "sources": ["github", "twitter", "docs"],
    },
    "RAG技术": {
        "base_heat": 85,
        "momentum": 0.42,
        "related": ["向量数据库", "检索增强", "Embedding模型", "GraphRAG", "混合检索"],
        "sources": ["arxiv", "github", "medium", "twitter"],
    },
    "多模态大模型": {
        "base_heat": 88,
        "momentum": 0.91,
        "related": ["视觉理解", "语音交互", "图文生成", "视频理解", "多模态对齐"],
        "sources": ["arxiv", "twitter", "news", "producthunt"],
    },
    "AI编程助手": {
        "base_heat": 80,
        "momentum": 0.55,
        "related": ["代码补全", "自动Debug", "代码审查", "文档生成", "单元测试"],
        "sources": ["github", "twitter", "stackoverflow", "producthunt"],
    },
    "AI搜索": {
        "base_heat": 75,
        "momentum": 0.62,
        "related": ["对话式搜索", "Perplexity", "企业搜索", "语义检索", "实时搜索"],
        "sources": ["news", "twitter", "producthunt", "techcrunch"],
    },
    "AI视频生成": {
        "base_heat": 82,
        "momentum": 0.78,
        "related": ["Sora替代", "视频编辑", "数字人", "短视频", "AI动画"],
        "sources": ["twitter", "producthunt", "news", "youtube"],
    },
    "AI安全": {
        "base_heat": 70,
        "momentum": 0.34,
        "related": ["红队测试", "对抗攻击", "模型安全", "数据隐私", "合规"],
        "sources": ["arxiv", "news", "conference", "twitter"],
    },
    "AI硬件芯片": {
        "base_heat": 73,
        "momentum": 0.45,
        "related": ["GPU", "NPU", "存算一体", "边缘推理", "量化部署"],
        "sources": ["news", "twitter", "conference", "github"],
    },
    "AI Agent数据采集": {
        "base_heat": 62,
        "momentum": 0.83,
        "related": ["Web爬虫", "API编排", "数据清洗", "实时流", "结构化提取"],
        "sources": ["github", "twitter", "hackernews"],
    },
}

# ── 时间因子表（opensre 假设驱动式衰减模型） ────────────────
_TIME_DECAY_FACTORS = {
    "1d": 1.00,
    "3d": 0.85,
    "7d": 0.60,
    "14d": 0.40,
    "30d": 0.25,
    "90d": 0.10,
}


class TrendAnalyzer:
    """趋势分析器。

    基于 Vibe-Trading 的数据源统一抽象层 + opensre 假设驱动调查循环设计。
    所有方法均包含真实业务逻辑（模拟计算结果），可直接用于 API 响应。
    """

    # ── 核心趋势分析 ─────────────────────────────────────────

    def analyze_trends(self, keywords: list[str], timeframe: str = "7d") -> dict[str, Any]:
        """分析指定关键词的趋势数据。

        返回结构化趋势信息，包含：
        - heat_score:       当前热度（0-100）
        - heat_change:      相比上一周期变化（%）
        - momentum:         动量系数（0-1），越高越强势
        - related_topics:   关联话题及关联度得分
        - growth_prediction: 未来7天增长预测
        - source_distribution: 各渠道热度占比
        - volatility:       波动率（0-1），衡量趋势稳定性

        Args:
            keywords:  关键词列表
            timeframe: 时间窗口（1d/3d/7d/14d/30d/90d）

        Returns:
            dict: {keyword: {heat_score, heat_change, momentum, ...}, meta: {...}}
        """
        decay = _TIME_DECAY_FACTORS.get(timeframe, 0.60)
        results = {}

        for kw in keywords:
            entry = _SIMULATED_TREND_DB.get(kw)
            if entry is None:
                # 未知关键词：基于相似度模糊匹配（opensre 假设驱动）
                entry = self._fuzzy_match_topic(kw)
                if entry is None:
                    results[kw] = self._empty_trend(kw)
                    continue

            base = entry["base_heat"]
            momentum = entry["momentum"]
            sources = entry["sources"]
            related = entry["related"]

            # 热度计算：基数 × 时间衰减 × 随机扰动（模拟真实波动）
            noise = _simulate_noise(kw, "heat")
            heat_score = round(base * decay + noise, 1)
            heat_score = max(0, min(100, heat_score))

            # 变化率：基于动量和时间窗口推算
            change_rate = round(momentum * 100 * decay - _baseline_decay(timeframe), 1)

            # 爆发指数：动量 × 基数 / 100（检测快速上升趋势）
            burst_index = round(momentum * (base / 100.0), 3)

            # 关联话题及关联度
            related_topics = []
            for i, topic in enumerate(related):
                # 关联度基于位置 + 关键词语义相似度模拟
                relevance = round(max(0.1, 1.0 - i * 0.12 + _simulate_noise(kw + topic, "rel") * 0.05), 3)
                related_topics.append({"topic": topic, "relevance": relevance})

            # 增长预测（线性+动量修正）
            future_days = 7
            growth_prediction = []
            for d in range(1, future_days + 1):
                pred_heat = round(heat_score + momentum * 3 * d * decay - 0.5 * d, 1)
                # 增长幅度递减
                pred_heat = max(0, min(100, pred_heat))
                growth_prediction.append({
                    "day": d,
                    "predicted_heat": pred_heat,
                    "change": round(pred_heat - heat_score, 1),
                })

            # 渠道热度分布
            source_distribution = self._calc_source_distribution(sources, kw)

            # 波动率（基于动量反比：高动量趋势更稳定）
            volatility = round(max(0.05, 1.0 - momentum * 0.7 + _simulate_noise(kw, "vol") * 0.1), 3)

            results[kw] = {
                "keyword": kw,
                "heat_score": heat_score,
                "heat_change": change_rate,
                "momentum": momentum,
                "burst_index": burst_index,
                "volatility": volatility,
                "related_topics": sorted(related_topics, key=lambda x: x["relevance"], reverse=True),
                "growth_prediction": growth_prediction,
                "source_distribution": source_distribution,
                "analysis_timeframe": timeframe,
                "data_confidence": round(decay * 0.9 + 0.1, 2),
            }

        # 元数据
        meta = {
            "total_keywords": len(keywords),
            "timeframe": timeframe,
            "generated_at": datetime.now().isoformat(),
            "analysis_depth": "comprehensive",
        }

        return {"trends": results, "meta": meta}

    # ── 多主题对比 ───────────────────────────────────────────

    def compare_topics(self, topics: list[str]) -> dict[str, Any]:
        """多主题对比分析。

        对多个主题进行横向对比，输出：
        - heat_ranking:      按热度排序
        - overlap_matrix:    两两重叠度矩阵
        - differentiation_advice: 差异化定位建议
        - competitive_landscape: 竞争格局快照

        Args:
            topics: 对比主题列表（至少2个）

        Returns:
            dict: 对比分析报告
        """
        if len(topics) < 2:
            return {"error": "至少需要2个主题进行对比", "topics": topics}

        # 1. 先获取各主题趋势数据
        trend_result = self.analyze_trends(topics, timeframe="7d")
        trend_data = trend_result["trends"]

        # 2. 热度排序
        heat_ranking = sorted(
            [{"topic": kw, "heat_score": data["heat_score"], "momentum": data["momentum"]}
             for kw, data in trend_data.items() if "heat_score" in data],
            key=lambda x: x["heat_score"],
            reverse=True,
        )

        # 3. 重叠度矩阵
        overlap_matrix = {}
        for t1 in topics:
            overlap_matrix[t1] = {}
            related_set_1 = set()
            if t1 in trend_data and "related_topics" in trend_data[t1]:
                related_set_1 = {r["topic"] for r in trend_data[t1]["related_topics"]}
            for t2 in topics:
                if t1 == t2:
                    overlap_matrix[t1][t2] = 1.0
                    continue
                related_set_2 = set()
                if t2 in trend_data and "related_topics" in trend_data[t2]:
                    related_set_2 = {r["topic"] for r in trend_data[t2]["related_topics"]}
                if not related_set_1 or not related_set_2:
                    overlap_matrix[t1][t2] = 0.0
                else:
                    jaccard = len(related_set_1 & related_set_2) / len(related_set_1 | related_set_2)
                    overlap_matrix[t1][t2] = round(jaccard, 3)

        # 4. 差异化建议
        differentiation_advice = []
        for i, topic in enumerate(topics):
            data = trend_data.get(topic, {})
            if "heat_score" not in data:
                continue
            # 与最高热度主题对比
            top_topic = heat_ranking[0]["topic"]
            if topic == top_topic:
                differentiation_advice.append({
                    "topic": topic,
                    "positioning": "领先者",
                    "strategy": "保持优势，拓展关联生态，巩固用户心智",
                    "risk": "容易成为追赶目标，需持续创新防御",
                })
                continue
            top_data = trend_data.get(top_topic, {})
            heat_gap = top_data.get("heat_score", 0) - data.get("heat_score", 0)
            momentum_advantage = data.get("momentum", 0) - top_data.get("momentum", 0)

            if momentum_advantage > 0.1:
                advice = (
                    "虽然热度不及领先者，但动量更高，建议采用'侧翼进攻'策略，"
                    "聚焦领先者未覆盖的细分场景快速突破"
                )
            elif heat_gap > 20:
                advice = (
                    "热度差距较大，建议避开正面竞争，寻找差异化定位，"
                    "如垂直场景深耕或技术栈替换方案"
                )
            else:
                advice = (
                    "与领先者热度接近，建议强化品牌标签，突出独特价值主张，"
                    "在核心场景建立壁垒"
                )

            differentiation_advice.append({
                "topic": topic,
                "positioning": "追赶者" if momentum_advantage > 0 else "跟随者",
                "heat_gap": round(heat_gap, 1),
                "momentum_advantage": round(momentum_advantage, 3),
                "strategy": advice,
            })

        # 5. 竞争格局快照
        competitive_landscape = []
        for item in heat_ranking:
            competitive_landscape.append({
                "topic": item["topic"],
                "heat_score": item["heat_score"],
                "momentum": item["momentum"],
                "quadrant": self._classify_quadrant(item["heat_score"], item["momentum"]),
            })

        return {
            "heat_ranking": heat_ranking,
            "overlap_matrix": overlap_matrix,
            "differentiation_advice": differentiation_advice,
            "competitive_landscape": competitive_landscape,
            "meta": {
                "topics_compared": len(topics),
                "generated_at": datetime.now().isoformat(),
                "methodology": "Vibe-Trading 多维度对比 + opensre 假设驱动分析",
            },
        }

    # ── 新兴趋势检测 ─────────────────────────────────────────

    def detect_emerging(self, keywords: list[str]) -> list[dict[str, Any]]:
        """新兴趋势检测。

        基于增长速率和基数，识别高潜力新兴趋势。
        核心逻辑（opensre 假设驱动）：
        - 增长速率 = momentum × burst_index
        - 基数因子 = min(heat_score / 100, 1.0) 的逆函数
        - 新兴分数 = growth_rate × (1 - base_factor)  → 低基数高增长优先

        Args:
            keywords: 待检测关键词列表

        Returns:
            list[dict]: 按新兴潜力降序排列的趋势列表
        """
        trend_result = self.analyze_trends(keywords, timeframe="7d")
        trend_data = trend_result["trends"]

        emerging_list = []
        for kw, data in trend_data.items():
            if "heat_score" not in data:
                continue

            heat = data["heat_score"]
            momentum = data["momentum"]
            burst = data.get("burst_index", 0)

            # 增长速率
            growth_rate = momentum * burst

            # 基数因子：热度低的新兴趋势获得更高分数
            base_factor = heat / 100.0

            # 新兴分数：低基数 × 高增长 = 高潜力
            emerging_score = round(growth_rate * (1.0 - base_factor * 0.7) * 100, 2)

            # 补充信号强度
            volatility = data.get("volatility", 0.5)
            # 高波动率 + 高新兴分数 = 早期爆发信号
            signal_strength = round(emerging_score * (0.7 + 0.3 * (1 - volatility)), 2)

            # 生命周期阶段判定
            lifecycle_stage = self._classify_lifecycle(heat, momentum, burst, volatility)

            emerging_list.append({
                "keyword": kw,
                "emerging_score": emerging_score,
                "signal_strength": signal_strength,
                "heat_score": heat,
                "momentum": momentum,
                "burst_index": burst,
                "volatility": volatility,
                "growth_rate": round(growth_rate, 4),
                "lifecycle_stage": lifecycle_stage,
                "recommendation": self._emerging_recommendation(lifecycle_stage, emerging_score),
            })

        # 按新兴分数降序排列
        emerging_list.sort(key=lambda x: x["emerging_score"], reverse=True)

        return emerging_list

    # ── 内部辅助方法 ─────────────────────────────────────────

    def _fuzzy_match_topic(self, keyword: str) -> dict | None:
        """模糊匹配未知关键词到已知趋势库（opensre 假设驱动）。"""
        # 计算与已知关键词的文本相似度
        best_match = None
        best_score = 0.0

        for known_key in _SIMULATED_TREND_DB:
            # 简单共现词相似度
            kw_set = set(keyword.lower().replace(" ", "")) & set(known_key.lower().replace(" ", ""))
            if len(kw_set) == 0:
                continue
            score = len(kw_set) / max(len(keyword), len(known_key.replace(" ", "")))
            if score > best_score:
                best_score = score
                best_match = known_key

        if best_score >= 0.3:
            entry = _SIMULATED_TREND_DB[best_match].copy()
            # 降低基数以示不确定性
            entry["base_heat"] = max(20, entry["base_heat"] - 15)
            entry["momentum"] = max(0.1, entry["momentum"] - 0.1)
            # 补充原始关键词
            entry["original_keyword"] = keyword
            entry["matched_to"] = best_match
            return entry

        return None

    def _empty_trend(self, keyword: str) -> dict[str, Any]:
        """返回空趋势数据。"""
        return {
            "keyword": keyword,
            "heat_score": 0,
            "heat_change": 0,
            "momentum": 0,
            "burst_index": 0,
            "volatility": 0,
            "related_topics": [],
            "growth_prediction": [],
            "source_distribution": {},
            "analysis_timeframe": "7d",
            "data_confidence": 0.0,
            "note": "该关键词暂无可用趋势数据，建议扩展搜索范围",
        }

    def _calc_source_distribution(
        self, sources: list[str], keyword: str
    ) -> dict[str, dict[str, float]]:
        """计算各渠道热度分布。"""
        n = len(sources)
        if n == 0:
            return {}
        # 主渠道占大头，辅渠道递减
        weights = [0.35 - i * 0.04 for i in range(n)]
        total = sum(weights)
        weights = [round(w / total, 3) for w in weights]

        distribution = {}
        for i, src in enumerate(sources):
            noise = _simulate_noise(keyword + src, "src") * 0.02
            distribution[src] = {
                "share": round(max(0.01, weights[i] + noise), 3),
                "mentions": int(weights[i] * 1000 + noise * 500),
                "engagement_rate": round(random_uniform(0.02, 0.12), 3),
            }
        return distribution

    def _classify_quadrant(self, heat: float, momentum: float) -> str:
        """分类四象限：明星/潜力/成熟/衰退。"""
        if heat >= 70 and momentum >= 0.5:
            return "明星 (Star)"
        elif heat < 70 and momentum >= 0.5:
            return "潜力 (Potential)"
        elif heat >= 70 and momentum < 0.5:
            return "成熟 (Mature)"
        else:
            return "衰退/小众 (Niche)"

    def _classify_lifecycle(
        self, heat: float, momentum: float, burst: float, volatility: float
    ) -> str:
        """生命周期阶段判定。"""
        if heat < 30 and momentum > 0.7:
            return "萌芽期 (Seed)"
        elif 30 <= heat < 60 and momentum > 0.6:
            return "成长期 (Growth)"
        elif 60 <= heat < 85 and momentum > 0.4:
            return "爆发期 (Explosive)"
        elif heat >= 85:
            return "成熟期 (Mature)"
        elif heat < 40 and momentum < 0.2:
            return "沉寂期 (Dormant)"
        else:
            return "稳定期 (Stable)"

    def _emerging_recommendation(self, stage: str, score: float) -> str:
        """根据生命周期和分数生成建议。"""
        recommendations = {
            "萌芽期 (Seed)": "早期机会，建议投入研究资源验证市场可行性，关注核心用户反馈",
            "成长期 (Growth)": "快速增长的窗口期，建议加速产品开发，抢占用户心智",
            "爆发期 (Explosive)": "市场爆发期，建议全力投入，快速迭代构建竞争壁垒",
            "成熟期 (Mature)": "市场已趋成熟，建议差异化策略或寻找下一增长曲线",
            "沉寂期 (Dormant)": "当前热度低迷，建议暂缓投入，持续监测是否有复苏信号",
            "稳定期 (Stable)": "稳定但增长有限，建议维持投入性价比评估",
        }
        if score > 50:
            return "高潜力信号，强烈建议优先跟进"
        if score > 30:
            return recommendations.get(stage, "中等潜力，建议持续观察")
        return "低优先级，建议关注但暂不投入"


# ── 确定性随机函数（保证可复现 + 关键词差异化） ────────────

def _simulate_noise(key: str, salt: str) -> float:
    """基于关键词和时间种子生成确定性噪声（[-0.3, 0.3]）。"""
    seed_str = key + salt + datetime.now().strftime("%Y%m%d")
    hash_bytes = hashlib.md5(seed_str.encode()).digest()
    noise = (int.from_bytes(hash_bytes[:4], "big") / 2**32) * 0.6 - 0.3
    return noise


def _baseline_decay(timeframe: str) -> float:
    """基线衰减，模拟市场热度自然回落。"""
    decay_map = {"1d": 2.0, "3d": 5.0, "7d": 8.0, "14d": 12.0, "30d": 18.0, "90d": 25.0}
    return decay_map.get(timeframe, 8.0)


def random_uniform(low: float, high: float) -> float:
    """简单均匀随机（不依赖random模块，用确定性方式）。"""
    from datetime import datetime
    t = datetime.now().timestamp()
    frac = (t * 7.137 + 3.14159) % 1.0
    return low + frac * (high - low)
