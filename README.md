<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-00b894?style=flat-square&logo=python" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-MIT-00b894?style=flat-square" alt="License MIT">
  <img src="https://img.shields.io/badge/brain-Hermes_Agent-8e44ad?style=flat-square" alt="Hermes Agent">
  <img src="https://img.shields.io/badge/skills-559-success?style=flat-square" alt="500+ Skills">
  <img src="https://img.shields.io/badge/cron_jobs-21-blue?style=flat-square" alt="21 Cron Jobs">
  <img src="https://img.shields.io/badge/lines-44K_Python-ff6b6b?style=flat-square" alt="44K Lines">
  <img src="https://img.shields.io/badge/revenue-¥52K/month-ff6b6b?style=flat-square" alt="Revenue">
  <img src="https://img.shields.io/badge/version-v5.0-blueviolet?style=flat-square" alt="v5.0">
</p>

# 墨麟 OS · Molin-OS

一个人，一台 MacBook，一个 AI 集团。
One person, one MacBook, one AI conglomerate.

---

## 架构总览 / Architecture

```
                    ┌──────────────────────────────────────┐
                    │           创 始 人 / Founder          │
                    │      (飞书 Feishu · CLI · API)        │
                    └──────────────┬───────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────┐
                    │      Hermes Agent（大脑 / Brain）      │
                    │      DARE v3.0 推理框架               │
                    │      决策 · 路由 · 编排                │
                    └──────────────┬───────────────────────┘
                                   │  python -m molib
                    ┌──────────────▼───────────────────────┐
                    │         molib（执行层 / Execution）     │
                    │      447 模块 · 50+ CLI 命令           │
                    └──────┬───────┬───────┬───────┬──────┘
                           │       │       │       │
              ┌────────────┼───────┼───────┼───────┼────────────┐
              │            │       │       │       │            │
         VP 营销(5)   VP 运营(4) VP 技术(4) VP 财务(1) VP 战略(3)
              │            │       │       │       │            │
              └────────────┼───────┼───────┼───────┼────────────┘
                           │       │       │       │
                    共享服务(3)     │  专项 Workers(3)
                                   │
                    ┌──────────────▼───────────────────────┐
                    │           结 果 / Results             │
                    │   内容 · 设计 · 客服 · 订单 · 报表     │
                    └──────────────────────────────────────┘
```

---

## 快速开始 / Quick Start

三行命令完成部署。

```bash
git clone git@github.com:moye-tech/Molin-OS.git
cd Molin-OS
bash setup.sh
```

setup.sh 会自动完成：环境检测 → Python 虚拟环境 → 依赖安装 → 配置初始化 → CLI 安装 → 健康验证。

首次运行后编辑 `~/.molin/.env` 填入 API Keys：

```bash
DEEPSEEK_API_KEY=sk-xxx
DASHSCOPE_API_KEY=sk-xxx
OPENROUTER_API_KEY=sk-xxx
```

验证安装：

```bash
source ~/.bashrc
molin health
molin '帮我写一篇小红书文案'
```

---

## 核心特性 / Core Features

- AI 原生操作系统 —— 不是工具集，是完整的 AI 一人公司运营系统
- 20 家垂直子公司 —— 覆盖营销、运营、技术、财务、战略五大 VP + 共享服务
- 强制委托协议 —— CEO（Hermes）只做决策和路由，产出由子公司执行，杜绝 AI 包办
- DARE v3.0 推理框架 —— Decompose·Analyze·Route·Elevate，四步完成从理解到超预期交付
- 每日自动化飞轮 —— 08:00 情报采集 → 09:20 内容工厂 → 10:45 增长引擎，全自动接力
- 5 级治理体系 —— L0 自动执行到 L4 绝对禁止，预算上限 + 审批门禁 + 审计追踪
- 统一 CLI 入口 —— `python -m molib <command>` 调度所有子系统，50+ 命令
- 多通道接入 —— 飞书对话、CLI 终端、REST API 三种交互方式
- 559 项技能 —— 从 SEO 优化到量化交易，从像素艺术到红队安全测试
- 单机运行 —— M2 MacBook 8GB 即可驱动整个集团
- 月收入目标 ¥52,000 —— 真实运营中的商业系统

---

## 子公司体系 / Subsidiary System

20 家子公司分布于 5 位 VP 麾下，加上 3 家共享服务。

