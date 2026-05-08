---
name: skill-quality-eval
description: 技能质量评估标准 — 5 维度评分模型、沉睡技能识别、每季度全技能审查流程
version: 0.1.0
tags: [meta, evaluation, quality, governance, skills]
metadata:
  hermes:
    molin_owner: L0-中枢
    review_frequency: 每季度
---

# 技能质量评估标准

## 概述

技能质量评估标准定义了 Hermes 系统中所有 SKILL.md 的质量评估体系，包括 5 维度评分模型、沉睡技能识别方法、季度审查流程和 GitHub 吸收评分参考。

- **物主**: L0-中枢（系统治理）
- **评估对象**: `~/hermes-os/skills/` 下的所有 SKILL.md
- **审查频率**: 每季度

## 技能有效性评分模型（5 维度）

### 评分维度

每个技能从以下 5 个维度评分，每项 0-20 分，总分 100 分。

| 维度 | 权重 | 说明 | 评分标准 |
|------|------|------|---------|
| 可调用性 | 20 分 | 技能能否被 Hermes 准确识别并调用 | 20=精确匹配触发词, 10=模糊匹配, 0=无法触发 |
| 准确性 | 20 分 | 技能执行结果是否符合预期 | 20=完全正确, 10=部分正确, 0=错误结果 |
| 产出质量 | 20 分 | 输出的文档/代码/数据的质量 | 20=可直接交付, 10=需修改, 0=不可用 |
| 执行速度 | 20 分 | 从调用到返回的时间 | 20=即时(<5s), 10=中等(<30s), 0=缓慢(>2min) |
| 可维护性 | 20 分 | 文档是否清晰、依赖是否明确 | 20=完整文档+明确依赖, 10=部分缺失, 0=无文档 |

### 评估模板

```markdown
---
name: skill-name
version: 0.1.0
tags: [tag1, tag2]
metadata:
  hermes:
    molin_owner: XXX
    quality_score: 0.0     # 总分 100
    quality_evaluated_at: "2026-05-08"
    quality_invoke_score: 0    # 可调用性 0-20
    quality_accuracy_score: 0  # 准确性 0-20
    quality_output_score: 0    # 产出质量 0-20
    quality_speed_score: 0     # 执行速度 0-20
    quality_maint_score: 0     # 可维护性 0-20
    quality_evaluator: "Hermes"
---
```

### 评级分类

| 分数段 | 等级 | 操作建议 |
|--------|------|---------|
| 85-100 | A — 优秀 | 保持，可作为参考模板 |
| 70-84 | B — 良好 | 小幅优化即可 |
| 50-69 | C — 合格 | 需针对性改进 |
| 30-49 | D — 不足 | 需大幅重写 |
| 0-29 | E — 差 | 废弃或完全重建 |

## 沉睡技能识别方法

### 定义

沉睡技能指在最近一个季度（3 个月）内未被 Hermes 调用的技能。

### 识别流程

```python
import json
import os
from pathlib import Path
from datetime import datetime, timedelta

def identify_dormant_skills() -> list[dict]:
    """识别沉睡技能"""
    skills_dir = Path("/home/ubuntu/hermes-os/skills")
    usage_log = Path("/home/ubuntu/hermes-os/skills/.usage.json")
    
    # 读取调用日志
    if usage_log.exists():
        with open(usage_log) as f:
            usage = json.load(f)
    else:
        usage = {}
    
    three_months_ago = datetime.now() - timedelta(days=90)
    dormant = []
    
    # 遍历所有技能
    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        
        skill_name = skill_dir.name
        last_used = usage.get(skill_name, {}).get("last_called")
        
        if last_used is None:
            dormant.append({
                "skill": skill_name,
                "status": "零调用",
                "last_used": None,
            })
        else:
            last_date = datetime.fromisoformat(last_used)
            if last_date < three_months_ago:
                dormant.append({
                    "skill": skill_name,
                    "status": "沉睡",
                    "last_used": last_used,
                })
    
    return dormant
```

### 处理沉睡技能

| 状态 | 处理方式 |
|------|---------|
| 零调用（从未使用） | 检查触发词是否正确、是否已注册到 AGENTS.md |
| 沉睡（>3 月未用） | 评估是否仍有价值 → 更新或归档 |
| 低效（评分 <50） | 标记为待重写 |
| 已废弃 | 移入 `skills/archived/` 目录 |

## 每季度全技能审查流程

### 审查日程

```
季度末最后一周
├── 周一：运行沉睡技能识别脚本
├── 周二：逐个评估活跃技能（5 维度评分）
├── 周三：生成审查报告
├── 周四：创建改进 Issue / PR
└── 周五：更新技能注册表 + 归档废弃技能
```

### 审查清单

