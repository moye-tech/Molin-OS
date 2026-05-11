# 墨麟AI集团 · 系统全景文档

> **版本**: v5.0.0 · **Git**: `960b2db` · **更新**: 2026-05-11
>
> 墨麟OS (Molin-OS) — 22 家 AI 子公司的全栈智能操作系统。
> 由 Hermes Agent 驱动，通过 Feishu/CLI/API 三通道交互。

---

## 一、架构总览

```
                        ┌──────────────────────────┐
                        │      Hermes Agent         │
                        │   (CEO · 大脑 · 决策)      │
                        └──────────┬───────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
        ┌──────────┐        ┌──────────┐        ┌──────────┐
        │  Feishu  │        │   CLI    │        │   API    │
        │  飞书对话 │        │ python -m│        │  Server  │
        │          │        │  molib   │        │  :8648   │
        └────┬─────┘        └────┬─────┘        └────┬─────┘
             │                   │                   │
             └───────────────────┼───────────────────┘
                                 ▼
                    ┌───────────────────────┐
                    │   SmartDispatcher     │
                    │   (14条 Open Design路由│
                    │   + 22条协作规则)       │
                    └───────────┬───────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         ▼                      ▼                      ▼
   ┌──────────┐          ┌──────────┐          ┌──────────┐
   │ WorkerChain│         │ Handoff  │          │SOP 金库  │
   │  多Worker  │         │  自动路由 │          │  经验匹配 │
   └──────────┘          └──────────┘          └──────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  22 家 AI 子公司 Worker │
                    │  + 465 Hermes 技能     │
                    └───────────────────────┘
```

### 堆栈

| 层 | 技术 |
|:--|:--|
| Agent 框架 | Hermes Agent (Python) |
| 对话入口 | Feishu/Lark · CLI (prompt_toolkit) · TUI (Ink/React) · API Server |
| 推理后端 | DeepSeek V4 (主) · DashScope (视觉/TTS) · OpenRouter (免费路由) |
| 执行引擎 | `python -m molib` — 纯 Python stdlib 优先 |
| 设计工程 | Open Design v0.6.0 (Node.js daemon :55888) — 149 设计系统 × 134 技能 |
| 记忆系统 | Hermes Memory + ChromaDB 向量库 + SuperMemory 云端 |
| 知识管理 | Obsidian (iCloud 同步) — 7 目录结构 |
| 部署 | macOS M2 (8GB) · Python 3.11 · Node 24 · Git(Hub) |

---

## 二、22 家 AI 子公司

### VP 营销 (5 家)

| Worker | 公司名 | 核心能力 | CLI 命令 |
|:--|:--|:--|:--|
| `content_writer` | 墨笔文创 | 文案创作、公众号、小红书、多语言 | `molib content write` |
| `ip_manager` | 墨韵IP | IP 衍生、商标、版权、品牌管理 | `molib handoff route --task "IP"` |
| `designer` | 墨图设计 | **Open Design 全栈 (149DS×134技能) + FLUX.2 生图** | `molib design web/image` |
| `short_video` | 墨播短视频 | 短视频脚本+生成 | `molib video script/generate` |
| `voice_actor` | 墨声配音 | TTS 语音合成、播客、多语言配音 | `molib avatar` |

### VP 运营 (4 家)

| Worker | 公司名 | 核心能力 | CLI 命令 |
|:--|:--|:--|:--|
| `crm` | 墨域私域 | CRM 管理、用户分层、社群运营 | `molib crm segment/push` |
| `customer_service` | 墨声客服 | 自动化客服 (闲鱼/飞书) | `molib xianyu reply` |
| `ecommerce` | 墨链电商 | 订单管理、电商平台 | `molib order list/status` |
| `education` | 墨学教育 | 课程设计、学习路径、AI 辅导 | `molib handoff route --task "教育"` |

### VP 技术 (4 家)

| Worker | 公司名 | 核心能力 |
|:--|:--|:--|
| `developer` | 墨码开发 | 软件开发、代码生成、CLI 工具 |
| `ops` | 墨维运维 | 服务器部署、DevOps、环境配置 |
| `security` | 墨安安全 | 代码审计、安全评估、漏洞扫描 |
| `auto_dream` | 墨梦AutoDream | AI 自动化实验、记忆蒸馏、自学习 |

### VP 财务 (1 家)

| Worker | 公司名 | 核心能力 | CLI 命令 |
|:--|:--|:--|:--|
| `finance` | 墨算财务 | 记账、预算、成本控制、报表 | `molib finance record/report` |

