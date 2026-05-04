---
name: gstack-agent-templates
description: 23个生产级Agent配置模板 — 基于 garrytan/gstack (88K⭐)，YC CEO Garry Tan 的 Claude Code Agent 配置。直接导入 Hermes Agent 系统，让墨麟具备 CIO 级别的 Agent 组织能力。
version: 1.0.0
tags: [agent-templates, gstack, garrytan, orchestration, ceo, production]
category: meta
metadata:
  hermes:
    source: https://github.com/garrytan/gstack
    stars: 88638
    author: Garry Tan (YC CEO)
    agents: 23
    molin_owner: 墨智（AI研发）
---

# GStack Agent Templates — 23个生产级Agent配置

## 概述

基于 YC CEO Garry Tan 的 gstack（88K⭐）配置体系，包含 23 个专业 Agent 的定义、职责范围、工具集和协作模式。这些模板可直接用于 Hermes Agent，极大提升墨麟各子公司的专业化程度。

## 23个Agent总览

### 🏛️ 指挥层（2个）
| # | Agent | 角色 | 对应墨麟 |
|:-:|:------|:----|:--------:|
| 1 | **CEO Agent** | 总编排 - 分解任务→委派→合成结果 | 董事会/你 |
| 2 | **PM Agent** | 项目管理 - 任务拆解/进度/依赖追踪 | 墨品 |

### 🎨 产品设计（4个）
| # | Agent | 角色 | 对应墨麟 |
|:-:|:------|:----|:--------:|
| 3 | **Product Agent** | PRD/规格/产品决策 | 墨品 |
| 4 | **Design Agent** | UI/UX设计/线框图 | 墨工 |
| 5 | **UX Agent** | 交互模式/无障碍/用户流 | 墨工 |
| 6 | **User Research Agent** | 用户反馈综合/人物画像 | 墨思 |

### 🔧 工程技术（5个）
| # | Agent | 角色 | 对应墨麟 |
|:-:|:------|:----|:--------:|
| 7 | **Frontend Agent** | React/TypeScript/CSS | 墨码 |
| 8 | **Backend Agent** | Node/Python/Go/API | 墨码 |
| 9 | **Data Agent** | SQL/分析管道/数据建模 | 墨数 |
| 10 | **Architecture Agent** | 系统设计/技术评估 | 墨智 |
| 11 | **DevOps Agent** | Docker/K8s/CI/CD/监控 | 墨维 |

### ✅ 质量保障（2个）
| # | Agent | 角色 | 对应墨麟 |
|:-:|:------|:----|:--------:|
| 12 | **QA Agent** | 测试计划/自动测试/回归 | 墨盾 |
| 13 | **Security Agent** | 威胁建模/漏洞扫描/合规 | 墨盾 |

### 📈 增长业务（3个）
| # | Agent | 角色 | 对应墨麟 |
|:-:|:------|:----|:--------:|
| 14 | **Growth Agent** | A/B测试/漏斗分析/增长飞轮 | 墨增 |
| 15 | **Marketing Agent** | 内容策略/文案/品牌 | 墨迹 |
| 16 | **Sales Agent** | 管道管理/外联模板/CRM | 墨商BD |

### 🛟 支持运营（3个）
| # | Agent | 角色 | 对应墨麟 |
|:-:|:------|:----|:--------:|
| 17 | **Support Agent** | 工单分类/FAQ/升级模式 | 墨声 |
| 18 | **Customer Success Agent** | 入门流程/健康分/留存 | 墨域 |
| 19 | **Legal Agent** | 条款审查/隐私合规/许可 | 墨律 |

### 📊 数据战略（4个）
| # | Agent | 角色 | 对应墨麟 |
|:-:|:------|:----|:--------:|
| 20 | **Analytics Agent** | 仪表盘/KPI/异常检测 | 墨数 |
| 21 | **Research Agent** | 竞品分析/市场研究/趋势 | 墨思 |
| 22 | **Finance Agent** | 成本追踪/预算建模/ROI | 墨算 |
| 23 | **Operations Agent** | 流程优化/内部工具/自动化 | 墨维 |

## 使用方式

这些 Agent 定义已从 gstack 仓库同步至本地：

```bash
cd ~/gstack-reference/agents
# 查看所有Agent定义
ls *.md
# 读取某个Agent
cat ceo-agent.md
```

### 在 Hermes 中调用

当需要某个领域的能力时，加载对应的 Agent 模板：

```python
# 示例：需要增长策略
"""
加载 Growth Agent 模板：
1. 角色：增长黑客
2. 核心能力：A/B测试、漏斗分析、增长飞轮
3. 方法：识别增长杠杆 → 假设验证 → 行动方案
"""
```

## gstack 核心理念（ETHOS）

| 原则 | 含义 |
|:----|:------|
| **速度即特性** | 快跑快迭代 |
| **清晰胜复杂** | 简单方案 > 聪明方案 |
| **结果胜产出** | 衡量影响，而非活动 |
| **行动偏误** | 完美是完成的大敌 |
| **主人翁心态** | 每个 Agent 都像创始人一样行动 |
| **透明至上** | 自由分享上下文，不隐藏 |
| **系统思维** | 解决根本原因，而非症状 |
| **默认开放** | 多写多分享，事事文档化 |

## 对应墨麟子公司的装态

| 子公司 | 已有能力 | gstack 补充 | 装态 |
|:------|:---------|:-----------|:----:|
| 墨智 | 工程技能 | Architecture Agent | ✅ |
| 墨码 | 开发技能 | Frontend/Backend/Fullstack Agent | ✅ |
| 墨增 | 空（标记---） | **Growth Agent** — 直接填补缺口 | 🔥 |
| 墨思 | 情报能力 | Research Agent — 交叉参考 | ✅ |
| 墨品 | PM技能 | Product/PM Agent | ✅ |
| 墨商BD | 销售技能 | Sales Agent | ✅ |
| 墨迹 | 内容管线 | Marketing Agent | ✅ |
| 墨声 | 客服技能 | Support Agent | ✅ |
| 墨域 | CRM技能 | Customer Success Agent | ✅ |
| 墨数 | 数据技能 | Data/Analytics Agent | ✅ |
| 墨算 | 财务技能 | Finance Agent | ✅ |
| 墨盾 | 安全技能 | QA/Security Agent | ✅ |
| 墨律 | 法务技能 | Legal Agent | ✅ |
| 墨维 | 运维技能 | DevOps/Operations Agent | ✅ |
| 墨工 | 设计技能 | Design/UX Agent | ✅ |
