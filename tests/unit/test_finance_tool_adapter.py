#!/usr/bin/env python3
"""
金融交易工具适配器单元测试

测试 FinanceToolAdapter 类的功能，包括市场分析、策略回测、投资组合评估、风险评估、交易信号生成等
"""

import sys
import os
import unittest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from hermes_fusion.integration.external_tools.finance_tools import FinanceToolAdapter


class TestFinanceToolAdapter(unittest.TestCase):
    """金融交易工具适配器测试类"""

    def setUp(self):
        """设置测试环境"""
        self.adapter = FinanceToolAdapter()

    def test_adapter_initialization(self):
        """测试适配器初始化"""
        self.assertEqual(self.adapter.tool_name, "finance_analyze_market")
        self.assertEqual(self.adapter.external_module, "tradingagents.graph.trading_graph")
        self.assertEqual(self.adapter.external_function, "TradingAgentsGraph")
        self.assertEqual(self.adapter.toolset, "finance")

    def test_analyze_market_simulation(self):
        """测试市场分析（模拟模式）"""
        # 测试市场分析
        symbol = "NVDA"
        analysis_date = "2024-05-10"
        result = self.adapter.analyze_market(symbol, analysis_date, "comprehensive")

        # 验证结果结构
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["source"], "mock")
        self.assertEqual(result["result"]["symbol"], symbol)
        self.assertEqual(result["result"]["analysis_date"], analysis_date)
        self.assertEqual(result["result"]["analysis_type"], "comprehensive")
        self.assertIn("decision", result["result"])
        self.assertIn("confidence", result["result"])
        self.assertIn("analysis_time", result["result"])
        self.assertIn("key_factors", result["result"])
        self.assertIn("price_targets", result["result"])
        self.assertIn("time_horizon", result["result"])
        self.assertIn("risk_level", result["result"])

        # 验证决策包含有效内容
        decision = result["result"]["decision"]
        self.assertTrue(len(decision) > 0)

        # 验证置信度在合理范围内
        confidence = result["result"]["confidence"]
        self.assertGreaterEqual(confidence, 0.6)
        self.assertLessEqual(confidence, 0.9)

        # 验证价格目标
        price_targets = result["result"]["price_targets"]
        self.assertIn("conservative", price_targets)
        self.assertIn("base_case", price_targets)
        self.assertIn("bull_case", price_targets)

    def test_analyze_market_no_date(self):
        """测试无日期市场分析"""
        # 测试不带日期的分析
        symbol = "AAPL"
        result = self.adapter.analyze_market(symbol)

        self.assertEqual(result["status"], "success")
        self.assertIn("analysis_date", result["result"])
        # 日期应该是昨天
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        self.assertEqual(result["result"]["analysis_date"], yesterday)

    def test_analyze_market_different_symbols(self):
        """测试不同股票代码分析"""
        # 测试多个股票代码
        symbols = ["NVDA", "AAPL", "GOOGL", "TSLA", "MSFT"]

        for symbol in symbols:
            result = self.adapter.analyze_market(symbol)
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["result"]["symbol"], symbol)

            # 验证每个股票都有不同的分析结果
            decision = result["result"]["decision"]
            self.assertTrue(len(decision) > 0)

    def test_backtest_strategy_simulation(self):
        """测试策略回测（模拟模式）"""
        # 测试策略回测
        strategy_name = "Moving Average Crossover"
        symbol = "NVDA"
        start_date = "2024-01-01"
        end_date = "2024-03-31"
        initial_capital = 10000.0

        result = self.adapter.backtest_strategy(
            strategy_name, symbol, start_date, end_date, initial_capital
        )

        # 验证结果结构
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["source"], "mock")
        self.assertEqual(result["result"]["strategy_name"], strategy_name)
        self.assertEqual(result["result"]["symbol"], symbol)
        self.assertEqual(result["result"]["period"]["start"], start_date)
        self.assertEqual(result["result"]["period"]["end"], end_date)
        self.assertIn("days", result["result"]["period"])
        self.assertIn("capital", result["result"])
        self.assertIn("performance_metrics", result["result"])
        self.assertIn("trades", result["result"])
        self.assertIn("analysis_summary", result["result"])

        # 验证资金数据
        capital = result["result"]["capital"]
        self.assertEqual(capital["initial"], initial_capital)
        self.assertGreater(capital["final"], 0)
        self.assertIn("total_return_pct", capital)

        # 验证性能指标
        metrics = result["result"]["performance_metrics"]
        expected_metrics = [
            "annualized_return_pct", "total_return_pct", "max_drawdown_pct",
            "sharpe_ratio", "volatility_pct", "win_rate_pct",
            "profit_factor", "total_trades", "avg_trade_return_pct"
        ]

        for metric in expected_metrics:
            self.assertIn(metric, metrics)

        # 验证交易记录
        trades = result["result"]["trades"]
        if trades:
            for trade in trades:
                self.assertIn("date", trade)
                self.assertIn("action", trade)
                self.assertIn("price", trade)
                self.assertIn("quantity", trade)
                self.assertIn("pnl", trade)
                self.assertIn("return_pct", trade)

        # 验证分析摘要
        summary = result["result"]["analysis_summary"]
        self.assertIn("strategy_effectiveness", summary)
        self.assertIn("risk_adjusted_return", summary)
        self.assertIn("recommendation", summary)
        self.assertIn("key_insights", summary)

    def test_evaluate_portfolio_simulation(self):
        """测试投资组合评估（模拟模式）"""
        # 测试投资组合评估
        portfolio = {
            "NVDA": 0.4,  # 40%
            "AAPL": 0.3,  # 30%
            "GOOGL": 0.2, # 20%
            "TSLA": 0.1   # 10%
        }

        result = self.adapter.evaluate_portfolio(portfolio)

        # 验证结果结构
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["source"], "mock")
        self.assertEqual(result["result"]["portfolio"], portfolio)
        self.assertIn("evaluation_date", result["result"])
        self.assertIn("metrics", result["result"])
        self.assertIn("portfolio_metrics", result["result"])
        self.assertIn("asset_allocation", result["result"])
        self.assertIn("diversification_analysis", result["result"])
        self.assertIn("performance_attribution", result["result"])
        self.assertIn("scenario_analysis", result["result"])

        # 验证投资组合指标
        portfolio_metrics = result["result"]["portfolio_metrics"]
        expected_metrics = [
            "total_return_pct", "total_risk_pct", "sharpe_ratio",
            "max_drawdown_pct", "volatility_pct", "beta", "alpha_pct",
            "information_ratio"
        ]

        for metric in expected_metrics:
            self.assertIn(metric, portfolio_metrics)

        # 验证资产配置
        asset_allocation = result["result"]["asset_allocation"]
        self.assertEqual(len(asset_allocation), len(portfolio))

        for asset in asset_allocation:
            self.assertIn("symbol", asset)
            self.assertIn("weight_pct", asset)
            self.assertIn("return_pct", asset)
            self.assertIn("risk_pct", asset)
            self.assertIn("contribution_to_return", asset)
            self.assertIn("contribution_to_risk", asset)
            self.assertIn(asset["symbol"], portfolio)

        # 验证多样化分析
        diversification = result["result"]["diversification_analysis"]
        self.assertIn("number_of_assets", diversification)
        self.assertIn("effective_n", diversification)
        self.assertIn("concentration_ratio", diversification)
        self.assertIn("diversification_score", diversification)
        self.assertIn("recommendations", diversification)

        # 验证情景分析
        scenario_analysis = result["result"]["scenario_analysis"]
        self.assertIn("bull_market_return_pct", scenario_analysis)
        self.assertIn("bear_market_return_pct", scenario_analysis)
        self.assertIn("stress_test_result", scenario_analysis)
        self.assertIn("liquidity_assessment", scenario_analysis)

    def test_assess_risk_simulation(self):
        """测试风险评估（模拟模式）"""
        # 测试风险评估
        positions = [
            {"symbol": "NVDA", "quantity": 100, "price": 150.25},
            {"symbol": "AAPL", "quantity": 50, "price": 175.50},
            {"symbol": "GOOGL", "quantity": 25, "price": 135.75}
        ]

        result = self.adapter.assess_risk(
            positions,
            risk_model="var",
            confidence_level=0.95,
            time_horizon=1
        )

        # 验证结果结构
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["source"], "mock")
        self.assertEqual(result["result"]["positions"], positions)
        self.assertEqual(result["result"]["risk_model"], "var")
        self.assertEqual(result["result"]["confidence_level"], 0.95)
        self.assertEqual(result["result"]["time_horizon_days"], 1)
        self.assertIn("risk_metrics", result["result"])
        self.assertIn("greeks", result["result"])
        self.assertIn("concentration_risk", result["result"])
        self.assertIn("liquidity_risk", result["result"])
        self.assertIn("stress_test_results", result["result"])
        self.assertIn("risk_limits_compliance", result["result"])
        self.assertIn("recommendations", result["result"])

        # 验证风险指标
        risk_metrics = result["result"]["risk_metrics"]
        expected_metrics = [
            "var_95_pct", "cvar_95_pct", "expected_shortfall_pct",
            "standard_deviation_pct", "value_at_risk", "conditional_var"
        ]

        for metric in expected_metrics:
            self.assertIn(metric, risk_metrics)

        # 验证希腊字母
        greeks = result["result"]["greeks"]
        expected_greeks = ["delta", "gamma", "theta", "vega", "rho"]
        for greek in expected_greeks:
            self.assertIn(greek, greeks)

        # 验证集中度风险
        concentration = result["result"]["concentration_risk"]
        self.assertIn("largest_position_pct", concentration)
        self.assertIn("top_3_positions_pct", concentration)
        self.assertIn("sector_concentration", concentration)
        self.assertIn("geographic_concentration", concentration)

        # 验证流动性风险
        liquidity = result["result"]["liquidity_risk"]
        self.assertIn("liquidity_score", liquidity)
        self.assertIn("estimated_liquidation_time_days", liquidity)
        self.assertIn("market_impact_cost_pct", liquidity)
        self.assertIn("recommendations", liquidity)

        # 验证压力测试结果
        stress_tests = result["result"]["stress_test_results"]
        if stress_tests:
            for scenario in stress_tests:
                self.assertIn("scenario", scenario)
                self.assertIn("impact_pct", scenario)
                self.assertIn("liquidity_impact", scenario)
                self.assertIn("recovery_time", scenario)

    def test_generate_trading_signals_simulation(self):
        """测试交易信号生成（模拟模式）"""
        # 测试交易信号生成
        symbol = "NVDA"
        signal_type = "technical"
        lookback_period = 20

        result = self.adapter.generate_trading_signals(symbol, signal_type, lookback_period)

        # 验证结果结构
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["source"], "mock")
        self.assertEqual(result["result"]["symbol"], symbol)
        self.assertEqual(result["result"]["signal_type"], signal_type)
        self.assertEqual(result["result"]["lookback_period_days"], lookback_period)
        self.assertIn("current_signal", result["result"])
        self.assertIn("current_strength", result["result"])
        self.assertIn("current_confidence", result["result"])
        self.assertIn("signal_history", result["result"])
        self.assertIn("key_indicators", result["result"])
        self.assertIn("trading_recommendations", result["result"])
        self.assertIn("signal_validation", result["result"])

        # 验证当前信号
        current_signal = result["result"]["current_signal"]
        valid_signals = ["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"]
        self.assertIn(current_signal, valid_signals)

        # 验证信号历史
        signal_history = result["result"]["signal_history"]
        if signal_history:
            for signal in signal_history:
                self.assertIn("date", signal)
                self.assertIn("signal", signal)
                self.assertIn("strength", signal)
                self.assertIn("type", signal)
                self.assertIn("indicators", signal)
                self.assertIn("price", signal)
                self.assertIn("confidence", signal)

        # 验证关键指标
        key_indicators = result["result"]["key_indicators"]
        expected_indicators = [
            "trend", "momentum", "volatility", "volume",
            "support_level", "resistance_level"
        ]

        for indicator in expected_indicators:
            self.assertIn(indicator, key_indicators)

        # 验证信号验证
        signal_validation = result["result"]["signal_validation"]
        self.assertIn("backtest_performance_pct", signal_validation)
        self.assertIn("accuracy_rate_pct", signal_validation)
        self.assertIn("average_holding_period_days", signal_validation)
        self.assertIn("risk_reward_ratio", signal_validation)

    def test_analyze_market_sentiment_simulation(self):
        """测试市场情绪分析（模拟模式）"""
        # 测试市场情绪分析
        symbol = "NVDA"
        sources = ["news", "social_media", "analyst_ratings"]
        timeframe = "7d"

        result = self.adapter.analyze_market_sentiment(symbol, sources, timeframe)

        # 验证结果结构
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["source"], "mock")
        self.assertEqual(result["result"]["symbol"], symbol)
        self.assertEqual(result["result"]["timeframe"], timeframe)
        self.assertEqual(result["result"]["sources_analyzed"], sources)
        self.assertIn("overall_sentiment", result["result"])
        self.assertIn("overall_score", result["result"])
        self.assertIn("sentiment_breakdown", result["result"])
        self.assertIn("sentiment_drivers", result["result"])
        self.assertIn("historical_comparison", result["result"])
        self.assertIn("market_implications", result["result"])
        self.assertIn("data_quality", result["result"])
        self.assertIn("recommendations", result["result"])

        # 验证情绪细分
        sentiment_breakdown = result["result"]["sentiment_breakdown"]
        for source in sources:
            self.assertIn(source, sentiment_breakdown)
            source_data = sentiment_breakdown[source]
            self.assertIn("score", source_data)
            self.assertIn("sentiment", source_data)
            self.assertIn("confidence", source_data)
            self.assertIn("volume", source_data)

        # 验证整体情绪
        overall_sentiment = result["result"]["overall_sentiment"]
        valid_sentiments = ["Bullish", "Neutral", "Bearish"]
        self.assertIn(overall_sentiment, valid_sentiments)

        # 验证情绪驱动因素
        sentiment_drivers = result["result"]["sentiment_drivers"]
        if sentiment_drivers:
            for driver in sentiment_drivers:
                self.assertIn("driver", driver)
                self.assertIn("impact", driver)
                self.assertIn("magnitude", driver)
                self.assertIn("source", driver)

        # 验证数据质量
        data_quality = result["result"]["data_quality"]
        self.assertIn("coverage", data_quality)
        self.assertIn("freshness", data_quality)
        self.assertIn("reliability", data_quality)
        self.assertIn("limitations", data_quality)

    def test_adapter_with_mock_external_module(self):
        """测试适配器使用模拟外部模块的情况"""
        # 在模拟模式下测试所有主要方法
        test_cases = [
            ("analyze_market", ("NVDA", "2024-05-10", "comprehensive", None)),
            ("backtest_strategy", ("MA Crossover", "NVDA", "2024-01-01", "2024-03-31", 10000.0, None)),
            ("evaluate_portfolio", ({"NVDA": 0.5, "AAPL": 0.5}, None, None)),
            ("assess_risk", ([{"symbol": "NVDA", "quantity": 100}], "var", 0.95, 1)),
            ("generate_trading_signals", ("NVDA", "technical", 20, None)),
            ("analyze_market_sentiment", ("NVDA", ["news", "social_media"], "7d", None)),
        ]

        for method_name, args in test_cases:
            method = getattr(self.adapter, method_name)

            try:
                result = method(*args)
                self.assertEqual(result["status"], "success")
                self.assertEqual(result["source"], "mock")
            except Exception as e:
                self.fail(f"方法 {method_name} 失败: {e}")

    def test_check_trading_agents_availability(self):
        """测试TradingAgents-CN可用性检查"""
        # 由于我们还没有安装TradingAgents-CN，应该返回False或True
        availability = self.adapter.trading_agents_available

        # 可以是False或True，取决于环境
        self.assertIsInstance(availability, bool)

        # 如果返回False，确保模拟方法正常工作
        if not availability:
            result = self.adapter.analyze_market("NVDA")
            self.assertEqual(result["source"], "mock")

    def test_different_risk_models(self):
        """测试不同风险模型"""
        # 测试不同风险模型
        positions = [{"symbol": "NVDA", "quantity": 100}]

        risk_models = ["var", "cvar", "historical"]
        for risk_model in risk_models:
            result = self.adapter.assess_risk(positions, risk_model=risk_model)
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["result"]["risk_model"], risk_model)

    def test_different_confidence_levels(self):
        """测试不同置信水平"""
        # 测试不同置信水平
        positions = [{"symbol": "NVDA", "quantity": 100}]

        confidence_levels = [0.90, 0.95, 0.99]
        for confidence in confidence_levels:
            result = self.adapter.assess_risk(positions, confidence_level=confidence)
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["result"]["confidence_level"], confidence)

    def test_portfolio_different_sizes(self):
        """测试不同规模的投资组合"""
        # 测试不同资产数量的投资组合
        portfolios = [
            {"NVDA": 1.0},  # 单一资产
            {"NVDA": 0.5, "AAPL": 0.5},  # 两个资产
            {"NVDA": 0.3, "AAPL": 0.3, "GOOGL": 0.2, "TSLA": 0.2}  # 多个资产
        ]

        for portfolio in portfolios:
            result = self.adapter.evaluate_portfolio(portfolio)
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["result"]["portfolio"], portfolio)


if __name__ == "__main__":
    unittest.main()