"""
墨麟OS — P4 商业闭环：订单生命周期 + 人工门控
================================================

1. OrderSM: 订单状态机 (DISCOVERED → COMPLETED)
2. HumanGateManager: 仅在定价确认和最终交付审核时推送飞书卡片
3. PlatformScanner: 平台线索扫描器（含闲鱼/猪八戒/程序员客栈）

零空转原则：扫描按需执行，人工门控仅在需要你决策时推送。
"""

import json
import time
import logging
import uuid
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger("molin.business.p4")


# ═══════════════════════════════════════════════════════════════════
# 1. 订单生命周期状态机
# ═══════════════════════════════════════════════════════════════════


class OrderStatus(Enum):
    DISCOVERED = "discovered"      # 发现商机线索
    EVALUATING = "evaluating"      # 评估可行性
    PRICING = "pricing"            # 待定价确认（人工门控点 #1）
    BIDDING = "bidding"            # 投标/报价中
    NEGOTIATING = "negotiating"    # 谈判中
    WON = "won"                    # 中标/成交
    IN_PROGRESS = "in_progress"    # 执行中
    REVIEWING = "reviewing"        # 待交付审核（人工门控点 #2）
    REVISING = "revising"          # 修改中
    COMPLETED = "completed"        # 已完成
    LOST = "lost"                  # 丢单/未中标
    CANCELLED = "cancelled"        # 取消


# 状态转换规则
VALID_TRANSITIONS = {
    OrderStatus.DISCOVERED: [OrderStatus.EVALUATING, OrderStatus.LOST],
    OrderStatus.EVALUATING: [OrderStatus.PRICING, OrderStatus.BIDDING, OrderStatus.LOST],
    OrderStatus.PRICING: [OrderStatus.BIDDING, OrderStatus.LOST, OrderStatus.NEGOTIATING],
    OrderStatus.BIDDING: [OrderStatus.WON, OrderStatus.LOST, OrderStatus.NEGOTIATING, OrderStatus.REVIEWING],
    OrderStatus.NEGOTIATING: [OrderStatus.WON, OrderStatus.LOST, OrderStatus.PRICING],
    OrderStatus.WON: [OrderStatus.IN_PROGRESS, OrderStatus.CANCELLED],
    OrderStatus.IN_PROGRESS: [OrderStatus.REVIEWING, OrderStatus.REVISING, OrderStatus.CANCELLED],
    OrderStatus.REVIEWING: [OrderStatus.COMPLETED, OrderStatus.CANCELLED, OrderStatus.REVISING],
    OrderStatus.REVISING: [OrderStatus.REVIEWING, OrderStatus.IN_PROGRESS],
    OrderStatus.COMPLETED: [],
    OrderStatus.LOST: [],
    OrderStatus.CANCELLED: [],
}


@dataclass
class HumanGate:
    """人工门控节点"""
    gate_type: str                 # "pricing" | "delivery"
    order_id: str
    status: str = "pending"        # pending | approved | rejected | modified
    context: dict = field(default_factory=dict)
    created_at: float = 0.0
    resolved_at: Optional[float] = None
    resolution: Optional[str] = None  # 用户回复


@dataclass
class Order:
    """完整订单"""
    id: str
    source: str                    # "xianyu" | "zbj" | "upwork" | "direct"
    title: str
    description: str
    status: OrderStatus = OrderStatus.DISCOVERED
    estimated_value: float = 0.0   # 预估金额 (¥)
    actual_value: float = 0.0      # 成交金额
    priority: int = 0              # 0-10, 10最高
    tags: list[str] = field(default_factory=list)

    # 时间线
    created_at: float = 0.0
    updated_at: float = 0.0
    timeline: list[dict] = field(default_factory=list)

    # 人工门控
    gates: list[HumanGate] = field(default_factory=list)
    pending_gate: Optional[HumanGate] = None

    # 交付物
    deliverables: list[str] = field(default_factory=list)
    final_deliverable: Optional[str] = None

    def transition_to(self, new_status: OrderStatus) -> bool:
        """状态转换，含校验"""
        if new_status not in VALID_TRANSITIONS.get(self.status, []):
            logger.warning(
                "[Order] 非法状态转换: %s → %s (order=%s)",
                self.status.value, new_status.value, self.id,
            )
            return False

        old = self.status
        self.status = new_status
        self.updated_at = time.time()
        self.timeline.append({
            "time": datetime.now().isoformat(),
            "event": f"状态变更: {old.value} → {new_status.value}",
        })
        return True


