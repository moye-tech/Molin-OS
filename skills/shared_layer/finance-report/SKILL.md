# finance-report · 财务报告
# 归属: Agent D (shared)
## 触发词
触发词: 财务|收入|支出|利润|成本|API费用|月报
触发词: 对账|预算|余额|花了多少钱
## 核心指标
收入: 副业订单收入 + 教育课程收入
成本: API费用 + 工具订阅 + 推广费
利润率 = (收入-成本)/收入 × 100%
## 数据来源
relay/side/orders.json（副业收入）
relay/edu/crm.json（教育收入）
hermes -p shared config get DASHSCOPE_MONTHLY_COST（API成本）
## 月报格式
{ "revenue": {"edu": 0, "side": 0}, "cost": {"api": 0, "tools": 0, "ads": 0}, "profit_rate": 0, "forecast": "下月预测" }
