#!/usr/bin/env python3
"""
CH6: GitHub吸收标准化管线
三步法：assess_project → convert_to_skill → validate_skill
零外部依赖，仅用标准库
"""
import os
import re
import json
import time
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# ──────────────────────────────────────────────
# 第一步：项目评估
# ──────────────────────────────────────────────

def assess_project(
    repo_url: str,
    stars: int = 0,
    match_keywords: Optional[List[str]] = None,
    has_readme: bool = True,
    has_api: bool = True,
    has_examples: bool = True,
) -> Dict:
    """
    评估GitHub项目，返回0-100评分及详情。

    评分公式：stars×0.3 + 匹配度×0.4 + 可执行性×0.3

    Args:
        repo_url: GitHub仓库URL
        stars: GitHub星数
        match_keywords: 与Hermes技能匹配的关键词列表
        has_readme: 是否有README
        has_api: 是否有API接口
        has_examples: 是否有使用示例

    Returns:
        dict: {score, details}
    """
    if match_keywords is None:
        match_keywords = []

    # 1. 星数评分 (stars×0.3)
    # 对数映射：1星=10, 10星=30, 100星=50, 1000星=70, 10000+=90
    if stars <= 0:
        star_score = 0
    elif stars < 10:
        star_score = 10 + (stars / 10) * 20
    elif stars < 100:
        star_score = 30 + ((stars - 10) / 90) * 20
    elif stars < 1000:
        star_score = 50 + ((stars - 100) / 900) * 20
    elif stars < 10000:
        star_score = 70 + ((stars - 1000) / 9000) * 20
    else:
        star_score = 90

    star_score = min(star_score, 100)

    # 2. 匹配度评分 (匹配度×0.4)
    # 关键词匹配度：每个匹配词+15分，最多100
    hermes_domains = [
        "agent", "automation", "content", "image", "video",
        "voice", "tts", "stt", "text", "crawler", "notification",
        "api", "bot", "cli", "pipeline", "workflow", "crm",
        "ecommerce", "social", "feishu", "lark", "wechat",
        "analysis", "data", "report", "design", "生成", "创作",
        "publish", "media", "chat", "llm", "ai",
    ]

    matched = [kw for kw in match_keywords if kw.lower() in hermes_domains]
    match_score = min(len(matched) * 15, 100)

    # 额外匹配加分
    repo_lower = repo_url.lower()
    extra_match = 0
    for domain in ["image", "generation", "content", "automation", "bot"]:
        if domain in repo_lower:
            extra_match += 5
    match_score = min(match_score + extra_match, 100)

    # 3. 可执行性评分 (可执行性×0.3)
    exec_score = 0
    if has_readme:
        exec_score += 30
    if has_api:
        exec_score += 35
    if has_examples:
        exec_score += 35

    # 4. 总分
    total = round(star_score * 0.3 + match_score * 0.4 + exec_score * 0.3, 1)
    total = max(0, min(total, 100))

    # 评分等级
    if total >= 80:
        level = "S级 — 优先吸收"
    elif total >= 60:
        level = "A级 — 推荐吸收"
    elif total >= 40:
        level = "B级 — 可吸收"
    elif total >= 20:
        level = "C级 — 观察"
    else:
        level = "D级 — 不推荐"

    details = {
        "repo_url": repo_url,
        "stars": stars,
        "star_score": round(star_score, 1),
        "match_score": round(match_score, 1),
        "exec_score": round(exec_score, 1),
        "total_score": total,
        "level": level,
        "matched_keywords": matched,
    }

    return details


# ──────────────────────────────────────────────
# 第二步：转换为SKILL.md模板
# ──────────────────────────────────────────────

