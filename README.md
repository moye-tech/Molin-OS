# 墨麟 OS — AI 一人公司操作系统

<p align="center">
  <strong>6 层架构 · 516 项技能 · 20 家子公司 · 26 个 Worker</strong><br>
  一个人就是一个集团
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12+-00b894?style=flat-square&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-00b894?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/skills-516-success?style=flat-square" alt="Skills">
  <img src="https://img.shields.io/badge/workers-26-success?style=flat-square" alt="Workers">
  <img src="https://img.shields.io/badge/absorbed-27%20projects-10b981?style=flat-square" alt="Absorbed">
  <img src="https://img.shields.io/badge/lines-44K%20Python-ff6b6b?style=flat-square" alt="Code">
</p>

---

## 概述

**墨麟 OS** 是一个人用一台服务器即可运营的 AI 一人公司操作系统。系统包含 20 家垂直子公司，每家子公司有专属 Worker 执行文件和 Skill 技能库，Hermes Agent 作为 CEO 大脑通过统一 CLI 入口调动所有子系统。

核心设计原则：

- **零空转** — 有任务才消耗 token，无任务时系统静止
- **治理驱动** — 5 级审批体系（L0 自动 → L4 绝对禁止），AI 不碰现金
- **技能优先** — 516 个 SKILL.md 作为系统的「长期记忆」，复用已有能力
- **数据持久化** — 所有成本、状态、记忆通过 SQLite 持久化

