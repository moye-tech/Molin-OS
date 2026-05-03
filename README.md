# 🐉 墨麟 Hermes OS

> **AI一人公司操作系统** — 让个体拥有企业的战斗力

[![Version](https://img.shields.io/badge/version-2.0.0-blue)](https://github.com/moye-tech/-Hermes-OS)
[![Python](https://img.shields.io/badge/python-3.10+-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Proprietary-red)](LICENSE)
[![Status](https://img.shields.io/badge/status-active-brightgreen)]()

---

## 📖 概述

**墨麟 (Molin)** 是一个基于 Hermes Agent 构建的 AI 原生操作系统，旨在让一个人拥有整个企业的战斗力。

它将一家公司需要的所有能力——**战略决策、内容创作、多平台发布、商业变现、情报监控、持续学习**——打包成一个可部署的 Python 系统。

```
你 + 墨麟 Hermes OS = 一个全自动运转的一人公司
```

### 核心理念

| 传统一人公司 | 墨麟 AI一人公司 |
|:---|:---|
| 一个人做所有事 | AI agent 做所有事 |
| 靠意志力坚持 | 靠系统自动运行 |
| 月产 10 条内容 | 日产 10 条内容 |
| 1 个收入来源 | 6+ 变现矩阵 |
| 手动发布 | 一键 7 平台发布 |

---

## 🏗 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    🐉 墨麟 Hermes OS                      │
├─────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  🧠 CEO │  │  📱 内容  │  │  📊 商业 │  │  🚀 增长 │ │
│  │  办公室  │  │   工厂    │  │   大脑    │  │   引擎    │ │
│  └────┬────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
│       │            │              │              │       │
│  ┌────┴────┐  ┌────┴─────┐  ┌────┴─────┐  ┌────┴─────┐ │
│  │ 🛠 研发  │  │  🔭 情报  │  │  🐝 蜂群  │  │  🧬 自学习 │ │
│  │   工坊   │  │   系统    │  │   引擎    │  │   循环    │ │
│  └─────────┘  └──────────┘  └──────────┘  └──────────┘ │
├─────────────────────────────────────────────────────────┤
│  💾 知识库: 235+ SKILL.md │ ⚖️ 治理: 4级审批 │ 📡 7平台 │
└─────────────────────────────────────────────────────────┘
```

### 6 大领域 × 22 智能角色

| 领域 | 目录 | 角色数 | 核心职责 |
|:---|:---|:---:|:---|
| **元决策层** | `meta/` | 35 | 战略、蜂群编排、治理、公司结构、自学习 |
| **内容工厂** | `content/` | 22 | 小红书、视频、SEO、营销文案 |
| **商业大脑** | `business/` | 76 | PM、BP、PRD、定价、项目管理 |
| **研发工坊** | `engineering/` | 23 | 编码、调试、架构、代码审查 |
| **增长引擎** | `growth/` | 11 | 闲鱼、营销、渠道、发布 |
| **情报系统** | `intelligence/` | 10 | 趋势、OSINT、监控 |

---

## 🚀 快速开始

### 前置要求

- Python 3.10+
- Git
- FFmpeg (可选，用于视频生成)
- Hermes Agent (核心AI引擎)

### 一键部署

```bash
# 1. 克隆仓库
git clone https://github.com/moye-tech/-Hermes-OS.git
cd -Hermes-OS

# 2. 一键部署
bash setup.sh

# 3. 加载环境
source ~/.bashrc

# 4. 验证
molin health
```

### 配置 API Keys

```bash
# 编辑环境变量
vim ~/.molin/.env

# 填入各平台API Keys (小红书、知乎、微博等)
```

---

## 📋 CLI 命令

```bash
# ── CEO 战略层 ──
molin ceo strategy          # 生成战略决策
molin ceo review            # 审查上周业绩

# ── 内容工厂 ──
molin content xhs AI工具     # 生成小红书内容
molin content video 一人公司  # 生成视频脚本
molin content seo AI创业     # 生成SEO内容

# ── 发布引擎 ──
molin publish xiaohongshu   # 发布到小红书
molin publish zhihu          # 发布到知乎

# ── 闲置变现 ──
molin xianyu list           # 查看闲鱼商品
molin xianyu publish        # 发布闲鱼商品

# ── 商业引擎 ──
molin business bp 我的项目   # 生成商业计划书
molin business prd 我的产品  # 生成PRD

# ── 情报系统 ──
molin intel trends          # 趋势洞察
molin intel monitor         # 运行监控

# ── 蜂群与自学习 ──
molin swarm run 生成10篇内容  # 启动蜂群
molin learn                  # 自学习循环

# ── 服务与调度 ──
molin serve                 # 启动Web仪表盘 (端口8080)
molin schedule list         # 查看定时任务
molin health                # 系统健康检查
```

---

## 📊 变现矩阵

### 闲鱼服务商店

| # | 商品 | 价格 | 交付周期 |
|:---:|:---|:---:|:---:|
| 1 | AI商业计划书定制 | ¥800 | 3-5天 |
| 2 | 简历优化升级 | ¥100 | 24小时 |
| 3 | PRD产品需求文档 | ¥500 | 2-3天 |
| 4 | PPT美化设计 | ¥200 | 1-2天 |
| 5 | AI绘画定制 | ¥100 | 2小时 |
| 6 | 小红书文案代写 | ¥30 | 4小时 |

### Freelancer 平台

- 猪八戒 (提案服务)
- 程序员客栈 (技术外包)
- Upwork (海外市场)

**目标月收入: ¥5,000**

---

## 🔄 内容管线

```
输入主题 → [小红书引擎] → 生成内容
              ↓
         [FFmpeg视频] → 制作视频 (无GPU)
              ↓
         [Social Push] → 7平台一键发布
              ↓
         [数据分析] → 效果追踪 → 优化迭代
```

---

## ⏰ 定时任务 (心跳系统)

| 任务 | 调度 | 描述 |
|:---|:---|:---|
| 🫀 每日心跳 | 每天 09:00 | 闲鱼状态 + 情报简报 |
| 📊 周度战略 | 每周一 10:00 | OKR审查 + 方向调整 |
| 🔭 趋势监控 | 每6小时 | GitHub/知乎/微博热搜扫描 |

---

## 🧬 自学习循环

```
评估 → 吸收 → 集成 → 淘汰
  │       │       │       │
  │  扫描GitHub  │  更新workflow  │  归档过时技能
  │  发现新工具  │  吸收知识    │  合并重复能力
  │              │              │
  └──────────────┴──────────────┘
        持续自我进化
```

---

## ⚖️ 治理系统

基于 Paperclip (62K★) 设计模式:

| 级别 | 名称 | 预算 | 说明 |
|:---:|:---|:---:|:---|
| L0 | 自动执行 | ¥0 | AI直接执行 |
| L1 | AI自审 | ≤¥10 | AI检查后执行 |
| L2 | 人工确认 | ≤¥100 | 需确认 |
| L3 | 董事会审批 | ≤¥1,000 | 全面评估 |

---

## 🗂 项目结构

```
墨麟Hermes-OS/
├── README.md                    # 项目说明
├── setup.sh                     # 一键部署脚本
├── Makefile                     # 常用命令
├── requirements.txt             # Python依赖
├── setup.py                     # 包安装配置
├── .env.example                 # 环境变量模板
├── .gitignore                   # Git过滤规则
├── config/                      # 配置文件
│   ├── company.yaml             # 公司结构配置
│   ├── governance.yaml          # 治理规则
│   └── channels.yaml            # 发布渠道配置
├── molin/                       # Python核心代码
│   ├── __init__.py              # 包定义 (v2.0.0)
│   ├── cli.py                   # CLI入口
│   ├── dashboard.py             # Web仪表盘
│   ├── core/                    # 核心引擎
│   │   ├── engine.py            # 调度中枢
│   │   ├── governance.py        # 4级审批
│   │   └── scheduler.py         # 定时任务
│   ├── agents/                  # 智能体
│   │   ├── ceo.py               # CEO战略
│   │   ├── swarm.py             # 蜂群编排
│   │   └── learner.py           # 自学习
│   ├── content/                 # 内容工厂
│   │   ├── xiaohongshu.py       # 小红书引擎
│   │   ├── video.py             # FFmpeg视频
│   │   └── seo.py               # SEO引擎
│   ├── publish/                 # 发布引擎
│   │   ├── social_push.py       # 7平台发布
│   │   └── xianyu.py            # 闲鱼自动化
│   ├── intelligence/            # 情报系统
│   │   └── trends.py            # 趋势监控
│   └── business/                # 商业引擎
│       ├── bp.py                # 商业计划书
│       └── prd.py               # PRD生成
├── skills/                      # 235+ SKILL.md 知识库
│   ├── meta/                    # 决策层 (35)
│   ├── content/                 # 内容层 (22)
│   ├── business/                # 商业层 (76)
│   ├── engineering/             # 工程层 (23)
│   ├── growth/                  # 增长层 (11)
│   └── intelligence/            # 情报层 (10)
├── tools/                       # 运维脚本
├── tests/                       # 测试套件
├── docs/                        # 文档
└── cron/                        # 定时任务
```

---

## 🧪 测试

```bash
# 运行全部测试
make test

# 或直接
pytest tests/ -v --cov=molin
```

---

## 🔒 安全说明

- **本仓库为私有项目**，不对外公开
- API Keys 存储在 `~/.molin/.env`，不提交到 Git
- `.gitignore` 已过滤 `.env` 和敏感文件
- 定期轮换访问令牌 (建议30天)

---

## 📝 开源协议

**Proprietary (私有)** — 本软件为闭源私有项目，禁止未经授权的复制、分发或使用。

---

## 👤 作者

- **moye-tech** — [GitHub](https://github.com/moye-tech)
- 邮箱: fengye940708@gmail.com
- 项目: [moye-tech/-Hermes-OS](https://github.com/moye-tech/-Hermes-OS)

---

> 💡 *"最好的创业方式是做一个全自动运转的系统，而不仅仅是一份工作。"*
