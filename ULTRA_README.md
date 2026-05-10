<!--
  Molin-OS-Ultra — README
  Version: 7.0
  Last updated: 2026-05-08
  Fusion of: Molin-OS v5.0 + molin-ai-intelligent-system v6.7
-->

# Molin-OS-Ultra v7.0 — AI 一人公司终极操作系统

<p align="center">
  <strong>6 层架构 · 22 Worker · 20 子公司 · 492 技能 · 26 Bot · 20 SOP</strong><br>
  CEO→Manager→Worker 三层决策 · 5 层记忆 · 自愈引擎 · 推理链可视化<br>
  一个人就是一个集团
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-00b894?style=flat-square&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-00b894?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/version-v7.0_Ultra-blueviolet?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/skills-492-success?style=flat-square" alt="Skills">
  <img src="https://img.shields.io/badge/workers-22-success?style=flat-square" alt="Workers">
  <img src="https://img.shields.io/badge/bots-26-success?style=flat-square" alt="Bots">
  <img src="https://img.shields.io/badge/SOP-20-success?style=flat-square" alt="SOP">
  <img src="https://img.shields.io/badge/revenue-%C2%A552K%2Fmonth-ff6b6b?style=flat-square" alt="Revenue">
</p>

---

## 融合来源

本系统由两个独立系统深度解构后融合而成：

| 来源系统 | 版本 | 贡献 |
|---------|------|------|
| **Molin-OS** | v5.0 | CLI入口、SOUL认知框架、492技能、26 Bot、飞轮管线、商业方案、治理规则 |
| **molin-ai-intelligent-system** | v6.7 | FastAPI服务、CEO→Manager→Worker三层架构、飞书深度集成、SOP引擎、记忆系统、自愈引擎 |

## 架构总览

```
创始人（你）
    │
    ├── CLI 入口 (python -m molib)          ← Molin-OS
    ├── HTTP API (FastAPI :8000)            ← AI-System
    └── 飞书 WebSocket                      ← AI-System
         │
┌── L0 中枢 ──────────────────────────────────────────┐
│  SOUL.md 认知框架 · IntentProcessor 意图预处理       │
│  CEO 决策引擎 · BudgetGuard 预算守卫                 │
│  governance.yaml 4级治理                             │
└──────────────────┬──────────────────────────────────┘
                   │
┌── L1 管理层 ────┼──────────────────────────────────┐
│  ManagerDispatcher · ConfigDrivenManager            │
│  QualityGate · Handoff自动路由(兜底)                 │
└──────────────────┬──────────────────────────────────┘
                   │
┌── L2 执行层 ────┼──────────────────────────────────┐
│  22 Worker (think→act→reflect)                      │
│  BaseAgency 人格化 · 492 SKILL.md 注入               │
└──────────────────┬──────────────────────────────────┘
                   │
┌── L3 自动化 ────┼──────────────────────────────────┐
│  26 Bot · 飞轮三棒 · 8 Cron · APScheduler · SOP     │
└──────────────────┬──────────────────────────────────┘
                   │
┌── L4 基础设施 ──┼──────────────────────────────────┐
│  5层记忆 · ModelRouter · EventBus · 自愈引擎         │
│  Prometheus · 知识图谱 · DataBrain · 飞书14模块       │
└──────────────────────────────────────────────────────┘
```

## 快速部署

```bash
# 1. 克隆 & 安装
git clone https://github.com/moye-tech/molin-os-ultra.git
cd molin-os-ultra
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. 配置
cp .env.example .env   # 编辑填入 API Keys

# 3A. CLI 模式（本地操作）
python -m molib health
python -m molib help

# 3B. Server 模式（远程服务）
uvicorn core.ceo.main:app --host 0.0.0.0 --port 8000

# 3C. 飞书 Bot
python integrations/feishu/bot_main.py
```

## 20 个子公司

### 营销 VP（5家）
| 子系统 | Worker | 核心能力 |
|--------|--------|---------|
| 墨笔文创 | content_writer | 文字创作·文案·小红书 |
| 墨韵IP | ip_manager | IP衍生·品牌·版权 |
| 墨图设计 | designer | 封面·UI·视觉 |
| 墨播短视频 | short_video | 短视频脚本+生成 |
| 墨声配音 | voice_actor | AI语音·播客 |

### 运营 VP（4家）
| 子系统 | Worker | 核心能力 |
|--------|--------|---------|
| 墨域私域 | crm | CRM·用户分层 |
| 墨声客服 | customer_service | 自动客服·闲鱼 |
| 墨链电商 | ecommerce | 订单·交易 |
| 墨学教育 | education | 课程·辅导 |

### 技术 VP（4家）
| 子系统 | Worker | 核心能力 |
|--------|--------|---------|
| 墨码开发 | developer | 软件开发·编程 |
| 墨维运维 | ops | DevOps·部署 |
| 墨安安全 | security | 审计·漏洞 |
| 墨梦AI | auto_dream | AI实验·记忆蒸馏 |

### 财务 VP（1家）+ 战略 VP（3家）+ 共同服务（3家）
| 子系统 | Worker | 核心能力 |
|--------|--------|---------|
| 墨算财务 | finance | 记账·预算 |
| 墨商BD | bd | 商务·合作 |
| 墨海出海 | global_marketing | 全球化·本地化 |
| 墨研竞情 | research | 竞争·情报 |
| 墨律法务 | legal | 合同·合规 |
| 墨脑知识 | knowledge | RAG·记忆 |
| 墨测数据 | data_analyst | BI·分析 |

## CLI 命令

```bash
python -m molib health              # 系统健康检查
python -m molib content write       # 内容创作
python -m molib design image        # 图片设计
python -m molib crm segment         # 用户分层
python -m molib finance report      # 财务报表
python -m molib trading signal      # 交易信号
python -m molib handoff route       # 自动路由
python -m molib plan decompose      # 任务分解
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/api/chat` | 多轮推理对话 |
| POST | `/api/decide` | 单次CEO决策 |
| GET | `/api/daily-loop` | 每日优化循环 |
| GET | `/api/pending-approvals` | 待审批列表 |

## 许可证

MIT License © 2026 Moye Tech
