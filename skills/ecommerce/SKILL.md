---

name: 电商子公司
description: 负责电商、销售业务
version: 1.0.0
author: 墨麟AI智能系统
license: MIT
dependencies: []
metadata:
  hermes:
    tags: [shop, subsidiary, business]
    config:
      approval_level: medium
      cost_level: high
      max_concurrent: 3
      model_preference: claude-haiku
    molin_owner: 墨商销售（闲鱼实业）
---

# 电商子公司

负责电商、销售业务

## 功能

1. **商品管理**: 商品上架、库存管理
2. **营销推广**: 促销活动、广告投放
3. **客户服务**: 客服支持、售后处理
4. **销售分析**: 销售数据、业绩分析

## 触发关键词

电商, 销售, 商品, 产品, 店铺, 购物, 客户, 营销, 推广, 促销

## 使用示例

```json
{
  "task": "请处理以下电商子公司相关任务",
  "context": "具体任务描述..."
}
```

## 配置

在config.yaml中添加：

```yaml
skills:
  shop:
    implementation:
      module: hermes_fusion.skills.hermes_native.subsidiary_base_skill
      class: SubsidiaryMolinSkill
      config:
        subsidiary_type: 'shop'
    approval_level: medium
    cost_level: high
    max_concurrent: 3
    model_preference: claude-haiku
```

## 工具

- product_listing_tool
- sales_analysis_tool

## 性能配置

- 最大并发: 3
- 成本级别: high
- 审批级别: medium
- 模型偏好: claude-haiku
