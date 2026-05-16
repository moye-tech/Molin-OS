# feishu-message-formatter · 飞书消息格式化
# 归属: 全部5个Agent共享 · 版本: v1.0

## 技能身份
将任何内容格式化为规范的飞书消息，自动选择T0-T4格式，
确保所有Agent发出的飞书消息信噪比最优。

## 触发词（必须调用的场景）
触发词: 发送飞书|发飞书|通知墨烨|推送|汇报结果|发消息
触发词: 日报|简报|告警|审批|内容草稿就绪|卡片

## 不调用时机
- 只是内部数据处理，不需要发飞书

## 五种输出格式判断规则
T0纯文字: 消息≤3行，状态通知，随口一问
T1数据卡片(turquoise): 字段≥3个，日报/统计/产出数据
T2审批卡片(orange): governance_level=L2/L3，需要墨烨确认
T3内容预览(wathet): has_draft=true，内容草稿待审
T4告警卡片(red): is_error=true，包含"失败/错误/异常/402"

## 调用格式
INPUT: { "message": "消息内容", "ctx": { "governance_level": "L0", "has_draft": false, "is_error": false, "field_count": 0 } }
OUTPUT: 飞书消息payload（dict），可直接发送

## 执行步骤
Step 1: 调用 tools/feishu_card_router.py 的 FeishuCardRouter.route() 判断格式
Step 2: 调用 FeishuCardRouter.render() 构建payload
Step 3: 通过feishu-cli或飞书API发送

## 三句话原则（T4告警必须遵守）
1句话说清楚: 发生了什么
1句话说清楚: 影响了什么
1句话说清楚: 需要做什么

## 禁止行为
- 禁止在T4告警中输出traceback、路径、JSON原始数据
- 禁止把1-2行通知做成卡片
- 禁止把报表数据用纯文字堆积
