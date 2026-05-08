"""墨麟OS — FastAPI主入口（L1/L2/L3 整合）
"""
import json, os, sys
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .intent_router import IntentRouter
from .risk_engine import RiskEngine
from .ceo_orchestrator import CEOOrchestrator
from .sop_store import SOPStore

HERMES_ROOT = Path(os.path.expanduser("~/.hermes"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    app.state.router = IntentRouter()
    app.state.risk = RiskEngine()
    app.state.orchestrator = CEOOrchestrator()
    app.state.sop = SOPStore()
    yield


app = FastAPI(title="墨麟OS", version="v1.0", lifespan=lifespan)


class TaskRequest(BaseModel):
    text: str
    session_id: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    workers_available: int
    vps_available: int


# ═══ API端点 ═══


@app.get("/api/health")
async def health():
    """系统健康检查"""
    from molib.agencies.workers import register_all, list_workers
    from molib.management.vp_registry import get_all_vps

    register_all()
    workers = list_workers()
    vps = get_all_vps()

    return {
        "status": "ok",
        "version": "v1.0",
        "workers": len(workers),
        "vps": len(vps),
        "sop_count": len(app.state.sop.list_recent()),
    }


@app.post("/api/analyze")
async def analyze(req: TaskRequest):
    """分析意图（不执行）"""
    intent = await app.state.router.analyze(req.text)
    risk = app.state.risk.assess(intent)
    return {
        "intent_type": intent.intent_type,
        "complexity": intent.complexity_score,
        "entities": intent.entities,
        "target_vps": intent.target_vps,
        "target_workers": intent.target_subsidiaries,
        "risk": {
            "score": risk.risk_score,
            "requires_approval": risk.requires_approval,
            "reason": risk.reason,
        },
    }


@app.post("/api/execute")
async def execute(req: TaskRequest):
    """完整任务执行"""
    result = await app.state.orchestrator.process(req.text)
    return result


@app.get("/api/workers")
async def list_workers_endpoint():
    """列出所有子公司Worker"""
    from molib.agencies.workers import register_all, list_workers
    register_all()
    return {"workers": list_workers()}


@app.get("/api/vps")
async def list_vps():
    """列出所有VP"""
    from molib.management.vp_registry import get_all_vps
    vps = get_all_vps()
    return {"vps": [
        {"name": vp.name, "quality_gate": vp.quality_gate,
         "escalation_model": vp.escalation_model,
         "subsidiaries": vp.subsidiaries}
        for vp in vps
    ]}


@app.get("/api/sops")
async def list_sops(limit: int = 10):
    """最近SOP记录"""
    return {"sops": app.state.sop.list_recent(limit=limit)}


@app.get("/api/risk/patterns")
async def risk_patterns():
    """风险模式列表"""
    return {
        "financial": [{"pattern": p[0], "severity": p[1]} for p in _patterns_from_module("financial")],
        "compliance": [{"pattern": p[0], "severity": p[1]} for p in _patterns_from_module("compliance")],
        "legal": [{"pattern": p[0], "severity": p[1]} for p in _patterns_from_module("legal")],
        "privacy": [{"pattern": p[0], "severity": p[1]} for p in _patterns_from_module("privacy")],
    }


def _patterns_from_module(dim: str) -> list:
    """获取风险引擎中的模式列表"""
    from molib.ceo import risk_engine as re
    attr_map = {
        "financial": "FINANCIAL_PATTERNS",
        "compliance": "COMPLIANCE_PATTERNS",
        "legal": "LEGAL_PATTERNS",
        "privacy": "PRIVACY_PATTERNS",
    }
    return getattr(re, attr_map.get(dim, ""), [])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5050)