### VP 营销 / Marketing（5 家）

| 子公司 | 代号 | 核心能力 |
|:-------|:-----|:---------|
| 墨笔文创 | Content Writer | 品牌文案、小红书、公众号、SEO 内容 |
| 墨韵 IP | IP Manager | IP 孵化、版权管理、品牌衍生 |
| 墨图设计 | Designer | FLUX.2 生图、Open Design 149 设计系统、封面/UI |
| 墨播短视频 | Short Video | 短视频脚本 + 生成、FFmpeg 视频引擎 |
| 墨声配音 | Voice Actor | AI 语音合成、播客制作、TTS |

### VP 运营 / Operations（4 家）

| 子公司 | 代号 | 核心能力 |
|:-------|:-----|:---------|
| 墨域私域 | CRM | 用户分层、社群运营、RFM 模型 |
| 墨声客服 | Customer Service | 自动化客服、闲鱼消息检测回复 |
| 墨链电商 | E-commerce | 订单管理、交易链路、多平台 |
| 墨学教育 | Education | 课程设计、AI 导师、学习路径 |

### VP 技术 / Technology（4 家）

| 子公司 | 代号 | 核心能力 |
|:-------|:-----|:---------|
| 墨码开发 | Developer | 软件开发、架构设计、代码审查 |
| 墨维运维 | Ops | 部署、监控、SRE、灾备 |
| 墨安安全 | Security | 代码审计、漏洞扫描、红队测试 |
| 墨梦 AutoDream | AutoDream | AI 自动化实验、记忆蒸馏、自学习 |

### VP 财务 / Finance（1 家）

| 子公司 | 代号 | 核心能力 |
|:-------|:-----|:---------|
| 墨算财务 | Finance | 记账、预算、成本控制、财务报表 |

### VP 战略 / Strategy（3 家）

| 子公司 | 代号 | 核心能力 |
|:-------|:-----|:---------|
| 墨商 BD | Business Development | 商务拓展、合作洽谈、销售策略 |
| 墨海出海 | Global Marketing | 多语言本地化、全球化运营 |
| 墨研竞情 | Research | 竞争分析、趋势扫描、实时情报 |

### 共享服务 / Shared Services（3 家）

| 子公司 | 代号 | 核心能力 |
|:-------|:-----|:---------|
| 墨律法务 | Legal | 合同审查、合规评估、风险评估 |
| 墨脑知识 | Knowledge | 知识图谱、ChromaDB 向量记忆、RAG |
| 墨测数据 | Data Analyst | BI 仪表盘、数据分析、质量检测 |

### 专项 Workers / Specialized（3 家）

| Worker | 领域 |
|:-------|:-----|
| 墨投交易 | 量化交易策略、信号生成、回测 |
| Scrapling | 网页抓取、数据采集 |
| Router9 | 网络流量、多路路由 |

---

## 飞轮管线 / Cron Flywheel Pipeline

每日全自动内容管线，通过 `relay/` 目录三棒接力，断链自动告警。

```
┌─────────────────────────────────────────────────────────────────────┐
│                        每 日 自 动 化 飞 轮                            │
│                                                                     │
│  08:00          09:20          10:45                                │
│  ┌──────┐      ┌──────┐      ┌──────┐                               │
│  │情报银行│ ──→ │内容工厂│ ──→ │增长引擎│                              │
│  │ Intel │      │Content│      │Growth │                               │
│  └──────┘      └──────┘      └──────┘                               │
│  扫描+筛选      生成+SEO       优化+分发                               │
│     │              │              │                                  │
│     └── relay/intelligence.json ──┘                                  │
│                 └── relay/content.json ──┘                           │
└─────────────────────────────────────────────────────────────────────┘
```

完整 21 项 Cron 时间表：

