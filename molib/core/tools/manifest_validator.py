"""
墨麟OS v2.0 — Manifest 标准化验证器

对标 Obsidian manifest.json 规范，为所有技能提供统一的版本管理标准。

标准 Manifest 字段（SKILL.md frontmatter）:
  name: string (必需) — 技能名称，与目录名一致
  description: string (必需) — 简短描述
  version: semver (必需) — 语义化版本，如 "1.2.3"
  min_hermes_version: semver (必需) — 最低兼容 Hermes 版本
  dependencies: list (可选) — 依赖的其他技能名称列表
  tags: list (可选) — 分类标签
  category: string (可选) — 分类
  source: url (可选) — 原始来源
  metadata: dict (可选) — 扩展元数据

用法:
  python -m molib manifest validate                # 验证所有技能
  python -m molib manifest validate --skill xxx     # 验证指定技能
  python -m molib manifest validate --fix           # 自动修复
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import yaml


# ── Semver 正则 ──────────────────────────────
SEMVER_RE = re.compile(
    r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)'
    r'(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)'
    r'(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?'
    r'(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
)

# 必需字段
REQUIRED_FIELDS = ["name", "description", "version", "min_hermes_version"]

# 可选但推荐的字段
RECOMMENDED_FIELDS = ["tags", "category"]


@dataclass
class ManifestIssue:
    """Manifest 问题"""
    skill_name: str
    path: str
    severity: str  # "error", "warning", "info"
    field: str
    message: str


@dataclass
class ManifestReport:
    """验证报告"""
    total: int = 0
    valid: int = 0
    issues: list = field(default_factory=list)

    @property
    def errors(self):
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self):
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def infos(self):
        return [i for i in self.issues if i.severity == "info"]


def parse_frontmatter(content: str) -> tuple:
    """解析 SKILL.md 的 YAML frontmatter。

    Returns (frontmatter_dict, body_text)
    """
    content = content.lstrip()
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return {}, content

    return fm, parts[2].strip()


def validate_semver(value: str) -> bool:
    """验证语义化版本号。"""
    return bool(SEMVER_RE.match(str(value)))


def validate_skill_manifest(skill_path: Path) -> list[ManifestIssue]:
    """验证单个技能的 manifest。"""
    issues = []
    skill_md = skill_path / "SKILL.md"
    skill_name = skill_path.name

    if not skill_md.exists():
        issues.append(ManifestIssue(
            skill_name=skill_name,
            path=str(skill_path),
            severity="error",
            field="SKILL.md",
            message="SKILL.md 文件不存在"
        ))
        return issues

    content = skill_md.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(content)

    if not fm:
        issues.append(ManifestIssue(
            skill_name=skill_name, path=str(skill_md),
            severity="error", field="frontmatter",
            message="缺少 YAML frontmatter（--- ... ---）"
        ))
        return issues

    # 检查必需字段
    for field_name in REQUIRED_FIELDS:
        if field_name not in fm or fm[field_name] is None:
            issues.append(ManifestIssue(
                skill_name=skill_name, path=str(skill_md),
                severity="error", field=field_name,
                message=f"缺少必需字段 '{field_name}'"
            ))
            continue

        if field_name in ("version", "min_hermes_version"):
            if not validate_semver(fm[field_name]):
                issues.append(ManifestIssue(
                    skill_name=skill_name, path=str(skill_md),
                    severity="error", field=field_name,
                    message=f"'{field_name}' 不是有效的语义化版本: {fm[field_name]}"
                ))

    # 检查 name 与目录名一致
    if "name" in fm and fm["name"] != skill_name:
        issues.append(ManifestIssue(
            skill_name=skill_name, path=str(skill_md),
            severity="warning", field="name",
            message=f"name '{fm['name']}' 与目录名 '{skill_name}' 不一致"
        ))

    # 检查推荐字段
    for field_name in RECOMMENDED_FIELDS:
        if field_name not in fm:
            issues.append(ManifestIssue(
                skill_name=skill_name, path=str(skill_md),
                severity="info", field=field_name,
                message=f"建议添加 '{field_name}' 字段"
            ))

    # 检查 dependencies 格式
    if "dependencies" in fm and fm["dependencies"] is not None:
        deps = fm["dependencies"]
        if not isinstance(deps, list):
            issues.append(ManifestIssue(
                skill_name=skill_name, path=str(skill_md),
                severity="error", field="dependencies",
                message="dependencies 必须是数组"
            ))
        else:
            for dep in deps:
                if not isinstance(dep, str):
                    issues.append(ManifestIssue(
                        skill_name=skill_name, path=str(skill_md),
                        severity="error", field="dependencies",
                        message=f"依赖项必须是字符串: {dep}"
                    ))

    # 检查是否有实质性 body 内容
    if len(body) < 20:
        issues.append(ManifestIssue(
            skill_name=skill_name, path=str(skill_md),
            severity="warning", field="body",
            message="技能正文内容过短（可能不完整）"
        ))

    return issues


def validate_all_skills(skills_dir: Path) -> ManifestReport:
    """验证技能目录下所有技能。"""
    report = ManifestReport()

    if not skills_dir.exists():
        report.issues.append(ManifestIssue(
            skill_name="(root)", path=str(skills_dir),
            severity="error", field="directory",
            message="技能目录不存在"
        ))
        return report

    skill_dirs = sorted(
        [d for d in skills_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
    )
    report.total = len(skill_dirs)

    for skill_dir in skill_dirs:
        issues = validate_skill_manifest(skill_dir)
        report.issues.extend(issues)
        if not any(i.severity == "error" for i in issues):
            report.valid += 1

    return report


def auto_fix_skill(skill_path: Path, hermes_version: str = "0.13.0") -> bool:
    """自动修复技能的 manifest 缺失字段。"""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return False

    content = skill_md.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(content)

    if not fm:
        return False

    changed = False

    # 补充 version
    if "version" not in fm or fm["version"] is None:
        fm["version"] = "1.0.0"
        changed = True

    # 补充 min_hermes_version
    if "min_hermes_version" not in fm or fm["min_hermes_version"] is None:
        fm["min_hermes_version"] = hermes_version
        changed = True

    if not changed:
        return False

    # 重新序列化
    new_fm = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False).strip()
    new_content = f"---\n{new_fm}\n---\n\n{body}"

    skill_md.write_text(new_content, encoding="utf-8")
    return True


def print_report(report: ManifestReport) -> None:
    """打印验证报告。"""
    total = report.total
    errors = len(report.errors)
    warnings = len(report.warnings)
    infos = len(report.infos)

    print(f"\n{'='*60}")
    print(f"  Manifest 验证报告")
    print(f"{'='*60}")
    print(f"  总计: {total}  有效: {report.valid}  错误: {errors}  警告: {warnings}  提示: {infos}")

    if errors > 0:
        print(f"\n  ❌ 错误 ({errors}):")
        for issue in report.errors:
            print(f"     [{issue.skill_name}] {issue.field}: {issue.message}")

    if warnings > 0:
        print(f"\n  ⚠️  警告 ({warnings}):")
        for issue in report.warnings:
            print(f"     [{issue.skill_name}] {issue.field}: {issue.message}")

    if infos > 0 and infos <= 20:
        print(f"\n  ℹ️  提示 ({infos}):")
        for issue in report.infos:
            print(f"     [{issue.skill_name}] {issue.field}: {issue.message}")
    elif infos > 20:
        print(f"\n  ℹ️  提示: {infos} 条（已折叠）")

    print()


# ── CLI 入口 ──────────────────────────────────

def main():
    """CLI: python -m molib.core.tools.manifest_validator"""
    import argparse

    parser = argparse.ArgumentParser(description="Manifest 标准化验证器")
    parser.add_argument("action", nargs="?", default="validate",
                        choices=["validate", "fix", "upgrade"])
    parser.add_argument("--skill", type=str, help="指定技能名称")
    parser.add_argument("--skills-dir", type=str,
                        default=str(Path.home() / ".hermes" / "skills"),
                        help="技能目录")
    parser.add_argument("--hermes-version", type=str, default="0.13.0",
                        help="当前 Hermes 版本")

    args = parser.parse_args()
    skills_dir = Path(args.skills_dir)

    if args.action == "validate":
        if args.skill:
            skill_path = skills_dir / args.skill
            if not skill_path.exists():
                print(f"错误: 技能 '{args.skill}' 不存在")
                sys.exit(1)
            issues = validate_skill_manifest(skill_path)
            report = ManifestReport(total=1, issues=issues)
            report.valid = 0 if any(i.severity == "error" for i in issues) else 1
        else:
            report = validate_all_skills(skills_dir)
        print_report(report)

    elif args.action == "fix":
        if args.skill:
            skill_path = skills_dir / args.skill
            ok = auto_fix_skill(skill_path, args.hermes_version)
            print(f"{'✅' if ok else '⏭️'}  {args.skill}: {'已修复' if ok else '无需修复'}")
        else:
            fixed = 0
            for d in sorted(skills_dir.iterdir()):
                if d.is_dir() and not d.name.startswith("."):
                    if auto_fix_skill(d, args.hermes_version):
                        fixed += 1
                        print(f"✅ {d.name}: 已修复")
            print(f"\n共修复 {fixed} 个技能")

    elif args.action == "upgrade":
        # 批量将旧格式升级为新格式
        from .manifest_upgrader import upgrade_all
        result = upgrade_all(skills_dir, args.hermes_version)
        print(f"\n升级完成: 成功 {result['success']}, 跳过 {result['skipped']}, 失败 {result['failed']}")


if __name__ == "__main__":
    main()
