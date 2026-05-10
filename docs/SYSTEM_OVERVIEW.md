# 墨麟OS (Molin-OS) — AI 一人公司操作系统

> **版本** v2.2 | **部署** Mac M2 8GB | **代码** 411 文件 · 79,474 行  
> **GitHub** [moye-tech/Molin-OS](https://github.com/moye-tech/Molin-OS)

---

## 目录

1. [系统概览](#1-系统概览)
2. [执行模型](#2-执行模型)
3. [企业架构与子公司](#3-企业架构与子公司)
4. [CEO 智能调度](#4-ceo-智能调度)
5. [核心模块清单](#5-核心模块清单)
6. [CLI 命令全集](#6-cli-命令全集)
7. [飞书集成](#7-飞书集成)
8. [飞轮管线](#8-飞轮管线)
9. [定时作业](#9-定时作业)
10. [记忆与知识系统](#10-记忆与知识系统)
11. [安全与治理](#11-安全与治理)
12. [备份与同步](#12-备份与同步)

---

## 1. 系统概览

墨麟OS 是一个 AI 驱动的一人公司操作系统，由以下三层构成：

```
┌─────────────────────────────────────────┐
│  Hermes Agent（大脑）                    │
│  推理 · 规划 · 调度 · 对话               │
├─────────────────────────────────────────┤
│  molib CLI（神经）                       │
│  python -m molib <command>              │
├─────────────────────────────────────────┤
│  22 家子公司 Worker（肌肉）               │
│  内容 · 设计 · 客服 · 交易 · 安全 · ...  │
└─────────────────────────────────────────┘
```

**三大设计原则**：
1. **纯 stdlib，零外部依赖** — 所有 molib 核心模块仅使用 Python 标准库
2. **Mac M2 本地优先** — 8GB 统一内存，Metal 加速，文件系统直通
3. **CEO 不是执行者** — 调度子公司并行工作，不自己包办

---

## 2. 执行模型

```
用户消息 → Hermes 推理（纯思考）
         → 需要执行时：terminal 工具
         → python -m molib <command>
         → 子公司 Worker 并行执行
         → 结果回传 → 飞书卡片输出
```

**关键规则**：
- 纯思考/规划/决策 → 在对话中完成，不调 Python
- 需要真实执行（发消息/调 API/读写文件）→ 调 molib CLI
- 3+ 子公司任务 → 并行调度，中间协调

---

## 3. 企业架构与子公司

### 5 VP + 20 家子公司

| VP | 子公司 | Worker | 核心能力 |
|----|--------|--------|---------|
| **VP 营销** | 墨笔文创 | content_writer | 文案/公众号/博客 |
| | 墨韵IP | ip_manager | IP/商标/品牌 |
| | 墨图设计 | designer | 图片/UI/封面 |
| | 墨播短视频 | short_video | 短视频脚本+生成 |
| | 墨声配音 | voice_actor | TTS/播客 |
| **VP 运营** | 墨域私域 | crm | CRM/用户分层 |
| | 墨声客服 | customer_service | 闲鱼自动客服 |
| | 墨链电商 | ecommerce | 订单/交易 |
| | 墨学教育 | education | 课程/培训 |
| **VP 技术** | 墨码开发 | developer | 软件开发 |
| | 墨维运维 | ops | 部署/DevOps |
| | 墨安安全 | security | 审计/红队 |
| | 墨梦AutoDream | auto_dream | AI实验/记忆蒸馏 |
| **VP 财务** | 墨算财务 | finance | 记账/预算 |
| **VP 战略** | 墨商BD | bd | 商务拓展 |
| | 墨海出海 | global_marketing | 出海/多语言 |
| | 墨研竞情 | research | 竞品/趋势 |
| **共同服务** | 墨律法务 | legal | 合同/合规 |
| | 墨脑知识 | knowledge | RAG/长期记忆 |
| | 墨测数据 | data_analyst | 数据分析 |
| **专项预置** | 墨投交易 | trading | 量化交易 |
| | Scrapling | scrapling_worker | 网页抓取 |
| | 9Router | router9 | 网络路由 |

---

## 4. CEO 智能调度

### 四层路由架构

```
Layer 0 ─ 问候/闲聊拦截 → 零成本直接回复
Layer 1 ─ 历史路由缓存 → Jaccard 相似度匹配
Layer 2 ─ LLM 语义路由 → DeepSeek 推理子公司画像
Layer 3 ─ 关键词兜底   → 完整关键词匹配表
```

### 三层需求拆解模型（v2.2 新增）

CEO 调度前必须完成三层分析：

| 层级 | 含义 | 示例（"闲鱼接单变现"） | 子公司 |
|------|------|----------------------|--------|
| **L1** 字面需求 | 用户说了什么 | 闲鱼能接哪些单 | research |
| **L2** 真实目标 | 真正想要的结果 | 快速变现，获取现金流 | shop + ip + data |
| **L3** 隐含约束 | 没说但必须满足 | 能力匹配 + 平台合规 | legal + knowledge |

**调度规则**：
- L1/L2 命中的子公司：必选
- L3 命中的：按风险决定
- 与三层均不相关：不选
- 涉及金钱/发布/外发：必选 legal
- 禁止行为：单子公司处理复杂任务、因关键词误触发、遗漏合规审查

---

## 5. 核心模块清单

### infra/ — 基础设施层

| 模块 | 文件 | 功能 |
|------|------|------|
| **BudgetGuard** | `budget_guard.py` | API 成本跟踪，¥100/日熔断 |
| **CocoIndex** | `coco_index.py` | 本地文件监听 SQLite 管道 |
| **DigitalHuman** | `digital_human.py` | M2 本地数字人 (Tier 1: ffmpeg+say) |
| **EventBus** | `event_bus.py` | 跨子公司事件发布/订阅 |
| **FeishuBitable** | `feishu_bitable.py` | 飞书多维表格自动写入 |
| **FeishuCardBuilder** | `gateway/feishu_card_builder.py` | 飞书互动卡片（11组件+6模板） |
| **FeishuNoiseFilter** | `feishu_noise_filter.py` | 8条正则可配置过滤 |
| **FeishuReplyPipeline** | `gateway/feishu_reply_pipeline.py` | 3消息有序发送 |
| **MemoryDistiller** | `memory/distiller.py` | 两层记忆蒸馏（工作→语义） |
| **FeishuGateway** | `gateway/platforms/feishu.py` | 飞书长连接+Webhook |

### agencies/ — 执行层

| 模块 | 文件 | 功能 |
|------|------|------|
| **SwarmBridge** | `swarm_bridge.py` | 跨子公司 Handoff 编排 |
| **TradingAgentsCN** | `trading_agents.py` | 多智能体交易分析 |
| **Handoff** | `handoff.py` | 16 领域自动路由 |
| **Planning** | `planning.py` | 结构化任务分解 |
| **Workers** | `workers/` (49文件) | 22 家子公司实现 |

### ceo/ — 决策层

| 模块 | 功能 |
|------|------|
| `intent_router.py` | 四层路由（739行） |
| `ceo_orchestrator.py` | CEO 编排器（658行） |
| `risk_engine.py` | 风险评估 |
| `dag_engine.py` | DAG 任务分解 |
| `sop_store.py` | SOP 记忆存储 |

---

## 6. CLI 命令全集

```bash
# ═══ 系统 ═══
python -m molib health                    # 系统健康检查
python -m molib help                       # 命令列表

# ═══ 内容创作 ═══
python -m molib content write --topic T --platform xhs
python -m molib content publish --platform xhs --draft-id ID
python -m molib design image --prompt "描述" --style 写实
python -m molib video script --topic T --duration 60s
python -m molib avatar create --text "你好" --image pic.jpg --voice Tingting
python -m molib avatar list-voices
python -m molib avatar check

# ═══ 运营 ═══
python -m molib xianyu reply --msg-id ID --content "回复"
python -m molib crm segment --by 活跃度
python -m molib order list --status pending

# ═══ 情报 ═══
python -m molib intel trending
python -m molib intel save --topic "AI Agent" --summary "..."
python -m molib intel firecrawl search --query Q
python -m molib intel firecrawl research --topic T

# ═══ 交易 ═══
python -m molib trading signal --symbol 000001 --market a-share
python -m molib trading analyze --symbol BTC/USDT --market crypto
python -m molib trading research --ticker TSLA

# ═══ 基础设施 ═══
python -m molib cost report               # API 成本报告
python -m molib cost check                # 预算检查
python -m molib index watch --dir PATH    # 文件监听索引
python -m molib index query --term "关键词"
python -m molib index sync
python -m molib memory distill            # 记忆蒸馏
python -m molib memory stats              # 记忆统计
python -m molib bitable schema            # 多维表格结构
python -m molib swarm list                # Swarm 通路
python -m molib swarm visualize           # ASCII 流程图

# ═══ 财务 ═══
python -m molib finance record --type expense --amount 100 --note "API"
python -m molib finance report

# ═══ 规划 ═══
python -m molib plan create --title "..." --description "..."
python -m molib plan decompose --plan-id xxx

# ═══ 知识 ═══
python -m molib query "FROM skills WHERE ..."
python -m molib manifest validate
```

---

## 7. 飞书集成

### 三层架构

```
┌─────────────────────────────────────┐
│ FeishuGateway (长连接 + Webhook)     │
│ feishu.py · 消息接收 · Token 管理    │
├─────────────────────────────────────┤
│ FeishuReplyPipeline (3消息流水线)     │
│ ① 思维链卡片 → ② 主回复 → ③ 详情     │
├─────────────────────────────────────┤
│ FeishuCardBuilder (JSON 组件引擎)     │
│ header · section · table · actions   │
└─────────────────────────────────────┘
```

### 3 消息回复结构（v2.2）

```
消息① · 思维链卡片
  🧠 CEO 推理过程
  ├ L1 字面需求
  ├ L2 真实目标
  ├ L3 隐含约束
  ├ 调度决策: research · shop · ip · data · legal
  └ ⏱ 87s · ¥0.016 · 5子公司 · 信心度 94%

消息② · 主回复卡片
  ✅ 任务完成
  ├ 🎯 核心结论
  ├ 💰 数据排名（表格）
  ├ ⚠️ 合规红线
  └ [查看全文] [导出报告] [继续提问]

消息③ · 子公司详情（每子公司一张）
  📊 research 完整报告
  📊 shop 完整报告
  📊 legal 完整报告
```

### 噪声过滤

8 条正则规则自动过滤飞书群消息：
- R0: 空消息 · R1: 纯表情 · R2: 系统消息（入群/退群）
- R4: 超短无意义 · R5: @机器人无内容 · R6: 纯数字日期
- R7: URL only · R8: 飞书富文本碎片

---

## 8. 飞轮管线

全自动内容生产链，通过 `relay/` 目录接力：

```
🕐 08:00  第一棒 · 情报采集（墨研竞情）
  daily_hot_report.py → relay/intelligence_morning.json

🕐 09:00  第二棒 · 内容生成（墨笔文创）
  flywheel_content.py ← intelligence_morning.json
  → relay/content_flywheel.json

🕐 09:30  第三棒 · 分发策略（墨测数据）
  flywheel_distribute.py ← content_flywheel.json
  → relay/distribution_plan.json

🕐 10:00  简报推送（墨研竞情）
  daily_briefing.py → relay/briefing_daily.md
```

**接力规则**：
1. 每棒先检查 relay/ 中上游文件
2. 无上游数据 → 跳过或降级
3. 格式严格对齐，纯 stdlib
4. 日志备份至 `~/.hermes/daily_reports/`

---

## 9. 定时作业

共计 **18 个 Cron 作业**，全部投递到飞书自动化控制群：

| 时间 | 作业 | 说明 |
|------|------|------|
| 03:00 | 系统备份 | 双轨备份 (GitHub + 本地 HDD) |
| 06:00 | 记忆蒸馏 (周一) | 周度经验提取 |
| 07:00 | 夸克云盘备份 | 增量云端备份 |
| 07:30 | API 成本预警 | 超 ¥80 阈值告警 |
| 08:00 | 墨思情报扫描 | 博客/论文/热点采集 |
| 09:00 | CEO 每日简报 | 昨日产出+今日待办 |
| 09:00 | 墨迹内容工厂 | 飞轮第二棒 |
| 09:15–21:45 | 闲鱼消息检测 | 每 30 分钟检查新消息 |
| 10:00 | 治理合规审计 | L1/L2 操作审计 |
| 10:00 | 墨增增长引擎 | 飞轮第三棒 |
| 10:00 | 技能库审计 (15日) | 30天未用技能归档 |
| 11:00 | 内容效果回收 | 阅读/点赞/收藏分析 |
| 12:00 | 系统健康快照 | 20 家子公司产出汇总 |
| 14:00 | 竞品监控 | 价格 + 内容对比 |
| 17:00 | CEO 下班简报 | 今日全量汇总 |
| 每2小时 | GitHub 双向同步 | pull --rebase → push |
| 周五 10:00 | 自学习进化 | 周度反思协议 |
| 每月1日 | 月度财务对账 | 收入/支出/利润 |

---

## 10. 记忆与知识系统

### 两层蒸馏架构（v2.1，Mac 8GB 适配）

```
┌──────────────────┐
│ 工作记忆 (Working) │  ← 最近 50 条对话摘要（SQLite）
│ 自动触发蒸馏 ↑     │
├──────────────────┤
│ 语义记忆 (Semantic)│  ← SOP 模式 · 经验法则 · 关键词标签
└──────────────────┘
```

**存储位置**：
```
~/.hermes/memory/distillation.db    # 蒸馏SQLite
~/.hermes/memory/chroma_db/         # 向量存储
~/.hermes/memory/long_term/         # 长期记忆
~/.hermes/coco_index.db             # 文件索引
```

**CocoIndex** — 本地文件知识管道：
- 监控 `~/Molin-OS/molib/` 和 `~/.hermes/relay/`
- SHA256 增量索引，SQLite 存证
- 支持关键词搜索 + 文件类型统计

---

## 11. 安全与治理

### 五级治理模型

| 级别 | 名称 | 行为 | 示例 |
|------|------|------|------|
| L0 | 自动执行 | 直接做 | 自动回复、内容生成 |
| L1 | 通知 | 做完发飞书 | 系统备份、日报 |
| L2 | 审批 | 等创始人确认 | 报价 >¥100、对外发布 |
| L3 | 董事会审批 | 全面评估 | 重大决策 |
| L4 | 绝对禁止 | 直接拒绝 | 涉及真实现金/转账 |

### BudgetGuard 成本盾

- 每日预算 ¥100，实时追踪 DeepSeek/Claude/Qwen 消耗
- 80% → warning，100% → blocked
- 持久化 JSON 日志，`molib cost report` 查看

---

## 12. 备份与同步

| 目标 | 方式 | 频率 | 内容 |
|------|------|------|------|
| **GitHub** | `git push` | 每 2h | 源码 + 配置（不含密钥） |
| **本地 HDD** | `rsync` | 每日 03:00 | 全量镜像（含密钥） |
| **夸克云盘** | `molin_backup.sh` | 每日 07:00 | 增量云端 |

恢复流程：
```bash
git clone https://github.com/moye-tech/Molin-OS.git ~/Molin-OS
rsync -av /Volumes/MolinOS/hermes/ ~/
# 一键恢复完毕
```

---

## 附录 A：系统环境

| 项目 | 值 |
|------|-----|
| 芯片 | Apple M2 |
| 内存 | 8 GB 统一内存 |
| Python | 3.11.15 |
| 系统 | macOS 26.4.1 |
| ffmpeg | 8.1.1 |
| 磁盘可用 | 169 GB |
| Hermes Agent | 部署于 `~/.hermes/hermes-agent/` |

## 附录 B：关键架构决策

| 决策 | 原因 |
|------|------|
| 纯 stdlib | Mac M2 离线可用，零 pip install |
| 不自己管理飞书 Token | Hermes Agent 内置 feishu 平台接管 |
| 两层记忆蒸馏 | 8GB 内存不支持三层，跳过情节记忆层 |
| 跳过 HeyGen/D-ID | 云端 ¥50+/月，Tier 1 ffmpeg+say 0 成本替代 |
| 跳过 DSPy | 每次 10K+ token，现有提示词已够好 |
| 跳过夸克/猪八戒 | 已有双轨备份 + 无 API |

---

*墨麟OS v2.2 — 2026-05-10 · 墨烨（尹建业）*
