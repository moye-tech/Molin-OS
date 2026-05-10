---
name: mo-tou
description: 墨投交易 — 量化交易 Workflow，集成 TradingAgents-CN 多角度金融分析，支持信号生成、回测、市场分析和研究
version: 0.1.0
tags: [trading, quant, finance, backtest, analysis, signal]
metadata:
  hermes:
    molin_owner: 墨投交易
    worker_path: /home/ubuntu/hermes-os/molib/agencies/workers/trading.py
    cli_command: python -m molib trading
---

# 墨投交易 — 量化交易 Workflow

## 概述

墨投交易是 Hermes OS 的量化交易子公司，负责量化交易策略研究、回测、信号生成和市场分析。

- **Worker 文件**: `molib/agencies/workers/trading.py`
- **CLI 入口**: `python -m molib trading {signal|backtest|analyze|research}`
- **物主**: 墨投交易
- **状态**: ✅ Worker 已注册到 WorkerRegistry

## CLI 命令

```bash
# 生成交易信号
python -m molib trading signal --symbol BTC/USDT

# 市场分析
python -m molib trading analyze --market-type crypto --symbol BTC/USDT

# 研究
python -m molib trading research --ticker BTC

# 回测
python -m molib trading backtest --strategy moving_average --symbol BTC/USDT
```

### 子命令详解

| 子命令 | 说明 | 示例 |
|--------|------|------|
| `signal` | 生成交易信号（买/卖/持有） | `python -m molib trading signal --symbol ETH/USDT` |
| `backtest` | 策略回测 | `python -m molib trading backtest --strategy macd --period 30d` |
| `analyze` | 市场多维度分析 | `python -m molib trading analyze --market-type crypto --symbol BTC/USDT` |
| `research` | 深度研究 | `python -m molib trading research --ticker AAPL` |

## TradingAgents-CN 集成

TradingAgents-CN 提供多角度金融分析能力，已通过 molin-trading-agents 技能加载。

### 调用方式

```python
# 通过 TradingAgents-CN 进行多角度分析
from trading_agents_cn.analyst import TradingAgents

agents = TradingAgents()
result = agents.analyze(
    symbol="BTC/USDT",
    angles=[
        "technical",     # 技术面分析
        "fundamental",   # 基本面分析
        "sentiment",     # 情绪面分析
        "onchain",       # 链上数据分析
        "macro",         # 宏观分析
    ]
)
```

### HuggingFace 模型集成

```python
# 使用 smolagents 加载金融分析模型
from smolagents import CodeAgent, HfApiModel

agent = CodeAgent(
    tools=[...],
    model=HfApiModel("Qwen/Qwen2.5-72B-Instruct")
)
```

## 量化信号生成工作流

### 完整管线

```
数据采集 → 特征工程 → 模型推理 → 信号生成 → 风险评分 → 输出
   │           │           │          │          │
   ▼           ▼           ▼          ▼          ▼
 Market     Technical  ML Model    Buy/Hold/  VaR/Sha
 Data       Indicators Inference  Sell       rpe/Risk
```

### Python 示例

```python
from molib.agencies.workers.trading import TradingWorker

worker = TradingWorker()

# 生成信号
signal = await worker.execute(
    task=Task(
        task_id="sig-001",
        task_type="signal",
        payload={"symbol": "BTC/USDT", "timeframe": "1h"}
    )
)
print(signal.output)  # {"action": "buy", "confidence": 0.78, "price": 68000}

# 市场分析
analysis = await worker.execute(
    task=Task(
        task_id="ana-001",
        task_type="analyze",
        payload={"symbol": "ETH/USDT", "metrics": ["rsi", "macd", "volume"]}
    )
)
```

## 技能依赖

以下技能需已安装：

| 技能 | 状态 | 用途 |
|------|------|------|
| `molin-trading` | ✅ 已激活 | 基础交易 CLI 命令 |
| `molin-trading-agents` | ✅ 已激活 | TradingAgents-CN 多角度分析 |

技能目录位置：
- `~/hermes-os/skills/molib/trading/` — 交易相关技能
- `~/hermes-os/skills/trading-agents-cn/` — TradingAgents-CN 集成技能

## 合规声明

> ⚠️ **重要合规声明**
>
> 本技能提供的所有分析、信号和研究仅供参考和教育目的。
> - **不提供**具体的买卖建议
> - **不构成**任何投资建议
> - 所有交易决策应由用户独立判断
> - 过往表现不代表未来收益
> - 投资有风险，决策需谨慎

## 风险提示

- 量化交易策略存在亏损风险
- 回测表现不代表实盘表现
- 市场异常波动可能导致策略失效
- 建议先用模拟盘验证策略
- 初始资金控制在可承受范围内
