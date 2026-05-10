"""
Skill Adapter
用于动态加载外部代码库（如 agent-skills）中的特定技能逻辑，并将其包装为墨麟兼容的 Prompt 闭包或函数。
"""
import os
import importlib.util
from typing import Dict, Any, Optional
from loguru import logger

class SkillAdapter:
    def __init__(self, skills_dir: str):
        self.skills_dir = skills_dir
        self.loaded_skills: Dict[str, Any] = {}
        
    def scan_and_load(self):
        """扫描外部技能库目录并尝试加载 Python 技能模块"""
        if not os.path.exists(self.skills_dir):
            logger.warning(f"Skill directory not found: {self.skills_dir}")
            return
            
        for filename in os.listdir(self.skills_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                skill_name = filename[:-3]
                filepath = os.path.join(self.skills_dir, filename)
                try:
                    spec = importlib.util.spec_from_file_location(skill_name, filepath)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        self.loaded_skills[skill_name] = module
                        logger.debug(f"Loaded external skill: {skill_name}")
                except Exception as e:
                    logger.warning(f"Failed to load external skill {skill_name}: {e}")
                    
    def get_skill_doc(self, skill_name: str) -> str:
        """获取外部技能的使用文档或 System Prompt 增强"""
        if skill_name in self.loaded_skills:
            module = self.loaded_skills[skill_name]
            return getattr(module, "__doc__", f"External skill: {skill_name}")
        return ""

    def invoke_skill(self, skill_name: str, func_name: str, *args, **kwargs) -> Any:
        """反射调用外部技能的特定函数"""
        if skill_name in self.loaded_skills:
            module = self.loaded_skills[skill_name]
            if hasattr(module, func_name):
                func = getattr(module, func_name)
                return func(*args, **kwargs)
        raise ValueError(f"Skill {skill_name} or function {func_name} not found")
