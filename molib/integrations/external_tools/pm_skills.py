"""
PM Skills Integrator (phuryn/pm-skills)
产品经理技能包：PRD 模板、用户访谈框架、竞品分析方法论。
"""
from typing import Dict, Any
import os
from loguru import logger
from molib.integrations.adapters.tool_adapter import ExternalToolAdapter


class PMSkillsTool(ExternalToolAdapter):
    def __init__(self):
        super().__init__(tool_name="pm_skills")
        self.skills_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "external", "hermes-agent", "skills", "pm-skills",
        )
        self.register_command("generate_prd", self._generate_prd)
        self.register_command("user_interview", self._user_interview)
        self.register_command("competitive_analysis", self._competitive_analysis)
        self._loaded_skills = {}
        self._initialize()
        logger.info("PMSkillsTool initialized.")

    def _initialize(self):
        """加载 PM Skills 目录中的 SKILL.md 文件"""
        if not os.path.exists(self.skills_dir):
            self._load_virtual_skills()
        else:
            for subdir in os.listdir(self.skills_dir):
                subdir_path = os.path.join(self.skills_dir, subdir)
                skill_md = os.path.join(subdir_path, "SKILL.md")
                if os.path.exists(skill_md):
                    try:
                        with open(skill_md, "r", encoding="utf-8") as f:
                            self._loaded_skills[subdir] = f.read()[:500]
                    except Exception as e:
                        logger.warning(f"Failed to load SKILL.md for {subdir}: {e}")

    def _load_virtual_skills(self):
        """当物理技能目录不存在时，提供虚拟技能"""
        self._loaded_skills = {
            "prd_template": "Generate structured PRD with problem statement, goals, and success metrics.",
            "user_interview": "Create user interview frameworks with scenario-based questions.",
            "competitive_analysis": "Structured competitive analysis with feature comparison matrices.",
        }

    async def _generate_prd(self, params: Dict[str, Any]) -> Dict[str, Any]:
        product_name = params.get("product_name", "")
        description = params.get("description", "")
        if not product_name:
            raise ValueError("product_name parameter is required for PRD generation.")

        return {
            "status": "success",
            "product_name": product_name,
            "description": description,
            "framework": "standard_prd_v2",
            "skill_loaded": "prd_template" in self._loaded_skills,
        }

    async def _user_interview(self, params: Dict[str, Any]) -> Dict[str, Any]:
        target_user = params.get("target_user", "")
        scenario = params.get("scenario", "")
        if not target_user:
            raise ValueError("target_user parameter is required for user interview.")

        return {
            "status": "success",
            "target_user": target_user,
            "scenario": scenario,
            "framework": "scenario_based_interview",
            "skill_loaded": "user_interview" in self._loaded_skills,
        }

    async def _competitive_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        competitors = params.get("competitors", [])
        if not competitors:
            raise ValueError("competitors parameter is required for competitive analysis.")

        return {
            "status": "success",
            "competitors": competitors,
            "framework": "feature_comparison_matrix",
            "skill_loaded": "competitive_analysis" in self._loaded_skills,
        }


_pm_skills = PMSkillsTool()

def get_pm_skills() -> PMSkillsTool:
    return _pm_skills
