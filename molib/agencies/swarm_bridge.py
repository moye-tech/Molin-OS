"""
Swarm Bridge — 跨子公司 Handoff 编排系统
==========================================

SwarmBridge 提供跨子公司工作流编排能力：
1. 注册跨子公司 handoff 通路（register_handoff）
2. 多 Agency 工作流编排（orchestrate）：支持线性链 + 扇出
3. 列出所有已注册的通路（list_handoffs）
4. ASCII 流程图可视化（visualize）
5. 预定义的 SWARM_PATTERNS 工作流模板

CLI 入口：
    python -m molib swarm list       # 列出所有通路
    python -m molib swarm run        # 运行预定义工作流
    python -m molib swarm visualize  # ASCII 流程图

集成 HandoffManager：注册的 handoff 自动同步到 HandoffManager，
确保与现有 handoff 系统兼容。
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("molin.swarm_bridge")

# ═══════════════════════════════════════════════════════════════
# HandoffRecord — 跨子公司 handoff 通路追踪
# ═══════════════════════════════════════════════════════════════


@dataclass
class HandoffRecord:
    """跨子公司 handoff 通路记录

    追踪一次注册的跨子公司通路，包括触发统计。
    与 molib.agencies.handoff.HandoffRecord（单次执行记录）不同，
    此 record 用于追踪通路的注册和统计。
    """
    source: str                     # 源子公司名称（中文，如 '墨研竞情'）
    target: str                     # 目标子公司名称（中文，如 '墨笔文创'）
    condition: dict = field(default_factory=dict)  # 触发条件规则
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_triggered: str | None = None  # 最后一次触发时间
    trigger_count: int = 0          # 累计触发次数

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "condition": self.condition,
            "created_at": self.created_at,
            "last_triggered": self.last_triggered,
            "trigger_count": self.trigger_count,
        }


# ═══════════════════════════════════════════════════════════════
# SWARM_PATTERNS — 预定义的多 Agency 工作流
# ═══════════════════════════════════════════════════════════════

SWARM_PATTERNS: dict[str, dict[str, Any]] = {
    "content_full_pipeline": {
        "name": "全内容流水线",
        "description": "从情报采集到私域分发的完整内容链路",
        "type": "linear",
        "chain": [
            "墨研竞情",   # 1. 情报采集
            "墨笔文创",   # 2. 内容创作
            "墨图设计",   # 3. 视觉设计
            "墨播短视频", # 4. 短视频制作
            "墨域私域",   # 5. 私域分发
        ],
    },
    "customer_response": {
        "name": "客诉响应链",
        "description": "客服→财务→电商的客诉处理链路",
        "type": "linear",
        "chain": [
            "墨声客服",   # 1. 客服响应
            "墨算财务",   # 2. 财务核算
            "墨链电商",   # 3. 电商执行
        ],
    },
    "crisis_response": {
        "name": "危机响应链",
        "description": "安全→法务→运维的危机处理链路",
        "type": "linear",
        "chain": [
            "墨安安全",   # 1. 安全评估
            "墨律法务",   # 2. 法务审查
            "墨维运维",   # 3. 运维执行
        ],
    },
}


# ═══════════════════════════════════════════════════════════════
# SwarmBridge — 跨子公司 Handoff 编排引擎
# ═══════════════════════════════════════════════════════════════


class SwarmBridge:
    """跨子公司 Handoff 编排引擎。

    功能：
    - register_handoff(source, target, condition) — 注册跨子公司通路
    - orchestrate(task, context) — 多 Agency 工作流编排
    - list_handoffs() — 列出所有通路
    - visualize() — ASCII 流程图

    所有注册的 handoff 自动同步到 HandoffManager，
    确保与现有 handoff 路由系统兼容。
    """

    def __init__(self):
        # 通路注册表: {(source, target): HandoffRecord}
        self._pathways: dict[tuple[str, str], HandoffRecord] = {}
        # 预定义模式缓存
        self._patterns: dict[str, dict] = dict(SWARM_PATTERNS)
        # 图结构：source -> [targets]
        self._graph: dict[str, list[str]] = defaultdict(list)
        # 入度：target -> count（用于拓扑排序）
        self._indegrees: dict[str, int] = defaultdict(int)

    # ── 注册 ───────────────────────────────────────────────

    def register_handoff(
        self,
        source_agency: str,
        target_agency: str,
        condition_rule: dict | None = None,
    ) -> HandoffRecord:
        """注册一个跨子公司 handoff 通路。

        Args:
            source_agency: 源子公司名称（中文），如 '墨研竞情'
            target_agency: 目标子公司名称（中文），如 '墨笔文创'
            condition_rule: 触发条件规则 dict，如 {'type': 'content'}

        Returns:
            HandoffRecord: 注册的通路记录

        Raises:
            ValueError: 源或目标子公司名称无效
        """
        # 验证子公司名称
        from molib.ceo.intent_router import SUBSIDIARY_PROFILES

        if source_agency not in SUBSIDIARY_PROFILES:
            valid = list(SUBSIDIARY_PROFILES.keys())
            raise ValueError(
                f"未知源子公司: '{source_agency}'，有效值: {valid}"
            )
        if target_agency not in SUBSIDIARY_PROFILES:
            valid = list(SUBSIDIARY_PROFILES.keys())
            raise ValueError(
                f"未知目标子公司: '{target_agency}'，有效值: {valid}"
            )

        key = (source_agency, target_agency)
        if key in self._pathways:
            # 更新条件
            existing = self._pathways[key]
            if condition_rule:
                existing.condition.update(condition_rule)
            logger.info(
                f"SwarmBridge: 更新已存在通路 {source_agency} → {target_agency}"
            )
            return existing

        record = HandoffRecord(
            source=source_agency,
            target=target_agency,
            condition=condition_rule or {},
        )
        self._pathways[key] = record

        # 更新图结构
        self._graph[source_agency].append(target_agency)
        self._indegrees[target_agency] += 1
        if source_agency not in self._indegrees:
            self._indegrees[source_agency] = self._indegrees.get(source_agency, 0)

        # 同步到 HandoffManager
        self._sync_to_handoff_manager(source_agency, target_agency, condition_rule)

        logger.info(
            f"SwarmBridge: 注册通路 {source_agency} → {target_agency}"
        )
        return record

    def _sync_to_handoff_manager(
        self, source: str, target: str, condition: dict | None
    ) -> None:
        """将跨子公司 handoff 同步到 HandoffManager。"""
        try:
            from molib.agencies.handoff import Handoff, HandoffManager
        except ImportError:
            return

        # 使用子公司中文名作为 tool_name
        tool_name = f"swarm_transfer_{source}_to_{target}"
        desc_cond = f" [{condition.get('type', '')}]" if condition else ""
        tool_desc = f"Swarm跨子公司Handoff: {source} → {target}{desc_cond}"

        handoff = Handoff(
            tool_name=tool_name,
            tool_description=tool_desc,
            target_worker=target,
            target_worker_name=target,
        )
        HandoffManager.register(handoff)

    def _record_trigger(self, source: str, target: str) -> None:
        """记录一次通路触发。"""
        key = (source, target)
        if key in self._pathways:
            record = self._pathways[key]
            record.trigger_count += 1
            record.last_triggered = datetime.now(timezone.utc).isoformat()

    # ── 编排 ───────────────────────────────────────────────

    def orchestrate(
        self, task: str, context: dict | None = None
    ) -> dict[str, Any]:
        """多 Agency 工作流编排。

        支持两种模式：
        1. 按预定义 pattern 名运行（如 'content_full_pipeline'）
        2. 按自定义 chain 列表运行（线性链）
        3. Fan-out：当 task 匹配多个通路时并发执行

        Args:
            task: 任务名称，可以是 pattern 名（如 'content_full_pipeline'）
                  或自定义 chain 如 ['墨研竞情', '墨笔文创', '墨图设计']
                  或普通任务字符串（自动匹配通路）
            context: 上下文数据 dict

        Returns:
            dict: 编排结果
        """
        ctx = context or {}

        # 模式 1: task 是预定义 pattern 名
        if isinstance(task, str) and task in self._patterns:
            return self._run_pattern(task, ctx)

        # 模式 2: task 是自定义 chain 列表
        if isinstance(task, list):
            return self._run_chain(task, ctx)

        # 模式 3: 从已注册通路中匹配
        return self._run_auto(task, ctx)

    def _run_pattern(self, pattern_name: str, ctx: dict) -> dict:
        """运行预定义 pattern。"""
        pattern = self._patterns[pattern_name]
        chain = pattern.get("chain", [])
        ptype = pattern.get("type", "linear")

        if ptype == "linear":
            return self._run_chain(chain, ctx, pattern_name=pattern_name)

        # 未来可扩展 fan-out / dag 等类型
        return {
            "status": "ok",
            "pattern": pattern_name,
            "mode": ptype,
            "results": [],
        }

    def _run_chain(
        self, chain: list[str], ctx: dict, pattern_name: str | None = None
    ) -> dict:
        """线性链执行：依次调用每个 Agency。"""
        from molib.ceo.intent_router import SUBSIDIARY_PROFILES

        results = []
        accumulated = dict(ctx)

        for i, agency in enumerate(chain):
            step_result = {
                "step": i + 1,
                "agency": agency,
                "status": "pending",
            }

            # 验证 Agency 存在
            if agency not in SUBSIDIARY_PROFILES:
                step_result["status"] = "skipped"
                step_result["reason"] = f"unknown_agency: {agency}"
                results.append(step_result)
                continue

            # 记录触发
            if i > 0:
                prev = chain[i - 1]
                self._record_trigger(prev, agency)

            # 模拟执行（实际执行需要 Worker 实例）
            profile = SUBSIDIARY_PROFILES[agency]
            step_result["status"] = "simulated"
            step_result["agency_role"] = profile.get("role", "")
            step_result["capabilities"] = profile.get("capabilities", [])
            step_result["context_snapshot"] = {
                k: str(v)[:100] for k, v in accumulated.items()
            }

            # 积累上下文（模拟输出传递）
            accumulated[f"_{agency}_output"] = f"[{agency}] 处理完成"
            results.append(step_result)

        return {
            "status": "ok",
            "pattern": pattern_name,
            "mode": "linear",
            "chain": chain,
            "steps": len(results),
            "results": results,
        }

    def _run_auto(self, task: str, ctx: dict) -> dict:
        """自动匹配通路执行。"""
        # 查找所有匹配的通路
        matched = []
        for (src, tgt), record in self._pathways.items():
            cond = record.condition
            if cond:
                cond_type = cond.get("type", "")
                if cond_type and cond_type in task.lower():
                    matched.append((src, tgt))
            else:
                matched.append((src, tgt))

        if not matched:
            return {
                "status": "no_match",
                "message": f"未找到匹配 '{task}' 的通路",
                "suggestion": "使用 list_handoffs() 查看所有可用通路",
            }

        # Fan-out: 并发执行所有匹配通路
        if len(matched) > 1:
            results = []
            for src, tgt in matched:
                self._record_trigger(src, tgt)
                results.append({
                    "source": src,
                    "target": tgt,
                    "status": "triggered",
                })
            return {
                "status": "fan_out",
                "mode": "parallel",
                "matched_pathways": len(matched),
                "results": results,
            }

        # 单通路
        src, tgt = matched[0]
        self._record_trigger(src, tgt)
        return {
            "status": "ok",
            "mode": "single",
            "source": src,
            "target": tgt,
            "task": task,
        }

    # ── 查询 ───────────────────────────────────────────────

    def list_handoffs(self) -> list[dict]:
        """列出所有已注册的跨子公司 handoff 通路。

        Returns:
            list[dict]: 通路列表，每个元素包含 source, target, condition 等
        """
        return [record.to_dict() for record in self._pathways.values()]

    def list_patterns(self) -> dict[str, dict]:
        """列出所有预定义工作流模式。"""
        return {
            name: {
                "name": p["name"],
                "description": p["description"],
                "type": p["type"],
                "chain": p["chain"],
            }
            for name, p in self._patterns.items()
        }

    # ── 可视化 ─────────────────────────────────────────────

    def visualize(self) -> str:
        """生成 ASCII 流程图。

        Returns:
            str: ASCII 流程图文本（可直接 print）
        """
        lines = []
        lines.append("")
        lines.append("╔══════════════════════════════════════════════════════╗")
        lines.append("║        Swarm Bridge — 跨子公司 Handoff 通路          ║")
        lines.append("╠══════════════════════════════════════════════════════╣")

        if not self._pathways:
            lines.append("║  (暂无通路)                                           ║")
        else:
            # 按 source 分组
            by_source: dict[str, list[HandoffRecord]] = defaultdict(list)
            for record in self._pathways.values():
                by_source[record.source].append(record)

            for source, records in sorted(by_source.items()):
                lines.append(f"║                                                      ║")
                lines.append(f"║  📤 {source}")
                for rec in records:
                    cond_str = ""
                    if rec.condition:
                        cond_items = [f"{k}={v}" for k, v in rec.condition.items()]
                        cond_str = f"  [{', '.join(cond_items)}]"
                    count_str = f"  (触发{rec.trigger_count}次)"
                    lines.append(f"║      └──▶ {rec.target}{cond_str}{count_str}")

        lines.append("╚══════════════════════════════════════════════════════╝")
        lines.append("")

        # 预定义模式
        lines.append("╔══════════════════════════════════════════════════════╗")
        lines.append("║        预定义工作流模式 (SWARM_PATTERNS)              ║")
        lines.append("╠══════════════════════════════════════════════════════╣")

        for name, pattern in self._patterns.items():
            lines.append(f"║                                                      ║")
            lines.append(f"║  📋 {pattern['name']} ({name})")
            lines.append(f"║     {pattern['description']}")
            chain = pattern.get("chain", [])
            chain_str = " → ".join(chain)
            lines.append(f"║     {chain_str}")

        lines.append("╚══════════════════════════════════════════════════════╝")
        lines.append("")

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# CLI — 用于注册到 molib __main__.py
# ═══════════════════════════════════════════════════════════


def cmd_swarm(args: list[str]) -> dict:
    """Swarm Bridge CLI 入口。

    用法:
        python -m molib swarm list            列出所有通路
        python -m molib swarm patterns        列出预定义模式
        python -m molib swarm run <pattern>   运行预定义工作流
        python -m molib swarm visualize       显示 ASCII 流程图
        python -m molib swarm register --source S --target T [--type C]  注册通路
    """
    bridge = SwarmBridge()

    # 默认加载预定义通路
    _load_default_pathways(bridge)

    if not args:
        return {
            "status": "ok",
            "message": "Swarm Bridge CLI",
            "usage": {
                "list": "列出所有通路",
                "patterns": "列出预定义模式",
                "run <pattern>": "运行预定义工作流",
                "visualize": "显示 ASCII 流程图",
                "register --source S --target T [--type C]": "注册通路",
            },
        }

    subcmd = args[0]
    rest = args[1:]

    if subcmd == "list":
        return {
            "pathways": bridge.list_handoffs(),
            "total": len(bridge.list_handoffs()),
        }

    if subcmd == "patterns":
        patterns = bridge.list_patterns()
        return {"patterns": patterns, "total": len(patterns)}

    if subcmd == "run":
        pattern_name = rest[0] if rest else ""
        if not pattern_name:
            return {"error": "请指定模式名: swarm run <pattern>"}
        if pattern_name not in SWARM_PATTERNS:
            return {
                "error": f"未知模式: '{pattern_name}'",
                "available": list(SWARM_PATTERNS.keys()),
            }
        result = bridge.orchestrate(pattern_name)
        return result

    if subcmd == "visualize":
        diagram = bridge.visualize()
        # 直接 print 以便查看流程图
        print(diagram)
        return {"status": "ok", "visualized": True}

    if subcmd == "register":
        source = ""
        target = ""
        cond_type = ""
        i = 0
        while i < len(rest):
            if rest[i] == "--source" and i + 1 < len(rest):
                source = rest[i + 1]
                i += 2
            elif rest[i] == "--target" and i + 1 < len(rest):
                target = rest[i + 1]
                i += 2
            elif rest[i] == "--type" and i + 1 < len(rest):
                cond_type = rest[i + 1]
                i += 2
            else:
                i += 1

        if not source or not target:
            return {"error": "请指定 --source 和 --target"}
        condition = {"type": cond_type} if cond_type else {}
        try:
            record = bridge.register_handoff(source, target, condition)
            return {"status": "ok", "pathway": record.to_dict()}
        except ValueError as e:
            return {"error": str(e)}

    return {"error": f"未知子命令: {subcmd}，支持: list | patterns | run | visualize | register"}


def _load_default_pathways(bridge: SwarmBridge) -> None:
    """从 SWARM_PATTERNS 加载预定义通路。"""
    for pattern_name, pattern in SWARM_PATTERNS.items():
        chain = pattern.get("chain", [])
        for i in range(len(chain) - 1):
            src = chain[i]
            tgt = chain[i + 1]
            try:
                bridge.register_handoff(src, tgt, {"type": pattern_name})
            except ValueError:
                # 子公司名称可能不在 SUBSIDIARY_PROFILES 中
                pass


__all__ = [
    "SwarmBridge",
    "HandoffRecord",
    "SWARM_PATTERNS",
    "cmd_swarm",
]
