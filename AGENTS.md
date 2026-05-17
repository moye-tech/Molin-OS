<!--
墨麟 AI 集团 · 项目上下文（系统提示注入）

本文件在每次会话启动时注入系统提示。
它描述公司的执行模型、子公司-Worker 映射、常用 CLI 命令和治理规则。
所有名字与 company.toml 和 Worker 文件名严格对齐。

注意：治理级别定义以 config/governance.yaml 为单一真相源。
     本文件中治理相关描述仅作摘要参考，如需精确配置请查阅 governance.yaml。

最新更新: 2026-05-06 — v5.0 全面同步
-->

# 墨麟 AI 集团 · 项目上下文

## 核心文档体系

系统从多文件分散模式升级为 **3 个核心文件**：

| 文件 | 用途 | 地位 |
|------|------|------|
| `SYSTEM.md` | 主脑文档 — 所有 Agent SOP 合并为模块块 | 单一真相源 |
| `AGENT_REGISTRY.md` | Agent 轻量索引 | 快速导航 |
| `scheduler.yaml` | 统一调度配置 | 唯一调度源 |
| `molib/memory/retriever.py` | 记忆检索入口 | 知识决策核心 |

**重要**: Agent SOP 不再放在独立 skill 文件中。所有 SOP 定义见 `SYSTEM.md`。
skill 文件继续存在（作为专业知识库），但执行流程以 `SYSTEM.md` 为准。

## 执行模型

```
Hermes（你，大脑）→ terminal工具（神经）→ python -m molib <command>（肌肉）→ 结果回传
```

- **纯思考/规划/决策** → 直接在对话中完成，不需要调 Python
- **需要真实执行**（发消息/生成文件/调用API/读写数据） → 用 terminal 执行 molib CLI
- **cron 定时任务** → Hermes cron 按 jobs.yaml 配置，加载对应 SKILL.md，执行后产生 relay/ 文件

## 企业架构（治理级别）

治理级别定义见 `config/governance.yaml`（单一真相源）。摘要如下：

### L0 自动执行 (auto)
低风险操作：自动回复、内容生成、数据采集、例行报告
→ 无需确认，直接做

### L1 通知 (notify)
中风险操作完成后通知创始人
→ 做完后发飞书说你完成了什么

### L2 审批 (approve)
高风险操作必须等创始人说"可以"
- 报价 > ¥100（超预算上限需审批）
- 承诺交付时间
- 对外发布内容（特别是付费渠道）
- 修改系统配置

### L3 董事会审批 (board_approve)
重大决策需全面评估
→ 需创始人/董事会全面评估后执行

### L4 绝对禁止 (forbidden)
涉及真实现金/转账/支付/改价的操作
→ 绝不碰，直接拒绝

## 统一 CLI 入口

所有执行通过 `python -m molib <command> [args...]` 调用：

```
# 通用命令
python -m molib health              # 系统健康检查
python -m molib help                 # 查看所有命令

# 内容创作（墨笔文创）
python -m molib content write --topic "主题" --platform xhs
python -m molib content publish --platform xhs --draft-id xxx

# 设计（墨图设计 v2.2）
python -m molib design image --prompt "描述" --style 写实
python -m molib design web --prompt "墨麟AI集团官网" --action landing_page --ds apple
python -m molib design web --prompt "销售数据看板" --action dashboard --ds stripe
python -m molib design web --prompt "融资计划" --action pitch_deck --ds airbnb

# 短视频（墨播短视频）
python -m molib video script --topic "主题" --duration 60s

# 私域运营（墨域私域）
python -m molib crm segment --by 活跃度
python -m molib crm push --segment 高活跃 --content "消息"

# 客服（墨声客服）
python -m molib xianyu reply --msg-id xxx --content "回复内容"

# 情报（墨研竞情）
python -m molib intel trending
python -m molib intel save --topic "AI Agent" --summary "..."

# 财务（墨算财务）
python -m molib finance record --type expense --amount 100 --note "API费用"
python -m molib finance report

# 电商（墨链电商）
python -m molib order list --status pending
python -m molib order status --order-id xxx

# 数据（墨测数据）
python -m molib data analyze --file xxx.csv

# 交易（墨投交易）
python -m molib trading signal --symbol BTC/USDT
python -m molib trading analyze --market-type crypto --symbol BTC/USDT
python -m molib trading research --ticker BTC

# Handoff自动路由
python -m molib handoff list                     # 查看所有可用Worker
python -m molib handoff route --task "内容创作"  # 自动路由到匹配Worker
python -m molib handoff history                  # 查看handoff执行历史

# 规划分解
python -m molib plan create --title "..." --description "..."
python -m molib plan decompose --plan-id xxx

# 技能商店安装器
python -m molib skill-store install --package xxx
python -m molib skill-store list

# 核心元技能（自动加载，也可手动调用）
python -m molib ghost-os health              # 系统健康检查（ghost-os）
python -m molib ghost-os cron list           # Cron作业状态
python -m molib ghost-os diagnose            # 环境诊断
python -m molib self-learning reflect        # 手动触发反思协议（self-learning-loop）
python -m molib self-learning session-id XXX # 反思指定会话
python -m molib karpathy scan --topic "主题"  # 情报扫描（karpathy-autoresearch）
python -m molib karpathy depth --level deep  # 深度研究模式
python -m molib moneymaker assess --idea "..." # 变现评估（moneymaker-turbo）
python -m molib moneymaker score --plan xxx  # 变现路径评分
```

