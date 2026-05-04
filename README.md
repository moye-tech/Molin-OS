<!--
  README.md — 墨麟 Hermes OS
  遵循 GitHub Flavored Markdown 规范
-->

# 墨麟 Hermes OS

<p align="center">
  <strong>AI 一人公司操作系统</strong> — 将整个公司的能力打包进一个 Python 项目
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-00b894?style=flat-square&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-00b894?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/skills-267-6c5ce7?style=flat-square" alt="Skills">
  <img src="https://img.shields.io/badge/status-active-brightgreen?style=flat-square" alt="Status">
</p>

---

## 目录

- [概述](#概述)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [CLI 参考](#cli-参考)
- [配置说明](#配置说明)
- [项目结构](#项目结构)
- [许可证](#许可证)

---

## 概述

墨麟 Hermes OS 是基于 Hermes Agent 构建的 AI 原生操作系统。它将一家公司需要的全部能力——**战略决策、内容创作、多平台发布、商业变现、情报监控、持续学习**——封装为一个可部署的 Python 系统。

```
你 + 墨麟 Hermes OS = 全自动运转的一人公司
```

| 维度 | 传统模式 | 墨麟模式 |
|:---|:---|:---|
| 执行主体 | 人工逐项完成 | AI Agent 自动执行 |
| 内容产出 | 月产 ~10 条 | 日产 ~10 条 |
| 收入来源 | 1 个 | 6+ 变现矩阵 |
| 平台发布 | 逐平台手动 | 一键多平台 |
| 演进方式 | 被动学习 | 自动评估→吸收→集成 |

---

## 系统架构

### 组织架构（22 墨系子公司）

| # | 子公司 | 月收入目标 | 职责 |
|:-:|:------|:--------:|:-----|
| 01 | 墨智（AI研发） | ¥2,000 | AI 基础能力、MLOps、Agent 开发 |
| 02 | 墨码（软件工坊） | ¥5,000 | 软件开发、技术外包、代码实现 |
| 03 | 墨商BD（商务拓展） | ¥3,000 | 投标、方案、商务对接 |
| 04 | 墨影（IP孵化） | ¥5,000 | 小红书/知乎 IP 孵化与品牌合作 |
| 05 | 墨增（增长引擎） | ¥3,000 | 增长实验、A/B 测试、SEO/CRO |
| 06 | 墨声（客服） | ¥1,000 | 智能客服、FAQ 自动维护 |
| 07 | 墨域（私域CRM） | ¥3,000 | 私域运营、微信公众号、复购激活 |
| 08 | 墨单（订单交付） | ¥2,000 | 询盘处理、报价、交付管理 |
| 09 | 墨算（财务） | ¥2,000 | 成本核算、ROI 分析、预算 |
| 10 | 墨思（情报研究） | ¥2,000 | 行业研究、趋势洞察、竞品分析 |
| 11 | 墨律（法务） | ¥1,000 | 合同审查、合规风险、隐私合规 |
| 12 | 墨盾（安全/QA） | ¥1,000 | 安全审计、代码审查、风险评估 |
| 13 | 墨品（产品设计） | ¥2,000 | MVP 设计、PRD、产品路线图 |
| 14 | 墨数（数据） | ¥2,000 | 数据分析、BI 报表、可视化 |
| 15 | 墨维（运维） | ¥1,000 | CI/CD、GitHub、DevOps 基础设施 |
| 16 | 墨育（教育） | ¥1,000 | 课程设计、培训、知识付费 |
| 17 | 墨海（出海） | ¥2,000 | 多语言内容、海外平台运营 |
| 18 | 墨脑（知识管理） | ¥1,000 | SOP、知识图谱、最佳实践沉淀 |
| 19 | 墨迹（内容工厂） | ¥2,000 | 内容代写、短视频、PPT 制作 |
| 20 | 墨投（量化交易） | ¥1,000 | 量化分析、投资建议、市场研判 |
| 21 | 墨商销售（闲鱼实业） | ¥5,000 | 闲鱼销售转化、C 端商品出售 |
| 22 | 墨工（设计） | ¥2,000 | AI 音乐、UI/UX、品牌视觉 |
| | **合计** | **¥48,000** | 总预算 ¥2,440/月 |

### 技能体系（三层归属）

所有 267 个 Hermes 技能按 `molin_owner` 标签分为三层：

- **🔵 CEO 核心（27 skills）** — 战略、治理、调度、元技能，归 Hermes/你本人掌握
- **🟢 子公司专用（239 skills）** — 映射到 19/22 家子公司，每个技能有明确的业务归属
- **🟡 共享（1 skill）** — 全系统通用的公共设施

### 能力全景

```
┌─────────────────────────────────────────────────────────┐
│                  墨麟 Hermes OS                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│   │  CEO 决策 │  │  内容工厂  │  │  商业引擎  │  │ 增长引擎│ │
│   │  (27 skills)  │  (18 skills) │  (7 skills) │  (19 skills)│
│   └─────┬────┘  └─────┬────┘  └─────┬────┘  └───┬────┘ │
│         │              │             │           │      │
│   ┌─────┴────┐  ┌──────┴──────┐  ┌──┴──────┐  ┌┴─────┐ │
│   │   研发    │  │   情报      │  │  AI 基础 │  │ 运维  │ │
│   │  (31 skills) │  (12 skills) │  │(28 skills)│  │(27 skills)│
│   └──────────┘  └────────────┘  └─────────┘  └───────┘ │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  知识库: 267 SKILL.md  │  22 子公司  │  预算: ¥2,440/m  │
└─────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 环境要求

| 依赖 | 必需 | 说明 |
|:---|:---:|:-----|
| Python ≥ 3.10 | ✅ | |
| Git | ✅ | |
| Hermes Agent | ✅ | 底层 Agent 运行时 |
| FFmpeg | 可选 | 视频生成管线 |

### 安装

```bash
# 克隆仓库
git clone https://github.com/moye-tech/-Hermes-OS.git
cd -Hermes-OS

# 一键部署
bash setup.sh

# 验证
molin health
```

### 配置

编辑 `~/.molin/.env`，填入各平台 API Key（参考 `.env.example` 模板）。

---

## CLI 参考

| 命令 | 说明 |
|:---|:---|
| `molin ceo strategy` | 生成 CEO 战略决策 |
| `molin ceo review` | 审查周度业绩 |
| `molin content xhs <主题>` | 生成小红书内容 |
| `molin content video <主题>` | 生成视频脚本 |
| `molin content seo <关键词>` | 生成 SEO 优化内容 |
| `molin publish <平台>` | 发布到指定平台 |
| `molin xianyu list` | 列出闲鱼商品 |
| `molin xianyu publish` | 发布闲鱼商品 |
| `molin business bp <项目>` | 生成商业计划书 |
| `molin business prd <产品>` | 生成产品需求文档 |
| `molin intel trends` | 趋势洞察报告 |
| `molin intel monitor` | 启动持续监控 |
| `molin swarm run <任务>` | 蜂群并行执行 |
| `molin learn` | 执行自学习循环 |
| `molin serve` | 启动 Web 仪表盘 (端口 8080) |
| `molin schedule list` | 查看定时任务 |
| `molin health` | 系统健康检查 |

---

## 配置说明

| 文件 | 说明 |
|:---|:-----|
| `config/company.yaml` | 公司结构（22 墨系子公司）、预算、变现矩阵 |
| `config/governance.yaml` | L0-L3 四级审批规则、审计日志、安全策略 |
| `config/channels.yaml` | 多平台发布配置（日限额、最佳发布时间、内容类型） |
| `.env.example` | API Keys、Hermes 连接配置、告警等环境变量模板 |

### 治理级别

| 级别 | 预算上限 | 审批方式 |
|:---:|:---:|:---:|
| L0 | ¥0 | 自动执行 |
| L1 | ≤ ¥10 | AI 自审 |
| L2 | ≤ ¥100 | 人工确认 |
| L3 | ≤ ¥1,000 | 董事会审批 |

---

## 项目结构

```
-Hermes-OS/
├── README.md
├── LICENSE
├── setup.sh               # 一键部署脚本
├── Makefile               # 常用命令入口
├── setup.py               # pip install -e . 安装配置
├── requirements.txt       # Python 依赖
├── .env.example           # 环境变量模板
├── .gitignore
│
├── config/                # YAML 配置文件
│   ├── company.yaml       #   公司架构、预算、变现
│   ├── governance.yaml    #   审批规则、审计、安全
│   └── channels.yaml      #   发布渠道配置
│
├── molin/                 # Python 源码
│   ├── cli.py             #   CLI 入口
│   ├── dashboard.py       #   Web 仪表盘 (Flask)
│   ├── core/              #   核心层: 引擎/治理/调度
│   ├── agents/            #   智能体层: CEO/蜂群/自学习
│   ├── content/           #   内容层: 小红书/视频/SEO
│   ├── publish/           #   发布层: 多平台/闲鱼
│   ├── intelligence/      #   情报层: 趋势/OSINT/监控
│   └── business/          #   商业层: BP/PRD
│
├── skills/                # Hermes 知识库 (267 个)
│   ├── meta/              #   决策与治理
│   ├── engineering/       #   软件开发
│   ├── business/          #   商业与产品
│   ├── content/           #   内容创作
│   ├── growth/            #   增长营销
│   ├── intelligence/      #   情报研究
│   ├── mlops/             #   AI/ML 引擎
│   ├── creative/          #   设计与创意
│   └── 40+ 更多领域       #   54 领域全覆盖
│
├── tests/                 # 测试套件
├── docs/                  # 文档与案例
├── tools/                 # 运维脚本
└── cron/                  # cron 任务脚本
```

---

## 许可证

本项目基于 [MIT License](LICENSE) 开源。

---

<p align="center">
  <sub>Built by <a href="https://github.com/moye-tech">moye-tech</a> · <a href="mailto:fengye940708@gmail.com">fengye940708@gmail.com</a></sub>
</p>
