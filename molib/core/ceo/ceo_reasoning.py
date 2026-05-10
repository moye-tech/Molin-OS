"""
墨麟AI智能系统 v6.6 — CEO Reasoning Loop

CEO 的多轮推理循环，替代原有的 ceo.run_async() 一次性决策。

灵感来源：Claude Code `src/query.ts` 的 queryLoop()。

核心流程（每个 Turn）：
1. Context Preprocessing — 压缩历史，提取关键信息
2. Intent Inference — 推理用户当前轮的真实意图
3. Tool Selection — 选择需要的工具
4. Tool Execution — 执行选中的工具
5. Result Synthesis — 综合工具结果生成回复
6. Stop Hook Evaluation — 判断是否该停止
"""

from __future__ import annotations
from datetime import datetime

import json
import os
import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from loguru import logger

from molib.core.ceo.session_state import SessionContext, SessionState, SessionStore
from molib.core.ceo.model_router import ModelRouter
from molib.core.evolution.engine import EvolutionEngine

# ManagerDispatcher（可选）
try:
    from molib.core.managers.manager_dispatcher import get_dispatcher, dispatch_to_manager
    from molib.agencies.base import Task
    MANAGER_DISPATCHER_AVAILABLE = True
except ImportError:
    MANAGER_DISPATCHER_AVAILABLE = False


# ── CEO 系统 Prompt（定义行为） ──────────────────────────────

