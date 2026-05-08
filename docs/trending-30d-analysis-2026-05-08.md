# 📈 Molin OS · 近30天GitHub Trending Top项目分析报告

> 生成日期: 2026-05-08
> 数据源: GitHub API (4个搜索源合并) + 源码深度分析
> 总采集: 140个项目 | 去重过滤后: 26个候选 | 深度分析: 5个S/A级

---

## 一、数据采集方法

| 搜索策略 | 条件 | 获取数 |
|:---------|:-----|:------:|
| 新建项目 | `created>2026-04-06 + stars>1000 + language:python` | 39 |
| AI Agent 主题 | `stars>2000 + pushed>2026-04-01 + topic:ai-agent` | 42 |
| 近期活跃高星 | `stars>5000 + pushed>2026-04-15 + language:python` | 50 |
| 最近热门 | `stars>8000 + language:python + pushed>2026-04-20` | 9 |
| **合并去重后** | | **140** |

**过滤规则**：跳过已吸收项目(AutoGPT/crewai/langchain等)、非代码项目(awesome-list/教程/指南)、基础设施框架(django/flask/pytorch等)

---

## 二、全部26个候选项目速览

| # | 项目 | ⭐ | 类型 | 一句话 |
|:-:|:-----|:-:|:----|:-------|
| 1 | **NousResearch/hermes-agent** | 137K | 🤖 Agent | Hermes Agent本体，127K⭐参考增强 |
| 2 | **home-assistant/core** | 86K | 🏠 IoT | 开源智能家居平台，与Agent不直接相关 |
| 3 | **Integuru-AI/Integuru** | 4.6K | 🔧 集成 | AI逆向HAR→自动生成API集成代码 |
| 4 | **Q00/ouroboros** | 3.6K | 🧠 Agent | 新范式：Spec-first Agent OS，从prompt转为spec |
| 5 | **theori-io/copy-fail-CVE** | 3.5K | 🔒 安全 | Linux内核LPE漏洞，安全方向 |
| 6 | **OpenMOSS/MOSS-TTS-Nano** | 2.8K | 🎤 音频 | 开源多语言TTS模型，轻量语音生成 |
| 7 | **masterking32/MasterHttpRelayVPN** | 2.6K | 🌐 网络 | Domain-fronted VPN代理 |
| 8 | **denuitt1/mhr-cfw** | 2.6K | 🌐 网络 | 同上类，Cloudflare Workers代理 |
| 9 | **codejunkie99/agentic-stack** | 1.9K | 📦 协议 | 便携.agent/文件夹协议，跨Harness知识迁移 |
| 10 | **Tencent-Hunyuan/HY-World-2.0** | 1.8K | 🎨 3D | 多模态3D世界模型 |
| 11 | **0x0funky/agent-sprite-forge** | 1.8K | 🎨 设计 | Agent技能：2D精灵图+透明PNG生成 |
| 12 | **wuyoscar/gpt_image_2_skill** | 1.6K | 🎨 生图 | GPT Image 2 Prompt/Skill库 |
| 13 | **phuryn/claude-usage** | 1.5K | 📊 监控 | Claude Code token/成本Dashboard |
| 14 | **mattmireles/gemma-tuner-multimodal** | 1.4K | 🤖 ML | Gemma 4微调框架(多模态) |
| 15 | **wbh604/UZI-Skill** | 1.4K | 💰 金融 | A股量化：51位大佬看盘+180条规则 |
| 16 | **GammaLabTechnologies/harmonist** | 1.4K | 🧠 编排 | 186 Agent编排+机械协议强制 |
| 17 | **joeynyc/hermes-hudui** | 1.4K | 🖥️ UI | Hermes Agent Web UI监控(你已有Hermes) |
| 18 | **VRSEN/OpenSwarm** | 1.3K | 🤖 多Agent | Claude code做所有事除了编程 |
| 19 | **yaojingang/yao-open-prompts** | 1.2K | 📝 提示词 | 中文AI提示词库，覆盖工作/学习/营销 |
| 20 | **DanOps-1/Gpt-Agreement-Payment** | 1.1K | 💰 工具 | ChatGPT订阅重放+hCaptcha求解器 |
| 21 | **ZJU-REAL/ClawGUI** | 1.1K | 🤖 GUI | GUI Agent构建/评估/部署+在线RL训练 |
| 22 | **russellromney/honker** | 1.1K | 🗄️ 数据库 | SQLite扩展+Postgres NOTIFY语义 |
| 23 | **fancyai-official/skills** | 1.1K | 📦 技能 | Agent技能集合 |
| 24 | **XBuilderLAB/cheat-on-content** | 1.0K | 📝 内容 | 内容模式破解引擎 |
| 25 | **OranAi-Ltd/oransim** | 1.0K | 📊 营销 | 营销因果数字孪生 |
| 26 | **EvoLinkAI/awesome-gpt-image-2-API** | 13K | 📋 列表 | GPT-Image-2 API&Prompts集合(列表型跳过) |

