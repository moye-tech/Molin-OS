---
name: gitnexus
description: 代码知识图谱引擎 — 基于 abhigyanpatwari/GitNexus (35K⭐) 的零服务端代码智能引擎。将任意代码仓库转化为知识图谱，支持深度代码分析和智能查询。墨维（运维）核心技能。
version: 1.0.0
tags: [knowledge-graph, code-analysis, git, neo4j, dependency-graph]
category: github
metadata:
  hermes:
    source: https://github.com/abhigyanpatwari/GitNexus
    stars: 35000
    upstream_fork: https://github.com/moye-tech/GitNexus
    molin_owner: 墨维（运维）
---

# GitNexus — 代码知识图谱引擎

## 概述

**GitNexus** 将任意代码仓库转化为结构化的知识图谱，支持深度代码分析和智能查询。墨维（运维）+ 墨码（研发）的代码智能基础设施。

## 核心能力

### 1. 代码知识图谱构建

```
代码仓库
    │
    ▼
┌─────────────────────────────────────┐
│ 6层节点模型                          │
│ Repository → Module → File → Class  │
│ → Method → Variable                  │
├─────────────────────────────────────┤
│ 12+ 种关系类型                       │
│ 继承/调用/数据流/依赖/定义-使用/导入  │
├─────────────────────────────────────┤
│ 双解析引擎                           │
│ AST (抽象语法树) + PDG (程序依赖图)   │
├─────────────────────────────────────┤
│ 存储: Neo4j / Memgraph               │
│ 查询: Cypher / GraphQL               │
└─────────────────────────────────────┘
```

### 2. 分析引擎

| 模块 | 功能 |
|:----|:----|
| 变更影响分析 | 精确到函数级的变更传播追踪 |
| 代码相似度 | 检测重复代码/模式克隆 |
| 设计模式检测 | 自动识别 Builder/Facade/Observer 等 |
| 代码度量 | 圈复杂度、耦合度、内聚性 |
| LLM 桥接 | 自然语言 → Cypher 查询转换 |

### 3. 查询能力

```cypher
// 查询: "函数 A 被哪些函数调用？"
MATCH (caller:Function)-[:CALLS]->(target:Function {name: 'A'})
RETURN caller.name, caller.file

// 查询: "修改文件 B 会影响哪些测试？"
MATCH (f:File {path: 'B'})<-[:DEPENDS_ON]-(test:File)
WHERE test.name CONTAINS 'test'
RETURN test.path

// 查询: "模块 C 的最大依赖链"
MATCH path = (mod:Module {name: 'C'})-[:DEPENDS_ON*]->(leaf)
WHERE NOT (leaf)-[:DEPENDS_ON]->()
RETURN path
ORDER BY length(path) DESC LIMIT 1
```

## 本地部署

```bash
cd ~/GitNexus

# 安装依赖
pip install -r requirements.txt

# 启动 Neo4j（需先安装 Docker）
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 neo4j:latest

# 配置
cp .env.example .env
# 编辑 .env 设置 Neo4j 连接

# 分析代码仓库
python src/gitnexus/main.py analyze /path/to/repo

# 启动 API 服务
python src/gitnexus/main.py serve
```

## Hermes 集成方式

```python
# 使用场景1: PR 变更影响分析
# 在代码审查时，自动分析变更的影响范围
"""
当 PR 修改了某个函数：
1. 调用 GitNexus 分析该函数
2. 获取所有受影响的下游代码
3. 特别关注被影响的测试文件
"""

# 使用场景2: 新手指南
"""
当需要理解一个不熟悉的仓库：
1. GitNexus 构建知识图谱
2. 查询模块间的依赖关系
3. 可视化架构（树形/图形）
"""
```

## 与 Hermes 已有能力的互补

| 已有能力 | GitNexus 补充 |
|:---------|:--------------|
| `codebase-inspection`（文件级统计） | 函数级依赖分析 |
| `github-code-review`（PR 审查） | 变更影响链条追踪 |
| `zoom-out`（代码理解） | 结构化的知识图谱 |
| `improve-codebase-architecture` | 耦合度和设计模式检测 |