CEO_SYSTEM_PROMPT = """
你是 Hermes，老墨 AI 工作室的 AI CEO，也是老板（墨烨）最信任的决策伙伴。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【核心人格】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

你不是工具，不是助手，你是老板的"二号位"。
你聪明、果断、有判断力，像一个优秀的 COO——
既懂战略（看得远），也懂执行（能拆解）。

你与老板的沟通方式：
- 自然、简洁，像两个聪明人之间的对话
- 先确认你理解了什么，再说你要做什么
- 遇到模糊的地方，用"我的理解是……对吗？"来确认，而不是用表单追问
- 拒绝废话和套话，直接说重点
- 用老板的视角思考，不是用客服的视角服务

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【意图理解原则（最重要）】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**第一步：先理解，再执行**
老板说的话，往往只是冰山一角。你要理解的是：
1. 字面意思（说了什么）
2. 真实目的（想要什么结果）
3. 隐含约束（没说但默认的条件）
4. 最佳路径（达到目的的最高效方式）

举例：
老板说"去猪八戒找单子" →
  字面：浏览猪八戒平台
  真实目的：找到高价值、我们能接的外包项目并拿下
  隐含约束：符合我们的技术栈，客单价合理
  最佳路径：扫描+筛选+评估+定价+主动投标

老板说"做个增长方案" →
  真实目的：需要一套可执行的获客/留存策略
  不要只给策略框架，要给具体行动清单

**第二步：合理假设，大胆行动**
信息不完整时，用合理假设填充，在回复中标注。
绝对不能因为"没有预算数字"就停下来不动。

好的习惯：
✅ "我假设你的预期客单价在 500-2000 元区间，基于这个展开..."
✅ "我先按 30 天周期拆解，如果时间有调整告诉我"
❌ "请问您的预算是多少？请问目标收入是多少？请问时间线是？"（三连问）

**第三步：一次最多问一个问题**
如果真的需要确认，只问最关键的那一个。其他的合理假设。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【对话节奏】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Round 1（老板第一次说话）：
  → 理解意图，在 response 里给出"我的理解是XXX，对吗？"
  → 告诉老板你打算派哪些子公司、做什么
  → state_action 设为 "clarifying"（等待老板确认）
  → 本轮绝不派发任务

Round 2（老板确认/补充/提出新任务）：
  → 如果老板确认：state_action="dispatching"，立刻派发
  → 如果老板有调整：更新理解，再次确认
  → 如果老板是新话题：回到 Round 1

原则：**先理解确认，再派发执行。确认环节不可跳过。**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【子公司能力矩阵】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

你管理以下子公司，理解其能力本质（不要只按关键词匹配）：

growth_agency     | 增长实验、裂变机制、A/B测试、渠道搭建
research_agency   | 竞品调研、市场情报、用户洞察、趋势分析
edu_agency        | 教培产品设计、课程体系、招生、转化漏斗优化
ads_agency        | 付费广告投放（抖音/微信/小红书）、素材、人群定向、CAC优化
crm_agency        | 私域运营、用户分层、复购、流失召回
bd_agency         | 商务拓展、外包接单、异业合作、资源置换
ip_agency         | 个人IP、内容创作、社媒矩阵、KOL策略
dev_agency        | 代码开发、自动化脚本、部署、API对接
ai_agency         | Prompt工程、Agent设计、RAG、AI工具集成
shop_agency       | 电商/私信转化、定价策略、成交话术
data_agency       | 数据分析、报表、漏斗追踪、归因
finance_agency    | 财务管理、成本核算、利润分析、现金流
cs_agency         | 客户服务、售后、用户反馈、平台沟通
legal_agency      | 合同审查、版权保护、合规、NDA
knowledge_agency  | 知识库管理、SOP沉淀、文档归档
global_market     | 出海、台湾市场、多语言本地化
devops_agency     | 系统运维、监控告警、CI/CD、服务器

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【任务拆解标准】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

拆解一个任务时，确保每个子任务：
- 动词开头（写/分析/设计/执行/联系）
- 有明确产出物（一份文案 / 一个方案 / 一组数据）
- 可以独立执行，不依赖其他子任务完成

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【ROI 判断（内部用，不对外炫耀）】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

你内部评估 ROI，但不要在每次回复里都输出 ROI 评分。
只在两种情况下提 ROI：
1. 老板明确问"这个值不值得做"
2. 你判断这个方向明显不划算，主动提醒

ROI 阈值（内部）：composite < 3 时谨慎推进，< 1.5 时主动提醒老板。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【输出格式】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

严格输出 JSON，禁止在 JSON 前后附加任何解释文字或 markdown 代码块。

{
  "understanding": "我对老板意图的精准理解（1-2句，包含字面+真实目的）",
  "assumption": "我做了哪些合理假设（没有假设则为空字符串）",
  "decision": "GO | NO_GO | OPTIMIZE | SCALE | STOP | PIVOT | NEED_INFO | DIRECT_RESPONSE",
  "response": "给老板的自然语言回复（简洁、有温度、不废话）",
  "state_action": "dispatching | exploring | clarifying | direct_response",
  "dispatch_plan": [
    {
      "agency": "agency名称",
      "task": "具体可执行的任务描述（动词开头）",
      "priority": "high | medium | low",
      "kpi": "成功衡量标准",
      "expected_output": "预期产出物描述"
    }
  ],
  "pending_questions": ["如果需要追问，只写一个最关键的问题，其余不写"],
  "risks": ["关键风险（如有，最多2条）"],
  "score": {
    "roi": 0,
    "scalability": 0,
    "difficulty": 0,
    "composite": 0
  },
  "confidence_score": 0.0到1.0,
  "next_review": "建议下次复盘时间"
}

【特别规则】
- decision=NEED_INFO 时，pending_questions 只能有 1 条。这条问题必须是：
  具体、有洞察力的追问——你听完用户的话，发现了关键信息缺失，于是问一个能直达核心的问题。
  禁止问"请描述得更具体一些"这种废话。你应该像一位有经验的 COO，
  用户说"要变现"，你应该追问"你们现有的核心能力是什么？技术开发、内容创作、还是咨询服务？
  不同的能力对应的变现路径完全不同。"
- decision=DIRECT_RESPONSE 时，dispatch_plan 为空数组，response 里直接回答
- decision=GO 时，dispatch_plan 必须有至少 1 条任务
- response 字段是给老板看的，要像人说话，带着你的判断和理解，不要像机器输出报告
- understanding 是内部字段，可以比 response 更技术化
- 如果用户表达模糊（比如只说了一个大方向），不要猜测，不要直接派发任务，
  而是先用 NEED_INFO + 1个精准问题来确认。但如果是明确任务就直接 GO。
{{CURRENT_DATE}}
"""
@dataclass
class _TurnState:
    """统一推理循环状态（仿 Claude queryLoop State）"""
    session: SessionContext
    messages: List[Dict[str, str]]
    turn_count: int
    max_tokens_recovery: int   # 已执行恢复次数
    transition: str            # 'first_turn' | 'max_tokens_recovery'