## 22家 Worker 与 20家子公司映射

### VP 营销（5家）
| 统一名称 | Worker 文件 | 核心能力 | 所属技能 |
|---------|------------|---------|---------|
| 墨笔文创 | content_writer.py | 文字内容创作、文案、公众号、博客 | molin-xiaohongshu, copywriting, content-strategy |
| 墨韵IP | ip_manager.py | IP衍生、商标、版权、品牌管理 | ai-taste-quality |
| 墨图设计 | designer.py | Open Design全栈(149设计系统×134技能) + FLUX.2生图 + 封面/UI | molin-design, excalidraw, pixel-art, open-design |
| 墨播短视频 | short_video.py | 短视频脚本+生成 | ffmpeg-video-engine, pixelle-video-engine |
| 墨声配音 | voice_actor.py | AI语音合成、播客制作 | molin-audio-engine, songwriting |

### VP 运营（4家）
| 统一名称 | Worker 文件 | 核心能力 | 所属技能 |
|---------|------------|---------|---------|
| 墨域私域 | crm.py | CRM、用户分层、社群运营 | molin-crm, social-push-publisher |
| 墨声客服 | customer_service.py | 自动化客服（消息检测→回复） | molin-customer-service, xianyu-automation |
| 墨链电商 | ecommerce.py | 订单管理、交易、电商平台 | molin-order |
| 墨学教育 | education.py | 课程设计、学习路径、辅导 | molin-education, ranedeer-ai-tutor |

### VP 技术（4家）
| 统一名称 | Worker 文件 | 核心能力 | 所属技能 |
|---------|------------|---------|---------|
| 墨码开发 | developer.py | 软件开发、代码编写 | agent-engineering-backend-architect, cli-anything |
| 墨维运维 | ops.py | 服务器、部署、DevOps | ghost-os, cli-anything, opensre-sre-agent |
| 墨安安全 | security.py | 代码审计、安全评估 | red-teaming, ag-vulnerability-scanner |
| 墨梦AutoDream | auto_dream.py | AI自动化实验、快速原型 | deep-dream-memory, self-learning-loop |

### VP 财务（1家）
| 统一名称 | Worker 文件 | 核心能力 |
|---------|------------|---------|
| 墨算财务 | finance.py | 记账、预算、成本控制 |

### VP 战略（3家）
| 统一名称 | Worker 文件 | 核心能力 | 所属技能 |
|---------|------------|---------|---------|
| 墨商BD | bd.py | 商务拓展、合作洽谈 | molin-bd-scanner, agent-sales-deal-strategist |
| 墨海出海 | global_marketing.py | 多语言、全球化、出海运营 | molin-global, weblate-localization |
| 墨研竞情 | research.py | 竞争分析、趋势研究 | karpathy-autoresearch, world-monitor, mirofish-trends |

### 共同服务（3家）
| 统一名称 | Worker 文件 | 核心能力 | 所属技能 |
|---------|------------|---------|---------|
| 墨律法务 | legal.py | 合同审查、合规、风险评估 | molin-legal |
| 墨脑知识 | knowledge.py | 知识管理、RAG、长期记忆 | molin-memory, supermemory, gitnexus |
| 墨测数据 | data_analyst.py | 数据分析、测试、质量 | molin-data-analytics, molin-vizro |

### 专项预置（2家 — 非标准20家，专用领域）
| Worker | 核心能力 | 说明 |
|:-------|:---------|:-----|
| trading.py | 量化交易策略·信号·回测 | 已激活，CLI: `python -m molib trading` |
| scrapling_worker.py | 网页抓取·数据采集 | 吸收自 Scrapling |
| router9.py | 网络流量·多路路由 | 吸收自 9router |

## Handoff 自动路由

16家子公司已注册Handoff，支持全自动任务路由：

