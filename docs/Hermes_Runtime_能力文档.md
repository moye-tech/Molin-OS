# Hermes Agent 运行态能力文档

> 本文档描述墨麟 Hermes OS 在 Hermes Agent 运行时环境下的**真实能力**。
> 与 `molin/*.py` 的纯代码实现不同，这里记录的是 Agent + 技能 + 工具的联合能力。

---

## 一、系统架构（运行态）

```
你（用户）→ 飞书/Felica/CLI
    │
    ▼
Hermes Agent（运行时）
    ├── DeepSeek V4 Pro（默认模型）
    ├── 266 SKILL.md（指导行为）
    ├── 32+ 内置工具（terminal/delegate_task/browser/cronjob等）
    ├── 持久记忆（memory + session_search）
    └── 定时调度（cronjob 引擎）
```

**关键区别：** 真正的运行能力不在 `molin/*.py` 中，而在：
- Hermes Agent 本身的工具链（terminal, delegate_task, cronjob, memory, etc.）
- 266 个 SKILL.md 技能（指导 Agent 在不同场景下的行为）
- 记忆系统（memory 工具 + session_search 跨会话检索）

---

## 二、能力清单

### 2.1 执行引擎

| 能力 | 实现方式 | 状态 |
|:-----|:---------|:----:|
| LLM 调用 | DeepSeek V4 Pro via OpenRouter | ✅ 运行中 |
| 代码执行 | `terminal` 工具（Python/Bash/Node.js） | ✅ 运行中 |
| 文件操作 | `write_file`/`read_file`/`patch`/`search_files` | ✅ 运行中 |
| 浏览器自动化 | `browser_navigate`/`click`/`type`/`vision` | ✅ 运行中 |
| 并行任务 | `delegate_task` 最多 3 子Agent并发 | ✅ 运行中 |
| 定时任务 | `cronjob` 引擎（cron 表达式/间隔/一次性） | ✅ 运行中 |
| 跨会话记忆 | `memory` 工具（用户偏好+环境事实） | ✅ 运行中 |
| 历史检索 | `session_search` 全文检索历史会话 | ✅ 运行中 |
| 图片分析 | `vision_analyze` AI 视觉理解 | ✅ 运行中 |
| 语音合成 | `text_to_speech` 多平台语音消息 | ✅ 运行中 |
| 消息推送 | `send_message` → 飞书/Telegram/Discord/WhatsApp等 | ✅ 运行中 |

### 2.2 定时作业（当前运行中）

| 作业 | 调度 | 功能 |
|:-----|:----|:-----|
| 自学习每周循环 | 每周五 10:00 | 扫描GitHub/HN/PH → 提炼洞察 → 更新技能 → 汇报 |
| 墨迹内容工厂 | 每日 09:00 | 获取热点 → 评估方向 → 生产内容 → 沉淀 |

### 2.3 技能体系（266个SKILL.md，三层归属）

| 层 | 数量 | 说明 |
|:--|:----:|:-----|
| 🔵 CEO 核心 | 27 | 战略、治理、调度、元技能 |
| 🟢 子公司专用 | 238 | 映射到 19/22 家墨系子公司 |
| 🟡 共享 | 1 | 全系统通用公共设施 |

### 2.4 子公司能力覆盖

| 子公司 | 技能数 | 核心能力 |
|:-------|:------:|:---------|
| 墨品（产品设计） | 54 | PRD、需求分析、用户研究、AB测试、定价策略 |
| 墨码（软件工坊） | 31 | TDD、调试、代码审查、架构设计、Git工作流 |
| 墨智（AI研发） | 28 | MLOps、模型训练/推理、Agent开发、HuggingFace |
| 墨维（运维） | 27 | GitHub、CI/CD、Google Workspace、邮件、基础设施 |
| CEO | 27 | 战略决策、治理、元技能、自学习、技能发现 |
| 墨增（增长引擎） | 19 | SEO、CRO、营销文案、A/B测试、社交媒体策略 |
| 墨迹（内容工厂） | 18 | 视频制作、动画、设计原型、ComfyUI、PPT、游戏 |
| 墨思（情报研究） | 12 | arXiv论文、趋势预测、OSINT、世界监控、博客监控 |
| 墨盾（安全/QA） | 11 | 安全测试、SQL注入、XSS、渗透测试、零信任审计 |
| 墨工（设计） | 10 | ASCII艺术、像素艺术、架构图、信息图、AI音乐 |
| 墨商BD（商务拓展） | 7 | 提案策略、交易谈判、财务分析、项目管理 |
| 墨脑（知识管理） | 5 | 记忆系统、自学习、技能创作、笔记管理 |
| 墨影（IP孵化） | 4 | 小红书内容引擎、短视频、知识漫画 |
| 墨域（私域CRM） | 3 | 微信公众号、社交发布、X/Twitter运营 |
| 墨商销售（闲鱼实业） | 3 | 闲鱼自动化、CRO优化 |
| 墨数（数据） | 2 | 数据可视化（信息图） |
| 墨投（量化交易） | 1 | 多视角金融分析 |
| 墨算（财务） | 1 | 多Agent财务分析 |
| 墨单（订单交付） | 1 | 订单流程 |
| 墨育（教育） | 1 | 教育课程 |
| 墨声（客服） | 0 | 待实装 |
| 墨律（法务） | 0 | 待实装 |
| 墨海（出海） | 0 | 待实装 |

