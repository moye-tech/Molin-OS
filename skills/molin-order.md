---
name: molin-order
description: 墨单订单 — 全生命周期订单管理，从询盘到收款的完整闭环
version: 2.0.0
molin_owner: 墨链电商
molin_vp: 运营
approval_level: L1
dependencies:
  - molib.agencies.order.invoice_engine
  - molib.agencies.order.payment_tracker
  - molib.agencies.workers.order_worker
  - molib.business.order_engine
  - molib.infra.pocketbase
integrations:
  - Invoice Ninja (9K⭐, 发票设计模式)
  - Kill Bill (4.7K⭐, 订阅计费模式)
  - PocketBase (54K⭐, 统一后端)
---

# 墨单订单 · 完整技能

## 概述

墨单订单是墨麟AI集团的订单全生命周期管理系统。覆盖从商机发现→报价→发票→收款→交付的完整闭环。

## 架构

```
询盘来源 (闲鱼/猪八戒/直接) 
  → PlatformScanner (评分+匹配) 
  → Order (状态机)
  → HumanGateManager (L0/L1/L2 人工门控)
  → InvoiceEngine (发票生成+HTML)
  → PaymentTracker (支付追踪+验证码)
  → PocketBase (可选: 统一后端存储)
```

## CLI 命令

```bash
# 订单管理
python -m molib order create --title "项目名" --source xianyu --value 500
python -m molib order list --status won
python -m molib order status --order-id ORD-XXX
python -m molib order transition --order-id ORD-XXX --to bidding
python -m molib order stats
python -m molib order report
python -m molib order remind-overdue

# 发票
python -m molib order invoice --order-id ORD-XXX --customer "客户名"
python -m molib order invoice --order-id ORD-XXX --items '[{"name":"服务费","amount":1000}]'

# 支付
python -m molib order payment --invoice-id INV-XXX --amount 1000 --method wechat
```

## Python API

```python
from molib.agencies.workers.order_worker import OrderWorker

worker = OrderWorker()

# 创建订单
order = worker.create_order(source="xianyu", title="AI咨询", 
                             description="企业AI部署咨询", estimated_value=5000)

# 生成发票
invoice = worker.create_invoice(order_id=order["order_id"],
                                customer_name="客户A", tax_regime="CN_SMALL")

# 记录支付
payment = worker.record_payment(invoice_id=invoice["invoice_id"],
                                 amount=5000, method="wechat")

# 综合报告
report = worker.daily_report()
```

## 状态机

```
DISCOVERED → EVALUATING → PRICING → BIDDING → NEGOTIATING → WON
  → IN_PROGRESS → REVIEWING → COMPLETED
                 → LOST / CANCELLED (终点)
```

## 人工门控

- L0 (<¥100): 自动放行
- L1 (¥100-500): 发飞书通知 + 自动继续
- L2 (>¥500): 必须飞书确认 → 创始人决策

## 支付方式

- wechat (微信支付)
- alipay (支付宝)
- bank_transfer (银行转账)
- crypto_usdt (USDT TRC20)
- crypto_eth (ETH)
- crypto_btc (BTC)

## 数据存储

- 订单: `~/.hermes/orders/`
- 发票: `~/.molin/orders/invoices/`
- 支付: `~/.molin/orders/payments/`
- PocketBase (可选): `~/.molin/pocketbase/`
