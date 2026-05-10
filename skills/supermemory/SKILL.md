---
name: supermemory
description: 超级记忆引擎 — 基于 supermemoryai/supermemory (22K⭐) 的超快速语义记忆检索API。作为 Hermes
  mempalace 的补充后端，提供快速检索+跨会话记忆关联能力。
version: 1.0.0
tags:
- memory
- semantic-search
- api
- cross-session
- retrieval
category: intelligence
metadata:
  hermes:
    source: https://github.com/supermemoryai/supermemory
    stars: 22000
    upstream_fork: https://github.com/moye-tech/supermemory
    complements: mempalace
    molin_owner: 墨脑（知识管理）
min_hermes_version: 0.13.0
---

# Supermemory — 超级记忆引擎

## 概述

**Supermemory** 是 LongMemEval #1 的记忆引擎，提供超快速检索和跨会话记忆关联。作为 Hermes `mempalace` 的补充后端，两者组合使用形成完整的记忆体系。

## 架构对比

| 能力 | mempalace（已有） | supermemory（新增） |
|:----|:-----------------|:-------------------|
| 存储方式 | ChromaDB 向量数据库 | ChromaDB + PostgreSQL |
| 检索方式 | 语义搜索 + BM25 | 混合搜索 + 多路召回 |
| API | CLI 工具 | REST API / SDK |
| 速度 | 中等 | 超快（优化索引） |
| 关联能力 | 知识图谱 | 跨会话联想 |
| 部署 | 本地 | 本地/云端 |

## 核心特性

### 1. 超快速检索
- 优化的向量索引结构，查询时间 <50ms
- 多路召回：向量相似度 + BM25 + 时间衰减
- 支持流式搜索（实时返回结果）

### 2. 跨会话记忆关联
```
会话A: 讨论了项目X的架构设计
    ↓ supermemory自动关联
会话B: 看到技术术语Y → 自动关联到会话A的讨论
    ↓
输出: "这个Y问题上次在项目X的架构讨论中提过..."
```

### 3. 记忆 API
```python
# 搜索记忆
GET /api/memories/search?q=项目架构决策

# 添加记忆
POST /api/memories
{
    "content": "决定用FastAPI替代Flask",
    "tags": ["决策", "项目X"],
    "source": "session-20260504"
}

# 关联查询
GET /api/memories/related?id=xxx
```

## 本地部署

```bash
# supermemory 项目在 ~/supermemory/
cd ~/supermemory

# 依赖（需要 Bun + PostgreSQL）
bun install

# 配置环境变量
cp .env.example .env
# 编辑 .env 设置数据库连接

# 启动
bun run dev
```

## Hermes 集成方式

```python
# 方式1: 通过 supermemory API 增强记忆检索
# 在需要跨会话联想时调用
import requests

def search_with_supermemory(query):
    """使用 supermemory 进行语义搜索"""
    try:
        resp = requests.post(
            "http://localhost:3000/api/memories/search",
            json={"q": query, "limit": 5}
        )
        return resp.json()
    except:
        # fallback 到 hermes session_search
        return session_search(query=query)

# 方式2: 替代写入
def save_to_supermemory(content, tags):
    """同时写入 hermes memory + supermemory"""
    # 写入 hermes
    memory(action="add", target="memory", content=content)
    
    # 写入 supermemory
    try:
        requests.post(
            "http://localhost:3000/api/memories",
            json={"content": content, "tags": tags}
        )
    except:
        pass  # supermemory 挂掉不影响基础功能
```

## 使用场景

| 场景 | 用 mempalace | 用 supermemory |
|:----|:------------|:--------------|
| 日常记忆读写 | ✅ 默认 | ❌ 备选 |
| 跨会话深度关联 | ⚡ 一般 | ✅ 更强 |
| 超快搜索（<50ms） | ❌ | ✅ |
| 知识图谱 | ✅ | ❌ |
| API 化可编程访问 | ❌ | ✅ |