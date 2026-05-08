"""
墨麟 — LLM 交易分析代理模块
============================================================
从 TradingAgents-CN (hsliuping/TradingAgents-CN 25K⭐) 提取的核心设计模式：
  1. 多Agent讨论框架 — 多个LLM Agent分别分析同一股票后汇总讨论
  2. 多周期同步 — 日线/周线/月线数据统一处理
  3. LLM适配器模式 — 多种LLM提供者的统一调用接口
  4. 多源数据同步 — akshare/tushare/baostock 等数据源的统一抽象

设计模式核心类：
  - TradingAnalysisAgent  : 单只股票的分析 Agent（市场/基本面/新闻/情绪）
  - MultiAgentPanel       : 多 Agent 讨论与共识框架
  - DataSourceAdapter     : 数据源统一适配器（抽象基类）
  - LLMAdapter            : LLM 提供者统一适配器

依赖: Python 标准库 + httpx（已装）
不依赖: MongoDB, Redis, LangChain, LangGraph

用法:
    from molib.trading.llm_trading_agent import analyze_stock
    report = analyze_stock("000001", model="deepseek/deepseek-chat")
    print(report["summary"])
"""

import json
import os
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Literal
from pathlib import Path

import httpx

# ── 常量 ──────────────────────────────────────────────────────────

DEFAULT_MODEL = "deepseek/deepseek-chat"
DEFAULT_API_BASE = "https://api.openai.com/v1"
OPENAI_COMPATIBLE_PROVIDERS = {
    "openai":       {"base_url": "https://api.openai.com/v1",              "key_env": "OPENAI_API_KEY"},
    "deepseek":     {"base_url": "https://api.deepseek.com",               "key_env": "DEEPSEEK_API_KEY"},
    "dashscope":    {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "key_env": "DASHSCOPE_API_KEY"},
}

# 时间窗口
PERIOD_MAP = {
    "daily":   {"label": "日线",  "days": 365},
    "weekly":  {"label": "周线",  "days": 365 * 2},
    "monthly": {"label": "月线",  "days": 365 * 5},
}

# ── 数据类型 ──────────────────────────────────────────────────────

Vote = Literal["bullish", "neutral", "bearish"]
Verdict = Literal["strong_bullish", "bullish", "neutral", "bearish", "strong_bearish"]
AgentRole = Literal["market", "fundamentals", "news", "sentiment", "bull", "bear", "trader"]


@dataclass
class AnalystOpinion:
    """单个分析师的判断"""
    role: AgentRole
    label: str           # 显示名称
    score: float         # 1-10
    vote: Vote           # 看涨/中性/看跌
    confidence: float    # 0-1
    reasoning: str       # 分析推理
    indicators: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisReport:
    """完整分析报告"""
    symbol: str
    name: str = ""
    timestamp: str = ""
    opinions: List[AnalystOpinion] = field(default_factory=list)
    consensus_score: float = 5.0
    consensus_verdict: Verdict = "neutral"
    summary: str = ""
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "timestamp": self.timestamp or datetime.now().isoformat(),
            "consensus_score": self.consensus_score,
            "consensus_verdict": self.consensus_verdict,
            "summary": self.summary,
            "opinions": [
                {
                    "role": o.role,
                    "label": o.label,
                    "score": o.score,
                    "vote": o.vote,
                    "confidence": o.confidence,
                    "reasoning": o.reasoning,
                    "indicators": o.indicators,
                }
                for o in self.opinions
            ],
            "error": self.error,
        }


# ── LLM 适配器（Adapter 模式） ─────────────────────────────────────

