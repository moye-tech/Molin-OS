# molin-trading-agents

**墨投 (Trading Subsidiary) — Multi-Agent Trading Analysis Framework**

A skill for orchestrating multi-agent financial analysis using the architecture from [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) ⭐65.9k (arXiv:2412.20138).

## Overview

This skill implements the **multi-agent trading analysis pattern** from TradingAgents, enabling Hermes to coordinate multiple specialized AI agents — Research Manager, Trader(s), and Portfolio Manager — for structured, multi-perspective financial analysis. Rather than running the TradingAgents project locally (which is in active development and not pip-installable), this skill **adopts its architectural pattern** for use within Hermes' own multi-agent system.

## Use Cases

Trigger this skill when the user needs:

- **Multi-dimensional financial analysis** (fundamental + technical + sentiment)
- **Multi-agent trading decision framework** for stocks or crypto
- **Structured investment research** with role-based deliberation
- **Buy/sell/hold recommendations** backed by multiple agent perspectives

## Architecture: The Three-Agent Pattern

### 1. Research Manager (`research_manager`)

**Role:** Gathers, validates, and synthesizes market intelligence.

**Responsibilities:**
- Collect and cross-reference financial data (price, volume, fundamentals)
- Perform technical analysis (trend, support/resistance, indicators like RSI, MACD, moving averages)
- Analyze market sentiment from news and social signals
- Produce a **structured research report** with cited data points

**Output:**
```json
{
  "agent": "research_manager",
  "ticker": "AAPL",
  "timeframe": "1d",
  "technical_signals": { "trend": "bullish", "rsi": 62, "macd": "positive_crossover" },
  "fundamental_signals": { "pe_ratio": 28.5, "eps_growth": "15% YoY" },
  "sentiment_signals": { "overall": "positive", "news_bias": 0.72 },
  "key_levels": { "support": 170, "resistance": 195 },
  "confidence": 0.78,
  "summary": "Bullish technical setup with strong fundamentals."
}
```

### 2. Trader (`trader`)

**Role:** Generates executable trading strategies based on Research Manager's inputs.

**Responsibilities:**
- Translate research into actionable trade plans
- Determine entry/exit points, position sizing, stop-loss/take-profit
- Evaluate risk-reward ratios
- Consider market microstructure and liquidity

**Output:**
```json
{
  "agent": "trader",
  "ticker": "AAPL",
  "action": "long",
  "entry_range": [172.50, 174.00],
  "stop_loss": 168.20,
  "take_profit": [185.00, 192.00],
  "position_size_pct": 15,
  "risk_reward_ratio": 3.2,
  "time_horizon": "3-10 days",
  "rationale": "Breakout above resistance with volume confirmation."
}
```

### 3. Portfolio Manager (`portfolio_manager`)

**Role:** Final arbiter — validates decisions against portfolio risk, diversification, and capital allocation.

**Responsibilities:**
- Assess overall portfolio exposure
- Enforce risk limits (max drawdown, concentration, VaR)
- Rank competing trade proposals from multiple traders
- Approve/reject/modify final execution plan

**Output:**
```json
{
  "agent": "portfolio_manager",
  "ticker": "AAPL",
  "decision": "approve",
  "position_size_final": 12,
  "max_risk_per_trade": 0.02,
  "portfolio_risk_impact": "low",
  "diversification_check": "pass",
  "correlation_warning": null,
  "final_order": { "side": "buy", "type": "limit", "price": 173.20, "quantity": 120 },
  "rationale": "Approved with reduced size to maintain sector exposure limits."
}
```

## Multi-Agent Workflow

The agents operate in a **pipeline with feedback loops**:

```
User Query
    ↓
Research Manager ──► Structured Research Report
    │                        ↓
    │                   Trader Agent(s)
    │                        ↓
    │               Trade Plans (1..N)
    │                        ↓
    └──────────────────► Portfolio Manager
                             ↓
                    Final Decision & Order
```

### Execution Flow