> 仓库: [github.com/moye-tech/Molin-OS](https://github.com/moye-tech/Molin-OS)  
> 许可: MIT License © 2026 Moye Tech

---

## 目录

- [系统架构](#系统架构)
- [子公司一览](#子公司一览)
- [核心指标](#核心指标)
- [治理体系](#治理体系)
- [快速部署](#快速部署)
- [CLI 参考](#cli-参考)
- [已吸收项目](#已吸收项目)
- [项目结构](#项目结构)
- [许可协议](#许可协议)

---

## 系统架构

```
创始人（你）
    │
┌── CEO 层 ───────────────────────────────────────────┐
│  Hermes Agent · IntentProcessor · 风险控制 · SOP     │
│  卡片系统(6模块) · HealthProbe(3探针)                │
└──────────────────┬──────────────────────────────────┘
                   │  决策流
    ┌──────────────┼─────────────────────┐
    │ 执行层 (20 家子公司 + 专项 Worker)   │
    │ ┌─ 营销(5) ───┐ ┌─ 运营(4) ────┐  │
    │ │ 墨笔·墨韵·   │ │ 墨域·墨声·     │  │
    │ │ 墨图·墨播·   │ │ 墨链·墨学       │  │
    │ │ 墨声配音     │ │                │  │
    │ ├─ 技术(4) ─┤ ├─ 财务(1) ────┤  │
    │ │ 墨码·墨维·   │ │ 墨算            │  │
    │ │ 墨安·墨梦    │ │                │  │
    │ ├─ 战略(3) ─┤ ├─ 共同(3) ────┤  │
    │ │ 墨商·墨海·   │ │ 墨律·墨脑·墨测  │  │
    │ │ 墨研         │ │                │  │
    │ └────────────┘ └───────────────┘  │
    └────────────────┬────────────────────┘
                     │  服务
    ┌────────────────┼────────────────────┐
    │ 基础设施层                           │
    │ 5 层记忆 · EventBus · Config 体系    │
    │ 飞书/闲鱼/小红书集成 · HealthProbe   │
    │ Hermes Toolchain · 516 SKILL.md     │
    └──────────────────────────────────────┘
```

### 执行模型

```
Hermes Agent → terminal 工具 → python -m molib <command> → 结果回传
```

- 简单任务直接用 CLI，复杂推理走 Agent 决策
- 所有子系统通过统一入口 `python -m molib` 调度
- Handoff 自动路由到 16 个领域的最佳 Worker

---

## 子公司一览

### VP 营销（5 家）

| 子公司 | Worker | 核心能力 |
|:-------|:-------|:---------|
| **墨笔文创** | content_writer.py | 文字创作、文案、小红书/公众号内容 |
| **墨韵 IP** | ip_manager.py | IP 孵化、品牌衍生、版权管理 |
| **墨图设计** | designer.py | 封面设计、UI、视觉、电商主图 |
| **墨播短视频** | short_video.py | 短视频脚本生成与制作 |
| **墨声配音** | voice_actor.py | AI 语音合成、播客、有声书 |

### VP 运营（4 家）

| 子公司 | Worker | 核心能力 |
|:-------|:-------|:---------|
| **墨域私域** | crm.py | CRM、用户分层、社群运营 |
| **墨声客服** | customer_service.py | 自动化客服、闲鱼消息 AI 回复 |
| **墨链电商** | ecommerce.py | 订单管理、交易处理 |
| **墨学教育** | education.py | 课程设计、AI 个性化辅导 |

### VP 技术（4 家）

| 子公司 | Worker | 核心能力 |
|:-------|:-------|:---------|
| **墨码开发** | developer.py | 软件开发、代码编写 |
| **墨维运维** | ops.py | 部署、DevOps、GUI 自动化 |
| **墨安安全** | security.py | 安全审计、漏洞扫描 |
| **墨梦 AutoDream** | auto_dream.py | AI 自动化实验、记忆蒸馏 |

### VP 财务（1 家）

| 子公司 | Worker | 核心能力 |
|:-------|:-------|:---------|
| **墨算财务** | finance.py | 记账、预算、成本控制 |

### VP 战略（3 家）

| 子公司 | Worker | 核心能力 |
|:-------|:-------|:---------|
| **墨商 BD** | bd.py | 商务拓展、投标、合作 |
| **墨海出海** | global_marketing.py | 多语言本地化、繁体运营 |
| **墨研竞情** | research.py | 竞争分析、趋势研究、情报 |

### 共同服务（3 家）

| 子公司 | Worker | 核心能力 |
|:-------|:-------|:---------|
| **墨律法务** | legal.py | 合同审查、合规、隐私 |
| **墨脑知识** | knowledge.py | 知识管理、RAG、向量检索 |
| **墨测数据** | data_analyst.py | 数据分析、测试、BI 仪表盘 |

### 专项 Worker（3 个）

| Worker | 核心能力 |
|:-------|:---------|
| trading.py | 量化交易策略、信号、回测 |
| scrapling_worker.py | 网页抓取、数据采集 |
| router9.py | 网络流量、多路路由 |

---

## 核心指标

| 指标 | 数值 |
|:----|:----:|
| Python 模块 | 182 个（44,765 行） |
| SKILL.md 技能 | 516 个 |
| Worker 文件 | 26 个 |
| 子公司 | 20 家 |
| 自动化脚本 | 25 个（bots/） |
| 商业方案 | 9 个（business/） |
| 系统文档 | 25 篇（docs/） |
| 已吸收开源项目 | 27 个（~520K⭐） |
| Handoff 路由领域 | 16 个 |
| SQLite 数据库 | 3 个（cost / state / tasks） |
| 卡片系统模块 | 6 个（cards/） |
| 健康探针 | 3 个（HealthProbe） |
| 定时作业 | 8 个（默认暂停，零空转） |

---

## 治理体系

5 级审批体系，定义见 `config/governance.yaml`（单一真相源）：

| 级别 | 类型 | 描述 |
|:----:|:----:|:-----|
| **L0** | auto | 自动执行 — 内容生成、数据采集、例行报告 |
| **L1** | notify | 完成后通知 — 中风险操作 |
| **L2** | approve | 需人工确认 — 报价 > ¥100、对外发布、修改配置 |
| **L3** | board_approve | 董事会审批 — 重大决策 |
| **L4** | **forbidden** | **绝对禁止 — 涉及现金、转账、支付的操作** |

SOUL.md 和 AGENTS.md 均引用 governance.yaml，确保治理定义无歧义。

---

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

---

## CLI 参考

```bash
python -m molib health          # 系统健康检查
python -m molib help            # 查看所有命令

python -m molib content write   # 内容创作
python -m molib design image    # 图片生成
python -m molib video script    # 视频脚本
python -m molib tts generate    # 语音合成
python -m molib crm segment     # 用户分层
python -m molib xianyu reply    # 闲鱼回复
python -m molib order list      # 订单列表
python -m molib finance report  # 财务报表
python -m molib trading signal  # 交易信号
python -m molib intel trending  # 趋势扫描
python -m molib data analyze    # 数据分析
python -m molib handoff route   # 自动路由
python -m molib plan decompose  # 任务分解
```

---

## 已吸收项目

从 27 个高星开源项目中提取设计模式注入系统架构：

| 项目 | ⭐ | 注入模式 |
|:----|:-:|:---------|
| OpenAI Agents SDK | 110K | Handoff 协议 |
| MetaGPT | 67K | 角色-行动-消息循环 |
| CowAgent | 44K | 记忆蒸馏与梦境系统 |
| nanobot | 41K | 轻量 Agent 循环 |
| MiroFish | 35K | 群体智能预测 |
| CLI-Anything | 33K | CLI 原生 Agent |
| Ranedeer | 29.6K | AI 导师 Prompt DSL |
| UI-TARS | 29.6K | 多模态 Agent 栈 |
| InvokeAI | 27.1K | AI 创意引擎 |
| FastMCP | 25K | MCP Server SDK |
| Onlook | 25.6K | 设计 ↔ 代码双向同步 |
| A2A | 23.5K | Agent 通信协议 |
| Stagehand | 22.4K | Browser Agent SDK |
| DeepTutor | 23.3K | 深度辅导 |
| CozeStudio | 20.7K | Agent 工作室 |
| Skyvern | 21.5K | 浏览器自动化 |
| CUA | 15.6K | Computer-Use Agent |
| Parlant | 18.1K | 客服上下文工程 |
| Weblate | 5.8K | 本地化平台 |
| BeeAI | 3.8K | Schema 工作流 |
| FIBO | — | JSON 驱动电商主图 |
| Generative-Media-Skills | 3.2K | 多媒体创作 |
| Toonflow | — | 剧本 → 分镜管线 |
| Vibe-Workflow | — | 创意工作流 DAG |
| CloakBrowser | — | 反检测浏览器 |

---

## 项目结构

```
Molin-OS/
├── config/                       # 系统配置
│   ├── governance.yaml           # 5 级审批规则
│   ├── company.toml              # 子公司映射
│   ├── models.toml               # 模型路由
│   └── channels.yaml             # 消息渠道
├── molib/                        # 核心执行包（182 模块）
│   ├── __main__.py               # CLI 入口
│   ├── ceo/                      # CEO 引擎
│   │   └── cards/                #   卡片系统（6 模块）
│   ├── agencies/                 # 执行层
│   │   ├── handoff.py            #   自动路由
│   │   ├── planning.py           #   任务分解
│   │   ├── screenplay.py         #   剧本→分镜管线
│   │   ├── agent_collab.py       #   三层 Agent 协作
│   │   └── workers/              #   26 个 Worker
│   ├── infra/                    # 基础设施
│   │   ├── health_probe.py       #   3 探针健康检查
│   │   ├── event_bus.py          #   事件总线
│   │   └── self_healing.py       #   自愈引擎
│   ├── shared/                   # 共享能力
│   │   └── ai/                   #   AI 引擎
│   │       ├── fibo_image_gen.py           # FIBO 生图
│   │       ├── generative_media_skills.py  # 多媒体创作
│   │       └── vibe_workflow.py            # 创意工作流
│   ├── evolution/                # 进化引擎
│   ├── sop/                      # SOP 引擎
│   ├── skills/                   # 本地技能知识库
│   │   └── library/              #   领域知识（导演/营销）
│   └── ...                       # xianyu, trading, video 等子包
├── bots/                         # 25 个自动化脚本
│   └── cloak_browser_adapter.py  #   反检测浏览器
├── business/                     # 9 个商业方案
├── docs/                         # 25 篇系统文档
├── cron/jobs.yaml                # 8 个定时作业
├── skills/                       # 本地 skill 参考
├── setup.py                      # pip 安装包
├── requirements.txt              # Python 依赖
└── setup.sh                      # 一键部署
```

---

## 许可协议

MIT License © 2026 Moye Tech

---

<p align="center">
  <sub>墨麟 OS — 一个人就是一个集团</sub>
</p>
