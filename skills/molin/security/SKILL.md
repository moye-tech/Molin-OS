---

name: 安全子公司
description: 负责安全、合规、风控
version: 1.0.0
author: 墨麟AI智能系统
license: MIT
dependencies: []
metadata:
  hermes:
    tags: [secure, subsidiary, business]
    config:
      approval_level: high
      cost_level: low
      max_concurrent: 2
      model_preference: glm-5
    molin_owner: 墨盾（安全/QA）
---

# 安全子公司

负责安全、合规、风控

## 功能

1. **安全审计**: 安全检查、漏洞扫描
2. **合规管理**: 合规检查、风险管理
3. **数据保护**: 数据加密、隐私保护
4. **安全监控**: 实时监控、事件响应

## 触发关键词

安全, 合规, 风险, 审核, 检查, 监控, 审计, 保护, 加密, 隐私

## 使用示例

```json
{
  "task": "请处理以下安全子公司相关任务",
  "context": "具体任务描述..."
}
```

## 配置

在config.yaml中添加：

```yaml
skills:
  secure:
    implementation:
      module: hermes_fusion.skills.hermes_native.subsidiary_base_skill
      class: SubsidiaryMolinSkill
      config:
        subsidiary_type: 'secure'
    approval_level: high
    cost_level: low
    max_concurrent: 2
    model_preference: glm-5
```

## 工具

- security_audit_tool
- compliance_check_tool

## 性能配置

- 最大并发: 2
- 成本级别: low
- 审批级别: high
- 模型偏好: glm-5
