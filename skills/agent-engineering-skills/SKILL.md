---
name: agent-engineering-skills
description: 墨智工程技能库 — 基于 addyosmani/agent-skills (27K⭐) 批量导入的21个生产级工程技能。覆盖API设计/浏览器测试/CI-CD/代码简化/上下文工程/性能优化等功能。
version: 1.0.0
tags: [engineering, skills-library, api-design, testing, perf, security, frontend]
category: engineering
metadata:
  hermes:
    source: https://github.com/addyosmani/agent-skills
    stars: 27000
    upstream_fork: https://github.com/moye-tech/agent-skills
    skills_imported: 21
    new_to_hermes: 12
    molin_owner: 墨智（AI研发）
---

# Agent Engineering Skills — 墨智工程技能库

## 概述

基于 **addyosmani/agent-skills**（27K⭐）批量导入的 21 个生产级工程技能。Hermes 已有 11 个对应技能，新补充 12 个。

## 技能总表

| # | 技能 | 来源 | Hermes状态 | 路径 |
|:-:|:----|:----:|:----------:|:----:|
| 1 | API & Interface Design | agent-skills | 🔴新导入 | `~/agent-skills/skills/api-and-interface-design/` |
| 2 | Browser Testing w/ DevTools | agent-skills | 🔴新导入 | `~/agent-skills/skills/browser-testing-with-devtools/` |
| 3 | CI/CD & Automation | agent-skills | ✅已有 | 参考 `devops/` 系列 |
| 4 | Code Simplification | agent-skills | 🔴新导入 | `~/agent-skills/skills/code-simplification/` |
| 5 | Code Review & Quality | agent-skills | ✅已有 | `requesting-code-review` |
| 6 | Context Engineering | agent-skills | 🔴新导入 | `~/agent-skills/skills/context-engineering/` |
| 7 | Debugging & Error Recovery | agent-skills | ✅已有 | `diagnose` + `systematic-debugging` |
| 8 | Deprecation & Migration | agent-skills | 🔴新导入 | `~/agent-skills/skills/deprecation-and-migration/` |
| 9 | Documentation & ADRs | agent-skills | 🔴新导入 | `~/agent-skills/skills/documentation-and-adrs/` |
| 10 | Frontend UI Engineering | agent-skills | ✅已有 | `agent-engineering-frontend-developer` |
| 11 | Git Workflow & Versioning | agent-skills | ✅已有 | `github-pr-workflow` |
| 12 | Idea Refine | agent-skills | 🔴新导入 | `~/agent-skills/skills/idea-refine/` |
| 13 | Incremental Implementation | agent-skills | 🔴新导入 | `~/agent-skills/skills/incremental-implementation/` |
| 14 | Performance Optimization | agent-skills | 🔴新导入 | `~/agent-skills/skills/performance-optimization/` |
| 15 | Planning & Task Breakdown | agent-skills | ✅已有 | `plan` + `writing-plans` |
| 16 | Security & Hardening | agent-skills | ✅已有 | `requesting-code-review` |
| 17 | Shipping & Launch | agent-skills | 🔴新导入 | `~/agent-skills/skills/shipping-and-launch/` |
| 18 | Source-Driven Development | agent-skills | 🔴新导入 | `~/agent-skills/skills/source-driven-development/` |
| 19 | Spec-Driven Development | agent-skills | 🔴新导入 | `~/agent-skills/skills/spec-driven-development/` |
| 20 | Test-Driven Development | agent-skills | ✅已有 | `test-driven-development` |
| 21 | Using Agent Skills | agent-skills | 元技能 | 参考说明 |

## 如何使用

需要任何工程技能时，直接引用对应目录：

```
任务需要 API 设计 → 参考 ~/agent-skills/skills/api-and-interface-design/SKILL.md
需要浏览器测试 → 参考 ~/agent-skills/skills/browser-testing-with-devtools/SKILL.md
需要性能优化 → 参考 ~/agent-skills/skills/performance-optimization/SKILL.md
```

## 按 Hermes 已有技能映射

agent-skills 中已有对应 Hermes 技能的 9 项，直接用 Hermes 技能：

```
agent-skills                      → Hermes
─────────────────────────────────────────
test-driven-development           → test-driven-development
code-review-and-quality           → requesting-code-review
debugging-and-error-recovery      → diagnose + systematic-debugging
planning-and-task-breakdown       → plan + writing-plans
git-workflow-and-versioning       → github-pr-workflow
frontend-ui-engineering           → agent-engineering-frontend-developer
ci-cd-and-automation              → archon-workflow
security-and-hardening            → requesting-code-review
documentation-and-adrs            → zoom-out
```
