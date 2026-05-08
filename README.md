<!-- 墨麟OS README v5.0 — 基于系统真实状态 -->

# 🏛️ 墨麟OS (Molin OS)

<p align="center">
  <strong>AI 一人公司操作系统 · 6层架构 · 290技能 · 25家子公司Worker · 22营收实体</strong><br>
  从一句话指令到完整企业级AI操作系统，一个人就是一个集团
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12+-00b894?style=flat-square&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-00b894?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/skills-290-success?style=flat-square" alt="Skills">
  <img src="https://img.shields.io/badge/workers-25-success?style=flat-square" alt="Workers">
  <img src="https://img.shields.io/badge/status-v5.0-blueviolet?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/monthly_revenue-¥52K-ff6b6b?style=flat-square" alt="Revenue">
  <img src="https://img.shields.io/badge/吸收了-27个开源项目-10b981?style=flat-square" alt="Absorbed">
</p>

---

## 一句话

**墨麟OS 是一个人用一台服务器就能运营的AI公司操作系统。** 你拥有22个垂直子公司（墨笔文创/墨域私域/墨码开发…），每个子公司有专属Worker执行文件和技能库。Hermes Agent 是CEO大脑，你通过它调动所有子公司。零空转设计——有任务才消耗token。

## 架构总览（6层）

```
你（创始人/董事会）
    │
┌── L0 中枢 ──────────────────────────────────────┐
│  CEO引擎 (Hermes Agent)：意图路由·风险引擎·SOP  │
│  治理规则 (L0自动/L1通知/L2审批/L3绝不碰现金)    │
└──────────────────┬──────────────────────────────┘
                   │ 决策流
    ┌──────────────┼─────────────────────┐
    │ L1 营收子公司 (22家)                │
    │ ┌─ 营销(5) ─┐ ┌─ 运营(4) ──────┐ │
    │ │墨笔·墨韵· │ │墨域·墨声·       │ │
    │ │墨图·墨播· │ │墨链·墨学         │ │
    │ │墨声配音    │ │                  │ │
    │ ├─ 技术(4) ─┤ ├─ 财务(1) ──────┤ │
    │ │墨码·墨维· │ │墨算              │ │
    │ │墨安·墨梦   │ │                  │ │
    │ ├─ 战略(3) ─┤ ├─ 共同(3) ──────┤ │
    │ │墨商·墨海· │ │墨律·墨脑·墨测    │ │
    │ │墨研        │ │                  │ │
    │ └────────────┘ └─────────────────┘ │
    │ 目标: ¥52,000/月                    │
    └────────────────┬────────────────────┘
                     │ 服务
    ┌────────────────┼────────────────────┐
    │ L2-L5 基础设施                         │
    │   Hermes Toolchain · Skills引擎 ·    │
    │   飞书/闲鱼/小红书集成 · Config体系    │
    │   MCP Server · 记忆系统 · 飞轮管线     │
    └──────────────────────────────────────┘
```

## 核心指标（基于真实数据）

| 指标 | 数值 | 说明 |
|:----|:----:|:-----|
| 自主研发技能 | **290个** SKILL.md | `skills/` 目录 |
| 子公司Worker | **25个** Worker 执行文件 | `molib/agencies/workers/` |
| 营收子公司数 | **22家** L1实体 | 含5营销+4运营+4技术+1财务+3战略+3共同+2预置 |
| 已吸收开源项目 | **27个** (~520K⭐) | 设计模式注入到技能库 |
| Handoff路由 | **16家** 注册了自动路由 | `handoff_register.py` |
| CLI命令 | **25+** 统一入口 | `python3 -m molib <cmd>` |
| 自动化脚本 | **24个** Bots | `bots/` 闲鱼/小红书/日报/飞轮/生图/TTS |
| 商业化方案 | **9个** 文档+安装器 | `business/` |
| 文档 | **27个** 系统文档 | `docs/` |
| 定时作业 | **8个** cron | 默认暂停，零空转 |
| 总收入目标 | **¥52,000/月** | 22家子公司加权 |
| 总预算 | **¥3,490/月** | API 成本控制 |
| ROI | **14.9x** | 收入/成本 |

