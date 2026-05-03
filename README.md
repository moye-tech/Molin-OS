# 墨麟 Hermes OS

> 一人公司 AI 操作系统 — 232 技能 · 6 部门 · 自进化

基于 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 构建的企业级 AI 智能体系统，专为「一个人运营一家公司」设计。

## 架构

```
┌─────────────────────────────────────────┐
│           governance · 治理层            │
│   4级审批 · 预算控制 · 审计 · 回滚        │
├─────────────────────────────────────────┤
│           meta · 决策层                  │
│   CEO人格 · 蜂群引擎 · 自学习 · 技能发现  │
├──────────┬──────────┬───────────────────┤
│ content  │ business │ growth            │
│ 23技能    │ 76技能    │ 11技能            │
│ 小红书   │ PM/BP    │ 闲鱼自动化         │
│ 视频引擎  │ 市场分析  │ 成交话术           │
│ SEO/AI画 │ 财务/法务 │ 营销/BD            │
├──────────┼──────────┼───────────────────┤
│engineering│intelligence│ infrastructure   │
│ 23技能    │ 10技能     │ 支持层            │
│ 编码/调试 │ 搜索/OSINT │ GitHub/DevOps     │
│ TDD/架构  │ 监控/趋势  │ MCP/MLOps         │
└──────────┴──────────┴───────────────────┘
```

## 核心能力

- **内容工厂**: 小红书算法级引擎 · AI视频管线 · SEO优化 · AI绘画
- **商业大脑**: 50+ PM技能 · BP/PRD · SWOT · TAM/SAM/SOM · 财务分析
- **销售引擎**: 闲鱼自动化(30+成交信号) · 五步成交话术 · 多平台自动发布
- **研发工坊**: 全栈开发 · 代码审查 · 调试诊断 · 确定性工作流
- **情报系统**: 跨平台热度搜索 · OSINT侦查 · 蜂群趋势预测
- **自进化**: 每次任务后反思→结晶→更新技能

## 技能来源

| 来源 | 技能数 | Stars |
|------|--------|-------|
| Hermes Agent 内置 | 85+ | — |
| Matt Pocock Skills | 6 | 56K |
| Antigravity Skills | 39 | 36K |
| PM Skills Marketplace | 49 | — |
| Agency Agents | 23 | — |
| Molin AI System | 12 | — |
| Pixelle-Video | 1 | 9.6K |
| SEO Machine | 1 | 6.8K |
| TradingAgents | 1 | 64K |
| MiroFish | 1 | 59K |
| World Monitor | 1 | 53K |
| Maigret OSINT | 1 | 23K |
| Archon | 1 | 20K |
| Marketing Skills | 2 | 26K |
| Social Push | 1 | — |
| 自建技能 | 3 | — |

## 项目结构

```
molin-hermes-os/
├── README.md                    # 本文件
├── skills/                      # 232个SKILL.md技能
│   ├── meta/                    # 决策层(CEO/蜂群/自学习)
│   ├── content/                 # 内容工厂
│   ├── business/                # 商业大脑
│   ├── engineering/             # 研发工坊
│   ├── growth/                  # 销售引擎
│   └── intelligence/            # 情报系统
└── docs/                        # 文档与案例
    ├── 能力白皮书_2026.md
    ├── 商业计划书_样品.md
    ├── 简历优化_样品.md
    └── AI绘画案例_样品.md
```

## 心跳系统

| 任务 | 时间 | 内容 |
|------|------|------|
| 每日早报 | 每天 9:00 | 闲鱼消息 + 情报摘要 |
| 每周复盘 | 周一 10:00 | 收入回顾 + 战略调整 |

## 相关项目

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) — AI 智能体框架
- [Molin AI System](https://github.com/moye-tech/molin-ai-intelligent-system) — 企业级多Agent系统
- [Paperclip](https://github.com/paperclipai/paperclip) — 零人类公司编排

## 许可

MIT License

---

> 墨麟一人公司 · 用 AI 一个人干一个公司的活
