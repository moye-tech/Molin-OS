---
name: pm-skills-marketplace
description: PM技能市场 — 基于 phuryn/pm-skills (11K⭐) 批量导入的 65 个产品管理技能和 36 个工作流。覆盖产品发现/战略/执行/增长/市场研究全链路。墨品（产品设计）技能库。
version: 1.0.0
tags: [product-management, skills, marketplace, discovery, strategy, growth]
category: business
metadata:
  hermes:
    source: https://github.com/phuryn/pm-skills
    stars: 11000
    upstream_fork: https://github.com/moye-tech/pm-skills
    skills_available: 65
    workflows: 36
    plugins: 8
    molin_owner: 墨品（产品设计）
---

# PM Skills Marketplace — 墨品产品管理技能库

## 概述

基于 **phuryn/pm-skills**（11K⭐）的 65 个产品管理技能 + 36 个链式工作流。Hermes 已有 30+ `pm-*` 系列技能，本技能导入新增内容。

## 插件架构

pm-skills 分为 8 个插件（对应 8 个能力域）：

| 插件 | 技能数 | Hermes 覆盖度 |
|:----|:------|:-------------|
| **pm-product-discovery** | 12个 | ✅ 已有（Hermes pm-* 系列已覆盖） |
| **pm-product-strategy** | 6个 | ✅ 已有 |
| **pm-execution** | 10个 | ✅ 已有 |
| **pm-go-to-market** | 8个 | ✅ 已有 |
| **pm-marketing-growth** | 6个 | ✅ 已有 |
| **pm-market-research** | 5个 | ✅ 已有 |
| **pm-data-analytics** | 4个 | ✅ 已有 |
| **pm-toolkit** | 14个 | ⚡ 部分新增 |

## Hermes vs pm-skills 对照

Hermes 已有以下对应技能：
```
pm-skills 插件            Hermes 对应技能
─────────────────────────────────────────
/discover                  pm-analyze-feature-requests
/assumptions               pm-identify-assumptions-*
/prioritize                pm-prioritize-features
/strategy                  pm-ansoff-matrix
/user-persona              pm-user-personas
/write-prd                 pm-create-prd
/north-star                pm-north-star-metric
/market-sizing             pm-market-sizing
/customer-journey          pm-customer-journey-map
/ab-test                   pm-ab-test-analysis
/cohort                    pm-cohort-analysis
```

## pm-toolkit 新增内容

pm-skills 的 **pm-toolkit** 插件提供了 14 个辅助工具技能，其中部分 Hermes 未覆盖：

- Resume Review（pm-review-resume）
- 更多模板和工作流

## 如何使用

```bash
# 查看所有 pm 技能
cd ~/pm-skills
ls -d pm-*/

# 查看某个技能的详细内容
cat ~/pm-skills/pm-discovery/discover/SKILL.md
```

## 按需使用

需要 PM 能力时：
1. 先检查 Hermes 已有 `pm-*` 系列技能（30+ 个）
2. 如果 Hermes 没有，从 `~/pm-skills/` 对应插件中查找
3. 结合两者使用
