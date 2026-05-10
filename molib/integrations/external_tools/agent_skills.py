"""
Agent Skills Integrator
封装 agent-skills 仓库中的能力（例如代码审查、调试、测试、规划），并加载到内存中供 Worker 直接调用。
"""
import os
from loguru import logger
from molib.integrations.adapters.skill_adapter import SkillAdapter

class AgentSkillsIntegrator:
    tool_name = "agent_skills"
    def __init__(self):
        # 指向外部 hermes-agent skills 中的 software-development 技能
        self.skills_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "external", "hermes-agent", "skills", "software-development",
        )
        self.adapter = SkillAdapter(self.skills_dir)
        self._initialize()

    def _initialize(self):
        """初始化加载所有的标准化技能"""
        if not os.path.exists(self.skills_dir):
            logger.warning(f"Agent-skills directory not found: {self.skills_dir}")
            self._load_virtual_skills()
        else:
            self.adapter.scan_and_load()
            # 加载每个子技能目录的 SKILL.md
            for subdir in os.listdir(self.skills_dir):
                subdir_path = os.path.join(self.skills_dir, subdir)
                if os.path.isdir(subdir_path) and not subdir.startswith("__"):
                    self._load_skill_md(subdir, subdir_path)

        logger.info(f"AgentSkillsIntegrator initialized with {len(self.adapter.loaded_skills)} skills.")

    def _load_virtual_skills(self):
        """当物理技能目录不存在时，提供基于 SKILL.md 的虚拟技能"""
        virtual = {
            "code_reviewer": "Review code using AST analysis and systematic debugging.",
            "refactoring_wizard": "Automated code refactoring with subagent-driven development.",
            "test_driven_development": "Write tests before implementation using TDD methodology.",
            "planning_wizard": "Generate structured development plans with risk analysis.",
        }
        self.adapter.loaded_skills.update(virtual)

    def _load_skill_md(self, name: str, skill_dir: str):
        """加载 SKILL.md 文件作为技能文档"""
        skill_md_path = os.path.join(skill_dir, "SKILL.md")
        if os.path.exists(skill_md_path):
            try:
                with open(skill_md_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.adapter.loaded_skills[name] = content[:500]  # 截断到 500 字符
            except Exception as e:
                logger.warning(f"Failed to load SKILL.md for {name}: {e}")

    def get_available_commands(self) -> list:
        return list(self.adapter.loaded_skills.keys())

    def get_skill_system_prompt_addon(self) -> str:
        """获取所有可用外部技能的文档，拼接到 Worker 的 System Prompt 中"""
        addon = "\n\n[External Engineering Skills Available]:\n"
        for name in self.adapter.loaded_skills:
            doc = self.adapter.get_skill_doc(name)
            addon += f"- {name}: {doc.strip()[:100]}\n"
        return addon

_agent_skills = AgentSkillsIntegrator()

def get_agent_skills() -> AgentSkillsIntegrator:
    return _agent_skills
