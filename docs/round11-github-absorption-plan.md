# 第11轮 GitHub 项目吸收计划

## 概述
- 日期：2026-05-05
- 目标：吸收 26 个 GitHub 项目，补强 15 家偏弱子公司
- 现有技能存量统计：268 个全局技能，22 家子公司

---

## 1. 墨数数据（数据分析子公司）

### 现有技能
| 技能 | 类型 | 说明 |
|:----|:----|:-----|
| `business/molin/data-analysis` | 子公司定义 | L1-墨数数据，基础配置 |
| `molin-vizro` | 产品型 skill | BI仪表盘引擎（McKinsey Vizro ⭐3.7k） |
| `baoyu-infographic` | 数据可视化 | 信息图生成 |
| `creative/baoyu-info..` | 设计类 | 21种布局类型的专业图表 |

### 要吸收的项目
- **dbt-core** (dbt-labs/dbt-core ⭐14k) — 数据转换工具，ELT中的T
- **ploomber** (ploomber/ploomber ⭐4k) — 端到端数据管线框架（特性：pipeline-as-code、增量构建、notebook集成）

### 缺什么设计模式
1. **数据转换管线（DAG编排）** — 从源头到目标的ELT流程控制
2. **增量构建策略** — 只处理变更数据而非全量刷新
3. **数据质量测试框架** — 内置数据完整性断言
4. **模块化连接器** — 多种数据源/目标的统一抽象

### 建议注入方案
1. 从 dbt-core 提取「DAG 任务编排」模式，创建 `dbt-data-pipeline` skill
2. 从 ploomber 提取「pipeline-as-code + 增量执行」模式，创建 `molin-ploomber-pipeline` skill
3. 将两种模式融合到 molin-vizro，支持从数据管线→BI看板的全链路

---

## 2. 墨投交易（量化交易子公司）

### 现有技能
| 技能 | 类型 | 说明 |
|:----|:----|:-----|
| `molin-trading` | 产品型 | Freqtrade 量化交易（⭐34k），含策略/回测/优化 |
| `molin-trading-agents` | 设计模式 | TauricResearch TradingAgents 多Agent框架 |
| `trading-agents-cn` | 中文版 | TradingAgents-CN 中文A股增强版（⭐25k） |
| `quant-trading-agent-engine` | 设计模式 | Vibe-Trading 7市场引擎 + 6数据源协议 |

### 要吸收的项目
- **freqtrade** (freqtrade/freqtrade ⭐34k) — 已有 skill，需深度整合
- **hftbacktest** (noklam/hftbacktest ⭐2k) — 高频回测引擎（特性：逐笔订单簿重建、纳秒级时间戳、市场微观结构分析）

### 缺什么设计模式
1. **高频订单簿重建** — 逐笔TICK数据的LOB重建算法
2. **市场微观结构分析** — 价差/深度/订单流不平衡
3. **纳秒级时间处理** — 高频策略的时间对齐
4. **Exchange模拟器** — 回测中的真实撮合引擎模拟

### 建议注入方案
1. 从 hftbacktest 提取「订单簿重建+微观结构分析」模式，创建 `hft-orderbook-analysis` skill
2. 与 molin-trading 的 Freqtrade 策略引擎对接：低频策略+高频微观结构信号
3. 整合到 quant-trading-agent-engine 作为第8个市场引擎

---

## 3. 墨域私域（私域CRM子公司）

### 现有技能
| 技能 | 类型 | 说明 |
|:----|:----|:-----|
| `molin-crm` | 产品型 | RFM用户分层、私域运营、CRM引擎 |
| `social-push-publisher` | 工具型 | 多平台社媒发布 |
| `xurl` | 工具型 | X/Twitter交互 |
| `agent-marketing-wechat-official-account` | 工具型 | 公众号运营 |

### 要吸收的项目
- **twenty** (twentyhq/twenty ⭐30k) — 现代化开源CRM（特性：自定义对象、工作流自动化、API原生）
- **mautic** (mautic/mautic ⭐8k) — 营销自动化平台（特性：邮件营销、联系人分群、营销日历）

