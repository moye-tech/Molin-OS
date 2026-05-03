---
name: molin-company-structure
description: 墨麟一人公司组织架构 — 6部门、232技能、角色定义、汇报线、预算模型。将技能系统映射为可运营的公司结构。
version: 1.0.0
---

# 墨麟 AI 一人公司 · 组织架构

> 基于 Paperclip 公司模型 + Hermes Agent v2 架构

## 公司使命

**月收入 ¥30,000 的 AI 一人公司，通过闲鱼服务 + 小红书IP + 猪八戒接单实现。**

## 组织架构

```
                        董事会（你，尹建业）
                              │
                    ┌─────────┴─────────┐
                    │   COO / 幕僚长     │
                    │ molin-ceo-persona │
                    │ 决策·路由·ROI评估  │
                    └─────────┬─────────┘
                              │
        ┌──────────┬──────────┼──────────┬──────────┬──────────┐
        ▼          ▼          ▼          ▼          ▼          ▼
   ┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐
   │内容中心  ││商业中心  ││增长中心  ││工程中心  ││情报中心  ││运营中心  │
   │content  ││business ││growth   ││eng      ││intel    ││ops      │
   │  22技能  ││  76技能  ││  11技能  ││  23技能  ││  10技能  ││  infra  │
   │         ││         ││         ││         ││         ││         │
   │小红书   ││BP/PRD   ││闲鱼自动  ││全栈开发  ││热度搜索  ││GitHub   │
   │视频引擎  ││市场分析  ││成交话术  ││代码审查  ││OSINT    ││DevOps   │
   │SEO优化  ││SWOT/财务││营销专家  ││调试诊断  ││情报监控  ││定时任务  │
   │AI绘画   ││产品管理  ││销售专家  ││TDD/架构  ││趋势预测  ││Webhook  │
   │PPT/图表 ││交易分析  ││BD报价   ││工作流    ││学术研究  ││记忆系统  │
   └─────────┘└─────────┘└─────────┘└─────────┘└─────────┘└─────────┘
```

## 部门详情

### 内容中心（Content Division）
| 角色 | 核心技能 | 月预算 |
|------|---------|--------|
| 小红书主编 | `xiaohongshu-content-engine` | ¥50 |
| 视频制作 | `pixelle-video` | ¥100 |
| SEO优化师 | `seo-machine` | ¥30 |
| AI画师 | `comfyui` | ¥50 |
| PPT设计师 | `powerpoint` | ¥20 |

### 商业中心（Business Division）
| 角色 | 核心技能 | 月预算 |
|------|---------|--------|
| 产品总监 | `pm-create-prd`, `pm-business-model` | ¥100 |
| 市场研究员 | `pm-market-sizing`, `pm-competitor-analysis` | ¥80 |
| 财务分析师 | `trading-agents`, `pm-business-model` | ¥50 |
| 战略顾问 | `pm-swot-analysis`, `pm-ansoff-matrix` | ¥50 |

### 增长中心（Growth Division）
| 角色 | 核心技能 | 月预算 |
|------|---------|--------|
| 闲鱼运营 | `xianyu-automation` | ¥30 |
| 销售专员 | `agent-sales-deal-strategist` | ¥30 |
| 社媒策略 | `agent-marketing-social-media-strategist` | ¥50 |
| 商务拓展 | `agent-sales-proposal-strategist` | ¥50 |

### 工程中心（Engineering Division）
| 角色 | 核心技能 | 月预算 |
|------|---------|--------|
| 全栈工程师 | `agent-engineering-backend-architect` | ¥200 |
| 前端开发 | `agent-engineering-frontend-developer` | ¥150 |
| QA工程师 | `agent-testing-reality-checker` | ¥80 |
| 代码审查员 | `agent-engineering-code-reviewer` | ¥50 |

### 情报中心（Intelligence Division）
| 角色 | 核心技能 | 月预算 |
|------|---------|--------|
| 趋势分析师 | `mirofish-trends`, `last30days` | ¥80 |
| OSINT调查员 | `maigret-osint` | ¥30 |
| 情报监控员 | `world-monitor` | ¥50 |

### 运营中心（Operations）
| 角色 | 核心技能 | 月预算 |
|------|---------|--------|
| DevOps | webhook, cron, git | ¥30 |
| 记忆管理 | memory, session | ¥0 |

## 治理级别

| 级别 | 触发条件 | 示例 |
|------|---------|------|
| **L0 自动** | 低风险、低金额 | 回复闲鱼消息、发布定时内容 |
| **L1 审查** | 中等风险 | 新服务上线、定价 >¥500 |
| **L2 审批** | 高风险 | 大额报价 >¥2000、合同签署 |
| **L3 董事会** | 战略级 | 新业务线、月预算调整 |

## 月度预算总表

| 部门 | 月预算 | 占比 |
|------|--------|------|
| 内容中心 | ¥250 | 17% |
| 商业中心 | ¥280 | 19% |
| 增长中心 | ¥160 | 11% |
| 工程中心 | ¥480 | 32% |
| 情报中心 | ¥160 | 11% |
| 运营中心 | ¥30 | 2% |
| **合计** | **¥1,360** | |

> 预算基于 DeepSeek API 中等用量估算。实际按 token 消耗跟踪。