class LLMAdapter:
    """
    LLM 适配器 — 统一封装多种 LLM 提供者的 API 调用。

    从 TradingAgents-CN 提取的 design pattern:
    OpenAICompatibleBase 为基类，各供应商通过 adapter 子类实现。
    此处简化为 httpx 直连，无 LangChain 依赖。
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        timeout: int = 120,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

        # 自动推断 provider 和 base_url
        if "/" in model and base_url is None:
            provider_key = model.split("/")[0]
            provider_cfg = OPENAI_COMPATIBLE_PROVIDERS.get(provider_key)
            if provider_cfg:
                base_url = provider_cfg["base_url"]
                api_key = api_key or os.environ.get(provider_cfg["key_env"])

        self.base_url = (base_url or DEFAULT_API_BASE).rstrip("/")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")

        if not self.api_key:
            raise ValueError(
                f"API Key 未配置。请设置环境变量或传入 api_key。"
                f"当前 model={model}, base_url={self.base_url}"
            )

    def chat(self, messages: List[Dict[str, str]], system: Optional[str] = None) -> str:
        """调用 LLM 聊天补全，返回纯文本响应"""
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        # 提取真正的模型名（去掉 provider 前缀）
        model_name = self.model.split("/")[-1] if "/" in self.model else self.model

        payload = {
            "model": model_name,
            "messages": full_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"LLM API 错误 ({e.response.status_code}): {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"LLM 调用失败: {e}")


# ── 数据源适配器（Adapter 模式） ───────────────────────────────────

class DataSourceAdapter(ABC):
    """
    数据源统一适配器 — 抽象基类。

    从 TradingAgents-CN 提取:
    BaseStockDataProvider 定义统一接口，各数据源（Tushare/AKShare/BaoStock）
    通过继承实现标准化。
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def get_quotes(self, symbol: str) -> Dict[str, Any]:
        """获取当前行情"""
        ...

    @abstractmethod
    def get_historical(self, symbol: str, days: int = 365) -> List[Dict[str, Any]]:
        """获取历史 K 线"""
        ...

    @abstractmethod
    def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """获取基本面数据（PE/PB/营收等）"""
        ...


class MockDataSource(DataSourceAdapter):
    """
    模拟数据源 — 不依赖外部 API，用 mock 数据演示。
    生产环境可替换为 TushareAdapter / AKShareAdapter / BaoStockAdapter。
    """

    def __init__(self):
        super().__init__("mock")
        self._mock_prices = {
            "000001": {"name": "平安银行", "price": 11.50, "pe": 5.2, "pb": 0.65},
            "600519": {"name": "贵州茅台", "price": 1880.00, "pe": 30.5, "pb": 9.8},
            "000858": {"name": "五粮液", "price": 168.50, "pe": 22.3, "pb": 5.6},
            "300750": {"name": "宁德时代", "price": 218.00, "pe": 25.1, "pb": 4.2},
            "AAPL":   {"name": "Apple Inc.", "price": 198.50, "pe": 32.0, "pb": 48.0},
            "TSLA":   {"name": "Tesla Inc.", "price": 245.60, "pe": 55.0, "pb": 14.0},
        }

    def get_quotes(self, symbol: str) -> Dict[str, Any]:
        info = self._mock_prices.get(symbol, {"name": symbol, "price": 100.0, "pe": 15.0, "pb": 2.0})
        return {
            "symbol": symbol,
            "name": info["name"],
            "price": info["price"],
            "change_pct": round((hash(symbol + datetime.now().strftime("%Y%m%d")) % 100 - 50) / 20, 2),
            "volume": int(1e7 + hash(symbol) % 5e6),
            "timestamp": datetime.now().isoformat(),
        }

    def get_historical(self, symbol: str, days: int = 365) -> List[Dict[str, Any]]:
        base = self._mock_prices.get(symbol, {"price": 100.0})["price"]
        bars = []
        for i in range(min(days, 252)):
            date = (datetime.now() - timedelta(days=252 - i)).strftime("%Y-%m-%d")
            noise = (hash(symbol + str(i)) % 200 - 100) / 100 * base * 0.05
            close = round(base + noise, 2)
            bars.append({
                "date": date,
                "open": round(close - noise * 0.5, 2),
                "high": round(close + abs(noise) * 0.8, 2),
                "low": round(close - abs(noise) * 0.8, 2),
                "close": close,
                "volume": int(1e7 + hash(symbol + str(i)) % 5e6),
            })
        return bars

    def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        info = self._mock_prices.get(symbol, {"name": symbol, "price": 100.0, "pe": 15.0, "pb": 2.0})
        return {
            "pe_ttm": info["pe"],
            "pb": info["pb"],
            "roe": round(hash(symbol) % 3000 / 100, 1),
            "revenue_growth": round(hash(symbol + "rev") % 500 / 100, 1),
            "profit_growth": round(hash(symbol + "prf") % 400 / 100, 1),
            "market_cap": round(info["price"] * 1e9, 0),
            "dividend_yield": round(hash(symbol + "div") % 500 / 100, 2),
        }


# ── 多周期数据提取 ─────────────────────────────────────────────────

