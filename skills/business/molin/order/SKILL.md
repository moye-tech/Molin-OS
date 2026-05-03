---
name: 订单子公司
description: 负责定价、订单、交易处理
version: 1.0.0
author: 墨麟AI智能系统
license: MIT
dependencies: []
metadata:
  hermes:
    tags: [order, subsidiary, business]
    config:
      approval_level: high
      cost_level: high
      max_concurrent: 3
      model_preference: claude-sonnet
---

# 订单子公司

负责定价、订单、交易处理

## 功能

1. **订单处理**: 订单创建、修改、取消
2. **价格管理**: 定价策略、折扣管理
3. **交易处理**: 支付处理、退款管理
4. **物流跟踪**: 发货、配送、签收跟踪

## 触发关键词

订单, 价格, 定价, 交易, 支付, 购买, 销售, 金额, 费用, 账单

## 使用示例

```json
{
  "task": "请处理以下订单子公司相关任务",
  "context": "具体任务描述..."
}
```

## 配置

在config.yaml中添加：

```yaml
skills:
  order:
    implementation:
      module: hermes_fusion.skills.hermes_native.subsidiary_base_skill
      class: SubsidiaryMolinSkill
      config:
        subsidiary_type: 'order'
    approval_level: high
    cost_level: high
    max_concurrent: 3
    model_preference: claude-sonnet
```

## 工具

- pricing_tool
- order_processing_tool

## 性能配置

- 最大并发: 3
- 成本级别: high
- 审批级别: high
- 模型偏好: claude-sonnet
