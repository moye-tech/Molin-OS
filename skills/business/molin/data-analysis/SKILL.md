---
name: 数据子公司
description: 负责数据分析、洞察
version: 1.0.0
author: 墨麟AI智能系统
license: MIT
dependencies: []
metadata:
  hermes:
    tags: [data, subsidiary, business]
    config:
      approval_level: low
      cost_level: medium
      max_concurrent: 2
      model_preference: qwen3.6-plus
---

# 数据子公司

负责数据分析、洞察

## 功能

1. **数据分析**: 数据清洗、分析处理
2. **报表生成**: 报表制作、可视化展示
3. **业务洞察**: 业务分析、趋势预测
4. **数据挖掘**: 模式发现、价值提取

## 触发关键词

数据, 分析, 统计, 报表, 指标, 可视化, 洞察, 趋势, 预测, 挖掘

## 使用示例

```json
{
  "task": "请处理以下数据子公司相关任务",
  "context": "具体任务描述..."
}
```

## 配置

在config.yaml中添加：

```yaml
skills:
  data:
    implementation:
      module: hermes_fusion.skills.hermes_native.subsidiary_base_skill
      class: SubsidiaryMolinSkill
      config:
        subsidiary_type: 'data'
    approval_level: low
    cost_level: medium
    max_concurrent: 2
    model_preference: qwen3.6-plus
```

## 工具

- data_analysis_tool
- report_generation_tool

## 性能配置

- 最大并发: 2
- 成本级别: medium
- 审批级别: low
- 模型偏好: qwen3.6-plus
