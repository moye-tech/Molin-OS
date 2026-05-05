"""
多Agent编排引擎 — 从 THU-MAIC/OpenMAIC (16.8K⭐) 汲取的导演-演员(Director-Actor)模式

核心思想:
  - Stateless: 服务端不保留状态，所有上下文通过请求传递
  - Director-Actor: Director决定谁发言，Actor执行内容生成
  - LangGraph StateGraph: 有向图拓扑 START → director → agent → director(循环) → END
  - 结构化输出流: LLM输出JSON数组 {type:'text'|'action', content/params}

适用场景:
  - 多Agent课堂/会议/辩论
  - CEO决策引擎的多Agent协作
  - 子公司的任务编排
"""

import json
import re
from typing import Any, AsyncGenerator, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime


# ─── 类型定义 ────────────────────────────────────────────────────────────

@dataclass
class AgentConfig:
    """Agent配置 — 对应OpenMAIC的Agent注册表"""
    id: str
    name: str
    role: str  # teacher | assistant | student | specialist
    persona: str
    allowed_actions: list[str] = field(default_factory=lambda: [
        "text", "wb_draw_text", "wb_draw_shape", "wb_draw_chart"
    ])
    max_turns: int = 10
    priority: int = 0


@dataclass
class OrchestratorState:
    """编排运行时状态 — 对应OpenMAIC的OrchestratorState"""
    messages: list[dict] = field(default_factory=list)
    available_agent_ids: list[str] = field(default_factory=list)
    current_agent_id: Optional[str] = None
    turn_count: int = 0
    max_turns: int = 20
    agent_responses: list[dict] = field(default_factory=list)
    whiteboard_ledger: list[dict] = field(default_factory=list)
    should_end: bool = False
    metadata: dict = field(default_factory=dict)


@dataclass
class StructuredAction:
    """结构化动作 — 对应OpenMAIC的StructuredEvent"""
    type: str  # text | action
    content: Optional[str] = None
    action_name: Optional[str] = None
    agent_id: Optional[str] = None
    params: dict = field(default_factory=dict)


# ─── 结构化输出流解析器 ──────────────────────────────────────────────

class StructuredOutputParser:
    """结构化输出流解析 — 从OpenMAIC partial-json解析器汲取

    解析LLM输出的JSON数组流:
    [{type:'text', content:'...'}, {type:'action', name:'xxx', params:{...}}, ...]
    """

    def __init__(self):
        self.buffer = ""
        self.json_started = False
        self.emitted_count = 0
        self.done = False

    def feed(self, chunk: str) -> list[StructuredAction]:
        """喂入新chunk，返回新解析出的action列表"""
        if self.done:
            return []

        self.buffer += chunk

        # 检测JSON开始
        if not self.json_started:
            # 跳过前导文本，找到第一个 [
            bracket_pos = self.buffer.find('[')
            if bracket_pos == -1:
                # 可能是纯文本模式，不解析
                return []
            if bracket_pos > 0:
                # 有前导文本，作为text action发射
                text = self.buffer[:bracket_pos].strip()
                self.buffer = self.buffer[bracket_pos:]
                self.json_started = True
                if text:
                    return [StructuredAction(type="text", content=text)]
            else:
                self.json_started = True

        if not self.json_started:
            return []

        # 尝试解析JSON数组
        actions = self._try_parse_json()
        return actions

    def _try_parse_json(self) -> list[StructuredAction]:
        """尝试增量解析JSON数组"""
        results = []

        try:
            data = json.loads(self.buffer)
            if isinstance(data, list):
                # 完全解析成功
                new_items = data[self.emitted_count:]
                self.emitted_count = len(data)
                self.done = True

                for item in new_items:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            results.append(StructuredAction(
                                type="text", content=item.get("content", "")
                            ))
                        elif item.get("type") == "action":
                            results.append(StructuredAction(
                                type="action",
                                action_name=item.get("name", ""),
                                params=item.get("params", {})
                            ))
            return results
        except json.JSONDecodeError:
            # 不完全的JSON，尝试部分解析
            return self._try_partial_parse()

    def _try_partial_parse(self) -> list[StructuredAction]:
        """尝试部分解析（通过正则提取完成的对象）"""
        results = []

        # 匹配完整的JSON对象: {...}
        pattern = r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}'
        matches = list(re.finditer(pattern, self.buffer))

        for match in matches:
            try:
                obj = json.loads(match.group())
                if isinstance(obj, dict) and obj.get("type") == "action":
                    results.append(StructuredAction(
                        type="action",
                        action_name=obj.get("name", ""),
                        params=obj.get("params", {})
                    ))
            except json.JSONDecodeError:
                pass

        return results

    def finalize(self) -> list[StructuredAction]:
        """完成解析，返回剩余未发射的action"""
        if not self.json_started:
            text = self.buffer.strip()
            if text:
                return [StructuredAction(type="text", content=text)]
            return []
        return []


