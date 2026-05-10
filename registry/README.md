# Molin Skills Registry

墨麟OS 社区技能注册中心 — 对标 [Obsidian community-plugins.json](https://github.com/obsidianmd/obsidian-releases)。

## 这是什么？

这是墨麟OS（Molin-OS）的官方技能目录。Hermes Agent 从这里读取可用技能列表，用户可以浏览和安装社区贡献的技能。

## 架构

```
moye-tech/Molin-Skills-Registry
├── community-skills.json          # 技能目录（单一真相源）
├── community-skills-stats.json    # 自动生成的统计
├── community-skills-deprecated.json # 已下架技能
├── DEVELOPER_POLICIES.md          # 开发者政策
├── .github/
│   ├── ISSUE_TEMPLATE/submit-skill.yml  # PR 提交模板
│   └── workflows/validate.yml          # 自动验证 + 统计
└── README.md
```

## 对标参考

| 功能 | Obsidian | 墨麟OS |
|------|----------|--------|
| 技能目录 | community-plugins.json | community-skills.json |
| 版本管理 | manifest.json | SKILL.md frontmatter |
| 统计 | community-plugin-stats.json | community-skills-stats.json |
| 下架追踪 | community-plugins-removed.json | community-skills-deprecated.json |
| 开发者政策 | Developer Policies | DEVELOPER_POLICIES.md |
| 审核 | PR Review | PR Review |

## 提交你的技能

1. Fork 本仓库
2. 在 `community-skills.json` 的 `skills` 数组末尾添加你的条目
3. 确保所有必需字段完整
4. 提交 PR 并完成清单

详见 [DEVELOPER_POLICIES.md](DEVELOPER_POLICIES.md)。

## 技能条目格式

```json
{
  "id": "my-skill",
  "name": "My Awesome Skill",
  "author": "Your Name",
  "description": "简短描述（50-200字）",
  "repo": "username/repo-name",
  "version": "1.0.0",
  "min_hermes_version": "0.13.0",
  "tags": ["tag1", "tag2"],
  "category": "tools",
  "added": "2026-05-10"
}
```

## 如何安装技能

用户在 Hermes Agent 中：
```bash
# 浏览可用技能
python -m molib query "FROM skills WHERE category = 'tools'"

# 安装技能
hermes skills install my-skill
```

## 许可证

MIT