```python
# Python 调用
from molib.agencies.handoff import HandoffManager
result = HandoffManager.route("帮我写一篇小红书文案", input_data)

# CLI 调用
python -m molib handoff route --task "帮我做数据分析"
```

支持：内容创作、设计、开发、运维、安全、CRM、客服、数据、交易、BD、财务、法务、教育、情报、出海、知识管理 共16个领域。
路由失败时自动降级返回，不会抛出异常。

## 规划分解

```python
from molib.agencies.planning import PlanningTool

pt = PlanningTool()
task = pt.decompose_task("开发一个AI封面生成器", ["墨图设计", "墨码开发", "墨维运维"])
# 返回 {tasks: [...], dependencies: {...}, total_duration: "..."}

# CLI
python -m molib plan decompose --plan-id xxx
```

## 飞轮管线（内容自动化链）

系统每日自动运行的飞轮管线，三棒全自动通过 relay/ 目录接力：

```
🕐 08:00  第一棒：情报银行 (墨思情报)
   Agent → relay/intelligencemorning.json
   Cron: bf670fd0a49d · skills: blogwatcher+arxiv+firecrawl

🕐 09:20  第二棒：内容工厂 (墨迹内容)
   Agent ← intelligencemorning.json → 生成内容+SEO → relay/
   Cron: 8d3480b7a03e · 前置检查: 上游文件存在且<90分钟

🕐 10:45  第三棒：增长引擎 (墨增增长)
   Agent ← relay/内容文件 → SEO优化+审计+追踪+策略调整
   Cron: e2d424db0a17 · 前置检查: 上游文件存在且<90分钟
```

飞轮接力关键规则：
1. 每棒必须先检查 relay/ 中是否有上一棒的文件（flywheel_guard.check_upstream）
2. 如果没有且超过90分钟 → 发T4飞书告警"飞轮断裂"，退出不空转
3. 第1棒失败 → 第2棒自动断链告警 → 第3棒也会断链（级联保护）
4. 所有Cron任务prompt禁止直接调用FeishuCardSender → 统一通过Enforcer
5. Cron输出格式: cron-output-formatter卡片规范（加粗标题+hr分割+note脚注）

## 记忆系统

统一通过 `molib/memory/retriever.py` 检索。
双源检索：Obsidian（结构化知识 `产出/`）+ Supermemory（语义块）。

四层架构：
```
🔴 L1 工作记忆     → 飞书对话上下文（24h清理）
🟡 L2 情节记忆     → Supermemory（30天未调用→蒸馏）
🟢 L3 语义记忆     → Obsidian `产出/`（永久）
🔵 L4 程序记忆     → SKILL.md 技能文件（版本化管理）
```

Agent 接入：
```python
from molib.memory.retriever import retrieve_context
context = retrieve_context(query="转化率提升", agent_name="edu")
```

Agent 输出通过 `molib/memory/output_writer.py` 强制结构化模板写入。

## 记忆系统文件位置

```
~/.hermes/memory/chroma_db/        # 向量记忆存储（ChromaDB）
~/.hermes/memory/vector_memory.db  # 结构化记忆（SQLite）
~/.hermes/dream/                   # 墨梦AutoDream的记忆蒸馏产出
~/.hermes/daily_reports/           # 每日数据报表存档
~/.hermes/memory/long_term/        # claude-mem 长期记忆
~/.hermes/events/                  # FileEventBus 事件
~/.hermes/os/                      # Hermes Agent 系统文件
~/.hermes/plugins/claude-mem/      # claude-mem 插件
~/hermes-os/docs/                  # 系统文档
```

## 系统关键文件位置

```
~/.hermes/os/                             # Hermes Agent 系统
~/hermes-os/                              # 工作目录
~/hermes-os/SOUL.md                       # CEO 认知框架（灵魂文件）
~/hermes-os/AGENTS.md                     # 公司上下文（本文件）
~/hermes-os/config/company.toml           # 子公司映射（唯一配置源）
~/hermes-os/molib/                        # Python 执行包（129文件）
~/hermes-os/molib/__main__.py             # CLI 统一入口
~/hermes-os/molib/ceo/                    # CEO引擎（10模块）
~/hermes-os/molib/agencies/               # 执行层（handoff/planning/workers）
~/hermes-os/molib/shared/                 # 共享层（AI/分析/内容/知识/发布/存储）
~/hermes-os/bots/                         # 24个机器人脚本
~/hermes-os/business/                     # 9个商业化方案
~/hermes-os/cron/jobs.yaml                # 8个定时作业
~/hermes-os/relay/                        # 飞轮接力数据
~/hermes-os/docs/                         # 27个系统文档
```