- [ ] 运行沉睡技能识别
- [ ] 对活跃技能进行 5 维度评分
- [ ] 检查技能的触发词是否仍有效
- [ ] 检查依赖是否有更新（版本变更）
- [ ] 检查是否与其他技能功能重叠
- [ ] 更新 `.usage.json` 调用日志
- [ ] 输出审查报告到 `~/hermes-os/docs/skill-review-{quarter}.md`
- [ ] 更新 `skills-index.md`
- [ ] 归档废弃技能

### 审查报告模板

```markdown
# 技能审查报告 — 2026-Q1

## 概要

| 项目 | 值 |
|------|----|
| 审查时间 | 2026-03-31 |
| 总技能数 | XX |
| 活跃技能 | XX |
| 沉睡技能 | XX |
| 废弃技能 | XX |
| 平均评分 | XX/100 |

## 评分排行

### 最高分（Top 5）
| 技能 | 总分 | 可调用 | 准确 | 质量 | 速度 | 维护 |
|------|------|--------|------|------|------|------|
| ... | ... | ... | ... | ... | ... | ... |

### 最低分（Bottom 5）
| 技能 | 总分 | 问题描述 | 改进建议 |
|------|------|---------|---------|
| ... | ... | ... | ... |

## 沉睡技能

| 技能 | 最后调用 | 建议操作 |
|------|---------|---------|
| ... | ... | 归档/更新/废弃 |

## 改进计划

- [ ] 技能 A：更新触发词（低可调用性）
- [ ] 技能 B：补充示例（低准确性）
- [ ] 技能 C：更新依赖版本（低维护性）
```

## GitHub 吸收评分模型参考

### 评估维度

当从 GitHub 吸收新技能时，使用以下评分模型：

| 维度 | 权重 | 评分依据 |
|------|------|---------|
| ⭐ 星数 | 30 分 | 0-100: star/1000, 最高 100K+ |
| 🎯 匹配度 | 40 分 | 与当前业务/技能栈的相关性 |
| ⚡ 可执行性 | 30 分 | README/API/示例的完整性 |

### 等级判定

| 分数 | 等级 | 行动 |
|------|------|------|
| 80-100 | S 级 | 立即吸收 |
| 60-79 | A 级 | 推荐吸收 |
| 40-59 | B 级 | 可吸收（非紧急） |
| 20-39 | C 级 | 暂不吸收 |
| 0-19 | D 级 | 不吸收 |

### 参考案例

```python
def score_github_repo(repo_data: dict) -> dict:
    """评估 GitHub 仓库的吸收价值"""
    stars = repo_data.get("stars", 0)
    topics = repo_data.get("topics", [])
    has_readme = repo_data.get("has_readme", False)
    has_api = repo_data.get("has_api", False)
    has_examples = repo_data.get("has_examples", False)
    
    # 星数评分
    star_score = min(stars / 1000 * 3, 30)  # 每 1K ⭐ 得 3 分，上限 30
    
    # 匹配度评分（基于 topics 与已有技能的重叠）
    match_score = 40 if len(topics) > 0 else 10
    
    # 可执行性评分
    exec_score = sum([has_readme, has_api, has_examples]) * 10  # 每个 10 分
    
    total = star_score + match_score + exec_score
    
    if total >= 80:
        level = "S 级 — 立即吸收"
    elif total >= 60:
        level = "A 级 — 推荐吸收"
    elif total >= 40:
        level = "B 级 — 可吸收"
    elif total >= 20:
        level = "C 级 — 暂不吸收"
    else:
        level = "D 级 — 不吸收"
    
    return {
        "total": total,
        "level": level,
        "star_score": star_score,
        "match_score": match_score,
        "exec_score": exec_score,
    }
```

### 吸收后评估

技能被吸收后，在下次季度审查中按 5 维度模型重新评估，验证吸收决策的质量。

## 自动评估脚本

```bash
# 运行完整性检查
python -c "
from pathlib import Path
import yaml

errors = []
for skill_dir in Path('~/hermes-os/skills').iterdir():
    if not skill_dir.is_dir():
        continue
    skill_md = skill_dir / 'SKILL.md'
    if not skill_md.exists():
        errors.append(f'缺少 SKILL.md: {skill_dir.name}')
        continue
    content = skill_md.read_text()
    if not content.startswith('---'):
        errors.append(f'缺少 frontmatter: {skill_dir.name}')
    if 'molin_owner' not in content:
        errors.append(f'缺少 molin_owner: {skill_dir.name}')

for e in errors:
    print(f'❌ {e}')
print(f'共发现 {len(errors)} 个问题')
"
```

## 前置条件

- 所有技能目录下有 `SKILL.md`
- SKILL.md 包含规范的 frontmatter
- `.usage.json` 调用日志文件（需启用调用记录）
- 技能已注册到 `AGENTS.md` 或技能索引

## 注意事项

- 评分带有主观性，建议至少两人交叉评估
- 沉睡技能归档前需确认是否有用户依赖
- 季度审查结果应通知相关 molin_owner
- 自动评分仅作参考，最终决策需人工确认
- 低分技能不一定需要废弃 — 可能只是需要更新
