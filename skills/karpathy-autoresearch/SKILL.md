---
name: karpathy-autoresearch
description: 自主科研Agent — 基于 karpathy/autoresearch (78K⭐)。AI Agent在单GPU上独立运行科研流程：提出假设→收集数据→分析→生成报告。墨思（情报研究）核心增强。
version: 1.0.0
tags:
- research
- agent
- autonomous
- karpathy
- scientific
- gpu
category: research
metadata:
  hermes:
    source: https://github.com/karpathy/autoresearch
    stars: 78662
    author: Andrej Karpathy
    molin_owner: 墨思（情报研究）
min_hermes_version: 0.13.0
---

# Karpathy AutoResearch — 自主科研Agent

## 概述

Andrej Karpathy 开发的自主科研Agent，在单GPU上运行完整科研流程。墨思情报局的"研究引擎"升级——从"搜集情报"升级到"做研究"。

## 核心流程

```
研究问题
    │
    ▼
┌───────────────┐
│ 1. 文献调研   │  → 搜索相关论文/文章
└───────┬───────┘
        ▼
┌───────────────┐
│ 2. 假设生成   │  → AI提出可验证假设
└───────┬───────┘
        ▼
┌───────────────┐
│ 3. 实验设计   │  → 设计验证方案
└───────┬───────┘
        ▼
┌───────────────┐
│ 4. 数据分析   │  → 运行实验+分析结果
└───────┬───────┘
        ▼
┌───────────────┐
│ 5. 报告生成   │  → 结构化研究输出
└───────────────┘
```

## Hermes 集成

当需要深度研究时：
```python
# 1. 调研阶段（墨思已有能力）
last30days(query="AI教育趋势")
world-monitor()

# 2. 深度分析（使用autoresearch模式）
"""
研究问题：AI教育工具在中国市场的增长潜力
研究方式：文献调研→假设→分析→报告
"""

# 3. 输出结构化研究报告
```

## 本地运行

```bash
cd ~/autoresearch  # 需先克隆
pip install -r requirements.txt
python run.py --topic "研究主题"
```