<!--
  README.md — 墨麟 Hermes OS
  遵循 GitHub Flavored Markdown 规范
-->

# 墨麟 Hermes OS

<p align="center">
  <strong>AI 一人公司操作系统</strong> — 将整个公司的能力打包进一个 Python 项目
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-4.0.0-6c5ce7?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/python-3.10+-00b894?style=flat-square&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/tests-21%20passed-success?style=flat-square" alt="Tests">
  <img src="https://img.shields.io/badge/license-MIT-00b894?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/status-active-brightgreen?style=flat-square" alt="Status">
</p>

---

## 目录

- [概述](#概述)
- [特性](#特性)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [CLI 参考](#cli-参考)
- [配置说明](#配置说明)
- [项目结构](#项目结构)
- [测试](#测试)
- [安全](#安全)
- [许可证](#许可证)

---

## 概述

墨麟 (Molin) 是一个基于 Hermes Agent 构建的 AI 原生操作系统。它将一家公司需要的全部能力——**战略决策、内容创作、多平台发布、商业变现、情报监控、持续学习**——封装为一个可部署的 Python 系统。

```
你 + 墨麟 Hermes OS = 全自动运转的一人公司
```

| 维度 | 传统模式 | 墨麟模式 |
|:---|:---|:---|
| 执行主体 | 人工逐项完成 | AI Agent 自动执行 |
| 内容产出 | 月产 ~10 条 | 日产 ~10 条 |
| 收入来源 | 1 个 | 6+ 变现矩阵 |
| 平台发布 | 逐平台手动 | 一键 7 平台 |
| 演进方式 | 被动学习 | 自动评估→吸收→集成 |

---

## 特性

### 核心能力

- **🧠 CEO 决策引擎** — 使命→OKR→周任务→日行动 四级目标级联
- **📱 内容工厂** — 小红书算法级内容生成 + FFmpeg 视频管线 + SEO 优化
- **📡 7 平台发布** — 小红书 / 知乎 / 微博 / 微信公众号 / 掘金 / X / 闲鱼 统一发布
- **📊 商业引擎** — 商业计划书 / PRD / 定价策略 自动生成
- **🔭 情报系统** — 5 源趋势监控 + OSINT 开源情报 + 世界事件追踪
- **🐝 蜂群编排** — 7 角色并行调度 (CEO / 分析师 / 创作者 / 开发者 / 审阅者 / 发布者 / 监控者)
- **🧬 自学习循环** — 评估 → 吸收 → 集成 → 淘汰，持续自动进化
- **⚖️ 治理系统** — L0-L3 四级审批 + 审计追踪 + 预算控制

### 技术特性

- **Python 3.10+** 原生实现，无重型框架依赖
- **21 个单元测试**覆盖全部核心模块
- **一键部署脚本** (`bash setup.sh`)
- **Web 仪表盘** (Flask，暗色主题)
- **定时心跳** (每日 9:00 + 每周一 10:00 + 每 6h 趋势扫描)
- **YAML 配置**驱动，零硬编码

---

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                 墨麟 Hermes OS v4.0                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│   │  CEO 决策 │  │  内容工厂  │  │  商业大脑  │  │ 增长引擎│ │
│   │  1 人     │  │  4 人     │  │  4 人     │  │ 4 人   │ │
│   └─────┬────┘  └─────┬────┘  └─────┬────┘  └───┬────┘ │
│         │              │             │           │      │
│   ┌─────┴────┐  ┌──────┴──────┐  ┌──┴──────┐  ┌┴─────┐ │
│   │  研发工坊  │  │  情报系统   │  │ 蜂群引擎 │  │自学习 │ │
│   │  5 人     │  │  4 人      │  │ 7 角色  │  │循环   │ │
│   └──────────┘  └────────────┘  └─────────┘  └───────┘ │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  知识库: 266 SKILL.md  │  治理: L0-L3  │  预算: ¥2,440/m │
└─────────────────────────────────────────────────────────┘
```

### 领域划分

| 领域 | 路径 | 模块数 | 职责 |
|:---|:---|:---:|:---|
| 元决策 | `skills/meta/` | 35 | 战略、蜂群、治理、公司架构、自学习 |
| 内容 | `skills/content/` | 22 | 小红书、视频、SEO、营销文案 |
| 商业 | `skills/business/` | 76 | PM、BP、PRD、定价、项目管理 |
| 研发 | `skills/engineering/` | 23 | 编码、调试、架构、代码审查 |
| 增长 | `skills/growth/` | 11 | 闲鱼、营销、渠道、发布 |
| 情报 | `skills/intelligence/` | 10 | 趋势、OSINT、监控 |

> **molin_owner 三层体系**: CEO (27 skills) / 子公司专用 (238 skills) / 共享 (1 skill) — 覆盖 19/22 家墨系子公司

---

## 快速开始

### 环境要求

| 依赖 | 版本 | 必需 |
|:---|:---|:---:|
| Python | ≥ 3.10 | ✅ |
| Git | 任意 | ✅ |
| Hermes Agent | 最新 | ✅ |
| FFmpeg | 任意 | 可选 (视频) |

### 安装

```bash
# 克隆仓库
git clone https://github.com/moye-tech/-Hermes-OS.git
cd -Hermes-OS

# 一键部署 (创建 venv、安装依赖、初始化配置)
bash setup.sh

# 加载 CLI
source ~/.bashrc

# 验证
molin health
```

### 配置

```bash
# 编辑环境变量
vim ~/.molin/.env

# 填入各平台 API Keys
# 参考 .env.example 中的完整模板
```

---

## CLI 参考

### 命令一览

| 命令 | 说明 |
|:---|:---|
| `molin ceo strategy` | 生成 CEO 战略决策 |
| `molin ceo review` | 审查周度业绩 |
| `molin content xhs <主题>` | 生成小红书内容 |
| `molin content video <主题>` | 生成视频脚本 (FFmpeg) |
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

### Makefile

```bash
make install    # 安装依赖
make test       # 运行测试
make serve      # 启动仪表盘
make health     # 健康检查
make backup     # 备份 skills 和配置
make clean      # 清理构建产物
```

---

## 配置说明

| 文件 | 说明 |
|:---|:---|
| `config/company.yaml` | 公司结构 (22 墨系子公司)、预算 ¥2,440/月、变现矩阵 |
| `config/governance.yaml` | L0-L3 四级审批规则、审计日志、安全策略 |
| `config/channels.yaml` | 7 平台发布配置 (日限额、最佳发布时间、内容类型) |
| `.env.example` → `~/.molin/.env` | API Keys、Hermes 连接配置、告警等环境变量 |

### 治理级别

| 级别 | 预算上限 | 审批方式 |
|:---:|:---:|:---|
| L0 | ¥0 | 自动执行 |
| L1 | ≤ ¥10 | AI 自审 |
| L2 | ≤ ¥100 | 人工确认 |
| L3 | ≤ ¥1,000 | 董事会审批 |

### 定时任务

| ID | 调度 | 说明 |
|:---|:---|:---|
| `heartbeat_daily` | `0 9 * * *` | 每日心跳：闲鱼状态 + 情报简报 |
| `strategy_weekly` | `0 10 * * 1` | 每周一战略审查 |
| `trends_monitor` | `0 */6 * * *` | 每 6 小时趋势扫描 |

---

## 项目结构

```
-Hermes-OS/
├── README.md
├── LICENSE
├── setup.sh                     # 一键部署脚本
├── Makefile                     # 常用命令入口
├── setup.py                     # pip install -e . 安装配置
├── requirements.txt             # Python 依赖
├── .env.example                 # 环境变量模板
├── .gitignore
│
├── config/                      # YAML 配置文件
│   ├── company.yaml             #   公司架构、预算、变现
│   ├── governance.yaml          #   审批规则、审计、安全
│   └── channels.yaml            #   发布渠道配置
│
├── molin/                       # Python 源码
│   ├── __init__.py              #   包定义 (v4.0.0)
│   ├── cli.py                   #   CLI 入口 (16 个子命令)
│   ├── dashboard.py             #   Web 仪表盘 (Flask)
│   ├── core/                    #   核心层
│   │   ├── engine.py            #     调度中枢 + 健康检查
│   │   ├── governance.py        #     L0-L3 审批 + 审计
│   │   └── scheduler.py         #     定时任务管理
│   ├── agents/                  #   智能体层
│   │   ├── ceo.py               #     CEO 战略 + OKR
│   │   ├── swarm.py             #     蜂群编排 (7 角色)
│   │   └── learner.py           #     自学习循环
│   ├── content/                 #   内容层
│   │   ├── xiaohongshu.py       #     小红书内容引擎
│   │   ├── video.py             #     FFmpeg 视频管线
│   │   └── seo.py               #     SEO 优化引擎
│   ├── publish/                 #   发布层
│   │   ├── social_push.py       #     7 平台统一发布
│   │   └── xianyu.py            #     闲鱼店铺自动化
│   ├── intelligence/            #   情报层
│   │   └── trends.py            #     趋势 + OSINT + 世界监控
│   └── business/                #   商业层
│       ├── bp.py                #     商业计划书生成
│       └── prd.py               #     PRD 文档生成
│
├── skills/                      # Hermes SKILL.md 知识库 (266 个)
│   ├── meta/           (35)     #   决策层
│   ├── content/        (22)     #   内容层
│   ├── business/       (76)     #   商业层
│   ├── engineering/    (23)     #   工程层
│   ├── growth/         (11)     #   增长层
│   ├── intelligence/   (10)     #   情报层
│   ├── apple/                   #   Apple 生态
│   ├── autonomous-ai-agents/    #   自主AI Agent
│   ├── data-science/            #   数据科学
│   ├── devops/                  #   DevOps
│   ├── diagramming/             #   图表绘制
│   ├── domain/                  #   独立域名
│   ├── email/                   #   邮件
│   ├── gaming/                  #   游戏
│   ├── github/                  #   GitHub
│   ├── mcp/                     #   MCP 协议
│   ├── media/                   #   媒体
│   ├── mlops/                   #   MLOps
│   ├── social-media/            #   社交媒体
│   └── 更多 30+ 领域            #   54 领域全覆盖
│
├── tests/                       # 测试套件
│   └── test_core.py             #   核心模块测试 (21 用例)
│
├── docs/                        # 文档与案例
├── tools/                       # 运维脚本
└── cron/                        # cron 任务脚本
```

---

## 测试

```bash
# 运行全部测试
pytest tests/ -v

# 带覆盖率报告
pytest tests/ -v --cov=molin --cov-report=term

# 或使用 Makefile
make test
```

---

## 安全

- **仓库为私有项目** — 仅授权账号可访问
- **凭据隔离** — API Keys 存储在 `~/.molin/.env`，已加入 `.gitignore`
- **令牌轮换** — 建议每 30 天轮换一次访问令牌
- **审计追踪** — 所有决策记录为 JSONL 审计日志

---

## 许可证

本项目基于 [MIT License](LICENSE) 开源。

---

<p align="center">
  <sub>Built by <a href="https://github.com/moye-tech">moye-tech</a> · <a href="mailto:fengye940708@gmail.com">fengye940708@gmail.com</a></sub>
</p>
