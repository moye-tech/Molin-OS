---
name: molin-customer-service
description: "墨声 · 智能客服引擎 — AI驱动的客服应答、FAQ自动维护、工单管理、满意度追踪。Use when: 用户需要配置客服自动回复、管理FAQ、处理客户咨询、追踪服务满意度。集成Hermes的xianyu-automation和send_message能力。"
version: 1.0.0
author: Hermes Agent (Molin AI)
license: MIT
metadata:
  hermes:
    tags: [customer-service, faq, ticket, automation, chatbot, support, molin]
    related_skills: [xianyu-automation, marketing-skills-copywriting, marketing-skills-cro, social-push-publisher]
    molin_owner: 墨声（智能客服）
---

# 墨声 · 智能客服引擎

## 概述

**墨声** 是赫墨斯 OS 的原生智能客服引擎。**不依赖任何外部客服系统或第三方SaaS**——墨声利用 Hermes 自身能力（记忆、工具、技能编排）来实现完整客服生命周期：FAQ 维护、自动应答、工单追踪、满意度测量、多平台消息发送。

### 核心理念

```
客户消息 → 意图识别 → FAQ匹配/工单创建 → 自动回复/人工升级 → 满意度追踪 → FAQ知识库迭代
```

墨声将 Hermes 的内建能力重组为客服管线，而非引入外部依赖。

---

## 何时使用

- 用户说："帮我配置自动回复"、"客户问XX问题该怎么回"
- 用户说："帮我管理FAQ"、"添加一条新的问答"
- 用户说："查一下工单进度"、"创建一个售后工单"
- 用户说："给客户发个消息"、"回复所有未处理的咨询"
- 用户说："做个满意度调查"、"追踪本周的服务评分"
- 用户说："接入了闲鱼，帮我自动回复买家问题"

---

## 架构：Hermes 即客服引擎

墨声不依赖任何外部 OSS 客服项目。它利用 Hermes 内建能力构成完整客服系统：

| 客服功能 | Hermes 能力 | 说明 |
|---------|-------------|------|
| **FAQ知识库** | `memory / session_search` | FAQ 存储为记忆条目，通过语义搜索匹配 |
| **自动回复模板** | `skill` 及其内建指令 | 回复模板定义为 skill 指令，按意图路由 |
| **工单状态追踪** | `todo` 任务系统 | 每个工单是一个 todo，含优先级/状态/截止日期 |
| **满意度调查** | `clarify` + 模板消息 | 会话结束后发送满意度评分请求 |
| **闲鱼消息自动化** | `xianyu-automation` | 对接闲鱼买家消息，自动检测购买/退款信号 |
| **多平台回复** | `send_message` / 平台特定 skill | 通过 Hermes 消息通道回复微信/邮件/飞书等 |
| **客服统计** | `session_search` + 汇总 | 分析客服会话数据生成服务报告 |

### 数据流

```
                     ┌─────────────────────┐
                     │   客户消息来源        │
                     │  (闲鱼/微信/邮件/飞书) │
                     └──────────┬──────────┘
                                ▼
                     ┌─────────────────────┐
                     │   意图识别 (LLM)     │
                     │  分类: 咨询/售后/投诉 │
                     └──────────┬──────────┘
                                ▼
              ┌─────────────────────────────────┐
              │                                 │
              ▼                                 ▼
    ┌──────────────────┐             ┌──────────────────┐
    │ FAQ 自动匹配      │             │ 工单创建 (todo)   │
    │ (memory_search)  │             │ 优先级: P0-P3    │
    │ → 自动回复        │             │ → 通知客服跟进    │
    └──────────────────┘             └──────────────────┘
              │                                 │
              └──────────────┬──────────────────┘
                             ▼
                   ┌──────────────────┐
                   │ 满意度追踪         │
                   │ (clarify + 评分)  │
                   │ → FAQ知识库迭代    │
                   └──────────────────┘
```

---

## FAQ 知识库管理

FAQ 存储为 Hermes 记忆条目（`memory` 或 `session_search` 可检索），每个条目包含问题、答案、分类、标签。

### FAQ 条目格式

将每个 FAQ 存储为结构化的记忆条目：

