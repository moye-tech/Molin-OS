---

name: IP子公司
description: 负责内容创作、IP孵化
version: 1.0.0
author: 墨麟AI智能系统
license: MIT
dependencies: []
metadata:
  hermes:
    tags: [ip, subsidiary, business]
    config:
      approval_level: medium
      cost_level: medium
      max_concurrent: 2
      model_preference: claude-opus
    molin_owner: 墨影（IP孵化）
---

# IP子公司

负责内容创作、IP孵化

## 功能

1. **内容创作**: 文案、视频、图片创作
2. **IP管理**: IP孵化、版权管理
3. **社交媒体**: 内容发布、粉丝互动
4. **品牌建设**: 品牌形象、宣传材料

## 触发关键词

内容, 创作, IP, 文案, 文章, 视频, 图片, 设计, 创意, 故事

## 使用示例

```json
{
  "task": "请处理以下IP子公司相关任务",
  "context": "具体任务描述..."
}
```

## 配置

在config.yaml中添加：

```yaml
skills:
  ip:
    implementation:
      module: hermes_fusion.skills.hermes_native.subsidiary_base_skill
      class: SubsidiaryMolinSkill
      config:
        subsidiary_type: 'ip'
    approval_level: medium
    cost_level: medium
    max_concurrent: 2
    model_preference: claude-opus
```

## 工具

- content_creation_tool
- ip_management_tool

## 性能配置

- 最大并发: 2
- 成本级别: medium
- 审批级别: medium
- 模型偏好: claude-opus
