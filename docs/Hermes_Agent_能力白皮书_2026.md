---
name: hermes-capabilities-whitepaper
description: Hermes Agent 完整能力白皮书 — 218个技能、15条能力线、一人公司操作系统全览
version: 2026.05.04
---

# Hermes Agent 能力白皮书

> **版本**：2026年5月4日 | **技能总数**：218 | **类别数**：20

---

## 目录

1. [系统架构](#一系统架构)
2. [交互与通信](#二交互与通信)
3. [内容创作能力](#三内容创作能力)
4. [商业与战略能力](#四商业与战略能力)
5. [研发与技术能力](#五研发与技术能力)
6. [数据与智能能力](#六数据与智能能力)
7. [设计与视觉能力](#七设计与视觉能力)
8. [销售与变现能力](#八销售与变现能力)
9. [自动化与运维能力](#九自动化与运维能力)
10. [学习与进化能力](#十学习与进化能力)
11. [专家人格库](#十一专家人格库)
12. [能力速查表](#十二能力速查表)

---

## 一、系统架构

```
┌─────────────────────────────────────────────────────┐
│                  Hermes Agent v2.x                    │
│                                                       │
│  接入层：飞书 / 终端CLI / Telegram / Discord / 企业微信 │
│     │     Slack / Signal / WhatsApp / Email / ...     │
│     │                                                 │
│  决策层：molin-ceo-persona（四层意图理解）              │
│     │   agentic-engineering（编排模式）                 │
│     │   swarm-orchestration（蜂群并行）                 │
│     │                                                 │
│  技能层：218个SKILL.md                                │
│     ├── 内容工厂（小红书/公众号/视频/翻译）              │
│     ├── 商业大脑（PM/战略/市场/财务/法律）               │
│     ├── 研发工坊（全栈/脚本/爬虫/AI工程）               │
│     ├── 设计中心（AI绘画/图表/简历/PPT）                │
│     ├── 销售引擎（闲鱼自动化/成交话术/投标）             │
│     └── 专家人格（23个领域AI专家）                      │
│     │                                                 │
│  执行层：20+工具（终端/文件/搜索/浏览器/子代理/定时）     │
│     │                                                 │
│  进化层：self-learning-loop（自学习）                   │
│          memory（持久记忆）                             │
│          skill-discovery（技能发现）                    │
└─────────────────────────────────────────────────────┘
```

### 核心设计原则

- **CEO决策模式**：不被动响应，主动理解意图、分解任务、驱动执行
- **技能组合驱动**：单技能解决单点问题，多技能联动解决复杂任务
- **自进化**：每次复杂任务后自动反思→提取经验→更新技能
- **模型无关**：支持DeepSeek/Anthropic/OpenAI/Google等20+提供商

---

## 二、交互与通信

### 消息平台接入

| 平台 | 状态 | 说明 |
|------|------|------|
| **飞书（Feishu/Lark）** | ✅ 当前使用 | 支持文档评论、消息、文件 |
| 终端CLI | ✅ | hermes chat / hermes -q |
| Telegram | ✅ | Bot接入 |
| Discord | ✅ | Bot接入 |
| Slack | ✅ | Bot接入 |
| 企业微信 | ✅ | 回调接入 |
| 钉钉 | ✅ | Bot接入 |
| WhatsApp | ✅ | Bot接入 |
| Signal | ✅ | Bot接入 |
| Email | ✅ | SMTP/IMAP |
| SMS | ✅ | 短信 |
| Matrix | ✅ | 去中心化 |
| iMessage | ✅ | BlueBubbles |
| 微信 | ✅ | 个人微信 |
| QQ | ✅ | QQ Bot |
| Open WebUI | ✅ | API Server |

### 消息能力

- 文本消息（Markdown渲染）
- 图片发送（.jpg/.png/.webp）
- 音频发送（.mp3语音消息）
- 文件附件（任意格式）
- TTS文字转语音（Edge/OpenAI/ElevenLabs/MiniMax）
- STT语音转文字（本地whisper/Groq/OpenAI）

---

## 三、内容创作能力

### 3.1 小红书内容引擎（`xiaohongshu-content-engine`，268行）

**完整的内容生产系统，不是简单的文案生成：**

| 能力模块 | 具体输出 |
|----------|----------|
| **平台算法理解** | 推荐权重排序：封面点击率→完读率→点赞收藏→评论→分享 |
| **用户画像** | 25-35岁，追求实用/真实感/颜值，深度厌恶广告感 |
| **5种标题公式** | A数字+结果 / B对比反转 / C疑问钩子 / D身份代入 / E稀缺感 |
| **正文结构** | 前3行钩子→3-5个价值点→强CTA结尾 |
| **禁词检测** | 自动扫描暴富/月入百万/躺赚/保证等敏感词 |
| **封面建议** | 文字内容+背景色+排版方向+视觉元素 |
| **发布时间优化** | 按内容类型推荐最佳时段 |
| **A/B测试** | 每次输出双版本供对比 |
| **结构化输出** | JSON格式含title/hook/body/cta/tags/cover/engagement预估 |

### 3.2 公众号/长文内容

| 能力 | 说明 |
|------|------|
| 深度长文 | 3000-10000字行业分析/教程/案例 |
| 图文排版 | Markdown + 结构化段落 |
| 多语言 | 中/英/日/韩/繁 |
| 知识漫画 | 教育类/传记类/教程类漫画脚本 |
| 信息图 | 21种布局×21种风格 |

### 3.3 短视频内容

| 能力 | 说明 |
|------|------|
| 脚本撰写 | 分镜+旁白+字幕+节奏建议 |
| 口播文案 | 抖音/视频号风格 |
| 数字人脚本 | AI虚拟主播台本 |
| AI音乐 | Suno风格歌曲/背景音乐 |

### 3.4 翻译能力

- 中↔英双向翻译，千字5分钟
- 支持日/韩/法/德/西/葡/俄/阿等30+语言
- 专业领域翻译（技术/商务/法律/医学）
- 繁简转换（台湾/香港市场）

---

## 四、商业与战略能力

这是接高单价单子的核心能力。

### 4.1 产品管理（49个pm-*技能）

| 阶段 | 技能（代表性） | 产出 |
|------|---------------|------|
| **市场研究** | `pm-market-sizing` `pm-competitor-analysis` `pm-market-segments` `pm-user-personas` `pm-customer-journey-map` | TAM/SAM/SOM、竞品矩阵、用户画像 |
| **产品战略** | `pm-swot-analysis` `pm-ansoff-matrix` `pm-pestle-analysis` `pm-porters-five-forces` `pm-product-vision` `pm-lean-canvas` | 战略分析、商业模式画布 |
| **产品发现** | `pm-brainstorm-ideas-new` `pm-brainstorm-experiments-existing` `pm-opportunity-solution-tree` `pm-identify-assumptions-new` | 机会树、假设验证、实验设计 |
| **执行交付** | `pm-create-prd` `pm-user-stories` `pm-brainstorm-okrs` `pm-sprint-plan` `pm-pre-mortem` `pm-test-scenarios` | PRD、用户故事、OKR、Sprint |
| **市场进入** | `pm-gtm-strategy` `pm-beachhead-segment` `pm-competitive-battlecard` `pm-growth-loops` `pm-ideal-customer-profile` | GTM策略、竞争Battlecard |
| **营销增长** | `pm-north-star-metric` `pm-marketing-ideas` `pm-positioning-ideas` `pm-product-name` `pm-value-prop-statements` | 北极星指标、营销创意 |
| **数据分析** | `pm-ab-test-analysis` `pm-cohort-analysis` `pm-sentiment-analysis` `pm-sql-queries` | A/B测试、同期群、SQL |
| **工具箱** | `pm-review-resume` `pm-summarize-interview` `pm-draft-nda` `pm-privacy-policy` | 简历审查、访谈摘要、NDA |

### 4.2 商业文档

| 能力 | 交付标准 |
|------|----------|
| **商业计划书** | 执行摘要 + 市场分析(TAM/SAM/SOM) + 竞品矩阵 + SWOT + 商业模式 + 财务预测 + 团队 |
| **融资BP** | 投行级格式，含估值模型、资金用途、退出策略 |
| **PRD产品文档** | 8段式模板：问题/目标/用户/方案/功能/指标/发布/风险 |
| **MRD/BRD** | 市场需求文档/商业需求文档 |
| **竞品分析报告** | 5-10竞品深度对比 + 差异化策略 |
| **市场研究报告** | 行业趋势/规模/用户画像/机会/风险 |

### 4.3 财务与法务

| 能力 | 说明 |
|------|------|
| 财务预测模型 | 3年收入/成本/利润预测 |
| 预算管理 | 成本监控、ROI分析 |
| 定价策略 | 成本加成/价值定价/竞争定价 |
| 合同审查 | NDA/服务协议/外包合同 |
| 法务合规 | 隐私政策/用户协议/版权合规 |

### 4.4 CEO决策引擎（`molin-ceo-persona`，173行）

| 能力 | 说明 |
|------|------|
| **四层意图理解** | 字面意思→真实目的→隐含约束→最优路径 |
| **假设驱动** | 信息不全时合理假设，最多问1个问题 |
| **任务拆解** | 动词开头+明确产出+独立执行 |
| **ROI评估** | 内部评估，只在警告时提及 |
| **决策姿态** | GO/NEED_INFO/DIRECT_RESPONSE/NO_GO |

---

## 五、研发与技术能力

### 5.1 全栈开发

| 层级 | 技术栈 |
|------|--------|
| **后端** | Python/FastAPI/Flask/Django、Node.js/Express、Go |
| **前端** | React/Vue/Next.js/Nuxt、TypeScript、TailwindCSS |
| **数据库** | PostgreSQL/MySQL/MongoDB/Redis/SQLite |
| **API** | RESTful/GraphQL、JWT/OAuth认证、Swagger文档 |
| **测试** | pytest/jest/Playwright、单元/集成/E2E |

### 5.2 脚本与自动化

| 能力 | 说明 |
|------|------|
| Python脚本 | 数据处理/文件操作/API调用/Web Scraping |
| Shell脚本 | 系统管理/部署/批处理 |
| 爬虫开发 | 网页抓取/数据提取/反爬对抗 |
| 定时任务 | Cron调度/后台运行/失败重试 |

### 5.3 AI工程

| 能力 | 说明 |
|------|------|
| Prompt工程 | 系统提示词设计/优化/测试 |
| RAG系统 | 检索增强生成，含知识库构建 |
| Agent设计 | 多智能体协作系统架构 |
| 模型微调 | LoRA/QLoRA/DPO/GRPO（Axolotl/TRL/Unsloth） |
| 模型部署 | llama.cpp本地推理/vLLM高吞吐服务 |
| 模型评估 | MMLU/GSM8K等基准测试 |
| 结构化输出 | JSON/Regex/Pydantic约束生成（Outlines） |
| 模型安全 | 消除拒绝回答（OBLITERATUS） |

### 5.4 平台开发

| 能力 | 说明 |
|------|------|
| 微信小程序 | 原生/uni-app |
| Web应用 | 全栈SaaS |
| API服务 | 含认证/限流/监控 |
| 飞书应用 | Bot+文档+多维表格 |
| Chrome扩展 | 浏览器插件 |

---

## 六、数据与智能能力

### 6.1 数据分析

| 能力 | 工具/方法 |
|------|-----------|
| 数据清洗 | Python/Pandas处理缺失值/异常值/格式转换 |
| 统计分析 | 描述统计/假设检验/回归分析 |
| 可视化 | Matplotlib/Seaborn/Plotly图表生成 |
| SQL查询 | 自然语言→SQL（BigQuery/PostgreSQL/MySQL） |
| A/B测试 | 显著性检验+置信区间+决策建议 |
| 同期群分析 | 留存曲线/特征采用/分群洞察 |
| 情感分析 | 用户反馈→情感评分+需求挖掘 |

### 6.2 研究能力

| 能力 | 说明 |
|------|------|
| **last30days** | 跨Reddit/HN/Polymarket/GitHub/YouTube/TikTok/X热度搜索 |
| **学术研究** | arXiv论文搜索/ML论文写作（NeurIPS/ICML/ICLR格式） |
| **竞品调研** | 市场情报/用户洞察/趋势分析 |
| **博客监控** | RSS/Atom订阅自动监测 |
| **预测市场** | Polymarket数据查询 |
| **知识库** | Karpathy LLM Wiki构建/查询 |
| **Obsidian** | 知识管理读写 |

---

## 七、设计与视觉能力

### 7.1 AI绘画

| 能力 | 工具链 |
|------|--------|
| 文生图 | Stable Diffusion / Midjourney / DALL-E |
| 图生图 | ControlNet / IP-Adapter / img2img |
| 工作流 | ComfyUI节点编排 |
| 风格迁移 | 真人→动漫/赛博朋克/国潮/3D/写实 |
| 批量生成 | 50+张批量，统一风格 |

**适用场景**：头像定制/插画/电商图/Logo/壁纸/小红书封面

### 7.2 图表与文档设计

| 能力 | 产出 |
|------|------|
| **PPT** | 完整.pptx含封面/图表/动画/备注 |
| **架构图** | 暗色SVG云架构/系统设计图 |
| **信息图** | 21种布局×21种风格 |
| **手绘图** | Excalidraw风格架构/流程/时序图 |
| **PDF编辑** | 文字修改/标题调整 |
| **OCR** | PDF/扫描件文字提取 |

### 7.3 创意设计

| 能力 | 说明 |
|------|------|
| 像素艺术 | NES/GameBoy/PICO-8调色板 |
| ASCII艺术 | pyfiglet/cowsay/图片转ASCII |
| 生成艺术 | p5.js着色器/交互/3D |
| 数学动画 | Manim CE算法可视化 |
| UI原型 | 快速HTML原型（54个设计系统参考） |
| 设计规范 | Google DESIGN.md |
| 网页设计 | 一次性HTML落地页/演示 |

---

## 八、销售与变现能力

### 8.1 闲鱼自动化（`xianyu-automation`，348行）

| 能力模块 | 说明 |
|----------|------|
| **消息轮询** | 30秒间隔扫描新消息 |
| **对话记忆** | 按买家+商品维护上下文，最多20轮 |
| **成交信号检测** | 30+关键词：成交/好的/怎么交易/多少钱/包邮/ok/buy... |
| **退款预警** | 8个退款关键词优先级最高，立即升级 |
| **首问模板** | 自动回复：你好，关于「商品」有什么可以帮你的？ |
| **成交流程** | 信号检测→触发报价→BD介入→关闭交易 |
| **状态持久化** | 对话保存到JSON，重启不丢失 |

### 8.2 成交话术（Shop Sales Framework）

| 阶段 | 话术 |
|------|------|
| 触发识别 | 检测到「咨询/了解/怎么收费/靠谱吗」→ 引导需求 |
| 需求诊断 | 三问法：现状→痛点→目标 |
| 价值陈述 | 案例匹配→产品推荐→报价 |
| 异议处理 | 5种异议（贵/不信/没时间/考虑/拒绝）× 对应话术 |
| 成交确认 | 付款链接+入群+今晚开始 |

### 8.3 投标与报价

| 能力 | 产出 |
|------|------|
| 猪八戒投标 | 完整标书：公司简介/方案/报价/案例/团队 |
| 项目报价单 | 服务项/交付物/周期/价格/付款方式 |
| 服务商店 | 闲鱼商品文案（标题/描述/标签/案例） |
| 商务邮件 | 中英文客户沟通/跟进/催款 |

---

## 九、自动化与运维能力

### 9.1 任务自动化

| 能力 | 说明 |
|------|------|
| **蜂群编排** | 7种角色（研究员/后端/前端/测试/审查/作家/分析师）并行 |
| **子代理委托** | delegate_task，最多3并发，可嵌套2层 |
| **定时任务** | Cron调度，支持分钟/小时/天/周/月 |
| **Webhook** | 事件驱动触发，支持自定义路由 |
| **后台进程** | 长期运行服务/监控/轮询 |

### 9.2 DevOps

| 能力 | 说明 |
|------|------|
| CI/CD | GitHub Actions/自动部署 |
| Docker | 容器化/编排 |
| 监控告警 | Grafana仪表盘 |
| 健康检查 | 服务状态巡检 |
| 性能调优 | 自动诊断+优化建议 |

### 9.3 安全

| 能力 | 说明 |
|------|------|
| 代码安全审计 | OWASP Top 10扫描 |
| 依赖漏洞检查 | CVE扫描 |
| 密钥管理 | 凭证加密/轮换 |
| 访问控制 | 权限管理/审批流程 |
| 合规检查 | GDPR/隐私/数据保护 |

---

## 十、学习与进化能力

### 10.1 自学习回路（`self-learning-loop`）

```
完成任务(5+工具调用)
    ↓
反思：哪里做对了？哪里踩坑了？
    ↓
分类：是pitfall？pattern？用户偏好？环境信息？
    ↓
决策：存memory（事实）或存skill（流程）
    ↓
结晶：自动更新或创建技能
    ↓
下次：加载技能，不再犯同样的错
```

### 10.2 技能发现（`skill-discovery`）

- 批量评估外部GitHub项目
- 自动判定集成价值（直接可用/可转换/仅参考/跳过）
- 大规模技能导入（50+技能批量curl+write）
- 分级实施路线图

### 10.3 持久记忆

| 类型 | 存储内容 |
|------|----------|
| 用户记忆 | 姓名、偏好、沟通风格、平台、语言 |
| 环境记忆 | OS、安装工具、项目结构、API配置 |
| 经验记忆 | 踩过的坑、有效的命令、最佳实践 |

---

## 十一、专家人格库

23个预置AI专家，加载即切换角色：

### 营销与内容（9个）

| 专家 | 专长 |
|------|------|
| `agent-marketing-xiaohongshu-specialist` | 小红书运营 |
| `agent-marketing-douyin-strategist` | 抖音策略 |
| `agent-marketing-tiktok-strategist` | TikTok策略 |
| `agent-marketing-bilibili-content-strategist` | B站内容 |
| `agent-marketing-wechat-official-account` | 公众号运营 |
| `agent-marketing-social-media-strategist` | 全平台社媒策略 |
| `agent-marketing-content-creator` | 内容创作 |
| `agent-marketing-seo-specialist` | SEO优化 |
| `agent-marketing-growth-hacker` | 增长黑客 |

### 工程与产品（8个）

| 专家 | 专长 |
|------|------|
| `agent-engineering-backend-architect` | 后端架构 |
| `agent-engineering-frontend-developer` | 前端开发 |
| `agent-engineering-code-reviewer` | 代码审查 |
| `agent-engineering-rapid-prototyper` | 快速原型 |
| `agent-engineering-technical-writer` | 技术写作 |
| `agent-product-manager` | 产品管理 |
| `agent-product-feedback-synthesizer` | 用户反馈分析 |
| `agent-product-trend-researcher` | 产品趋势研究 |

### 销售与商务（3个）

| 专家 | 专长 |
|------|------|
| `agent-sales-proposal-strategist` | 投标策略 |
| `agent-sales-deal-strategist` | 成交策略 |
| `agent-marketing-growth-hacker` | 增长黑客 |

### 其他（3个）

| 专家 | 专长 |
|------|------|
| `agent-design-ux-researcher` | UX研究 |
| `agent-finance-financial-analyst` | 财务分析 |
| `agent-specialized-chief-of-staff` | 幕僚长/总助 |
| `agent-testing-reality-checker` | 现实检验 |

---

## 十二、能力速查表

### 按交付物类型

```
📄 文档类
  商业计划书 ✓  融资BP ✓  PRD ✓  MRD/BRD ✓
  竞品分析 ✓  市场研究报告 ✓  用户画像 ✓
  SWOT分析 ✓  OKR方案 ✓  Sprint计划 ✓

🎨 设计类
  PPT定制 ✓  AI绘画 ✓  架构图 ✓  信息图 ✓
  简历优化 ✓  像素艺术 ✓  UI原型 ✓  手绘图表 ✓

💻 技术类
  全栈Web ✓  API开发 ✓  小程序 ✓  爬虫 ✓
  脚本自动化 ✓  AI集成 ✓  模型微调 ✓

📱 内容类
  小红书笔记 ✓  公众号文章 ✓  短视频脚本 ✓
  翻译 ✓  信息图 ✓  知识漫画 ✓

💰 商业类
  闲鱼自动化 ✓  成交话术 ✓  投标方案 ✓
  商务邮件 ✓  定价策略 ✓  财务预测 ✓
```

### 按接单平台适配

| 平台 | 适配服务 |
|------|----------|
| **闲鱼** | 商业计划书/简历优化/PPT/AI绘画/文案/翻译 |
| **猪八戒** | PRD/竞品分析/市场研究/小程序/网站/BP |
| **小红书** | 内容代运营/文案批量/封面设计/策略咨询 |
| **Upwork/Fiverr** | PRD/BP/Translation/Data Analysis/Web Dev |

---

> **这份系统的独特价值**：不是218个孤立技能，而是一个能自我进化的AI操作系统。你不需要告诉它用哪个技能——你只需要说目标，它自动理解意图、分解任务、调度资源、交付结果。
