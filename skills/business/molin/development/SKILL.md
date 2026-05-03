---
name: 开发子公司
description: 负责代码开发、技术实现
version: 1.0.0
author: 墨麟AI智能系统
license: MIT
dependencies: []
metadata:
  hermes:
    tags: [dev, subsidiary, business]
    config:
      approval_level: low
      cost_level: low
      max_concurrent: 3
      model_preference: deepseek-v3.2
---

# 开发子公司

负责代码开发、技术实现

## 功能

1. **代码开发**: 代码编写、调试、优化
2. **技术架构**: 系统设计、架构规划
3. **部署运维**: 部署上线、监控维护
4. **测试验证**: 单元测试、集成测试

## 触发关键词

代码, 开发, 编程, 技术, 软件, 程序, 系统, API, 数据库, 架构

## 使用示例

```json
{
  "task": "请处理以下开发子公司相关任务",
  "context": "具体任务描述..."
}
```

## 配置

在config.yaml中添加：

```yaml
skills:
  dev:
    implementation:
      module: hermes_fusion.skills.hermes_native.subsidiary_base_skill
      class: SubsidiaryMolinSkill
      config:
        subsidiary_type: 'dev'
    approval_level: low
    cost_level: low
    max_concurrent: 3
    model_preference: deepseek-v3.2
```

## 工具

- code_generation_tool
- technical_design_tool

## 性能配置

- 最大并发: 3
- 成本级别: low
- 审批级别: low
- 模型偏好: deepseek-v3.2