---

## 三、部署说明

### 环境要求
- Python ≥ 3.10
- Hermes Agent（必须，这是运行底座）
- Git

### 安装流程

```bash
# 1. 安装 Hermes Agent
pip install hermes-agent  # 或使用官方安装脚本

# 2. 克隆 Hermes OS 仓库
git clone https://github.com/moye-tech/-Hermes-OS.git
cd -Hermes-OS

# 3. 同步技能到 Hermes
bash tools/sync-skills.sh  # 将 skills/ 复制到 ~/.hermes/skills/

# 4. 安装 molin Python 包（可选——CLI 工具）
pip install -e .

# 5. 配置
cp .env.example ~/.molin/.env
# 编辑 ~/.molin/.env 填入 API Key

# 6. 验证
molin health
```

### 技能同步说明
系统的**真正能力**在 Hermes Agent 的运行时环境中，而非本仓库的 Python 代码。
`skills/` 目录是本系统对 Hermes Agent 的配置文件——每次同步后：
- Agent 获得新的行为指引
- 所有 22 子公司的技能自动可用
- 无需重启 Agent

---

## 四、与评估报告的对应

2026-05-04 架构评估报告指出了几个关键缺陷，以下是当前真实状态：

| 报告指出的问题 | 当前状态 | 说明 |
|:---------------|:---------|:-----|
| 无持久记忆 | ✅ 已解决 | Hermes 内置 memory + session_search |
| 子公司零通信 | ✅ 已解决 | 你=CEO + Agent=COO 作为通信总线 |
| 自学习是空壳 | ✅ 已运行 | P0 cronjob: 每周五10:00自动执行 |
| CEO战略硬编码 | ✅ 已解决 | 你直接对话 = 真实 CEO 决策 |
| 蜂群无并行 | ✅ 已解决 | delegate_task 真实并行 |
| 治理未执行 | ⚡ 部分 | 通过 cronjob 审批流 + L0-L3 规则 */
| 技能库实装率低 | ⚡ 部分 | 266 skill存在，需进一步编排成自动管线 |

---

## 五、cronjob 架构设计

Hermes OS 的定时任务通过 Hermes Agent 的 `cronjob` 工具管理，而非系统 crontab：

```yaml
特点：
- 每次执行在独立会话中运行（不受当前会话污染）
- 可指定加载哪些 skills（技能指导行为）
- 结果自动投递到指定平台（飞书/Telegram/原点）
- 支持 one-shot（一次性）和 forever（循环）模式
- 可设置 per-job model override（不同任务用不同模型）
- 支持 pre-run script（脚本输出注入 prompt 作为上下文）
```

### 当前作业清单
参见上方 2.2 节。

---

## 六、后续路线图

| 阶段 | 内容 | 时间 |
|:----|:-----|:----:|
| P1 | 墨迹内容工厂每日闭环 — ✅ 已部署 | 2026-05-05 首次运行 |
| P0 | 自学习每周循环 — ✅ 已部署 | 2026-05-08 首次运行 |
| P2 | 墨思情报银行 — 每日趋势扫描自动沉淀到知识库 | 待定 |
| P3 | 墨商销售闲鱼自动化 — 自动上架+回复 | 待定 |
| P4 | 跨子公司飞轮 — 墨思→墨迹→墨增→墨域→墨单→墨算 | 待定 |
