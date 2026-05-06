# 墨麟 AI 集团 · 组织架构 v5.0

> 一人公司 · 330 技能 · 4 层体系 · 零重叠 · 可扩展

---

## 1. 设计原则

1. **Tier-by-purpose**: 每层有明确的职能定位，收入/成本/治理分离
2. **Non-overlapping domains**: 每个子公司的业务边界清晰，不重叠
3. **Directory = Organization**: 技能目录结构直接映射组织架构
4. **Extensible by design**: 新增技能可以定位到唯一子公司，无需重组
5. **Brand preservation**: 墨X 品牌名保留，层级通过前缀区分

---

## 2. 四层架构全景

```
                     ┌─────────────────────────────────────────────┐
                     │       L0: 战略治理层 (STRATEGY)              │
                     │      CEO · 董事会 · 集团中台                 │
                     │  目标/治理/记忆/风控/技能工厂                 │
                     │  预算: -¥500/月 · 成本中心                    │
                     └──────────────────┬──────────────────────────┘
                                        │ 决策流 ↑↓
     ┌──────────────────────────────────┼──────────────────────────────────┐
     │         L1: 营收业务线 (REVENUE)  │                                  │
     │  每个子公司独立P&L，对外创收       │                                  │
     │  预算: +¥45,000/月目标             │                                  │
     │                                    │                                  │
     │  墨商商务  墨迹内容  墨影IP  墨码开发  墨声客服  墨域私域            │
     │  墨单订单  墨育教育  墨海出海  墨投交易  墨工设计  墨律法务          │
     │  墨思研究  墨增增长  墨数数据                                        │
     └──────────────────────────────────┬──────────────────────────────────┘
                                        │ 服务 ↑↓
     ┌──────────────────────────────────┼──────────────────────────────────┐
     │    L2: 内部中台 (INTERNAL)        │                                  │
     │  服务内部，不对外创收              │                                  │
     │  预算: -¥1,200/月                 │                                  │
     │                                    │                                  │
     │  墨智AI研发  墨维运维  墨算财务  墨盾安全  墨脑知识                  │
     └──────────────────────────────────┬──────────────────────────────────┘
                                        │ 工具 ↑↓
     ┌─────────────────────────────────────────────────────────────────────┐
     │         L3: 共享能力层 (SHARED)                                      │
     │  跨子公司复用的通用能力                                              │
     │  DevOps工具 · 工程模板 · 数据管道 · 设计系统 · 合规框架              │
     └─────────────────────────────────────────────────────────────────────┘
```

---

## 3. 完整子公司列表

### L0 — 战略治理层 (Strategy)

| # | 墨名 | 英文 | 职责 | 目录 |
|---|------|------|------|------|
| 00 | 中枢 | Nexus | CEO决策、治理规则、目标管理、记忆系统、技能工厂 | `strategy/ceo/` |

关键技能: molin-governance, molin-goals, molin-ceo-persona, molin-daily-briefing, 
molin-okr-tracker, molin-company-structure, molin-relay-protocol, molin-memory,
self-learning-loop, skill-discovery, self-evolving-sop-system, scaffold-subsidiary,
hermes-tool-development, batch-yaml-frontmatter-injection, readme-standardization,
decompiled-codebase-extraction, ai-taste-quality, paperclip-company-os

### L1 — 营收业务线 (Revenue Business Units)

每个业务线有独立的SKU、定价、交付流程。

#### 01. 墨商 商务 — MoShang Commerce
**旧:** 墨商BD + 墨商销售 → **合并为"墨商 商务"**

| 字段 | 值 |
|------|-----|
| **核心产品** | 闲鱼商品销售·投标方案·商务分析报告·竞品分析·商业计划书 |
| **收入目标** | ¥8,000/月 (原BD¥3k+销售¥5k) |
| **关键技能** | xianyu-automation, agent-sales-proposal-strategist, agent-sales-deal-strategist, marketing-skills-copywriting, marketing-skills-cro |
| **目录** | `revenue/commerce/` |

**边界:** 专注交易转化 → 从询盘到成交的全链路。BD投标+闲鱼销售合并，统一"商务"定位。

#### 02. 墨迹 内容 — MoJi Content
**保留，范围微调**

