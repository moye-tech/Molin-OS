---
name: molin-memory
description: "墨麟记忆引擎 — 子公司级向量RAG (ChromaDB) + 结构化存储 (SQLite) + 事件总线。22家子公司各自独立向量collection，支持语义检索、跨子公司事件通知、自动记忆上下文注入。Use when: 需要子公司回忆历史经验、跨子公司传递事件、为 Agent 注入带记忆的上下文。"
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [memory, rag, vector, chromadb, sqlite, event-bus, molin]
    related_skills: [self-learning-loop, molin-governance, molin-company-structure, molin-legal]
    molin_owner: 墨脑（知识管理）
---

# 墨麟记忆引擎 · molin-memory

## 概述

墨麟记忆引擎是 22 家子公司的「集体记忆系统」。它解决评估报告中指出的三个核心问题：

1. **无持久记忆** → ChromaDB 向量库，语义检索历史经验
2. **跨子公司零通信** → SQLite 事件总线，pub/sub 模式
3. **自学习无法积累** → 每次任务输出自动归档，下次可检索

### 架构

```
┌──────────────┐     ┌───────────────────────┐     ┌─────────────┐
│  Hermes Agent │────▶│   molin-memory CLI    │────▶│  ChromaDB   │
│  (每次执行前)  │     │   (scripts/molin_    │     │  22 个       │
│              │     │    memory.py)          │     │  collection  │
│              │     │                       │     │  (每子公司)   │
│              │     ├───────────────────────┤     ├─────────────┤
│              │     │   SQLite (state.db)   │────▶│  decisions  │
│              │     │                       │     │  events     │
│              │     │                       │     │  tasks      │
│              │     │                       │     │  metrics    │
└──────────────┘     └───────────────────────┘     └─────────────┘
```

---

## 何时使用

- 用户说"之前我们处理过类似的问题"、"看看过去有什么经验"
- 执行 molin-xxx skill 前 → 自动检索相关记忆注入上下文
- 需要跨子公司传递消息（墨思发现趋势→通知墨迹）
- 需要在 SQLite 中跟踪决策、任务、KPI

---

## 安装

系统依赖已满足（chromadb, sqlite3 均已内置）：

```bash
# 初始化
python3 ~/.hermes/skills/molin-memory/scripts/molin_memory.py init
```

### 数据位置

```
~/.molin-memory/
├── vectors/          # ChromaDB 持久化（22子公司各1 collection）
├── state.db          # SQLite 结构化存储
└── skill_sources.json  # 可选的技能映射
```

---

## 快速参考

### 基础操作

```bash
# 1. 初始化（第一次使用）
python3 ~/.hermes/skills/molin-memory/scripts/molin_memory.py init

# 2. 存入一条记忆
python3 ~/.hermes/skills/molin-memory/scripts/molin_memory.py store 墨律 \
  "审查了一份SaaS合同，发现无限责任条款(第8.3条)需要修改" \
  '{"type":"contract_review","source":"molin-legal","tags":["SaaS","liability"]}'

# 3. 检索记忆
python3 ~/.hermes/skills/molin-memory/scripts/molin_memory.py recall 墨律 \
  "SaaS合同责任条款风险" 5

# 4. 批量导入现有 skills
python3 ~/.hermes/skills/molin-memory/scripts/molin_memory.py import-skills \
  ~/.hermes/skills

# 5. 查看统计
python3 ~/.hermes/skills/molin-memory/scripts/molin_memory.py stats
```

### 事件总线（发布/订阅）

```bash
# 墨思发现趋势 → 通知墨迹（非阻塞）
python3 ~/.hermes/skills/molin-memory/scripts/molin_memory.py event 墨思 \
  "trend_detected" \
  '{"topic":"AI Agent 低代码","source":"GitHub Trending","urgency":"high"}'

# 墨增检查未处理事件
python3 ~/.hermes/skills/molin-memory/scripts/molin_memory.py events

# 墨迹消费事件后，用 memory 标记已处理
```

---

## 自学习闭环（P3.2 升级）

基于评估报告的四阶段路线图，完整的 evaluate→absorb→integrate→retire：

```bash
# 执行完整四阶段
python3 ~/.hermes/skills/molin-memory/scripts/molin_learn.py full

# 仅执行单个阶段
python3 ~/.hermes/skills/molin-memory/scripts/molin_learn.py evaluate
python3 ~/.hermes/skills/molin-memory/scripts/molin_learn.py absorb
python3 ~/.hermes/skills/molin-memory/scripts/molin_learn.py integrate
python3 ~/.hermes/skills/molin-memory/scripts/molin_learn.py retire
python3 ~/.hermes/skills/molin-memory/scripts/molin_learn.py report
```

### 四阶段详解

| 阶段 | 功能 | 数据源 |
|:----:|:-----|:-------|
| **Evaluate** | 扫描外部数据源，收集发现 | GitHub Trending、事件总线、系统统计 |
| **Absorb** | 自动分析相关度(1-5)，提炼洞察 | 上阶段发现 |
| **Integrate** | 生成技能更新/创建建议 | 高价值洞察 |
| **Retire** | 每月清理90天过期知识 | 向量库访问频率 |

