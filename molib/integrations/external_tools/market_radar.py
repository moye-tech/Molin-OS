"""
Market Radar External Tool (seomachine & MiroFish Integration)
为增长与研究子公司提供 SEO 分析、关键词挖掘以及市场情报监控。
"""
import os
from typing import Dict, Any
from loguru import logger
from molib.integrations.adapters.tool_adapter import ExternalToolAdapter

SEOMACHINE_BASE = os.getenv("SEOMACHINE_URL", "http://localhost:7070")


class MarketRadarTool(ExternalToolAdapter):
    def __init__(self):
        super().__init__(tool_name="market_radar")
        self.register_command("analyze_seo", self._analyze_seo)
        self.register_command("gather_intelligence", self._gather_intelligence)
        logger.info("MarketRadarTool initialized (seomachine & MiroFish).")

    async def _analyze_seo(self, params: Dict[str, Any]) -> Dict[str, Any]:
        keyword = params.get("keyword", "")
        if not keyword:
            raise ValueError("keyword parameter is required")
        logger.info(f"[MarketRadar] Running SEO analysis for '{keyword}' via seomachine")

        import httpx
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{SEOMACHINE_BASE}/api/analyze",
                    json={"keyword": keyword, "lang": "zh-CN"},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.warning(f"[MarketRadar] seomachine 不可用 ({e})，返回模拟分析")
            return {
                "status": "simulated",
                "keyword": keyword,
                "difficulty": "medium",
                "search_volume": "N/A",
                "suggested_long_tail": [f"{keyword} 教程", f"如何使用 {keyword}", f"{keyword} 最佳实践"],
                "note": "seomachine 服务未启动，返回模拟数据",
            }

    async def _gather_intelligence(self, params: Dict[str, Any]) -> Dict[str, Any]:
        target = params.get("target", "competitor")
        logger.info(f"[MarketRadar] Gathering market intelligence on '{target}'")

        import httpx
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{SEOMACHINE_BASE}/api/intelligence",
                    params={"target": target},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.warning(f"[MarketRadar] 情报服务不可用 ({e})，返回模拟结果")
            return {
                "status": "simulated",
                "target": target,
                "insights": ["暂无实时情报数据"],
                "note": "情报服务未启动，返回模拟数据",
            }


_market_radar = MarketRadarTool()
def get_market_radar() -> MarketRadarTool:
    return _market_radar
