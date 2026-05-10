---
name: molin-trading
description: '墨投交易 — 加密货币量化交易策略开发、回测、优化、实盘管理。基于 Freqtrade 2026.4 (github.com/freqtrade/freqtrade
  ⭐34k+)。Use when: 用户需要开发量化交易策略、回测策略、参数优化、分析市场数据、管理交易机器人。支持币安/OKX/Coinbase等主流交易所。'
version: 1.0.0
author: Hermes Agent + Freqtrade
license: GPL-3.0
metadata:
  hermes:
    tags:
    - trading
    - crypto
    - quant
    - backtesting
    - freqtrade
    - bot
    - finance
    - molin
    related_skills:
    - data-science
    - agent-finance-financial-analyst
    - research
    - writing-plans
    molin_owner: 墨投（交易）
min_hermes_version: 0.13.0
---

# 墨投 · 量化交易引擎

## 概述

墨投交易基于 **Freqtrade**（开源加密货币量化交易框架，⭐34k+），提供策略开发、历史回测、参数优化和实盘管理能力。

### 核心工作流

```
策略开发 → 数据下载 → 回测 → 超参数优化 → 实盘交易
```

---

## 何时使用

- 用户说："帮我写个回测脚本"、"分析这个交易策略"
- 用户说："看看 BTC/ETH 这周走势"、"帮我选交易对"
- 用户说："我想看哪个策略收益最高"、"回测这个策略"
- 用户说："调优策略参数"、"帮我看下单子"

---

## 快速开始

### 1. 初始化环境

```bash
# 创建用户数据目录
freqtrade create-userdir --userdir ~/freqtrade/user_data

# 创建新策略
freqtrade new-strategy --userdir ~/freqtrade/user_data \
  --strategy SampleStrategy --template full
```

### 2. 新建配置文件

```bash
freqtrade new-config --userdir ~/freqtrade/user_data
# 交互式配置需回答：交易所、API Key/Secret、交易对、策略等
```

### 3. 下载回测数据

```bash
# 下载币安现货 1h K线数据
freqtrade download-data --userdir ~/freqtrade/user_data \
  --exchange binance --pairs BTC/USDT ETH/USDT \
  --timeframe 1h --days 90

# 下载多个时间周期
freqtrade download-data --userdir ~/freqtrade/user_data \
  --exchange binance --pairs ".*/USDT" \
  --timeframes 5m 15m 1h 4h 1d \
  --days 180
```

### 4. 回测策略

```bash
freqtrade backtesting --userdir ~/freqtrade/user_data \
  --strategy SampleStrategy \
  --timeframe 1h \
  --timerange 20250101-20250401
```

### 5. 超参数优化

```bash
freqtrade hyperopt --userdir ~/freqtrade/user_data \
  --strategy SampleStrategy \
  --hyperopt-loss SharpeHyperOptLoss \
  --spaces buy sell roi trailing \
  --epochs 100
```

### 6. 查看结果

```bash
# 列出回测结果
freqtrade backtesting-show --userdir ~/freqtrade/user_data

# 列出超参数优化结果
freqtrade hyperopt-list --userdir ~/freqtrade/user_data

# 查看详细超参数
freqtrade hyperopt-show --userdir ~/freqtrade/user_data -n 1
```

### 7. 可视化

```bash
# 绘制 K 线 + 指标
freqtrade plot-dataframe --userdir ~/freqtrade/user_data \
  --strategy SampleStrategy \
  --pairs BTC/USDT

# 绘制盈利曲线
freqtrade plot-profit --userdir ~/freqtrade/user_data \
  --strategy SampleStrategy
```

---

## 策略开发快速参考

### 最小策略结构

```python
# freqtrade/strategy.py
from freqtrade.strategy import IStrategy
from pandas import DataFrame

class MyStrategy(IStrategy):
    # 策略参数
    timeframe = '1h'
    minimal_roi = {"0": 0.01}         # 1% 止盈
    stoploss = -0.05                   # 5% 止损
    trailing_stop = True
    trailing_stop_positive = 0.01
    
    # 买入信号
    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe['rsi'] < 30) &         # RSI < 30 超卖
            (dataframe['volume'] > 0),         # 有成交量
            'buy'] = 1
        return dataframe
    
    # 卖出信号
    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe['rsi'] > 70) &         # RSI > 70 超买
            (dataframe['volume'] > 0),
            'sell'] = 1
        return dataframe
```

