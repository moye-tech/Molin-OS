"""墨域OS — 子公司Worker基类"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class Task(Generic[T]):
    task_id: str
    task_type: str
    payload: T | dict = field(default_factory=dict)
    priority: str = "medium"
    requester: str = "ceo"
    source_handoff: str = ""
    """从哪个 handoff 发起的（用于追踪）"""


@dataclass
class WorkerResult:
    task_id: str
    worker_id: str
    status: str = "success"
    output: dict = field(default_factory=dict)
    cost: float = 0.0
    error: str | None = None

class SubsidiaryWorker(ABC):
    worker_id: str = "base"
    worker_name: str = "基础子公司"
    description: str = ""
    oneliner: str = ""

    @abstractmethod
    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        ...

    def quality_check(self, output: dict) -> float:
        return 85.0

    # ── LLM 辅助工具 ────────────────────────────────────────────────

    async def llm_chat(self, prompt: str, system: str = "",
                       model: str = "deepseek-v4-flash") -> str:
        """
        简便的 LLM 调用，供 Worker 实现使用。
        自动记录成本到 cost.db。
        """
        try:
            from molib.ceo.llm_client import LLMClient
            client = LLMClient()
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            result = await client.chat(messages, model=model)
            # 估算 token 并记成本
            try:
                from molib.cost import record
                input_tokens = len(prompt) // 1  # 粗略估算
                output_tokens = len(result) // 2
                record(model=model, input_tokens=input_tokens,
                       output_tokens=output_tokens,
                       task=f"worker:{self.worker_id}")
            except Exception:
                pass
            return result
        except Exception:
            return ""

    async def llm_chat_json(self, prompt: str, system: str = "",
                            model: str = "deepseek-v4-flash") -> dict:
        """
        调用 LLM 并解析 JSON 响应。
        返回解析后的 dict，解析失败返回空 dict。
        """
        import json
        import re
        result = await self.llm_chat(prompt, system=system, model=model)
        if not result:
            return {}
        try:
            json_match = re.search(r"\{.*\}", result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        except (json.JSONDecodeError, AttributeError):
            pass
        return {}

class WorkerRegistry:
    _workers: dict[str, type[SubsidiaryWorker]] = {}

    @classmethod
    def register(cls, worker_cls: type[SubsidiaryWorker]):
        cls._workers[worker_cls.worker_id] = worker_cls

    @classmethod
    def get(cls, worker_id: str) -> type[SubsidiaryWorker] | None:
        return cls._workers.get(worker_id)

    @classmethod
    def list_all(cls) -> list[str]:
        return list(cls._workers.keys())
