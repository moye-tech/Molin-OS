"""墨研竞情 Worker — v2.1 开源武装升级 (gpt-researcher ⭐18k + firecrawl ⭐70k + STORM ⭐22k)

升级内容:
  - deep_research: GPT-Researcher 实时联网深度调研 (替代静态LLM)
  - firecrawl_search: Firecrawl 竞品文章抓取+结构分析
  - storm_report: STORM 维基百科级别深度报告
  - 保留原有 predict/trending/trend_scan/analyze 全部功能
"""
from .base import SmartSubsidiaryWorker as _Base, Task, WorkerResult


class Research(_Base):
    worker_id = "research"
    worker_name = "墨研竞情"
    description = "竞品监控、行业情报与群体智能预测（v2.1: gpt-researcher + firecrawl + STORM）"
    oneliner = "实时联网调研+竞品抓取+深度报告，从情报采集到趋势预测"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "实时联网深度调研 (gpt-researcher ⭐18k)",
            "竞品文章URL抓取与结构分析 (firecrawl ⭐70k)",
            "维基百科级别深度报告 (STORM ⭐22k)",
            "群体智能预测 (MiroFish)",
            "行业趋势扫描与热点追踪",
            "情报日报生成与自动推送",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨研竞情",
            "vp": "战略",
            "description": "实时联网调研+竞品抓取+深度报告 (v2.1 开源武装)",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            action = task.payload.get("action", "analyze")
            domain = task.payload.get("domain", "AI Agent")
            topic = task.payload.get("topic", "")
            context_info = task.payload.get("context", "")
            competitors = task.payload.get("competitors", [])

            # v2.0: 上下文注入
            exp_hint = (context or {}).get("exp_hint", "")
            chain_ctx = task.payload.get("__context__", "")

            enriched_ctx = context_info
            if exp_hint:
                enriched_ctx = f"{context_info}\n【历史成功经验】\n{exp_hint}"
            if chain_ctx:
                enriched_ctx = f"{enriched_ctx}\n【上游协作背景】\n{chain_ctx}"

            # ── v2.1 新增 Action: 实时联网深度调研 ──
            if action in ("deep_research", "联网调研", "research"):
                output = await self._deep_research(topic or domain, task.payload)

            # ── v2.1 新增 Action: 竞品URL抓取 ──
            elif action in ("firecrawl_search", "url_scrape", "scrape"):
                output = await self._firecrawl_search(task.payload)

            # ── v2.1 新增 Action: STORM深度报告 ──
            elif action in ("storm_report", "深度报告"):
                output = await self._storm_report(topic or domain)

            elif action == "predict":
                try:
                    from molib.intelligence.predictor import predict
                    result = await predict(
                        topic=topic or domain, context=enriched_ctx,
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
                    output = await self._llm_predict(topic or domain, enriched_ctx)

            elif action == "trending":
                output = await self._analyze_trends(domain, enriched_ctx)

            elif action == "trend_scan":
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

    # ══════════════════ v2.1: 开源武装 Actions ══════════════════

    async def _deep_research(self, query: str, payload: dict) -> dict:
        """GPT-Researcher 实时联网深度调研 (⭐18k)"""
        try:
            from molib.infra.external.gpt_researcher import deep_research
            depth = payload.get("depth", "medium")
            return await deep_research(query, depth=depth)
        except Exception:
            return await self._llm_fallback(query, "research")

    async def _firecrawl_search(self, payload: dict) -> dict:
        """Firecrawl 竞品抓取 (⭐70k)"""
        query = payload.get("query", payload.get("topic", ""))
        urls = payload.get("urls", [])
        try:
            from molib.infra.external.firecrawl import search_and_scrape, scrape_url
            if urls:
                results = []
                for url in urls[:5]:
                    r = scrape_url(url)
                    results.append(r)
                return {"action": "url_batch_scrape", "results": results, "count": len(results), "source": "firecrawl"}
            elif query:
                return search_and_scrape(query, limit=payload.get("limit", 5))
        except Exception:
            pass
        return {"action": "firecrawl_search", "query": query, "results": [], "source": "firecrawl_unavailable"}

    async def _storm_report(self, topic: str) -> dict:
        """STORM 维基百科级别深度报告 (⭐22k)"""
        try:
            from molib.infra.external.storm_research import storm_report
            return await storm_report(topic)
        except Exception:
            return await self._llm_fallback(topic, "storm")

    async def _llm_fallback(self, topic: str, source: str) -> dict:
        """LLM兜底：当外部工具不可用时"""
        system = "你是墨研竞情——墨麟AI集团旗下的竞争情报与战略研究子公司。请对以下主题给出深度分析。"
        prompt = f"请分析: {topic}\n\n输出JSON: action, topic, report(详细分析), key_findings(3-5条), source({source}_llm_fallback)"
        result = await self.llm_chat_json(prompt, system=system)
        if result:
            return {**result, "source": f"{source}_llm_fallback"}
        return {"action": source, "topic": topic, "report": f"关于{topic}的分析报告（LLM fallback）", "source": "fallback"}

    # ══════════════════ 原有方法 ══════════════════

    async def _trend_scan(self, topic: str, platform: str) -> dict:
        system = (
            "你是墨研竞情——墨麟AI集团旗下的竞争情报与战略研究子公司。"
            "请对给定主题进行快速热词/趋势扫描，输出可用于内容创作的洞察。"
        )
        prompt = (
            f"请扫描以下主题在{platform or '全网'}的热词和趋势：\n\n"
            f"主题：{topic}\n\n"
            f"请输出JSON格式，包含：summary, hot_keywords(含word和热度), trending_angles, competitor_headlines, status='trend_scan_done'"
        )
        result = await self.llm_chat_json(prompt, system=system)
        if result:
            return {**result, "source": "llm"}
        return {"summary": f"{topic}热度稳定", "hot_keywords": [{"word": topic, "热度": "高"}], "trending_angles": ["专业科普"], "status": "trend_scan_done", "source": "mock"}

    async def _analyze_competitors(self, competitors: list, domain: str, enriched_ctx: str = "") -> dict:
        system = "你是墨研竞情——墨麟AI集团旗下的竞争情报子公司。请输出结构化竞品分析。"
        if enriched_ctx:
            system += f"\n\n【增强上下文】\n{enriched_ctx}"
        prompt = (
            f"竞品分析：领域={domain}, 竞品={', '.join(competitors) if competitors else '典型竞品'}\n"
            f"输出JSON: action='competitor_analysis', domain, competitors(含name/position/strengths/weaknesses/threat), key_findings, strategic_recommendations, status='intel_ready'"
        )
        result = await self.llm_chat_json(prompt, system=system)
        if result:
            return {**result, "source": "llm"}
        return {"action": "competitor_analysis", "domain": domain, "competitors": [{"name": c, "threat": "medium"} for c in competitors], "status": "intel_ready", "source": "mock"}

    async def _analyze_trends(self, domain: str, enriched_ctx: str = "") -> dict:
        system = "你是墨研竞情——墨麟AI集团旗下的竞争情报子公司。请输出行业趋势分析。"
        if enriched_ctx:
            system += f"\n【增强上下文】\n{enriched_ctx}"
        prompt = (
            f"行业趋势：领域={domain}\n"
            f"输出JSON: action='trend_analysis', domain, trends(含trend/impact/description/timeframe), emerging_technologies, strategic_implications, status='intel_ready'"
        )
        result = await self.llm_chat_json(prompt, system=system)
        if result:
            return {**result, "source": "llm"}
        return {"action": "trend_analysis", "domain": domain, "trends": [{"trend": "Agent协作主流化", "impact": "高"}], "status": "intel_ready", "source": "mock"}

    async def _llm_predict(self, topic: str, enriched_ctx: str) -> dict:
        system = "你是墨研竞情，采用MiroFish设计模式进行群体智能预测。"
        if enriched_ctx:
            system += f"\n【增强上下文】\n{enriched_ctx}"
        prompt = (
            f"预测分析：主题={topic}, 上下文={enriched_ctx}\n"
            f"输出JSON: action='prediction', topic, num_agents, perspectives(含agent_name/analysis/confidence), final_report, confidence_avg, key_signals, uncertainties"
        )
        result = await self.llm_chat_json(prompt, system=system)
        if result:
            return {**result, "source": "llm"}
        return {"action": "prediction", "topic": topic, "num_agents": 3, "final_report": f"关于{topic}的预测（LLM兜底）", "confidence_avg": 0.7, "source": "mock"}
