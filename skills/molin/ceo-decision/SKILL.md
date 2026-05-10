---

name: CEO Decision Engine
description: CEO决策引擎 - 负责ROI分析、三层决策（GO/NO_GO/NEED_INFO）、记忆集成的CEO决策系统
version: 1.0.0
author: 墨麟AI智能系统
license: MIT
dependencies: []
metadata:
  hermes:
    tags: [ceo, decision, roi, analysis, business, investment]
    config:
      min_roi_ratio: 1.5
      min_confidence: 0.7
      max_payback_days: 180
      high_composite_score: 7.0
    molin_owner: CEO
---

# CEO决策引擎

专业的CEO决策系统，负责分析项目ROI、做出三层决策（GO/NO_GO/NEED_INFO），并集成记忆系统。

## 功能

1. **ROI分析**：分析项目预算、时间线、目标收入，计算ROI
2. **三层决策**：基于ROI分析和记忆系统做出GO/NO_GO/NEED_INFO决策
3. **记忆集成**：查询分层记忆系统（SQLite/Qdrant/Redis/Supermemory）
4. **每日优化**：执行每日决策优化和系统调优

## 触发关键词

- 决策
- 分析
- ROI
- 预算
- 项目
- 投资
- 评估
- 审批
- ceo
- ceo决策

## 使用示例

```json
{
  "task": "分析一个投资项目的ROI和预算",
  "budget": 50000,
  "target_revenue": 150000,
  "timeline": "90天"
}
```

## 配置

在config.yaml中添加：

```yaml
skills:
  ceo_decision:
    implementation:
      module: hermes_fusion.skills.hermes_native.ceo_decision_skill
      class: CeoDecisionMolinSkill
    approval_level: high
    cost_level: high
    max_concurrent: 1
    model_preference: glm-5
```

## 工具

- analyze_roi_tool: ROI分析工具
- make_decision_tool: 决策工具
- query_memory_tool: 记忆查询工具
- daily_optimization_tool: 每日优化工具

## 性能配置

- 超时: 30秒
- 重试次数: 2
- 缓存启用: 是
- 缓存TTL: 300秒