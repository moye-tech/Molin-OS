# 墨麟 Hermes OS — 系统详细介绍

> 生成于 2026-05-04 · 基于当前运行中的系统状态
> GitHub: [moye-tech/Molin-OS](https://github.com/moye-tech/Molin-OS)

---

## 一、系统概述

**墨麟 Hermes OS** 是一个基于 Hermes Agent 构建的 AI 原生操作系统，将一家公司需要的全部能力——战略决策、内容创作、多平台发布、商业变现、情报监控、持续学习——封装为一个与 Hermes Agent 深度集成的技能体系。

```
你（CEO）+ Hermes OS（COO）= 全自动运转的一人公司
```

### 核心数据

| 维度 | 数值 |
|:-----|:----:|
| 技能数 | 270 个 SKILL.md |
| 子公司 | 22 家（19家有专属技能） |
| 定时作业 | 8 个（5个每日运行 + 1个高频 + 1个每周 + 1个每30分） |
| 总月收入目标 | ¥48,000（预算 ¥2,440/月） |
| 启动优先级 | T0 立即赚钱 → T1 1-2周启动 → T2 筹备中 |

---

## 二、技术架构

### 运行栈

```
Layer 1: 你（用户）
    │ 飞书 / Telegram / CLI
Layer 2: Hermes Agent（运行时）
    ├── DeepSeek V4 Pro（默认模型）
    ├── 270 SKILL.md（行为指引）
    ├── 30+ 内置工具（terminal / delegate_task / browser / cronjob / memory 等）
    └── 记忆系统（memory + session_search 跨会话检索）
        │
Layer 3: 墨麟 Hermes OS（技能体系 + 定时作业）
    ├── 三层归属（CEO / 子公司专用 / 共享）
    ├── 8 个 cronjob（飞轮协作）
    └── 治理规则（L0-L3）
```

### 关键设计决策

- **能力在技能层，不在 Python 代码层** — 真正的运行能力在 Hermes Agent 的工具链 + SKILL.md 中，不在 `molin/*.py` 中
- **三线飞轮协同** — 墨思（情报 08:00）→ 墨迹（内容 09:00）→ 墨增（增长 10:00）
- **分级治理** — L0 自动 / L1 AI 自审 / L2 人工确认 / L3 董事会审批

---

## 三、22 家子公司体系

| # | 子公司 | 职责 | 月收入目标 | 技能数 |
|:-:|:-------|:-----|:--------:|:------:|
| 01 | 墨智（AI研发） | AI 基础能力、MLOps、Agent 开发 | ¥2,000 | 28 |
| 02 | 墨码（软件工坊） | 软件开发、技术外包、代码实现 | ¥5,000 | 31 |
| 03 | 墨商BD（商务拓展） | 投标、方案、商务对接 | ¥3,000 | 7 |
| 04 | 墨影（IP孵化）🔥 | AI封面/热点采集/定时发布/多账户 | ¥5,000 | 5 | `molin-xiaohongshu` ⭐1.9k |
| 05 | 墨增（增长引擎） | 增长实验、A/B 测试、SEO/CRO | ¥3,000 | 19 | |
| 06 | 墨声（客服）🔥 | FAQ/工单/满意度/闲鱼自动化/多平台 | ¥1,000 | 1 | `molin-customer-service` |
| 07 | 墨域（私域CRM） | 私域运营、微信公众号、复购激活 | ¥3,000 | 3 |
| 08 | 墨单（订单交付） | 询盘处理、报价、交付管理 | ¥2,000 | 1 |
| 09 | 墨算（财务） | 成本核算、ROI 分析、预算 | ¥2,000 | 1 |
| 10 | 墨思（情报研究） | 行业研究、趋势洞察、竞品分析 | ¥2,000 | 12 |
| 11 | 墨律（法务）🔥 | 合同审查·风险评估·NDA·隐私·合规·TOS·谈判 | ¥1,000 | 2 | `molin-legal` ⭐1.2k |
| 12 | 墨盾（安全/QA） | 安全审计、代码审查、风险评估 | ¥1,000 | 11 |
| 13 | 墨品（产品设计） | MVP 设计、PRD、产品路线图 | ¥2,000 | 54 |
| 14 | 墨数（数据）🔥 | BI仪表盘/可视化/数据分析/归因 | ¥2,000 | 3 | `molin-vizro` ⭐3.7k |
| 15 | 墨维（运维） | CI/CD、GitHub、DevOps 基础设施 | ¥1,000 | 28 | |
| 16 | 墨育（教育）🔥 | AI辅导/课程设计/学习路径/测验 | ¥1,000 | 2 | `molin-education` (DeepTutor ⭐23.2k + human-skill-tree ⭐517) |
| 17 | 墨海（出海）🔥🔥 | 翻译/社媒/SEO/视频/合规 6合1 | ¥2,000 | 1 | `molin-global` |
| 18 | 墨脑（知识管理） | SOP、知识图谱、最佳实践沉淀 | ¥1,000 | 5 | |
| 19 | 墨迹（内容工厂） | 内容代写、短视频、PPT 制作 | ¥2,000 | 18 | |
| 20 | 墨投（量化交易）🔥🔥 | Freqtrade回测+TradingAgents多Agent分析 | ¥1,000 | 3 | `molin-trading` ⭐34k+ + `molin-trading-agents` ⭐65.9k |
| 21 | 墨商销售（闲鱼实业） | 闲鱼销售转化、C 端商品出售 | ¥5,000 | 3 |
| 22 | 墨工（设计） | AI 音乐、UI/UX、品牌视觉 | ¥2,000 | 10 |
| | **合计** | | **¥48,000** | **280** |

### 三层归属体系

| 层次 | 技能数 | 说明 |
|:----|:------:|:-----|
| 🔵 **CEO 核心层** | 29 | 战略、治理、调度、元技能，归你 + Hermes 掌握 |
| 🟢 **子公司专用层** | 240 | 映射到 19/22 家墨系子公司，每技能有明确的业务归属 |
| 🟡 **共享层** | 1 | 全系统通用的公共设施（ComfyUI 图像生成） |

---

## 四、定时作业（8 个运行的 cronjob）

> 所有作业通过 Hermes Agent 的 cronjob 工具管理，非系统 crontab。

### 工作日自动流水线

```
时间     | 作业                    | 子公司     | 说明
─────────────────────────────────────────────────────
08:00  🔍 墨思情报银行           | 墨思       | 扫描5源→提炼→高价值存入memory
09:00  📝 墨迹内容工厂飞轮       | 墨迹       | 接墨思情报→生产内容→memory接力
09:00  📋 CEO每日简报            | CEO        | 昨日产出+今日待办+系统状态
10:00  📈 墨增增长引擎接力       | 墨增       | 接墨迹内容→投放策略→SEO优化
10:00  🛡️ 每日治理合规检查       | 墨盾       | L0-L3审计→L2待审批项上报
12:00  📊 系统状态快照汇总       | 墨算+墨数  | 全子公司24h产出→运营统计
15/45 🛒 闲鱼消息检测（每30分） | 墨商销售   | 按L0/L1/L2分级处理消息
```

### 每周熔断

```
周五10:00 🧬 自学习循环            | CEO        | 扫描GitHub/HN/PH→自动更新技能→清理过时→进化报告
```

### 飞轮链路

```
墨思(08:00) ──情报──→ 墨迹(09:00) ──内容──→ 墨增(10:00) ──方案──→ CEO披露(12:00)
```

---

## 五、治理规则（L0-L3）

| 级别 | 预算上限 | 审批方式 | 示例场景 |
|:---:|:--------:|:---------|:---------|
| L0 | ¥0 | 自动执行 | 内容生成、情报扫描、系统内部操作 |
| L1 | ≤ ¥10 | AI 自审 | SKILL.md 更新、自动回复 |
| L2 | ≤ ¥100 | 人工确认（你） | 闲鱼砍价 >20% 、推广费用、退款请求 |
| L3 | ≤ ¥1,000 | 董事会审批 | 修改 API Key、删除技能、预算超限 |

每日 10:00 治理合规检查作业自动执行审计，L2 事项在报告中明确标注"待你审批"。

---

## 六、技能能力分类

### 🔧 执行引擎类

| 能力 | 实现方式 | 状态 |
|:-----|:---------|:----:|
| LLM 调用 | DeepSeek V4 Pro via OpenRouter | ✅ |
| 代码执行 | terminal（Python/Bash/Node.js） | ✅ |
| 文件操作 | write_file / read_file / patch / search_files | ✅ |
| 浏览器自动化 | browser_navigate / click / type / vision | ✅ |
| 并行任务 | delegate_task（最多 3 子 Agent 并发） | ✅ |
| 定时任务 | cronjob 引擎 | ✅ |
| 跨会话记忆 | memory + session_search | ✅ |
| 消息推送 | send_message → 飞书/Telegram/Discord/WhatsApp | ✅ |

### 📦 业务能力类

| 领域 | 技能数 | 代表技能 |
|:-----|:------:|:---------|
| 产品管理（墨品） | 54 | pm-create-prd, pm-user-stories, pm-okrs, pm-ab-test 等全系列 |
| 软件开发（墨码） | 31 | test-driven-development, systematic-debugging, plan, writing-plans |
| AI 研发（墨智） | 28 | llama-cpp, vllm, dspy, unsloth, axolotl, huggingface-hub |
| 系统运维（墨维） | 28 | github-pr-workflow, google-workspace, linear, notion, himalaya |
| 增长营销（墨增） | 19 | claude-seo, seo-audit, content-strategy, page-cro, copywriting |
| 内容创作（墨迹） | 18 | xiaohongshu-content-engine, manim-video, ffmpeg-video-engine, p5js |
| 情报研究（墨思） | 12 | arxiv, blogwatcher, world-monitor, maigret-osint, polymarket |
| 安全质量（墨盾） | 11 | sql-injection-testing, vulnerability-scanner, godmode |
| 创意设计（墨工） | 10 | ascii-art, pixel-art, architecture-diagram, excalidraw |
| 商务BD（墨商BD） | 7 | agent-sales-proposal-strategist, agent-finance-financial-analyst |
| 知识管理（墨脑） | 5 | mempalace, self-learning-loop, skill-discovery, obsidian |
| IP 孵化（墨影） | 4 | xiaohongshu-content-engine, pixelle-video, baoyu-comic |
| 销售变现 | 3 | xianyu-automation, marketing-skills-cro |

---

## 七、部署说明

### 环境要求

- Python ≥ 3.10
- Hermes Agent（运行底座）
- Git

### 部署流程

```bash
# 1. 安装 Hermes Agent
pip install hermes-agent

# 2. 克隆仓库
git clone https://github.com/moye-tech/Molin-OS.git
cd Molin-OS

# 3. 同步技能
bash tools/sync-skills.sh

# 4. 安装 CLI（可选）
pip install -e .

# 5. 配置
cp .env.example ~/.molin/.env
# 编辑 ~/.molin/.env 填入 API Key

# 6. 验证
bash tools/healthcheck.sh
```

### 技能同步说明

系统的真正能力在 Hermes Agent 的运行时环境中。`skills/` 目录是本系统对 Hermes Agent 的配置——每次同步后 Agent 获得新的行为指引，所有 22 子公司技能自动可用，无需重启 Agent。

### 定时作业恢复

部署后需手动创建 cronjob（当前 cronjob 存储在 Hermes Agent 内部，非仓库中）。在 Hermes 对话中执行：

```
使用 cronjob(action='create', ...) 按 cron/jobs.yaml 中的配置逐个创建。
```

---

## 八、2026-05-04 全量整改记录

| 维度 | 改动 | 数量 |
|:-----|:-----|:----:|
| 技能体系 | molin_owner 全量标记（三层体系） | 270 个 |
| 仓库同步 | README 标准化 + 技能索引 + 部署脚本 + cron 配置 | 12 个文件 |
| 定时作业 | 新建 7 个 + 升级 1 个 | 8 个 |
| 飞书 UX | 消息格式化 skill（噪声过滤 + 卡片 + 分级） | 1 个 skill |
| 子公司配置 | 六层垂直化文档 + cronjob 模板 | 2 个文档 |
| 治理执行 | 闲鱼分级处理 + 每日合规审计 | 2 个 cronjob |
| 自进化 | Integrate 自动更新 skill + Retire 清理 | 1 个 cronjob 升级 |
| 覆盖评估报告 | 15/15 缺陷全部解决 | 100% |

---

## 九、文件索引

| 仓库路径 | 说明 |
|:---------|:-----|
| `skills/` | 270 个 SKILL.md 技能文件（54 个领域目录） |
| `molin/` | Python 包（CLI 入口、Agent 基类、内容/发布/情报模块） |
| `config/company.yaml` | 22 子公司架构、预算、变现矩阵 |
| `config/governance.yaml` | L0-L3 治理规则、审计、安全策略 |
| `config/channels.yaml` | 多平台发布配置 |
| `cron/jobs.yaml` | 全部 8 个定时作业定义 |
| `tools/sync-skills.sh` | 技能同步部署脚本 |
| `tools/healthcheck.sh` | 环境健康检查脚本 |
| `docs/skills-index.md` | 270 技能全量索引（按子公司分组） |
| `docs/Hermes_Runtime_能力文档.md` | 运行时真实能力说明 |
| `docs/subsidiary-deep-config.md` | 子公司六层垂直化配置中心 |
| `docs/cronjob-template.md` | 新子公司 cronjob 创建模板 |
| `docs/hermes_os_evaluation_report.html` | 架构评估与升级报告（原始诊断） |
