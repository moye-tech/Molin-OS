"""
墨麟AIOS — SkillLoader (技能加载器)
参考 CowAgent (44K⭐) 模块化技能系统 + Deep Dream记忆蒸馏思路。
支持从 SKILL.md 加载技能定义、任务匹配、工具清单提取。
"""

import os
import json
import re
import yaml
from typing import Optional
from pathlib import Path
from collections import defaultdict

# ───────── 技能描述模板 ─────────
SKILL_TEMPLATE = """# {name}

## 描述
{description}

## 分类
{category}

## 能力
{capabilities}

## 工具
{tools}

## 示例
{examples}

## 前置条件
{prerequisites}

## 版本
{version}
"""

# ───────── 内建技能库 ─────────
BUILTIN_SKILLS = {
    "content_writer": {
        "name": "内容写作",
        "description": "专业内容创作，支持多种文体和风格",
        "category": "content",
        "capabilities": ["文章写作", "文案优化", "SEO内容", "多语言翻译"],
        "tools": ["llm_chat", "seo_analyze", "translate"],
        "examples": ["撰写产品介绍", "优化博客文章", "生成社交媒体文案"],
        "prerequisites": ["LLMClient"],
        "version": "1.0.0",
    },
    "data_analyzer": {
        "name": "数据分析",
        "description": "数据采集、清洗、分析和可视化",
        "category": "analysis",
        "capabilities": ["数据清洗", "统计分析", "可视化", "报告生成"],
        "tools": ["pandas", "matplotlib", "llm_chat"],
        "examples": ["分析销售数据", "生成月度报告", "数据异常检测"],
        "prerequisites": ["pandas", "numpy"],
        "version": "1.1.0",
    },
    "code_assistant": {
        "name": "编程助手",
        "description": "代码生成、审查、调试和重构",
        "category": "development",
        "capabilities": ["代码生成", "代码审查", "调试辅助", "重构建议"],
        "tools": ["llm_chat", "code_review", "git_ops"],
        "examples": ["生成Python函数", "审查PR代码", "修复Bug"],
        "prerequisites": ["python>=3.8"],
        "version": "2.0.0",
    },
    "research_agent": {
        "name": "研究助手",
        "description": "文献检索、信息整合、知识提炼",
        "category": "research",
        "capabilities": ["文献搜索", "信息整合", "知识蒸馏", "报告撰写"],
        "tools": ["rag_engine", "web_search", "llm_chat"],
        "examples": ["文献综述", "技术调研", "竞品分析"],
        "prerequisites": ["RAGEngine"],
        "version": "1.2.0",
    },
    "vision_processor": {
        "name": "视觉处理",
        "description": "图像分析、OCR识别、图片生成",
        "category": "vision",
        "capabilities": ["图片描述", "OCR识别", "文生图", "图片对比"],
        "tools": ["vision_client", "llm_chat"],
        "examples": ["识别图片文字", "生成产品图", "对比设计稿"],
        "prerequisites": ["VisionClient"],
        "version": "1.0.0",
    },
    "workflow_automator": {
        "name": "工作流自动化",
        "description": "自动化流程编排和执行",
        "category": "automation",
        "capabilities": ["SOP执行", "流程编排", "任务调度", "异常处理"],
        "tools": ["sop_manager", "llm_chat", "task_scheduler"],
        "examples": ["自动化数据流水线", "定时报告生成", "批量处理"],
        "prerequisites": ["SOPManager"],
        "version": "1.3.0",
    },
}


