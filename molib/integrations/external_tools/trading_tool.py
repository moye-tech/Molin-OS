"""
Trading Tool Integrator (TradingAgents-CN)
国内化金融情报多智能体系统，提供 A 股量化分析、行情监控和投资建议生成。
"""
from typing import Dict, Any
import os
import aiohttp
from loguru import logger
from molib.integrations.adapters.tool_adapter import ExternalToolAdapter


class TradingTool(ExternalToolAdapter):
    def __init__(self):
        super().__init__(tool_name="trading_tool")
        self.api_base = os.getenv("TRADING_TOOL_API_BASE", "http://localhost:9000")
        self.register_command("analyze_market", self._analyze_market)
        self.register_command("execute_order", self._execute_order)
        self.register_command("portfolio_review", self._portfolio_review)
        logger.info(f"TradingTool (TradingAgents-CN) initialized, API: {self.api_base}")

    async def _analyze_market(self, params: Dict[str, Any]) -> Dict[str, Any]:
        symbol = params.get("symbol", "000001")
        analysis_type = params.get("analysis_type", "technical")

        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                f"{self.api_base}/api/analyze",
                json={
                    "symbol": symbol,
                    "analysis_type": analysis_type,
                    "period": params.get("period", "daily"),
                },
                timeout=aiohttp.ClientTimeout(total=30),
            )
            data = await resp.json()

        return {
            "symbol": symbol,
            "analysis_type": analysis_type,
            "signal": data.get("signal", "neutral"),
            "confidence": data.get("confidence", 0),
            "summary": data.get("summary", ""),
        }

    async def _execute_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        approval_token = params.get("__approval_token__")
        if not approval_token:
            raise PermissionError(
                "Trading execute_order requires human approval token. "
                "Please approve via Feishu card first."
            )

        symbol = params.get("symbol")
        action = params.get("action")
        if not symbol or not action:
            raise ValueError("symbol and action parameters are required for order execution.")

        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                f"{self.api_base}/api/order",
                json={
                    "symbol": symbol,
                    "action": action,
                    "quantity": params.get("quantity", 100),
                    "order_type": params.get("order_type", "market"),
                    "approval_token": approval_token,
                },
                timeout=aiohttp.ClientTimeout(total=60),
            )
            data = await resp.json()

        return {
            "order_id": data.get("order_id"),
            "symbol": symbol,
            "action": action,
            "status": data.get("status", "submitted"),
        }

    async def _portfolio_review(self, params: Dict[str, Any]) -> Dict[str, Any]:
        portfolio = params.get("portfolio", [])
        if not portfolio:
            raise ValueError("portfolio parameter is required (list of symbols).")

        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                f"{self.api_base}/api/portfolio/review",
                json={"holdings": portfolio},
                timeout=aiohttp.ClientTimeout(total=30),
            )
            data = await resp.json()

        return {
            "total_holdings": len(portfolio),
            "risk_score": data.get("risk_score"),
            "recommendations": data.get("recommendations", []),
            "summary": data.get("summary", ""),
        }


_trading_tool = TradingTool()

def get_trading_tool() -> TradingTool:
    return _trading_tool
