---

name: 产品子公司
description: 负责产品规划、设计
version: 1.0.0
author: 墨麟AI智能系统
license: MIT
dependencies: []
metadata:
  hermes:
    tags: [product, subsidiary, business]
    config:
      approval_level: medium
      cost_level: medium
      max_concurrent: 2
      model_preference: qwen3.6-plus
    molin_owner: 墨品（产品设计）
---

# 产品子公司

负责产品规划、设计

## 功能

1. **产品规划**: 产品路线图、版本规划
2. **需求分析**: 需求收集、优先级排序
3. **用户体验**: 交互设计、可用性测试
4. **产品迭代**: 版本迭代、功能优化

## 触发关键词

产品, 设计, 规划, 需求, 功能, 体验, 界面, 原型, 测试, 迭代

## 使用示例

```json
{
  "task": "请处理以下产品子公司相关任务",
  "context": "具体任务描述..."
}
```

## 配置

在config.yaml中添加：

```yaml
skills:
  product:
    implementation:
      module: hermes_fusion.skills.hermes_native.subsidiary_base_skill
      class: SubsidiaryMolinSkill
      config:
        subsidiary_type: 'product'
    approval_level: medium
    cost_level: medium
    max_concurrent: 2
    model_preference: qwen3.6-plus
```

## 工具

- product_design_tool
- requirement_analysis_tool

## 性能配置

- 最大并发: 2
- 成本级别: medium
- 审批级别: medium
- 模型偏好: qwen3.6-plus
