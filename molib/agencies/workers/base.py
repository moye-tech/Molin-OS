"""墨域OS — 子公司Worker基类"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Task:
    task_id: str
    task_type: str
    payload: dict
    priority: str = "medium"
    requester: str = "ceo"

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