class MultiPeriodDataBuilder:
    """
    多周期数据构建器 — 统一处理日线/周线/月线。

    从 TradingAgents-CN 提取:
    MultiPeriodSyncService 的周期处理逻辑。
    """

    @staticmethod
    def build(mock_source: MockDataSource, symbol: str) -> Dict[str, Any]:
        """从原始日线数据构建多周期 K 线"""
        daily = mock_source.get_historical(symbol, days=365)
        weekly = []
        monthly = []

        # 周线: 每 5 个交易日聚合
        for i in range(0, len(daily), 5):
            chunk = daily[i:i + 5]
            if chunk:
                weekly.append(MultiPeriodDataBuilder._aggregate(chunk))

        # 月线: 每 20 个交易日聚合
        for i in range(0, len(daily), 20):
            chunk = daily[i:i + 20]
            if chunk:
                monthly.append(MultiPeriodDataBuilder._aggregate(chunk))

        return {
            "daily": daily[-30:] if len(daily) > 30 else daily,      # 近30日
            "weekly": weekly[-12:] if len(weekly) > 12 else weekly,  # 近12周
            "monthly": monthly[-6:] if len(monthly) > 6 else monthly, # 近6月
        }

    @staticmethod
    def _aggregate(bars: List[Dict]) -> Dict:
        """聚合 K 线数据"""
        return {
            "date": bars[0]["date"],
            "open": bars[0]["open"],
            "high": max(b["high"] for b in bars),
            "low": min(b["low"] for b in bars),
            "close": bars[-1]["close"],
            "volume": sum(b["volume"] for b in bars),
            "change_pct": round((bars[-1]["close"] - bars[0]["open"]) / bars[0]["open"] * 100, 2),
        }


# ── 单 Agent 分析引擎 ─────────────────────────────────────────────

class TradingAnalysisAgent:
    """
    单 Agent 分析引擎 — 针对一只股票的一种分析视角。

    从 TradingAgents-CN 提取:
    每个 Analyst（market/social/news/fundamentals）各自分析同一只股票，
    通过 LLM 调用 + 工具数据生成结构化报告。
    """

    ROLE_PROMPTS: Dict[AgentRole, str] = {
        "market": (
            "你是一位资深技术分析师。请分析以下股票的多周期技术面数据，"
            "包括趋势、支撑阻力、成交量分析、技术指标信号。"
        ),
        "fundamentals": (
            "你是一位基本面分析师。请分析以下股票的财务数据，"
            "包括估值水平、盈利能力、成长性、财务健康度。"
        ),
        "news": (
            "你是一位新闻情报分析师。请分析近期关于该股票的新闻动态、"
            "行业政策、市场情绪。"
        ),
        "sentiment": (
            "你是一位社交情绪分析师。请分析市场对该股票的情绪倾向、"
            "人气热度、社交媒体讨论。"
        ),
    }

    def __init__(self, role: AgentRole, llm: LLMAdapter):
        self.role = role
        self.llm = llm
        self.label = {
            "market": "技术分析师",
            "fundamentals": "基本面分析师",
            "news": "新闻情报分析师",
            "sentiment": "情绪分析师",
            "bull": "看多研究员",
            "bear": "看空研究员",
            "trader": "交易员",
        }.get(role, role)

    def analyze(
        self,
        symbol: str,
        name: str,
        quotes: Dict[str, Any],
        fundamentals: Dict[str, Any],
        multi_period: Dict[str, Any],
    ) -> AnalystOpinion:
        """对一只股票执行一次分析，返回结构化意见"""
        system_prompt = self.ROLE_PROMPTS.get(self.role, "你是一位金融分析师。")
        data_context = self._format_data_context(symbol, name, quotes, fundamentals, multi_period)

        user_prompt = (
            f"请分析股票 {name} ({symbol})。\n\n"
            f"【行情与基本面】\n{json.dumps(data_context, ensure_ascii=False, indent=2)}\n\n"
            f"请输出JSON格式的分析结果：\n"
            f'{{"score": 1-10的整数分, "vote": "bullish/neutral/bearish", '
            f'"confidence": 0.0-1.0, "reasoning": "分析理由", '
            f'"indicators": {{"key_factors": ["因素1", "因素2"]}}}}'
        )

        try:
            response = self.llm.chat(
                messages=[{"role": "user", "content": user_prompt}],
                system=system_prompt,
            )
            result = self._parse_llm_response(response)
            return AnalystOpinion(
                role=self.role,
                label=self.label,
                score=result.get("score", 5.0),
                vote=result.get("vote", "neutral"),
                confidence=result.get("confidence", 0.5),
                reasoning=result.get("reasoning", ""),
                indicators=result.get("indicators", {}),
            )
        except Exception as e:
            return AnalystOpinion(
                role=self.role,
                label=self.label,
                score=5.0,
                vote="neutral",
                confidence=0.3,
                reasoning=f"分析失败: {e}",
            )

    def _format_data_context(
        self, symbol: str, name: str, quotes: Dict, fundamentals: Dict, multi_period: Dict
    ) -> Dict:
        """格式化数据上下文供LLM使用"""
        return {
            "symbol": symbol,
            "name": name,
            "current_price": quotes.get("price", 0),
            "change_pct": quotes.get("change_pct", 0),
            "volume": quotes.get("volume", 0),
            "fundamentals": {
                "pe_ttm": fundamentals.get("pe_ttm"),
                "pb": fundamentals.get("pb"),
                "roe": fundamentals.get("roe"),
                "revenue_growth": fundamentals.get("revenue_growth"),
                "profit_growth": fundamentals.get("profit_growth"),
                "market_cap": fundamentals.get("market_cap"),
            },
            "multi_period_summary": {
                "daily_trend": self._trend_summary(multi_period.get("daily", [])),
                "weekly_trend": self._trend_summary(multi_period.get("weekly", [])),
                "monthly_trend": self._trend_summary(multi_period.get("monthly", [])),
            },
        }

    @staticmethod
    def _trend_summary(bars: List[Dict]) -> str:
        """简单趋势描述"""
        if not bars:
            return "数据不足"
        first = bars[0]["close"]
        last = bars[-1]["close"]
        change = (last - first) / first * 100
        if change > 5:
            return f"上升趋势 ({change:+.1f}%)"
        elif change < -5:
            return f"下降趋势 ({change:+.1f}%)"
        else:
            return f"震荡趋势 ({change:+.1f}%)"

    @staticmethod
    def _parse_llm_response(response: str) -> Dict:
        """从 LLM 响应中提取 JSON"""
        # 尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 尝试提取 JSON 块
        match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # 尝试提取 score
        score_match = re.search(r'(?:score|评分)[：:]\s*(\d+(?:\.\d+)?)', response)
        score = float(score_match.group(1)) if score_match else 5.0

        vote = "neutral"
        if re.search(r'(?:看涨|bullish|买入|BUY)', response, re.IGNORECASE):
            vote = "bullish"
        elif re.search(r'(?:看跌|bearish|卖出|SELL)', response, re.IGNORECASE):
            vote = "bearish"

        return {"score": score, "vote": vote, "confidence": 0.5, "reasoning": response[:500]}