```yaml
faq_entry:
  id: "faq-001"
  category: "shipping"          # 分类: shipping/refund/product/account/general
  question: "发货时间是多久？"
  keywords: ["发货", "物流", "快递", "配送", "多久到"]
  answer: "订单确认后24小时内发货，通常3-5个工作日送达。如遇节假日可能延迟，我们会提前通知。"
  tone: "friendly"              # 语气: friendly/professional/urgent
  priority: 1                   # 匹配优先级: 1(高) / 2(中) / 3(低)
  used_count: 0                 # 使用次数（自动递增）
  last_used: null               # 最后匹配时间
  satisfaction: 4.5             # 用户满意度(1-5)
  created: "2026-05-04"
  updated: "2026-05-04"
```

### FAQ 操作流程

#### 添加 FAQ

```
1. 用户提供问题+答案
2. 提取关键词（LLM 自动生成 5-10 个同义/相关词）
3. 分配分类和优先级
4. 存储为记忆条目
5. 确认：告知用户FAQ已添加及匹配示例
```

#### 搜索 FAQ

使用 `session_search` 或语义匹配来找到最匹配的 FAQ：

```
输入：客户消息 → 关键词提取 → 记忆搜索 → 匹配度评分 → 返回 top-3 FAQ
```

匹配度评分标准：
- **≥90%**：直接自动回复（无需人工确认）
- **70-89%**：推荐给客服确认后回复
- **<70%**：创建工单，由人工处理

#### 自动回复模板

回复模板可定义为 skill 指令，按客户意图路由：

```yaml
reply_templates:
  greeting:
    trigger: ["你好", "在吗", "hello", "hi"]
    reply: "您好！我是墨声智能客服，请问有什么可以帮您的？😊"
    tone: friendly

  shipping_query:
    trigger: ["发货", "物流", "快递", "什么时候到"]
    reply_template: |
      您好！关于{product_name}的物流信息：
      - 发货时间：{shipping_time}
      - 预计送达：{estimated_delivery}
      - 物流单号：{tracking_number}
      您可以随时在订单页面查看物流进度。如有其他问题请随时问我！
    tone: friendly

  refund_request:
    trigger: ["退款", "退货", "不要了", "取消订单"]
    reply: "您好，非常抱歉给您带来不便。退款流程如下：... 如需要人工处理，请回复"人工""
    tone: professional

  escalation:
    trigger: ["人工", "投诉", "经理", "负责人"]
    reply: "好的，我将为您转接人工客服，请稍候。您的工单编号：{ticket_id}"
    tone: professional
```

---

## 工单管理（基于 todo）

每个客服工单是一个 Hermes `todo` 条目。Todo 的优先级、状态、截止日期直接映射为工单管理字段。

### 工单生命周期

```
创建 (todo create) → 待处理 (status: pending)
    → 处理中 (status: in_progress)
    → 已解决 (status: done)
    → 满意度追踪 → 关闭
```

### 工单四级优先级

| 优先级 | Hermes todo 标记 | 响应时限 | 适用场景 |
|--------|-----------------|---------|---------|
| **P0 紧急** | `priority: critical` | 30分钟内 | 投诉、退款纠纷、系统故障 |
| **P1 高** | `priority: high` | 2小时内 | 售后问题、产品故障 |
| **P2 中** | `priority: medium` | 24小时内 | 产品咨询、使用指导 |
| **P3 低** | `priority: low` | 48小时内 | 建议、一般性提问 |

### 工单数据结构

```yaml
ticket:
  id: "TK-20260504-001"        # 自动生成
  created: "2026-05-04T10:30:00Z"
  customer:
    name: "王先生"
    platform: "xianyu"         # 来源平台: xianyu/wechat/email/feishu
    contact: "用户ID或联系方式"
  category: "refund"           # 分类: shipping/product/refund/account/complaint/other
  priority: "high"             # 对应 Hermes todo priority
  status: "pending"            # pending / in_progress / resolved / closed
  summary: "客户要求退款，理由是产品与描述不符"
  messages:
    - role: "customer"
      content: "这个产品跟描述不一样，我要退款"
      time: "2026-05-04T10:28:00Z"
    - role: "agent"
      content: "已为您创建退款工单，编号TK-20260504-001"
      time: "2026-05-04T10:30:00Z"
  resolution: null
  satisfaction: null           # 1-5 评分
  assigned_to: null
  sla_deadline: "2026-05-04T12:30:00Z"  # P1 → 2小时
```

