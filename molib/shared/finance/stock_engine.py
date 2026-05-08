"""
墨域OS — 今日股票分析引擎
=========================
从 ZhuLinsen/daily_stock_analysis (34K⭐) 吸收的6大设计模式：

1. Pipeline + Chain-of-Responsibility 编排器 — 多Agent串行编排
2. Template Method Agent基类 — 骨架+子类填空
3. Decorator + Registry 工具注册 — 声明式功能注册
4. Strategy + Composite多渠道通知 — 统一推送接口
5. Pipeline with Stage Isolation 管线架构 — 阶段隔离降级
6. Singleton + Producer-Consumer + SSE 任务队列 — 线程安全异步队列

用法:
    from molib.shared.finance.stock_engine import StockPipeline
    engine = StockPipeline()
    result = engine.analyze("AAPL")
"""

import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger("molin.finance.stock_engine")


# ═══════════════════════════════════════════════════
# 模式1: Pipeline 的 Stage 定义
# ═══════════════════════════════════════════════════

class StageStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Stage:
    """管线中的单个阶段
    - execute: 执行函数
    - fallback: 降级函数
    - is_critical: 失败时是否中止整个管线
    """
    name: str
    execute: Callable[[dict], Any]
    fallback: Optional[Callable[[dict], Any]] = None
    is_critical: bool = False
    status: StageStatus = StageStatus.PENDING
    result: Any = None
    error: Optional[str] = None


class Pipeline:
    """通用的Pipeline模式：串行执行+阶段隔离降级"""

    def __init__(self):
        self._stages: list[Stage] = []
        self._context: dict = {}

    def add_stage(self, stage: Stage) -> "Pipeline":
        self._stages.append(stage)
        return self

    def run(self, context: dict | None = None) -> dict:
        """执行所有阶段，失败时非关键阶段降级继续"""
        ctx = {**(context or {}), "_pipeline_start": time.time()}
        for stage in self._stages:
            stage.status = StageStatus.RUNNING
            try:
                stage.result = stage.execute(ctx)
                stage.status = StageStatus.SUCCESS
                ctx[stage.name] = stage.result
                logger.debug("[Pipeline] %s ✅", stage.name)
            except Exception as e:
                logger.warning("[Pipeline] %s ❌: %s", stage.name, e)
                if stage.fallback:
                    try:
                        stage.result = stage.fallback(ctx)
                        stage.status = StageStatus.SUCCESS
                        ctx[stage.name] = stage.result
                        logger.info("[Pipeline] %s 降级成功", stage.name)
                    except Exception as e2:
                        stage.error = str(e2)
                        stage.status = StageStatus.FAILED
                        if stage.is_critical:
                            raise RuntimeError(f"关键阶段失败: {stage.name}") from e2
                else:
                    stage.status = StageStatus.FAILED
                    if stage.is_critical:
                        raise RuntimeError(f"关键阶段失败: {stage.name}") from e
        ctx["_pipeline_duration"] = time.time() - ctx["_pipeline_start"]
        return ctx


# ═══════════════════════════════════════════════════
# 模式2: Template Method — Agent基类
# ═══════════════════════════════════════════════════

class BaseAgent(ABC):
    """Template Method模式：子类只需实现 system_prompt + execute"""

    agent_name: str = "base"

    @abstractmethod
    def system_prompt(self, ctx: dict) -> str: ...

    @abstractmethod
    def execute(self, ctx: dict) -> dict: ...

    def post_process(self, ctx: dict, result: dict) -> dict:
        """可选后处理钩子"""
        return result

    def run(self, ctx: dict) -> dict:
        """Template Method骨架"""
        result = self.execute(ctx)
        return self.post_process(ctx, result)


# ═══════════════════════════════════════════════════
# 模式3: Decorator + Registry 工具注册
# ═══════════════════════════════════════════════════

@dataclass
class ToolDef:
    name: str
    description: str
    category: str
    handler: Callable


class ToolRegistry:
    """中央工具注册表"""

    def __init__(self):
        self._tools: dict[str, ToolDef] = {}

    def register(self, tool_def: ToolDef):
        self._tools[tool_def.name] = tool_def

    def execute(self, name: str, **kwargs) -> Any:
        tool = self._tools.get(name)
        if not tool:
            raise KeyError(f"工具未注册: {name}")
        return tool.handler(**kwargs)

    def list_by_category(self, category: str) -> list[ToolDef]:
        return [t for t in self._tools.values() if t.category == category]

    def all_tools(self) -> list[ToolDef]:
        return list(self._tools.values())


_DEFAULT_REGISTRY: ToolRegistry | None = None


def get_default_registry() -> ToolRegistry:
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        _DEFAULT_REGISTRY = ToolRegistry()
    return _DEFAULT_REGISTRY


def register(name: str, description: str = "", category: str = "data"):
    """@register 装饰器：声明式工具注册"""
    def decorator(func):
        tool_def = ToolDef(name=name, description=description or func.__doc__ or "", category=category, handler=func)
        get_default_registry().register(tool_def)
        return func
    return decorator


