"""Skills Hub — 统一技能注册、发现与执行中心"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger

try:
    import toml
    TOML_AVAILABLE = True
except ImportError:
    TOML_AVAILABLE = False

# ── 外部工具注册 ──
EXTERNAL_TOOLS: List[Dict[str, Any]] = []

for _tool_mod, _tool_name, _tool_desc in [
    ("integrations.external_tools.web_browser", "web_browser", "实时网页浏览与信息检索"),
    ("integrations.external_tools.social_hub", "social_hub", "社媒平台命令执行（小红书/抖音/知乎）"),
    ("integrations.external_tools.vision_engine", "vision_engine", "图像生成与视觉处理"),
    ("integrations.external_tools.agent_skills", "agent_skills", "Agent 技能代码执行"),
]:
    try:
        mod = importlib.import_module(_tool_mod)
        for attr in dir(mod):
            if attr.startswith(("get_", "run_")) and callable(getattr(mod, attr)):
                func = getattr(mod, attr)
                tool_info = {"name": f"{_tool_name}.{attr}", "func": func, "description": _tool_desc}
                EXTERNAL_TOOLS.append(tool_info)
    except ImportError:
        pass


class SkillsHub:
    """技能注册与分发中心

    技能来源：
    1. agencies/ — 每个 Python Agency 自动注册为一个 Skill
    2. external_tools/ — 外部工具自动发现
    3. workers/ — Worker 子任务自动注册
    """

    def __init__(self):
        self._skills: Dict[str, Dict[str, Any]] = {}
        self._initialized = False

    def initialize(self):
        """自动发现并注册所有技能"""
        if self._initialized:
            return
        self._register_agencies_as_skills()
        self._register_external_tools()
        self._initialized = True
        logger.info(f"SkillsHub initialized with {len(self._skills)} skills")

    def _register_agencies_as_skills(self):
        """从 AGENCY_MAP 自动注册所有 Agency 为 Skill"""
        try:
            from molib.agencies.dispatcher import AGENCY_MAP
            subs_path = Path(__file__).resolve().parent.parent.parent / "config" / "subsidiaries.toml"
            toml_agencies = {}
            if TOML_AVAILABLE and subs_path.exists():
                with open(subs_path, 'r', encoding='utf-8') as f:
                    config = toml.load(f)
                for agency in config.get('agencies', []):
                    if isinstance(agency, dict) and 'id' in agency:
                        toml_agencies[agency['id']] = agency

            for aid, ag in AGENCY_MAP.items():
                cfg = toml_agencies.get(aid, {})
                self._skills[aid] = {
                    "type": "agency",
                    "id": aid,
                    "name": cfg.get("name", aid),
                    "description": cfg.get("description", f"{aid} 业务技能"),
                    "keywords": getattr(ag, 'trigger_keywords', []),
                    "agency_instance": ag,
                    "approval_level": cfg.get("approval_level", getattr(ag, 'approval_level', 'low')),
                    "cost_level": cfg.get("cost_level", getattr(ag, 'cost_level', 'low')),
                }
        except Exception as e:
            logger.warning(f"Failed to register agencies as skills: {e}")

    def _register_external_tools(self):
        """注册外部工具"""
        for tool in EXTERNAL_TOOLS:
            self._skills[tool["name"]] = {
                "type": "external_tool",
                "id": tool["name"],
                "name": tool["name"],
                "description": tool["description"],
                "func": tool["func"],
                "keywords": [tool["name"]],
            }

    def list_skills(self, skill_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出所有已注册技能

        Args:
            skill_type: 过滤类型 'agency' | 'external_tool'
        """
        results = []
        for sid, sinfo in self._skills.items():
            if skill_type and sinfo.get("type") != skill_type:
                continue
            results.append({
                "id": sid,
                "name": sinfo["name"],
                "description": sinfo["description"],
                "type": sinfo["type"],
                "keywords": sinfo.get("keywords", []),
            })
        return results

    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """获取技能详情"""
        return self._skills.get(skill_id)

    def match_skill(self, query: str) -> Optional[str]:
        """根据查询匹配最合适的技能（first-match-wins by keyword）"""
        query_lower = query.lower()
        # agency 技能优先
        for sid, sinfo in self._skills.items():
            if sinfo.get("type") != "agency":
                continue
            if any(kw.lower() in query_lower for kw in sinfo.get("keywords", [])):
                return sid
        # 外部工具
        for sid, sinfo in self._skills.items():
            if sinfo.get("type") != "external_tool":
                continue
            if any(kw.lower() in query_lower for kw in sinfo.get("keywords", [])):
                return sid
        return None

    async def execute(self, skill_id: str, task: Any) -> Any:
        """执行指定技能

        Args:
            skill_id: 技能 ID
            task: 任务对象（Task 或 dict）
        """
        skill = self._skills.get(skill_id)
        if not skill:
            return {"error": f"Skill '{skill_id}' not found"}

        if skill["type"] == "agency":
            agency = skill["agency_instance"]
            return await agency.safe_execute(task)
        elif skill["type"] == "external_tool":
            func = skill.get("func")
            if func:
                return func()
            return {"error": f"External tool '{skill_id}' has no callable"}

        return {"error": f"Unknown skill type: {skill['type']}"}


# 全局单例
_skills_hub: Optional[SkillsHub] = None


def get_skills_hub() -> SkillsHub:
    global _skills_hub
    if _skills_hub is None:
        _skills_hub = SkillsHub()
        _skills_hub.initialize()
    return _skills_hub
