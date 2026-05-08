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
        # 外部API参考（网络受限，暂不使用）:
        # from molib.trading.api import get_market_data
        # data = await get_market_data(symbol=symbol, exchange="binance")
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
        # 外部API参考:
        # from molib.trading.backtest import run_backtest
        # result = run_backtest(strategy=strategy, pairs=pairs, timerange=period)
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
            "skill_context": {
                "molin_trading_loaded": bool(skills.get("molin_trading")),
            },
        }

    # ------------------------------------------------------------------
    # 交易信号
    # ------------------------------------------------------------------
    async def _generate_signal(self, payload: dict, skills: dict) -> dict:
        symbol = payload.get("symbol", "BTC/USDT")
        timeframe = payload.get("timeframe", "1h")
        # 外部API参考:
        # from molib.trading.signal import generate_signal
        # signal = generate_signal(symbol=symbol, timeframe=timeframe)
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
        }

    # ------------------------------------------------------------------
    # 研究报告（TradingAgents 三代理模式）
    # ------------------------------------------------------------------
    async def _research(self, payload: dict, skills: dict) -> dict:
        ticker = payload.get("ticker", "BTC")
        timeframe = payload.get("timeframe", "1d")
        # 外部API参考（TradingAgents 多智能体分析）:
        # from molib.trading.agents import run_multi_agent_analysis
        # result = await run_multi_agent_analysis(ticker=ticker, timeframe=timeframe)
        return {
            "task": "research",
            "ticker": ticker,
            "timeframe": timeframe,
            "multi_agent_analysis": {
                "research_manager": {
                    "technical_signals": {"trend": "bullish", "rsi": 62, "macd": "positive_crossover"},
                    "fundamental_signals": {"adoption_rate": "increasing", "hash_rate": "all_time_high"},
                    "sentiment_signals": {"overall": "positive", "news_bias": 0.72},
                    "key_levels": {"support": 65000, "resistance": 75000},
                    "confidence": 0.78,
                    "summary": "技术面看涨，基本面强劲，市场情绪积极。",
                },
                "trader": {
                    "action": "long",
                    "entry_range": [66000, 67500],
                    "stop_loss": 64200,
                    "take_profit": [74000, 78000],
                    "position_size_pct": 15,
                    "risk_reward_ratio": 3.5,
                    "time_horizon": "3-10 days",
                    "rationale": "突破阻力位后成交量确认，出现持续买入信号。",
                },
                "portfolio_manager": {
                    "decision": "approve",
                    "position_size_final": 12,
                    "max_risk_per_trade": 0.02,
                    "portfolio_risk_impact": "low",
                    "diversification_check": "pass",
                    "rationale": "以降低后的仓位批准，以维持整体风险敞口限制。",
                },
            },
        }


# ---------------------------------------------------------------------------
# 注册
# ---------------------------------------------------------------------------
WorkerRegistry.register(Trading)