# ═══════════════════════════════════════════════════
# 模式4: Strategy + Composite 多渠道通知
# ═══════════════════════════════════════════════════

class NotificationSender(ABC):
    """通知发送器接口"""

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def send(self, title: str, content: str, **kwargs) -> bool: ...


class NotificationService:
    """多渠道通知聚合器
    - 自动检测已配置渠道
    - 遍历发送，单渠道失败不影响其他
    """

    def __init__(self):
        self._senders: dict[str, NotificationSender] = {}

    def register_sender(self, name: str, sender: NotificationSender):
        self._senders[name] = sender

    def broadcast(self, title: str, content: str, **kwargs) -> dict[str, bool]:
        """向所有可用渠道发送"""
        results = {}
        for name, sender in self._senders.items():
            if not sender.is_available():
                results[name] = False
                continue
            try:
                results[name] = sender.send(title, content, **kwargs)
            except Exception as e:
                logger.warning("[通知] %s 发送失败: %s", name, e)
                results[name] = False
        return results


# ═══════════════════════════════════════════════════
# 模式5: 股票分析Pipeline
# ═══════════════════════════════════════════════════

class StockPipeline:
    """股票分析管线 — 阶段隔离降级"""

    def __init__(self):
        self.pipeline = Pipeline()
        self._init_stages()

    def _init_stages(self):
        self.pipeline.add_stage(Stage("quote", self._step_quote, fallback=self._step_quote_fallback))
        self.pipeline.add_stage(Stage("fundamental", self._step_fundamental, is_critical=False))
        self.pipeline.add_stage(Stage("technical", self._step_technical, is_critical=False))
        self.pipeline.add_stage(Stage("news", self._step_news, is_critical=False))
        self.pipeline.add_stage(Stage("analysis", self._step_analysis, is_critical=True))

    def _step_quote(self, ctx: dict) -> dict:
        """获取实时行情"""
        return {"symbol": ctx.get("symbol", ""), "price": 0, "change_pct": 0, "timestamp": time.time()}

    def _step_quote_fallback(self, ctx: dict) -> dict:
        """行情降级：昨日收盘价"""
        return {"symbol": ctx.get("symbol", ""), "price": 0, "note": "使用昨日收盘价"}

    def _step_fundamental(self, ctx: dict) -> dict:
        return {"pe": 0, "pb": 0, "market_cap": 0}

    def _step_technical(self, ctx: dict) -> dict:
        return {"ma_20": 0, "rsi": 50, "trend": "neutral"}

    def _step_news(self, ctx: dict) -> dict:
        return {"articles": [], "sentiment": "neutral"}

    def _step_analysis(self, ctx: dict) -> dict:
        """综合LLM分析（占位: 实际调用LLM）"""
        return {"verdict": "hold", "confidence": 0.5, "summary": "分析占位"}

    def analyze(self, symbol: str) -> dict:
        return self.pipeline.run({"symbol": symbol})


# ═══════════════════════════════════════════════════
# 模式6: 任务队列
# ═══════════════════════════════════════════════════

class TaskQueue:
    """线程安全的任务队列 — 去重+并行消费"""

    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, max_workers: int = 4):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self._executor = None  # lazy init
        self._tasks: dict[str, dict] = {}
        self._dedup_set: set[str] = set()
        self._lock = threading.Lock()

    def submit(self, task_id: str, task_fn: Callable, dedup_key: str = "") -> bool:
        """提交任务，自动去重"""
        key = dedup_key or task_id
        with self._lock:
            if key in self._dedup_set:
                return False  # 已存在，跳过
            self._dedup_set.add(key)
            self._tasks[task_id] = {"status": "pending", "result": None}
        # 实际执行（占位）
        return True


# ═══════════════════════════════════════════════════
# 便捷入口
# ═══════════════════════════════════════════════════

def analyze_stock(symbol: str) -> dict:
    """一键分析股票"""
    engine = StockPipeline()
    return engine.analyze(symbol)


# ═══════════════════════════════════════════════════
# 示例工具注册
# ═══════════════════════════════════════════════════

@register(name="get_realtime_quote", description="获取股票实时行情", category="market")
def get_realtime_quote(symbol: str) -> dict:
    return {"symbol": symbol, "price": 0, "time": time.time()}


@register(name="get_news_sentiment", description="获取新闻情绪分析", category="analysis")
def get_news_sentiment(topic: str) -> dict:
    return {"topic": topic, "sentiment": "neutral", "score": 0.5}


# ═══════════════════════════════════════════════════
# 测试
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    import json

    # 测试 Pipeline
    result = analyze_stock("AAPL")
    print(f"📊 股票分析结果: {json.dumps(result, indent=2, default=str)[:300]}...")

    # 测试工具注册
    registry = get_default_registry()
    print(f"🔧 已注册工具: {[t.name for t in registry.all_tools()]}")

    # 测试通知
    notifier = NotificationService()
    print(f"📢 通知服务就绪: 可注册 {len(notifier._senders)} 个渠道")
    print("\n✅ stock_engine 导入成功")
