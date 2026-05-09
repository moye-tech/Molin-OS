<!--
  Molin OS — README
  Version: 5.0.1
  Repository: https://github.com/moye-tech/Molin-OS
  Last updated: 2026-05-09
-->

# 墨麟OS — AI 一人公司操作系统

<p align="center">
  <strong>6 层架构 · 516 项技能 · 20 家子公司 · 22 个 Worker</strong><br>
  一个人就是一个集团
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12+-00b894?style=flat-square&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-00b894?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/skills-516%2B-success?style=flat-square" alt="Skills">
  <img src="https://img.shields.io/badge/workers-22-success?style=flat-square" alt="Workers">
  <img src="https://img.shields.io/badge/status-final-blueviolet?style=flat-square" alt="Status">
  <img src="https://img.shields.io/badge/absorbed-27%20projects-10b981?style=flat-square" alt="Absorbed">
  <img src="https://img.shields.io/badge/revenue-%C2%A552K%2Fmonth-ff6b6b?style=flat-square" alt="Revenue">
</p>

---

## 概述

**墨麟OS (Molin OS)** 是一个人用一台服务器即可运营的 AI 一人公司操作系统。系统包含 20 个垂直子公司（墨笔文创、墨域私域、墨码开发等），每个子公司有专属 Worker 执行文件和 Hermes 技能库。Hermes Agent 作为 CEO 大脑，通过统一 CLI 入口调动所有子系统。

核心设计原则：
- **零空转** — 有任务才消耗 token，无任务时系统静止
- **治理驱动** — 5 级审批体系（L0 自动 → L4 绝对禁止），AI 不碰现金
- **数据持久化** — 所有成本/状态/记忆通过 SQLite 持久化，重启不丢失