| 字段 | 值 |
|------|-----|
| **核心产品** | 公众号代运营·短视频制作·PPT工坊·代写社·科普动画 |
| **收入目标** | ¥2,000/月 |
| **关键技能** | ffmpeg-video-engine, manim-video, powerpoint, social-push-publisher, agent-marketing-content-creator, seo-machine, moneymaker-turbo, humanizer |
| **目录** | `revenue/content/` |

**边界:** 内容生产管线，不含IP运营(归墨影)。生产→多渠道分发的管道角色。承接定制订单。

#### 03. 墨影 IP — MoYing IP
**保留并强化**

| 字段 | 值 |
|------|-----|
| **核心产品** | 小红书IP代运营·内容策划·品牌合作·AI封面生成·热点笔记 |
| **收入目标** | ¥5,000/月 |
| **关键技能** | molin-xiaohongshu, xiaohongshu-content-engine, social-push-publisher, baoyu-comic, pixelle-video |
| **目录** | `revenue/ip/` |

**边界:** IP孵化与品牌运营。专注于小红书/知乎等平台的内容IP化，与墨迹(内容生产)是"制作→包装"关系，墨迹做单，墨影做IP。不包含增长投放(归墨增)。

#### 04. 墨码 开发 — MoMa Dev
**保留，明确边界**

| 字段 | 值 |
|------|-----|
| **核心产品** | Python自动化脚本¥3k·Web工具¥5k·数据爬虫¥2k·API对接¥3k·技术咨询 |
| **收入目标** | ¥5,000/月 |
| **关键技能** | agent-engineering-rapid-prototyper, agent-engineering-backend-architect, agent-engineering-frontend-developer, agent-testing-reality-checker, systematic-debugging, writing-plans, test-driven-development |
| **目录** | `revenue/dev/` |

**边界:** 对外技术外包。与墨智(内部研发)的边界：墨码接外部客户单，墨智做内部工具。共享技能通过目录分离。

#### 05. 墨声 客服 — MoSheng CS
**保留**

| 字段 | 值 |
|------|-----|
| **核心产品** | 客服代运营¥1k/月·FAQ体系建设¥500·工单SOP¥300·满意度报告¥200 |
| **收入目标** | ¥1,000/月 |
| **关键技能** | molin-customer-service, parlant-customer-agent |
| **目录** | `revenue/cs/` |

**边界:** 客服SaaS+代运营。不包含私域运营(归墨域)，专注客服场景。

#### 06. 墨域 私域 — MoYu CRM
**保留，明确与墨增的边界**

| 字段 | 值 |
|------|-----|
| **核心产品** | 私域代运营¥3k/月·社群SOP¥500·自动化营销文案¥200·RFM分析 |
| **收入目标** | ¥3,000/月 |
| **关键技能** | molin-crm, agent-marketing-wechat-official-account, social-push-publisher, marketing-skills-copywriting |
| **目录** | `revenue/crm/` |

**边界:** 私域用户生命周期管理(已有用户/粉丝)。墨增专注公域获客(新用户获取)。墨域=存量运营，墨增=增量获取。

#### 07. 墨单 订单 — MoDan Order
**保留**

| 字段 | 值 |
|------|-----|
| **核心产品** | 订单管理SOP¥500·报价模板套装¥300·交付质量检查¥200 |
| **收入目标** | ¥2,000/月 |
| **关键技能** | xianyu-automation, agent-sales-deal-strategist, agent-product-manager |
| **目录** | `revenue/order/` |

**边界:** 订单交付管理，不包含客户获取。

#### 08. 墨育 教育 — MoYu Education
**保留**

| 字段 | 值 |
|------|-----|
| **核心产品** | 课程大纲¥500·教学设计¥800·AI辅导¥300/小时·学习路径规划¥500·测验生成¥200 |
| **收入目标** | ¥1,000/月 |
| **关键技能** | molin-education, ranedeer-ai-tutor, deeptutor-ai-tutor-engine |
| **目录** | `revenue/education/` |

**边界:** 知识付费+AI教育。不包含培训材料生产(归墨迹)。

#### 09. 墨海 出海 — MoHai Global
**保留**

| 字段 | 值 |
|------|-----|
| **核心产品** | 英文文案代写¥500·海外社媒运营¥2k/月·本地化翻译¥300/篇·合规检查¥200 |
| **收入目标** | ¥2,000/月 |
| **关键技能** | molin-global, weblate-localization, social-push-publisher, agent-marketing-content-creator |
| **目录** | `revenue/global/` |