### 工单操作指令

```bash
# 创建工单
create_ticket:
  goal: "创建售后工单"
  input:
    customer_name: "王先生"
    platform: "xianyu"
    category: "refund"
    priority: "high"
    summary: "客户要求退款，产品与描述不符"

# 查询工单
search_tickets:
  goal: "查询所有待处理的P0/P1工单"
  filter:
    priority_in: ["critical", "high"]
    status: "pending"

# 更新工单状态
update_ticket:
  goal: "标记工单TK-20260504-001为已解决"
  ticket_id: "TK-20260504-001"
  new_status: "resolved"
  resolution: "已为客户办理全额退款，退款将在3个工作日内到账"

# 工单统计
ticket_stats:
  goal: "生成本周客服工单统计报告"
  period: "week"
  metrics: ["total", "by_category", "by_priority", "avg_resolution_time", "satisfaction_avg"]
```

---

## 满意度追踪

客户会话或工单关闭后，使用 Hermes 的 `clarify` 能力发送满意度调查。

### 满意度的端工作流

```
工单关闭 (status: resolved)
  ↓
等待 1 小时（冷却期）
  ↓
发送满意度调查消息（通过原平台）
  ↓
客户评分 (1-5) + 可选文字反馈
  ↓
记录到工单 + FAQ 关联更新
  ↓
定期生成满意度报告
```

### 调查模板

```yaml
satisfaction_survey:
  message: |
    您好，您的问题已处理完毕。麻烦您花10秒钟给个评价：
    
    😍 非常满意（5分）
    🙂 满意（4分）
    😐 一般（3分）
    😞 不满意（2分）
    😡 非常不满意（1分）
    
    您的反馈将帮助我们持续改进服务质量，谢谢！
```

### 评分分析

| 评分 | 含义 | 后续行动 |
|:----:|------|---------|
| 5 | 非常满意 | 记录最佳案例，更新 FAQ |
| 4 | 满意 | 记录 |
| 3 | 一般 | 询问改进建议 |
| 1-2 | 不满意 | 自动升级为 P0 工单，客服主管介入回访 |

---

## 闲鱼客服自动化

墨声深度集成 `xianyu-automation` skill，实现闲鱼平台 7x24 小时自动客服。

### 闲鱼消息处理管线

```
闲鱼买家消息 → xianyu-automation 消息轮询 (30s间隔)
  → 信号检测（购买/退款/咨询/闲聊）
  → 墨声意图识别
  → FAQ 自动匹配或工单创建
  → 自动回复（通过 xianyu-automation 消息管道）
```

### 闲鱼特定 FAQ 分类

| 分类 | 常见问题 | 自动回复策略 |
|------|---------|-------------|
| **购买意向** | "还在吗"、"怎么买"、"多少钱" | 自动发送购买引导 + 商品链接 |
| **价格议价** | "能便宜吗"、"最低多少" | 根据预设议价策略自动回复 |
| **产品咨询** | "这个多大"、"什么材质" | FAQ 匹配自动回复 |
| **物流查询** | "发货了吗"、"快递单号" | 查 todo/订单记录自动回复 |
| **售后问题** | "坏了"、"用不了"、"退货" | 创建 P1 工单 + 自动回复售后流程 |
| **退款要求** | "我要退款"、"退钱" | 创建 P0 工单 + 转接人工 |

### 闲鱼回复模板（对接 marketing-skills-copywriting）

利用 `marketing-skills-copywriting` 的 Persuasion Frameworks（AIDA/PAS/4P）优化闲鱼回复文案：

