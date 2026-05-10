"""墨研竞情 Worker — 竞争情报 + 群体智能预测（基于MiroFish设计模式）
v2.0: SmartSubsidiaryWorker + 上下文注入（历史经验+链路上下文）
"""
from .base import SmartSubsidiaryWorker as _Base, Task, WorkerResult


class Research(_Base):
    worker_id = "research"
    worker_name = "墨研竞情"
    description = "竞品监控、行业情报与群体智能预测"
    oneliner = "从情报采集到趋势预测，以群体智能辅助决策"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "竞品监控与竞争力分析",
            "行业趋势扫描与热点追踪",
            "群体智能预测（基于MiroFish设计模式）",
            "情报日报生成与自动推送",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨研竞情",
            "vp": "战略",
            "description": "竞品监控、行业情报与群体智能预测",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            action = task.payload.get("action", "analyze")
            domain = task.payload.get("domain", "AI Agent")
            topic = task.payload.get("topic", "")
            context_info = task.payload.get("context", "")
            competitors = task.payload.get("competitors", [])

            # ── v2.0: 上下文注入 ──
            exp_hint = (context or {}).get("exp_hint", "")
            chain_ctx = task.payload.get("__context__", "")

            # 构建增强上下文（传给子方法）
            enriched_ctx = context_info
            if exp_hint:
                enriched_ctx = f"{context_info}\n【历史成功经验】\n{exp_hint}"
            if chain_ctx:
                enriched_ctx = f"{enriched_ctx}\n【上游协作背景】\n{chain_ctx}"

            if action == "predict":
                # 群体智能预测（基于MiroFish设计模式）
                try:
                    from molib.intelligence.predictor import predict
                    result = await predict(
                        topic=topic or domain,
                        context=enriched_ctx,
                        num_agents=task.payload.get("num_agents", 5),
                    )
                    output = {
                        "action": "prediction",
                        "topic": result["topic"],
                        "num_agents": result["num_agents"],
                        "final_report": result["final_report"],
                        "confidence_avg": result["confidence_avg"],
                        "source": "predictor",
                    }
                except Exception:
                    # fallback: LLM生成预测
                    output = await self._llm_predict(topic or domain, enriched_ctx)
            elif action == "trending":
                output = await self._analyze_trends(domain, enriched_ctx)
            elif action == "trend_scan":
                # ── v2.0: ContentWriter 主动调用的热词扫描 ──
                output = await self._trend_scan(topic or domain, task.payload.get("platform", ""))
            else:
                output = await self._analyze_competitors(competitors, domain, enriched_ctx)

            return WorkerResult(
                task_id=task.task_id,
                worker_id=self.worker_id,
                status="success",
                output=output,
            )
        except Exception as e:
            return WorkerResult(
                task_id=task.task_id,
                worker_id=self.worker_id,
                status="error",
                output={"error": str(e)},
            )

    async def _trend_scan(self, topic: str, platform: str) -> dict:
        """v2.0: 热词/趋势扫描 — 供 ContentWriter 等协作调用"""
        system = (
            "你是墨研竞情——墨麟AI集团旗下的竞争情报与战略研究子公司。"
            "请对给定主题进行快速热词/趋势扫描，输出可用于内容创作的洞察。"
        )
        prompt = (
            f"请扫描以下主题在{platform or '全网'}的热词和趋势：\n\n"
            f"主题：{topic}\n\n"
            f"请输出JSON格式，包含：\n"
            f"- summary（一句话趋势摘要）\n"
            f"- hot_keywords（热词列表，每项含 word 和热度高/中/低）\n"
            f"- trending_angles（热门切入角度列表）\n"
            f"- competitor_headlines（竞品爆款标题列表）\n"
            f"- status（固定为'trend_scan_done'）"
        )
        result = await self.llm_chat_json(prompt, system=system)
        if result:
            return {**result, "source": "llm"}
        return {
            "summary": f"{topic}在{platform}上热度稳定",
            "hot_keywords": [{"word": topic, "热度": "高"}],
            "trending_angles": ["专业科普角度", "实用教程角度"],
            "status": "trend_scan_done",
            "source": "mock",
        }

    async def _analyze_competitors(self, competitors: list, domain: str, enriched_ctx: str = "") -> dict:
        system = (
            "你是墨研竞情——墨麟AI集团旗下的竞争情报与战略研究子公司。"
            "你的专长是：竞品监控与竞争力分析、行业趋势扫描与热点追踪、"
            "群体智能预测、情报日报生成。你能从碎片化信息中提炼出可行动的洞察。"
            "请输出结构化的竞品分析报告。"
        )
        if enriched_ctx:
            system += f"\n\n【增强上下文】\n{enriched_ctx}"
        prompt = (
            f"请对以下领域进行竞品分析：\n\n"
            f"领域：{domain}\n"
            f"竞品列表：{', '.join(competitors) if competitors else '未指定具体竞品，请分析该领域的典型竞品'}\n\n"
            f"请输出JSON格式，包含：\n"
            f"- action（固定为'competitor_analysis'）\n"
            f"- domain（分析领域）\n"
            f"- competitors（竞品分析数组，每项含：name名称, position市场定位, strengths优势, weaknesses劣势, threat威胁等级, market_share预估份额）\n"
            f"- key_findings（关键发现列表）\n"
            f"- strategic_recommendations（战略建议列表）\n"
            f"- status（固定为'intel_ready'）"
        )
        result = await self.llm_chat_json(prompt, system=system)
        if result:
            return {**result, "source": "llm"}
        # fallback
        return {
            "action": "competitor_analysis",
            "domain": domain,
            "competitors": [{"name": c, "threat": "medium"} for c in competitors] if competitors else [],
            "status": "intel_ready",
            "source": "mock",
        }

    async def _analyze_trends(self, domain: str, enriched_ctx: str = "") -> dict:
        system = (
            "你是墨研竞情——墨麟AI集团旗下的竞争情报与战略研究子公司。"
            "你的专长是：竞品监控与竞争力分析、行业趋势扫描与热点追踪、"
            "群体智能预测、情报日报生成。你能从碎片化信息中提炼出可行动的洞察。"
            "请输出结构化的行业趋势分析报告。"
        )
        if enriched_ctx:
            system += f"\n\n【增强上下文】\n{enriched_ctx}"
        prompt = (
            f"请对以下领域进行行业趋势分析：\n\n"
            f"领域：{domain}\n\n"
            f"请输出JSON格式，包含：\n"
            f"- action（固定为'trend_analysis'）\n"
            f"- domain（分析领域）\n"
            f"- trends（趋势数组，每项含：trend趋势名称, impact影响等级, description描述, timeframe时间范围）\n"
            f"- emerging_technologies（新兴技术/模式列表）\n"
            f"- market_dynamics（市场动态分析）\n"
            f"- strategic_implications（战略启示）\n"
            f"- status（固定为'intel_ready'）"
        )
        result = await self.llm_chat_json(prompt, system=system)
        if result:
            return {**result, "source": "llm"}
        # fallback
        return {
            "action": "trend_analysis",
            "domain": domain,
            "trends": [
                {"trend": "Agent协作主流化", "impact": "高"},
                {"trend": "成本控制关键", "impact": "高"},
            ],
            "status": "intel_ready",
            "source": "mock",
        }

    async def _llm_predict(self, topic: str, enriched_ctx: str) -> dict:
        system = (
            "你是墨研竞情——墨麟AI集团旗下的竞争情报与战略研究子公司。"
            "你采用MiroFish设计模式进行群体智能预测。请综合多角度思考，"
            "给出结构化、有深度的预测报告。"
        )
        if enriched_ctx:
            system += f"\n\n【增强上下文】\n{enriched_ctx}"
        prompt = (
            f"请对以下主题进行深度预测分析：\n\n"
            f"主题：{topic}\n"
            f"上下文：{enriched_ctx if enriched_ctx else '无额外上下文'}\n\n"
            f"请输出JSON格式，包含：\n"
            f"- action（固定为'prediction'）\n"
            f"- topic（预测主题）\n"
            f"- num_agents（使用的分析视角数量，建议3-7）\n"
            f"- perspectives（各视角分析，数组，每项含：agent_name视角名, analysis分析内容, confidence置信度0-1）\n"
            f"- final_report（综合预测报告）\n"
            f"- confidence_avg（平均置信度）\n"
            f"- key_signals（关键信号列表）\n"
            f"- uncertainties（不确定因素列表）"
        )
        result = await self.llm_chat_json(prompt, system=system)
        if result:
            return {**result, "source": "llm"}
        return {
            "action": "prediction",
            "topic": topic,
            "num_agents": 3,
            "final_report": f"关于{topic}的初步预测分析（基于模拟数据）",
            "confidence_avg": 0.7,
            "source": "mock",
        }
