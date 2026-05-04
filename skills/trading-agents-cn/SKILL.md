---
name: trading-agents-cn
description: 中文金融多智能体交易框架 — 基于 hsliuping/TradingAgents-CN (25K⭐) 的中文增强版。行情分析→多Agent决策→交易策略生成。墨投（量化交易）核心引擎。
version: 1.0.0
tags: [trading, finance, multi-agent, chinese, stock, investment, strategy]
category: business
metadata:
  hermes:
    source: https://github.com/hsliuping/TradingAgents-CN
    stars: 25000
    upstream_fork: https://github.com/moye-tech/TradingAgents-CN
    based_on: https://github.com/TauricResearch/TradingAgents (64K⭐)
    molin_owner: 墨投（量化交易）
---

# TradingAgents-CN — 墨投中文交易引擎

## 概述

**TradingAgents-CN** 是 TradingAgents 的中文增强版，基于多智能体LLM的中文金融交易框架。墨投的核心引擎——从"有定位没产品"升级为"有核心引擎可出产品"。

与已有的 Hermes `trading-agents` skill（TauricResearch 英文版）的区别：
- ✅ **中文支持**：全面汉化，适配 A 股/港股/中文新闻
- ✅ **完整管线**：行情接入 → 多Agent分析 → 策略生成 → 执行建议
- ✅ **本地数据**：支持通联数据/东方财富/Tushare 等中文数据源

## 架构

```
行情数据（Tushare/Akshare/东方财富）
    │
    ▼
┌─────────────────────────────────────┐
│ 多智能体分析层 (Multi-Agent Layer)  │
├────────────────┬────────────────┬───┤
│ 基本面Agent    │ 技术面Agent    │   │
│ (财报/估值/ROE)│ (K线/均线/MACD) │   │
├────────────────┼────────────────┤   │
│ 情绪面Agent    │ 风险控制Agent  │   │
│ (新闻/舆情/研报)│ (回撤/仓位/止损)│   │
├────────────────┴────────────────┤   │
│ 策略合成器 (Strategy Synthesizer)│   │
└────────────────┬─────────────────┘   │
                 ▼                      │
┌────────────────────────────────┐      │
│ 策略输出 (Signal/Buy-Sell/Hold)│      │
└────────────────────────────────┘      │
```

## 四个Agent视角

### 1. 基本面Agent（A股适配）
```python
analysis_focus = {
    "财报分析": "营收/利润/现金流增长率",
    "估值判断": "PE/PB/PS 历史分位数",
    "行业对比": "同行业财务指标排名",
    "机构持仓": "北向资金/基金持仓变化",
    "分红情况": "股息率/分红率"
}
```

### 2. 技术面Agent（A股指标）
```python
technical_indicators = {
    "趋势指标": "MA5/MA10/MA20/MA60, MACD, DMI",
    "震荡指标": "KDJ, RSI, WR, BOLL",
    "量价关系": "量比, 换手率, 资金流向",
    "形态识别": "头肩顶/底, 双底, 突破确认"
}
```

### 3. 情绪面Agent（中文舆情）
```python
sentiment_sources = {
    "新闻情绪": "东方财富/同花顺/财联社",
    "社交舆情": "雪球/微博/股吧热帖",
    "研报观点": "券商研报摘要/评级变化",
    "政策解读": "证监会/央行/国务院政策",
}
```

### 4. 风控Agent
```python
risk_params = {
    "仓位管理": "单票≤20%, 行业≤40%",
    "止损规则": "日内-5%, 波段-10%",
    "回撤控制": "最大回撤≤15%",
    "黑名单": "ST/问题股/立案调查股"
}
```

## 策略输出格式

```python
strategy_output = {
    "symbol": "000001.SZ",
    "name": "平安银行",
    "signal": "BUY",  # BUY/SELL/HOLD
    "confidence": 0.75,  # 0-1
    "price_range": {"current": 12.5, "target": 15.0, "stop_loss": 11.0},
    "analysis": {
        "fundamental": {"score": 7.5, "summary": "营收增长稳健，估值处于历史低位"},
        "technical": {"score": 6.8, "summary": "MACD金叉，放量突破MA60"},
        "sentiment": {"score": 7.2, "summary": "北向资金持续加仓，研报看好"},
        "risk": {"score": 6.0, "summary": "大盘系统性风险需关注"}
    },
    "timeframe": "中短线（1-3个月）",
    "action_plan": "建议分3批建仓，每下跌3%加仓一次"
}
```

## 快速上手

```bash
# 查看项目源码
cd ~/TradingAgents-CN

# 文件结构
app/           # Web应用
cli/           # 命令行工具
config/        # 配置（数据源/模型/策略）
data/          # 数据模块
```

## 集成到墨麟

```python
# 使用场景1: 单票分析
result = await trading_agents_cn.analyze_stock("000001.SZ")

# 使用场景2: 大盘判断
result = await trading_agents_cn.market_overview(market="SH")

# 使用场景3: 策略生成
strategy = await trading_agents_cn.generate_strategy(
    symbols=["000001.SZ", "600519.SH"],
    capital=100000,
    horizon="mid"
)
```

## 与已有 trading-agents 技能的关系

本技能是 **trading-agents** 的中文增强版：
- 英文版（TauricResearch）：多视角金融分析框架
- 中文版（hsliuping）：完整的中文金融交易管线
- **使用建议**：分析港股美股用 trading-agents，分析A股用 trading-agents-cn