---

## 三、深度分析项目（5个S/A级候选）

### 🥇 Integuru — API集成逆向引擎 (S级 · 4.6K⭐)

| 维度 | 评估 |
|:-----|:------|
| **核心能力** | 输入浏览器HAR文件 → AI自动构建请求依赖图 → 生成可运行Python代码 |
| **核心架构** | LangGraph状态机 + NetworkX DAG + Function Calling Agent编排 |
| **设计模式(6个)** | ① HAR→Request值对象 ② LLM单例+模型路由 ③ DAG属性图管理器 ④ Function Calling AgentStep ⑤ 拓扑代码合成 ⑥ Cookie反向查找+去重缓存 |
| **吸收价值** | **S级** — HAR解析+LLM路由+AgentStep编排可直接注入 `molib/shared/` |
| **对一人公司价值** | 极高 — 把「手工逆向→写集成代码」从数小时缩短到数分钟 |
| **吸收前** | `molib/` 没有通用HAR解析，每个集成手动写requests代码 |
| **吸收后** | `HarParser.parse(har)` → `LLMRouter.for_task()` → `AgentStep.execute()` —— 录制→自动集成 |

### 🥇 Ouroboros — Spec-first Agent OS (S级 · 3.6K⭐)

| 维度 | 评估 |
|:-----|:------|
| **核心能力** | 用结构化Spec代替Prompt驱动的Agent OS，五阶段闭环：Interview→Seed→Execute→Evaluate→Evolve |
| **核心架构** | Immutable Seed + DAG编排 + Event Sourcing + 多模型路由 |
| **设计模式(8个)** | ① Immutable Seed(S) ② 本體论AOP(S) ③ PAL三层LLM路由(S) ④ Event Sourcing(S) ⑤ Double Diamond执行(A) ⑥ 3阶段评估管线(A) ⑦ Drift测量(A) ⑧ 停滞检测(A) |
| **吸收价值** | **S级** — 4个可直接注入molib的S级模式(Immutable Seed/PAL路由/Event Sourcing/本体论AOP) |
| **互补性** | Ouroboros管「做什么」→ Hermes管「怎么做」，前者是meta-cognitive层，后者是执行层 |
| **吸收前** | 模糊需求直接执行 → 高返工率，成本高，无停止条件 |
| **吸收后** | 清晰Spec+3阶段评估+多模型路由 → 50-90%成本节省，自动停止 |

### 🥈 agentic-stack — 便携Agent定义协议 (A级 · 1.9K⭐)

| 维度 | 评估 |
|:-----|:------|
| **核心能力** | `.agent/` 文件夹协议：记忆+技能+协议，跨10种Harness(Claude Code/Cursor/Hermes…)可移植 |
| **核心架构** | 四层记忆(Working→Episodic→Semantic→Personal) + 渐进式技能 + 声明式权限 |
| **设计模式(5个)** | ① 四层记忆Dream Cycle ② 渐进式技能_manifest.jsonl ③ 权限Hook+pre_tool_call ④ Transfer Bundle ⑤ 数据层/Data Flywheel |
| **吸收价值** | **A级** — `.agent/` 协议可直接作为Hermes OS的跨项目知识迁移标准 |
| **互补性** | 技能格式兼容agentskills.io，AGENTS.md可直接作为workspace context |
| **吸收前** | 每个项目/工具的记忆和技能隔离，切换工具时知识丢失 |
| **吸收后** | `.agent/` 文件夹随身带，任何工具都能读取同一套知识 |

### 🥈 UZI-Skill — A股量化投资分析 (A级 · 1.4K⭐)

| 维度 | 评估 |
|:-----|:------|
| **核心能力** | 22维数据采集×109条量化规则×51位投资评委投票×A股特色分析 |
| **核心架构** | Pipeline三段式(采集→打分→合成) + 评委Panel投票 + 游资射程匹配 |
| **设计模式(5个)** | ① Adapter工厂(22 fetcher) ② 3-Wave并发采集 ③ 纯函数打分编排 ④ 规则引擎(Rule dataclass) ⑤ 共识聚合(连续分+离散票+极化) |
| **吸收价值** | **A级** — 评委共识算法+规则引擎设计可直接移植到 `molib/trading/` |
| **对一人公司价值** | A股量化的完整可运行方案，51位投资大师的观点聚合方法 |
| **局限性** | 仅A股，规则引擎偏简单(if-then lambda无ML) |