**边界:** 出海本地化与多语言内容。与墨域(国内私域)不重叠。

#### 10. 墨投 交易 — MoTou Trading
**保留**

| 字段 | 值 |
|------|-----|
| **核心产品** | 量化策略开发¥1k·回测分析报告¥500·策略优化¥800·市场简报¥200 |
| **收入目标** | ¥1,000/月 |
| **关键技能** | molin-trading, molin-trading-agents, quant-trading-agent-engine, agent-finance-financial-analyst |
| **目录** | `revenue/trading/` |

**边界:** 加密/股票量化交易。与墨算(内部财务)无重叠。

#### 11. 墨工 设计 — MoGong Design
**保留，合并墨品"设计"职能**

| 字段 | 值 |
|------|-----|
| **核心产品** | AI音乐¥200/首·BGM定制¥300·TTS配音¥100·UI设计¥500·品牌视觉 |
| **收入目标** | ¥2,000/月 |
| **关键技能** | songwriting-and-ai-music, onlook-design-tool, invokeai-creative-engine, pixel-art, architecture-diagram, ascii-art, popular-web-designs |
| **目录** | `revenue/design/` |

**边界:** 创意设计(视觉/音乐/声音)。与墨迹(内容)区别：设计侧重创意产出，内容侧重文字/视频管线。

#### 12. 墨律 法务 — MoLv Legal
**保留**

| 字段 | 值 |
|------|-----|
| **核心产品** | 合同审查¥500·隐私政策生成¥300·合规审计¥500·NDA生成¥200·谈判策略¥300·TOS生成¥400 |
| **收入目标** | ¥1,000/月 |
| **关键技能** | molin-legal, requesting-code-review, writing-plans |
| **目录** | `revenue/legal/` |

**边界:** 法律文档+合规。不包含安全审计(归墨盾)。

#### 13. 墨思 研究 — MoSi Research
**保留**

| 字段 | 值 |
|------|-----|
| **核心产品** | AI行业日报¥99/月·趋势周报¥499/月·竞品监控¥1k/月·定制研究¥5k |
| **收入目标** | ¥2,000/月 |
| **关键技能** | blogwatcher, world-monitor, arxiv, maigret-osint, agent-product-trend-researcher, research-paper-writing, polymarket, karpathy-autoresearch |
| **目录** | `revenue/research/` |

**边界:** 行业研究/情报/趋势洞察。输出研究报告，不包含数据分析(归墨数)。

#### 14. 墨增 增长 — MoZeng Growth
**保留，明确与墨域边界**

| 字段 | 值 |
|------|-----|
| **核心产品** | 增长策略方案¥1k·A/B测试分析¥500·投放优化方案¥800·SEO审计 |
| **收入目标** | ¥3,000/月 |
| **关键技能** | molin-growth, claude-seo, marketing-skills-cro, molin-growth-marketing, agent-marketing-growth-hacker, seo-machine, analytics-tracking |
| **目录** | `revenue/growth/` |

**边界:** 公域获客(SEO/投放/增长实验)。墨域=存量运营(私域)，墨增=增量获取(公域)。

#### 15. 墨数 数据 — MoShu Data
**从内部→升级为营收业务线**

| 字段 | 值 |
|------|-----|
| **核心产品** | 数据分析报告¥800·可视化Dashboard¥500·BI仪表盘¥1k·归因分析¥1k·数据产品 |
| **收入目标** | ¥2,000/月 |
| **关键技能** | molin-vizro, baoyu-infographic, data-science, jupyter-live-kernel, agent-product-trend-researcher |
| **目录** | `revenue/data/` |

**边界:** 数据分析与可视化。从内部支持升级为可对外销售的数据产品。不包含行业研究(归墨思)。

---

### L2 — 内部中台 (Internal Infrastructure)

内部部门，不对外创收。服务L1业务线。

#### 16. 墨智 AI研发 — MoZhi AI R&D
**保留，明确与墨码的边界**

