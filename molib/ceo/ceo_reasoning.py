"""
墨麟OS — CEO 意图推理引擎
============================
⚠️ DEPRECATED — 此文件已废弃，不再使用。

弃用原因：
- 多轮对话LLM推理已被 IntentRouter 的四层架构替代
- IntentRouter 整合了问候拦截(L0) + 缓存(L1) + LLM语义(L2) + 关键词(L3)
- ceo_reasoning.py 的 CEOAction/Session 管理已不再需要

替代方案：
    from molib.ceo.intent_router import IntentRouter, IntentResult
    router = IntentRouter(llm_client)
    result = await router.analyze("用户输入")

此文件保留仅作参考，不会被任何代码导入（除 ceo.py 兼容层外）。
ceo.py 已重写为直接使用 IntentRouter。

废弃日期: 2026-05-08
"""

import json
import re
import uuid
import time
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("molin.ceo.reasoning")


# ── 子公司能力画像 ──────────────────────────────────────────────

SUBSIDIARY_CAPABILITIES = {
    "墨笔文创": "内容创作：品牌文案、SEO文章、软文、小红书/公众号/知乎内容、文创产品文案",
    "墨韵IP": "IP孵化与管理：IP企划、版权授权、IP衍生开发、品牌联名企划",
    "墨图设计": "视觉设计：UI设计、海报设计、封面图、品牌视觉、LOGO设计、排版",
    "墨播短视频": "短视频制作与增长：短视频脚本、剪辑方案、抖音运营、投流策略、直播方案",
    "墨声配音": "音频制作与配音：AI配音、旁白录制、播客制作、有声书制作、音效设计",
    "墨域私域": "私域运营与CRM：私域运营方案、用户分层、自动化营销、社群SOP、RFM分析",
    "墨声客服": "智能客服：客服应答设计、FAQ体系、工单SOP、满意度追踪",
    "墨链电商": "电商运营：商品上架、店铺运营、闲鱼商品管理、订单管理",
    "墨学教育": "在线教育：课程设计、学习路径规划、课件生成、测验设计、个性化辅导",
    "墨码开发": "软件开发：Python开发、Web开发、API对接、自动化脚本、技术咨询",
    "墨维运维": "基础设施运维：部署方案、Docker化、K8s管理、监控搭建、CI/CD",
    "墨安安全": "信息安全：安全审计、渗透测试、漏洞扫描、权限方案",
    "墨算财务": "财务核算：预算规划、成本分析、财务报表、ROI分析",
    "墨商BD": "商务拓展：招投标方案、商业计划书、商务合作方案、客户谈判",
    "墨海出海": "出海本地化：多语言翻译、英文文案、海外社媒运营、跨境合规",
    "墨研竞情": "行业研究：行业研究报告、竞品分析、趋势洞察、技术情报",
    "墨律法务": "法务合规：合同审查、NDA生成、隐私政策、合规审计",
    "墨脑知识": "知识管理：知识库搭建、文档管理方案、企业搜索",
    "墨测数据": "数据与测试：数据分析报告、BI仪表盘、可视化、自动化测试",
    "墨梦AutoDream": "AI自动化：AI工作流搭建、Agent设计、Prompt工程、模型微调",
}

# 子公司归属VP
SUBSIDIARY_TO_VP = {
    "墨笔文创": "VP营销", "墨韵IP": "VP营销", "墨图设计": "VP营销",
    "墨播短视频": "VP营销", "墨声配音": "VP营销",
    "墨域私域": "VP运营", "墨声客服": "VP运营", "墨链电商": "VP运营",
    "墨学教育": "VP运营",
    "墨码开发": "VP技术", "墨维运维": "VP技术", "墨安安全": "VP技术",
    "墨梦AutoDream": "VP技术",
    "墨算财务": "VP财务",
    "墨商BD": "VP战略", "墨海出海": "VP战略", "墨研竞情": "VP战略",
    "墨律法务": "共同", "墨脑知识": "共同", "墨测数据": "共同",
}


@dataclass
class CEOAction:
    """CEO 推理动作"""
    action_type: str               # "clarify" | "dispatch" | "chat" | "refuse"
    message: str                   # 给用户的回复
    subsidiaries: list[str] = field(default_factory=list)
    deliverable_spec: str = ""     # 交付物规格说明
    confidence: float = 0.0        # 决策置信度 0-1
    context_clues: list[str] = field(default_factory=list)  # 推理线索
    plan: dict | None = None       # 结构化计划（从 deepagents Planning Tool 吸收）

    def to_output(self) -> dict:
        result = {
            "action_type": self.action_type,
            "message": self.message,
            "subsidiaries": self.subsidiaries,
            "deliverable_spec": self.deliverable_spec,
            "confidence": self.confidence,
        }
        if self.plan:
            result["plan"] = self.plan
        return result


# ── 对话上下文存储（内存） ─────────────────────────────────────