class SkillLoader:
    """
    技能加载器 — 加载、发现、匹配技能。

    参考 CowAgent 技能系统：
    - load_skill: 加载SKILL.md技能定义
    - list_available: 列出可用技能
    - find_for_task: 任务与技能匹配
    - get_tools: 提取技能工具清单

    支持从本地文件系统加载自定义SKILL.md，
    并提供内建技能库作为默认技能集。
    """

    def __init__(
        self,
        skill_dirs: Optional[list[str]] = None,
        auto_register_builtins: bool = True,
    ):
        """
        Args:
            skill_dirs: 额外技能目录列表
            auto_register_builtins: 是否自动注册内建技能
        """
        # 技能存储
        self._skills: dict[str, dict] = {}
        self._skill_cache: dict[str, dict] = {}

        # 技能目录
        self._skill_dirs = []
        if skill_dirs:
            self._skill_dirs = [Path(d).expanduser() for d in skill_dirs]

        # 默认目录
        default_dir = Path("~/.hermes/skills/").expanduser()
        if default_dir not in self._skill_dirs:
            self._skill_dirs.append(default_dir)

        for d in self._skill_dirs:
            d.mkdir(parents=True, exist_ok=True)

        # 注册内建技能
        if auto_register_builtins:
            for name, skill_def in BUILTIN_SKILLS.items():
                self._skills[name] = skill_def

        # 索引计数器
        self._stats = {
            "total_skills": len(self._skills),
            "total_loads": 0,
            "total_matches": 0,
        }

    # ───────── 加载技能 ─────────

    def load_skill(self, skill_name: str) -> dict:
        """
        加载指定技能。

        查找顺序：
        1. 内建技能库
        2. 注册的自定义技能
        3. 文件系统中的 SKILL.md (搜索所有skill_dirs)

        Args:
            skill_name: 技能名称

        Returns:
            dict: 技能定义字典
        """
        self._stats["total_loads"] += 1

        # 1. 检查内存缓存
        if skill_name in self._skill_cache:
            return dict(self._skill_cache[skill_name])

        # 2. 检查已注册技能
        if skill_name in self._skills:
            skill = dict(self._skills[skill_name])
            self._skill_cache[skill_name] = skill
            return skill

        # 3. 从文件系统加载
        skill = self._load_from_file(skill_name)
        if skill:
            self._skills[skill_name] = skill
            self._skill_cache[skill_name] = skill
            return skill

        raise ValueError(
            f"技能「{skill_name}」未找到。 "
            f"可用技能: {list(self._skills.keys())[:10]}..."
        )

    def _load_from_file(self, skill_name: str) -> Optional[dict]:
        """从文件系统加载SKILL.md。"""
        for skill_dir in self._skill_dirs:
            # 搜索各种可能的文件名
            candidates = [
                skill_dir / f"{skill_name}.md",
                skill_dir / f"{skill_name}.yaml",
                skill_dir / f"{skill_name}.json",
                skill_dir / skill_name / "SKILL.md",
                skill_dir / skill_name / "skill.yaml",
            ]

            for path in candidates:
                if path.exists():
                    return self._parse_skill_file(path)

            # 递归搜索
            for md_file in skill_dir.rglob("SKILL.md"):
                if md_file.parent.name == skill_name or md_file.parent.stem == skill_name:
                    return self._parse_skill_file(md_file)

        return None

    def _parse_skill_file(self, path: Path) -> Optional[dict]:
        """解析技能文件 (支持 .md, .yaml, .json)。"""
        content = path.read_text(encoding="utf-8")

        if path.suffix == ".json":
            return json.loads(content)

        if path.suffix in (".yaml", ".yml"):
            return yaml.safe_load(content)

        if path.suffix == ".md":
            return self._parse_markdown_skill(content)

        return None

    def _parse_markdown_skill(self, content: str) -> dict:
        """从Markdown格式解析技能定义。"""
        skill = {
            "name": "",
            "description": "",
            "category": "general",
            "capabilities": [],
            "tools": [],
            "examples": [],
            "prerequisites": [],
            "version": "1.0.0",
        }

        # 提取各字段
        sections = {
            "name": r"#\s*(.+)\s*\n",
            "description": r"##\s*描述\s*\n(.+?)(?:\n##|\Z)",
            "category": r"##\s*分类\s*\n(.+?)(?:\n##|\Z)",
            "capabilities": r"##\s*能力\s*\n(.+?)(?:\n##|\Z)",
            "tools": r"##\s*工具\s*\n(.+?)(?:\n##|\Z)",
            "examples": r"##\s*示例\s*\n(.+?)(?:\n##|\Z)",
            "prerequisites": r"##\s*前置条件\s*\n(.+?)(?:\n##|\Z)",
            "version": r"##\s*版本\s*\n(.+?)(?:\n##|\Z)",
        }

        for field, pattern in sections.items():
            match = re.search(pattern, content, re.DOTALL)
            if match:
                value = match.group(1).strip()

                if field in ("capabilities", "tools", "examples", "prerequisites"):
                    # 列表字段：每一行一个项目
                    items = [line.strip().lstrip("- ") for line in value.split("\n")
                             if line.strip() and not line.strip().startswith("##")]
                    skill[field] = [i for i in items if i]
                else:
                    skill[field] = value

        return skill

    # ───────── 注册技能 ─────────

    def register_skill(self, name: str, skill_def: dict) -> None:
        """
        注册自定义技能。

        Args:
            name: 技能名称
            skill_def: 技能定义字典
        """
        if not name:
            raise ValueError("技能名称不能为空")
        if not skill_def:
            raise ValueError("技能定义不能为空")

        if "name" not in skill_def:
            skill_def["name"] = name
        if "category" not in skill_def:
            skill_def["category"] = "general"
        if "capabilities" not in skill_def:
            skill_def["capabilities"] = []
        if "tools" not in skill_def:
            skill_def["tools"] = []

        self._skills[name] = skill_def
        self._stats["total_skills"] = len(self._skills)

    def unregister_skill(self, name: str) -> bool:
        """注销技能。"""
        if name in self._skills:
            del self._skills[name]
            self._skill_cache.pop(name, None)
            self._stats["total_skills"] = len(self._skills)
            return True
        return False

    # ───────── 列出可用技能 ─────────

    def list_available(self, category: Optional[str] = None) -> list[str]:
        """
        列出可用技能名称。

        Args:
            category: 按分类筛选 (如 content/analysis/development/research/vision/automation)

        Returns:
            list[str]: 技能名称列表
        """
        if category is None:
            return sorted(self._skills.keys())

        return sorted([
            name for name, skill in self._skills.items()
            if skill.get("category") == category
        ])

    def list_categories(self) -> list[str]:
        """列出所有技能分类。"""
        categories = set()
        for skill in self._skills.values():
            cat = skill.get("category", "general")
            categories.add(cat)
        return sorted(categories)

    def list_with_details(self, category: Optional[str] = None) -> list[dict]:
        """列出技能详情。"""
        results = []
        for name, skill in self._skills.items():
            if category and skill.get("category") != category:
                continue
            results.append({
                "name": name,
                "display_name": skill.get("name", name),
                "category": skill.get("category", "general"),
                "description": skill.get("description", ""),
                "capabilities_count": len(skill.get("capabilities", [])),
                "tools_count": len(skill.get("tools", [])),
                "version": skill.get("version", "1.0.0"),
            })
        return sorted(results, key=lambda x: x["name"])

    # ───────── 任务匹配 ─────────

    def find_for_task(self, task_description: str, top_k: int = 3) -> list[dict]:
        """
        根据任务描述匹配合适的技能。

        使用关键词匹配 + 能力覆盖度 + 工具可用性综合评分。

        Args:
            task_description: 任务描述
            top_k: 返回结果数

        Returns:
            list[dict]: 匹配的技能列表，按匹配度排序
                - name: 技能名称
                - display_name: 显示名称
                - match_score: 匹配度 (0-1)
                - match_reason: 匹配原因
                - category: 分类
                - capabilities: 能力列表
        """
        if not task_description or not task_description.strip():
            return []

        self._stats["total_matches"] += 1
        task_lower = task_description.lower()
        task_tokens = set(re.findall(r'[\w\u4e00-\u9fff]+', task_lower))

        if not task_tokens:
            return []

        scored_results = []
        for name, skill in self._skills.items():
            # 构建匹配文本
            match_text = f"{name} {skill.get('name', '')} {skill.get('description', '')} "
            match_text += " ".join(skill.get("capabilities", []))
            match_text += " ".join(skill.get("examples", []))
            match_text += f" {skill.get('category', '')}"

            match_tokens = set(re.findall(r'[\w\u4e00-\u9fff]+', match_text.lower()))

            # Jaccard相似度
            intersection = task_tokens & match_tokens
            union = task_tokens | match_tokens
            jaccard = len(intersection) / len(union) if union else 0

            # 任务词覆盖率
            coverage = len(intersection) / len(task_tokens) if task_tokens else 0

            # 能力匹配度：检查任务是否包含能力关键词
            capability_matches = 0
            for cap in skill.get("capabilities", []):
                cap_lower = cap.lower()
                if any(cap_lower in token for token in task_tokens) or \
                   any(token in cap_lower for token in task_tokens):
                    capability_matches += 1
            cap_score = capability_matches / max(len(skill.get("capabilities", [])), 1)

            # 综合评分
            score = 0.3 * jaccard + 0.3 * coverage + 0.4 * cap_score

            if score > 0.1:
                # 生成匹配原因
                reasons = []
                if coverage > 0.3:
                    reasons.append(f"任务词覆盖{coverage:.0%}")
                if cap_score > 0.3:
                    reasons.append(f"能力匹配{cap_score:.0%}")
                if not reasons:
                    reasons.append("关键词部分匹配")

                match_reason = "; ".join(reasons)

                # 计算工具适配度
                tools_match = []
                for tool in skill.get("tools", []):
                    if tool.lower() in task_lower:
                        tools_match.append(tool)
                        match_reason += f" + 工具{tool}匹配"

                scored_results.append({
                    "name": name,
                    "display_name": skill.get("name", name),
                    "category": skill.get("category", "general"),
                    "match_score": round(score, 4),
                    "match_reason": match_reason,
                    "capabilities": skill.get("capabilities", []),
                    "tools": skill.get("tools", []),
                    "tools_match": tools_match,
                    "version": skill.get("version", "1.0.0"),
                })

        # 排序去重
        scored_results.sort(key=lambda x: x["match_score"], reverse=True)

        # 合并相似技能
        seen_names = set()
        unique_results = []
        for r in scored_results:
            if r["name"] not in seen_names:
                seen_names.add(r["name"])
                unique_results.append(r)
                if len(unique_results) >= top_k:
                    break

        return unique_results

    # ───────── 工具清单提取 ─────────

    def get_tools(self, skill_name: str) -> list[str]:
        """
        提取指定技能的工具清单。

        Args:
            skill_name: 技能名称

        Returns:
            list[str]: 工具名称列表
        """
        skill = self.load_skill(skill_name)
        return skill.get("tools", [])

    def get_all_tools(self, category: Optional[str] = None) -> dict[str, list[str]]:
        """
        获取所有技能的工具清单。

        Args:
            category: 按分类筛选

        Returns:
            dict: {技能名称: [工具列表]}
        """
        result = {}
        for name, skill in self._skills.items():
            if category and skill.get("category") != category:
                continue
            result[name] = skill.get("tools", [])
        return result

    # ───────── 技能执行辅助 ─────────

    def get_prompt(self, skill_name: str, task_context: Optional[dict] = None) -> str:
        """
        根据技能定义生成执行提示词。

        Args:
            skill_name: 技能名称
            task_context: 任务上下文

        Returns:
            str: 系统提示词
        """
        skill = self.load_skill(skill_name)
        context = task_context or {}

        prompt_parts = [
            f"你正在使用「{skill.get('name', skill_name)}」技能。",
            f"技能描述: {skill.get('description', '')}",
            f"可用能力: {', '.join(skill.get('capabilities', []))}",
            f"可用工具: {', '.join(skill.get('tools', []))}",
        ]

        if context:
            prompt_parts.append("任务上下文:")
            for key, value in context.items():
                prompt_parts.append(f"- {key}: {value}")

        return "\n".join(prompt_parts)

    # ───────── 统计 ─────────

    def stats(self) -> dict:
        """获取技能加载器统计信息。"""
        # 按分类统计
        category_counts = defaultdict(int)
        for skill in self._skills.values():
            category_counts[skill.get("category", "general")] += 1

        # 工具使用统计
        tool_usage = defaultdict(int)
        for skill in self._skills.values():
            for tool in skill.get("tools", []):
                tool_usage[tool] += 1

        return {
            "total_skills": len(self._skills),
            "total_loads": self._stats["total_loads"],
            "total_matches": self._stats["total_matches"],
            "categories": dict(category_counts),
            "most_used_tools": sorted(tool_usage.items(), key=lambda x: x[1], reverse=True)[:10],
            "builtin_skills": list(BUILTIN_SKILLS.keys()),
            "custom_skills": [n for n in self._skills if n not in BUILTIN_SKILLS],
        }

    def __repr__(self) -> str:
        return f"SkillLoader(skills={len(self._skills)}, dirs={len(self._skill_dirs)})"
