---
name: batch-yaml-frontmatter-injection
description: 批量注入/修改 SKILL.md 的 YAML frontmatter 字段（如 molin_owner），处理行号前缀文件、多 frontmatter、缺失 metadata 块等各种边界情况。
version: 1.0.0
tags: [batch, yaml, frontmatter, maintenance, metadata, skills]
---

# 批量 YAML Frontmatter 注入

当需要对 Hermes 技能库（或任何 Markdown 文件集合）做批量 frontmatter 修改时使用。

## 适用场景

- 给全部技能注入新元数据字段（如 `molin_owner`）
- 修复大量技能文件的 YAML 格式问题
- 更新所有技能的版本号或描述
- 统一 metadata 结构

## 步骤

### 1. 先扫描，后批量

```bash
# 统计总数
find ~/.hermes/skills -name 'SKILL.md' | wc -l

# 检查已有字段覆盖
grep -rl 'molin_owner:' ~/.hermes/skills/ --include='SKILL.md' | wc -l

# 查看字段分布
grep -rh 'molin_owner:' --include='SKILL.md' ~/.hermes/skills/ | sort | uniq -c | sort -rn

# 查看未覆盖文件
grep -rL 'molin_owner:' ~/.hermes/skills/ --include='SKILL.md'
```

### 2. 检查行号前缀文件

有些文件可能带有 `N|` 或 `     N|` 行号前缀（Hermes 工具输出的遗留格式）。检查方法：

```bash
# 检查前5行是否有行号前缀
head -5 some/skill/SKILL.md | od -c

# 批量查找
find ~/.hermes/skills -name 'SKILL.md' -exec sh -c '
  grep -q "^\s*[0-9]|" "$1" && echo "$1"
' _ {} \;
```

修复方法（Python）：
```python
import re
def fix_line_numbers(content):
    lines = content.split('\n')
    return '\n'.join(re.sub(r'^\s*\d+\|', '', l) for l in lines)
```

### 3. 分类设计

不要在脚本里直接硬编码所有映射。应该先设计分类方案：

```
三层体系参考：
1. CEO 层 — 元技能、治理、调度、架构
2. 子公司层 — 按业务线垂直归属
3. 共享层 — 谁都能用的公共技能
```

写一个 Python 字典映射表，支持：
- **精确匹配**：`rel_path → owner`
- **前缀/通配符匹配**：`prefix/* → owner`（用于 PM 技能库等批量技能）

### 4. 注入策略（处理多种 YAML 结构）

SKILL.md 的 frontmatter 有 3+ 种变体：

**变体 A：标准 `metadata.hermes` 结构**
```yaml
---
name: xxx
metadata:
  hermes:
    tags: [xxx]
---
```
→ 在 `hermes:` 下加 `    field: value`

**变体 B：有 metadata 但无 hermes**
```yaml
---
name: xxx
metadata:
  sources:
    - url
---
```
→ 在 metadata 块内创建 `  hermes:` 子块

**变体 C：无 metadata 块**
```yaml
---
name: xxx
description: yyy
---
```
→ 在 frontmatter 末尾（`---` 前）插入整个 `metadata.hermes.field`

**变体 D：多 frontmatter（antigravity 等）**
```yaml
---
name: ag-xxx  # 聚合头
source: github
---
---
name: real-skill  # 实际技能
description: ...
---
```
→ 在 **最后一个** `---` 之前注入

核心注入代码（Python）：
```python
def inject_field(content, field_name, field_value):
    """在最后一个 --- 前注入 metadata.hermes.{field_name}: {field_value}"""
    if content.count('---') < 2:
        return content, False
    
    lines = content.split('\n')
    # 找最后一个 ---
    last_delim = None
    for i, line in enumerate(lines):
        if line.strip() == '---':
            last_delim = i
    
    if last_delim is None:
        return content, False
    
    # 检查是否已有该字段
    frontmatter = lines[1:last_delim]
    for line in frontmatter:
        if field_name in line:
            return content, False  # already exists
    
    # 检查现有结构
    has_meta = any(l.strip() == 'metadata:' for l in frontmatter)
    has_hermes = any('hermes:' in l for l in frontmatter)
    
    insert_lines = []
    if not has_meta:
        insert_lines = ['metadata:', '  hermes:', f'    {field_name}: {field_value}']
    elif not has_hermes:
        insert_lines = ['  hermes:', f'    {field_name}: {field_value}']
    else:
        insert_lines = [f'    {field_name}: {field_value}']
    
    new_lines = lines[:last_delim] + insert_lines + lines[last_delim:]
    return '\n'.join(new_lines), True
```

### 5. 验证

```bash
# 总数不变
find ~/.hermes/skills -name 'SKILL.md' | wc -l

# 所有文件都有新字段
grep -rL 'field_name:' ~/.hermes/skills/ --include='SKILL.md' | wc -l  # 应该为 0

# 分布合理
grep -rh 'field_name:' --include='SKILL.md' ~/.hermes/skills/ | sort | uniq -c | sort -rn
```

## 陷阱

1. **行号前缀文件** — `cat -A` 输出格式被写入文件，表现为 `N|内容\n`。此类文件 grep / sed 解析 `---` 会失败，必须先修复格式
2. **多 frontmatter** — antigravity 类技能可能有多层 `---` 包裹。注入时请匹配 **最后一个** `---`，因为前面的都是聚合元数据
3. **YAML 缩进** — Hermes frontmatter 统一用 2-space 缩进。metadata.hermes 下是 4-space
4. **已存在检查** — 注入前必须检查字段是否已存在，避免重复
5. **文件编码** — 全部为 UTF-8 / ASCII，无特殊