| 时间 | 任务 | 说明 |
|:-----|:-----|:-----|
| 03:00 | 系统备份 | 全量数据备份 |
| 07:00 | 轻量同步 | 记忆索引同步 |
| 07:30 | API 预警 | API 余额 + 可用性检查 |
| 08:00 | 情报银行 ★ | 飞轮第一棒：情报扫描采集 |
| 09:00 | CEO 简报 | 每日摘要推送 |
| 09:20 | 内容工厂 ★ | 飞轮第二棒：内容生成 + SEO |
| 09:28 | 上班提醒 | 日程同步 |
| 09:45-17:45 | 闲鱼检测 | 每 30 分钟检测新消息 |
| 10:00 | 治理合规 | 预算 + 安全审计 |
| 10:45 | 增长引擎 ★ | 飞轮第三棒：优化 + 分发 |
| 11:00 | 内容回收 | 旧内容清理归档 |
| 12:00 | 系统健康 | 全系统健康检查 |
| 14:00 | 竞品监控 | 竞品动态扫描 |
| 18:28 | CEO 下班汇总 | 当日产出总结 |
| 周末 | 闲鱼精简版 | 每 2 小时检测 |
| 周末 | 记忆蒸馏 | 周度知识压缩 |
| 周末 | 自学习循环 | 技能反思优化 |
| 周末 | 技能审计 | 技能库健康评估 |

★ 标记为核心飞轮三棒，任意一棒失败触发级联告警。

---

## CLI 命令参考 / CLI Command Reference

所有命令通过统一入口调用：`python -m molib <command> [args]`

### 系统管理 / System

```
health         系统健康检查（9/9 组件状态）
help           列出所有可用命令
validate       验证配置文件完整性
sync           同步子公司状态与技能
```

### 内容创作 / Content

```
content write --topic "主题" --platform xhs    生成平台内容
content publish --platform xhs --draft-id xxx  发布内容草稿
design image --prompt "描述" --style 写实       生成图片/封面
design web --prompt "描述" --action landing_page 生成网页/仪表盘
```

### 视频制作 / Video

```
video script --topic "主题" --duration 60s    生成短视频脚本
```

### 商业运营 / Commerce

```
crm segment --by 活跃度                     用户分层
crm push --segment 高活跃 --content "消息"   精准推送
xianyu reply --msg-id xxx --content "回复"   闲鱼自动回复
order list --status pending                 订单列表
order status --order-id xxx                 订单状态
```

### 财务管理 / Finance

```
finance record --type expense --amount 100 --note "费用说明"   记账
finance report                                               财务报表
cost                                                          成本分析
```

### 情报研究 / Intelligence

```
intel trending                       趋势扫描
intel save --topic "主题" --summary "摘要"   情报保存
```

### 量化交易 / Trading

```
trading signal --symbol BTC/USDT               交易信号
trading analyze --market-type crypto --symbol   市场分析
trading research --ticker BTC                  策略研究
```

### 数据分析 / Data

```
data analyze --file xxx.csv    数据分析
```

### 元操作 / Meta

```
handoff route --task "任务描述"     自动路由到最匹配的子公司
handoff list                       列出所有可路由 Worker
plan create --title "..."          创建任务计划
plan decompose --plan-id xxx       智能分解为子任务
memory                             记忆查询
manifest                           系统清单
query "问题"                       知识库查询
ghost-os health                    幽灵系统自检
self-learning reflect              触发自学习反思
karpathy scan --topic "主题"       Karpathy 式情报扫描
moneymaker assess --idea "..."     变现评估
```

---

## 治理模型 / Governance Model

5 级审批体系，基于预算上限 + 风险等级的量化治理。

| 级别 | 名称 | 预算上限 | 规则 |
|:-----|:-----|:---------|:-----|
| L0 | 自动执行 | ¥0 | 零成本操作，AI 自动完成无需审批（生成草稿、查询数据、健康检查） |
| L1 | AI 自审 | ≤ ¥10 | AI 内部检查后自动执行（发布笔记、更新 SEO、调整定价） |
| L2 | 人工确认 | ≤ ¥100 | 需创始人确认后执行（对外提案、大额推广、客户交付物） |
| L3 | 董事会审批 | ≤ ¥1,000 | 重大决策需全面评估（新产品线、战略调整、超预算支出） |
| L4 | 绝对禁止 | — | 涉及真实现金/转账/支付/改价，绝不触碰 |

核心原则：
- 月度运营预算 ¥1,360，80% 时触发预警
- 审计日志 90 天保留，JSONL 格式
- Token 30 天轮换，禁止提交凭证
- 预算和审批级别以 `config/governance.yaml` 为单一真相源

---

## 项目结构 / Project Structure

