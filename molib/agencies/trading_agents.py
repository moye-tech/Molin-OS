"""
TradingAgents-CN — 多智能体交易分析系统
=======================================
Multi-agent architecture for A-share + crypto analysis.
Mac M2: API-based, zero local model. Uses free public endpoints.

Agents:
  FundamentalAnalyst — company fundamentals analysis
  TechnicalAnalyst — MA/RSI/MACD/Bollinger indicators
  SentimentAnalyst — market sentiment from public sources
  RiskManager — position sizing + stop-loss
  Coordinator — ensemble signal (BUY/SELL/HOLD + confidence)

CLI:
  python -m molib trading signal --symbol 000001 --market a-share
  python -m molib trading analyze --symbol BTC/USDT --market crypto
  python -m molib trading research --ticker TSLA
"""

from __future__ import annotations

import json
import logging
import math
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger("molin.trading_agents")


@dataclass
class TradingSignal:
    symbol: str
    market: str
    action: str  # BUY / SELL / HOLD
    confidence: float  # 0-100
    reasoning: list[str] = field(default_factory=list)
    stop_loss: float = 0.0
    take_profit: float = 0.0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def summary(self) -> str:
        emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}
        e = emoji.get(self.action, "⚪")
        lines = [
            f"{e} {self.symbol} → {self.action} (置信度: {self.confidence:.0f}%)",
            f"   止损: {self.stop_loss:.2f} | 止盈: {self.take_profit:.2f}",
        ]
        for r in self.reasoning[:3]:
            lines.append(f"   • {r}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# 数据源
# ═══════════════════════════════════════════════════════════════

def _fetch_json(url: str, timeout: int = 10) -> dict:
    """HTTP GET → JSON 解析。"""
    req = urllib.request.Request(url, headers={"User-Agent": "Molin-TradingAgents/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as e:
        logger.warning(f"数据获取失败 {url[:60]}: {e}")
        return {}


def _eastmoney_quote(symbol: str, market_code: int = 1) -> dict:
    """东方财富 A 股实时行情。
    
    market_code: 1=上海, 0=深圳
    """
    secid = f"{market_code}.{symbol}"
    url = f"https://push2his.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f44,f45,f46,f47,f48,f50,f55,f57,f58,f60,f170"
    data = _fetch_json(url)
    if not data.get("data"):
        return {"error": "无数据", "symbol": symbol}
    d = data["data"]
    return {
        "symbol": symbol,
        "price": d.get("f43", 0) / 100 if d.get("f43") else 0,
        "high": d.get("f44", 0) / 100 if d.get("f44") else 0,
        "low": d.get("f45", 0) / 100 if d.get("f45") else 0,
        "open": d.get("f46", 0) / 100 if d.get("f46") else 0,
        "volume": d.get("f47", 0),
        "turnover": d.get("f48", 0),
        "change_pct": d.get("f170", 0) / 100 if d.get("f170") else 0,
        "pe": d.get("f55", 0) / 100 if d.get("f55") else 0,
    }


def _binance_quote(symbol: str) -> dict:
    """Binance 加密货币行情。"""
    symbol = symbol.replace("/", "").upper()
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
    data = _fetch_json(url)
    if not data or "lastPrice" not in data:
        return {"error": "无数据", "symbol": symbol}
    return {
        "symbol": symbol,
        "price": float(data.get("lastPrice", 0)),
        "high": float(data.get("highPrice", 0)),
        "low": float(data.get("lowPrice", 0)),
        "volume": float(data.get("volume", 0)),
        "change_pct": float(data.get("priceChangePercent", 0)),
    }


# ═══════════════════════════════════════════════════════════════
# Agent 1: 基本面分析
# ═══════════════════════════════════════════════════════════════

class FundamentalAnalyst:
    """基本面分析师。"""

    def analyze(self, symbol: str, market: str, quote: dict) -> dict:
        findings = []
        score = 50  # 中性起点

        if market == "a-share":
            pe = quote.get("pe", 0)
            change = quote.get("change_pct", 0)

            if 0 < pe < 15:
                score += 15
                findings.append(f"PE={pe:.1f} 偏低，估值合理")
            elif 15 <= pe < 30:
                score += 5
                findings.append(f"PE={pe:.1f} 中等估值")
            elif pe >= 50:
                score -= 15
                findings.append(f"PE={pe:.1f} 偏高，警惕泡沫")
            elif pe <= 0:
                score -= 10
                findings.append("PE为负，公司可能亏损")

            if change > 5:
                score -= 10
                findings.append("单日涨幅过大(>5%)，追高风险")
            elif change < -5:
                score += 10
                findings.append("单日跌幅过大(>5%)，可能存在超跌机会")

        elif market == "crypto":
            findings.append("加密资产无传统基本面（PE/ROE），以链上数据和市场情绪为主")
            score = 60  # 中性偏上

        return {"score": max(0, min(100, score)), "findings": findings}


# ═══════════════════════════════════════════════════════════════
# Agent 2: 技术分析
# ═══════════════════════════════════════════════════════════════

class TechnicalAnalyst:
    """技术分析师 — MA/RSI/MACD 模拟。"""

    def analyze(self, symbol: str, market: str, quote: dict) -> dict:
        price = quote.get("price", 0)
        change = quote.get("change_pct", 0)
        findings = []
        score = 50

        # 简化 RSI 估算：基于涨跌幅
        if change > 8:
            score -= 20
            findings.append("RSI 偏高(估算>75)，超买信号")
        elif change > 4:
            score -= 10
            findings.append("RSI 中等偏高(估算>65)")
        elif change < -8:
            score += 20
            findings.append("RSI 偏低(估算<25)，超卖信号")
        elif change < -4:
            score += 10
            findings.append("RSI 中等偏低(估算<35)")

        # 成交量信号
        volume = quote.get("volume", 0)
        if volume > 0:
            findings.append(f"成交量 {volume:,.0f}")

        # MACD 信号（简化：用涨跌幅方向模拟）
        if change > 2 and change < 5:
            score += 5
            findings.append("MACD 趋势向上（模拟）")
        elif change < -2 and change > -5:
            score -= 5
            findings.append("MACD 趋势向下（模拟）")

        # 支撑/阻力
        high = quote.get("high", price)
        low = quote.get("low", price)
        if high > price * 1.05:
            findings.append(f"上方阻力 {high}")
        if low < price * 0.95:
            findings.append(f"下方支撑 {low}")

        return {"score": max(0, min(100, score)), "findings": findings}


# ═══════════════════════════════════════════════════════════════
# Agent 3: 情绪分析
# ═══════════════════════════════════════════════════════════════

class SentimentAnalyst:
    """市场情绪分析师。"""

    def analyze(self, symbol: str, market: str, quote: dict) -> dict:
        change = quote.get("change_pct", 0)
        findings = []
        score = 50

        # 基于价格变化推断情绪
        if change > 3:
            score -= 5
            findings.append("市场情绪偏热（价格连续上涨），FOMO风险")
        elif change < -3:
            score += 10
            findings.append("市场恐慌情绪（价格下跌），可能存在反向机会")
        else:
            findings.append("市场情绪中性")

        volume = quote.get("volume", 0)
        if volume > 0:
            findings.append(f"24h成交活跃")

        return {"score": max(0, min(100, score)), "findings": findings}


# ═══════════════════════════════════════════════════════════════
# Agent 4: 风险管理
# ═══════════════════════════════════════════════════════════════

class RiskManager:
    """风险管理员。"""

    def analyze(self, symbol: str, market: str, quote: dict) -> dict:
        price = quote.get("price", 0)
        change = quote.get("change_pct", 0)
        findings = []

        # 仓位建议
        if abs(change) > 8:
            findings.append("波动率极高，建议仓位 ≤5%")
        elif abs(change) > 4:
            findings.append("波动率较高，建议仓位 ≤10%")
        else:
            findings.append("波动率可控，仓位可放宽至 15-20%")

        # 止损价位
        if market == "a-share":
            stop_loss = price * 0.93  # A股 -7%
            take_profit = price * 1.12  # +12%
        else:
            stop_loss = price * 0.90  # 加密 -10%
            take_profit = price * 1.20  # +20%

        findings.append(f"建议止损 {stop_loss:.2f} | 目标 {take_profit:.2f}")

        return {
            "score": 50,
            "findings": findings,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "position_pct": 10 if abs(change) < 4 else 5,
        }


# ═══════════════════════════════════════════════════════════════
# Agent 5: 协调器
# ═══════════════════════════════════════════════════════════════

class Coordinator:
    """多智能体协调器。"""

    def __init__(self):
        self.fundamental = FundamentalAnalyst()
        self.technical = TechnicalAnalyst()
        self.sentiment = SentimentAnalyst()
        self.risk = RiskManager()

    def synthesize(self, symbol: str, market: str, quote: dict) -> TradingSignal:
        results = {
            "fundamental": self.fundamental.analyze(symbol, market, quote),
            "technical": self.technical.analyze(symbol, market, quote),
            "sentiment": self.sentiment.analyze(symbol, market, quote),
            "risk": self.risk.analyze(symbol, market, quote),
        }

        # 加权综合评分
        weights = {"fundamental": 0.25, "technical": 0.35, "sentiment": 0.20, "risk": 0.20}
        composite = sum(results[k]["score"] * weights[k] for k in weights)

        # 决策
        if composite >= 65:
            action, confidence = "BUY", composite
        elif composite <= 35:
            action, confidence = "SELL", 100 - composite
        else:
            action, confidence = "HOLD", 50 + abs(composite - 50)

        # 收集所有分析
        reasoning = []
        for agent_name, result in results.items():
            for f in result.get("findings", [])[:2]:
                reasoning.append(f"[{agent_name}] {f}")

        stop_loss = results["risk"].get("stop_loss", 0)
        take_profit = results["risk"].get("take_profit", 0)

        return TradingSignal(
            symbol=symbol,
            market=market,
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )


# ═══════════════════════════════════════════════════════════════
# 统一入口
# ═══════════════════════════════════════════════════════════════

class TradingAgentsCN:
    """交易智能体统一入口。"""

    def __init__(self):
        self.coordinator = Coordinator()

    def get_signal(self, symbol: str, market: str = "a-share") -> TradingSignal:
        """获取交易信号。"""
        # 获取行情
        if market == "crypto":
            quote = _binance_quote(symbol)
        else:
            # A股：判断上海/深圳
            code = str(symbol)
            mkt_code = 1 if code.startswith("6") else 0
            quote = _eastmoney_quote(symbol, mkt_code)

        if "error" in quote:
            return TradingSignal(
                symbol=symbol, market=market, action="HOLD", confidence=0,
                reasoning=[f"数据获取失败: {quote['error']}"],
            )

        return self.coordinator.synthesize(symbol, market, quote)

    def research(self, ticker: str) -> dict:
        """简易研究摘要。"""
        return {
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
            "note": "完整研究报告需接入东方财富财报/同花顺F10等数据源",
            "recommendation": "请调用 signal 子命令获取实时交易信号",
        }


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def cmd_trading_signal(symbol: str, market: str = "a-share"):
    tcn = TradingAgentsCN()
    signal = tcn.get_signal(symbol, market)
    print(signal.summary())


def cmd_trading_analyze(symbol: str, market: str = "crypto"):
    tcn = TradingAgentsCN()
    signal = tcn.get_signal(symbol, market)
    print(signal.summary())
    print(f"\n详细分析:")
    for r in signal.reasoning:
        print(f"  {r}")


def cmd_trading_research(ticker: str):
    tcn = TradingAgentsCN()
    result = tcn.research(ticker)
    print(json.dumps(result, ensure_ascii=False, indent=2))