### VP 战略 (3 家)

| Worker | 公司名 | 核心能力 | CLI 命令 |
|:--|:--|:--|:--|
| `bd` | 墨商BD | 商务拓展、合作方案 | `molib handoff route --task "BD"` |
| `global_marketing` | 墨海出海 | 多语言出海、全球化运营 | `molib handoff route --task "出海"` |
| `research` | 墨研竞情 | 竞争分析、趋势研究、情报采集 | `molib intel trending/search` |

### 共同服务 (3 家)

| Worker | 公司名 | 核心能力 |
|:--|:--|:--|
| `legal` | 墨律法务 | 合同审查、合规风险评估 |
| `knowledge` | 墨脑知识 | RAG 知识库、长期记忆、SOP 管理 |
| `data_analyst` | 墨测数据 | 数据分析、BI 报表、质量追踪 |

### 专项 (2 家)

| Worker | 公司名 | 核心能力 | CLI 命令 |
|:--|:--|:--|:--|
| `trading` | 墨投交易 | 量化交易策略、信号、回测 | `molib trading signal/analyze` |
| `scrapling` | 墨研Scrapling | 网页抓取、浏览器指纹模拟 | `molib scrap fetch` |

---

## 三、墨图设计 v2.2 — Open Design 集成

> ⭐ 34K · Apache 2.0 · 149 设计系统 × 134 技能

### 架构

```
python -m molib design web --prompt="..." --action=landing_page --ds=apple
    │
    ▼
Designer._web_design()
    ├── GET /api/skills/saas-landing      → 技能规范
    ├── GET /api/design-systems/apple     → Apple 设计系统 (17,764 chars)
    ├── LLM (DeepSeek V4)                 → 生成 HTML/CSS
    ├── POST /api/artifacts/save          → daemon 预览
    └── 💾 ~/Molin-OS/output/designs/     → 本地 HTML
```

### 14 个快捷动作

| action | 映射 skill | 说明 |
|:--|:--|:--|
| `landing_page` | `saas-landing` | SaaS 落地页 |
| `dashboard` | `dashboard` | 数据分析仪表盘 |
| `pitch_deck` | `html-ppt-pitch-deck` | 投资人 PPT |
| `blog_post` | `blog-post` | 博客文章 |
| `pricing_page` | `pricing-page` | 定价方案页 |
| `mobile_app` | `mobile-app` | 移动端原型 |
| `web_prototype` | `web-prototype` | 通用网页原型 |
| `docs_page` | `docs-page` | 文档/知识库页 |
| `waitlist` | `waitlist-page` | 预发布等待页 |
| `login_flow` | `login-flow` | 登录认证流程 |
| `weekly_report` | `weekly-update` | 周报 |
| `finance_report` | `finance-report` | 财务报表 |
| `kami_landing` | `kami-landing` | 日式简约落地页 |
| `ppt` | `html-ppt-pitch-deck` | PPT (同 pitch_deck) |

### Top 10 设计系统

| ID | 风格 | 适用场景 |
|:--|:--|:--|
| `apple` | 极简白 + SF Pro | 科技/SaaS |
| `stripe` | 深蓝 + 渐变 | 金融/支付 |
| `airbnb` | 暖色 + Cereal | 社区/平台 |
| `ant` | 蓝白企业级 | 后台/中台 |
| `arc` | 暗色霓虹 | 开发者工具 |
| `bento` | 网格卡片 | 产品展示 |
| `agentic` | AI 原生 | AI Agent |
| `notion` | 极简黑白 | 文档/知识库 |
| `linear` | 暗色 + 紫 | 项目工具 |
| `vercel` | 黑 + 几何 | 开发者平台 |

---

## 四、CLI 命令手册

### 核心命令

```bash
python -m molib health                              # 系统健康检查
python -m molib help                                 # 命令列表
```

### 内容创作 (墨笔文创)

```bash
python -m molib content write --topic "主题" --platform xhs
python -m molib content publish --platform xhs --draft-id xxx
```

### 设计 (墨图设计 v2.2)

```bash
# AI 生图
python -m molib design image --prompt "描述" --style 写实

# Open Design 全栈网页
python -m molib design web --prompt "墨麟官网" --action landing_page --ds apple
python -m molib design web --prompt "销售看板" --action dashboard --ds stripe
python -m molib design web --prompt "融资计划" --action pitch_deck --ds airbnb
python -m molib design web --prompt "定价方案" --action pricing_page --ds vercel
```

