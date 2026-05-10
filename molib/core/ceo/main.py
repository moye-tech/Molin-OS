"""
墨麟AI智能系统 v6.6 — FastAPI 主入口
使用 lifespan 上下文管理器替代已废弃的 on_event 装饰器
"""

import json
import os
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, Response
from loguru import logger
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

from .ceo import CEO
from .ceo_reasoning import CEOReasoningLoop
from molib.infra.memory.qdrant_client import MolinMemory
from molib.infra.memory.sqlite_client import SQLiteClient
from molib.utils.tracing import generate_request_id, set_request_id, get_request_id
from molib.core.middleware import setup_cors, rate_limit_middleware, get_auth_dependency
try:
    from molib.infra.monitoring.metrics import get_metrics_response
except Exception:
    get_metrics_response = None
from molib.infra.scheduler.cron import setup_scheduler, scheduler
import sys

# 配置 loguru 以支持结构化日志和 context_var 绑定的 request_id
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level> {extra}",
    enqueue=True,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # ── Startup ──
    logger.info("墨麟ai智能系统v6.6 启动中...")

    # 配置验证：启动前校验 managers.toml / subsidiaries.toml / worker 文件一致性
    try:
        from molib.utils.validate_config import validate_all
        if not validate_all():
            logger.error("配置验证失败，系统终止启动")
            sys.exit(1)
    except Exception as exc:
        logger.warning(f"配置验证跳过: {exc}")

    await SQLiteClient().init()

    # 注册默认工具（Worker 执行依赖）
    try:
        from molib.core.tools.registry import register_default_tools, ToolRegistry
        register_default_tools()
        logger.info(f"ToolRegistry 已注册: 工具列表 = {list(ToolRegistry.list_all())}")
    except Exception as exc:
        logger.warning(f"ToolRegistry 注册跳过: {exc}")

    try:
        MolinMemory().init_collections()
        logger.info("Qdrant 集合初始化完成")
    except Exception as exc:
        logger.warning(f"Qdrant init skipped: {exc}")

    # 启动定时任务调度器
    try:
        setup_scheduler()
        scheduler.start()
        logger.info("APScheduler 定时任务已启动")
    except Exception as exc:
        logger.warning(f"Scheduler start failed: {exc}")

    # FIX-F4: ManagerDispatcher 预初始化（不等第一条请求触发）
    try:
        from molib.core.managers.manager_dispatcher import get_dispatcher
        dispatcher = await get_dispatcher()
        await dispatcher.initialize()
        manager_count = len(dispatcher.managers)
        logger.info(f"ManagerDispatcher 预初始化完成: {manager_count} managers")
        if manager_count == 0:
            logger.error("0个Manager注册成功，系统功能受损！检查 config/managers.toml")
        app.state.manager_available = manager_count > 0
    except Exception as e:
        logger.error(f"ManagerDispatcher 初始化失败: {e}")
        app.state.manager_available = False

    # P2-5: 启动自愈引擎
    try:
        from molib.infra.self_healing.self_healing_engine import get_self_healing_engine
        healer = await get_self_healing_engine()
        await healer.start()
        logger.info("Self-healing engine started")
    except Exception as exc:
        logger.warning(f"Self-healing engine start failed: {exc}")

    # 飞书消息统一由独立 feishu-bot 容器处理（WebSocket 长连接）

    logger.info("墨麟ai智能系统v6.6 启动完成")
    yield
    # ── Shutdown ──
    logger.info("墨麟ai智能系统v6.6 关闭中...")
    try:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
    except Exception:
        pass
    # 关闭自愈引擎
    try:
        from molib.infra.self_healing.self_healing_engine import _self_healing_engine
        if _self_healing_engine:
            await _self_healing_engine.stop()
            logger.info("Self-healing engine stopped")
    except Exception:
        pass


app = FastAPI(title="墨麟ai智能系统v6.6 CEO", version="6.6", lifespan=lifespan)

# ── CORS 白名单（最外层）──
setup_cors(app)

# 飞书消息统一由独立 feishu-bot 容器处理（WebSocket 长连接），不再嵌入 Webhook

# ── 速率限制 ──
app.add_middleware(BaseHTTPMiddleware, dispatch=rate_limit_middleware)

# ── 链路追踪 ──
class RequestTracingMiddleware(BaseHTTPMiddleware):
    """为每个请求分配唯一 request_id"""
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or generate_request_id()
        set_request_id(rid)
        with logger.contextualize(request_id=rid):
            logger.info(f"{request.method} {request.url.path}")
            response = await call_next(request)
            response.headers["X-Request-ID"] = rid
            return response

app.add_middleware(RequestTracingMiddleware)

# ── 请求体大小限制（1MB）──
MAX_BODY_SIZE = int(os.getenv("MAX_BODY_SIZE_BYTES", "1048576"))

