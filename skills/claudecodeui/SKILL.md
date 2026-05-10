---
name: claudecodeui
description: CloudCLI 可视化界面参考 — 基于 siteboon/claudecodeui (10K⭐)。在移动端和Web端使用 Claude
  Code / Cursor CLI / Codex。WebUI/GUI，远程管理Claude Code会话和项目。墨智（AI研发）的UI参考方案。
version: 1.0.0
tags:
- webui
- claude-code
- cloudcli
- gui
- remote
category: engineering
metadata:
  hermes:
    source: https://github.com/siteboon/claudecodeui
    stars: 10000
    upstream_fork: https://github.com/moye-tech/claudecodeui
    language: TypeScript/React
    molin_owner: 墨智（AI研发）
min_hermes_version: 0.13.0
---

# CloudCLI / claudecodeui — 可视化界面参考

## 概述

**CloudCLI**（claudecodeui）是一个开源 WebUI，让你在手机和浏览器上使用 Claude Code / Cursor CLI / Codex。远程管理 Agent 会话和项目。

## 核心功能

- **Web端 CLI**：浏览器中运行 Claude Code
- **移动端支持**：手机上操作 Coding Agent
- **会话管理**：远程查看/恢复/终止会话
- **多后端**：支持 Claude Code / Cursor / Codex

## 架构

```
User (Browser/Mobile)
    ↓ WebSocket
CloudCLI Server
    ↓ PTY/Process
Claude Code / Codex / Cursor CLI
```

## 对 Hermes 的参考价值

| 特性 | 参考点 |
|:----|:-------|
| WebSocket 实时通信 | Hermes 未来 Web UI 的核心传输层 |
| 多后端适配 | Learnes 自身的 gateway 可以类似扩展 |
| 移动端支持 | 随手可用的 Agent 界面 |
| 会话持久化 | 服务端保持会话状态 |

## 本地部署（参考）

```bash
cd ~/claudecodeui
cp .env.example .env
npm install
npm run dev
# 浏览器打开 http://localhost:5173
```

## 与 Hermes 现有能力的关系

当前 Hermes 以 CLI/TUI/飞书DM 为主要交互方式。claudecodeui 作为**未来 Web UI 的参考实现**，当需要 Web 管理界面时可直接参考其架构。