| 字段 | 值 |
|------|-----|
| **核心职责** | AI工具链建设·Prompt模板·Hermes技能市场·自动化脚本·MLOps基础设施 |
| **预算** | ¥2,000/月 (vs ¥2,000 原目标，改为成本中心) |
| **关键技能** | agent-engineering-backend-architect, agent-engineering-rapid-prototyper, swarm-engine, gstack-agent-templates, claude-code-sourcemap, opencli-hub, cli-anything, all mlops/*, all autonomous-ai-agents/*, all mlops/* |
| **目录** | `internal/ai-rd/` |

**边界:** 内部工具研发。墨码接外部单，墨智建内部能力。墨智产出→墨码使用。

#### 17. 墨维 运维 — MoWei DevOps
**保留**

| 字段 | 值 |
|------|-----|
| **核心职责** | 系统健康监控·自动故障恢复·CI/CD·容器管理·GitHub管理·邮件/通知/日历 |
| **预算** | ¥200/月 |
| **关键技能** | opensre-sre-agent, devops/*, cronjob-*, github/*, webhook-subscriptions, native-mcp, lightpanda-browser, ghost-os, productivity/*, email/*, apple/*, smart-home/* |
| **目录** | `internal/devops/` |

**边界:** 系统层运维。不包含安全审计(归墨盾)。

#### 18. 墨算 财务 — MoSuan Finance
**从内部→保留为内部部门**

| 字段 | 值 |
|------|-----|
| **核心职责** | 成本核算·ROI分析·预算规划·财务报表自动生成·子公司P&L追踪 |
| **预算** | ¥100/月 |
| **关键技能** | molin-daily-ledger, agent-finance-financial-analyst, trading-agents |
| **目录** | `internal/finance/` |

**边界:** 内部财务管理。墨投(对外交易)涉及财务分析但使用不同技能集。

#### 19. 墨盾 安全 — MoDun Security
**保留为内部部门**

| 字段 | 值 |
|------|-----|
| **核心职责** | 安全审计·权限管理·合规检查·漏洞扫描·渗透测试·代码安全审查 |
| **预算** | ¥100/月 |
| **关键技能** | sandbox-execution-protection, ag-vulnerability-scanner, ag-web-security-testing, ag-sql-injection-testing, ag-xss-html-injection, ag-ssh-penetration-testing, ag-solidity-security, ag-error-handling-patterns, ag-zeroize-audit, ag-spec-to-code-compliance, red-teaming/* |
| **目录** | `internal/security/` |

**边界:** 安全审计+QA。墨律(法务)管法律合规，墨盾管技术安全。

#### 20. 墨脑 知识 — MoNao Knowledge
**保留为内部部门**

| 字段 | 值 |
|------|-----|
| **核心职责** | 经验沉淀·SOP管理·最佳实践·知识图谱·记忆系统·技能发现 |
| **预算** | ¥100/月 |
| **关键技能** | self-learning-loop, skill-discovery, self-evolving-sop-system, molin-memory, supermemory, claude-mem, mempalace, obsidian, note-taking/* |
| **目录** | `internal/knowledge/` |

**边界:** 内部知识管理。不包含对外内容生产(归墨迹/墨影)。

---

#### 墨品 产品 — MoPin Product (已解散并入其他子公司)

**问题:** 墨品(产品设计)太模糊，既有PM技能又接单PRD，与多个子公司重叠。

**处理方案:**
- PM技能(用户研究/市场分析/PRD) → 拆分给**墨思研究**(市场研究部分)和**中枢层**(产品路线图/定价策略等战略决策)
- 设计类 → 并入**墨工设计**
- 产品管理执行 → 成为**中枢层**的共享职能，不独立为公司

---

#### L3 — 共享能力层 (Shared Capabilities)

不是独立子公司，而是跨L0/L1/L2复用的通用技能库。

| # | 能力域 | 目录 | 说明 |
|---|--------|------|------|
| S1 | **工程模板** Engineering | `shared/engineering/` | 软件开发最佳实践、TDD、调试、代码审查、架构模式 |
| S2 | **DevOps工具链** | `shared/devops/` | CI/CD模板、容器配置、监控模板 |
| S3 | **内容管线** | `shared/content/` | 跨内容子公司复用的视频/图片/渲染管线 |
| S4 | **设计系统** | `shared/design/` | 品牌视觉规范、设计模板、SVG组件 |
| S5 | **数据管道** | `shared/data/` | 数据分析模板、ETL管线、Jupyter notebooks |
| S6 | **合规框架** | `shared/compliance/` | 跨法务+安全+财务的合规检查清单 |
| S7 | **个人/生活工具** | `personal/` | gaming, smart-home, social-media等个人用途 |

---

## 4. 目录结构映射

| 新目录 | 对应 | 技能范围 |
|--------|------|----------|
| `strategy/ceo/` | L0 中枢 | 治理/目标/记忆/技能工厂/决策 |
| `revenue/commerce/` | L1 墨商 | 商务投标+闲鱼销售 |
| `revenue/content/` | L1 墨迹 | 内容生产管线 |
| `revenue/ip/` | L1 墨影 | 小红书IP孵化 |
| `revenue/dev/` | L1 墨码 | 对外技术外包 |
| `revenue/cs/` | L1 墨声 | 客服自动化 |
| `revenue/crm/` | L1 墨域 | 私域运营 |
| `revenue/order/` | L1 墨单 | 订单交付 |
| `revenue/education/` | L1 墨育 | AI教育 |
| `revenue/global/` | L1 墨海 | 出海本地化 |
| `revenue/trading/` | L1 墨投 | 量化交易 |
| `revenue/design/` | L1 墨工 | 创意设计 |
| `revenue/legal/` | L1 墨律 | 法务合规 |
| `revenue/research/` | L1 墨思 | 行业研究 |
| `revenue/growth/` | L1 墨增 | 增长获客 |
| `revenue/data/` | L1 墨数 | 数据分析与可视化 |
| `internal/ai-rd/` | L2 墨智 | AI研发基础设施 |
| `internal/devops/` | L2 墨维 | 系统运维 |
| `internal/finance/` | L2 墨算 | 财务 |
| `internal/security/` | L2 墨盾 | 安全QA |
| `internal/knowledge/` | L2 墨脑 | 知识管理 |
| `shared/engineering/` | L3 工程 | 开发最佳实践模板 |
| `shared/devops/` | L3 DevOps | CI/CD/部署模板 |
| `shared/content/` | L3 内容 | 跨业务复用内容工具 |
| `shared/design/` | L3 设计 | 设计系统组件 |
| `shared/data/` | L3 数据 | 数据分析管道 |
| `shared/compliance/` | L3 合规 | 合规检查框架 |
| `personal/` | (非公司) | 个人生活技能 |

---

## 5. 技能目录迁移计划

### 5.1 迁移原则

1. **SKILL.md 文件不动**（避免破坏引用和链接），只改 `molin_owner` 元数据
2. 目录结构通过 `molin_owner` 标签索引，而非物理路径
3. 新增技能写入新目录，旧技能逐步迁移标记
4. 使用 `batch-yaml-frontmatter-injection` 批量更新 molin_owner

### 5.2 批量重标记计划

```bash
# 使用 batch-yaml-frontmatter-injection 批量更新 molin_owner
# 目标映射表（旧 molin_owner → 新 所属层+子公司）

# 旧: 墨商BD + 墨商销售 → 新: L1-墨商商务
# 旧: 墨迹内容 → 新: L1-墨迹内容
# 旧: 墨影IP → 新: L1-墨影IP
# 旧: 墨码开发 → 新: L1-墨码开发
# 旧: 墨声客服 → 新: L1-墨声客服
# 旧: 墨域CRM → 新: L1-墨域私域
# 旧: 墨单订单 → 新: L1-墨单订单
# 旧: 墨育教育 → 新: L1-墨育教育
# 旧: 墨海出海 → 新: L1-墨海出海
# 旧: 墨投交易 → 新: L1-墨投交易
# 旧: 墨工设计 → 新: L1-墨工设计
# 旧: 墨律法务 → 新: L1-墨律法务
# 旧: 墨思研究 → 新: L1-墨思研究
# 旧: 墨增增长 → 新: L1-墨增增长
# 旧: 墨数数据 → 新: L1-墨数数据
# 旧: 墨智AI → 新: L2-墨智AI研发
# 旧: 墨维运维 → 新: L2-墨维运维
# 旧: 墨算财务 → 新: L2-墨算财务
# 旧: 墨盾安全 → 新: L2-墨盾安全
# 旧: 墨脑知识 → 新: L2-墨脑知识
# 旧: 墨品产品 → 技能拆分到L0中枢、L1墨思、L1墨工
# 旧: CEO → 新: L0-中枢
```

### 5.3 墨品产品 技能归属再分配

| 技能 | 新归属 | 理由 |
|------|--------|------|
| agent-product-manager | L0 中枢 | 产品战略决策 |
| agent-product-feedback-synthesizer | L1 墨思 | 反馈分析→研究 |
| agent-product-trend-researcher | L1 墨思 | 趋势研究 |
| agent-design-ux-researcher | L1 墨工 | UX研究→设计 |
| pm-skills-marketplace (65个) | L0 中枢 | 方法论库，不直接创收 |
| pm-business-model | L0 中枢 | 商业模式设计 |
| pm-skills/* (全部65+) | L0 中枢 | 产品管理方法论 |

### 5.4 新技能纳入流程

```
1. 发现外部GitHub项目 → skill-discovery评估
2. 创建 SKILL.md，设置 molin_owner = "L1-墨X"
3. 自动更新 skills-index.md
4. 更新 molin-company-structure 子公司技能列表
5. 更新对应子公司的营收预算表
```

---

## 6. 子公司月度预算总表 (v5.0)

| 层 | # | 子公司 | 墨名 | 收入目标 | 预算 | 类型 |
|:--:|:-:|:------|:---:|:--------:|:---:|:----:|
| L0 | 00 | 中枢 | 墨♾ | - | ¥500 | 成本中心 |
| L1 | 01 | 商务 | 墨商 | ¥8,000 | ¥300 | 利润中心 |
| L1 | 02 | 内容 | 墨迹 | ¥2,000 | ¥150 | 利润中心 |
| L1 | 03 | IP | 墨影 | ¥5,000 | ¥250 | 利润中心 |
| L1 | 04 | 开发 | 墨码 | ¥5,000 | ¥300 | 利润中心 |
| L1 | 05 | 客服 | 墨声 | ¥1,000 | ¥50 | 利润中心 |
| L1 | 06 | 私域 | 墨域 | ¥3,000 | ¥100 | 利润中心 |
| L1 | 07 | 订单 | 墨单 | ¥2,000 | ¥80 | 利润中心 |
| L1 | 08 | 教育 | 墨育 | ¥1,000 | ¥50 | 利润中心 |
| L1 | 09 | 出海 | 墨海 | ¥2,000 | ¥80 | 利润中心 |
| L1 | 10 | 交易 | 墨投 | ¥1,000 | ¥80 | 利润中心 |
| L1 | 11 | 设计 | 墨工 | ¥2,000 | ¥80 | 利润中心 |
| L1 | 12 | 法务 | 墨律 | ¥1,000 | ¥50 | 利润中心 |
| L1 | 13 | 研究 | 墨思 | ¥2,000 | ¥160 | 利润中心 |
| L1 | 14 | 增长 | 墨增 | ¥3,000 | ¥100 | 利润中心 |
| L1 | 15 | 数据 | 墨数 | ¥2,000 | ¥80 | 利润中心 |
| L2 | 16 | AI研发 | 墨智 | - | ¥200 | 成本中心 |
| L2 | 17 | 运维 | 墨维 | - | ¥200 | 成本中心 |
| L2 | 18 | 财务 | 墨算 | - | ¥100 | 成本中心 |
| L2 | 19 | 安全 | 墨盾 | - | ¥100 | 成本中心 |
| L2 | 20 | 知识 | 墨脑 | - | ¥100 | 成本中心 |
| | | **合计** | | **¥39,000** | **¥3,210** | |

> **变化说明:**
> - 墨商商务合并后统一收入目标 ¥8,000 (原 BD¥3K+销售¥5K)
> - 墨品产品 解散 (¥2,000收入移除，技能拆分)
> - 墨数数据 从内部升级为营收业务线 (¥2,000新目标)
> - L2 全部转为成本中心 (原也有收入目标，不合理)
> - 总目标从 ¥48,000 调为 ¥39,000 (更务实，去除了墨品虚拟收入)
> - 总预算从 ¥2,440 调为 ¥3,210 (墨智/墨维/墨盾/墨脑 预算调高反映实际成本)

---

## 7. 关键重叠问题解决

### 🔴 问题1: 墨商BD vs 墨商销售
**解决:** 合并为**墨商商务**。BD(投标/竞标/企业客户)和销售(闲鱼/C端)是同一"商务"职能的不同渠道。统一管理商务全链路。

### 🔴 问题2: 墨影IP vs 墨迹内容
**解决:** 保持分离但边界清晰。
- **墨迹内容**: "生产工厂" — 接单制作，按件计费。内容=产品
- **墨影IP**: "品牌孵化" — 运营账号/IP，持续积累。IP=资产
- 墨迹制作的内容可以授权给墨影运营，内部结算。

### 🔴 问题3: 墨增增长 vs 墨域CRM
**解决:** 按用户生命周期划分。
- **墨增增长**: 公域获客(SEO/投放/增长实验) — 新用户获取
- **墨域CRM**: 私域运营(老客复购/社群/留存) — 存量用户运营
- 中间衔接点：墨增获取的新用户→转交给墨域进行留存运营

### 🔴 问题4: 墨智AI vs 墨码开发
**解决:**
- **墨智AI研发** (L2, 内部): 内部工具、Prompt模板、MLOps、技能工厂
- **墨码开发** (L1, 营收): 对外技术外包，接客户订单
- 墨智产出的工具→墨码用来交付客户项目

### 🔴 问题5: 墨品产品
**解决:** 解散。PM技能分散到中枢(战略)、墨思(研究)、墨工(设计)。

---

## 8. 从22→20子公司的变化

| 变化 | 旧数量 | 操作 | 新数量 |
|------|--------|------|--------|
| 墨商BD+墨商销售→墨商商务 | 2 | 合并 | 1 |
| 墨品产品解散 | 1 | 移除 | 0 |
| 墨数数据升级为营收线 | 0 | 加入L1 | 1 |
| 中枢层正式纳入 | 0 | 新增L0 | 1 |
| L3共享层(非实体) | 0 | 新增 | (非计数) |
| **总计** | **22** | | **20子公司** |

---

## 9. 实施路线图

### Phase 1: 文档更新 (1天)
1. 更新本架构文档 (✅ 已完成)
2. 更新 `molin-company-structure` SKILL.md 为 v5.0
3. 更新 `skills-index.md` 反映新分层

### Phase 2: 元数据批量更新 (1天)
1. 使用 `batch-yaml-frontmatter-injection` 批量更新所有SKILL.md的 molin_owner
2. 更新映射表: 旧标签→新L1/L2标签格式

### Phase 3: 物理目录重构 (可选, 2天)
1. 创建新目录结构
2. 迁移SKILL.md到对应子目录
3. 更新所有内部引用

### Phase 4: 预算调整 (1天)
1. 更新 cron/jobs.yaml 中月度报告模板
2. 更新 molin-goals 中的目标设定

### Phase 5: 系统验证 (1天)
1. 运行 molin-memory 更新技能向量库
2. 验证所有子公司的技能索引完整性
3. 端到端测试: 从目标设定→技能调度→收入追踪

---

## 10. 未来扩展性

### 新增子公司流程
1. 确定属于哪个层 (L1营收 / L2内部)
2. 分配墨名 (命名空间: 墨+单字)
3. 指定目录: `revenue/新业务/` 或 `internal/新部门/`
4. 分配3-5个核心技能
5. 设定收入目标/预算

### 吸收外部技能流程
1. 评估技能归属哪个子公司
2. 检查是否与现有子公司领域重叠
3. 如有重叠→扩展现有子公司技能列表
4. 如无重叠→考虑是否成立新子公司

---

## 附录: 新旧组织架构对比

| 维度 | v4.0 (旧) | v5.0 (新) |
|------|-----------|-----------|
| 层数 | 模糊的T0/T1/T2 | 4层: L0战略/L1营收/L2内部/L3共享 |
| 子公司数 | 22 | 20 (合并2个+解散1个+新增L0+L1各1) |
| 营收目标 | ¥48,000 (含内部虚拟收入) | ¥39,000 (纯对外营收) |
| 重叠问题 | 5处严重重叠 | 全部解决 |
| 目录映射 | 不匹配 | 完全映射 |
| 扩展性 | 无设计 | 有新增流程 |
| 墨品产品 | 模糊存在 | 解散, 技能再分配 |
| 墨数数据 | 内部部门 | 升级为营收业务线 |
| 墨商BD/销售 | 两个子公司 | 合并为一个 |