### 常用指标

| 指标 | 函数 | 典型参数 |
|:----:|:----:|:--------:|
| RSI | `ta.RSI(dataframe, timeperiod=14)` | 超卖<30, 超买>70 |
| MACD | `ta.MACD(dataframe)` | 12,26,9 |
| SMA | `ta.SMA(dataframe, timeperiod=20)` | 20, 50, 200 |
| EMA | `ta.EMA(dataframe, timeperiod=20)` | 12, 26, 200 |
| Bollinger | `ta.BBANDS(dataframe, timeperiod=20)` | 20, 2 std |
| ATR | `ta.ATR(dataframe, timeperiod=14)` | 波动率 |
| Volume SMA | `ta.SMA(dataframe['volume'], timeperiod=20)` | 成交量均值 |

### 止盈策略 (minimal_roi)

```python
minimal_roi = {
    "0": 0.10,      # 10% 收益立即卖出
    "30": 0.05,     # 30分钟后 5% 止盈
    "60": 0.03,     # 1小时后 3% 止盈
    "120": 0.01,    # 2小时后 1% 止盈
    "240": -0.05,   # 4小时后 -5% 强制止损
}
```

---

## 数据管理

```bash
# 查看已下载数据
freqtrade list-data --userdir ~/freqtrade/user_data

# 列出交易所支持的市场
freqtrade list-markets --userdir ~/freqtrade/user_data \
  --exchange binance --base USDT

# 列出交易对
freqtrade list-pairs --userdir ~/freqtrade/user_data \
  --exchange binance --base USDT --quote BTC --trading-mode spot
```

---

## 如何输出报告

回测完成后，推荐以格式化的方式展示关键指标：

| 指标 | 值 | 说明 |
|:----:|:---:|:----:|
| 总收益率 | +12.45% | 回测期间的账户总增长率 |
| 年化收益率 | +45.8% | 年化后收益率 |
| 胜率 | 65.3% | 盈利交易占比 |
| 盈利因子 | 2.31 | 总盈利/总亏损 |
| 最大回撤 | -8.2% | 最大回撤比例 |
| Sharpe比率 | 1.85 | 风险调整后收益(>1好, >2优秀) |
| 总交易次数 | 287 | 回测期间总交易数 |
| 平均持有时间 | 4h 32m | 持仓平均时长 |

---

## 常见陷阱

1. **过拟合** — 不要用大量参数优化去拟合历史数据；用样本外数据验证
2. **未来函数** — 确保策略不使用未来数据（如用"明天的收盘价"做当前决策）
3. **忽略滑点** — 实盘滑点会吃掉策略利润；回测时设置 0.1%-0.15% 滑点
4. **单一时间框架** — 用多时间框架确认信号（如 1h 看趋势, 15m 找入场）
5. **忽略手续费** — 币安现货 0.1%，合约 maker 0.02%/taker 0.04%
6. **买卖逻辑不对称** — 确保买入条件不重复触发，卖出条件有明确规则
7. **小样本验证** — 至少 100 笔交易才有统计意义

---

## 验证清单

- [ ] freqtrade 已安装 (`pip list | grep freqtrade`)
- [ ] 已创建用户目录 (`freqtrade create-userdir`)
- [ ] 配置文件已创建 (`freqtrade new-config`)
- [ ] 回测数据已下载 (`freqtrade download-data`)
- [ ] 策略文件已编写并测试通过
- [ ] 回测结果已分析并记录
- [ ] 关键指标(收益率/胜率/回撤/Sharpe)已报告

---

## 参考

- Freqtrade 官方文档: https://www.freqtrade.io/
- GitHub: https://github.com/freqtrade/freqtrade
- 支持的交易所: binance, okx, coinbase, kraken, bybit, kucoin, gate.io 等 50+
- 目前支持的交易模式: spot (现货), futures (合约)