### 缺什么设计模式
1. **自定义对象建模** — 动态实体-属性-值（EAV）模式
2. **工作流自动化引擎** — 基于触发条件的自动化动作链
3. **邮件营销引擎** — 模板化邮件+发送队列+打开率追踪
4. **营销日历/计划** — 多渠道营销活动的编排

### 建议注入方案
1. 从 twenty 提取「自定义对象+工作流自动化」模式，创建 `twenty-crm-engine` skill
2. 从 mautic 提取「营销自动化+邮件引擎」模式，创建 `mautic-marketing-automation` skill
3. 整合到 molin-crm：从当前纯策略输出→可执行CRM系统

---

## 4. 墨育教育（教育子公司）

### 现有技能
| 技能 | 类型 | 说明 |
|:----|:----|:-----|
| `molin-education` | 产品型 | AI教育引擎（DeepTutor+HumanSkillTree） |
| `ranedeer-ai-tutor` | 设计模式 | Mr. Ranedeer DSL + 7维学生配置 |
| `business/molin/education` | 子公司定义 | L1-墨育教育基础配置 |

### 要吸收的项目
- **moodle** (moodle/moodle ⭐6k) — 全球最大开源LMS（特性：课程管理、测验引擎、评分系统、学习分析、插件生态）

### 缺什么设计模式
1. **完整LMS课程管理** — 课程/章节/活动/资源的层次化组织
2. **测验引擎** — 多种题型（选择题/填空题/匹配题/简答题）+自动评分
3. **学习分析仪表盘** — 学生参与度、完成率、成绩分布
4. **插件/块架构** — 通过插件扩展功能的模块化系统

### 建议注入方案
1. 从 moodle 提取「LMS课程管理+测验引擎」模式，创建 `moodle-lms-engine` skill
2. 与 ranedeer-ai-tutor 的AI导师模式结合：AI生成课程内容→导入LMS结构
3. 整合测验引擎到 molin-education，实现从AI辅导到正式考试的全链路

---

## 5. 墨单订单（订单交付子公司）

### 现有技能
| 技能 | 类型 | 说明 |
|:----|:----|:-----|
| `business/molin/order` | 子公司定义 | L1-墨单订单基础配置（仅骨架） |

### SKILL.md 状态
- **仅有子公司定义文件**，无任何产品型或工具型 skill
- 是15家中最弱的之一，只有占位符

### 要吸收的项目
- **invoiceninja** (invoiceninja/invoiceninja ⭐9k) — 开票+费用跟踪+时间追踪（特性：发票模板、在线支付、客户门户、税务支持）
- **midday** (midday-ai/midday ⭐8k) — 全能商业操作系统（特性：交易追踪、收据OCR、支出分类、客户管理）

### 缺什么设计模式
1. **发票引擎** — 模板化发票生成+在线支付集成+催款流程
2. **交易追踪** — 银行流水自动同步+分类+对账
3. **收据OCR** — 扫描收据自动提取金额/日期/品类
4. **客户门户** — 客户自助查看发票/支付/历史

### 建议注入方案
1. 从 invoiceninja 提取「发票引擎+客户门户」模式，创建 `invoiceninja-order-engine` skill
2. 从 midday 提取「交易追踪+收据OCR」模式，创建 `midday-finance-tracking` skill
3. 两个 skill 对接形成完整订单生命周期：下单→发票→支付→追踪

---

## 6. 墨海出海（出海本地化子公司）

### 现有技能
| 技能 | 类型 | 说明 |
|:----|:----|:-----|
| `molin-global` | 产品型 | 出海本地化引擎（翻译+发布+SEO+合规） |
| `weblate-localization` | 设计模式 | Weblate ⭐5.8k VCS集成+MT抽象+插件Addon |

### 要吸收的项目
- **tolgee** (tolgee/tolgee ⭐3.5k) — 开发者优先的本地化平台（特性：Git同步、上下文翻译、AI翻译、CDN分发）
- **lingo.dev** (lingodotdev/lingo.dev ⭐10k) — AI i18n自动化（特性：i18n提取、AI翻译、TypeScript原生、CI流水线）

