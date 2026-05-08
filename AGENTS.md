<!--
墨麟 AI 集团 · 项目上下文（系统提示注入）

本文件在每次会话启动时注入系统提示。
它描述公司的执行模型、子公司-Worker 映射、常用 CLI 命令和治理规则。
所有名字与 company.toml 和 Worker 文件名严格对齐。

最新更新: 2026-05-06 — v5.0 全面同步
-->

# 墨麟 AI 集团 · 项目上下文

## 执行模型

```
Hermes（你，大脑）→ terminal工具（神经）→ python -m molib <command>（肌肉）→ 结果回传
```

- **纯思考/规划/决策** → 直接在对话中完成，不需要调 Python
- **需要真实执行**（发消息/生成文件/调用API/读写数据） → 用 terminal 执行 molib CLI
- **cron 定时任务** → Hermes cron 按 jobs.yaml 配置，加载对应 SKILL.md，执行后产生 relay/ 文件

## 企业架构（L0-L3 治理）

### L0 自动执行
低风险操作：自动回复、内容生成、数据采集、例行报告
→ 无需确认，直接做

### L1 通知
中风险操作完成后通知创始人
→ 做完后发飞书说你完成了什么

### L2 审批
高风险操作必须等创始人说"可以"
- 报价 > ¥500
- 承诺交付时间
- 对外发布内容（特别是付费渠道）
- 修改系统配置

### L3 坚决不做
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

# 设计（墨图设计）
python -m molib design image --prompt "描述" --style 写实

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
```

## 22家 Worker 与 20家子公司映射

### VP 营销（5家）
| 统一名称 | Worker 文件 | 核心能力 | 所属技能 |
|---------|------------|---------|---------|
| 墨笔文创 | content_writer.py | 文字内容创作、文案、公众号、博客 | molin-xiaohongshu, copywriting, content-strategy |
| 墨韵IP | ip_manager.py | IP衍生、商标、版权、品牌管理 | ai-taste-quality |
| 墨图设计 | designer.py | 图片/UI/封面/视觉设计 | molin-design, excalidraw, pixel-art |
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
🕐 08:00  第一棒：情报采集 (墨研竞情)
   daily_hot_report.py → relay/intelligence_morning.json

🕐 09:00  第二棒：内容生成 (墨笔文创)
   flywheel_content.py ← intelligence_morning.json → relay/content_flywheel.json

🕐 09:30  第三棒：分发策略 (墨测数据)
   flywheel_distribute.py ← content_flywheel.json → relay/distribution_plan.json

🕐 10:00  简报推送 (墨研竞情)
   daily_briefing.py ← intelligence_morning.json → relay/briefing_daily.md
```

飞轮接力关键规则：
1. 每棒必须先检查 relay/ 中是否有上一棒的文件
2. 如果没有，用上次可用数据或跳过该环节
3. 文件格式必须严格对齐（intelligence_morning.json → content_flywheel.json → distribution_plan.json）
4. 所有脚本使用纯Python标准库，零外部依赖
5. 日志备份至 ~/.hermes/daily_reports/

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

## 预算参考

- 每月 API 预算：¥1,360
- LLM：DeepSeek via OpenRouter（flash 级简单任务，pro 级复杂分析）
- 视觉：通义千问 qwen3-vl-plus（百炼 API）
- 视频：HappyHorse-1.0-T2V（百炼 API）
- 生图：千问百炼 qwen-image-2.0-pro
- GPT Image 2：通过你 ChatGPT 免费额度（codex CLI/auth.json）

## Cron 作业清单

默认全部暂停（零空转）：

| 时间 | 作业 | 功能 |
|:---:|:-----|:-----|
| 08:00 | 墨思情报银行 | 扫描博客/arXiv/MiroFish → 情报日报 |
| 09:00 | 墨迹内容工厂 | 情报→AI生成3篇内容 |
| 09:00 | CEO每日简报 | 汇总状态推送到你 |
| 10:00 | 墨增增长引擎 | SEO优化·增长分析 |
| 10:00 | 每日治理合规 | 审计+合规检查 |
| 12:00 | 系统状态快照 | 汇总产出+运营快照 |
| 15/45分 | 闲鱼消息检测 | 新消息AI自动回复 |
| 周五10:00 | 自学习进化 | GitHub扫描+技能更新 |

