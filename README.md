<!-- 墨麟OS README v5.0 -->

# 🏛️ 墨麟OS (Molin OS)

<p align="center">
  <strong>AI 一人公司操作系统 · 28实体 · 336技能 · 5VP管理层 · 22家营收子公司</strong><br>
  从一句话指令到完整企业级AI操作系统，一个人就是一个集团
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12+-00b894?style=flat-square&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-00b894?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/skills-336-success?style=flat-square" alt="Skills">
  <img src="https://img.shields.io/badge/subsidiaries-22-success?style=flat-square" alt="Subsidiaries">
  <img src="https://img.shields.io/badge/status-v5.0-blueviolet?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/monthly_revenue-¥52K-ff6b6b?style=flat-square" alt="Revenue">
</p>

---

## 架构总览

```
                           董事会（你）
                                │
                      ┌─────────┴─────────┐
                      │  L0: 战略治理层     │
                      │  中枢 Nexus         │
                      │  CEO决策·治理·目标·  │
                      │  孵化·产品化路线      │
                      └─────────┬─────────┘
                                │ 决策流
    ┌───────────────────────────┼───────────────────────────┐
    │  L1: 营收业务线 (22家)      │                           │
    │  ¥52,000/月目标            │                           │
    │  ┌── 营销(5) ──────────┐ ┌── 运营(4) ────────────┐    │
    │  │ 墨笔·墨韵·墨图·      │ │ 墨域·墨声·墨链·         │    │
    │  │ 墨播·墨声配           │ │ 墨学                   │    │
    │  ├── 技术(4) ──────────┤ ├── 财务(1) ────────────┤    │
    │  │ 墨码·墨维·墨安·      │ │ 墨算                   │    │
    │  │ 墨梦                  │ │                        │    │
    │  ├── 战略(3) ──────────┤ ├── 共同(3) ────────────┤    │
    │  │ 墨商·墨海·墨研       │ │ 墨律·墨脑·墨测           │    │
    │  └────────────────────────┘                          │
    └───────────────────────────┬───────────────────────────┘
                                │ 服务
    ┌──────────────────────────────────────────────────────┐
    │  L2-L4: 基础设施                                        │
    │  MCP Server·Hermes Toolchain·Config系统                │
    └──────────────────────────────────────────────────────┘
```

## 核心指标

| 指标 | 数值 |
|:----|:----:|
| 总实体数 | **28个**（L0 + 22家L1 + 5家L2 = 中枢+5VP+20子公司+3共同） |
| 总收入目标 | **¥52,000/月** |
| 总预算 | **¥3,490/月** |
| ROI | **14.9x** |
| 技能总数 | **336个** SKILL.md（含28个吸收项目设计模式） |
| 已吸收项目 | **27个开源高星项目**（~520K⭐） |
| 闲鱼集成 | 统一入口 `xianyu_helper.py`（防踩坑已验证） |
| 零空转 | ✅ 所有cron默认暂停，有任务才消耗token |
| 拓展任务 | **42项行动×9个方向，56/56 全部闭合** |

## 快速部署

```bash
git clone https://github.com/moye-tech/-Hermes-OS.git
cd -Hermes-OS
bash setup.sh     # 一键安装依赖 + 初始配置
```

## 统一入口

```bash
python3 -m molib health              # 系统健康检查
python3 -m molib content write       # 内容创作
python3 -m molib design image        # 图片生成
python3 -m molib video script        # 视频脚本
python3 -m molib crm segment         # 私域运营
python3 -m molib xianyu reply        # 闲鱼客服
python3 -m molib trading signal      # 交易信号
python3 -m molib handoff route       # 任务自动路由
python3 -m molib plan create         # 目标分解
```

## 22家子公司一览 (v5.0)

### 营销VP
| 子公司 | 核心能力 | Worker |
|:-------|:---------|:-------|
| **墨笔文创** | 文字内容创作、小红书/公众号运营 | content_writer.py |
| **墨韵IP** | IP衍生、商标、品牌管理 | ip_manager.py |
| **墨图设计** | 封面/UI/品牌视觉 | designer.py |
| **墨播短视频** | 短脚本+自动生成 | short_video.py |
| **墨声配音** | AI语音合成、播客 | voice_actor.py |

### 运营VP
| 子公司 | 核心能力 | Worker |
|:-------|:---------|:-------|
| **墨域私域** | CRM、用户分层、社群运营 | crm.py |
| **墨声客服** | 闲鱼自动回复、客服自动化 | customer_service.py |
| **墨链电商** | 订单管理、交易 | ecommerce.py |
| **墨学教育** | 课程设计、辅导 | education.py |

### 技术VP
| 子公司 | 核心能力 | Worker |
|:-------|:---------|:-------|
| **墨码开发** | 软件编写、爬虫 | developer.py |
| **墨维运维** | 服务器部署、DevOps | ops.py |
| **墨安安全** | 安全审计、漏洞扫描 | security.py |
| **墨梦AutoDream** | AI自动化实验、原型 | auto_dream.py |

### 财务VP
| 子公司 | 核心能力 | Worker |
|:-------|:---------|:-------|
| **墨算财务** | 记账、预算、成本控制 | finance.py |

### 战略VP
| 子公司 | 核心能力 | Worker |
|:-------|:---------|:-------|
| **墨商BD** | 商务拓展、投标 | bd.py |
| **墨海出海** | 多语言本地化、海外运营 | global_marketing.py |
| **墨研竞情** | 竞争分析、趋势研究 | research.py |

### 共同服务
| 子公司 | 核心能力 | Worker |
|:-------|:---------|:-------|
| **墨律法务** | 合同审查、合规、NDA | legal.py |
| **墨脑知识** | 知识管理、RAG记忆 | knowledge.py |
| **墨测数据** | 数据分析、测试 | data_analyst.py |

## 已吸收项目

| 项目 | ⭐ | 设计模式 |
|:----|:-:|:---------|
| MetaGPT | 67K | 角色-行动-消息循环 |
| CowAgent | 44K | 记忆蒸馏+梦境 |
| nanobot | 41K | 轻量Agent |
| MiroFish | 35K | 群体智能预测 |
| Ranedeer | 29.6K | AI导师DSL |
| UI-TARS | 29.6K | 多模态Agent |
| InvokeAI | 27.1K | AI创意引擎 |
| A2A | 23.5K | Agent通信协议 |
| Stagehand | 22.4K | Browser SDK |
| DeepTutor | 23.3K | 深度辅导 |
| OpenAI Handoff | 110K | Agent交接协议 |
| deepagents | 22.4K | 规划工具 |
| Parlant | 18.1K | 客服上下文工程 |
| ...另有15+项目 | — | — |

## 拓展路线图状态

42项行动×9个方向全部落实 (56/56 100%)：

| 方向 | 完成度 |
|:-----|:------:|
| CH1 记忆自进化 | ✅ 4/4 (100%) |
| CH2 沉睡激活 | ✅ 7/7 (100%) |
| CH3 变现矩阵 | ✅ 6/6 (100%) |
| CH4 内容生产 | ✅ 4/4 (100%) |
| CH5 电商私域 | ✅ 5/5 (100%) |
| CH6 GitHub吸收 | ✅ 6/6 (100%) |
| CH7 多模态能力 | ✅ 7/7 (100%) |
| CH8 出海本地化 | ✅ 3/3 (100%) |
| CH9 SaaS化 | ✅ 4/4 (100%) |
| CH10 子公司 | ✅ 3/3 (100%) |
| CH11 技能层 | ✅ 14/14 (100%) |

## 许可

MIT License © 2026 Moye Tech