### 缺什么设计模式
1. **Git同步翻译工作流** — 源码变更→翻译任务→自动合并的CI/CD管线
2. **上下文翻译** — 在真实UI截图中直接翻译（所见即所得）
3. **i18n密钥提取** — 自动扫描代码库提取待翻译文本
4. **CDN翻译分发** — 翻译文件的CDN缓存和即时更新

### 建议注入方案
1. 从 tolgee 提取「Git同步+上下文翻译」模式，创建 `tolgee-git-localization` skill
2. 从 lingo.dev 提取「i18n提取+CI流水线」模式，创建 `lingodev-i18n-pipeline` skill
3. 与 weblate-localization 形成三层：i18n提取→翻译管理→CDN分发
4. 整合到 molin-global 的出海管线中作为「代码本地化」模块

---

## 7. 墨律法务（法务子公司）

### 现有技能
| 技能 | 类型 | 说明 |
|:----|:----|:-----|
| `molin-legal` | 产品型 | 合同审查+风险评估+NDA生成+隐私政策+合规审计等13项能力（基于ai-legal-claude ⭐1.2k） |

### 要吸收的项目
- **LaWGPT** (Tsinghua/LaWGPT ⭐10k) — 中文法律大模型（特性：法律知识增强、判决预测、法条检索、法律问答）

### 缺什么设计模式
1. **法律知识增强检索** — 基于向量数据库的法律条文+判例检索
2. **判决预测模型** — 基于案件事实预测判决结果
3. **法条-事实关联推理** — 法律三段论的结构化推理
4. **法律文书生成** — 起诉状/答辩状/判决书的结构化生成

### 建议注入方案
1. 从 LaWGPT 提取「法条检索+判决预测」模式，创建 `lawgpt-legal-reasoning` skill
2. 整合到 molin-legal 的合同审查管线：增加法律条文引用和判例参考
3. 作为 molin-legal 的「智能法条检索」工具模块

---

## 8. 墨声客服（智能客服子公司）

### 现有技能
| 技能 | 类型 | 说明 |
|:----|:----|:-----|
| `molin-customer-service` | 产品型 | 智能客服引擎（FAQ+工单+满意度） |
| `parlant-customer-agent` | 设计模式 | Parlant ⭐18k Context Engineering+C-A Rules+Journeys状态机 |

### 要吸收的项目
- **Rasa** (RasaHQ/rasa ⭐20k) — 开源对话AI框架（特性：NLU管道、故事训练、Slot filling、Custom Actions）
- **Chatwoot** (chatwooot/chatwoot ⭐25k) — 开源客服平台（特性：多收件箱、实时聊天、对话分配、CRM标签）

### 缺什么设计模式
1. **NLU意图识别管道** — 从text→intent/entity的结构化NLU流程
2. **对话状态跟踪** — 多轮对话中的上下文维护（Slot/Story）
3. **多收件箱路由** — 来自不同渠道（微信/邮件/网页）的统一收件箱
4. **对话分配** — 基于技能/负载的智能分配规则
5. **自定义Action服务器** — 在对话流中执行外部API调用的Server Action模式

### 建议注入方案
1. 从 Rasa 提取「NLU管道+对话状态机」模式，创建 `rasa-dialogue-engine` skill
2. 从 Chatwoot 提取「多收件箱+对话分配」模式，创建 `chatwoot-multi-channel` skill
3. 整合到 molin-customer-service：增强当前FAQ匹配为完整NLU，增加多渠道路由
4. 与 parlant-customer-agent 的 Context Engineering 模式融合

---

## 9. 墨算财务（财务子公司）

### 现有技能
| 技能 | 类型 | 说明 |
|:----|:----|:-----|
| `trading-agents` (business/productivity) | 工具型 | 多视角金融分析（TradingAgents 英文版），标记为墨算 |

### SKILL.md 状态
- **极其薄弱** — 只有一个归属于墨算的 trading-agents skill，且它是交易分析而非财务会计

