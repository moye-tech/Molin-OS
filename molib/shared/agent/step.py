"""
墨麟 — Agent 步骤引擎 (AgentStep)
从 Integuru 提取的 Function Calling Agent 编排模式。

每个 Agent 步骤定义自己的输入/输出 Schema，
LLM 输出强制符合 Schema，无需 Parser。

用法:
    from molib.shared.agent.step import AgentStep, AgentState

    class IdentifyEndpoint(AgentStep):
        def function_schema(self):
            return {
                "name": "identify_endpoint",
                "parameters": {
                    "url": {"type": "string"}
                }
            }
        def execute(self, state: AgentState):
            state["endpoint"] = "https://api.example.com/v1"
            return state
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


# ── 标准 Agent 状态 ────────────────────────────────────────────────


AgentState = Dict[str, Any]
"""
标准 Agent 状态类型。

每步 Agent 操作接收并返回此类型（类似 Redux reducer 模式）。
建议字段:
    - input: 用户输入或上游数据
    - output: 当前步骤输出
    - errors: List[str] 错误列表
    - metadata: Dict 上下文元数据
"""


# ── 抽象基类 ──────────────────────────────────────────────────────


class AgentStep(ABC):
    """
    Agent 单步操作的抽象基类。

    子类必须实现:
    - function_schema(): 返回该步骤的 JSON Schema 定义
    - execute(state): 执行该步骤并返回更新后的状态

    可选覆盖:
    - should_run(state): 条件执行判断
    - rollback(state): 失败回滚
    """

    def __init__(self, name: Optional[str] = None):
        self._name = name or self.__class__.__name__

    @property
    def name(self) -> str:
        """步骤名称"""
        return self._name

    @abstractmethod
    def function_schema(self) -> Dict[str, Any]:
        """
        返回该步骤的 Function Calling Schema。

        返回值格式（OpenAI function calling 兼容）:
        {
            "name": "步骤名称",
            "description": "步骤描述",
            "parameters": {
                "type": "object",
                "properties": {
                    "field1": {"type": "string", "description": "..."}
                },
                "required": ["field1"]
            }
        }
        """

    @abstractmethod
    def execute(self, state: AgentState) -> AgentState:
        """
        执行该步骤。

        参数:
            state: 当前 Agent 状态（包含前置步骤的输出）

        返回:
            更新后的 Agent 状态
        """

    def should_run(self, state: AgentState) -> bool:
        """
        判断是否应该执行此步骤。
        默认始终执行，子类可覆盖实现条件路由。
        """
        return True

    def rollback(self, state: AgentState) -> AgentState:
        """
        失败回滚。
        子类可覆盖实现自定义回滚逻辑。
        """
        state.setdefault("errors", []).append(f"{self._name}: rollback")
        return state


# ── 步骤链编排 ────────────────────────────────────────────────────


class StepChain:
    """
    Agent 步骤链：按顺序执行多个 AgentStep。
    前一步的输出作为后一步的输入。
    """

    def __init__(self, steps: Optional[List[AgentStep]] = None):
        self._steps: List[AgentStep] = steps or []

    def add_step(self, step: AgentStep):
        """添加一个步骤到链尾"""
        self._steps.append(step)

    def run(self, initial_state: Optional[AgentState] = None) -> AgentState:
        """
        按顺序执行所有步骤。

        参数:
            initial_state: 初始状态（可选）

        返回:
            最终状态（所有步骤依次累加的结果）
        """
        state: AgentState = dict(initial_state or {})

        for step in self._steps:
            try:
                if step.should_run(state):
                    state = step.execute(state)
                else:
                    state.setdefault("skipped_steps", []).append(step.name)
            except Exception as e:
                state.setdefault("errors", []).append(f"{step.name}: {e}")
                state = step.rollback(state)
                break

        return state

    @property
    def steps(self) -> List[AgentStep]:
        """获取步骤列表（只读）"""
        return list(self._steps)

    def __len__(self) -> int:
        return len(self._steps)

    def __repr__(self) -> str:
        return f"StepChain({len(self._steps)} steps: {', '.join(s.name for s in self._steps)})"
