"""
Hermes OS — 子公司 Agency 基类
基于 molin-ai-intelligent-system 适配 Hermes OS 生态
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class Task:
    task_id: str
    task_type: str
    payload: dict
    priority: str = "medium"
    requester: str = "hermes"

@dataclass
class AgencyResult:
    task_id: str
    agency_id: str
    status: str  # success / error / pending_approval
    output: dict = field(default_factory=dict)
    cost: float = 0.0
    latency: float = 0.0
    error: Optional[str] = None
    needs_approval: bool = False

class BaseAgency(ABC):
    agency_id: str = "base"
    agency_name: str = "基础子公司"
    trigger_keywords: List[str] = []
    molin_owner: str = ""
    
    def __init__(self):
        self._skills = []
    
    def get_identity_prompt(self) -> str:
        return f"你是墨麟集团的{self.agency_name}部门负责人"
    
    def enrich_task_context(self, task: Task) -> str:
        payload = task.payload or {}
        desc = payload.get("description", str(payload))
        return f"CEO 派我来处理：{desc}\n任务类型：{task.task_type}"
    
    def load_skills(self) -> List[str]:
        """加载本子公司对应的 SKILL.md"""
        if self._skills:
            return self._skills
        
        import os
        from pathlib import Path
        
        skills_dir = Path(os.path.expanduser("~/.hermes/skills"))
        if not skills_dir.exists():
            return []
        
        # 搜索本子公司对应的 skill
        for skill_file in skills_dir.rglob("SKILL.md"):
            content = skill_file.read_text()
            if f"molin_owner: {self.molin_owner}" in content:
                self._skills.append(str(skill_file))
        
        return self._skills
    
    @abstractmethod
    async def execute(self, task: Task) -> AgencyResult:
        pass