@app.middleware("http")
async def body_size_limit(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_BODY_SIZE:
        return JSONResponse(status_code=413, content={"detail": "Request body too large"})
    return await call_next(request)

ceo = CEO()
reasoning_loop = CEOReasoningLoop()
auth_deps = get_auth_dependency()


class DecisionRequest(BaseModel):
    input: str
    budget: Optional[float] = None
    timeline: Optional[str] = None
    target_revenue: Optional[float] = None
    context: Optional[dict] = None


@app.get("/health")
async def health():
    return {"status": "ok", "version": "6.6", "name": "墨麟ai智能系统"}


@app.get("/metrics")
async def metrics():
    """Prometheus 指标端点"""
    return Response(content=get_metrics_response(), media_type="text/plain")


@app.post("/api/decide", dependencies=auth_deps)
async def decide(req: DecisionRequest):
    try:
        return await ceo.run_async(
            user_input=req.input,
            budget=req.budget,
            timeline=req.timeline,
            target_revenue=req.target_revenue,
            context=req.context or {}
        )
    except Exception as e:
        logger.error(f"Decision failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ChatRequest(BaseModel):
    """多轮对话请求"""
    session_id: str
    input: str
    budget: Optional[float] = None
    timeline: Optional[str] = None
    target_revenue: Optional[float] = None
    progress_message_id: Optional[str] = None
    chat_id: Optional[str] = None


@app.post("/api/chat", dependencies=auth_deps)
async def chat(req: ChatRequest):
    """多轮推理对话端点"""
    try:
        return await reasoning_loop.run(
            session_id=req.session_id,
            user_input=req.input,
            budget=req.budget,
            timeline=req.timeline,
            target_revenue=req.target_revenue,
            progress_message_id=req.progress_message_id,
            chat_id=req.chat_id,
        )
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/daily-loop", dependencies=auth_deps)
async def daily_loop():
    """每日23:00由定时任务触发，执行墨麟自优化循环"""
    return await ceo.daily_loop()


# ── 审批 API（仅飞书入口，无 Web 面板）──

class ApprovalAction(BaseModel):
    comment: Optional[str] = ""


@app.get("/api/pending-approvals")
async def get_pending_approvals(status: str = "pending"):
    """获取待审批列表"""
    from molib.infra.memory.sqlite_client import SQLiteClient
    db = SQLiteClient()
    return await db.get_pending_approvals(status=status)


@app.post("/api/approve/{approval_id}")
async def approve_item(approval_id: str, action: ApprovalAction):
    """通过审批"""
    from molib.infra.memory.sqlite_client import SQLiteClient
    db = SQLiteClient()
    await db.approve(approval_id, comment=action.comment)
    return {"status": "approved", "approval_id": approval_id}


@app.post("/api/reject/{approval_id}")
async def reject_item(approval_id: str, action: ApprovalAction):
    """驳回审批"""
    from molib.infra.memory.sqlite_client import SQLiteClient
    db = SQLiteClient()
    await db.reject(approval_id, comment=action.comment)
    return {"status": "rejected", "approval_id": approval_id}


# ── 飞书审批回调（FS-5）──
if os.getenv("FEISHU_APPROVAL_ENABLED", "false").lower() == "true":
    try:
        from molib.integrations.feishu.bridge import get_feishu_callback_router
        app.include_router(get_feishu_callback_router())
        logger.info("飞书审批回调端点已注册: /feishu/callback")
    except Exception as e:
        logger.warning(f"飞书回调路由注册失败: {e}")


class ApprovalCreateRequest(BaseModel):
    """创建审批请求"""
    title: str
    description: str = ""
    task_type: str = ""
    agency_id: str = ""


@app.post("/api/create-approval")
async def create_approval(req: ApprovalCreateRequest):
    """创建审批 — FS-1: 同时推送飞书审批卡片"""
    import uuid
    from molib.infra.memory.sqlite_client import SQLiteClient
    db = SQLiteClient()
    approval_id = str(uuid.uuid4())[:8]
    await db.add_pending_approval(
        approval_id=approval_id,
        title=req.title,
        description=req.description,
        task_type=req.task_type,
        agency_id=req.agency_id,
    )
    # 飞书审批卡片推送
    chat_id = os.getenv("FEISHU_APPROVAL_CHAT_ID", "")
    if chat_id and os.getenv("FEISHU_APPROVAL_ENABLED", "false").lower() == "true":
        try:
            from molib.integrations.feishu.bridge import push_approval_card
            import asyncio
            asyncio.create_task(push_approval_card(
                approval_id=approval_id,
                title=req.title,
                description=req.description,
                chat_id=chat_id,
            ))
        except Exception as e:
            logger.warning(f"飞书审批卡片推送失败: {e}")
    return {"status": "created", "approval_id": approval_id}