# ── 多 Agent 讨论面板 ─────────────────────────────────────────────

class MultiAgentPanel:
    """
    多 Agent 讨论框架 — 多个 LLM Agent 分别分析后汇总讨论。

    从 TradingAgents-CN 提取:
    - LangGraph 工作流: Analyst → Bull/Bear Debate → Trader → Risk Debate
    - 此处简化为: 各 Agent 独立分析 → 共识聚合 → 讨论总结
    """

    def __init__(self, llm: LLMAdapter, roles: Optional[List[AgentRole]] = None):
        self.llm = llm
        self.roles = roles or ["market", "fundamentals", "news", "sentiment"]

    def analyze(
        self,
        symbol: str,
        name: str,
        quotes: Dict[str, Any],
        fundamentals: Dict[str, Any],
        multi_period: Dict[str, Any],
    ) -> AnalysisReport:
        """启动多 Agent 并行分析"""
        opinions: List[AnalystOpinion] = []

        # 第1阶段: 各 Agent 独立分析
        for role in self.roles:
            agent = TradingAnalysisAgent(role=role, llm=self.llm)
            opinion = agent.analyze(symbol, name, quotes, fundamentals, multi_period)
            opinions.append(opinion)

        # 第2阶段: 共识聚合
        consensus = self._compute_consensus(opinions)

        # 第3阶段: 讨论总结 — 让 LLM 做最终汇总
        summary = self._generate_summary(symbol, name, opinions, consensus)

        report = AnalysisReport(
            symbol=symbol,
            name=name,
            timestamp=datetime.now().isoformat(),
            opinions=opinions,
            consensus_score=consensus["score"],
            consensus_verdict=consensus["verdict"],
            summary=summary,
        )
        return report

    def _compute_consensus(self, opinions: List[AnalystOpinion]) -> Dict:
        """计算多 Agent 共识"""
        if not opinions:
            return {"score": 5.0, "verdict": "neutral"}

        scores = [o.score for o in opinions if o.score > 0]
        avg_score = sum(scores) / len(scores) if scores else 5.0

        # 投票加权
        votes = {"bullish": 0, "neutral": 0, "bearish": 0}
        for o in opinions:
            votes[o.vote] = votes.get(o.vote, 0) + o.confidence

        total = sum(votes.values()) or 1
        bull_ratio = votes["bullish"] / total
        bear_ratio = votes["bearish"] / total

        # 共识公式: 连续分 + 投票加权
        raw = 0.65 * (avg_score / 10 * 100) + 0.35 * (bull_ratio * 100)
        polarized = 50 + (raw - 50) * 1.3
        consensus_score = max(0, min(100, polarized))

        if consensus_score >= 75:
            verdict: Verdict = "strong_bullish"
        elif consensus_score >= 60:
            verdict = "bullish"
        elif consensus_score >= 40:
            verdict = "neutral"
        elif consensus_score >= 25:
            verdict = "bearish"
        else:
            verdict = "strong_bearish"

        return {"score": round(consensus_score, 1), "verdict": verdict}

    def _generate_summary(
        self,
        symbol: str,
        name: str,
        opinions: List[AnalystOpinion],
        consensus: Dict,
    ) -> str:
        """让 LLM 生成最终讨论总结"""
        opinions_text = "\n\n".join(
            f"【{o.label}】评分={o.score}/10, 观点={o.vote}, "
            f"信心={o.confidence:.0%}\n分析: {o.reasoning[:200]}"
            for o in opinions
        )

        prompt = (
            f"基于以下多分析师对 {name}({symbol}) 的独立分析意见，"
            f"请写一份综合讨论总结（200字以内）：\n\n"
            f"当前共识: 综合评分 {consensus['score']}/100, "
            f"判定={consensus['verdict']}\n\n{opinions_text}"
        )

        try:
            return self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                system="你是一位投资研究主管，整合各分析师意见形成最终结论。",
            )
        except Exception:
            # 降级: 简单拼接
            votes = [o.vote for o in opinions]
            bull_count = votes.count("bullish")
            return (
                f"多Agent分析完成。{len(opinions)}位分析师中 "
                f"{bull_count}人看涨, {votes.count('bearish')}人看跌, "
                f"{votes.count('neutral')}人中性。"
                f"综合评分{consensus['score']}/100，判定为{consensus['verdict']}。"
            )