## 快速部署

```bash
git clone https://github.com/moye-tech/-Hermes-OS.git
cd -Hermes-OS
python3 -m venv venv          # 创建虚拟环境
source venv/bin/activate
pip install -r requirements.txt
pip install -e .              # 安装 molib 包
cp .env.example .env          # 编辑填入API Keys
python -m molib health        # 验证安装
```

一键部署（自动安装依赖+创建目录）：

```bash
bash setup.sh
```

## CLI 统一入口（25+ 命令）

```bash
python3 -m molib health              # 系统健康检查
python3 -m molib help                 # 所有命令列表

python3 -m molib content write       # 墨笔文创 — 内容创作
python3 -m molib content publish     # 小红书发布
python3 -m molib design image        # 墨图设计 — 图片生成
python3 -m molib video script        # 墨播短视频 — 视频脚本
python3 -m molib tts generate        # 墨声配音 — 语音合成
python3 -m molib crm segment         # 墨域私域 — 用户分层
python3 -m molib xianyu reply        # 墨声客服 — 闲鱼回复
python3 -m molib order list          # 墨链电商 — 订单列表
python3 -m molib finance report      # 墨算财务 — 财务报表
python3 -m molib trading signal      # 墨投交易 — 交易信号
python3 -m molib intel trending      # 墨研竞情 — 趋势扫描
python3 -m molib data analyze        # 墨测数据 — 数据分析
python3 -m molib handoff route       # 自动路由到最佳Worker
python3 -m molib handoff list        # 查看所有可用Worker
python3 -m molib plan create         # 创建目标分解
python3 -m molib plan decompose      # 自动分解大任务
```

## 22家营收子公司一览

### 营销VP（5家）
| 子公司 | Worker | 核心能力 | 所属技能 |
|:-------|:-------|:---------|:---------|
| **墨笔文创** | content_writer.py | 文字创作·文案·公众号·小红书 | molin-xiaohongshu, copywriting, content-strategy |
| **墨韵IP** | ip_manager.py | IP衍生·商标·版权·品牌管理 | ai-taste-quality |
| **墨图设计** | designer.py | 封面·UI·视觉设计 | molin-design, excalidraw, pixel-art |
| **墨播短视频** | short_video.py | 短视频脚本+自动生成 | ffmpeg-video-engine, pixelle-video-engine |
| **墨声配音** | voice_actor.py | AI语音·播客·有声书 | molin-audio-engine, songwriting |

### 运营VP（4家）
| 子公司 | Worker | 核心能力 | 所属技能 |
|:-------|:-------|:---------|:---------|
| **墨域私域** | crm.py | CRM·用户分层·社群运营 | molin-crm, social-push-publisher |
| **墨声客服** | customer_service.py | 自动化客服·闲鱼消息→AI回复 | molin-customer-service, xianyu-automation |
| **墨链电商** | ecommerce.py | 订单管理·交易 | molin-order |
| **墨学教育** | education.py | 课程设计·AI辅导 | molin-education, ranedeer-ai-tutor |

### 技术VP（4家）
| 子公司 | Worker | 核心能力 | 所属技能 |
|:-------|:-------|:---------|:---------|
| **墨码开发** | developer.py | 软件开发·代码编写·爬虫 | agent-engineering, cli-anything |
| **墨维运维** | ops.py | 部署·DevOps·GUI自动化 | ghost-os, opensre-sre-agent |
| **墨安安全** | security.py | 安全审计·漏洞扫描 | red-teaming, ag-vulnerability-scanner |
| **墨梦AutoDream** | auto_dream.py | AI自动化实验·记忆蒸馏 | deep-dream-memory, self-learning-loop |

### 财务VP（1家）
| 子公司 | Worker | 核心能力 |
|:-------|:-------|:---------|
| **墨算财务** | finance.py | 记账·预算·成本控制 |