### 要吸收的项目
- **actual** (actualbudget/actual ⭐20k) — 本地优先的个人/家庭预算工具（特性：账户管理、预算编制、交易导入、报表生成）
- **Dolibarr** (Dolibarr/dolibarr ⭐7k) — 开源ERP/CRM（特性：会计总账、发票、库存、HR、项目、税务）

### 缺什么设计模式
1. **复式记账引擎** — 借贷平衡的会计核心
2. **预算编制系统** — 预算vs实际对比+滚动预测
3. **交易导入/同步** — OFX/CSV/银行API自动同步
4. **财务报表生成** — 利润表/资产负债表/现金流量表
5. **ERP模块化架构** — 会计+库存+采购+销售的统一入口

### 建议注入方案
1. 从 actual 提取「预算管理+交易导入」模式，创建 `actual-budget-engine` skill
2. 从 Dolibarr 提取「会计总账+ERP模块」模式，创建 `dolibarr-erp-accounting` skill
3. 对接 molin-memory 的 metrics 表：实时财务数据写入
4. 对接 molin-vizro：生成财务看板

---

## 10. 墨康医疗（健康医疗子公司）

### 现有技能
| 技能 | 类型 | 说明 |
|:----|:----|:-----|
| `molin-health-assistant` | 产品型 | AI健康辅助（健身计划、营养分析、体检解读） |
| `wger-fitness-platform` | 设计模式 | Wger ⭐6.1k 健身平台5大设计模式 |

### SKILL.md 状态
- 有两个skill但内容都较浅，主要靠LLM能力组合

### 要吸收的项目
- **workout-cool** (tony-go/workout-cool ⭐2.5k) — 现代健身/训练计划应用（特性：训练计划设计、运动记录追踪、动作库、进度可视化）
- **healthchecks** (healthchecks/healthchecks ⭐10k) — 定时任务健康检查（特性：定时监控、宕机告警、通知渠道、定期报告）

### 缺什么设计模式
1. **训练计划编排** — 结构化训练计划（动作/组/次数/休息）
2. **运动记录追踪** — 用户运动数据的持久化和趋势分析
3. **健康监控调度** — 定时检查+告警+报告的完整监控架构
4. **步进式健康评估** — 基于问卷和数据的健康评分

### 建议注入方案
1. 从 workout-cool 提取「训练计划编排+运动追踪」模式，创建 `workout-plan-engine` skill
2. 从 healthchecks 提取「健康监控+定时告警」模式，创建 `health-monitoring-engine` skill
3. 整合到 molin-health-assistant：从纯LLM建议→可执行的健身/健康系统

---

## 11. 墨聘招聘（招聘子公司）

### 现有技能
| 技能 | 类型 | 说明 |
|:----|:----|:-----|
| `molin-hr-recruiter` | 产品型 | AI招聘（简历筛选、JD生成、面试题、评估报告） |
| `open-resume-engine` | 设计模式 | Open-Resume ⭐8.6k 简历构建引擎 |

### SKILL.md 状态
- 有两个skill但偏文本AI，缺少真正的招聘系统能力

### 要吸收的项目
- **frappe/hrms** (frappe/hrms ⭐3k) — 开源HR管理系统（特性：员工管理、请假审批、考勤、工资单、招聘追踪）
- **ever-gauzy** (ever-co/ever-gauzy ⭐4k) — 开源商业管理平台（特性：时间追踪、项目管理、员工费用、工时表）

### 缺什么设计模式
1. **员工主数据管理** — 组织架构+员工档案+角色权限
2. **招聘追踪系统** — 候选人管道+面试安排+Offer管理
3. **考勤/请假管理** — 请假类型+审批流程+考勤报表
4. **工资单引擎** — 工资项计算+税务+社保
5. **时间追踪+工时表** — 项目时间分配和计费

### 建议注入方案
1. 从 frappe/hrms 提取「员工管理+招聘追踪」模式，创建 `frappe-hr-engine` skill
2. 从 ever-gauzy 提取「时间追踪+项目管理」模式，创建 `ever-gauzy-project-tracking` skill
3. 整合到 molin-hr-recruiter：构成从招聘→入职→考勤→工资的完整HR链

