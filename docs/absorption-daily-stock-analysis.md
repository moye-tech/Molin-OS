"""
墨麟OS — 今日股票分析引擎
=========================
从 ZhuLinsen/daily_stock_analysis (34K⭐) 吸收的6大设计模式。

文件: molib/shared/finance/stock_engine.py (13KB)

源项目: https://github.com/ZhuLinsen/daily_stock_analysis
源码位置: /tmp/daily_stock_analysis/ (132MB, git clone)
"""

import json

PATTERNS = [
    {
        "name": "Pipeline + Stage Isolation",
        "file": "src/core/pipeline.py (2104行)",
        "description": "9阶段串行管线，每阶段 try/except 隔离降级，支持断点续传",
        "absorbed_at": "molib/shared/finance/stock_engine.py::Pipeline + Stage",
    },
    {
        "name": "Pipeline + Chain-of-Responsibility 编排器",
        "file": "src/agent/orchestrator.py (1593行)",
        "description": "按 mode (quick/standard/full/specialist) 构建 Agent 链，critical/non-critical 降级",
        "absorbed_at": "molib/shared/finance/stock_engine.py::Pipeline",
    },
    {
        "name": "Template Method Agent 基类",
        "file": "src/agent/agents/base_agent.py (271行)",
        "description": "run()骨架 + system_prompt()/build_user_message()/post_process()钩子",
        "absorbed_at": "molib/shared/finance/stock_engine.py::BaseAgent(ABC)",
    },
    {
        "name": "Decorator + Registry 工具注册",
        "file": "src/agent/tools/registry.py (265行)",
        "description": "@register装饰器 + ToolRegistry，自动类型推断参数Schema",
        "absorbed_at": "molib/shared/finance/stock_engine.py::register/Registry",
    },
    {
        "name": "Strategy + Composite 多渠道通知",
        "file": "src/notification_sender/ (10渠道)",
        "description": "统一send()接口，10个Sender(Feishu/WeChat/Telegram/Discord/Slack/Email等)",
        "absorbed_at": "molib/shared/finance/stock_engine.py::NotificationService",
    },
    {
        "name": "Singleton + Producer-Consumer + SSE 任务队列",
        "file": "src/services/task_queue.py (762行)",
        "description": "双重检查锁单例, ThreadPoolExecutor消费, call_soon_threadsafe SSE广播",
        "absorbed_at": "molib/shared/finance/stock_engine.py::TaskQueue",
    },
]