```
Molin-OS/
├── setup.sh                    # 一键部署脚本
├── requirements.txt            # Python 依赖
├── Makefile                    # 构建命令
├── LICENSE                     # MIT License
├── SOUL.md                     # CEO 认知框架（灵魂文件）
├── AGENTS.md                   # 公司上下文（系统提示注入）
├── ENVIRONMENT.md              # 环境清单
│
├── config/
│   ├── company.toml            # 20 家子公司映射（唯一配置源）
│   ├── governance.yaml         # 治理规则（L0-L4 + 预算）
│   ├── subsidiaries.toml       # 子公司详细配置
│   ├── models.toml             # AI 模型路由
│   ├── routing.toml            # Handoff 路由规则
│   ├── channels.yaml           # 多通道配置
│   ├── memory.toml             # 记忆系统配置
│   ├── memory_acl.toml         # 记忆访问控制
│   └── hermes-agent/           # Hermes Agent 集成配置
│       ├── config.yaml
│       ├── gateways/           # 飞书网关
│       ├── skills/             # 技能配置
│       ├── tools/              # 工具配置
│       └── workflows/          # 审批工作流
│
├── molib/                      # Python 执行包（447 模块 · 44K 行）
│   ├── __init__.py             # 版本号 v5.0
│   ├── __main__.py             # CLI 统一入口
│   ├── cli.py                  # 命令行解析
│   ├── ceo/                    # CEO 引擎（推理·决策·编排）
│   ├── agencies/               # 执行层
│   │   ├── workers/            # 20+ 子公司 Worker
│   │   ├── handoff/            # 自动路由系统
│   │   ├── planning/           # 任务规划分解
│   │   ├── bd/                 # 商务拓展
│   │   ├── crm/                # 客户关系
│   │   ├── cs/                 # 客服系统
│   │   ├── data/               # 数据分析
│   │   ├── dev/                # 开发工具
│   │   ├── devops/             # 运维部署
│   │   └── ads/                # 广告投放
│   ├── infra/                  # 基础设施
│   │   ├── gateway/            # 飞书网关 + 消息管线
│   │   └── data_brain/         # 数据大脑
│   ├── skills/                 # 559 项技能库
│   ├── shared/                 # 共享工具层
│   ├── management/             # VP 管理层
│   └── xianyu/                 # 闲鱼集成
│
├── skills/                     # 外部技能市场
├── molin-skills/               # 墨麟定制技能包
├── sop/                        # 标准操作流程引擎
├── scripts/                    # 辅助脚本
│   ├── setup_env.sh
│   ├── deploy.sh
│   └── backup.sh
├── docs/                       # 文档
├── backup/                     # 备份区（含闲鱼 Bot）
└── fork_repos/                 # Fork 的外部项目
```

---

## 技术栈 / Tech Stack

| 层级 | 技术 |
|:-----|:-----|
| AI 大脑 | Hermes Agent（Nous Research） |
| 推理框架 | DARE v3.0（Decompose·Analyze·Route·Elevate） |
| 执行引擎 | Python 3.11+ · Click · Rich |
| 配置管理 | TOML · YAML · dotenv |
| 记忆系统 | ChromaDB（向量）· SQLite（结构化）· claude-mem（长期） |
| 通信通道 | 飞书 Bot · CLI · FastAPI（:5050） |
| 视觉设计 | FLUX.2 · Open Design · FFmpeg |
| 数据存储 | JSONL 审计日志 · 内存向量库 · 文件系统 |
| 自学习 | Self-Learning Loop · AutoDream · Memory Distillation |
| 版本控制 | Git · GitHub |

---

## 环境要求 / Requirements

| 项目 | 要求 |
|:-----|:-----|
| 操作系统 | macOS 推荐（M2 8GB 已测试通过），Linux 兼容 |
| Python | 3.11+ |
| AI 引擎 | Hermes Agent（Nous Research） |
| API Keys | DeepSeek · DashScope · OpenRouter（至少一个） |
| 可选 | FFmpeg（视频功能）· Docker（容器化部署） |
| 最低硬件 | M2 8GB / 同等算力，约 2GB 磁盘 |

---

## 开源协议 / License

MIT License © 2026 Moye Tech

本项目基于 [Hermes Agent](https://github.com/nousresearch/hermes-agent)（Nous Research）构建。技能库中部分技能来自开源社区贡献，各自保留原许可。

---

<p align="center">
  <strong>墨麟 OS — 一个人就是一个集团</strong><br>
  <sub>Built with Hermes Agent · 447 modules · 559 skills · 20 subsidiaries · 21 cron jobs</sub>
</p>
