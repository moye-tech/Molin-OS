---

name: AI子公司
description: 负责提示工程、AI优化
version: 1.0.0
author: 墨麟AI智能系统
license: MIT
dependencies: []
metadata:
  hermes:
    tags: [ai, subsidiary, business]
    config:
      approval_level: low
      cost_level: low
      max_concurrent: 2
      model_preference: glm-5
    molin_owner: 墨智（AI研发）
---

# AI子公司

负责提示工程、AI优化

## 功能

1. **模型训练**: AI模型训练、优化
2. **提示工程**: 提示词优化、模板设计
3. **模型部署**: 模型部署、API服务
4. **性能评估**: 模型评估、性能监控

## 触发关键词

提示, AI, 模型, 智能, 优化, 调整, 参数, 配置, 训练, 微调

## 使用示例

```json
{
  "task": "请处理以下AI子公司相关任务",
  "context": "具体任务描述..."
}
```

## 配置

在config.yaml中添加：

```yaml
skills:
  ai:
    implementation:
      module: hermes_fusion.skills.hermes_native.subsidiary_base_skill
      class: SubsidiaryMolinSkill
      config:
        subsidiary_type: 'ai'
    approval_level: low
    cost_level: low
    max_concurrent: 2
    model_preference: glm-5
```

## 工具

- prompt_optimization_tool
- model_evaluation_tool

## 性能配置

- 最大并发: 2
- 成本级别: low
- 审批级别: low
- 模型偏好: glm-5