def convert_to_skill(repo_data: Dict) -> str:
    """
    根据项目评估数据生成SKILL.md模板。

    Args:
        repo_data: assess_project 返回的评估数据

    Returns:
        str: SKILL.md 内容
    """
    repo_url = repo_data.get("repo_url", "")
    repo_name = repo_url.rstrip("/").split("/")[-1] if repo_url else "unknown"
    owner = repo_url.rstrip("/").split("/")[-2] if repo_url else "unknown"
    score = repo_data.get("total_score", 50)
    stars = repo_data.get("stars", 0)

    # 从URL推断技能名称
    skill_name = re.sub(r"[^a-z0-9-]", "", repo_name.lower().replace("_", "-"))
    if not skill_name:
        skill_name = f"skill-from-{owner}-{int(time.time())}"

    matched = repo_data.get("matched_keywords", [])
    tags = ", ".join([skill_name, owner] + matched[:5])

    description = f"从 {repo_url} 吸收的技能 — {repo_data.get('level', '待评估')}"

    sk = f"""---
name: {skill_name}
description: {description}
version: 0.1.0
tags: [{tags}]
metadata:
  hermes:
    source: {repo_url}
    owner: {owner}
    stars: {stars}
    assessment_score: {score}
    assessment_level: "{repo_data.get('level', '待评估')}"
    absorbed_at: "{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}"
---

# {repo_name}

## 概述

从 [{owner}/{repo_name}]({repo_url}) 吸收的技能。
评分: {score}/100 ({repo_data.get('level', '待评估')})

## 功能

- 待补充：从原项目README提取核心功能

## 工具文件

| 文件 | 路径 | 用途 |
|------|------|------|
| {skill_name}.py | ~/hermes-os/tools/{skill_name}.py | 主工具实现 |

## 调用方式

```bash
cd ~/hermes-os
python3 tools/{skill_name}.py --help
```

## 吸收评估

| 维度 | 评分 | 说明 |
|------|------|------|
| ⭐ 星数 | {repo_data.get('star_score', 0)}/100 | {stars} stars |
| 🎯 匹配度 | {repo_data.get('match_score', 0)}/100 | 匹配: {', '.join(matched) if matched else '无'} |
| ⚡ 可执行性 | {repo_data.get('exec_score', 0)}/100 | README/API/示例 |

## 前置条件

- Python 3.10+
- 待补充依赖

## 注意事项

- 此技能由吸收管线自动生成
- 需手动验证和补充功能描述
"""
    return sk.strip()


# ──────────────────────────────────────────────
# 第三步：验证技能文件
# ──────────────────────────────────────────────

def validate_skill(skill_path: str) -> Dict:
    """
    验证SKILL.md的语法和完整性。

    Checks:
      - YAML front matter 存在且格式正确
      - 必要字段存在 (name, description, version)
      - SKILL.md结构完整性
      - 引用文件是否存在

    Args:
        skill_path: SKILL.md文件路径

    Returns:
        dict: {valid: bool, errors: list, warnings: list}
    """
    errors = []
    warnings = []

    path = Path(skill_path).expanduser()

    if not path.exists():
        return {"valid": False, "errors": [f"文件不存在: {skill_path}"], "warnings": []}

    content = path.read_text(encoding="utf-8")

    # 1. 检查YAML front matter
    if not content.startswith("---"):
        errors.append("缺少YAML front matter（应以 --- 开头）")
    else:
        # 找到第二个 ---
        end_idx = content.find("---", 3)
        if end_idx == -1:
            errors.append("YAML front matter 未闭合（缺少第二个 ---）")
        else:
            front_matter = content[3:end_idx].strip()
            if not front_matter:
                errors.append("YAML front matter 为空")
            else:
                # 解析必要字段
                has_name = False
                has_desc = False
                has_version = False

                for line in front_matter.split("\n"):
                    line = line.strip()
                    if line.startswith("name:"):
                        has_name = True
                        name_val = line.split(":", 1)[1].strip().strip('"')
                        if not name_val:
                            warnings.append("name 字段值为空")
                    elif line.startswith("description:"):
                        has_desc = True
                    elif line.startswith("version:"):
                        has_version = True
                        version_val = line.split(":", 1)[1].strip().strip('"')
                        # 验证版本号格式
                        if not re.match(r"^\d+\.\d+\.\d+$", version_val):
                            warnings.append(f"version 格式不规范: {version_val}（应为 x.y.z）")

                if not has_name:
                    errors.append("缺少必要字段: name")
                if not has_desc:
                    errors.append("缺少必要字段: description")
                if not has_version:
                    errors.append("缺少必要字段: version")

    # 2. 检查文档结构
    sections_found = []
    section_pattern = re.compile(r"^## (.+)$", re.MULTILINE)
    for match in section_pattern.finditer(content):
        sections_found.append(match.group(1))

    required_sections = ["概述", "功能", "调用方式"]
    for section in required_sections:
        if section not in sections_found:
            warnings.append(f"缺少建议章节: {section}")

    # 3. 检查引用文件
    tool_refs = re.findall(r"\|[\s]*([\w._-]+\.py)[\s]*\|", content)
    for ref in tool_refs:
        # 尝试查找文件
        tool_path = path.parent / ref
        if not tool_path.exists():
            # 也检查 ~/hermes-os/tools/
            alt_path = Path.home() / "hermes-os" / "tools" / ref
            if not alt_path.exists():
                warnings.append(f"引用的工具文件不存在: {ref}")

    # 4. 检查是否有占位符
    placeholder_patterns = [
        r"待补充",
        r"TODO",
        r"FIXME",
        r"待完善",
    ]
    for pattern in placeholder_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            warnings.append(f"包含未完成的占位符: {pattern}")
            break

    valid = len(errors) == 0
    return {
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
        "sections": sections_found,
    }


# ──────────────────────────────────────────────
# 批量处理：执行完整三步管线
# ──────────────────────────────────────────────

