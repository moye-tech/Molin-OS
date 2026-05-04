---
name: claude-code-sourcemap
description: Claude Code 源码参考 — 基于 ChinaSiro/claude-code-sourcemap (9K⭐)，通过 npm sourcemap 还原的 4756 个文件（含1884个 .ts/.tsx）。提供 Claude Code v2.1.88 的完整TypeScript源码作为代码分析/工具参考源。
version: 1.0.0
tags: [claude-code, source-code, reference, typescript, analysis]
category: engineering
metadata:
  hermes:
    source: https://github.com/ChinaSiro/claude-code-sourcemap
    stars: 9000
    upstream_fork: https://github.com/moye-tech/claude-code-sourcemap
    files: 4756
    ts_files: 1884
    version: 2.1.88
    note: 与 claude-code-repo（claude-code-best版）同源但还原方式不同，可交叉参考
    molin_owner: 墨智（AI研发）
---

# Claude Code Sourcemap — 源码参考

## 概述

通过 npm 包 `@anthropic-ai/claude-code` 的 sourcemap（`cli.js.map`）还原的 TypeScript 源码，版本 v2.1.88。

**与已有 claude-code-repo 的区别：**

| 对比 | claude-code-repo（已有） | claude-code-sourcemap |
|:----|:-----------------------|:---------------------|
| 来源 | 反向工程/社区复原 | npm sourcemap 直接还原 |
| 文件数 | ~1300个 | 4756个（含1884个ts/tsx） |
| 目录 | 工具为主 | 完整项目结构 |
| 备注 | 有1341个tsc错误 | 更完整的源码 |

## 目录结构（关键模块）

```
restored-src/src/
├── main.tsx              # CLI 入口
├── tools/                # 工具实现（30+ 个）
├── commands/             # 命令实现（40+ 个）
├── services/             # API、MCP、分析等服务
├── coordinator/          # 多 Agent 协调模式
├── assistant/            # 助手模式（KAIROS）
├── buddy/                # AI 伴侣 UI
├── remote/               # 远程会话
├── plugins/              # 插件系统
├── skills/               # 技能系统
├── voice/                # 语音交互
└── vim/                  # Vim 模式
```

## 使用方式

```bash
cd ~/claude-code-sourcemap
# 查看还原的源码
ls package/
# 提取源文件
node extract-sources.js
```

当需要参考 Claude Code 的某个具体实现（如 coordinator / skills 系统 / plugin 架构）时，可以交叉对比这个版本与已有 claude-code-repo 的差异，获取更完整的实现参考。
