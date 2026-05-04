---
name: claude-mem
description: 自动交互记忆捕捉系统 — 基于 thedotmack/claude-mem (71K⭐) 的自动记忆管线。每次任务后自动提取关键信息→写入Hermes记忆系统→构建知识图谱。墨脑（知识管理）核心技能。
version: 1.0.0
tags: [memory, auto-capture, knowledge-graph, self-learning, cross-session]
category: intelligence
metadata:
  hermes:
    source: https://github.com/thedotmack/claude-mem
    stars: 71000
    upstream_fork: https://github.com/moye-tech/claude-mem
    molin_owner: 墨脑（知识管理）
---

# Claude-Mem — 墨麟自动记忆捕捉系统

## 概述

**Claude-Mem** 原是一个 MCP 服务器/Claude Code 插件，自动捕捉所有交互信息构建持久化记忆。本技能将其核心机制适配为 **Hermes Agent 的自动记忆捕捉管线**。

**核心机制：** 每次任务完成后 → 自动提取关键信息 → 写入 Hermes 记忆系统 → 构建知识图谱。

## 自动捕捉管线

```
任务完成
    │
    ▼
┌─────────────────────────────┐
│ 1. 信息提取 (Extract)        │
│    从任务对话中提取:          │
│    · 事实 (Fact)             │
│    · 决策 (Decision)         │
│    · 关系 (Relationship)     │
│    · 偏好 (Preference)      │
│    · 模式 (Pattern)          │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│ 2. 分类分级 (Classify)      │
│    重要性评分 (0-1):         │
│    · ≥0.8: 自动写入记忆      │
│    · 0.5-0.8: 待确认后写入   │
│    · <0.5: 忽略              │
│    · 类别: 用户/项目/工具/流程│
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│ 3. 写入存储 (Store)         │
│    · memory(action='add')   │
│    · mempalace (语义检索)   │
│    · 知识图谱 (实体关系)     │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│ 4. 图谱关联 (Relate)        │
│    · 连接新旧记忆            │
│    · 建立实体关系            │
│    · 检测冲突/更新          │
└─────────────────────────────┘
```

## 触发机制

### 自动触发（推荐）
在 `self-learning-loop` 的回调中自动调用：
```
复杂任务完成（5+ 工具调用）
    → self-learning-loop 反思
    → claude-mem 提取信息
    → 写入记忆 → 更新知识图谱
```

### 手动触发
```python
# 在任务完成后手动调用
from hermes_tools import memory

# 1. 提取关键信息
extracted = {
    "facts": ["用户偏好简洁响应", "项目使用Python 3.11"],
    "decisions": ["决定用FastAPI而非Flask"],
    "patterns": ["跨会话记忆查询频率高"],
}

# 2. 按重要性写入
for fact in extracted["facts"]:
    memory(action="add", target="memory", content=fact)

for decision in extracted["decisions"]:
    memory(action="add", target="memory", content=f"[决策] {decision}")

for pattern in extracted["patterns"]:
    memory(action="add", target="memory", content=f"[模式] {pattern}")
```

## 信息提取模板

在复杂任务结束后，运行以下反思：

```
📋 本次任务信息提取
━━━━━━━━━━━━━━━━━━━━━━━
🟢 关键事实:
  · [用户/项目/工具的具体信息]
🟡 重要决策:
  · [架构/技术/流程的决策记录]
🔵 重复模式:
  · [观察到的问题/习惯/模式]
⚪ 用户偏好:
  · [响应风格/命名习惯/工作流]
━━━━━━━━━━━━━━━━━━━━━━━
重要性评分: [0.0-1.0]
```

## 重要性评分标准

| 分数 | 标准 | 操作 |
|:----:|------|:----:|
| 0.9-1.0 | 用户明确要求记住 / 纠正行为 | 立即写入记忆 |
| 0.7-0.9 | 重复出现的模式 / 环境事实 | 写入 + 图谱化 |
| 0.5-0.7 | 有用但非关键的上下文 | 可选写入 |
| 0.0-0.5 | 临时任务状态 | 忽略（用 session_search） |

## 知识图谱构建

每次写入新记忆时，自动建立关联：

```python
# 检查是否有关联的旧记忆
session_search(query="相关主题")

# 如果有冲突信息 → 更新
if conflict:
    memory(action="replace", old_text="旧信息", content="新信息")

# 如果有补充信息 → 关联存储
else:
    memory(action="add", target="memory", 
           content=f"[关联:旧主题→新事实] 关系描述")
```

## 集成到墨麟体系

```
claude-mem (自动捕捉)
    │
    ├──→ memory 工具（基础记忆存储）
    ├──→ mempalace（语义搜索 + 知识图谱）
    ├──→ self-learning-loop（自学习循环）
    └──→ session_search（跨会话知识检索）

墨脑知识管理流程:
任务 → claude-mem提取 → 分类分级 → 多端写入
     → 下次会话自动检索 → 避免重复沟通
```

## 触发条件

**必须触发（自动）：**
- 对话结束后（Hermes 自动回调）
- 复杂任务完成时（5+ 工具调用）
- 用户纠正/指导后
- 新发现工具/命令/环境信息

**跳过：**
- 简单问答（<3 工具调用）
- 测试性对话
- 用户明确要求不记录

## 绩效指标

- **目标:** 每天自动提取 ≥5 条有价值记忆
- **效果:** 跨会话重复率降低 80%+
- **长期:** 知识图谱节点数持续增长，新旧知识自动关联