- **仓库**: [github.com/moye-tech/Molin-OS](https://github.com/moye-tech/Molin-OS)
- **许可**: MIT License © 2026 Moye Tech

## 目录

- [架构](#架构)
- [治理体系](#治理体系)
- [核心指标](#核心指标)
- [快速部署](#快速部署)
- [CLI 入口](#cli-入口)
- [子系统一览](#子系统一览)
- [系统模块](#系统模块)
- [基础设施](#基础设施)
- [卡片系统](#卡片系统)
- [已吸收项目](#已吸收项目)
- [定时作业](#定时作业)

## 架构

```
创始人（你）
    │
┌── L0 认知中枢 ──────────────────────────────────┐
│  SOUL.md(人格) · AGENTS.md(手册)                │
│  governance.yaml(唯一治理源) · IntentProcessor   │
└──────────────────┬──────────────────────────────┘
                   │  决策流
    ┌──────────────┼─────────────────────┐
    │ L1-L2 执行层 (20 家子公司 + 专项)    │
    │ ┌─ 营销(5) ──┐ ┌─ 运营(4) ────┐  │
    │ │ 墨笔·墨韵· │ │ 墨域·墨声·     │  │
    │ │ 墨图·墨播· │ │ 墨链·墨学       │  │
    │ │ 墨声配音   │ │                │  │
    │ ├─ 技术(4) ─┤ ├─ 财务(1) ────┤  │
    │ │ 墨码·墨维· │ │ 墨算            │  │
    │ │ 墨安·墨梦  │ │                │  │
    │ ├─ 战略(3) ─┤ ├─ 共同(3) ────┤  │
    │ │ 墨商·墨海· │ │ 墨律·墨脑·墨测  │  │
    │ │ 墨研       │ │                │  │
    │ └────────────┘ └───────────────┘  │
    │ 营收目标: ¥52,000/月               │
    └────────────────┬────────────────────┘
                     │  服务
    ┌────────────────┼────────────────────┐
    │ L3-L5 基础设施                        │
    │ 6 模块卡片系统 · 3 探针 HealthProbe   │
    │ 5 层记忆 · EventBus(文件+内存降级)    │
    │ Hermes Toolchain · 516 SKILL.md     │
    │ 飞书/闲鱼/小红书集成 · Config 体系    │
    └──────────────────────────────────────┘
```

## 治理体系

5 级审批体系（定义见 `config/governance.yaml`，单一真相源）：

| 级别 | 类型 | 预算上限 | 描述 |
|:----:|:----:|:--------:|:-----|
| **L0** | auto | ¥0 | 自动执行 · 内容生成/数据采集/例行报告 |
| **L1** | notify | ¥10 | 完成后通知 · 中风险操作 |
| **L2** | approve | ¥100 | 需人工确认 · 报价>¥100/对外发布/修改配置 |
| **L3** | board_approve | ¥1,000 | 董事会审批 · 重大决策 |
| **L4** | **forbidden** | **∞** | **绝对禁止 · 现金/转账/支付** |

SOUL.md 和 AGENTS.md 均引用 governance.yaml，确保治理定义无歧义。

## 核心指标

| 指标 | 数值 |
|:----|:----:|
| Python 代码 | 177 个模块（40,948 行） |
| 技能定义 | 516 个 SKILL.md |
| Worker 文件 | 22 个（`molib/agencies/workers/`） |
| 子公司 | 20 家（5 营销 + 4 运营 + 4 技术 + 1 财务 + 3 战略 + 3 共同） |
| 已吸收开源项目 | 27 个（~520K⭐） |
| Handoff 自动路由 | 16 家子公司已注册 |
| CLI 命令 | 25+ 统一入口 |
| 自动化脚本 | 25 个（bots/） |
| 商业化方案 | 9 个（business/） |
| 系统文档 | 28 篇（docs/） |
| 定时作业 | 8 个（默认暂停，零空转） |
| 卡片系统 | 6 模块子包（cards/） |
| 健康探针 | 3 外部依赖（HealthProbe） |
| SQLite 数据库 | 3 个（cost/state/tasks） |
| 月营收目标 | ¥52,000 |
| 月预算 | ¥1,360 |
| ROI | 38.2x |

## 快速部署

```bash
git clone https://github.com/moye-tech/Molin-OS.git
cd Molin-OS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
cp .env.example .env
# 编辑 .env 填入 API Keys
python -m molib health
```

一键部署：

```bash
bash setup.sh
```

## CLI 入口

```bash
python -m molib health                 # 系统健康检查（含 HealthProbe）
python -m molib help                    # 查看所有命令

python -m molib content write          # 墨笔文创 — 内容创作
python -m molib content publish        # 小红书发布
python -m molib design image           # 墨图设计 — 图片生成
python -m molib video script           # 墨播短视频 — 视频脚本
python -m molib tts generate           # 墨声配音 — 语音合成
python -m molib crm segment            # 墨域私域 — 用户分层
python -m molib xianyu reply           # 墨声客服 — 闲鱼回复
python -m molib order list             # 墨链电商 — 订单列表
python -m molib finance report         # 墨算财务 — 财务报表
python -m molib trading signal         # 墨投交易 — 交易信号
python -m molib intel trending         # 墨研竞情 — 趋势扫描
python -m molib data analyze           # 墨测数据 — 数据分析
python -m molib handoff route          # 自动路由到最佳 Worker
python -m molib handoff list           # 查看所有可用 Worker
python -m molib health probe           # 手动运行 HealthProbe
python -m molib plan create            # 创建目标分解
python -m molib plan decompose         # 自动分解大任务
```

## 子系统一览

### 营销 VP（5 家）

| 子系统 | Worker | 核心能力 | 关联技能 |
|:-------|:-------|:---------|:---------|
| **墨笔文创** | content_writer.py | 文字创作·文案·公众号·小红书 | copywriting, content-strategy |
| **墨韵 IP** | ip_manager.py | IP 衍生·商标·版权·品牌管理 | ai-taste-quality |
| **墨图设计** | designer.py | 封面·UI·视觉设计 | molin-design, pixel-art |
| **墨播短视频** | short_video.py | 短视频脚本+生成 | ffmpeg-video-engine |
| **墨声配音** | voice_actor.py | AI 语音·播客·有声书 | molin-audio-engine |

### 运营 VP（4 家）

| 子系统 | Worker | 核心能力 | 关联技能 |
|:-------|:-------|:---------|:---------|
| **墨域私域** | crm.py | CRM·用户分层·社群运营 | molin-crm |
| **墨声客服** | customer_service.py | 自动化客服·闲鱼消息 AI 回复 | xianyu-automation |
| **墨链电商** | ecommerce.py | 订单管理·交易 | molin-order |
| **墨学教育** | education.py | 课程设计·AI 辅导 | molin-education |

### 技术 VP（4 家）

| 子系统 | Worker | 核心能力 | 关联技能 |
|:-------|:-------|:---------|:---------|
| **墨码开发** | developer.py | 软件开发·代码编写·爬虫 | cli-anything |
| **墨维运维** | ops.py | 部署·DevOps·GUI 自动化 | ghost-os |
| **墨安安全** | security.py | 安全审计·漏洞扫描 | red-teaming |
| **墨梦 AutoDream** | auto_dream.py | AI 自动化实验·记忆蒸馏 | self-learning-loop |

### 财务 VP（1 家）

| 子系统 | Worker | 核心能力 |
|:-------|:-------|:---------|
| **墨算财务** | finance.py | 记账·预算·成本控制 |

### 战略 VP（3 家）

| 子系统 | Worker | 核心能力 | 关联技能 |
|:-------|:-------|:---------|:---------|
| **墨商 BD** | bd.py | 商务拓展·合作·投标 | molin-bd-scanner |
| **墨海出海** | global_marketing.py | 多语言·全球化·出海·繁体 | molin-global |
| **墨研竞情** | research.py | 竞争分析·趋势·情报 | world-monitor |

### 共同服务（3 家）

| 子系统 | Worker | 核心能力 | 关联技能 |
|:-------|:-------|:---------|:---------|
| **墨律法务** | legal.py | 合同·隐私·合规·NDA | molin-legal |
| **墨脑知识** | knowledge.py | 知识管理·RAG·记忆 | molin-memory |
| **墨测数据** | data_analyst.py | 数据分析·测试·BI | molin-vizro |

### 专项预置（3 个额外 Worker）

| Worker | 核心能力 |
|:-------|:---------|
| trading.py | 量化交易策略·信号·回测 |
| scrapling_worker.py | 网页抓取·数据采集 |
| router9.py | 网络流量·多路路由 |

## 系统模块

```
Molin-OS/
├── config/                       # 系统配置（单一真相源）
│   ├── governance.yaml           # 5 级审批规则（L0-L4）
│   ├── company.toml              # 子公司映射
│   ├── models.toml               # 模型路由（含 version+alias）
│   └── channels.yaml             # 消息渠道配置
├── molib/                        # 核心执行包（177 模块）
│   ├── cli.py                    # CLI 入口
│   ├── __main__.py               # Python 入口（v5.0.1）
│   ├── cost.py                   # 成本追踪（SQLite 持久化）
│   ├── ceo/                      # L0 CEO 引擎（17 模块）
│   │   ├── cards/                # 卡片系统子包（6 模块）
│   │   │   ├── builder.py        # CardBuilder 核心构建器
│   │   │   ├── templates.py      # 6 个卡片模板
│   │   │   ├── sender.py         # FeishuCardSender
│   │   │   ├── thinking.py       # ThinkingCardManager
│   │   │   └── utils.py          # 降级转换
│   │   ├── feishu_card.py        # 弃用（重定向到 cards/）
│   │   └── thinking_card.py      # 弃用（重定向到 cards/）
│   ├── agencies/                 # L1-L2 执行层
│   │   ├── handoff.py            # Handoff 自动路由
│   │   ├── handoff_register.py   # 16 家 Worker 注册
│   │   ├── planning.py           # 规划分解引擎
│   │   └── workers/              # 26 个 Worker 文件
│   ├── infra/                    # L4 基础设施
│   │   ├── self_healing.py       # 自愈引擎（默认禁用）
│   │   ├── health_probe.py       # HealthProbe（3 探针）
│   │   ├── event_bus.py          # 内存 Pub/Sub 事件总线
│   │   ├── credential_vault.py   # 凭证管理
│   │   └── deep_approval.py      # 深度审批
│   ├── shared/                   # L3 共享能力层
│   │   ├── event_bus.py          # 文件接力事件总线
│   │   ├── ai/                   # LLM 客户端·视觉·Browser Agent
│   │   ├── analysis/             # 分析·评价·预测引擎
│   │   ├── content/              # SEO·社交写作
│   │   ├── knowledge/            # RAG·SOP·知识图谱
│   │   ├── publish/              # 平台发布·翻译
│   │   └── storage/              # 向量数据库·缓存·文件
│   ├── xianyu/                   # 闲鱼集成（WebSocket + API）
│   ├── management/               # VP 管理层
│   ├── sop/                      # SOP 引擎
│   └── evolution/                # 进化引擎
├── bots/                         # 31 个自动化脚本
│   └── xhs/                      # 小红书子目录（5 文件）
├── business/                     # 9 个商业化方案
├── docs/                         # 28 篇系统文档
├── relay/                        # 飞轮接力数据
├── cron/jobs.yaml                # 8 个定时作业（时区: Asia/Shanghai）
├── tests/                        # 测试模块
├── skills/                       # 290+ 个 SKILL.md
├── setup.py                      # pip 安装（v5.0.0）
├── requirements.txt              # Python 依赖
└── setup.sh                      # 一键部署
```

## 基础设施

### 记忆系统（5 层）

| 层级 | 存储 | 用途 |
|:----|:-----|:----|
| 工作记忆 | LLM 上下文 | 当前会话内信息 |
| 情节记忆 | claude-mem / session_search | 跨会话关键事实 |
| 向量记忆 | ChromaDB (SQLite) | 语义检索 |
| 成本追踪 | cost.db | API 费用持久化 |
| 状态存储 | state.db / tasks.db | 系统运行时状态 |

### 健康探测（HealthProbe）

`molib/infra/health_probe.py` — 自动探测 3 个外部依赖：

| 探针 | 检测内容 | 失败时 |
|:----|:---------|:------|
| DeepSeek API | OpenRouter 可达性 | 飞书告警 |
| 飞书服务 | feishu-cli 登录状态 | 重试 + 告警 |
| 本地进程 | Hermes/Python 存活 | 自动恢复 |

### 卡片系统

`molib/ceo/cards/` — 统一卡片入口（6 模块）：

```
cards/builder.py      → CardBuilder 构建器
cards/templates.py    → 6 个卡片模板函数
cards/sender.py       → FeishuCardSender
cards/thinking.py     → ThinkingCardManager
cards/utils.py        → card_to_text 降级
cards/__init__.py     → 统一导出
```

## 已吸收项目

从 27 个高星开源项目中提取设计模式注入系统架构：

| 项目 | ⭐ | 注入的设计模式 |
|:----|:-:|:--------------|
| OpenAI Agents SDK | 110K | Handoff 模式 — Agent 交接协议 |
| MetaGPT | 67K | 角色-行动-消息循环 |
| CowAgent | 44K | 记忆蒸馏 + 梦境系统 |
| nanobot | 41K | 轻量 Agent 循环 |
| MiroFish | 35K | 群体智能趋势预测 |
| CLI-Anything | 33K | CLI 原生 Agent |
| Ranedeer | 29.6K | AI 导师 Prompt DSL |
| UI-TARS | 29.6K | 多模态 Agent 栈 |
| InvokeAI | 27.1K | AI 创意引擎 |
| FastMCP | 25K | MCP Server SDK |
| Onlook | 25.6K | 设计 ↔ 代码双向同步 |
| A2A | 23.5K | Agent 通信协议 |
| Stagehand | 22.4K | Browser Agent SDK |
| deepagents | 22.4K | 规划工具 — 任务分解 + 拓扑排序 |
| DeepTutor | 23.3K | 深度辅导引擎 |
| CozeStudio | 20.7K | Agent 工作室 |
| Parlant | 18.1K | 客服上下文工程 |
| Skyvern | 21.5K | 浏览器自动化 |
| CUA | 15.6K | Computer-Use Agent |
| Weblate | 5.8K | 本地化平台模式 |
| BeeAI | 3.8K | Schema 驱动工作流 |
| ...另有 6 个项目 | — | — |

## 定时作业

默认全部暂停（零空转）。激活后每日自动流水线（时区: Asia/Shanghai）：

| 时间 | 作业 | 功能 |
|:---:|:-----|:-----|
| 08:00 | 墨思情报扫描 | 博客 / arXiv / MiroFish → 情报日报 |
| 09:00 | 墨迹内容工厂 | 情报 → AI 生成 3 篇内容 |
| 09:00 | CEO 每日简报 | 汇总状态推送至创始人 |
| 10:00 | 墨增增长引擎 | SEO 优化 · 增长分析 |
| 10:00 | 每日治理合规 | 审计 · 合规检查 |
| 12:00 | 系统状态快照 | 汇总产出 + 运营快照 |
| 15/45 分 | 闲鱼消息检测 | 新消息 AI 自动回复 |
| 周五 10:00 | 自学习进化 | GitHub 扫描 + 技能更新 |