# ── 订单仓库（持久化 JSON） ───────────────────────────────────

ORDERS_DIR = Path.home() / ".hermes" / "orders"
ORDERS_DIR.mkdir(parents=True, exist_ok=True)


class OrderStore:
    """订单存储 — JSON 持久化"""

    def __init__(self):
        self._orders: dict[str, Order] = {}
        self._load()

    def _load(self):
        """从 JSON 加载所有订单"""
        idx_path = ORDERS_DIR / "_index.json"
        if idx_path.exists():
            try:
                index = json.loads(idx_path.read_text(encoding="utf-8"))
                for oid in index.get("order_ids", []):
                    order_file = ORDERS_DIR / f"{oid}.json"
                    if order_file.exists():
                        data = json.loads(order_file.read_text(encoding="utf-8"))
                        self._orders[oid] = self._from_dict(data)
            except (json.JSONDecodeError, OSError):
                pass

    def _save_order(self, order: Order):
        """持久化单个订单"""
        order_file = ORDERS_DIR / f"{order.id}.json"
        order_file.write_text(
            json.dumps(self._to_dict(order), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        # 更新索引
        idx_path = ORDERS_DIR / "_index.json"
        index = {"order_ids": list(self._orders.keys()), "updated_at": time.time()}
        idx_path.write_text(
            json.dumps(index, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _to_dict(self, order: Order) -> dict:
        return {
            "id": order.id,
            "source": order.source,
            "title": order.title,
            "description": order.description,
            "status": order.status.value,
            "estimated_value": order.estimated_value,
            "actual_value": order.actual_value,
            "priority": order.priority,
            "tags": order.tags,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "timeline": order.timeline,
            "gates": [
                {"gate_type": g.gate_type, "order_id": g.order_id,
                 "status": g.status, "context": g.context,
                 "created_at": g.created_at}
                for g in order.gates
            ],
            "deliverables": order.deliverables,
            "final_deliverable": order.final_deliverable,
        }

    def _from_dict(self, data: dict) -> Order:
        order = Order(
            id=data["id"],
            source=data["source"],
            title=data["title"],
            description=data.get("description", ""),
            status=OrderStatus(data.get("status", "discovered")),
            estimated_value=data.get("estimated_value", 0),
            actual_value=data.get("actual_value", 0),
            priority=data.get("priority", 0),
            tags=data.get("tags", []),
            created_at=data.get("created_at", 0),
            updated_at=data.get("updated_at", 0),
        )
        order.timeline = data.get("timeline", [])
        order.gates = [
            HumanGate(
                gate_type=g["gate_type"], order_id=g["order_id"],
                status=g.get("status", "pending"),
                context=g.get("context", {}),
                created_at=g.get("created_at", 0),
            )
            for g in data.get("gates", [])
        ]
        order.deliverables = data.get("deliverables", [])
        order.final_deliverable = data.get("final_deliverable")
        return order

    def create(self, source: str, title: str, description: str,
               estimated_value: float = 0, tags: list[str] = None) -> Order:
        """创建新订单"""
        now = time.time()
        order = Order(
            id=f"ORD-{uuid.uuid4().hex[:8].upper()}",
            source=source,
            title=title,
            description=description,
            estimated_value=estimated_value,
            tags=tags or [],
            created_at=now,
            updated_at=now,
            status=OrderStatus.DISCOVERED,
        )
        order.timeline.append({
            "time": datetime.now().isoformat(),
            "event": f"创建订单 (来源: {source})",
        })
        self._orders[order.id] = order
        self._save_order(order)
        return order

    def get(self, order_id: str) -> Optional[Order]:
        return self._orders.get(order_id)

    def list(self, status: Optional[OrderStatus] = None,
             source: Optional[str] = None) -> list[Order]:
        orders = list(self._orders.values())
        if status:
            orders = [o for o in orders if o.status == status]
        if source:
            orders = [o for o in orders if o.source == source]
        orders.sort(key=lambda o: o.updated_at, reverse=True)
        return orders

    def update_status(self, order_id: str, new_status: OrderStatus) -> bool:
        order = self._orders.get(order_id)
        if not order:
            return False
        ok = order.transition_to(new_status)
        if ok:
            self._save_order(order)
        return ok

    def stats(self) -> dict:
        """订单统计"""
        total = len(self._orders)
        by_status = {}
        for o in self._orders.values():
            s = o.status.value
            by_status[s] = by_status.get(s, 0) + 1
        total_value = sum(o.actual_value for o in self._orders.values())
        pending_gates = sum(
            1 for o in self._orders.values()
            if o.pending_gate and o.pending_gate.status == "pending"
        )
        return {
            "total": total,
            "by_status": by_status,
            "total_value": total_value,
            "pending_gates": pending_gates,
        }


# ═══════════════════════════════════════════════════════════════════
# 2. 人工门控管理器
# ═══════════════════════════════════════════════════════════════════


class HumanGateManager:
    """
    人工门控 — 仅在两个关键节点停下来等你确认。

    Gate #1 (Pricing): 定价确认
       触发: EVALUATING → PRICING 时
       行动: 飞书推送互动卡片 → 你确认金额后自动投标
       L0: <¥100 自动放行
       L1: ¥100-500 提示但自动
       L2: >¥500 必须确认

    Gate #2 (Delivery): 最终交付审核
       触发: IN_PROGRESS → REVIEWING 时
       行动: 飞书推送交付物卡片 → 你审核后自动完成
    """

    def __init__(self, order_store: OrderStore, feishu_sender=None):
        self.orders = order_store
        self._feishu = feishu_sender  # 飞书消息发送器

    def set_feishu_sender(self, sender):
        self._feishu = sender

    async def request_pricing(self, order_id: str) -> dict:
        """
        请求定价确认。

        自动规则：
        - L0 (<¥100): 自动通过，不打扰你
        - L1 (¥100-500): 发飞书通知，但自动继续
        - L2 (>¥500): 必须等确认
        """
        order = self.orders.get(order_id)
        if not order:
            return {"error": "订单不存在"}

        value = order.estimated_value

        # L0: 自动放行
        if value < 100:
            order.transition_to(OrderStatus.EVALUATING)
            order.transition_to(OrderStatus.BIDDING)
            self.orders._save_order(order)
            return {
                "action": "auto_pass",
                "note": f"小额订单 ¥{value}，自动放行投标",
                "order_id": order_id,
                "status": "bidding",
            }

        # 创建门控
        gate = HumanGate(
            gate_type="pricing",
            order_id=order_id,
            context={
                "title": order.title,
                "estimated_value": value,
                "source": order.source,
                "description": order.description[:200],
            },
            created_at=time.time(),
        )
        order.gates.append(gate)
        order.pending_gate = gate

        # L1: 通知但自动继续
        if value <= 500:
            order.transition_to(OrderStatus.EVALUATING)
            order.transition_to(OrderStatus.BIDDING)
            self.orders._save_order(order)
            note = f"¥{value} 已自动放行投标（¥100-500 区间只需通知）"
            if self._feishu:
                await self._feishu(
                    f"🔔 订单报价通知\n{order.title}\n¥{value} | 来源: {order.source}\n已自动投标，无需确认"
                )
            return {
                "action": "notify_and_continue",
                "note": note,
                "order_id": order_id,
                "status": "bidding",
            }

        # L2: 必须等你确认
        order.transition_to(OrderStatus.EVALUATING)
        order.transition_to(OrderStatus.PRICING)
        self.orders._save_order(order)

        msg = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"  🔔 报价需要你确认 · L2审批\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"· 订单：{order.title}\n"
            f"· 金额：¥{value}\n"
            f"· 来源：{order.source}\n"
            f"· 描述：{order.description[:100]}\n\n"
            f"⚡ 操作：批准 / 拒绝 / 修改金额\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )

        if self._feishu:
            await self._feishu(msg)

        return {
            "action": "awaiting_approval",
            "note": f"¥{value} 需确认后才能投标",
            "order_id": order_id,
            "status": "pricing",
            "message": msg,
        }

    async def request_delivery_review(self, order_id: str,
                                       deliverable: str) -> dict:
        """
        请求交付审核。

        无论金额大小，交付物必须经过你的肉眼审核。
        """
        order = self.orders.get(order_id)
        if not order:
            return {"error": "订单不存在"}

        # 保存交付物
        order.final_deliverable = deliverable

        gate = HumanGate(
            gate_type="delivery",
            order_id=order_id,
            context={
                "title": order.title,
                "deliverable_length": len(deliverable),
                "actual_value": order.actual_value,
            },
            created_at=time.time(),
        )
        order.gates.append(gate)
        order.pending_gate = gate
        order.transition_to(OrderStatus.REVIEWING)
        self.orders._save_order(order)

        msg = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"  ✅ 交付物待审核 · L2审批\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"· 订单：{order.title}\n"
            f"· 金额：¥{order.actual_value or order.estimated_value}\n"
            f"· 大小：{len(deliverable)} 字符\n\n"
            f"⚡ 操作：批准交付 / 需要修改\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )

        if self._feishu:
            await self._feishu(msg)

        return {
            "action": "awaiting_review",
            "note": "交付物待你审核",
            "order_id": order_id,
            "status": "reviewing",
            "deliverable": deliverable[:200],
            "message": msg,
        }

    def resolve_pricing(self, order_id: str, decision: str,
                        modified_value: float = None) -> bool:
        """解决定价门控"""
        order = self.orders.get(order_id)
        if not order or not order.pending_gate:
            return False
        if order.pending_gate.gate_type != "pricing":
            return False

        if decision == "approve":
            order.transition_to(OrderStatus.BIDDING)
        elif decision == "reject":
            order.transition_to(OrderStatus.LOST)
        elif decision == "modify" and modified_value:
            order.estimated_value = modified_value
            order.transition_to(OrderStatus.BIDDING)
        else:
            return False

        order.pending_gate.status = "resolved"
        order.pending_gate.resolved_at = time.time()
        order.pending_gate.resolution = decision
        order.pending_gate = None
        self.orders._save_order(order)
        return True

    def resolve_delivery(self, order_id: str, decision: str) -> bool:
        """解决交付门控"""
        order = self.orders.get(order_id)
        if not order or not order.pending_gate:
            return False
        if order.pending_gate.gate_type != "delivery":
            return False

        if decision == "approve":
            order.transition_to(OrderStatus.COMPLETED)
        elif decision == "revise":
            order.transition_to(OrderStatus.REVISING)
        else:
            return False

        order.pending_gate.status = "resolved"
        order.pending_gate.resolved_at = time.time()
        order.pending_gate.resolution = decision
        order.pending_gate = None
        self.orders._save_order(order)
        return True

    def stats(self) -> dict:
        """人工门控统计"""
        gates_info = {"total": 0, "pending": 0, "resolved": 0}
        for order in self.orders.list():
            for g in order.gates:
                gates_info["total"] += 1
                if g.status == "pending":
                    gates_info["pending"] += 1
                else:
                    gates_info["resolved"] += 1
        return gates_info


# ═══════════════════════════════════════════════════════════════════
# 3. 平台扫描器
# ═══════════════════════════════════════════════════════════════════


@dataclass
class Lead:
    """商机线索"""
    source: str
    title: str
    description: str
    budget: float                     # 预算 (¥)
    url: str = ""
    platform_order_id: str = ""
    match_score: int = 0              # 0-100 匹配度
    matched_subsidiaries: list[str] = field(default_factory=list)


# 子公司匹配规则（用于平台线索自动评分）
SUBSIDIARY_SKILL_MAP = {
    "墨笔文创": ["文案", "写作", "文章", "内容", "软文", "推广文案", "SEO"],
    "墨图设计": ["设计", "海报", "logo", "封面", "UI", "视觉", "包装"],
    "墨码开发": ["开发", "编程", "Python", "小程序", "网站", "API", "自动化"],
    "墨商BD": ["商业计划书", "BP", "投标", "竞标", "方案"],
    "墨学教育": ["课程", "培训", "教学", "课件"],
    "墨研竞情": ["调研", "研究", "报告", "分析", "市场"],
    "墨声配音": ["配音", "音频", "旁白", "播客"],
    "墨播短视频": ["视频", "剪辑", "短视频", "抖音"],
    "墨增增长": ["推广", "投流", "SEO", "营销", "增长"],
    "墨域私域": ["社群", "私域", "用户运营"],
}


class PlatformScanner:
    """
    平台线索扫描器 — 从闲鱼/猪八戒/程序员客栈等平台抓取商机。

    当前实现为结构化线索搜索 + 匹配度评分。
    真实浏览器自动化扫描由 Hermes Agent 的 browser 工具执行。
    """

    def __init__(self, order_store: OrderStore, gate_manager: HumanGateManager):
        self.orders = order_store
        self.gates = gate_manager

    def score_lead(self, title: str, description: str) -> tuple[int, list[str]]:
        """
        计算线索与子公司技能的匹配度。

        Returns:
            (match_score, matched_subsidiaries)
        """
        text = f"{title} {description}".lower()
        total_score = 0
        matched = []

        for sub, keywords in SUBSIDIARY_SKILL_MAP.items():
            sub_score = 0
            for kw in keywords:
                if kw.lower() in text:
                    sub_score += 15
            if sub_score > 0:
                total_score += sub_score
                matched.append(sub)

        return min(total_score, 100), matched

    async def process_lead(self, source: str, title: str,
                            description: str, budget: float,
                            url: str = "") -> Optional[Order]:
        """
        处理一条线索：评分 → 创建订单 → 进入定价流程。

        高分线索（>=50）自动创建订单并触发报价流程。
        低分线索跳过。
        """
        score, subs = self.score_lead(title, description)

        if score < 30:
            logger.info("[Scanner] 低分跳过: %s (score=%d)", title[:40], score)
            return None

        # 创建订单
        order = self.orders.create(
            source=source,
            title=title,
            description=description[:500],
            estimated_value=budget,
            tags=subs,
        )

        logger.info("[Scanner] 🎯 订单创建: %s | %s (score=%d, budget=¥%.0f)",
                    order.id, title[:40], score, budget)

        # 创建订单后先评估
        order.transition_to(OrderStatus.EVALUATING)
        order.priority = min(10, max(1, score // 10))
        self.orders._save_order(order)

        # 进入定价
        await self.gates.request_pricing(order.id)

        return order

    def list_high_value_leads(self) -> list[Lead]:
        """列出待处理的高价值线索（从存储读取活跃订单）"""
        leads = []
        for order in self.orders.list():
            if order.status in (OrderStatus.DISCOVERED, OrderStatus.EVALUATING):
                leads.append(Lead(
                    source=order.source,
                    title=order.title,
                    description=order.description,
                    budget=order.estimated_value,
                    match_score=order.priority * 10,
                    matched_subsidiaries=order.tags,
                ))
        return leads