# ─── 导演-演员编排引擎 ─────────────────────────────────────────────

class DirectorAgent:
    """导演Agent — 决定谁下一个发言，何时结束"""

    def __init__(self, llm_func: Callable):
        self.llm_func = llm_func  # async (prompt: str) -> str

    def build_decision_prompt(self, state: OrchestratorState,
                              agents: dict[str, AgentConfig]) -> str:
        """构建导演决策提示词"""
        available = ", ".join([
            f"{a.id}({a.role}: {a.name})"
            for a in agents.values() if a.id in state.available_agent_ids
        ])

        recent_context = ""
        if state.agent_responses:
            recent = state.agent_responses[-3:]  # 近3轮
            recent_context = "\n".join([
                f"[{r.get('agent_id', '?')}]: {r.get('summary', '')[:200]}"
                for r in recent
            ])

        return f"""你是一个AI课堂的导演，负责决定下一个发言者。

可用Agent: {available}
当前轮次: {state.turn_count}/{state.max_turns}
最近发言:
{recent_context or '(无)'}

请从以下选项中选择一个:
1. 指定下一个发言的Agent ID
2. USER — 让用户发言/提问
3. END — 结束对话

只返回Agent ID、USER或END，不要其他文字。"""

    async def decide(self, state: OrchestratorState,
                     agents: dict[str, AgentConfig]) -> str:
        """做出决策"""
        if len(state.available_agent_ids) <= 1:
            # 单Agent模式，直接分派
            if state.available_agent_ids:
                return state.available_agent_ids[0]
            return "END"

        prompt = self.build_decision_prompt(state, agents)
        decision = await self.llm_func(prompt)
        decision = decision.strip().upper()

        if decision in ("USER", "END"):
            return decision

        if decision in agents:
            return decision

        # 尝试匹配
        for aid in state.available_agent_ids:
            if aid.upper() == decision:
                return aid
            if aid.lower() in decision.lower():
                return aid

        # 默认循环
        if state.agent_responses:
            # 选还没发言的
            spoken = set(r.get("agent_id") for r in state.agent_responses)
            for aid in state.available_agent_ids:
                if aid not in spoken:
                    return aid

        return state.available_agent_ids[0] if state.available_agent_ids else "END"


class ActorAgent:
    """演员Agent — 执行具体内容生成"""

    def __init__(self, config: AgentConfig, llm_func: Callable):
        self.config = config
        self.llm_func = llm_func

    def build_system_prompt(self, state: OrchestratorState) -> str:
        """构建角色感知的系统提示"""
        role_guidelines = {
            "teacher": "你是主导者。可以完整输出、使用白板、控制课堂节奏。",
            "assistant": "你是辅助者。补充teacher的内容，回答学生问题。",
            "student": f"你是学生({self.config.name})。简短回应(100字以内)，可以提问。",
            "specialist": "你是领域专家。深入解答专业问题，可引用案例。"
        }
        guideline = role_guidelines.get(
            self.config.role,
            "你是参与者。根据自己的persona发言。"
        )

        # 同轮上下文
        peer_context = ""
        if state.agent_responses:
            last = state.agent_responses[-1]
            peer_context = f"上一发言者: [{last.get('agent_id')}] {last.get('summary', '')[:300]}"

        return f"""你是{self.config.name} — {self.config.persona}
角色: {self.config.role}

{guideline}

{peer_context}

请以JSON数组格式输出:
[
  {{"type": "text", "content": "你的发言内容"}},
  {{"type": "action", "name": "wb_draw_text", "params": {{"content": "白板内容"}}}}
]
"""

    async def generate(self, state: OrchestratorState) -> tuple[str, list[StructuredAction]]:
        """生成回复，返回 (文本摘要, 动作列表)"""
        prompt = self.build_system_prompt(state)
        response = await self.llm_func(prompt)

        # 解析结构化输出
        parser = StructuredOutputParser()
        text_parts = []
        actions = []

        # 尝试直接解析JSON
        try:
            data = json.loads(response)
            if isinstance(data, list):
                for item in data:
                    if item.get("type") == "text":
                        text_parts.append(item.get("content", ""))
                    elif item.get("type") == "action":
                        actions.append(StructuredAction(
                            type="action",
                            action_name=item.get("name", ""),
                            agent_id=self.config.id,
                            params=item.get("params", {})
                        ))
        except json.JSONDecodeError:
            # 纯文本模式
            text_parts.append(response)

        summary = "\n".join(text_parts) if text_parts else "(无回复)"
        return summary, actions


