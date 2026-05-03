"""
墨麟蜂群引擎 — 多Agent并行编排
==============================

基于 Swarm Engine (合并版):
- 7种蜂群角色: CEO/分析师/创作者/开发者/审阅者/发布者/监控者
- 决策矩阵: 自动匹配任务→角色→工具
- 并行执行: 独立任务并行分发
"""

import logging

logger = logging.getLogger("molin.swarm")


class SwarmRole:
    """蜂群角色"""

    def __init__(self, name: str, expertise: str, tools: list[str]):
        self.name = name
        self.expertise = expertise
        self.tools = tools


class SwarmEngine:
    """蜂群编排引擎"""

    ROLES = {
        "ceo": SwarmRole("CEO", "战略决策、资源分配", ["analyze", "decide", "delegate"]),
        "analyst": SwarmRole("分析师", "数据洞察、趋势分析", ["search", "analyze", "report"]),
        "creator": SwarmRole("创作者", "内容创作、文案撰写", ["write", "design", "generate"]),
        "developer": SwarmRole("开发者", "编码、调试、部署", ["code", "test", "deploy"]),
        "reviewer": SwarmRole("审阅者", "质量审查、安全检查", ["review", "check", "approve"]),
        "publisher": SwarmRole("发布者", "多平台发布、调度", ["publish", "schedule", "track"]),
        "monitor": SwarmRole("监控者", "系统监控、告警", ["watch", "alert", "report"]),
    }

    TASK_ROLE_MAP = {
        "content": ["creator", "reviewer", "publisher"],
        "analysis": ["analyst", "reviewer", "ceo"],
        "development": ["developer", "reviewer"],
        "publishing": ["creator", "publisher", "monitor"],
        "monitoring": ["monitor", "analyst"],
        "strategy": ["ceo", "analyst", "reviewer"],
    }

    def __init__(self):
        self.active_tasks = []

    def assign_task(self, task_type: str, description: str) -> dict:
        """分配任务给蜂群角色组"""
        roles = self.TASK_ROLE_MAP.get(task_type, ["analyst", "reviewer"])
        agents = []

        for role_name in roles:
            role = self.ROLES.get(role_name)
            if role:
                agents.append({
                    "role": role_name,
                    "expertise": role.expertise,
                    "tools": role.tools,
                })

        task = {
            "type": task_type,
            "description": description,
            "agents_assigned": agents,
            "status": "assigned",
        }
        self.active_tasks.append(task)
        logger.info(f"蜂群任务分配: {task_type} → {roles}")
        return task


# 全局实例
swarm = SwarmEngine()

def run(task: str = ""):
    """CLI入口"""
    print(f"🐝 蜂群引擎已启动")
    print(f"   7种角色就绪: CEO / 分析师 / 创作者 / 开发者 / 审阅者 / 发布者 / 监控者")
    if task:
        assigned = swarm.assign_task("strategy", task)
        print(f"   任务已分配: {[a['role'] for a in assigned['agents_assigned']]}")
    return {"swarm_ready": True, "roles": list(SwarmEngine.ROLES.keys())}
