# 墨麟 OS — AI 一人公司操作系统

<p align="center">
  <strong>Hermes Agent（大脑）→ terminal（神经）→ molib（肌肉）</strong><br>
  <strong>6 层架构 · 447 Python 模块 · 559 项技能 · 20 家子公司 · 26 个 Worker</strong><br>
  一个人就是一个集团
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-00b894?style=flat-square&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-00b894?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/version-v5.0_Ultra_v7.0-blueviolet?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/workers-26-success?style=flat-square" alt="Workers">
  <img src="https://img.shields.io/badge/skills-559-success?style=flat-square" alt="Skills">
  <img src="https://img.shields.io/badge/lines-44K%20Python-ff6b6b?style=flat-square" alt="Code">
  <img src="https://img.shields.io/badge/revenue-%C2%A552K%2Fmonth-ff6b6b?style=flat-square" alt="Revenue">
</p>

---

## 一句话定位 / One-Liner

墨麟 OS 是一个人用一台 MacBook 即可运营的 AI 一人公司操作系统。系统基于 Hermes Agent，包含 20 家垂直子公司和 26 个 Worker，通过统一 CLI 入口调度所有子系统，实现从情报采集、内容创作到增长分发的全自动化管线。

Molin-OS is an AI-powered single-person company operating system that runs on a single MacBook. Built on Hermes Agent with 20 subsidiaries and 26 Workers, it automates the entire pipeline from intelligence gathering and content creation to growth distribution.