class MultiAgentOrchestrator:
    """多Agent编排引擎 — LangGraph风格的导演-演员循环

    使用方式:
        orchestrator = MultiAgentOrchestrator(llm_func)
        orchestrator.register_agent(AgentConfig(id="teacher", ...))
        orchestrator.register_agent(AgentConfig(id="student1", ...))
        state = OrchestratorState(available_agent_ids=["teacher", "student1"])
        await orchestrator.run(state)
    """

    def __init__(self, llm_func: Callable):
        self.llm_func = llm_func
        self.director = DirectorAgent(llm_func)
        self.agents: dict[str, ActorAgent] = {}

    def register_agent(self, config: AgentConfig):
        """注册一个演员Agent"""
        self.agents[config.id] = ActorAgent(config, self.llm_func)

    def register_agents(self, configs: list[AgentConfig]):
        """批量注册Agent"""
        for c in configs:
            self.register_agent(c)

    async def run(self, state: OrchestratorState) -> AsyncGenerator[StructuredAction, None]:
        """运行编排循环 — 生成器方式"""
        while state.turn_count < state.max_turns and not state.should_end:
            # 1. Director决策
            decision = await self.director.decide(state, self.agents)

            if decision == "END":
                state.should_end = True
                break

            if decision == "USER":
                yield StructuredAction(
                    type="action",
                    action_name="ask_user",
                    params={"message": "请发言"}
                )
                state.turn_count += 1
                continue

            # 2. 指定Agent发言
            actor = self.agents.get(decision)
            if not actor:
                state.turn_count += 1
                continue

            state.current_agent_id = decision

            # 3. Actor生成内容
            summary, actions = await actor.generate(state)
            state.agent_responses.append({
                "agent_id": decision,
                "summary": summary,
                "turn": state.turn_count,
                "timestamp": datetime.now().isoformat()
            })

            # 4. 发射动作
            yield StructuredAction(type="text", content=f"[{decision}]: {summary}")

            for action in actions:
                action.agent_id = decision
                yield action
                if action.action_name.startswith("wb_"):
                    state.whiteboard_ledger.append({
                        "agent_id": decision,
                        "action": action.action_name,
                        "params": action.params,
                        "timestamp": datetime.now().isoformat()
                    })

            state.turn_count += 1

    async def run_to_completion(self, state: OrchestratorState) -> dict:
        """运行到完成，返回完整结果"""
        all_actions = []
        async for action in self.run(state):
            all_actions.append(action)

        return {
            "state": state,
            "actions": all_actions,
            "agent_count": len(self.agents),
            "turns_used": state.turn_count,
            "summary": [
                f"[{r['agent_id']}]: {r['summary'][:100]}"
                for r in state.agent_responses
            ]
        }


# ─── 快速构建器 ─────────────────────────────────────────────────────

def create_classroom_orchestrator(llm_func: Callable) -> MultiAgentOrchestrator:
    """快速创建一个课堂多Agent编排器（默认配置）"""
    orchestrator = MultiAgentOrchestrator(llm_func)
    orchestrator.register_agents([
        AgentConfig(id="teacher", name="AI教师", role="teacher",
                    persona="专业、耐心的教师，引导学生思考"),
        AgentConfig(id="assistant", name="AI助教", role="assistant",
                    persona="补充知识点，解答疑问"),
        AgentConfig(id="student1", name="思考者", role="student",
                    persona="喜欢深入思考"),
        AgentConfig(id="student2", name="好奇宝", role="student",
                    persona="总是问为什么"),
    ])
    return orchestrator


def create_debate_orchestrator(llm_func: Callable) -> MultiAgentOrchestrator:
    """快速创建一个辩论多Agent编排器"""
    orchestrator = MultiAgentOrchestrator(llm_func)
    orchestrator.register_agents([
        AgentConfig(id="moderator", name="主持人", role="teacher",
                    persona="中立、公正的主持人"),
        AgentConfig(id="pro", name="正方辩手", role="specialist",
                    persona="支持论点，提供有力论据"),
        AgentConfig(id="con", name="反方辩手", role="specialist",
                    persona="质疑论点，找出漏洞"),
        AgentConfig(id="judge", name="评审", role="assistant",
                    persona="评估双方论点质量"),
    ])
    return orchestrator