def run_pipeline(
    repo_url: str,
    stars: int = 0,
    match_keywords: Optional[List[str]] = None,
    output_dir: str = "~/hermes-os/skills/absorbed",
) -> Dict:
    """
    对单个项目执行完整的三步吸收管线。

    Returns:
        dict: 完整管线结果
    """
    print(f"\n{'='*60}")
    print(f"📦 开始吸收: {repo_url}")
    print(f"{'='*60}")

    # Step 1: 评估
    print(f"\n🔍 Step 1/3: 项目评估...")
    assessment = assess_project(repo_url, stars, match_keywords or [])
    print(f"   评分: {assessment['total_score']}/100 ({assessment['level']})")
    print(f"   ⭐星数维度: {assessment['star_score']}/100")
    print(f"   🎯匹配度维度: {assessment['match_score']}/100")
    print(f"   ⚡可执行性维度: {assessment['exec_score']}/100")

    # Step 2: 转换
    print(f"\n📝 Step 2/3: 生成SKILL.md...")
    skill_content = convert_to_skill(assessment)

    # 确定输出路径
    repo_name = repo_url.rstrip("/").split("/")[-1]
    skill_name = re.sub(r"[^a-z0-9-]", "", repo_name.lower().replace("_", "-"))
    if not skill_name:
        skill_name = f"absorbed-{int(time.time())}"

    out_dir = Path(output_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    skill_path = out_dir / f"{skill_name}" / "SKILL.md"
    skill_path.parent.mkdir(parents=True, exist_ok=True)
    skill_path.write_text(skill_content + "\n", encoding="utf-8")
    print(f"   ✅ 已保存: {skill_path}")

    # Step 3: 验证
    print(f"\n✅ Step 3/3: 验证SKILL.md...")
    validation = validate_skill(str(skill_path))
    if validation["valid"]:
        print(f"   ✅ 验证通过！")
    else:
        print(f"   ❌ 验证失败:")
        for err in validation["errors"]:
            print(f"      - {err}")

    if validation["warnings"]:
        print(f"   ⚠️ 警告:")
        for w in validation["warnings"]:
            print(f"      - {w}")

    print(f"\n{'='*60}")
    print(f"🏁 吸收完成: {repo_url}")
    print(f"   技能路径: {skill_path}")
    print(f"{'='*60}")

    return {
        "repo_url": repo_url,
        "skill_path": str(skill_path),
        "assessment": assessment,
        "validation": validation,
    }


# ──────────────────────────────────────────────
# CLI入口
# ──────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="CH6: GitHub吸收标准化管线 — 三步法吸收GitHub项目为Hermes技能"
    )
    parser.add_argument("--repo", "-r", help="GitHub仓库URL")
    parser.add_argument("--stars", "-s", type=int, default=0, help="GitHub星数")
    parser.add_argument("--keywords", "-k", nargs="*", default=[],
                        help="匹配关键词（如: image generation automation）")
    parser.add_argument("--output", "-o", default="~/hermes-os/skills/absorbed",
                        help="输出目录")
    parser.add_argument("--validate", "-v", help="仅验证指定SKILL.md文件")
    parser.add_argument("--batch", "-b", help="批量模式：JSON文件路径（项目列表）")

    args = parser.parse_args()

    if args.validate:
        print(f"\n🔍 验证SKILL.md: {args.validate}")
        result = validate_skill(args.validate)
        if result["valid"]:
            print("   ✅ 验证通过")
        else:
            print("   ❌ 验证失败:")
            for err in result["errors"]:
                print(f"      - {err}")
        if result["warnings"]:
            print("   ⚠️ 警告:")
            for w in result["warnings"]:
                print(f"      - {w}")
        return

    if args.batch:
        # 批量模式：从JSON文件读取项目列表
        batch_path = Path(args.batch).expanduser()
        if not batch_path.exists():
            print(f"❌ 批量文件不存在: {batch_path}")
            return
        projects = json.loads(batch_path.read_text(encoding="utf-8"))
        results = []
        for proj in projects:
            result = run_pipeline(
                repo_url=proj["url"],
                stars=proj.get("stars", 0),
                match_keywords=proj.get("keywords", []),
                output_dir=proj.get("output", args.output),
            )
            results.append(result)

        # 输出汇总
        print(f"\n\n{'='*60}")
        print("📊 吸收汇总")
        print(f"{'='*60}")
        print(f"{'项目':<40} {'评分':<8} {'等级':<20}")
        print("-" * 68)
        for r in results:
            a = r["assessment"]
            print(f"{a['repo_url'][:38]:<40} {a['total_score']:<8} {a['level']:<20}")
        return

    if args.repo:
        run_pipeline(
            repo_url=args.repo,
            stars=args.stars,
            match_keywords=args.keywords,
            output_dir=args.output,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