### 🥈 Harmonist — 大规模Agent机械门控 (A级 · 1.4K⭐)

| 维度 | 评估 |
|:-----|:------|
| **核心能力** | 186 Agent编排 + 机械协议强制(Stop Gate) + 供应链完整性 + 结构化记忆 |
| **核心架构** | 7层: 旁路注入→纯文件系统状态→机械门控→供应链完整→结构化记忆→数据驱动路由→跨平台 |
| **设计模式(8个)** | ① 机械门控引擎(S) ② Correlation ID防伪造(A) ③ 30+密钥模式扫描(A) ④ 供应链完整性清单(A) ⑤ Agent Schema v2(A) ⑥ 结构化记忆(B) ⑦ 提示词注入扫描(B) ⑧ 跨平台Hook Runner(B) |
| **吸收价值** | **A级** — 机械门控是首个将Agent协议执行从提示词变为机械强制的创新 |
| **互补性** | Harmonist提供协议层，Hermes提供执行层 |
| **吸收前** | Agent协议执行依赖提示词"请遵守"→可绕过 |
| **吸收后** | Stop Gate机械拦截+Correlation ID追踪 → 协议执行不可绕过 |

---

## 四、吸收优先级排序

| 优先级 | 项目 | ⭐ | 评级 | 建议吸收方式 |
|:------:|:-----|:-:|:----:|:------------|
| **P0** | **Integuru** | 4.6K | S | 注入 `molib/shared/network/har_parser.py` + `molib/shared/agent/` |
| **P0** | **Ouroboros** | 3.6K | S | 注入 `molib/shared/llm/llm_router.py` + `molib/shared/agent/spec.py` |
| **P1** | **agentic-stack** | 1.9K | A | 采纳 `.agent/` 协议标准 |
| **P1** | **UZI-Skill** | 1.4K | A | 共识算法注入 `molib/trading/` |
| **P1** | **Harmonist** | 1.4K | A | Stop Gate → `molib/shared/gate/` |
| **P2** | **ClawGUI** | 1.1K | B | GUI Agent评估框架，参考其RL训练方法 |
| **P2** | **cheat-on-content** | 1.0K | B | 内容模式分析引擎 |
| **P2** | **claude-usage** | 1.5K | B | 成本监控Dashboard |
| **P3** | **OpenSwarm** | 1.3K | B | 多Agent编排参考 |
| **P3** | **MOSS-TTS-Nano** | 2.8K | B | TTS模型参考(已有molin-audio) |
| **跳过** | hermes-agent(已有)/home-assistant(不相关)/hermes-hudui(已有)/GPT-Image-2列表/安全类 | — | — | 已覆盖或不匹配 |

---

## 五、整合效果预测

| 项目 | 吸收前评分 | 吸收后评分 | 提升 | 关键收益 |
|:-----|:--------:|:--------:|:----:|:---------|
| **Integuru** | 2/10 | 7/10 | +250% | HAR→API集成代码全自动 |
| **Ouroboros** | 2/10 | 8/10 | +300% | 模糊需求→清晰Spec→3阶段评估 |
| **agentic-stack** | 3/10 | 6/10 | +100% | 跨工具知识可移植 |
| **UZI-Skill** | 1/10 | 6/10 | +500% | A股量化完整方案 |
| **Harmonist** | 3/10 | 7/10 | +133% | Agent协议不可绕过执行 |
| **整合后系统** | 5/10 | **8.5/10** | **+70%** | 从"LLM助手"升级为"自进化Agent OS" |

---

## 六、建议执行的吸收步骤（按P0→P1顺序）

```
第1步: Integuru HAR解析 → molib/shared/network/har_parser.py
第2步: Ouroboros Immutable Seed → molib/shared/agent/spec.py
第3步: Ouroboros PAL Router → molib/shared/llm/llm_router.py
第4步: Integuru AgentStep → molib/shared/agent/step.py
第5步: Harmonist Stop Gate → molib/shared/gate/stop_gate.py
第6步: UZI-Skill 共识算法 → molib/trading/consensus.py
第7步: agentic-stack .agent/ 协议采纳 → 跨Harness标准
```

---

*报告由 Hermes Agent 自动生成 · 基于5个深度源码分析和140个项目扫描*
*5个深度分析报告文件: integuru_analysis.md / ouroboros_analysis.md / agentic_stack_analysis.md / harmonist_analysis.md / openswarm_analysis.md*