### 视频 (墨播短视频)

```bash
python -m molib video script --topic "主题" --duration 60s
python -m molib video generate --topic "主题" --engine mpt|pixelle
```

### 情报 (墨研竞情)

```bash
python -m molib intel trending
python -m molib intel firecrawl scrape --url URL
python -m molib intel firecrawl search --query Q
python -m molib intel save --topic "主题" --summary "..."
```

### 财务 (墨算财务)

```bash
python -m molib finance record --type expense --amount 100 --note "说明"
python -m molib finance report
```

### 电商 (墨链电商)

```bash
python -m molib order list --status pending
python -m molib order status --order-id xxx
```

### 交易 (墨投交易)

```bash
python -m molib trading signal --symbol BTC/USDT
python -m molib trading analyze --market-type crypto --symbol BTC/USDT
```

### 同步 & 知识

```bash
python -m molib sync            # CocoIndex 增量同步
python -m molib query "SQL"     # MQL 知识查询
python -m molib handoff route --task "内容创作"  # Handoff 自动路由
python -m molib plan create --title "..." --description "..."
```

### 数字人 (墨声配音)

```bash
python -m molib avatar create --text "你好" --image pic.jpg
python -m molib avatar list-voices
python -m molib avatar check
```

---

## 五、SmartDispatcher 路由表

> 用户说一句话 → 自动匹配 WorkerChain → 并行/串行执行 → 返回结果

| 触发词 | Worker 链 |
|:--|:--|
| 落地页 / landing | `[designer]` |
| 仪表盘 / dashboard | `[designer, data_analyst]` |
| PPT / pitch | `[designer, content_writer]` |
| 网页设计 / 设计网页 | `[designer]` |
| UI设计 / 原型 | `[designer]` |
| 品牌视觉 | `[designer, ip_manager]` |
| 定价页 | `[designer, bd]` |
| 文档页 | `[designer, knowledge]` |
| 博客 | `[content_writer, designer]` |
| 营销文案 / 小红书 | `[research, content_writer, designer]` |
| 短视频 | `[research, content_writer, short_video, voice_actor]` |
| 产品上架 | `[content_writer, designer, ecommerce]` |
| 竞品报告 | `[research, data_analyst, content_writer]` |
| 安全审计 | `[security, developer, ops]` |
| 部署上线 | `[developer, ops, security]` |
| 交易策略 | `[trading, research, data_analyst]` |
| 出海 / 全球化 | `[research, global_marketing, legal]` |

---

## 六、飞轮管线

> 每日 08:00-10:00 全自动运行

```
08:00  墨研竞情 → relay/intelligence_morning.json     (情报采集)
09:00  墨笔文创 → relay/content_flywheel.json          (内容生成)
09:30  墨测数据 → relay/distribution_plan.json         (分发策略)
10:00  墨研竞情 → relay/briefing_daily.md              (简报推送)
```

---

## 七、技能系统

### 技能生态

| 层级 | 数量 | 位置 |
|:--|:--|:--|
| Hermes 内置技能 | 465 | `~/.hermes/skills/` |
| Molin-OS 技能 | 30 | `~/Molin-OS/skills/` |
| Open Design 技能 | 134 | daemon `:55888` |
| Open Design 设计系统 | 149 | daemon `:55888` |

### 核心技能分类

| 类别 | 数量 | 代表 |
|:--|:--|:--|
| Agent Engineering | 15+ | backend-architect, code-reviewer, frontend |
| Marketing | 20+ | content-creator, SEO, social-media |
| Product | 15+ | product-manager, PRD, user-stories |
| Creative | 30+ | ascii-art, architecture-diagram, p5js |
| Data Science | 10+ | jupyter, data-analysis, visualization |
| ML Ops | 20+ | unsloth, vllm, llama-cpp, huggingface |
| DevOps | 10+ | kanban, webhook, cron |
| GitHub | 8 | auth, code-review, pr-workflow, issues |
| Molin-OS | 20+ | 全部 22 家 Worker 对应技能 |
| Design | 5+ | molin-open-design, excalidraw, pixel-art |

---

## 八、记忆 & 知识管理

### 三层记忆

```
L1: Hermes Memory (SQLite FTS5)
    └── 16 条持久化记忆 · 跨会话 · ~93% 容量

L2: ChromaDB 向量库
    └── ~/.hermes/memory/chroma_db/ · 语义检索

L3: SuperMemory 云端
    └── app.supermemory.ai · GitHub 雷达日报同步
```