# ── 外部入口函数 ───────────────────────────────────────────────────

def analyze_stock(
    symbol: str,
    model: str = DEFAULT_MODEL,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    data_source: Optional[DataSourceAdapter] = None,
    roles: Optional[List[AgentRole]] = None,
) -> Dict[str, Any]:
    """
    主入口函数 — 对单只股票执行完整的多 Agent 分析。

    参数:
        symbol: 股票代码 (如 "000001", "600519", "AAPL")
        model: LLM 模型名 (如 "deepseek/deepseek-chat")
        api_key: API Key (默认从环境变量读取)
        base_url: API 基础 URL
        data_source: 数据源适配器 (默认 MockDataSource)
        roles: 分析师角色列表 (默认市场/基本面/新闻/情绪)

    返回:
        dict — 完整分析报告
    """
    ds = data_source or MockDataSource()
    llm = LLMAdapter(model=model, api_key=api_key, base_url=base_url)

    # 获取数据
    quotes = ds.get_quotes(symbol)
    fundamentals = ds.get_fundamentals(symbol)
    multi_period = MultiPeriodDataBuilder.build(ds, symbol)
    name = quotes.get("name", symbol)

    # 多 Agent 分析
    panel = MultiAgentPanel(llm=llm, roles=roles)
    report = panel.analyze(symbol, name, quotes, fundamentals, multi_period)

    return report.to_dict()


# ── CLI 入口 ───────────────────────────────────────────────────────

def main():
    """CLI 支持: python -m molib.trading.llm_trading_agent <symbol> [--model ...]"""
    import argparse

    parser = argparse.ArgumentParser(description="LLM Trading Agent — 多Agent股票分析")
    parser.add_argument("symbol", help="股票代码 (如 000001, AAPL)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"LLM 模型 (默认 {DEFAULT_MODEL})")
    parser.add_argument("--api-key", help="API Key (默认从环境变量读取)")
    parser.add_argument("--base-url", help="API 基础 URL")
    args = parser.parse_args()

    print(f"🔍 分析 {args.symbol} 中...")
    result = analyze_stock(
        symbol=args.symbol,
        model=args.model,
        api_key=args.api_key,
        base_url=args.base_url,
    )

    print(f"\n{'='*60}")
    print(f"📊 {result['name']} ({result['symbol']}) 分析报告")
    print(f"🕐 {result['timestamp']}")
    print(f"{'='*60}")
    print(f"🎯 综合评分: {result['consensus_score']}/100 — {result['consensus_verdict']}")
    print(f"\n📝 总结:\n{result['summary']}\n")
    print(f"{'─'*40}")
    for op in result.get("opinions", []):
        print(f"  {op['label']}: {op['score']}/10 [{op['vote']}] (信心 {op['confidence']:.0%})")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
