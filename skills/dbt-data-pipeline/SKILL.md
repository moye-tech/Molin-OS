---
name: dbt-data-pipeline
description: dbt-core (14K⭐) 数据管线工具 — 用 SQL 定义数据转换逻辑，支持增量更新、测试和文档生成
version: 0.1.0
tags:
- data
- pipeline
- analytics
- sql
- transformation
- dbt
metadata:
  hermes:
    molin_owner: 墨测数据
    source: https://github.com/dbt-labs/dbt-core
    stars: 14000
    pip_package: dbt-core
min_hermes_version: 0.13.0
---

# dbt-core — 数据管线工具

## 概述

dbt-core（data build tool，14K⭐）是一个数据转换工具，让数据分析师和工程师用 SQL 定义数据转换逻辑。dbt 负责编排、执行、测试和文档化这些转换。

- **GitHub**: https://github.com/dbt-labs/dbt-core
- **物主**: 墨测数据（data_analyst.py Worker）
- **依赖**: Python 3.8+、pip

## 安装

```bash
# 安装核心包
pip install dbt-core

# 安装数据库适配器（按需选择）
pip install dbt-postgres      # PostgreSQL
pip install dbt-bigquery      # Google BigQuery
pip install dbt-snowflake     # Snowflake
pip install dbt-redshift      # Amazon Redshift
pip install dbt-duckdb        # DuckDB（本地分析首选）
pip install dbt-sqlite        # SQLite
```

## 项目初始化

```bash
# 创建新项目
dbt init my_project
cd my_project

# 项目结构
my_project/
├── models/          # SQL 模型文件
│   ├── staging/     # 原始数据层
│   ├── intermediate/ # 中间转换层
│   └── marts/       # 业务聚合层
├── tests/           # 数据测试
├── analyses/        # 临时分析
├── snapshots/       # 缓慢变化维度
├── macros/          # Jinja 宏
├── seeds/           # CSV 种子数据
├── dbt_project.yml  # 项目配置
└── profiles.yml     # 数据库连接配置
```

## 基础数据建模

### 模型分层

```
Staging（原始） → Intermediate（中间） → Marts（业务）
    │                   │                    │
    ▼                   ▼                    ▼
  源表清洗          业务逻辑转换         聚合指标
```

### Staging 模型（原始数据层）

```sql
-- models/staging/stg_orders.sql
SELECT
    id AS order_id,
    user_id,
    amount,
    status,
    created_at::date AS order_date
FROM {{ source('shop', 'orders') }}
WHERE status != 'deleted'
```

### Marts 模型（业务聚合层）

```sql
-- models/marts/daily_revenue.sql
SELECT
    order_date,
    COUNT(DISTINCT user_id) AS paying_users,
    SUM(amount) AS total_revenue,
    SUM(amount) / COUNT(DISTINCT user_id) AS avg_order_value
FROM {{ ref('stg_orders') }}
WHERE status = 'completed'
GROUP BY order_date
```

### 数据源声明

```yaml
# models/sources.yml
version: 2

sources:
  - name: shop
    database: production
    schema: public
    tables:
      - name: orders
        description: 订单主表
      - name: users
        description: 用户表
```

## 数据测试

```yaml
# tests/schema.yml
version: 2

models:
  - name: stg_orders
    columns:
      - name: order_id
        tests:
          - unique
          - not_null
      - name: amount
        tests:
          - not_null
          - dbt_utils.accepted_range:
              min_value: 0
              max_value: 1000000

  - name: daily_revenue
    tests:
      - dbt_utils.expression_is_true:
          expression: "total_revenue >= 0"
```

### 运行测试

```bash
# 运行所有测试
dbt test

# 运行特定模型测试
dbt test --select daily_revenue
```

## 增量更新策略

```sql
-- models/marts/daily_metrics.sql
{{ config(
    materialized='incremental',
    unique_key='order_date',
    incremental_strategy='merge',
    on_schema_change='fail'
) }}

SELECT
    order_date,
    SUM(amount) AS total_revenue,
    COUNT(DISTINCT user_id) AS active_users
FROM {{ ref('stg_orders') }}

{% if is_incremental() %}
WHERE order_date >= (SELECT MAX(order_date) FROM {{ this }})
{% endif %}

GROUP BY order_date
```

### 增量策略对比

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| `append` | 追加新数据 | 日志/事件数据 |
| `merge` | 根据 unique_key 合并 | 维度表/可更新数据 |
| `insert_overwrite` | 替换分区数据 | 大数据量表（BigQuery） |
| `delete+insert` | 删除后插入 | Snowflake |

## 常用命令

```bash
# 运行所有模型
dbt build

# 运行特定模型
dbt run --select daily_revenue

# 运行模型及其依赖
dbt run --select stg_orders+

# 生成文档
dbt docs generate
dbt docs serve  # 启动文档服务器 http://localhost:8080

# 数据测试
dbt test

# 编译 SQL（不执行）
dbt compile

# 查看 DAG
dbt ls --select +daily_revenue+
```

## 接入墨测数据

墨测数据（data_analyst.py Worker）可通过 dbt 进行数据分析管线管理：

```python
# 通过 molib CLI 调用 dbt
import subprocess

def run_dbt_model(model_name: str) -> dict:
    """运行 dbt 模型并返回结果"""
    result = subprocess.run(
        ["dbt", "run", "--select", model_name],
        cwd="/home/ubuntu/hermes-os/data/dbt_project",
        capture_output=True, text=True
    )
    return {
        "model": model_name,
        "success": result.returncode == 0,
        "output": result.stdout,
        "error": result.stderr if result.returncode != 0 else None,
    }

# 墨测数据 CLI
python -m molib data analyze --query "dbt run --select daily_revenue"
python -m molib data analyze --query "dbt test"
```

## 前置条件

- Python 3.8+ 和 pip
- 目标数据库连接（PostgreSQL/BigQuery/Snowflake/DuckDB 等）
- `profiles.yml` 数据库连接配置
- dbt 项目已初始化

## 注意事项

- dbt 不处理数据加载（EL），只处理转换（T）—— 需要先通过其他工具加载数据
- 增量模型第一次运行等于全量刷新
- 测试失败不会阻断模型运行，但建议在 CI/CD 中先测试后部署
- 文档自动从模型 SQL 中的注释和 schema.yml 生成