### Obsidian 知识库

```
Vault: ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/
同步: iCloud (免费 · 多设备 · 同 Apple ID)

目录:
  00-Inbox/      — 临时收集
  10-Daily/      — 日报/GitHub雷达 (自动)
  20-Reports/    — 周报/月报/专项
  30-Knowledge/  — 知识卡片
  40-Projects/   — 项目追踪
  50-Archive/    — 归档
  99-Templates/  — 模板
```

### 同步管道

```bash
# 报告 → Obsidian
python3 ~/Molin-OS/scripts/obsidian_sync.py

# 报告 → SuperMemory
python3 ~/.hermes/scripts/supermemory_sync.py
```

---

## 九、部署 & 环境

### 硬件

| 项目 | 值 |
|:--|:--|
| 设备 | MacBook (Apple Silicon M2) |
| 内存 | 8 GB unified |
| 磁盘 | 169 GB 可用 |
| OS | macOS 26.4.1 |

### 运行时

| 组件 | 版本 | 端口 |
|:--|:--|:--|
| Hermes Agent | latest | — |
| Molin-OS | v5.0.0 | Web UI :8648 |
| Open Design Daemon | v0.6.0 | `:55888` |
| Python | 3.11.15 | — |
| Node.js | v24.14.0 | — |
| pnpm | 11.0.9 / 10.33.2 (Corepack) | — |
| ngrok | v3.39.1 | 反向代理 :8080 |

### 连接平台

| 平台 | 状态 |
|:--|:--|
| Feishu (飞书) | ✅ Connected |
| API Server (:8648) | ✅ Connected |
| Local (文件系统) | ✅ |

### 关键约束

| 约束 | 说明 |
|:--|:--|
| 无 Docker | 用户明确拒绝 · 所有方案纯 Python/macOS 原生 |
| 无本地 LLM | 不跑 Ollama · 用云端 API (DeepSeek/DashScope) |
| 网络限制 | GitHub >10MB 超时 · 需走 Clash 代理 (HK 出口) |
| stdlib 优先 | 新模块零外部依赖 · FastAPI/requests 除外 |
| M2 8GB | ComfyUI 不可用 · 用 diffusers MPS 方案2 |

---

## 十、治理 & 安全

### 四级治理

| 级别 | 名称 | 说明 |
|:--|:--|:--|
| L0 | 自动执行 | 内容生成、数据采集、例行报告 — 无需确认 |
| L1 | 通知 | 完成后飞书通知创始人 |
| L2 | 审批 | 报价 >¥100、承诺交付、对外发布、修改配置 |
| L3 | 董事会审批 | 重大决策需全面评估 |
| L4 | 绝对禁止 | 涉及真实现金/转账/支付 — 绝不碰 |

### CEO 委托协议 v2.0

```
核心原则: "问题问我，产出找他们"

决策树:
  Step 1: 分类 (是执行类还是问答类?)
  Step 2: 查历史 (之前谁做过?)
  Step 3: 规划 WorkerChain
  Step 4: 委托执行
  Step 5: 存档

3秒自查:
  ① 自己生成内容? → 委托
  ② 只用了一个Worker? → 考虑WorkerChain
  ③ 告诉创始人谁在做/多久/产出在哪?
```

---

## 十一、版本历史

| 版本 | 日期 | 关键变更 |
|:--|:--|:--|
| v5.0.0 | 2026-05-11 | 系统标准化审计 · Open Design 集成 · Obsidian 知识库 |
| v2.5 | 2026-05-10 | 文档驱动开发 · OpenRouter 免费路由 · FeishuCardRouter |
| v2.2 | 2026-05-09 | 墨图设计 Open Design 全栈 · 14 快捷动作 |
| v2.1 | 2026-05-08 | FLUX.2 生图 · Firecrawl v2 · 12 外部桥 |
| v2.0 | 2026-05-06 | SmartDispatcher · WorkerChain · Handoff 自动路由 |
| v1.0 | 2026-04 | 22 家 Worker · CLI · 飞轮管线 · SOP 金库 |

---

> 📋 本文档由 Hermes Agent 自动生成 · 最后同步: `960b2db`
> 
> 🌐 GitHub: [moye-tech/Molin-OS](https://github.com/moye-tech/Molin-OS) (Private)
> 
> 🧠 Obsidian: `obsidian://open?vault=iCloud~md~obsidian`
