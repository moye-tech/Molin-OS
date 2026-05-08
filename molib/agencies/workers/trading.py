"""墨投交易 Worker — 量化交易策略研究/回测/信号生成"""
from .base import SubsidiaryWorker, Task, WorkerResult, WorkerRegistry
from pathlib import Path


# ---------------------------------------------------------------------------
# 技能指令加载
# ---------------------------------------------------------------------------
def _load_skill_instructions() -> dict[str, str]:
    """加载 ~/.hermes/skills/molin-trading 和 molin-trading-agents 的核心指令"""
    skills = {}
    skill_paths = [
        ("molin-trading", Path.home() / ".hermes" / "skills" / "molin-trading" / "SKILL.md"),
        ("molin-trading-agents", Path.home() / ".hermes" / "skills" / "molin-trading-agents" / "SKILL.md"),
    ]
    for name, path in skill_paths:
        try:
            if path.exists():
                skills[name] = path.read_text(encoding="utf-8")
            else:
                skills[name] = f"# {name} — SKILL.md not found at {path}"
        except Exception as e:
            skills[name] = f"# {name} — failed to load: {e}"
    return skills


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------
class Trading(SubsidiaryWorker):
    worker_id = "trading"
    worker_name = "墨投交易"
    description = "量化交易策略研究/回测/信号解读"
    oneliner = "量化交易策略研究/回测/信号解读"

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            task_type = task.task_type
            payload = task.payload
            # 在需要时加载技能指令
            skills = _load_skill_instructions()
            skill_context = {
                "molin_trading": skills.get("molin-trading", ""),
                "molin_trading_agents": skills.get("molin-trading-agents", ""),
            }

            if task_type == "analyze_market":
                output = await self._analyze_market(payload, skill_context)
            elif task_type == "backtest":
                output = await self._backtest(payload, skill_context)
            elif task_type == "signal":
                output = await self._generate_signal(payload, skill_context)
            elif task_type == "research":
                output = await self._research(payload, skill_context)
            else:
                return WorkerResult(
                    task_id=task.task_id,
                    worker_id=self.worker_id,
                    status="error",
                    output={},
                    error=f"未知 task_type: {task_type}，支持: analyze_market, backtest, signal, research",
                )

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

    # ------------------------------------------------------------------
    # 市场分析
    # ------------------------------------------------------------------
    async def _analyze_market(self, payload: dict, skills: dict) -> dict:
        market_type = payload.get("market_type", payload.get("type", "crypto"))
        symbol = payload.get("symbol", payload.get("pair", "BTC/USDT"))

        system = (
            "你是墨投交易——AI量化交易分析师。"
            "你的专长是：市场趋势分析、技术指标解读、支撑阻力位判断、交易决策建议。"
            "请基于你掌握的金融知识分析指定市场，输出结构化分析结果。"
        )
        prompt = (
            f"请对以下市场进行技术分析和基本面分析：\n\n"
            f"市场类型：{market_type}\n"
            f"交易对/标的：{symbol}\n\n"
            f"请输出JSON格式，包含：\n"
            f"- summary（分析摘要）\n"
            f"- trend（趋势方向: bullish/bearish/neutral）\n"
            f"- rsi（RSI指标值0-100）\n"
            f"- support（支撑位价格）\n"
            f"- resistance（阻力位价格）\n"
            f"- recommendation（交易建议）\n"
            f"- confidence（置信度0-1）"
        )

        llm_result = await self.llm_chat_json(prompt, system=system)
        if llm_result:
            return {
                "task": "analyze_market",
                "market_type": market_type,
                "symbol": symbol,
                **llm_result,
                "source": "llm",
                "skill_context": {
                    "molin_trading_loaded": bool(skills.get("molin_trading")),
                    "molin_trading_agents_loaded": bool(skills.get("molin_trading_agents")),
                },
            }

        # fallback: mock 数据
        return {
            "task": "analyze_market",
            "market_type": market_type,
            "symbol": symbol,
            "summary": f"{symbol} 市场分析摘要（模拟）",
            "trend": "neutral",
            "rsi": 52,
            "support": 65000,
            "resistance": 72000,
            "recommendation": "观望，等待趋势确认",
            "source": "mock",
            "skill_context": {
                "molin_trading_loaded": bool(skills.get("molin_trading")),
                "molin_trading_agents_loaded": bool(skills.get("molin_trading_agents")),
            },
        }

    # ------------------------------------------------------------------
    # 回测
    # ------------------------------------------------------------------
    async def _backtest(self, payload: dict, skills: dict) -> dict:
        strategy = payload.get("strategy", "SampleStrategy")
        period = payload.get("period", "90d")
        pairs = payload.get("pairs", ["BTC/USDT", "ETH/USDT"])

        system = "你是量化回测分析师。请基于策略参数生成回测分析。"
        prompt = (
            f"请分析以下回测场景（模拟分析，非真实API数据）：\n\n"
            f"策略：{strategy}\n"
            f"回测周期：{period}\n"
            f"交易对：{', '.join(pairs)}\n\n"
            f"请输出JSON格式的回测结果，包含：\n"
            f"- total_return_pct（总收益率%）\n"
            f"- annual_return_pct（年化收益率%）\n"
            f"- win_rate_pct（胜率%）\n"
            f"- profit_factor（盈亏比）\n"
            f"- max_drawdown_pct（最大回撤%）\n"
            f"- sharpe_ratio（夏普比率）\n"
            f"- total_trades（总交易次数）\n"
            f"- avg_hold_time（平均持仓时间）\n"
            f"- analysis（分析评价）"
        )

        llm_result = await self.llm_chat_json(prompt, system=system)
        if llm_result:
            return {"task": "backtest", "strategy": strategy, "period": period, "pairs": pairs, **llm_result, "source": "llm"}

        return {
            "task": "backtest",
            "strategy": strategy,
            "period": period,
            "pairs": pairs,
            "results": {
                "total_return_pct": 12.45,
                "annual_return_pct": 45.8,
                "win_rate_pct": 65.3,
                "profit_factor": 2.31,
                "max_drawdown_pct": -8.2,
                "sharpe_ratio": 1.85,
                "total_trades": 287,
                "avg_hold_time": "4h 32m",
            },
            "source": "mock",
            "skill_context": {"molin_trading_loaded": bool(skills.get("molin_trading"))},
        }

    # ------------------------------------------------------------------
    # 交易信号
    # ------------------------------------------------------------------
    async def _generate_signal(self, payload: dict, skills: dict) -> dict:
        symbol = payload.get("symbol", "BTC/USDT")
        timeframe = payload.get("timeframe", "1h")

        system = "你是技术分析专家，擅长生成交易信号。"
        prompt = (
            f"请对以下品种生成交易信号：\n\n"
            f"交易对：{symbol}\n"
            f"时间框架：{timeframe}\n\n"
            f"请输出JSON（基于合理估算，非真实API数据）：\n"
            f"- signal（信号: BUY/SELL/HOLD）\n"
            f"- confidence（置信度0-1）\n"
            f"- entry_range（入场区间，数组）\n"
            f"- stop_loss（止损价）\n"
            f"- take_profit（止盈目标，数组）\n"
            f"- risk_reward_ratio（风险收益比）\n"
            f"- rationale（信号理由）"
        )

        llm_result = await self.llm_chat_json(prompt, system=system)
        if llm_result:
            return {"task": "signal", "symbol": symbol, "timeframe": timeframe, **llm_result, "source": "llm"}

        return {
            "task": "signal",
            "symbol": symbol,
            "timeframe": timeframe,
            "signal": "BUY",
            "confidence": 0.72,
            "entry_range": [65200, 65800],
            "stop_loss": 63800,
            "take_profit": [68500, 72000],
            "risk_reward_ratio": 3.2,
            "rationale": "RSI超卖反弹 + MACD金叉确认，成交量放大支持上涨",
            "source": "mock",
        }

    # ------------------------------------------------------------------
    # 研究报告（TradingAgents 三代理模式 + LLM）
    # ------------------------------------------------------------------
    async def _research(self, payload: dict, skills: dict) -> dict:
        ticker = payload.get("ticker", "BTC")
        timeframe = payload.get("timeframe", "1d")

        system = (
            "你是墨投交易的多智能体研究主管。你模拟三个角色：\n"
            "1. research_manager（研究经理）：技术面+基本面+情绪分析\n"
            "2. trader（交易员）：具体进场/出场/仓位建议\n"
            "3. portfolio_manager（投资组合经理）：风险评估/仓位审批\n"
            "请输出三个角色的协调分析报告。"
        )
        prompt = (
            f"请对 {ticker} 在 {timeframe} 时间框架下生成多智能体研究报告。\n\n"
            f"请输出JSON格式，包含三个角色的分析：\n"
            f"research_manager: technical_signals(趋势方向,rsi,摘要), fundamental_signals, key_levels(支撑,阻力), confidence(0-1), summary\n"
            f"trader: action(方向), entry_range(区间), stop_loss, take_profit, position_size_pct, rationale\n"
            f"portfolio_manager: decision(批准/拒绝), position_size_final, portfolio_risk_impact, diversification_check, rationale"
        )

        llm_result = await self.llm_chat_json(prompt, system=system)
        if llm_result and "multi_agent_analysis" in llm_result:
            ma = llm_result["multi_agent_analysis"]
        elif llm_result and any(k in llm_result for k in ("research_manager", "trader", "portfolio_manager")):
            ma = {
                "research_manager": llm_result.get("research_manager", {}),
                "trader": llm_result.get("trader", {}),
                "portfolio_manager": llm_result.get("portfolio_manager", {}),
            }
        else:
            ma = None

        result = {
            "task": "research",
            "ticker": ticker,
            "timeframe": timeframe,
            "multi_agent_analysis": ma or {
                "research_manager": {"technical_signals": {"trend": "bullish", "rsi": 62, "macd": "positive_crossover"}, "confidence": 0.78, "summary": "技术面看涨，基本面强劲。"},
                "trader": {"action": "long", "entry_range": [66000, 67500], "stop_loss": 64200, "take_profit": [74000, 78000], "position_size_pct": 15, "rationale": "突破阻力位后成交量确认。"},
                "portfolio_manager": {"decision": "approve", "position_size_final": 12, "max_risk_per_trade": 0.02, "portfolio_risk_impact": "low", "diversification_check": "pass", "rationale": "以降低后的仓位批准。"},
            },
            "source": "llm" if ma else "mock",
        }
        return result


# ---------------------------------------------------------------------------
# 注册
# ---------------------------------------------------------------------------
WorkerRegistry.register(Trading)