> 仓库: [github.com/moye-tech/Molin-OS](https://github.com/moye-tech/Molin-OS)  
> 许可: MIT License © 2026 Moye Tech

---

## 目录 / Table of Contents

- [架构总览 / Architecture](#架构总览--architecture)
- [技术栈 / Tech Stack](#技术栈--tech-stack)
- [核心设计原则 / Core Principles](#核心设计原则--core-principles)
- [子公司体系 / Subsidiaries](#子公司体系--subsidiaries)
- [执行模型 / Execution Model](#执行模型--execution-model)
- [定时任务体系 / Cron Jobs](#定时任务体系--cron-jobs)
- [飞轮管线 / Flywheel Pipeline](#飞轮管线--flywheel-pipeline)
- [治理模型 / Governance](#治理模型--governance)
- [CLI 命令一览 / CLI Reference](#cli-命令一览--cli-reference)
- [记忆系统 / Memory Architecture](#记忆系统--memory-architecture)
- [飞书消息规范 / Feishu Output](#飞书消息规范--feishu-output)
- [核心指标 / Key Metrics](#核心指标--key-metrics)
- [已吸收项目 / Absorbed Projects](#已吸收项目--absorbed-projects)
- [目录结构 / Project Structure](#目录结构--project-structure)
- [快速部署 / Quick Start](#快速部署--quick-start)
- [环境要求 / Requirements](#环境要求--requirements)
- [许可协议 / License](#许可协议--license)

---

## 架构总览 / Architecture

```
创始人 / Founder（墨烨）
    │
    ├── CLI 入口 (python -m molib)          ← 本地操作模式
    ├── HTTP API (FastAPI :8000)            ← 远程服务模式（Ultra）
    └── 飞书 WebSocket/Webhook              ← 消息平台接入
         │
┌── L0 中枢层 / CEO Layer ───────────────────────────────────────┐
│  Hermes Agent · SOUL.md 认知框架 · DARE 推理引擎                │
│  IntentProcessor · BudgetGuard · governance.yaml 治理规则        │
│  卡片系统(6模块) · HealthProbe(3探针) · 自愈引擎                  │
└──────────────────┬──────────────────────────────────────────────┘
                   │  委托 / Delegate
┌── L1 管理层 / Manager Layer ────────────────────────────────────┐
│  ManagerDispatcher · ConfigDrivenManager                        │
│  QualityGate · Handoff自动路由(16领域) · PlanningTool            │
└──────────────────┬──────────────────────────────────────────────┘
                   │  调度 / Dispatch
┌── L2 执行层 / Execution Layer ──────────────────────────────────┐
│  20 家子公司 + 3 个专项 Worker                                   │
│  ┌─ 营销(5) ───┐ ┌─ 运营(4) ────┐ ┌─ 技术(4) ────┐              │
│  │ 墨笔·墨韵·   │ │ 墨域·墨声·     │ │ 墨码·墨维·   │              │
│  │ 墨图·墨播·   │ │ 墨链·墨学       │ │ 墨安·墨梦    │              │
│  │ 墨声配音     │ │                │ │              │              │
│  ├─ 财务(1) ─┤ ├─ 战略(3) ────┤ ├─ 共同(3) ────┤              │
│  │ 墨算            │ │ 墨商·墨海·   │ │ 墨律·墨脑·墨测  │              │
│  │                 │ │ 墨研         │ │                │              │
│  └────────────────┘ └──────────────┘ └────────────────┘              │
└──────────────────┬──────────────────────────────────────────────┘
                   │  服务 / Services
┌── L3 自动化层 / Automation Layer ───────────────────────────────┐
│  8 个 Cron 定时任务 · 28 个 Bot 脚本                             │
│  飞轮三棒接力 · SOP 引擎 · 自学习每周循环                          │
└──────────────────┬──────────────────────────────────────────────┘
                   │
┌── L4 基础设施层 / Infrastructure Layer ─────────────────────────┐
│  5 层记忆（工作/情节/语义/向量/结构化）                          │
│  EventBus · ModelRouter · 自愈引擎                               │
│  飞书集成 · 闲鱼集成 · 小红书集成 · HealthProbe                  │
│  Hermes Toolchain · 559 SKILL.md 技能库                          │
└──────────────────────────────────────────────────────────────────┘
```

---

## 技术栈 / Tech Stack

| 类别 / Category | 技术 / Technology | 版本 |
|:---------------|:-----------------|:----:|
| 操作系统 / OS | macOS | 26.4.1 (Apple Silicon M2) |
| 运行时 / Runtime | Python | 3.11.15 (主) / 3.12.13 (闲鱼) |
| AI Agent 框架 | Hermes Agent | v0.13.0 |
| Python 包管理 | uv + pip | — |
| LLM 提供商 | DeepSeek via OpenRouter | flash/pro 分级 |
| 视觉模型 | 通义千问 qwen3-vl-plus（百炼 API） | — |
| 图像生成 | 千问百炼 qwen-image-2.0-pro | — |
| 视频生成 | HappyHorse-1.0-T2V / MPT / Pixelle | — |
| 语音合成 | Edge TTS | — |
| 网页采集 | Firecrawl + Scrapling | — |
| 向量数据库 | ChromaDB | — |
| 结构化存储 | SQLite (3 db) | — |
| 消息平台 | 飞书 / 闲鱼 / 小红书 | — |
| Web 仪表盘 | Flask | 可选 |
| 视频处理 | FFmpeg | 8.1.1 |
| 多媒体框架 | ComfyUI | 本地 |

**预算 / Budget:**
- 每月 API 预算：¥1,360 / month (零空转模式，实际消耗接近零)
- 收入目标：¥52,000 / month
- 子公司运营预算：¥3,490 / month (L0+L1+L2 分配)

---

## 核心设计原则 / Core Principles

1. **零空转** / Zero Idle — 有任务才消耗 token，无任务时系统静止
2. **治理驱动** / Governance-driven — 4 级审批体系（L0 自动 → L4 绝对禁止），AI 不碰现金
3. **技能优先** / Skill-first — 559 个 SKILL.md 作为系统的「长期记忆」，复用已有能力
4. **数据持久化** / Data Persistence — 所有成本、状态、记忆通过 SQLite + ChromaDB 持久化
5. **研究优先于创作** / Research First — 任何输出类任务必须先调用墨研竞情做实时调研
6. **强制委托** / Force Delegation — CEO 不自己包办，必须委托给对应子公司
7. **超预期交付** / Elevate — 每次交付都比基础需求多走一步

### 强制委托协议 / Mandatory Delegation Protocol (v2.0)

【黄金律】问题问我，产出找他们。

**必须委托的产出类型：** 写 / 做 / 生成 / 创作 / 设计 / 调研 / 分析 / 开发 / 配音 / 上架 / 记录 / 发布

**CEO 收到消息的强制决策树 (DARE v3.0):**
- D — 解构目标 (Decompose): 完成后应该是什么样子？
- A — 分析缺口 (Analyze): 缺实时数据？用户洞察？法律确认？技术实现？
- R — 智能编排 (Route): 找最擅长这个环节的 Worker，能并行的并行
- E — 超预期设计 (Elevate): 还能加什么让结果超出预期？

---

## 子公司体系 / Subsidiaries

20 家子公司 + 3 个专项 Worker，归属 5 位 VP + 共同服务。

### VP 营销 / Marketing（5 家）

| 子公司 | Worker 文件 | 核心能力 | 所属技能 |
|:-------|:-----------|:---------|:---------|
| 墨笔文创 | content_writer.py | 文字内容创作、文案、小红书/公众号 | molin-xiaohongshu, copywriting, content-strategy |
| 墨韵 IP | ip_manager.py | IP 孵化、品牌衍生、版权管理 | ai-taste-quality |
| 墨图设计 | designer.py | 封面设计、UI、视觉、Open Design 全栈(149设计系统×134技能) | molin-design, excalidraw, open-design |
| 墨播短视频 | short_video.py | 短视频脚本生成与制作 (MPT/Pixelle) | ffmpeg-video-engine, pixelle-video-engine |
| 墨声配音 | voice_actor.py | AI 语音合成、播客、有声书 | molin-audio-engine, songwriting |

### VP 运营 / Operations（4 家）

| 子公司 | Worker 文件 | 核心能力 | 所属技能 |
|:-------|:-----------|:---------|:---------|
| 墨域私域 | crm.py | CRM、用户分层、社群运营 | molin-crm, social-push-publisher |
| 墨声客服 | customer_service.py | 自动化客服、闲鱼消息 AI 回复 | molin-customer-service, xianyu-automation |
| 墨链电商 | ecommerce.py | 订单管理、交易处理、发票 | molin-order |
| 墨学教育 | education.py | 课程设计、AI 个性化辅导 | molin-education, ranedeer-ai-tutor |

### VP 技术 / Technology（4 家）

| 子公司 | Worker 文件 | 核心能力 | 所属技能 |
|:-------|:-----------|:---------|:---------|
| 墨码开发 | developer.py | 软件开发、代码编写、技术实现 | cli-anything, agent-engineering-backend-architect |
| 墨维运维 | ops.py | 部署、DevOps、GUI 自动化、系统健康 | ghost-os, opensre-sre-agent |
| 墨安安全 | security.py | 安全审计、漏洞扫描、合规检查 | red-teaming, ag-vulnerability-scanner |
| 墨梦 AutoDream | auto_dream.py | AI 自动化实验、记忆蒸馏、快速原型 | deep-dream-memory, self-learning-loop |

### VP 财务 / Finance（1 家）

| 子公司 | Worker 文件 | 核心能力 |
|:-------|:-----------|:---------|
| 墨算财务 | finance.py | 记账、预算、成本控制、财务报表 |

### VP 战略 / Strategy（3 家）

| 子公司 | Worker 文件 | 核心能力 | 所属技能 |
|:-------|:-----------|:---------|:---------|
| 墨商 BD | bd.py | 商务拓展、合作洽谈、投标 | molin-bd-scanner, agent-sales-deal-strategist |
| 墨海出海 | global_marketing.py | 多语言本地化、繁体运营、海外市场 | molin-global, weblate-localization |
| 墨研竞情 | research.py | 竞争分析、趋势研究、情报扫描 | karpathy-autoresearch, world-monitor, mirofish-trends |

### 共同服务 / Shared Services（3 家）

| 子公司 | Worker 文件 | 核心能力 | 所属技能 |
|:-------|:-----------|:---------|:---------|
| 墨律法务 | legal.py | 合同审查、合规、隐私、风险评估 | molin-legal |
| 墨脑知识 | knowledge.py | 知识管理、RAG、向量检索、MQL 查询 | molin-memory, supermemory, gitnexus |
| 墨测数据 | data_analyst.py | 数据分析、测试、BI 仪表盘 | molin-data-analytics, molin-vizro |

### 专项预置 / Special Workers（3 个）

| Worker | 核心能力 | 说明 |
|:-------|:---------|:-----|
| trading.py | 量化交易策略、信号、回测（BTC/ETH） | CLI: `python -m molib trading` |
| scrapling_worker.py | 网页抓取、数据采集（curl_cffi 指纹模拟） | CLI: `python -m molib scrap` |
| router9.py | 网络流量、AI 代理路由、多路路由 | CLI: `python -m molib proxy` |

### WorkerChain 标准组合表

| 任务场景 | 标准链路 | 并行可选 |
|:---------|:---------|:---------|
| 小红书内容营销 | 墨研竞情→墨笔文创→墨图设计 | 研情+设计并行 |
| 抖音短视频 | 墨研竞情→墨播短视频→墨声配音 | 否 |
| 闲鱼商品上架 | 墨研竞情→墨笔文创→墨图设计→墨链电商 | 研情+设计并行 |
| 课程设计 | 墨研竞情→墨学教育→墨笔文创 | 否 |
| 出海内容本地化 | 墨研竞情→墨笔文创→墨海出海→墨律法务 | 法务可并行 |
| 竞品深度报告 | 墨研竞情→墨测数据→墨笔文创 | 研情+数据并行 |
| 技术产品上线 | 墨码开发→墨安安全→墨维运维 | 安全+运维并行 |
| BD 商务谈判 | 墨研竞情→墨商 BD→墨律法务 | 否 |
| 私域用户触达 | 墨测数据→墨域私域→墨笔文创 | 数据+文创并行 |

---

## 执行模型 / Execution Model

### 模式 A：CLI 本地操作（默认）

```
Hermes Agent（大脑）→ terminal 工具（神经）→ python -m molib <command>（肌肉）→ 结果回传
```

- 纯思考/规划/决策 → 直接在对话中完成
- 需要真实操作（发消息/生成文件/调用API） → 用 terminal 执行 molib CLI
- cron 定时任务 → Hermes cron 按 jobs.yaml 配置，加载对应 SKILL.md 执行

### 模式 B：Server 远程服务（Ultra v7.0）

```
飞书/HTTP → IntentProcessor → CEO 决策 → Manager 调度 → Worker(think→act→reflect) → 结果综合
```

- FastAPI 服务 (:8000)
- 飞书 Bot WebSocket/Webhook 交互
- 多轮推理、审批流程支持

### Handoff 自动路由

16 家子公司已注册 Handoff，支持全自动任务路由：

```bash
python -m molib handoff route --task "帮我写一篇小红书文案"
python -m molib handoff route --task "帮我做数据分析"
python -m molib handoff list        # 查看所有可用 Worker
python -m molib handoff history     # 查看执行历史
```

支持领域：内容创作、设计、开发、运维、安全、CRM、客服、数据、交易、BD、财务、法务、教育、情报、出海、知识管理。

---

## 定时任务体系 / Cron Jobs

系统共有 8 个 Hermes Cron 定时任务，均默认设置为零空转模式（需手动激活）。

### 飞轮三棒核心管线

| 时间 | 作业 | ID | 技能 | 描述 |
|:----:|:-----|:---|:-----|:-----|
| 08:00 | 墨思情报银行每日扫描 | ff8d58571b1a | blogwatcher, last30days, world-monitor, mirofish-trends, arxiv | 飞轮第一棒：扫描外部情报→LLM提炼→输出日报 |
| 09:00 | 墨迹内容工厂飞轮闭环 | 36d28ca9139f | xiaohongshu-content-engine, ffmpeg-video-engine, seo-machine, agent-marketing-content-creator, humanizer | 飞轮第二棒：获取情报→评估→生成内容→接力 |
| 10:00 | 墨增增长引擎接力 | 56cf70cf7865 | claude-seo, seo-audit, analytics-tracking, content-strategy, page-cro, marketing-skills-cro/copywriting, agent-marketing-growth-hacker | 飞轮第三棒：获取接力数据→SEO优化→增长方案 |

### CEO 简报 + 治理

| 时间 | 作业 | ID | 技能 | 描述 |
|:----:|:-----|:---|:-----|:-----|
| 09:00 | CEO 每日简报 | 1fb85e22e60d | molin-ceo-persona, molin-goals | 汇总昨日产出/今日待办/系统状态 |
| 10:00 | 每日治理合规检查 | 2569ff28d2ae | molin-governance | 检查所有操作合规→审计日志→L2待审批上报 |
| 12:00 | 系统状态快照每日汇总 | 1ebce945f706 | molin-company-structure | 收集24小时产出→结构化统计→运营快照 |

### 高频 + 每周任务

| 时间 | 作业 | ID | 技能 | 描述 |
|:----:|:-----|:---|:-----|:-----|
| 15,45 9-21 | 墨商销售闲鱼消息检测 | e318dfc348d2 | xianyu-automation, marketing-skills-copywriting, agent-sales-deal-strategist | 每30分钟检测闲鱼新消息→L0/L1/L2分级处理 |
| 周五 10:00 | 自学习每周循环 | e4682a49699d | skill-discovery, self-learning-loop, karpathy-autoresearch | 扫描GitHub/HN/PH→提炼洞察→更新SKILL.md |

### 飞轮接力规则

1. 每棒必须先检查 relay/ 中是否有上一棒的文件（flywheel_guard.check_upstream）
2. 如果上游文件缺失且超过90分钟 → 发 T4 飞书告警"飞轮断裂"
3. 第1棒失败 → 第2棒自动断链告警 → 第3棒也会断链（级联保护机制）
4. 所有 Cron 输出统一通过 FeishuOutputEnforcer 格式化

---

## 飞轮管线 / Flywheel Pipeline

系统每日自动运行的内容自动化链，三棒全自动通过 relay/ 目录接力：

```
08:00   第一棒：情报银行（墨研竞情）
        daily_hot_report.py
        → relay/intelligence_morning.json
        （品类热度、爆款笔记、选题建议、热搜摘要）

09:00   第二棒：内容工厂（墨笔文创）
        flywheel_content.py
        ← intelligence_morning.json → AI生成3篇内容草稿
        → relay/content_flywheel.json
        （标题、正文、标签、封面Prompt、策略分析）

09:30   第三棒：分发策略（墨测数据）
        flywheel_distribute.py
        ← content_flywheel.json → 评估分发平台/优先级/时间/CTA
        → relay/distribution_plan.json
        （每篇内容的分发调度计划）

10:00   简报推送（墨研竞情）
        daily_briefing.py
        ← intelligence_morning.json → 生成排版简报
        → relay/briefing_daily.md

10:00   墨播短视频 → 读内容+脚本化 → relay/short_video_task.json（扩展中）
17:00   CEO复盘 → 汇总全天产出 → relay/daily_review.json（扩展中）
```

### 接力规则

1. 文件格式严格对齐：第一棒→第二棒→第三棒各层 JSON schema 一致
2. 缺失上游数据时生成占位数据，确保管线不中断
3. 所有脚本使用纯 Python 标准库（json/os/sys/datetime/random）
4. 日志同步备份至 ~/.hermes/daily_reports/

---

## 治理模型 / Governance

4 级审批体系 + 1 个绝对禁止等级，定义见 `config/governance.yaml`（单一真相源）。

| 级别 | 类型 | 预算上限 | 描述 | 示例 |
|:----:|:----:|:--------:|:-----|:-----|
| **L0** | auto | ¥0 | 自动执行，无需确认 | 内容草稿、趋势查询、健康检查 |
| **L1** | notify | ¥10 | AI 内部检查后自动执行，通知创始人 | 发布小红书、更新 SEO、调整定价 |
| **L2** | approve | ¥100 | 需创始人确认后执行 | 商业提案、大额推广、客户交付物 |
| **L3** | board_approve | ¥1,000 | 董事会审批 | 新增产品线、战略调整、超预算支出 |
| **L4** | **forbidden** | — | **绝对禁止** | **涉及现金/转账/支付/改价** |

**预算控制 / Budget Control:**
- 月度 API 预算上限：¥1,360（零空转，实际接近零）
- 触发告警阈值：80%
- 审计追踪：90 天 JSONL 日志，存储至 ~/.molin/audit/

---

## CLI 命令一览 / CLI Reference

所有执行通过 `python -m molib <command>` 调用：

```bash
# ── 系统 ──
python -m molib health                 # 9 探针健康检查
python -m molib help                    # 查看 50+ 命令

# ── 内容创作（墨笔文创）──
python -m molib content write --topic "主题" --platform xhs
python -m molib content publish --platform xhs --draft-id xxx

# ── 设计（墨图设计 v2.2）──
python -m molib design image --prompt "描述" --style 写实
python -m molib design web --prompt "官网" --action landing_page --ds apple

# ── 短视频（墨播短视频）──
python -m molib video script --topic "主题" --duration 60s
python -m molib video generate --topic "主题" --engine mpt|pixelle

# ── 私域运营（墨域私域）──
python -m molib crm segment --by 活跃度
python -m molib crm push --segment 高活跃 --content "消息"

# ── 客服（墨声客服）──
python -m molib xianyu reply --msg-id xxx --content "回复内容"

# ── 情报（墨研竞情）──
python -m molib intel trending
python -m molib intel predict --topic "AI Agent 趋势"
python -m molib intel firecrawl research --topic "主题"
python -m molib intel reach --url URL

# ── 抓取（Scrapling）──
python -m molib scrap fetch --url URL
python -m molib scrap crawl --start-urls U --max-pages N

# ── 财务（墨算财务）──
python -m molib finance record --type expense --amount 100 --note "API费用"
python -m molib finance report
python -m molib cost report
python -m molib cost daily 7

# ── 电商（墨链电商）──
python -m molib order list --status pending
python -m molib order create --title T --source S --value V
python -m molib order invoice --order-id ID --customer C
python -m molib order stats

# ── 交易（墨投交易）──
python -m molib trading signal --symbol BTC/USDT
python -m molib trading analyze --market-type crypto --symbol BTC/USDT
python -m molib trading backtest --strategy S --period 90d

# ── 数据（墨测数据）──
python -m molib data analyze --file xxx.csv

# ── Handoff 自动路由 ──
python -m molib handoff route --task "内容创作"
python -m molib handoff list
python -m molib handoff history

# ── 规划分解 ──
python -m molib plan create --title "..." --description "..."
python -m molib plan decompose --plan-id xxx

# ── 元技能（四核心）──
python -m molib ghost-os health              # 系统健康（ghost-os）
python -m molib ghost-os cron list           # Cron 状态
python -m molib self-learning reflect        # 反思协议（self-learning-loop）
python -m molib karpathy scan --topic "主题"  # 情报扫描（karpathy-autoresearch）
python -m molib moneymaker assess --idea "..." # 变现评估（moneymaker-turbo）

# ── 飞书多维表格 ──
python -m molib bitable schema
python -m molib bitable write <table> --json '{...}'
python -m molib bitable list <table>

# ── 设备 ──
python -m molib pocketbase install|start|stop|status
python -m molib proxy start|stop|status|providers
python -m molib avatar create --text "你好" --image pic.jpg

# ── 其他 ──
python -m molib query "FROM skills WHERE ..."  # MQL 结构化查询
python -m molib manifest validate              # Manifest 验证
python -m molib swarm list                     # Swarm 跨子公司通路
python -m molib sync list|run|start|stop       # CocoIndex 增量同步
python -m molib index watch|query|sync|stats   # 本地索引
```

---

## 记忆系统 / Memory Architecture

三层记忆架构，系统越用越聪明的核心机制：

### 1. 工作记忆 / Working Memory（当前会话）
- Agent 在当前对话中的上下文
- 会话结束后重要内容写入 relay/ 或更新 SKILL.md

### 2. 情节记忆 / Episodic Memory（跨会话）
- **claude-mem 插件**：每次会话结束后自动运行
- 提取关键事实、决策、模式、偏好、关系
- 按重要性评分 (0.0-1.0) 分级，>=0.5 存入向量数据库
- 构建知识图谱，实体自动关联
- 存储位置：`~/.hermes/memory/long_term/`

### 3. 语义记忆 / Semantic Memory（永久）
- 通用规律、SOP 模式、成功策略
- 存储于对应子公司的 SKILL.md 文件和 SOUL.md

### 存储位置

```
~/.hermes/memory/chroma_db/        # 向量记忆存储（ChromaDB）
~/.hermes/memory/vector_memory.db  # 结构化记忆（SQLite）
~/.hermes/dream/                   # 墨梦 AutoDream 的记忆蒸馏产出
~/.hermes/daily_reports/           # 每日数据报表存档
~/.hermes/memory/long_term/        # claude-mem 长期记忆
~/.hermes/events/                  # FileEventBus 事件存储
```

### 自学习反思协议 / Self-Learning Loop

复杂任务（5+ 工具调用）完成后自动激活 4 步反思协议：

1. **识别学习点** — 什么假设错了？什么成功了？
2. **分类教训** — Pitfall / Pattern / Command / Correction / Environment
3. **决定去向** — 用户偏好→memory；可复用流程→SKILL.md
4. **执行落地** — 使用 memory 工具或 skill_manage 工具

触发条件：修复 bug / 用户纠正 / 发现可复用流程 / 跨 session 任务

---

## 飞书消息规范 / Feishu Output

所有推送到飞书的内容必须遵守 3 条消息有序发送结构：

**消息① 思维链卡片** — 独立 `note` 小字组件，主回复前发送
- 意图解析、需求拆解（L1/L2/L3）、调度决策、成本预估、质量审查

**消息② 主回复卡片** — 结构化 interactive card
- header + section + divider + 彩色标签
- 内容层次：核心结论 → 数据支撑 → 风险兜底 → 操作按钮
- 禁止裸露 #、---、**、|表格|、```代码块``` 等 Markdown 格式

**消息③ 子公司详情卡片** — 按需展开

**发送前自检管线（FeishuPreSendValidator 三道关卡）：**
1. thinking 前缀截断（P0）— 自动移除模型泄漏文本
2. Markdown 残留检测（P3）— 自动检测并修复
3. 长消息降级（P4）— >1500 字自动写入 MD → 飞书文档 → 只发链接

---

## 核心指标 / Key Metrics

| 指标 / Metric | 数值 |
|:-------------|:----:|
| Python 模块 / Python Modules | 447 个（~44K 行） |
| SKILL.md 技能 | 559 个 |
| Worker 文件 | 26 个 |
| 子公司 / Subsidiaries | 20 家 |
| Bot 脚本 | 28 个（bots/） |
| 商业方案 / Business Plans | 9 个（business/） |
| 系统文档 / Docs | 21+ 篇（docs/） |
| 子公司技能 / molin-* Skills | ~30 个核心技能 |
| Handoff 路由领域 | 16 个 |
| Cron 定时任务 | 8 个 |
| SQLite 数据库 | 3 个（cost/state/tasks） |
| 卡片系统模块 | 6 个（cards/） |
| 健康探针 | 9 个（HealthProbe） |
| 已吸收开源项目 | 27 个（~520K ⭐） |
| VP 管理层 | 5 位 |
| 治理等级 | 4+1 级（L0-L4） |
| 月 API 预算 | ¥1,360 |
| 月收入目标 | ¥52,000 |

---

## 已吸收项目 / Absorbed Projects

从 27 个高星开源项目中提取设计模式注入系统架构：

| 项目 / Project | ⭐ | 注入模式 / Injected Pattern |
|:---------------|:-:|:---------------------------|
| OpenAI Agents SDK | 110K | Handoff 协议 |
| MetaGPT | 67K | 角色-行动-消息循环 |
| CowAgent | 44K | 记忆蒸馏与梦境系统 |
| nanobot | 41K | 轻量 Agent 循环 |
| MiroFish | 59K | 群体智能预测 |
| CLI-Anything | 33K | CLI 原生 Agent |
| PaperClip | 62K | 审批/治理引擎 |
| Ranedeer | 29.6K | AI 导师 Prompt DSL |
| UI-TARS | 29.6K | 多模态 Agent 栈 |
| InvokeAI | 27.1K | AI 创意引擎 |
| FastMCP | 25K | MCP Server SDK |
| Onlook | 25.6K | 设计↔代码双向同步 |
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
| Toonflow | — | 剧本→分镜管线 |
| Vibe-Workflow | — | 创意工作流 DAG |
| CloakBrowser | — | 反检测浏览器 |

---

## 目录结构 / Project Structure

```
Molin-OS/
├── SOUL.md                       # CEO 认知框架（灵魂文件 — DARE 推理、委托协议、自我检查）
├── SOUL_ULTRA.md                 # Ultra v7.0 版本（双模式：CLI + Server）
├── AGENTS.md                     # 项目上下文（子公司映射、CLI 参考、执行模型）
├── README.md                     # 本文件
├── ENVIRONMENT.md                # 环境清单（macOS/Python/Hermes 版本、密钥状态）
├── requirements.txt              # Python 依赖
├── setup.py                      # pip 安装包（entry_points: molin, moyu）
├── setup.sh                      # 一键部署脚本
│
├── config/                       # 系统配置
│   ├── governance.yaml           # 4 级审批规则（单一真相源）
│   ├── company.toml              # 20 家子公司映射（唯一配置源）
│   ├── models.toml               # 模型路由配置
│   └── channels.yaml             # 消息渠道配置
│
├── molib/                        # 核心执行包（447 Python 模块）
│   ├── __init__.py               # 包版本
│   ├── __main__.py               # CLI 统一入口（1276 行，50+ 命令）
│   ├── cli.py                    # 备用 CLI 实现
│   │
│   ├── ceo/                      # CEO 引擎层
│   │   ├── ceo.py                # CEO 核心决策
│   │   ├── ceo_orchestrator.py   # 编排器
│   │   ├── ceo_reasoning.py      # 推理引擎
│   │   ├── dare_reasoner.py      # DARE v3.0 推理
│   │   ├── intent_router.py      # 意图路由器
│   │   ├── semantic_router.py    # 语义路由
│   │   ├── llm_client.py         # LLM 客户端抽象
│   │   ├── budget_guard.py       # 预算守卫
│   │   ├── risk_engine.py        # 风险评估
│   │   ├── plan_mode.py          # 规划模式
│   │   ├── phase_executor.py     # 阶段执行器
│   │   ├── dag_engine.py         # DAG 任务编排
│   │   ├── task_logger.py        # 任务日志
│   │   ├── sop_store.py          # SOP 存储
│   │   ├── thinking_card.py      # 思维链卡片
│   │   ├── result_card_v7.py     # 结果卡片 v7
│   │   ├── feishu_card.py        # 飞书卡片
│   │   ├── main.py               # FastAPI 入口（Ultra）
│   │   └── cards/                # 卡片系统（6 模块）
│   │
│   ├── agencies/                 # 执行层
│   │   ├── base.py               # 基类
│   │   ├── worker.py             # Worker 抽象
│   │   ├── handoff.py            # Handoff 自动路由
│   │   ├── handoff_register.py   # Handoff 注册表
│   │   ├── planning.py           # 规划工具
│   │   ├── planning_bridge.py    # 规划桥接
│   │   ├── dispatcher.py         # 调度器
│   │   ├── smart_dispatcher.py   # 智能调度
│   │   ├── agent_collab.py       # 三层 Agent 协作
│   │   ├── swarm_bridge.py       # Swarm 桥接
│   │   ├── screenplay.py         # 剧本→分镜管线
│   │   ├── trading_agents.py     # 交易 Agent
│   │   └── worker_chain.py       # WorkerChain 组合
│   │
│   ├── infra/                    # 基础设施
│   │   ├── health_probe.py       # 9 探针健康检查
│   │   ├── event_bus.py          # 事件总线
│   │   ├── self_healing.py       # 自愈引擎
│   │   ├── coco_index.py         # CocoIndex 本地索引
│   │   ├── budget_guard.py       # 预算守卫（infra 版）
│   │   ├── credential_vault.py   # 凭据保险箱
│   │   ├── deep_approval.py      # 深度审批
│   │   ├── supermemory.py        # Supermemory 集成
│   │   ├── pocketbase.py         # PocketBase 管理
│   │   ├── feishu_bitable.py     # 飞书多维表格
│   │   ├── feishu_noise_filter.py # 飞书噪音过滤
│   │   ├── molib_db.py           # 数据库
│   │   ├── molib_flow.py         # 工作流引擎
│   │   ├── molib_mail.py         # 邮件
│   │   ├── molib_order.py        # 订单引擎
│   │   ├── molib_analytics.py    # 分析
│   │   ├── molib_comfy.py        # ComfyUI 集成
│   │   ├── molib_stt.py          # 语音识别
│   │   ├── digital_human.py      # 数字人
│   │   ├── gateway/              # 飞书网关
│   │   │   ├── feishu_card_builder.py
│   │   │   ├── feishu_pre_send.py
│   │   │   ├── feishu_pre_send_validator.py
│   │   │   ├── feishu_output_enforcer.py
│   │   │   └── feishu_reply_pipeline.py
│   │   └── ...（20+ infra 模块）
│   │
│   ├── intelligence/             # 情报
│   │   ├── firecrawl_client.py   # Firecrawl 集成
│   │   ├── predictor.py          # MiroFish 预测
│   │   ├── reacher.py            # Agent-Reach 爬虫
│   │   └── trends.py             # 趋势分析
│   │
│   ├── content/                  # 内容
│   ├── video/                    # 视频
│   ├── trading/                  # 量化交易
│   ├── xianyu/                   # 闲鱼
│   ├── management/               # VP 管理层
│   ├── evolution/                # 进化引擎
│   ├── sop/                      # SOP 引擎
│   ├── publish/                  # 发布
│   ├── relay/                    # 飞轮接力
│   ├── shared/                   # 共享层
│   ├── business/                 # 商业方案
│   ├── feishu_ext/               # 飞书扩展
│   └── integrations/             # 第三方集成
│
├── cron/                         # 定时任务
│   └── jobs.yaml                 # 8 个 Hermes Cron 作业
│
├── bots/                         # 28 个自动化脚本
│   ├── daily_hot_report.py       # 每日热点报告
│   ├── flywheel_content.py       # 飞轮内容生成
│   ├── flywheel_distribute.py    # 飞轮分发策略
│   ├── daily_briefing.py         # 每日简报
│   ├── xianyu_bot.py             # 闲鱼 Bot
│   ├── xhs_bot.py                # 小红书 Bot
│   ├── crm_automation.py         # CRM 自动化
│   ├── crm_daily_report.py       # CRM 日报
│   ├── backup.py                 # 备份
│   ├── money_printer.py          # 变现引擎
│   ├── browser_agent.py          # 浏览器 Agent
│   ├── cloak_browser_adapter.py  # 反检测浏览器
│   ├── tts_generator.py          # TTS 生成
│   ├── video_generator.py        # 视频生成
│   ├── podcast_generator.py      # 播客生成
│   ├── image_generator.py        # 图片生成
│   ├── localize_to_traditional.py # 繁体本地化
│   ├── vpn_optimizer.py          # VPN 优化
│   ├── skill_store_installer.py  # 技能商店安装
│   ├── build_visual_identity.py  # 视觉形象构建
│   └── ...（共 28 个 bot 脚本）
│
├── business/                     # 9 个商业方案
├── docs/                         # 21+ 篇系统文档
├── relay/                        # 飞轮接力数据（运行时生成）
│   ├── intelligence_morning.json # 情报日报
│   ├── content_flywheel.json     # 内容接力
│   ├── distribution_plan.json    # 分发计划
│   ├── briefing_daily.md         # 简报
│   └── growth_flywheel.json      # 增长数据
│
├── skills/                       # 本地技能知识库（340 个技能目录）
│   ├── molin-*/                  # ~30 个 molin 核心技能
│   ├── karpathy-autoresearch/    # 情报研究
│   ├── ghost-os/                 # 运维
│   ├── self-learning-loop/       # 自学习
│   ├── moneymaker-turbo/         # 变现评估
│   ├── ...（共 559 个 SKILL.md）
│   └── scripts/                  # 各技能的辅助脚本
│
├── molin-skills/                 # molin 技能子模块
├── .env.example                  # 环境变量模板
└── molib/xianyu/.venv/           # 闲鱼 Python 3.12 venv
```

---

## 快速部署 / Quick Start

### 前置条件 / Prerequisites
- macOS / Linux（推荐 Apple Silicon M2+）
- Python 3.11+
- Git 2.50+
- FFmpeg（可选，视频生成需要）

### 安装 / Install

```bash
# 1. 克隆仓库
git clone https://github.com/moye-tech/Molin-OS.git
cd Molin-OS

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt
pip install -e .

# 4. 环境变量
cp .env.example .env
# 编辑 .env 填入 API Keys:
#   DEEPSEEK_API_KEY / DASHSCOPE_API_KEY / OPENROUTER_API_KEY
#   FEISHU_APP_ID / FEISHU_APP_SECRET
#   GITHUB_TOKEN / SUPERMEMORY_API_KEY

# 5. 验证
python -m molib health
python -m molib help
```

### 一键部署 / One-click Setup

```bash
bash setup.sh
```

### 启用 Cron（可选）

```bash
# 通过 Hermes Agent cronjob 工具激活
# cron/jobs.yaml 中所有任务默认暂停，零空转
```

---

## 环境要求 / Requirements

### Python 依赖（requirements.txt）

```
# 核心
pyyaml>=6.0
python-dotenv>=1.0.0
click>=8.1.0
rich>=13.0.0

# 网络
requests>=2.31.0
httpx>=0.25.0
aiohttp>=3.9.0

# 数据处理
pandas>=2.0.0
numpy>=1.24.0

# 内容生成
openai>=1.0.0
markdown>=3.5

# 视频
ffmpeg-python>=0.2.0

# 监控与日志
loguru>=0.7.0
schedule>=1.2.0

# Web 仪表盘（可选）
flask>=3.0.0
flask-cors>=4.0.0

# 测试
pytest>=8.0.0
pytest-cov>=4.0.0
```

### Hermes Agent 环境

- Hermes Agent v0.13.0
- OpenAI SDK 2.36.0
- Gateway PID（launchd 托管）
- Firecrawl API（可选，情报采集用）
- 闲鱼 Python 3.12 独立环境

### 密钥清单

| 密钥 | 用途 | 状态 |
|:-----|:-----|:----:|
| DEEPSEEK_API_KEY | LLM 推理 | 必填 |
| DASHSCOPE_API_KEY | 视觉/图像/视频（百炼 API） | 必填 |
| OPENROUTER_API_KEY | LLM 备用 | 必填 |
| FEISHU_APP_ID/SECRET | 飞书消息 | 必填 |
| GITHUB_TOKEN | GitHub 扫描/备份 | 必填 |
| SUPERMEMORY_API_KEY | 长期记忆 | 必填 |
| FIRECRAWL_API_KEY | 网页采集 | 可选 |

---

## 许可协议 / License

MIT License © 2026 Moye Tech

---

<p align="center">
  <sub>墨麟 OS — 一个人就是一个集团 / One Person, One Conglomerate</sub><br>
  <sub>Built on Hermes Agent · Powered by DeepSeek · Orchestrated by DARE</sub>
</p>