1. **Research Phase:** Research Manager analyzes all available data using configured tools (price feeds, news APIs, on-chain data, etc.)
2. **Trading Phase:** Trader proposes specific entry/exit strategies. Multiple Trader agents can run in parallel for diversification.
3. **Portfolio Phase:** Portfolio Manager validates against risk constraints and portfolio context, then issues the final decision.
4. **Recovery (optional):** If any agent fails or times out, a LangGraph-style recovery mechanism retries or escalates.

## LLM Configuration

Each agent can use a different LLM. Recommended configurations:

| Agent | Recommended Model | Notes |
|-------|-------------------|-------|
| Research Manager | DeepSeek / Claude | Strong analytical reasoning |
| Trader | GPT-4o / Gemini 2.5 Pro | Fast, action-oriented |
| Portfolio Manager | Claude / Grok | Conservative, risk-aware reasoning |

Override via agent config:
```python
{
  "research_manager": {"model": "deepseek-chat", "temperature": 0.3},
  "trader": {"model": "gpt-4o", "temperature": 0.4},
  "portfolio_manager": {"model": "claude-sonnet-4-20250514", "temperature": 0.2}
}
```

## How to Use in Hermes

### Direct Skill Invocation

```hermes
/skill molin-trading-agents analyze ticker=AAPL timeframe=1w
```

### Multi-Agent Debate

```hermes
/skill molin-trading-agents debate tickers=AAPL,TSLA,MSFT context="Earnings season, tech sector"
```

### Custom Agent Configuration

```hermes
/skill molin-trading-agents analyze ticker=BTC-USD agents=research_manager,trader,portfolio_manager recovery=true
```

## Underlying Project Reference

This skill is inspired by **[TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents)** ⭐65.9k — a multi-agent framework for quantitative trading described in the paper *TradingAgents: Multi-Agent LLM Framework for Financial Trading* (arXiv:2412.20138).

**Key references from the original project:**
- Multi-agent architecture with role specialization
- Structured JSON output contracts between agents
- LangGraph-based state management and recovery
- Backtesting fidelity with historical data replay
- Docker deployment for containerized agent execution

> **Note:** The project is in active development (v0.2.4, released 2026-04). It is **not pip-installable**. To explore the original codebase:
> ```bash
> git clone git@github.com:TauricResearch/TradingAgents.git
> cd TradingAgents
> # Requires Python 3.10+, see docs/trading.md for setup
> ```

## Example: Complete Multi-Agent Analysis

```python
# Conceptual example of how Hermes orchestrates the agents

analysis = await hermes.run_skill("molin-trading-agents", {
    "ticker": "AAPL",
    "timeframe": "1d",
    "agents": ["research_manager", "trader", "portfolio_manager"],
    "context": "Post-earnings analysis, tech sector rallying",
    "portfolio": {
        "holdings": {"AAPL": 50, "MSFT": 30, "cash": 20},
        "max_drawdown": 0.05,
        "sector_limits": {"tech": 0.4}
    }
})

# Access each agent's output
print(analysis["research_manager"]["summary"])      # Market intelligence
print(analysis["trader"]["action"])                 # Trade plan
print(analysis["portfolio_manager"]["decision"])    # Final verdict
```

## Limitations

- This skill provides the **architectural pattern and orchestration logic** — it does not include real-time market data feeds, which must be provided via Hermes tool integrations
- Not a substitute for professional financial advice
- The original TradingAgents project is research-grade and rapidly evolving; production deployments require additional testing and safeguards
- Multi-agent analysis adds latency proportional to the number of agents used

## Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ticker` | string | — | Asset symbol to analyze |
| `timeframe` | string | `1d` | Analysis timeframe |
| `agents` | list | `all` | Which agents to activate |
| `context` | string | `""` | Additional market/portfolio context |
| `portfolio` | dict | `{}` | Portfolio state for portfolio manager |
| `recovery` | bool | `true` | Enable failure recovery mechanism |
| `models` | dict | `{}` | Per-agent LLM model overrides |
