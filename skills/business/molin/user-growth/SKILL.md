---
name: 增长子公司
description: 负责用户增长、营销
version: 1.0.0
author: 墨麟AI智能系统
license: MIT
dependencies: []
metadata:
  hermes:
    tags: [growth, subsidiary, business]
    config:
      approval_level: medium
      cost_level: high
      max_concurrent: 3
      model_preference: claude-sonnet
---

# 增长子公司

负责用户增长、营销

## 功能

1. **用户获取**: 获客策略、渠道拓展
2. **用户激活**: 激活流程、体验优化
3. **用户留存**: 留存策略、忠诚度管理
4. **转化优化**: 转化率提升、漏斗分析

## 触发关键词

增长, 用户, 营销, 获客, 留存, 激活, 转化, 漏斗, 渠道, 投放

## 使用示例

```json
{
  "task": "请处理以下增长子公司相关任务",
  "context": "具体任务描述..."
}
```

## 配置

在config.yaml中添加：

```yaml
skills:
  growth:
    implementation:
      module: hermes_fusion.skills.hermes_native.subsidiary_base_skill
      class: SubsidiaryMolinSkill
      config:
        subsidiary_type: 'growth'
    approval_level: medium
    cost_level: high
    max_concurrent: 3
    model_preference: claude-sonnet
```

## 工具

- user_acquisition_tool
- retention_analysis_tool

## 性能配置

- 最大并发: 3
- 成本级别: high
- 审批级别: medium
- 模型偏好: claude-sonnet