### 战略VP（3家）
| 子公司 | Worker | 核心能力 | 所属技能 |
|:-------|:-------|:---------|:---------|
| **墨商BD** | bd.py | 商务拓展·合作·投标 | molin-bd-scanner, agent-sales |
| **墨海出海** | global_marketing.py | 多语言·全球化·出海 | molin-global, weblate-localization |
| **墨研竞情** | research.py | 竞争分析·趋势·情报 | karpathy-autoresearch, world-monitor |

### 共同服务（3家）
| 子公司 | Worker | 核心能力 | 所属技能 |
|:-------|:-------|:---------|:---------|
| **墨律法务** | legal.py | 合同·隐私·合规·NDA | molin-legal |
| **墨脑知识** | knowledge.py | 知识管理·RAG·记忆 | molin-memory, supermemory |
| **墨测数据** | data_analyst.py | 数据·测试·BI | molin-data-analytics, molin-vizro |

### 专项预置（3家）
| Worker | 核心能力 |
|:-------|:---------|
| **trading.py** | 量化交易策略·信号·回测 |
| **scrapling_worker.py** | 网页抓取·数据采集 |
| **router9.py** | 网络流量·多路路由 |

## 核心系统模块

```
hermes-os/
├── config/                      # 系统配置
│   ├── governance.yaml          # 4级审批
│   ├── company.toml             # 子公司映射
│   ├── models.toml              # 模型路由
│   └── .env.example
├── molib/                       # 核心执行包
│   ├── cli.py                   # CLI入口
│   ├── __main__.py              # 统一入口
│   ├── ceo/                     # L0 CEO引擎 (10模块)
│   │   ├── ceo_reasoning.py     #   推理引擎
│   │   ├── ceo_orchestrator.py  #   编排器
│   │   ├── intent_router.py     #   意图路由
│   │   ├── risk_engine.py       #   风险评估
│   │   ├── dag_engine.py        #   DAG调度
│   │   ├── sop_store.py         #   SOP存储
│   │   └── main.py              #   FastAPI
│   ├── agencies/                # L1-L2 执行层
│   │   ├── handoff.py           #   Handoff路由
│   │   ├── handoff_register.py  #   16家Worker注册
│   │   ├── planning.py          #   规划分解
│   │   └── workers/             #   25个Worker
│   ├── shared/                  # L3 共享能力
│   │   ├── ai/                  #   LLM/视/Browser
│   │   ├── analysis/            #   分析/评价/预测
│   │   ├── content/             #   SEO/社交写作
│   │   ├── knowledge/           #   RAG/SOP/知识图谱
│   │   ├── publish/             #   平台发布/翻译
│   │   └── storage/             #   向量/缓存/文件
│   ├── xianyu/                  # 闲鱼集成
│   │   └── xianyu_helper.py     #   统一入口
│   ├── content/                 # 内容管线
│   ├── core/                    # 核心系统
│   ├── intelligence/            # 情报模块
│   ├── publish/                 # 发布模块
│   ├── business/                # 业务工具
│   └── management/              # VP管理层
├── bots/                        # 24个自动化脚本
│   ├── xianyu_bot.py            #   闲鱼WebSocket
│   ├── xhs_bot.py               #   小红书机器人
│   ├── daily_hot_report.py      #   每日热点
│   ├── flywheel_content.py      #   飞轮第二棒
│   ├── image_generator.py       #   三后端生图
│   ├── tts_generator.py         #   语音合成
│   ├── build_visual_identity.py #   品牌标识
│   └── ... (共24个)
├── business/                    # 9个商业化方案
│   ├── skill_store_installer.py #   技能商店安装器
│   ├── zsxq_manifesto.md        #   知识星球方案
│   ├── taiwan_market_entry.md   #   台湾市场方案
│   └── ... (共9个)
├── docs/                        # 27个系统文档
├── relay/                       # 飞轮接力数据
├── cron/jobs.yaml               # 8个定时作业
├── tests/                       # 6个测试模块
├── setup.py                     # pip安装
├── requirements.txt             # Python依赖
├── setup.sh                     # 一键部署
└── Makefile                     # 常用命令
```