```yaml
xianyu_reply_template:
  purchase_intent:
    framework: "AIDA"
    reply: |
      【Attention】您好，感谢关注！
      【Interest】这款产品目前是活动价，性价比很高
      【Desire】已经有{count}位客户下单，好评率{rate}%
      【Action】点击下方链接可直接下单：
      {product_link}
  
  price_negotiation:
    framework: "PAS"
    reply: |
      【Problem】理解您觉得价格偏高
      【Agitate】市面上同类产品均价在{market_price}左右
      【Solve】我们给您特殊优惠价{sale_price}，今天下单还送{bonus}
```

---

## 多平台客服回复

墨声通过 Hermes 的 `send_message` 能力（以及各平台特定 skill）实现跨平台统一客服。

| 平台 | 实现方式 | 适用场景 |
|------|---------|---------|
| **闲鱼** | `xianyu-automation` 消息管道 | 闲鱼买家咨询 |
| **微信** | `send_message` / wechat skill | 微信客户咨询 |
| **邮件** | `email/himalaya` skill | 邮件客服 |
| **飞书** | `feishu-message-formatter` | 飞书群客服 |
| **网页** | `send_message` (HTTP webhook) | 网站客服嵌入 |

---

## 完整工作流示例

### 场景：闲鱼买家咨询产品

```
1. 买家发消息："你好，这个手机壳还有吗？"
2. xianyu-automation 轮询到新消息
3. 墨声意图识别 → "product_availability" (92% 置信度)
4. FAQ 搜索 → 匹配 faq-042 "产品库存查询"
5. 自动回复："您好！这款手机壳目前有货喔~ 黑色和白色都有现货，下单后24小时内发出🚚"
6. 记录会话到 memory
```

### 场景：客户投诉退款

```
1. 客户发消息："收到的货是坏的，我要退款！"
2. 意图识别 → "refund_complaint" (95% 置信度)
3. FAQ 匹配度 < 70% → 创建工单
4. 创建 todo(priority=critical) — P0 紧急
5. 自动回复："非常抱歉给您带来不好的体验！我已经为您创建了售后工单(TK-20260504-002)，客服专员会尽快联系您处理..."
6. 通知客服主管（通过 send_message 或飞书通知）
7. 客服处理后关闭工单 → 发送满意度调查
```

---

## 客服质量报告

使用 `session_search` 和统计聚合生成客服报告：

```yaml
service_report:
  period: "2026-05-01 to 2026-05-07"
  metrics:
    total_conversations: 247
    auto_resolved: 186          # 自动回复解决的占比
    auto_resolve_rate: "75.3%"
    tickets_created: 61
    tickets_resolved: 55
    avg_resolution_time: "3.2h"
    
    satisfaction:
      total_responses: 48
      avg_score: 4.3
      distribution:
        5: 22
        4: 18
        3: 5
        2: 2
        1: 1
    
    top_faqs:
      - question: "发货时间是多久？"
        used: 45
        satisfaction: 4.6
      - question: "怎么退货？"
        used: 23
        satisfaction: 4.1
    
    improvement_suggestions:
      - "FAQ '退款到账时间' 满意度偏低(3.2)，建议更新回复内容"
      - "P0工单平均响应时间28分钟，接近SLA阈值(30分钟)"
```

---

## 验证清单

- [ ] FAQ 知识库已初始化（至少 5 条常见问答）
- [ ] 自动回复模板已配置（至少覆盖咨询/售后/投诉三类）
- [ ] 工单创建流程可正常运行（todo 创建/查询/更新）
- [ ] 闲鱼集成已配置（xianyu-automation 消息管道对接）
- [ ] 满意度调查模板可用
- [ ] 至少一个平台（闲鱼/微信/邮件）的消息发送已验证
- [ ] P0/P1 紧急工单的通知机制已配置
- [ ] 客服报告生成流程可运行

---

## FAQ 维护最佳实践

1. **定期审核**: 每周检查 FAQ 使用频率和满意度，淘汰或更新低效条目
2. **闭环迭代**: 满意度评分 < 3 的 FAQ → 人工审核修改内容
3. **关键词扩展**: 每季度更新 FAQ 关键词列表，覆盖新出现的用户说法
4. **季节性更新**: 节假日前后更新相关 FAQ（如春节物流延迟提醒）
5. **A/B 测试**: 对高频 FAQ 测试不同回复风格，选取满意度高的版本