---

## 12. 墨音音频（音频制作子公司）

### 现有技能
| 技能 | 类型 | 说明 |
|:----|:----|:-----|
| `molin-audio-engine` | 产品型 | AI音频制作（配音、播客、有声书、TTS） |
| `gptsovits-voice-cloning` | 设计模式 | GPT-SoVITS ⭐57.2k 少样本语音克隆5模式 |
| `audiocraft-audio-generation` (mlops) | 工具型 | 归属墨智（AI研发），非墨音直接所有 |

### 要吸收的项目
- **audiocraft** (facebookresearch/audiocraft ⭐22k) — 音频生成框架（特性：MusicGen文本生音乐、AudioGen音效生成、预处理管线）注：此技能已有但归属墨智，需吸收到墨音
- **LMMS** (LMMS/lmms ⭐10k) — 开源数字音频工作站（特性：DAW架构、MIDI编辑、混音台、插件效果器、钢琴卷帘）

### 缺什么设计模式
1. **DAW核心架构** — 轨道/片段/效果器/混音的层次化架构
2. **MIDI编排引擎** — 从MIDI序列到音频渲染的管线
3. **音频效果链** — DSP效果器的插件式链式处理
4. **多轨混音** — 音量/声像/EQ/压缩的混音总线

### 建议注入方案
1. 从 audiocraft (musicgen) 提取「音乐/音效生成+预处理」模式，创建 `audiocraft-audio-gen` skill（从墨智迁移到墨音专属）
2. 从 LMMS 提取「DAW架构+MIDI编排」模式，创建 `lmms-daw-engine` skill
3. 与 gptsovits-voice-cloning 整合：语音克隆+音乐生成+DAW编排的三层音频管线
4. 整合到 molin-audio-engine 作为核心技术底座

---

## 13. 墨程模板（工程模板子公司）

### 现有技能
| 技能 | 类型 | 说明 |
|:----|:----|:-----|
| `molin-template-engineer` | 产品型 | 工程模板（项目脚手架、架构文档、代码审查） |
| `cookiecutter-template-engine` | 设计模式 | Cookiecutter ⭐24.9k 5大设计模式（Facade/TemplateMethod/Hook/Strategy/Memento） |

### 要吸收的项目
- **ignite** (infinitered/ignite ⭐17k) — React Native 启动套件（特性：项目脚手架、CLI生成器、代码模板、导航+状态管理预配置）
- **html5-boilerplate** (h5bp/html5-boilerplate ⭐58k) — 前端项目标准模板（特性：前端最佳实践、性能优化、SEO基础、跨浏览器兼容）

### 缺什么设计模式
1. **CLI脚手架生成器** — 交互式CLI生成完整项目
2. **渐进式模板** — 从基础到复杂的组件级模板
3. **平台预配置** — 导航/状态管理/API层的预设集成
4. **性能基线** — .htaccess/nginx配置+缓存策略+压缩

### 建议注入方案
1. 从 ignite 提取「CLI脚手架+项目生成器」模式，创建 `ignite-cli-scaffold` skill
2. 从 html5-boilerplate 提取「前端最佳实践+性能基线」模式，创建 `h5bp-frontend-template` skill
3. 与 cookiecutter-template-engine 整合：新增CLI交互模式+前端模板集
4. 整合到 molin-template-engineer：从文字指南→可执行的脚手架

---

## 14. 墨测质量（质量测试子公司）

### 现有技能
| 技能 | 类型 | 说明 |
|:----|:----|:-----|
| `molin-qa-engineer` | 产品型 | AI质量测试（自动化测试、覆盖率、Bug发现） |
| `playwright-e2e-testing` | 设计模式 | Playwright ⭐88k 5大设计模式 |

### 要吸收的项目
- **k6** (grafana/k6 ⭐30k) — 负载/性能测试工具（特性：JS脚本、高并发模拟、指标收集、Grafana集成）
- **robotframework** (robotframework/robotframework ⭐10k) — 通用自动化测试框架（特性：关键字驱动、可扩展库、数据驱动、报告生成）