## 已吸收开源项目

从27个高星开源项目中提取设计模式注入系统：

| 项目 | ⭐ | 注入的设计模式 |
|:----|:-:|:--------------|
| OpenAI Agents SDK | 110K | **Handoff模式** — Agent交接协议 |
| MetaGPT | 67K | 角色-行动-消息循环 |
| CowAgent | 44K | 记忆蒸馏+梦境系统 |
| nanobot | 41K | 轻量Agent循环 |
| MiroFish | 35K | 群体智能趋势预测 |
| CLI-Anything | 33K | CLI原生Agent |
| Ranedeer | 29.6K | AI导师Prompt DSL |
| UI-TARS | 29.6K | 多模态Agent栈 |
| InvokeAI | 27.1K | AI创意引擎 |
| A2A | 23.5K | Agent通信协议 |
| deepagents | 22.4K | **规划工具** — 任务分解+拓扑排序 |
| Stagehand | 22.4K | Browser Agent SDK |
| DeepTutor | 23.3K | 深度辅导引擎 |
| Parlant | 18.1K | 客服上下文工程 |
| CUA | 15.6K | Computer-Use Agent |
| CozeStudio | 20.7K | Agent工作室 |
| Skyvern | 21.5K | 浏览器自动化 |
| Weblate | 5.8K | 本地化平台模式 |
| BeeAI | 3.8K | Schema驱动工作流 |
| FastMCP | 25K | MCP Server SDK |
| Onlook | 25.6K | 设计↔代码双向同步 |
| ...另有7个项目 | — | — |

## 定时作业（8个 Hermes Cron）

默认**全部暂停**，零空转。激活后每日自动流水线：

| 时间 | 作业 | 功能 |
|:---:|:-----|:-----|
| 08:00 | 墨思情报扫描 | 博客/arXiv/MiroFish → 日报 |
| 09:00 | 墨迹内容工厂 | 情报→AI生成3篇内容 |
| 09:00 | CEO每日简报 | 汇总状态推送到你 |
| 10:00 | 墨增增长引擎 | SEO优化·增长分析 |
| 10:00 | 每日治理 | 审计+合规检查 |
| 12:00 | 系统快照 | 汇总产出+运营快照 |
| 15/45分 | 闲鱼消息检测 | 新消息AI自动回复 |
| 周五10:00 | 自学习进化 | GitHub扫描+技能更新 |

## 拓展路线图（56/56 全部闭合）

| 方向 | 完成度 | 关键交付 |
|:-----|:------:|:---------|
| CH1 记忆自进化 | ✅ 4/4 | claude-mem + session_search + SOUL反思协议 + 墨梦蒸馏 |
| CH2 沉睡激活 | ✅ 7/7 | ghost-os/karpathy/cli-anything/xhs/moneymaker/MCP/trading |
| CH3 变现矩阵 | ✅ 6/6 | 星球方案/定制/模板/代运营/技能商店安装器/付费课程 |
| CH4 内容生产 | ✅ 4/4 | 三棒飞轮/播客/MoneyPrinterTurbo/每日简报 |
| CH5 电商私域 | ✅ 5/5 | 闲鱼5升级/私域4模块/电商策略/twenty CRM/猪八戒/小红书 |
| CH6 GitHub吸收 | ✅ 6/6 | 吸收管线/10+项目/deepagents planning |
| CH7 多模态 | ✅ 7/7 | 生图/TTS/视频/品牌/语音/插件化 |
| CH8 出海 | ✅ 3/3 | 台湾策略/繁简转换/Dcard-Vocus方案 |
| CH9 SaaS化 | ✅ 4/4 | 技能商店/安装器CLI/SKILL质量评估/molib CLI参考 |
| CH10 子公司 | ✅ 3/3 | 墨播矩阵/墨数分析/墨投交易(已激活) |
| CH11 技能层 | ✅ 14/14 | 12新SKILL + 方案文档 |

## 许可

MIT License © 2026 Moye Tech
