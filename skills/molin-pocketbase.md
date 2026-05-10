---
name: molin-pocketbase
description: PocketBase 统一后端 — 单 Go 二进制文件提供数据库、认证、文件存储、实时订阅
version: 1.0.0
molin_owner: 墨码开发
molin_vp: 技术
approval_level: L0
dependencies:
  - PocketBase 二进制 (v0.38.0+, darwin_arm64)
integrations:
  - PocketBase (54K⭐, GitHub: pocketbase/pocketbase)
---

# PocketBase · 墨麟统一后端

## 概述

PocketBase 是一个开源的单文件 Go 后端，提供：
- SQLite 数据库 + 实时订阅
- 用户认证 (邮箱/密码、OAuth2)
- 文件存储 (本地/S3)
- 管理面板 (Web UI)
- REST API (自动生成)

**为什么选 PocketBase？**
- 单一二进制文件 (~15MB)，零外部依赖
- 内存占用 <50MB，完美适配 Mac M2 (8GB)
- 自带管理面板，无需额外工具
- 54K GitHub Stars，活跃维护

## 安装

```bash
# CLI 一键安装
python -m molib pocketbase install

# 或手动安装
python -m molib pocketbase install v0.38.0
```

二进制位置: `/Users/moye/Molin-OS/tools/pocketbase`
数据目录: `~/.molin/pocketbase/`

## CLI 命令

```bash
# 服务管理
python -m molib pocketbase start         # 启动 (端口 8090)
python -m molib pocketbase stop          # 停止
python -m molib pocketbase restart       # 重启
python -m molib pocketbase status        # 查看状态
python -m molib pocketbase health        # 健康检查

# 一键部署
python -m molib pocketbase quick-start   # 安装+启动+初始化管理员
```

管理面板: http://127.0.0.1:8090/_/
API 端点: http://127.0.0.1:8090/api/

默认管理员:
- 邮箱: admin@molin.ai
- 密码: molin_pb_admin_2026

## Python API

```python
from molib.infra.pocketbase import (
    install, start, stop, status, quick_start, get_client
)

# 一键启动
result = quick_start()
# 返回: {"ok": True, "url": "http://127.0.0.1:8090", "admin_panel": "..."}

# 使用客户端
client = get_client()
client.superuser_login()

# 创建集合
client.collection_create("orders", [
    {"name": "title", "type": "text", "required": True},
    {"name": "amount", "type": "number", "required": True},
])

# CRUD 操作
client.record_create("orders", {"title": "项目A", "amount": 5000})
client.record_list("orders", filters="amount > 1000")
client.record_search("orders", "项目")
```

## 与墨链电商集成

PocketBase 作为墨链电商的可选统一后端：
- 订单数据 → `orders` 集合
- 发票数据 → `invoices` 集合
- 支付记录 → `payments` 集合
- 客户信息 → `customers` 集合

## 架构

```
Hermes Agent
  → molib order CLI (墨单订单)
    → OrderWorker
      → InvoiceEngine (JSON 文件存储)
      → PaymentTracker (JSON 文件存储)
      → PocketBase (可选: SQLite 统一存储)
```

选择策略: 默认使用 JSON 文件存储（零依赖），需要实时同步/Web管理时启用 PocketBase。