SESSION_DIR = Path.home() / ".hermes" / "ceo_sessions"
SESSION_DIR.mkdir(parents=True, exist_ok=True)

# 内存会话
_sessions: dict[str, list[dict]] = {}


def _get_session(session_id: str) -> list[dict]:
    if session_id not in _sessions:
        _sessions[session_id] = []
    return _sessions[session_id]


def _save_session(session_id: str, history: list[dict]):
    session_file = SESSION_DIR / f"{session_id}.json"
    session_file.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _sessions[session_id] = history


def _load_session(session_id: str) -> list[dict]:
    session_file = SESSION_DIR / f"{session_id}.json"
    if session_file.exists():
        try:
            data = json.loads(session_file.read_text(encoding="utf-8"))
            _sessions[session_id] = data
            return data
        except (json.JSONDecodeError, OSError):
            pass
    return []


# ── CEO 推理引导词（每条轮换，避免模式固化） ────────────────────

REASONING_PROMPTS = [
    """你是墨麟OS的CEO决策引擎。你的任务是基于20家子公司的能力，对用户请求进行深度推理。

子公司能力清单：
{capabilities}

你需要输出严格的JSON（不要markdown）：
{{
    "action": "clarify" | "dispatch" | "chat" | "refuse",
    "message": "给用户的回复（中文，清晰友好）",
    "subsidiaries": ["子公司1", "子公司2"],
    "deliverable_spec": "只有dispatch时需要：描述用户到底想要什么交付物，具体规格",
    "confidence": 0.95,
    "reasoning": "你的推理过程"
}}

决策规则：
1. **chat** — 纯聊天/问候/日常闲聊，不需要任何子公司参与
2. **clarify** — 用户说了一个模糊请求（如"帮我做个东西"），信息不足以确定子公司的。返回的message要引导用户说清楚要什么
3. **dispatch** — 你可以根据对话历史+当前输入，非常确定地判断出用户的意图和需要的子公司。返回具体的子公司列表和交付物规格
4. **refuse** — 请求超出能力范围或违反安全规则

关键原则：
- 不要假装你能做你不确定的事。不确定就clarify
- 仔细阅读对话历史，注意用户之前提供的细节
- 可以同时调度多家子公司，如果有多个子任务
- 置信度：非常确定0.9+，基本确定0.7-0.9，有点不确定0.5-0.7
- 如果用户之前clarify了你已经问过的信息，在后续消息中提取并使用它""",
]