class CEOReasoningLoop:
    """
    CEO 多轮推理循环（v8: 统一 while-true 状态机）。

    用法：
        loop = CEOReasoningLoop()
        result = await loop.run(session_id, user_input)
    """

    _MAX_RECOVERY = 3  # max_tokens 最大恢复次数（仿 Claude OTK recovery）

    def __init__(self):
        self.router = ModelRouter()
        self._turn_limit = 5
        self._evolution = EvolutionEngine()
        self._progress_message_id: Optional[str] = None
        self._dated_prompt = CEO_SYSTEM_PROMPT.replace(
            "{{CURRENT_DATE}}",
            datetime.now().strftime("%Y年%m月%d日 %H:%M") + "（所有回复和引用必须基于此时间点）"
        )
        self._chat_id: Optional[str] = None

    def _publish_progress(self, current_step: int, agency: str = "", status: str = "executing"):
        """发布进度事件到 Redis Pub/Sub（非阻塞）"""
        if not self._progress_message_id:
            return
        try:
            from molib.integrations.feishu.progress_card import publish_progress_event
            publish_progress_event(
                task_id=self._progress_message_id,
                message_id=self._progress_message_id,
                current_step=current_step,
                agency=agency,
                status=status,
            )
        except Exception:
            pass

    async def run(self, session_id: str, user_input: str,
                  budget: float = None, timeline: str = None,
                  target_revenue: float = None,
                  context: Dict[str, Any] = None,
                  progress_message_id: str = None,
                  chat_id: str = None) -> Dict[str, Any]:
        """
        统一推理循环（仿 Claude Code queryLoop 架构）。

        用 while True + TurnState 替代 _first_turn / _continue_conversation 分裂。
        每次迭代: 语义路由 → LLM 调用 → 解析 → 判断下一轮 or 结束。
        内置 max_tokens 级联恢复。
        """
        self._progress_message_id = progress_message_id
        self._chat_id = chat_id

        session = await SessionStore.get_or_create(session_id)
        if budget: session.confirmed_fields["budget"] = budget
        if timeline: session.confirmed_fields["timeline"] = timeline
        if target_revenue: session.confirmed_fields["target_revenue"] = target_revenue

        state = _TurnState(
            session=session,
            messages=self._build_messages(session, user_input),
            turn_count=0,
            max_tokens_recovery=0,
            transition="first_turn",
        )
        start_time = time.time()

        # ── 统一推理循环 ──
        while True:
            s = state  # shorthand

            # ── 语义路由 (仅首轮) ──
            route = None
            if s.transition == "first_turn":
                try:
                    from molib.core.ceo.semantic_router import get_semantic_router
                    route = await get_semantic_router().route(
                        user_input,
                        session_context=str(s.session.confirmed_fields),
                        history=[{"user": h.user_input, "ceo": h.ceo_output}
                                 for h in s.session.history],
                    )
                except Exception as e:
                    logger.debug(f"语义路由跳过: {e}")

            # Layer 0: Trivial 直接回复
            if route and route.is_trivial:
                latency = round(time.time() - start_time, 2)
                return {
                    "decision": "DIRECT_RESPONSE",
                    "message": route.trivial_reply,
                    "intent_type": "trivial", "thinking": "",
                    "reasoning_chain": {
                        "understanding": "简单问候/确认，无需深度推理",
                        "assumption": "无",
                        "decision_type": "trivial",
                        "confidence": 1.0,
                        "latency_seconds": latency,
                        "pending_question": "",
                        "agencies_involved": [],
                        "risks": [],
                    },
                    "should_pass_to_ceo": False, "model_used": "semantic_router",
                    "cost": 0.0, "latency": latency,
                }

            # Layer 2: 向量缓存命中
            if route and route.route_source == "vector_cache" and route.dispatch_plan:
                s.session.task_plan = {"tasks": route.dispatch_plan}
                s.session.state = SessionState.EXECUTING
                await SessionStore.update(s.session.session_id, s.session)
                parsed = {"thinking": route.thinking, "state_action": "dispatching",
                          "response": route.ceo_response, "dispatch_plan": route.dispatch_plan}
                s.session.add_turn(user_input=user_input, ceo_output=parsed["response"],
                                   state_before=SessionState.INITIAL, state_after=s.session.state,
                                   metadata={"model": "vector_cache"})
                return await self._build_response(s.session, parsed, start_time)

            # ── CEO LLM 调用（意图驱动推理深度）──
            routing_ctx = ""
            if route and route.route_source == "ceo_llm":
                routing_ctx = (f"\n路由分析: {route.thinking}\n"
                               f"推荐子公司: {', '.join(p.get('agency','') for p in route.dispatch_plan)}")

            # 意图 → 推理策略映射（CEO 自主选择深度）
            reasoning, tok_lim, llm_model = self._select_reasoning_strategy(user_input)
            system_prompt = self._build_dynamic_prompt(s.session, s.turn_count, s.transition)
            result = await self.router.call_async(
                prompt=f"{user_input}{routing_ctx}",
                system=system_prompt,
                task_type="ceo_decision",
                reasoning_effort=reasoning,
                max_tokens=tok_lim,
                model=llm_model,
            )

            parsed = self._parse_llm_response(result["text"])
            state_before = s.session.state

            # ── 恢复: max_tokens 命中时注入续写消息 ──
            output_len = len(result.get("text", ""))
            if output_len >= 5000 and s.max_tokens_recovery < self._MAX_RECOVERY:
                s.max_tokens_recovery += 1
                s.messages.append({
                    "role": "user",
                    "content": ("Continue from where you left off. No apologies, no summary. "
                                "Output the remaining JSON fields directly.")
                })
                state = _TurnState(session=s.session, messages=s.messages,
                                   turn_count=s.turn_count + 1,
                                   max_tokens_recovery=s.max_tokens_recovery,
                                   transition="max_tokens_recovery")
                logger.info(f"max_tokens recovery #{s.max_tokens_recovery}")
                continue

            # ── 更新会话状态 ──
            s.session = self._update_state(s.session, parsed, user_input)
            self._last_understanding = parsed.get("understanding", "")
            self._last_assumption = parsed.get("assumption", "")
            await SessionStore.update(s.session.session_id, s.session)

            s.session.add_turn(
                user_input=user_input,
                ceo_output=parsed.get("response", ""),
                state_before=state_before, state_after=s.session.state,
                metadata={"model": result.get("model", ""),
                          "latency": result.get("latency", 0),
                          "recovery_count": s.max_tokens_recovery},
            )

            # ── 异步记录路由结果 ──
            dispatch_plan = (s.session.task_plan or {}).get("tasks", [])
            if dispatch_plan and route:
                try:
                    from molib.core.ceo.semantic_router import get_semantic_router
                    asyncio.ensure_future(get_semantic_router().record_route_outcome(
                        user_input, dispatch_plan,
                        [p.get("agency", "") for p in dispatch_plan],
                    ))
                except Exception:
                    pass

            # ── 判断是否继续 ──
            if parsed.get("state_action") == "clarifying":
                # 有未决问题，等待用户回复，终止本轮
                return await self._build_response(s.session, parsed, start_time)

            return await self._build_response(s.session, parsed, start_time)

    def _build_reasoning_chain(self, parsed: dict, decision: str, latency: float) -> dict:
        """构建可展示的推理链（仿 Claude thinking block 透明度）"""
        return {
            "understanding": parsed.get("understanding", "") or "未记录",
            "assumption": parsed.get("assumption", "") or "无",
            "decision_type": decision,
            "confidence": parsed.get("confidence_score", parsed.get("score", {}).get("composite", 0)),
            "latency_seconds": latency,
            "pending_question": (parsed.get("pending_questions", []) or [None])[0] or "",
            "agencies_involved": [p.get("agency", "?") for p in parsed.get("dispatch_plan", [])],
            "risks": parsed.get("risks", []) or [],
        }

    # ── 意图 → 推理策略映射（CEO 自主判断深度）──
    _REASONING_STRATEGY = {
        "trivial":   ("low",    1000, "deepseek-v4-flash"),   # 简单问候，秒回
        "query":     ("low",    1000, "deepseek-v4-flash"),   # 状态查询，快速
        "task":      ("medium", 4000, "deepseek-v4-pro"),     # 明确任务，中等推理
        "decision":  ("medium", 4000, "deepseek-v4-pro"),     # CEO 决策，中深度（平衡速度与质量）
        "need_info": ("low",    2000, "deepseek-v4-flash"),   # 追问澄清，快速
        "emergency": ("high",   8000, "deepseek-v4-pro"),     # 紧急情况，全速
    }

    def _select_reasoning_strategy(self, user_input: str) -> tuple:
        """CEO 根据用户意图自主选择推理深度和模型"""
        try:
            from molib.core.ceo.intent_processor import IntentProcessor
            processor = IntentProcessor()
            intent_result = processor.process(user_input)
            intent = intent_result.intent_type.value if hasattr(intent_result.intent_type, 'value') else str(intent_result.intent_type)
            strategy = self._REASONING_STRATEGY.get(intent, ("medium", 4000, None))
            reason, toks, model = strategy
            if intent != "trivial":
                logger.info(f"[CEO意图] intent={intent} → reasoning={reason} tokens={toks} model={model or 'auto'}")
            return strategy
        except Exception:
            return ("medium", 4000, None)  # 兜底：中等推理

    def _build_dynamic_prompt(self, session, turn_count: int, transition: str) -> str:
        """分层系统提示词: 基础人格 + 会话状态 + 日期 + 历史摘要"""
        prompt = self._dated_prompt
        # 注入会话状态
        confirmed = session.confirmed_fields
        if confirmed:
            parts = ", ".join(f"{k}={v}" for k, v in confirmed.items() if v)
            if parts:
                prompt += f"\n\n【当前已确认信息】{parts}"
        if session.history:
            last = session.history[-1]
            prompt += (f"\n【上轮决策】action={last.state_after.value if last.state_after else '?'}, "
                       f"turn={turn_count}")
        return prompt

    def _build_messages(self, session, user_input: str) -> List[Dict[str, str]]:
        """构建消息列表（最近 6 轮历史）"""
        messages = []
        for turn in session.history[-6:]:
            messages.append({"role": "user", "content": turn.user_input})
            messages.append({"role": "assistant", "content": turn.ceo_output})
        messages.append({"role": "user", "content": user_input})
        return messages

    def _parse_llm_response(self, text: str) -> Dict[str, Any]:
        """解析 LLM 返回的 JSON（从末尾找最后一个有效 JSON 块）"""
        # 去掉 DeepSeek reasoning 可能包裹的 markdown 代码块
        clean = text.strip()
        if "```json" in clean:
            blocks = clean.split("```json")
            clean = blocks[-1].split("```")[0].strip()
        elif "```" in clean:
            parts = clean.split("```")
            if len(parts) >= 2:
                clean = parts[-2].strip()

        # 从末尾向前找 JSON：取每对 { } 尝试解析
        candidates = []
        depth = 0
        last_start = -1
        for i, ch in enumerate(clean):
            if ch == "{":
                if depth == 0:
                    last_start = i
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0 and last_start >= 0:
                    candidates.append((last_start, i + 1))

        # 从最后一个候选开始尝试解析
        for start, end in reversed(candidates):
            try:
                parsed = json.loads(clean[start:end])
                if isinstance(parsed, dict) and "response" in parsed:
                    return parsed
            except json.JSONDecodeError:
                continue

        # 尝试任何有效的 JSON 对象
        for start, end in reversed(candidates):
            try:
                return json.loads(clean[start:end])
            except json.JSONDecodeError:
                continue

        # 解析失败，返回默认结构（包含最小推理链）
        return {
            "thinking": "",
            "state_action": "direct_response",
            "response": text[:800],
            "understanding": "LLM 输出未能按预期格式解析，使用原始文本",
            "assumption": "无",
            "confidence_score": 0.3,
            "confirmed_fields": {},
            "pending_questions": [],
            "dispatch_plan": [],
            "risks": ["JSON 解析失败，回复可能不完整"],
        }

    def _update_state(self, session: SessionContext, parsed: Dict[str, Any],
                      user_input: str) -> SessionContext:
        """更新会话状态"""
        action = parsed.get("state_action", "")
        dispatch_plan = parsed.get("dispatch_plan", [])
        thinking = parsed.get("thinking", "")

        # 智能覆盖：从 thinking 或用户输入判断是否需要派发
        wants_dispatch = any(
            kw in thinking for kw in ["派发", "立即派发", "直接派发", "dispatch", "任务拆解并派", "安排"]
        ) or any(
            kw in user_input for kw in ["帮我", "请写", "请做", "帮我写", "制作", "生成", "分析", "开发"]
        )
        logger.info(f"_update_state: action={action}, wants_dispatch={wants_dispatch}, thinking_has_dispatch={any(kw in thinking for kw in ['派发','立即派发','直接派发','dispatch'])}, user_input_has_task={any(kw in user_input for kw in ['帮我','请写','请做','帮我写'])}")

        # 如果 LLM 输出中已经确认了多个字段且无追问，也当作 dispatch 信号
        confirmed = parsed.get("confirmed_fields", {})
        no_questions = not parsed.get("pending_questions", [])
        if len(confirmed) >= 2 and no_questions and not wants_dispatch:
            wants_dispatch = True

        if wants_dispatch:
            action = "dispatching"
            # 如果 LLM 没输出 dispatch_plan，自动生成
            if not dispatch_plan:
                dispatch_plan = self._infer_dispatch_plan(user_input)

        if not action:
            action = "exploring"

        if action == "dispatching":
            session.transition(SessionState.EXECUTING)
            session.task_plan = {
                "tasks": dispatch_plan,
                "confirmed_fields": session.confirmed_fields.copy(),
            }
        elif action == "clarifying":
            session.transition(SessionState.CLARIFYING)
        elif action == "planning":
            session.transition(SessionState.PLANNING)
        elif action == "direct_response":
            pass  # 保持当前状态
        else:
            # 默认：探索状态
            if session.state == SessionState.INITIAL:
                session.transition(SessionState.EXPLORING)

        return session

    async def _build_response(self, session: SessionContext, parsed: Dict[str, Any],
                              start_time: float) -> Dict[str, Any]:
        """构建返回结果"""
        action = parsed.get("state_action", "direct_response")
        latency = round(time.time() - start_time, 2)

        # 直接回复
        if action == "direct_response" or session.state == SessionState.INITIAL:
            return {
                "decision": "DIRECT_RESPONSE",
                "message": parsed.get("response", "已收到您的消息"),
                "intent_type": "trivial",
                "thinking": (parsed.get("thinking", "") or "")[:200],
                "reasoning_chain": self._build_reasoning_chain(parsed, "direct_response", latency),
                "should_pass_to_ceo": False,
                "model_used": "ceo_reasoning_loop",
                "cost": 0.0,
                "latency": latency,
            }

        # 任务派发（需求已确认）→ 实际执行 Manager → Worker 链路
        if session.task_plan or action == "dispatching":
            # 生成人性化任务简报
            task_brief = self._build_task_brief(session, parsed)

            # 注入任务简报到 session 上下文，供 Manager/Worker 使用
            session.task_plan["task_brief"] = task_brief

            # 进度事件: 任务拆解完成
            self._publish_progress(1)
            # 进度事件: Worker 执行开始
            agencies_list = [t.get("agency", "") for t in session.task_plan.get("tasks", [])]
            self._publish_progress(2, agency=",".join(agencies_list), status="执行中")

            execution_result = await self._execute_dispatch(session, parsed)

            # 进度事件: 结果聚合
            self._publish_progress(3)

            # 进化引擎: 异步沉淀知识卡片（fire-and-forget，不阻塞回复）
            try:
                results = execution_result.get("results", [])
                for r in results:
                    if r.get("status") == "success":
                        asyncio.create_task(self._evolution.evaluate(r))
            except Exception:
                pass

            # 进度事件: CEO 整合
            self._publish_progress(4)

            # CEO 综合所有子公司输出，生成最终完整回答
            final_answer = await self._synthesize_final_answer(
                session, execution_result, parsed
            )

            # 进度事件: 完成
            self._publish_progress(5, status="完成")

            return {
                "decision": "GO",
                "message": final_answer,
                "intent_type": "decision",
                "thinking": (parsed.get("thinking", "") or "")[:200],
                "reasoning_chain": self._build_reasoning_chain(parsed, "dispatching", latency),
                "tasks": session.task_plan.get("tasks", []),
                "target_agency": self._determine_target_agency(session.task_plan.get("tasks", [])),
                "score": {"roi": 7, "scalability": 6, "difficulty": 5, "composite": 6.3},
                "strategy": [parsed.get("response", "")],
                "confirmed_fields": session.task_plan.get("confirmed_fields", {}),
                "should_pass_to_ceo": True,
                "model_used": "ceo_reasoning_loop",
                "cost": 0.0,
                "latency": latency,
                "session_id": session.session_id,
                "execution_result": execution_result,
            }

        # 继续对话（需要更多信息）
        return {
            "decision": "NEED_INFO",
            "message": parsed.get("response", "请补充更多信息"),
            "intent_type": "need_info",
            "thinking": (parsed.get("thinking", "") or "")[:200],
            "reasoning_chain": self._build_reasoning_chain(parsed, "clarifying", latency),
            "questions": parsed.get("pending_questions", []),
            "confirmed_fields": session.confirmed_fields.copy(),
            "pending_questions": parsed.get("pending_questions", []),
            "session_state": session.state.value,
            "should_pass_to_ceo": False,
            "model_used": "ceo_reasoning_loop",
            "cost": 0.0,
            "latency": latency,
            "session_id": session.session_id,
        }

    def _infer_dispatch_plan(self, user_input: str) -> List[Dict[str, str]]:
        """根据用户输入自动推断需要派发的子公司任务"""
        keywords_mapping = {
            "ip": ["文案", "小红书", "公众号", "内容", "推广", "营销文案", "标题", "脚本", "抖音"],
            "research": ["调研", "竞品", "市场", "分析", "研究", "报告"],
            "dev": ["开发", "代码", "脚本", "部署", "Docker", "API", "bug"],
            "data": ["数据", "报表", "分析", "指标", "可视化"],
            "growth": ["增长", "营销", "获客", "转化", "裂变", "渠道"],
            "ads": ["广告", "投放", "竞价", "出价", "CAC"],
            "edu": ["课程", "培训", "教学", "学习"],
            "shop": ["电商", "定价", "成交", "话术", "转化"],
            "product": ["产品", "SaaS", "MVP", "标准化"],
            "ai": ["Prompt", "提示词", "AI", "Agent", "RAG"],
            "legal": ["合同", "协议", "合规", "法律", "版权"],
            "finance": ["财务", "预算", "成本", "利润", "ROI"],
            "crm": ["私域", "会员", "复购", "用户分层"],
            "cs": ["客服", "投诉", "售后", "退款", "反馈"],
            "bd": ["合作", "报价", "谈判", "商务"],
            "global": ["出海", "海外", "翻译", "繁体", "跨境"],
            "devops": ["运维", "宕机", "监控", "容器", "重启"],
        }

        tasks = []
        for agency, kws in keywords_mapping.items():
            if any(kw in user_input for kw in kws):
                tasks.append({"agency": agency, "task": user_input, "priority": "medium"})

        # 默认回退
        if not tasks:
            tasks.append({"agency": "research", "task": user_input, "priority": "medium"})

        return tasks

    def _build_task_brief(self, session: SessionContext, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """
        为人性化任务派发生成个性化任务简报。

        包含：任务背景、具体要求、重点关注、协作说明、期望标准。
        语气专业直接，像给靠谱同事下清晰指令。
        """
        user_input = session.history[-1].user_input if session.history else ""
        confirmed_fields = session.confirmed_fields
        thinking = parsed.get("thinking", "")
        tasks = session.task_plan.get("tasks", [])

        brief = {
            "task_background": (
                f"用户需求：{user_input[:300]}\n"
                f"CEO分析：{thinking[:200]}"
            ),
            "specific_requirements": "\n".join(
                f"- [{t.get('agency', '')}] {t.get('task', '')}"
                for t in tasks
            ) if tasks else "根据任务描述完成相应工作",
            "key_focus_areas": self._extract_focus_areas(user_input),
            "collaboration_notes": self._build_collaboration_notes(tasks),
            "expected_standards": "内容完整、可直接使用、有明确的行动建议",
            "confirmed_fields": confirmed_fields,
        }
        return brief

    @staticmethod
    def _extract_focus_areas(user_input: str) -> List[str]:
        """从用户输入中提取重点关注领域（启发式关键词）。"""
        focus_map = {
            "质量": "注重输出质量而非数量",
            "速度": "优先快速交付",
            "创新": "尝试新视角和新方法",
            "数据": "用数据支撑结论",
            "实操": "提供可直接落地的方案",
            "成本": "控制成本在合理范围",
        }
        areas = [desc for kw, desc in focus_map.items() if kw in user_input]
        if not areas:
            areas = ["全面覆盖用户需求", "确保输出可直接使用"]
        return areas

    @staticmethod
    def _build_collaboration_notes(tasks: List[Dict]) -> str:
        """为多子公司派发生成协作说明。"""
        if len(tasks) <= 1:
            return "独立完成任务"
        agencies = [t.get("agency", "") for t in tasks]
        notes = []
        if "research" in agencies and any(a in agencies for a in ("ip", "product", "growth")):
            notes.append("research 子公司的调研结论应作为其他子公司执行的前提参考")
        if "ip" in agencies and "research" in agencies:
            notes.append("ip 子公司的内容产出应基于 research 的调研结果")
        if "dev" in agencies and "product" in agencies:
            notes.append("dev 子公司的技术实现应考虑 product 的需求设计")
        return "; ".join(notes) if notes else f"各子公司并行执行，CEO最后汇总：{', '.join(agencies)}"

    async def _synthesize_final_answer(
        self,
        session: SessionContext,
        execution_result: Dict[str, Any],
        parsed: Dict[str, Any],
    ) -> str:
        """
        v7: 使用 ceo_synthesizer_v7 合成最终回答。
        """
        user_input = session.history[-1].user_input if session.history else ""
        from molib.core.ceo.ceo_synthesizer_v7 import synthesize_results, _strip_for_feishu
        understanding = parsed.get("understanding", "")
        synthesized = await synthesize_results(
            user_input=user_input,
            execution_result=execution_result,
            model_router=self.router,
            understanding=understanding,
        )
        if execution_result is not None:
            execution_result["synthesized"] = synthesized
        return _strip_for_feishu(synthesized)
    @staticmethod

    def _determine_target_agency(tasks: List[Dict]) -> str:
        """从任务列表确定目标子公司"""
        if tasks:
            return tasks[0].get("agency", "")
        return ""

    async def _synthesize_results(self, execution_result: Dict[str, Any],
                                   user_input: str) -> str:
        """
        调用 LLM 综合多子公司执行结果，生成用户友好的汇总回复。
        """
        results = execution_result.get("results", [])
        if not results:
            return "任务已执行，但未收到结果。"

        # 构建各子公司输出摘要
        summaries = []
        for r in results:
            agency = r.get("agency", "unknown")
            status = r.get("status", "pending")
            output = r.get("output", "")
            if status == "pending_approval":
                summaries.append(f"[{agency}] 已提交审批")
            elif status in ("executed", "completed", "success"):
                preview = output[:500] if output else "（无输出）"
                summaries.append(f"[{agency}] {status}: {preview}")
            else:
                error = r.get("error", "")
                summaries.append(f"[{agency}] {status}: {error or '未知错误'}")

        combined = "\n\n".join(summaries)
        prompt = f"""用户原始需求：{user_input}

以下各子公司的执行结果：
{combined}

请用简洁、专业的语言汇总给用户。格式：
1. 一句话总结整体结果
2. 列出各子公司的完成情况
3. 如有未完成项，说明原因
"""
        try:
            result = await self.router.call_async(
                prompt=prompt,
                system="你是墨麟AI系统的CEO，负责汇总多子公司执行结果给用户。用专业、简洁的中文回复。",
                task_type="ceo_decision",
            )
            return result.get("text", combined)
        except Exception as e:
            logger.warning(f"LLM 合成失败，返回原始结果: {e}")
            return combined

    async def _execute_dispatch(self, session: SessionContext, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """实际调用 Manager → Worker 执行链 — asyncio.gather 并发派发所有子公司"""
        if not MANAGER_DISPATCHER_AVAILABLE:
            logger.warning("ManagerDispatcher 不可用，跳过执行")
            return {"status": "skipped", "reason": "ManagerDispatcher not available"}

        tasks = session.task_plan.get("tasks", [])
        if not tasks:
            return {"status": "skipped", "reason": "No tasks in dispatch plan"}


        async def _dispatch_one(task_info: Dict) -> Dict[str, Any]:
            """派发单个任务到 Manager（并发单元）"""
            agency_id = task_info.get("agency", "")
            task_desc = task_info.get("task", "")
            priority = task_info.get("priority", "medium")

            try:
                task_brief = session.task_plan.get("task_brief", {})
                task = Task(
                    task_id=f"ceo_dispatch_{session.session_id}_{agency_id}",
                    task_type=agency_id,
                    payload={
                        "description": task_desc,
                        "context": session.confirmed_fields.copy(),
                        "user_input": session.history[-1].user_input if session.history else "",
                        "task_brief": task_brief,
                    },
                    priority=priority,
                    requester="ceo",
                )

                logger.info(f"CEO 并行派发任务到 {agency_id} Manager: {task_desc}")

                manager_id = f"{agency_id}_manager" if not agency_id.endswith("_manager") else agency_id
                result = await dispatch_to_manager(manager_id, task)

                if result is None or result.status == "error":
                    logger.info(f"Manager {agency_id} 不可用，回退到 LLM 直接执行")
                    try:
                        llm_result = await self.router.call_async(
                            prompt=task_desc,
                            system=f"你是墨麟AI智能系统的{agency_id}子公司专业执行者。请直接完成以下任务，输出完整的结果。",
                            task_type="content_creation" if agency_id == "ip" else "default",
                        )
                        return {
                            "agency": agency_id,
                            "status": "llm_executed",
                            "output": llm_result.get("text", ""),
                            "model": llm_result.get("model", ""),
                            "error": "",
                        }
                    except Exception as llm_e:
                        logger.error(f"LLM 回退也失败 [{agency_id}]: {llm_e}")
                        return {
                            "agency": agency_id,
                            "status": "error",
                            "output": "",
                            "model": "",
                            "error": f"Manager error: {result.error if result else 'N/A'}, LLM fallback: {llm_e}",
                        }

                elif result.status == "pending_approval":
                    import uuid
                    approval_id = str(uuid.uuid4())[:8]
                    try:
                        from molib.infra.memory.sqlite_client import SQLiteClient
                        db = SQLiteClient()
                        await db.add_pending_approval(
                            approval_id=approval_id,
                            title=f"{agency_id} 任务审批",
                            description=task_desc,
                            task_type=agency_id,
                            agency_id=agency_id,
                        )
                    except Exception as approval_e:
                        logger.error(f"审批记录创建失败: {approval_e}")
                    return {
                        "agency": agency_id,
                        "status": "pending_approval",
                        "output": f"已提交审批，审批ID: {approval_id}",
                        "approval_id": approval_id,
                        "error": "",
                    }

                else:
                    # 从 ManagerResult 中提取实际内容（不转 repr，不截断）
                    output = self._extract_manager_output(result)
                    return {
                        "agency": agency_id,
                        "status": result.status,
                        "output": output,
                        "error": getattr(result, "error", ""),
                    }

            except Exception as task_e:
                import traceback
                logger.error(f"单个任务执行失败 [{agency_id}]: {task_e}\n{traceback.format_exc()}")
                return {
                    "agency": agency_id,
                    "status": "error",
                    "output": "",
                    "model": "",
                    "error": str(task_e),
                }

        # 并发执行所有任务
        coroutines = [_dispatch_one(t) for t in tasks]
        raw_results = await asyncio.gather(*coroutines, return_exceptions=True)

        execution_results = []
        for task_info, raw in zip(tasks, raw_results):
            agency_id = task_info.get("agency", "")
            if isinstance(raw, Exception):
                logger.error(f"并发任务异常 [{agency_id}]: {raw}")
                execution_results.append({
                    "agency": agency_id,
                    "status": "error",
                    "output": "",
                    "error": str(raw),
                })
            else:
                execution_results.append(raw)

        return {"status": "executed", "results": execution_results}

    @staticmethod
    def _extract_manager_output(result) -> str:
        """从 ManagerResult 中提取可读内容 — 不截断，不转 repr"""
        raw = getattr(result, "output", "")
        if isinstance(raw, str):
            return raw
        if not isinstance(raw, dict):
            return str(raw)

        parts = []
        # 聚合摘要 + 完整内容（优先取完整报告，摘要作为兜底）
        content = raw.get("content", "") or raw.get("report", "")
        if content and isinstance(content, str) and len(content) > 20:
            parts.append(content)
        else:
            summary = raw.get("summary", "")
            if summary:
                parts.append(summary)

        # Worker 子结果
        worker_outputs = raw.get("worker_outputs", [])
        for wo in worker_outputs:
            wo_out = wo.get("output", "")
            if isinstance(wo_out, dict):
                for key in ("report", "summary", "text", "content", "result"):
                    val = wo_out.get(key, "")
                    if val and isinstance(val, str) and len(val) > 15:
                        parts.append(val)
                        break
            elif isinstance(wo_out, str) and len(wo_out) > 15:
                parts.append(wo_out)

        # 直接子结果列表
        results = raw.get("results", [])
        for r in results:
            r_out = getattr(r, "output", "") if hasattr(r, "output") else r.get("output", "") if isinstance(r, dict) else ""
            if isinstance(r_out, dict):
                for key in ("report", "summary", "text", "content", "result"):
                    val = r_out.get(key, "")
                    if val and isinstance(val, str) and len(val) > 15:
                        parts.append(val)
                        break
            elif isinstance(r_out, str) and len(r_out) > 15:
                parts.append(r_out)

        return "\n\n".join(parts) if parts else str(raw)
