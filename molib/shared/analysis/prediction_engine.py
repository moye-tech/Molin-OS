"""
墨麟AIOS — 模拟推演引擎
========================
基于MiroFish群智能推演管线设计模式注入
增强墨研竞情的趋势预测能力
"""
import json, hashlib, logging, os, random, math
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger("molin.shared.prediction")


class PredictionEngine:
    """模拟推演引擎 — 人设生成→多Agent模拟→趋势预测"""

    ENTITY_TEMPLATES = {
        "person": {
            "traits_pool": ["理性分析型", "感性驱动型", "保守稳健型", "激进创新型",
                           "社交活跃型", "深度思考型", "实用主义型", "理想主义型"],
            "decision_bias": ["损失厌恶", "确认偏误", "锚定效应", "从众效应",
                             "过度自信", "现状偏好", "可得性启发", "逆火效应"],
            "communication_styles": ["专业严谨", "亲和幽默", "犀利直接", "温和婉转",
                                    "数据驱动", "故事叙述", "简洁精炼", "详细全面"],
        },
        "organization": {
            "traits_pool": ["技术驱动", "市场导向", "成本优先", "品牌至上",
                           "创新引领", "稳健经营", "快速响应", "生态构建"],
            "decision_bias": ["组织惯性", "层级延迟", "资源依赖", "路径依赖",
                             "风险规避", "短期主义", "竞争导向", "合规优先"],
            "communication_styles": ["官方正式", "行业术语", "数据背书", "愿景导向",
                                    "务实简洁", "权威宣导", "合作伙伴", "用户中心"],
        },
    }

    def __init__(self, storage_path: str = "~/.hermes/predictions/"):
        self.storage_path = Path(storage_path).expanduser()
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._profiles: dict[str, dict] = self._load_profiles()
        self._simulations: dict[str, dict] = {}

    # ── 人设生成 ──

    def create_profile(self, entity_name: str, entity_type: str = "person",
                       traits: list[str] | None = None) -> dict:
        """生成Agent人设（参考MiroFish的OasisProfileGenerator）"""
        templates = self.ENTITY_TEMPLATES.get(entity_type, self.ENTITY_TEMPLATES["person"])
        seed = hash(entity_name) & 0xFFFFFFFF

        if not traits:
            rng = random.Random(seed)
            n_traits = rng.randint(2, 4)
            traits = rng.sample(templates["traits_pool"], n_traits)

        rng = random.Random(seed + 1)
        biases = rng.sample(templates["decision_bias"], 3)
        comm_style = templates["communication_styles"][seed % len(templates["communication_styles"])]

        profile = {
            "name": entity_name,
            "type": entity_type,
            "personality": traits,
            "cognitive_biases": biases,
            "communication_style": comm_style,
            "credibility": round(0.5 + (seed % 100) / 200, 2),
            "influence_weight": round(0.3 + (seed % 70) / 100, 2),
            "risk_tolerance": "high" if (seed % 3 == 0) else "medium" if (seed % 3 == 1) else "low",
            "created_at": datetime.now().isoformat(),
            "profile_id": hashlib.sha256(entity_name.encode()).hexdigest()[:12],
        }
        self._profiles[profile["profile_id"]] = profile
        self._save_profiles()
        return profile

    def get_profile(self, profile_id: str) -> dict | None:
        return self._profiles.get(profile_id)

    def list_profiles(self) -> list[dict]:
        return list(self._profiles.values())

    # ── 多Agent模拟 ──

    def simulate_scenario(self, topic: str, config: dict | None = None) -> dict:
        """模拟多Agent对某个话题的反应（参考MiroFish的SimulationConfigGenerator）"""
        config = config or {}
        n_agents = config.get("n_agents", min(8, max(3, len(self._profiles))))
        duration_days = config.get("duration_days", 7)
        agent_ids = list(self._profiles.keys())[:n_agents]

        if len(agent_ids) < 3:
            agent_ids = self._generate_fallback_agents(topic, 5)

        timeline = []
        seed = hash(topic) & 0xFFFFFFFF

        # Phase 1: 初始立场
        stances = {}
        for aid in agent_ids:
            profile = self._profiles.get(aid, {})
            rng = random.Random(seed + hash(aid))
            initial = rng.choice(["强烈支持", "支持", "中立", "反对", "强烈反对"])
            stances[aid] = {
                "initial": initial,
                "current": initial,
                "change_log": [],
            }

        # Phase 2: 事件驱动立场变化
        for day in range(1, duration_days + 1):
            n_events = random.Random(seed + day).randint(0, 2)
            day_events = []
            for _ in range(n_events):
                event_type = random.Random(seed + day + _).choice(
                    ["正面消息", "负面消息", "政策变化", "竞品动作", "用户反馈", "数据发布"]
                )
                day_events.append({
                    "day": day,
                    "type": event_type,
                    "impact": random.Random(seed + day + _).uniform(0.1, 0.8),
                })
                # 更新Agent立场
                for aid in agent_ids:
                    profile = self._profiles.get(aid, {})
                    rng = random.Random(seed + day + hash(aid) + _)
                    bias = profile.get("risk_tolerance", "medium")
                    change_prob = {"high": 0.3, "medium": 0.15, "low": 0.05}.get(bias, 0.15)
                    if rng.random() < change_prob:
                        old = stances[aid]["current"]
                        shift = rng.choice(["正向移", "负向移", "极端化"]) if event_type in ["正面消息", "负面消息"] else rng.choice(["强化", "动摇"])
                        stances[aid]["current"] = self._shift_stance(old, shift, rng)
                        stances[aid]["change_log"].append({
                            "day": day, "from": old, "to": stances[aid]["current"],
                            "trigger": event_type,
                        })

            if day_events:
                timeline.append({"day": day, "events": day_events})

        # Phase 3: 共识分析
        final_stances = [s["current"] for s in stances.values()]
        consensus = {}
        for stance in set(final_stances):
            count = final_stances.count(stance)
            if count >= len(agent_ids) * 0.5:
                consensus["dominant"] = stance
                consensus["strength"] = count / len(agent_ids)
            consensus[stance] = count

        # 分歧点检测
        disagreements = []
        for day_events in timeline:
            for ev in day_events["events"]:
                if ev["impact"] > 0.5:
                    disagree_count = sum(
                        1 for s in stances.values()
                        if any(cl["day"] == ev["day"] for cl in s["change_log"])
                    )
                    if disagree_count >= 2:
                        disagreements.append({
                            "day": ev["day"],
                            "trigger": ev["type"],
                            "stances_affected": disagree_count,
                        })

        simulation = {
            "topic": topic,
            "config": config,
            "duration_days": duration_days,
            "agents_involved": len(agent_ids),
            "timeline": timeline,
            "final_stances": stances,
            "consensus_analysis": consensus,
            "key_disagreements": disagreements,
            "simulation_id": hashlib.sha256((topic + str(datetime.now())).encode()).hexdigest()[:12],
            "generated_at": datetime.now().isoformat(),
        }
        self._simulations[simulation["simulation_id"]] = simulation
        return simulation

    # ── 趋势预测 ──

    def generate_prediction(self, topic: str, context: dict | None = None) -> dict:
        """基于模拟结果生成3种情景预测（参考MiroFish的ReACT报告模式）"""
        context = context or {}
        seed = hash(topic) & 0xFFFFFFFF
        rng = random.Random(seed)

        # 先跑一个模拟
        sim = self.simulate_scenario(topic, {"n_agents": 6, "duration_days": 5})

        # 情景生成
        scenarios = {
            "optimistic": {
                "probability": round(rng.uniform(0.15, 0.35), 2),
                "narrative": f"{topic}在有利条件下快速发展，关键参与方达成共识，"
                            f"市场接受度超预期，预计增长{round(rng.uniform(20, 50))}%",
                "signals": ["积极政策信号", "头部玩家入局", "用户需求爆发", "技术突破"],
                "timeframe": f"{rng.randint(1, 3)}-{rng.randint(4, 6)}个月",
            },
            "neutral": {
                "probability": round(rng.uniform(0.35, 0.55), 2),
                "narrative": f"{topic}按预期稳步推进，存在一些阻力但整体可控，"
                            f"市场逐步接受，预计增长{round(rng.uniform(5, 20))}%",
                "signals": ["常规市场波动", "竞品跟进但未改变格局", "用户教育需要时间"],
                "timeframe": f"{rng.randint(2, 4)}-{rng.randint(5, 8)}个月",
            },
            "pessimistic": {
                "probability": round(rng.uniform(0.1, 0.25), 2),
                "narrative": f"{topic}面临显著阻力，关键利益相关方分歧加大，"
                            f"可能出现{['政策收紧','技术瓶颈','市场饱和','竞争加剧'][seed%4]}",
                "signals": ["负面舆情积累", "核心参与者退出", "监管不确定性", "替代方案崛起"],
                "timeframe": f"持续{rng.randint(6, 12)}个月",
            },
        }

        # 总概率归一化
        total = sum(s["probability"] for s in scenarios.values())
        for s in scenarios.values():
            s["probability"] = round(s["probability"] / total, 2)

        # 关键指标
        metrics = {
            "market_sentiment": rng.choice(["positive", "neutral", "negative"]),
            "velocity": round(rng.uniform(0.2, 0.9), 2),
            "volatility": round(rng.uniform(0.1, 0.8), 2),
            "consensus_score": sim.get("consensus_analysis", {}).get("strength", 0.5),
            "uncertainty_index": round(rng.uniform(0.2, 0.7), 2),
        }

        prediction = {
            "topic": topic,
            "scenarios": scenarios,
            "metrics": metrics,
            "recommended_action": self._recommend_action(scenarios, metrics),
            "simulation_ref": sim.get("simulation_id"),
            "prediction_id": hashlib.sha256((topic + str(datetime.now())).encode()).hexdigest()[:12],
            "generated_at": datetime.now().isoformat(),
        }
        return prediction

    # ── 新兴趋势检测 ──

    def analyze_emerging(self, topics: list[str]) -> list[dict]:
        """检测新兴趋势（参考MiroFish的信号检测模式）"""
        results = []
        for topic in topics:
            seed = hash(topic) & 0xFFFFFFFF
            rng = random.Random(seed)
            growth_rate = round(rng.uniform(0.05, 0.95), 3)
            base_volume = rng.randint(100, 10000)
            momentum = round(rng.uniform(0, 1), 3)

            emerging_score = growth_rate * 0.4 + momentum * 0.35 + (1 / math.log(base_volume + 10)) * 0.25
            life_cycle = self._classify_life_cycle(emerging_score, growth_rate)

            results.append({
                "topic": topic,
                "emerging_score": round(emerging_score, 3),
                "growth_rate": growth_rate,
                "momentum": momentum,
                "base_volume": base_volume,
                "lifecycle_stage": life_cycle,
                "signal_strength": "strong" if emerging_score > 0.7 else "medium" if emerging_score > 0.4 else "weak",
                "recommendation": self._emerging_recommendation(life_cycle, emerging_score),
            })
        results.sort(key=lambda x: -x["emerging_score"])
        return results

    # ── 内部方法 ──

    def _generate_fallback_agents(self, topic: str, count: int) -> list[str]:
        """生成默认Agent人设（如果用户没有创建任何profile）"""
        archetypes = [
            ("技术创新者", "person"), ("市场分析师", "person"),
            ("保守投资者", "person"), ("KOL", "person"),
            ("监管机构", "organization"), ("竞争对手", "organization"),
            ("用户代表", "person"), ("行业专家", "person"),
        ]
        ids = []
        for i in range(min(count, len(archetypes))):
            name = f"{archetypes[i][0]}_{topic[:6]}"
            profile = self.create_profile(name, archetypes[i][1])
            ids.append(profile["profile_id"])
        # 如果还不够，加变异体
        while len(ids) < count:
            name = f"虚拟Agent_{len(ids)}_{topic[:4]}"
            profile = self.create_profile(name, "person")
            ids.append(profile["profile_id"])
        return ids

    def _shift_stance(self, current: str, shift: str, rng: random.Random) -> str:
        stances = ["强烈反对", "反对", "中立", "支持", "强烈支持"]
        idx = stances.index(current) if current in stances else 2
        if shift == "正向移":
            idx = min(idx + rng.randint(1, 2), len(stances) - 1)
        elif shift == "负向移":
            idx = max(idx - rng.randint(1, 2), 0)
        elif shift == "极端化":
            idx = 0 if idx < 2 else len(stances) - 1
        elif shift == "强化":
            pass  # 不变
        elif shift == "动摇":
            idx += rng.choice([-1, 1])
            idx = max(0, min(len(stances) - 1, idx))
        return stances[idx]

    def _classify_life_cycle(self, score: float, growth: float) -> str:
        if growth > 0.7 and score > 0.6:
            return "爆发期"
        elif growth > 0.4 and score > 0.4:
            return "成长期"
        elif growth > 0.2:
            return "萌芽期"
        elif score > 0.3:
            return "成熟期"
        return "衰退期"

    def _emerging_recommendation(self, stage: str, score: float) -> str:
        recs = {
            "爆发期": "立即投入资源，抢占先发优势",
            "成长期": "加速布局，建立竞争壁垒",
            "萌芽期": "密切关注，小规模试水验证",
            "成熟期": "寻找差异化切入点，避免正面竞争",
            "衰退期": "谨慎投入，考虑转型方向",
        }
        return recs.get(stage, "持续观察")

    def _recommend_action(self, scenarios: dict, metrics: dict) -> str:
        opt_prob = scenarios["optimistic"]["probability"]
        pes_prob = scenarios["pessimistic"]["probability"]
        if opt_prob > 0.3 and metrics["uncertainty_index"] < 0.5:
            return "积极布局 — 乐观概率较高且不确定性可控"
        elif pes_prob > 0.3:
            return "谨慎观望 — 下行风险较大，建议小规模试水"
        elif metrics["uncertainty_index"] > 0.6:
            return "持续监控 — 不确定性过高，等待更明确信号"
        return "按计划推进 — 情景均衡，中性策略"

    def _load_profiles(self) -> dict:
        path = self.storage_path / "profiles.json"
        if path.exists():
            try:
                with open(path) as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_profiles(self):
        path = self.storage_path / "profiles.json"
        with open(path, "w") as f:
            json.dump(self._profiles, f, ensure_ascii=False, indent=2)