### 缺什么设计模式
1. **性能测试脚本引擎** — 虚拟用户模拟+负载模式+场景编排
2. **指标收集/聚合** — 请求延迟/吞吐量/错误率的实时收集
3. **关键字驱动测试** — 自然语言测试用例+可扩展关键字库
4. **测试报告生成** — 结构化测试报告（TestRail/JUnit XML格式）
5. **混合测试模式** — API+UI+性能的混合测试执行

### 建议注入方案
1. 从 k6 提取「性能测试+指标收集」模式，创建 `k6-load-testing` skill
2. 从 robotframework 提取「关键字驱动+测试报告」模式，创建 `robotframework-test-automation` skill
3. 与 playwright-e2e-testing 整合：E2E测试+性能测试+关键字驱动的三层
4. 整合到 molin-qa-engineer 作为完整测试工具链

---

## 15. 墨律法务（已在上文#7覆盖）

> 已在第7节完整分析

---

## 全并行执行计划

所有子公司任务同时开工，L0-中枢只做协调和收口。

### Phase 1: 项目调研 (Day 1-2)

| 子公司 | 负责人 | 行动 |
|:-------|:-------|:-----|
| 所有15家 | 各子公司Agent | 1. git clone 目标项目到 /home/ubuntu/repos/ |
| | | 2. 阅读项目README/文档/架构 |
| | | 3. 识别核心设计模式 |
| | | 4. 准备吸收方案草稿 |

### Phase 2: 设计模式提取 (Day 3-5)

| 子公司 | 要提取的模式 |
|:-------|:-------------|
| 墨数 | DAG编排 + 增量构建 + 数据质量断言 |
| 墨投 | 订单簿重建 + 微观结构分析 + 纳秒时间处理 |
| 墨域 | 自定义对象建模 + 工作流自动化 + 邮件引擎 |
| 墨育 | LMS课程管理 + 测验引擎 + 插件架构 |
| 墨单 | 发票引擎 + 交易追踪 + 收据OCR + 客户门户 |
| 墨海 | Git同步翻译 + 上下文翻译 + i18n提取 + CDN分发 |
| 墨律 | 法律检索 + 判决预测 + 法条推理 + 文书生成 |
| 墨声 | NLU管道 + Slot状态跟踪 + 多收件箱 + Action Server |
| 墨算 | 复式记账 + 预算编制 + 交易导入 + 财务报表 + ERP模块 |
| 墨康 | 训练计划编排 + 运动追踪 + 健康监控 + 步进评估 |
| 墨聘 | 员工主数据 + 招聘追踪 + 考勤审批 + 工资单 + 时间追踪 |
| 墨音 | DAW架构 + MIDI编排 + 音频效果链 + 多轨混音 + MusicGen |
| 墨程 | CLI脚手架 + 渐进式模板 + 平台预配置 + 性能基线 |
| 墨测 | 性能测试 + 指标收集 + 关键字驱动 + 测试报告 + 混合模式 |

### Phase 3: 技能创建 (Day 6-10)

每家子公司并行创建 2-3 个新 skill（设计模式注入格式）：

```
skills/<subsidiary>/
├── <project1>-<pattern>/SKILL.md     # 设计模式提取
└── <project2>-<pattern>/SKILL.md     # 设计模式提取
```

### Phase 4: 集成验证 (Day 11-12)

1. L0-中枢检查所有新 skill 的 `molin_owner` 标记正确
2. 运行 `molin-memory import-skills` 注册新技能
3. 每个子公司至少运行 1 个端到端测试
4. 更新 skills-index.md

### 特殊注意事项

1. **墨单、墨算** — 这两家目前只有子公司定义骨架，要从零构建，优先给它们分配更多资源
2. **墨音/墨康** — 已有设计模式 skill 但缺产品实现，吸收后补齐产品层
3. **墨声** — 已有 parlant 模式+Rasa Chatwoot 项目，吸收后将成为最强客服子公司
4. **墨域** — twenty(30k⭐) 是大型项目，可能需要分多轮吸收