## Agent SOP 体系（v2.0 — 2026-05-17 — 主脑文档模式）

**架构升级**: 从多文件 SOP → 单一主脑文档 `SYSTEM.md`。

所有 Agent SOP 定义在 `SYSTEM.md` 中作为模块块存在。
`AGENT_REGISTRY.md` 提供轻量索引。
`scheduler.yaml` 是唯一调度源。

每个 Agent 统一采用四层架构：

```
Agent
 ├── SOP Block  —— 在 SYSTEM.md 中定义
 ├── Cron        —— 在 scheduler.yaml 中定义
 ├── KPI         —— 由 kpi-tracker 采集
 └── Memory      —— 由 retriever.py 检索 + output_writer.py 写入
```

缺失：墨域私域（需 LINE/Bottender 基础设施）

每个 Agent 统一采用四层架构：

```
Agent
 ├── SOP Layer    —— 标准作业程序（skill 文件）
 ├── Cron Layer   —— 自动循环周期（cronjob 工具）
 ├── KPI Layer    —— 结果监控指标
 └── Feedback Layer —— 反思优化闭环
```

### 覆盖状态

| VP | 子公司 | 状态 |
|----|--------|------|
| 营销 | 墨笔文创 / 墨韵IP / 墨图设计 / 墨播短视频 / 墨声配音 | ✅ SYSTEM.md 已定义 |
| 运营 | 墨域私域 | ❌ 待 LINE 基建 |
| 运营 | 墨声客服 / 墨链电商 / 墨学教育 | ✅ SYSTEM.md 已定义 |
| 技术 | 墨码开发 / 墨维运维 / 墨安安全 / 墨梦AutoDream | ✅ SYSTEM.md 已定义 |
| 财务 | 墨算财务 | ✅ SYSTEM.md 已定义 |
| 战略 | 墨商BD / 墨海出海 / 墨研竞情 | ✅ SYSTEM.md 已定义 |
| 共同服务 | 墨律法务 / 墨脑知识 / 墨测数据 | ✅ SYSTEM.md 已定义 |

### 共享层
| 组件 | 作用 |
|------|------|
| gatekeeper-sop | 全流量合规门禁 + QA 终检 |
| kpi-tracker | 效能/质量/成本 KPI 追踪 |
| memory/retriever.py | 统一记忆检索 |
| memory/output_writer.py | 结构化输出 + 双写 |

### 共享 SOP 技能
| 技能 | 作用 | 引用方 |
|------|------|--------|
| gatekeeper-sop | 全流量合规门禁 + QA 终检 | 所有对外输出 Agent |
| kpi-tracker | 效能/质量/成本 KPI 追踪 | 所有 Agent + 22:00复盘 |

### 经营节奏

调度配置见 `scheduler.yaml`（唯一真相源）。

| 时间 | Agent | 任务 | 加载技能 |
|------|-------|------|----------|
| 06:00 周一 | autodream | 垂直学习扫描 | vertical-learning-sop |
| 06:00 每日 | research | 情报采集 | — |
| 03:00 周一 | security | 安全审计 | security-sop-pack |
| 08:00 | bd | 商机扫描 | — |
| 08:30 工作日 | content | 内容生产 | content-sop-pack |
| 10:00 周一 | ip | IP矩阵规划 | — |
| */15分 | service | 闲鱼客服 | service-sop-pack |
| 21:00 每日 | ecommerce | 日对账 | — |
| 22:00 每日 | data/kpi | KPI采集+复盘 | pack+gatekeeper+kpi-tracker |
| 22:10 每日 | kpi-tracker | KPI看板 | script |
| 21:00 周日 | content | 增长复盘 | kpi-tracker+growth+pack |
| 23:00 每日 | finance | 财务日报 | finance-sop-pack+kpi-tracker |
| 09:00 1号 | kpi-tracker | 月度规划 | kpi-tracker+finance |

### 飞轮管线

```
06:30 情报采集     → research-sop-pack
08:00 选题池       → content-sop-lead
08:30 内容生产     → content-sop-pack
09:00 短视频脚本   → video-sop-pack + voice-sop-pack
09:30 配图/封面    → design-sop-pack
10:00 本地化出海   → global-marketing-sop-pack
15分钟 闲鱼客服    → service-sop-pack
22:00 复盘+KPI     → kpi-tracker + gatekeeper-sop
23:00 财务日报     → finance-sop-pack + data-sop-pack
周日 增长实验      → content-sop-growth + autodream-sop-pack
```

创建新 Agent 时参考 `SYSTEM.md` 的 SOP 模块块格式，在 SYSTEM.md 中追加 Agent 模块即可。

