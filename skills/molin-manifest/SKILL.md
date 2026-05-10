---
name: molin-manifest
description: Manifest 标准化工具 — 为墨麟OS所有技能提供统一的版本管理标准（对标 Obsidian manifest.json）。支持验证、自动修复、批量升级。
version: 1.0.0
min_hermes_version: 0.13.0
tags: [molin-os, manifest, versioning, standardization, skills]
category: infrastructure
---

# Manifest 标准化

为墨麟OS所有技能提供统一的版本管理标准，对标 Obsidian manifest.json 规范。

## 标准字段

```yaml
---
name: skill-name              # 必需 — 技能名称（与目录名一致）
description: "描述文本"        # 必需 — 简短描述
version: 1.0.0                # 必需 — 语义化版本
min_hermes_version: 0.13.0    # 必需 — 最低兼容 Hermes 版本
dependencies:                 # 可选 — 依赖的其他技能
  - other-skill
tags: [tag1, tag2]            # 推荐 — 分类标签
category: infrastructure      # 推荐 — 分类
source: https://...           # 可选 — 原始来源
metadata:                     # 可选 — 扩展元数据
  key: value
---
```

## 用法

```bash
# 验证所有技能
python -m molib manifest validate

# 验证指定技能
python -m molib manifest validate --skill obsidian

# 自动修复缺失字段
python -m molib manifest fix

# 升级单个技能
python -m molib manifest upgrade --skill obsidian
```

## Python API

```python
from molib.core.tools.manifest_validator import (
    validate_all_skills, validate_skill_manifest, print_report, auto_fix_skill
)
from molib.core.tools.manifest_upgrader import (
    upgrade_skill, upgrade_all, normalize_frontmatter, create_manifest_template
)

# 验证
report = validate_all_skills(skills_dir)
print_report(report)

# 升级
result = upgrade_all(skills_dir, hermes_version="0.13.0")

# 生成模板
template = create_manifest_template(
    name="my-skill",
    description="我的技能",
    category="tools"
)
```

## 对标参考

- Obsidian manifest.json: https://docs.obsidian.md/Plugins/Releasing/Submit+your+plugin
- Agent Skills spec: https://github.com/agent-skills/specification
