---
name: ghost-os
description: 本机 GUI 自动化参考 — 基于 ghostwright/ghost-os (1.4K⭐)。AI Agent 全计算机控制，自学习工作流，原生 macOS 操作。墨维（运维）的本机自动化参考方案。
version: 1.0.0
tags: [gui-automation, macos, mcp, self-learning, workflow]
category: devops
metadata:
  hermes:
    source: https://github.com/ghostwright/ghost-os
    stars: 1400
    upstream_fork: https://github.com/moye-tech/ghost-os
    platform: macOS 14+
    language: Swift
    mcp_compatible: true
    molin_owner: 墨维（运维）
---

# Ghost OS — 本机 GUI 自动化参考

## 概述

**Ghost OS** 让 AI Agent 能够看到和操作 Mac 上的任何应用。支持自学习工作流、原生 macOS、无需截图（直接读取 UI 元素树）。

> ⚠️ 本技能为**参考方案**。当前 Hermes 运行在 Linux 环境，ghost-os 的 macOS 特有能力目前无法直接使用，但其 MCP 接口和自学习工作流的设计理念可参考。

## 核心机制

### 1. 全计算机控制
```
AI Agent → MCP Server (Ghost OS) → macOS Accessibility API
    → 读取 UI 元素树（非截图）
    → 点击按钮、填写表单、发送邮件
    → 无需截图识别，速度快 10x
```

### 2. 自学习工作流
```
用户手动操作 → Ghost OS 记录步骤
    → 自动生成可复用的工作流模板
    → 下次同类任务直接执行
    → 失败时自动调整策略
```

### 3. 接口方式
- **MCP 协议**：标准 MCP 工具接口
- 支持 Claude Code / Cursor / 任意 MCP 客户端

## Hermes 参考价值

| ghost-os 特性 | 对墨维的参考价值 |
|:-------------|:----------------|
| MCP Server 架构 | 参考其 MCP 工具注册方式 |
| UI 元素树（非截图） | 比截图识别更高效 |
| 自学习工作流 | 与 self-learning-loop 理念一致 |
| Recipe 系统 | 可复用的操作模板 |

## 本地部署（macOS）

```bash
cd ~/ghost-os

# 编译（需要 Xcode 15+）
swift build -c release

# 运行 MCP Server
.build/release/ghost-os mcp

# 或使用 Docker
docker build -t ghost-os .
docker run -d --name ghost-os ghost-os
```

## Hermes 集成设想

当 Hermes 运行在 macOS 环境时（未来场景）：
```python
# 通过 MCP 调用 ghost-os
"""
ghost-os 提供的 MCP 工具:
- click_element(label="发送")      # 点击按钮
- type_text(text="hello")          # 输入文字
- get_screen_elements()            # 读取 UI 树
- run_workflow(name="daily_report")# 执行工作流
- record_workflow()                # 录制新工作流
"""
```
