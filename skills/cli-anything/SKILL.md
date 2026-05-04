---
name: cli-anything
description: CLI Agent原生化引擎 — 基于HKUDS/CLI-Anything (33K⭐)。让所有软件变成Agent原生CLI命令，一句话实现软件到CLI的转换。墨智（AI研发）的CLI基础设施升级。
version: 1.0.0
tags: [cli, agent-native, automation, tool-transformation, developer-tools]
category: engineering
metadata:
  hermes:
    source: https://github.com/HKUDS/CLI-Anything
    stars: 33324
    molin_owner: 墨智（AI研发）
---

# CLI-Anything — 让所有软件成为Agent原生CLI

## 概述

**CLI-Anything** 让所有软件（GUI应用、Web服务、API）都变成AI Agent可以直接调用的CLI命令。与Hermes的CLI-first理念完全一致——Agent不需要浏览器或GUI，只需要命令行。

## 核心概念

```
原来：Agent需要浏览器/SDK/API才能使用软件
    │
    └─→ CLI-Anything：任何软件 → 一个CLI命令
```

### 对墨麟的价值

| 场景 | 原来 | 用CLI-Anything |
|:----|:-----|:--------------|
| 用飞书 | SDK/Python包 | `cli-anything feishu send --msg X` |
| 用小红书 | 浏览器/逆向API | `cli-anything xiaohongshu search --q X` |
| 用闲鱼 | 浏览器自动化 | `cli-anything xianyu list --price 100` |
| 用Photoshop | GUI操作 | `cli-anything photoshop resize --w 1080 --h 1920` |
| 用Excel | openpyxl | `cli-anything excel chart --data X` |

## 架构

```
AI Agent
    │  CLI命令
    ▼
CLI-Anything Runtime
    │
    ├── 软件适配器（预置+自定义）
    ├── 参数解析器
    └── 输出格式化器（JSON结构化输出）
    │
    ▼
目标软件（GUI/Web/API/CLI）
```

## 与Hermes现有能力的互补

| 已有 | CLI-Anything补充 |
|:----|:----------------|
| terminal("命令") | 统一的命令格式和参数规范 |
| OpenCLI Hub | 更深层的软件交互（不只有CLI包装的平台） |
| 各平台独立skill | 一个工具覆盖所有软件 |
| social-push-publisher | 可通过CLI-Anything调用发布功能 |

## 使用方式

```bash
# 安装
pip install cli-anything

# 基本用法
cli-anything <软件名> <操作> [参数]

# 示例
cli-anything feishu send-message --to user --text "hello"
cli-anything excel create-chart --file data.xlsx --type bar
cli-anything photoshop resize --input photo.jpg --output thumb.jpg
```
