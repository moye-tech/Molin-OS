"""
墨麟OS v2.0 — Manifest 批量升级器

将旧格式 SKILL.md 升级为新 Manifest 标准格式。
支持：
  - 添加缺失的 version/min_hermes_version 字段
  - 规范化字段顺序
  - 从 metadata 中迁移旧字段
  - 干跑模式预览变更
"""

import re
from pathlib import Path
from datetime import datetime
from typing import Any

import yaml


# 标准字段顺序（对标 Obsidian manifest.json + Agent Skills 规范）
STANDARD_FIELD_ORDER = [
    "name",
    "description",
    "version",
    "min_hermes_version",
    "dependencies",
    "tags",
    "category",
    "source",
    "metadata",
]

# Hermes 版本到发布时间映射（用于从日期推断版本）
HERMES_VERSION_HISTORY = {
    "0.13.0": "2026-05-01",
    "0.12.0": "2026-03-01",
    "0.11.0": "2026-01-01",
    "0.10.0": "2025-11-01",
    "0.9.0":  "2025-09-01",
    "0.8.0":  "2025-07-01",
}


def parse_frontmatter(content: str) -> tuple[dict, str, str]:
    """解析 SKILL.md frontmatter。

    Returns (frontmatter_dict, raw_frontmatter_str, body_text)
    """
    content = content.lstrip()
    if not content.startswith("---"):
        return {}, "", content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, "", content

    raw_fm = parts[1]
    try:
        fm = yaml.safe_load(raw_fm) or {}
    except yaml.YAMLError:
        return {}, raw_fm, parts[2].strip() if len(parts) > 2 else ""

    return fm, raw_fm, parts[2].strip() if len(parts) > 2 else ""


def normalize_frontmatter(fm: dict, hermes_version: str = "0.13.0") -> dict:
    """规范化 frontmatter —— 添加缺失字段，整理字段顺序。"""
    normalized = {}

    # 1. 按标准顺序排列已有字段
    for key in STANDARD_FIELD_ORDER:
        if key in fm:
            normalized[key] = fm[key]

    # 2. 补充缺失的必需字段
    if "version" not in normalized:
        # 尝试从 metadata 中提取旧版本
        old_ver = (
            fm.get("metadata", {}).get("version")
            or fm.get("metadata", {}).get("hermes", {}).get("version")
        )
        normalized["version"] = str(old_ver) if old_ver else "1.0.0"

    if "min_hermes_version" not in normalized:
        # 尝试从 metadata 推断
        min_ver = (
            fm.get("metadata", {}).get("min_hermes_version")
            or fm.get("metadata", {}).get("hermes", {}).get("min_version")
        )
        normalized["min_hermes_version"] = str(min_ver) if min_ver else hermes_version

    # 3. 将不在标准顺序中的字段移到 metadata 中
    extra = {}
    for key, value in fm.items():
        if key not in normalized and key != "metadata":
            extra[key] = value

    if extra:
        if "metadata" not in normalized:
            normalized["metadata"] = {}
        if isinstance(normalized["metadata"], dict):
            # 合并，已有字段不覆盖
            existing = normalized["metadata"]
            for k, v in extra.items():
                if k not in existing:
                    existing[k] = v

    # 4. 如果没有任何额外元数据，删除 metadata
    if "metadata" in normalized and not normalized["metadata"]:
        del normalized["metadata"]

    return normalized


def upgrade_skill(skill_path: Path, hermes_version: str = "0.13.0",
                  dry_run: bool = False) -> dict:
    """升级单个技能的 manifest。

    Returns {"status": "success"|"skipped"|"error", "skill": name, "changes": [...]}
    """
    skill_md = skill_path / "SKILL.md"
    skill_name = skill_path.name

    if not skill_md.exists():
        return {"status": "error", "skill": skill_name,
                "changes": [], "error": "SKILL.md 不存在"}

    content = skill_md.read_text(encoding="utf-8")
    fm, raw_fm, body = parse_frontmatter(content)

    if not fm:
        return {"status": "error", "skill": skill_name,
                "changes": [], "error": "无法解析 frontmatter"}

    normalized = normalize_frontmatter(fm, hermes_version)
    changes = []

    # 检测变更
    for key in ["version", "min_hermes_version", "dependencies"]:
        if key not in fm:
            changes.append(f"+ 添加字段: {key} = {normalized.get(key)}")
        elif str(fm[key]) != str(normalized.get(key)):
            changes.append(f"~ 更新字段: {key}: {fm[key]} → {normalized.get(key)}")

    if not changes and set(normalized.keys()) == set(fm.keys()):
        return {"status": "skipped", "skill": skill_name, "changes": []}

    if dry_run:
        return {"status": "dry_run", "skill": skill_name, "changes": changes}

    # 写入新内容
    new_fm_yaml = yaml.dump(
        normalized,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=120
    ).strip()

    new_content = f"---\n{new_fm_yaml}\n---\n\n{body}"
    skill_md.write_text(new_content, encoding="utf-8")

    return {"status": "success", "skill": skill_name, "changes": changes}


def upgrade_all(skills_dir: Path, hermes_version: str = "0.13.0",
                dry_run: bool = False) -> dict:
    """批量升级所有技能。

    Returns {"success": int, "skipped": int, "failed": int, "details": [...]}
    """
    result = {"success": 0, "skipped": 0, "failed": 0, "details": []}

    if not skills_dir.exists():
        result["failed"] = 1
        result["details"].append({"status": "error", "skill": "(root)",
                                   "error": "技能目录不存在"})
        return result

    skill_dirs = sorted(
        [d for d in skills_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
    )

    for skill_dir in skill_dirs:
        r = upgrade_skill(skill_dir, hermes_version, dry_run)
        result["details"].append(r)
        if r["status"] == "success":
            result["success"] += 1
        elif r["status"] == "skipped":
            result["skipped"] += 1
        else:
            result["failed"] += 1

    return result


def create_manifest_template(name: str, description: str,
                              category: str = "",
                              tags: list = None,
                              version: str = "1.0.0",
                              hermes_version: str = "0.13.0") -> str:
    """生成标准 manifest 模板。"""
    fm = {
        "name": name,
        "description": description,
        "version": version,
        "min_hermes_version": hermes_version,
        "tags": tags or [],
        "category": category,
    }

    fm_yaml = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False).strip()
    return f"---\n{fm_yaml}\n---\n\n# {name}\n\nTODO: 编写技能内容。\n"