@dataclass
class CEOReasoningSession:
    """
    CEO 多轮推理会话。

    每个用户对话创建一次，保存对话历史。
    CEO 每轮基于完整上下文中推理决策。
    """

    session_id: str
    history: list[dict] = field(default_factory=list)

    @classmethod
    def create(cls, llm_client=None) -> "CEOReasoningSession":
        sid = f"ceo-{uuid.uuid4().hex[:12]}"
        session = cls(session_id=sid)
        session._llm = llm_client
        return session

    @classmethod
    def load(cls, session_id: str, llm_client=None) -> Optional["CEOReasoningSession"]:
        history = _load_session(session_id)
        if not history:
            return None
        session = cls(session_id=session_id, history=history)
        session._llm = llm_client
        return session

    def set_llm_client(self, llm_client):
        self._llm = llm_client

    async def reason(self, user_input: str) -> CEOAction:
        """
        基于当前会话上下文进行推理。

        每轮推理会：
        1. 将用户输入加入对话历史
        2. 构建完整上下文（子公司能力 + 历史对话）
        3. 调 LLM 推理
        4. 解析结果
        5. 将推理结果加入对话历史
        """
        if not self._llm:
            return CEOAction(
                action_type="chat",
                message="CEO 引擎未配置 LLM，无法进行智能推理。",
            )

        # 加入当前输入
        self.history.append({"role": "user", "content": user_input})

        # 构建推理上下文
        caps_text = "\n".join(
            f"- {name}: {desc}"
            for name, desc in SUBSIDIARY_CAPABILITIES.items()
        )

        history_text = ""
        if len(self.history) > 1:
            history_lines = []
            for msg in self.history[:-1]:  # 不包括最后一个（当前输入已在上面）
                role = "用户" if msg["role"] == "user" else "CEO"
                history_lines.append(f"{role}: {msg['content']}")
            if history_lines:
                history_text = "对话历史：\n" + "\n".join(history_lines[-6:])  # 最近3轮

        prompt_text = REASONING_PROMPTS[0].format(capabilities=caps_text)

        messages = []
        if history_text:
            messages.append({
                "role": "system",
                "content": f"{prompt_text}\n\n{history_text}\n\n用户最新消息: {user_input}\n\n请基于完整上下文推理并输出JSON。"
            })
        else:
            messages.append({
                "role": "system",
                "content": f"{prompt_text}\n\n用户消息: {user_input}\n\n请推理并输出JSON。"
            })

        # 调 LLM 推理（用 Flash，路由决策不需要 Pro）
        try:
            response = self._llm.chat(messages, model="deepseek-v4-flash")
        except Exception as e:
            logger.error("[CEO] 推理失败: %s", e)
            action = CEOAction(
                action_type="chat",
                message="抱歉，我暂时无法处理您的请求，请稍后再试。",
                confidence=0.0,
            )
            self._append_action(action)
            return action

        # 解析 JSON
        action = self._parse_response(response, user_input)

        # 加入对话历史
        self._append_action(action)

        # 持久化
        self.save()

        return action

    def _parse_response(self, response: str, user_input: str) -> CEOAction:
        """解析 LLM 回复为 CEOAction"""
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if not json_match:
            # 解析失败，保守处理
            return CEOAction(
                action_type="clarify",
                message="我理解您的需求，但我需要更多信息来准确判断。请告诉我您具体想要做什么？",
                confidence=0.3,
                context_clues=["LLM回复非JSON格式，保守回退到澄清"],
            )

        try:
            data = json.loads(json_match.group(0))
        except json.JSONDecodeError:
            return CEOAction(
                action_type="clarify",
                message="抱歉，我需要再确认一下。您能详细描述一下您想要什么吗？",
                confidence=0.3,
            )

        action_type = data.get("action", "chat")
        message = data.get("message", "")
        subsidiaries_raw = data.get("subsidiaries", [])
        deliverable_spec = data.get("deliverable_spec", "")
        confidence = min(float(data.get("confidence", 0.5)), 1.0)
        reasoning = data.get("reasoning", "")

        # 验证子公司名称
        valid_subs = [s for s in subsidiaries_raw if s in SUBSIDIARY_CAPABILITIES]

        # 如果是 dispatch 但没有有效子公司，转 clarify
        if action_type == "dispatch" and not valid_subs:
            action_type = "clarify"
            message = message or "您说的这个需求我初步判断可能需要一些专业能力，但能再说具体一点吗？比如您想要什么类型的结果？"
            confidence = min(confidence, 0.5)

        # 提取线索（从用户输入和推理中提取有用信息）
        clues = self._extract_clues(user_input, reasoning)

        # 如果是 dispatch，自动生成结构化计划
        plan_data = None
        if action_type == "dispatch" and valid_subs:
            try:
                from molib.agencies.planning import decompose_task
                plan = decompose_task(deliverable_spec or user_input)
                plan_data = plan.to_dict()
            except Exception:
                pass

        return CEOAction(
            action_type=action_type,
            message=message,
            subsidiaries=valid_subs,
            deliverable_spec=deliverable_spec,
            confidence=confidence,
            context_clues=clues,
            plan=plan_data,
        )

    def _extract_clues(self, user_input: str, reasoning: str) -> list[str]:
        """提取推理线索"""
        clues = []
        clue_patterns = [
            r"似乎是(.*?)(?:的需求|的任务)",
            r"属于(.*?)(?:领域|范畴)",
            r"涉及(.*?)(?:方面|维度)",
            r"推测.*?(用户|对方|您).*?想要(.*?)(?:，|。)",
            r"从.*?可以看(?:出|到).*?(?:用户|对方).*?需要(.*?)(?:，|。)",
        ]
        for p in clue_patterns:
            m = re.search(p, reasoning)
            if m:
                clues.append(m.group(0)[:50])
        return clues[:3]

    def _append_action(self, action: CEOAction):
        """将推理动作加入历史"""
        entry = {
            "role": "assistant",
            "action": action.action_type,
            "content": action.message,
            "subsidiaries": action.subsidiaries,
            "deliverable_spec": action.deliverable_spec,
            "confidence": action.confidence,
        }
        self.history.append(entry)

    def save(self):
        """持久化会话"""
        session_file = SESSION_DIR / f"{self.session_id}.json"
        session_file.write_text(
            json.dumps(self.history, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get_last_action(self) -> Optional[CEOAction]:
        """获取上一次推理动作"""
        if not self.history:
            return None
        last = self.history[-1]
        if last.get("role") == "assistant" and "action" in last:
            return CEOAction(
                action_type=last["action"],
                message=last["content"],
                subsidiaries=last.get("subsidiaries", []),
                deliverable_spec=last.get("deliverable_spec", ""),
                confidence=last.get("confidence", 0.5),
            )
        return None

    def is_completed(self) -> bool:
        """会话是否已完成（dispatch 或 refuse）"""
        last = self.get_last_action()
        if not last:
            return False
        return last.action_type in ("dispatch", "refuse")


def get_or_create_session(session_id: str = None, llm_client=None) -> CEOReasoningSession:
    """获取已有会话或创建新会话"""
    if session_id:
        session = CEOReasoningSession.load(session_id, llm_client)
        if session:
            return session
    return CEOReasoningSession.create(llm_client)