## 预算参考

- 每月 API 预算：¥1,360
- LLM：DeepSeek via OpenRouter（flash 级简单任务，pro 级复杂分析）
- 视觉：通义千问 qwen3-vl-plus（百炼 API）
- 视频：HappyHorse-1.0-T2V（百炼 API）
- 生图：千问百炼 qwen-image-2.0-pro
- GPT Image 2：通过你 ChatGPT 免费额度（codex CLI/auth.json）

## Cron 作业清单

调度以 `scheduler.yaml` 为准。Hermes 当前 14 个活跃 Cron job：

| 时间 | 作业 | 功能 |
|:---:|:-----|:-----|
| 每小时 | 记忆同步 | script |
| 每15分 | 跨线请求轮询 | script |
| 每30分 | 系统健康检查 | ops-sop-pack |
| 02:00 | Git备份 | script |
| 03:00 周一 | 安全审计 | security-sop-pack |
| 06:00 周一 | 垂直学习扫描 | vertical-learning-sop |
| 07:00 | arXiv论文 | script |
| 08:00 | BD商机扫描 | — |
| 08:30 工作日 | 内容生产 | content-sop-pack |
| 22:00 | KPI采集+复盘 | pack+gatekeeper+kpi-tracker |
| 22:10 | KPI看板 | script |
| 23:00 | 财务日报 | finance-sop-pack |
| 21:00 周日 | 增长复盘 | kpi-tracker+growth+pack |
| 09:00 1号 | 月度规划 | kpi-tracker+finance |

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **hermes-os** (21383 symbols, 30183 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/hermes-os/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/hermes-os/context` | Codebase overview, check index freshness |
| `gitnexus://repo/hermes-os/clusters` | All functional areas |
| `gitnexus://repo/hermes-os/processes` | All execution flows |
| `gitnexus://repo/hermes-os/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->

## 任务→Worker 组合矩阵（CEO 委托必查）

收到产出类任务时，按此表确定单Worker还是WorkerChain：

| 触发关键词/场景 | 单Worker / 首选 | WorkerChain（推荐组合） | CLI命令 |
|:---|:---|:---|:---|
| 写文案/写笔记/小红书/公众号 | 墨笔文创 | 墨研竞情→墨笔文创→墨图设计 | `molib content write --topic X --platform xhs` |
| 做封面/出图/设计/生图 | 墨图设计 | 墨笔文创→墨图设计（文案+封面） | `molib design image --prompt X` |
| 视频脚本/抖音/短视频 | 墨播短视频 | 墨研竞情→墨播短视频→墨声配音 | `molib video script --topic X` |
| 配音/TTS/播客/音频 | 墨声配音 | 独立完成为主 | `molib handoff route --task "配音"` |
| 竞品分析/市场调研/趋势/情报 | 墨研竞情 | 墨研竞情→墨测数据→墨笔文创（研究报告） | `molib intel trending` / `molib intel save --topic X` |
| 课程设计/逻辑思维/教程/教育 | 墨学教育 | 墨研竞情→墨学教育→墨笔文创 | `molib handoff route --task "课程设计"` |
| 闲鱼上架/商品发布/订单 | 墨链电商 | 墨笔文创→墨图设计→墨链电商 | `molib order list` / `molib handoff route --task "电商上架"` |
| 私域/用户运营/社群/复购 | 墨域私域 | 墨测数据→墨域私域→墨笔文创（用户分层+触达文案） | `molib crm segment --by 活跃度` |
| 客服/闲鱼回复/自动回复 | 墨声客服 | 独立完成为主 | `molib xianyu reply --msg-id X` |
| 写代码/开发/技术实现 | 墨码开发 | 墨码开发→墨安安全→墨维运维（开发+审查+部署） | `molib handoff route --task "开发"` |
| 出海/台湾/繁体/Vocus/LINE | 墨海出海 | 墨研竞情→墨笔文创→墨海出海→墨律法务 | `molib handoff route --task "出海本地化"` |
| 记账/财务/成本/预算 | 墨算财务 | 独立完成为主 | `molib finance record --type expense` / `molib finance report` |
| 合同/法务/隐私/合规 | 墨律法务 | 墨律法务→墨算财务（合同+报价核算） | `molib handoff route --task "法务审查"` |
| 数据分析/报表/BI/测试 | 墨测数据 | 墨测数据→墨笔文创（数据+报告） | `molib data analyze --file X.csv` |
| BD/合作/变现/收入 | 墨商BD | 墨研竞情→墨商BD→墨律法务 | `molib handoff route --task "BD拓展"` |
