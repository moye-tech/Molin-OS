---
name: opencli-hub
description: 通用CLI中心 — 将任何网站和工具转换为CLI命令。一个通用的CLI Hub和AI原生运行时，让Hermes能统一调用各平台工具。墨智（AI研发）+
  墨维（运维）的CLI基础设施。
version: 1.0.0
tags:
- cli
- hub
- integration
- automation
- tools
- universal
category: devops
metadata:
  hermes:
    source: https://github.com/OpenCLI/OpenCLI
    stars: 5000+
    upstream_fork: https://github.com/moye-tech/OpenCLI
    language: TypeScript
    molin_owner: 墨智（AI研发）
min_hermes_version: 0.13.0
---

# OpenCLI Hub — 通用CLI中心

## 概述

**OpenCLI** 是一个通用的 CLI Hub 和 AI 原生运行时——**让任何网站和工具变成CLI命令**。对于以 CLI 为中心的 Hermes Agent，OpenCLI 提供了统一的外部工具调用入口。

## 核心概念

```
原来: 每个平台有自己的API/SDK/Web界面
    闲鱼 → open api / 网页
    小红书 → 逆向API / 网页
    GitHub → gh CLI
    飞书 → SDK
    
OpenCLI: 所有平台 → 统一的 CLI 命令
    OpenCLI hub connect xianyu
    OpenCLI hub connect xiaohongshu
    OpenCLI hub list
    OpenCLI hub run xianyu.search --query "AI课程"
```

## 核心能力

### 1. 平台适配器
```bash
# 连接平台
opencli hub connect github
opencli hub connect xiaohongshu
opencli hub connect feishu

# 列出已连接的平台
opencli hub list

# 运行平台命令
opencli run xiaohongshu.search --keyword "AI工具" --limit 10
opencli run xianyu.list --category "编程"
```

### 2. AI 原生运行时
- 专为 AI Agent 设计的 CLI 输出格式（JSON/结构化）
- 错误处理友好，Agent 无需解析人类友好文本
- 支持流式输出（SSE）

### 3. 工具市场
- 插件化的工具注册系统
- 社区贡献的工具可直接安装
- 每个工具自带 schema 描述

## Hermes 集成方式

```bash
# 安装 OpenCLI
npm install -g opencli

# 连接平台
opencli hub connect feishu --token xxx
opencli hub connect xianyu --cookie xxx

# 通过 terminal 调用
opencli run xiaohongshu.search --keyword "AI" --limit 5
```

### 在 skill 中使用

```python
# 通过 Hermes terminal 调用 OpenCLI
from hermes_tools import terminal

# 搜索小红书
result = terminal("opencli run xiaohongshu.search --keyword 'AI编程' --limit 10")
data = json.loads(result["output"])

# 发布内容
terminal("opencli run xiaohongshu.publish --title 'xxx' --content 'xxx'")
```

## 与 Hermes 现有能力的互补

| 已有能力 | OpenCLI 补充 |
|:---------|:------------|
| `social-push-publisher`（发布管线） | 统一CLI入口，简化调用 |
| `xianyu-automation`（闲鱼自动化） | 可通过 OpenCLI 统一管理 |
| 各平台独立 skill | 一个 CLI 覆盖所有平台 |
| 手动调用 terminal | 标准化命令格式 |

## 使用场景

| 场景 | 命令 |
|:----|:-----|
| 搜索小红书 | `opencli run xiaohongshu.search --keyword X` |
| 发布闲鱼 | `opencli run xianyu.publish --title X --price X` |
| 查询 GitHub | `opencli run github.search --q X` |
| 发送飞书 | `opencli run feishu.send --msg X` |
| 浏览网页 | `opencli run web.get --url X` |