每周五 10:00 自动执行完整闭环。输出报告存入记忆系统。

### 上下文注入

```bash
# 在运行子公司前，自动获取带记忆的上下文
python3 ~/.hermes/skills/molin-memory/scripts/molin_memory.py context 墨律 \
  "审查一份新的SaaS合同"
```

返回格式：
```markdown
## 📚 相关历史经验（记忆检索）

### 1. [85%匹配] 审查了一份SaaS合同，发现无限责任条款(第8.3条)需要修改...
   标签: ["SaaS","liability"]
```

---

## 数据模型

### SQLite 表

**decisions** — 所有决策历史

| 字段 | 类型 | 说明 |
|:-----|:----|:-----|
| id | INTEGER | PK |
| timestamp | TEXT | ISO 时间 |
| subsidiary | TEXT | 子公司名 |
| action | TEXT | 操作名 |
| summary | TEXT | 摘要（<=200字） |
| cost | REAL | 成本（¥） |
| level | TEXT | L0-L3 |
| outcome | TEXT | completed/failed/blocked |

**events** — 事件总线

| 字段 | 类型 | 说明 |
|:-----|:----|:-----|
| id | INTEGER | PK |
| source | TEXT | 来源子公司 |
| target | TEXT | 目标子公司（null=广播） |
| event_type | TEXT | 事件类型 |
| payload | TEXT | JSON 负载 |
| processed | INTEGER | 0=未处理, 1=已消费 |

**tasks** — 任务跟踪

| 字段 | 类型 | 说明 |
|:-----|:----|:-----|
| id | INTEGER | PK |
| task_id | TEXT | 唯一任务ID |
| subsidiary | TEXT | 负责子公司 |
| status | TEXT | pending/in_progress/completed |

**metrics** — KPI 指标

| 字段 | 类型 | 说明 |
|:-----|:----|:-----|
| date | TEXT | 日期 |
| subsidiary | TEXT | 子公司 |
| metric_name | TEXT | 指标名 |
| metric_value | REAL | 值 |

---

## 评估报告关键缺陷覆盖

| # | 原缺陷 | 本系统解决方式 |
|:-:|:-------|:--------------|
| 1 | 无持久记忆 | ChromaDB 向量库 + SQLite 双写，跨会话持久化 |
| 2 | 子公司零通信 | SQLite events 表实现发布/订阅 |
| 3 | 自学习空壳 | `import-skills` + `store` 让学习循环有实质内容可检索 |
| 6 | 治理未强制执行 | `decisions` 表记录每笔操作的成本+级别+结果 |

---

## 常见陷阱

1. **不要存原始大文本** — 向量库每条限制 2000 字符。存摘要，详细结果存文件引用
2. **检索不到≠没发生过** — 语义搜索依赖 embedding 质量，太短的查询可能不匹配
3. **事件需要手动消费** — 事件总线是"发布"模式，消费端需要主动 `events` + `mark_event_processed`
4. **初始化只需一次** — `init` 是幂等的，重复调用不会丢失数据
5. **ChromaDB 不支持中文 collection 名** — collection name 必须匹配 `[a-zA-Z0-9._-]{3-512}`。中文字符报 `Validation error`。解决方案：用拼音/英文名（如 `molin_molv`、`molin_mozhi`），在 metadata 中存储中文名。Python 映射：`{cn: en for cn, en in SUBSIDIARY_PAIRS}`
6. **`count()` 返回的是 collection 数不是文档数** — `collection.count()` 在 ChromaDB v1.5 返回的是 1（只有一个 collection），不是文档数量。要查看实际文档数使用 `len(collection.get()['ids'])`
7. **upsert 相同 ID 会覆盖不报错** — 对同一 doc_id 多次 upsert 不会报错但后一次覆盖前一次。确保 ID 全局唯一：用 `skill_{skill_path}` 或 `{sub}_{content_hash}` 生成
8. **`patch` 工具遇到引号逃逸问题** — 当 old_string/new_string 中包含双引号时，`patch` 工具会报 `Escape-drift detected`。解决方案：不要在 old_string/new_string 中使用 `\"`，改用 Python 脚本直接替换文件内容
9. **`import-skills` 的 molin_owner 解析** — molin_owner 藏在 frontmatter 的 `metadata.hermes.molin_owner` 深层嵌套，不是在顶层。解析方法：做字符串匹配 `molin_owner` 在任何行出现，然后提取冒号后的值，再用中文前缀匹配（`"墨律（法务）"` 匹配 `"墨律"`）

---

## 验证清单

- [ ] `init` 成功 → 输出 22 家子公司 collections
- [ ] `store` + `recall` 闭环 → 存一条再搜到
- [ ] `import-skills` 完成 → `stats` 显示各子公司 > 0 条
- [ ] `context` 返回非空内容
- [ ] `event` + `events` 事件总线工作
