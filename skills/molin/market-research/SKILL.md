---

name: 研究子公司
description: 负责市场研究、竞品分析
version: 1.0.0
author: 墨麟AI智能系统
license: MIT
dependencies: []
metadata:
  hermes:
    tags: [research, subsidiary, business]
    config:
      approval_level: medium
      cost_level: medium
      max_concurrent: 2
      model_preference: claude-opus
    molin_owner: 墨思（情报研究）
---

# 研究子公司

负责市场研究、竞品分析

## 功能

1. **市场研究**: 市场分析、趋势研究
2. **竞品分析**: 竞争对手、产品分析
3. **机会识别**: 机会发现、风险评估
4. **研究报告**: 报告撰写、成果展示

## 触发关键词

研究, 市场, 竞品, 分析, 调研, 报告, 趋势, 机会, 威胁, SWOT

## 使用示例

```json
{
  "task": "请处理以下研究子公司相关任务",
  "context": "具体任务描述..."
}
```

## 配置

在config.yaml中添加：

```yaml
skills:
  research:
    implementation:
      module: hermes_fusion.skills.hermes_native.subsidiary_base_skill
      class: SubsidiaryMolinSkill
      config:
        subsidiary_type: 'research'
    approval_level: medium
    cost_level: medium
    max_concurrent: 2
    model_preference: claude-opus
```

## 工具

- market_research_tool
- competitor_analysis_tool

## 性能配置

- 最大并发: 2
- 成本级别: medium
- 审批级别: medium
- 模型偏好: claude-opus
