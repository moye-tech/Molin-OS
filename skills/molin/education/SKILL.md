---

name: 教育子公司
description: 负责教育、培训、知识付费业务
version: 1.0.0
author: 墨麟AI智能系统
license: MIT
dependencies: []
metadata:
  hermes:
    tags: [edu, subsidiary, business]
    config:
      approval_level: medium
      cost_level: low
      max_concurrent: 2
      model_preference: qwen3.6-plus
    molin_owner: 墨育（教育）
---

# 教育子公司

负责教育、培训、知识付费业务

## 功能

1. **课程管理**: 课程创建、编辑、发布
2. **培训材料**: 培训内容开发、资料管理
3. **知识付费**: 付费课程、订阅管理
4. **教学支持**: 学习路径规划、进度跟踪

## 触发关键词

课程, 培训, 教育, 学习, 知识付费, 教学, 学校, 学生, 老师, 教材

## 使用示例

```json
{
  "task": "请处理以下教育子公司相关任务",
  "context": "具体任务描述..."
}
```

## 配置

在config.yaml中添加：

```yaml
skills:
  edu:
    implementation:
      module: hermes_fusion.skills.hermes_native.subsidiary_base_skill
      class: SubsidiaryMolinSkill
      config:
        subsidiary_type: 'edu'
    approval_level: medium
    cost_level: low
    max_concurrent: 2
    model_preference: qwen3.6-plus
```

## 工具

- course_creation_tool
- training_material_tool

## 性能配置

- 最大并发: 2
- 成本级别: low
- 审批级别: medium
- 模型偏好: qwen3.6-plus
