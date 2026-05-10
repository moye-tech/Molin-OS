---
name: molin-vizro
description: '墨数 · BI仪表盘引擎 — 低代码数据可视化仪表盘，基于 McKinsey Vizro ⭐3.7k。Use when: 用户需要从数据创建可视化仪表盘、BI报告、数据分析看板、多指标KPI展示。兼容plotly/dash/pydantic生态。'
version: 1.0.0
author: Hermes Agent + Vizro
license: Apache-2.0
metadata:
  hermes:
    tags:
    - vizro
    - dashboard
    - bi
    - plotly
    - dash
    - data-visualization
    - analytics
    - kpi
    - molin
    related_skills:
    - data-science
    - analysis-tools
    - research
    - reporting
    - plotly-dash
    molin_owner: 墨数（BI仪表盘）
min_hermes_version: 0.13.0
---

# 墨数 · BI仪表盘引擎

## 概述

**墨数** 基于 **McKinsey Vizro** (github.com/mckinsey/vizro ⭐3.7k) — 低代码 Python 数据可视化仪表盘框架，兼容 Plotly / Dash / Pydantic 生态。通过声明式 Python API 即可构建企业级 BI 看板。

### 核心工作流

```
数据准备 → 定义 Page 结构 → 添加组件(Graph/Table/KPI/Filter) → 构建 Dashboard → 运行
```

---

## 何时使用

- 用户说："帮我做一个销售数据看板"、"展示 KPI 指标"
- 用户说："从 CSV 创建可视化仪表盘"、"数据分析仪表盘"
- 用户说："多页面 BI 报告"、"实时数据监控看板"
- 用户说："用 Plotly 画图展示在这个看板上"
- 用户说："我想筛选数据、下钻分析"

---

## 环境准备

```bash
# 安装核心库
pip install vizro

# 安装 MCP 服务（AI 辅助构建）
pip install vizro-mcp

# 验证安装
python -c "import vizro; print(vizro.__version__)"
```

---

## 快速开始

### 1. 最小示例 — 单页仪表盘

```python
import vizro.plotly.express as px
import vizro.models as vm
from vizro import Vizro

# 加载数据
df = px.data.iris()

# 定义页面
page = vm.Page(
    title="鸢尾花数据分析",
    components=[
        vm.Graph(
            id="scatter",
            figure=px.scatter(df, x="sepal_length", y="sepal_width",
                              color="species", title="花萼散点图"),
        ),
    ],
)

# 构建并运行
dashboard = vm.Dashboard(pages=[page])
Vizro().build(dashboard).run()
```

### 2. 添加 KPI 指标

```python
page = vm.Page(
    title="KPI 看板",
    components=[
        vm.Graph(id="hist", figure=px.histogram(df, x="sepal_length")),
        vm.Table(id="table", figure=px.data.iris()),
        vm.Card(
            text="""
            ### KPI 概览
            - **样本数**: 150
            - **特征数**: 4
            - **分类数**: 3
            """
        ),
        vm.KPI(
            id="avg_sepal_length",
            value=df["sepal_length"].mean().round(2),
            title="平均萼片长度 (cm)",
        ),
    ],
)
```

### 3. 添加筛选器与参数

```python
page = vm.Page(
    title="可筛选看板",
    components=[
        vm.Graph(
            id="scatter_filtered",
            figure=px.scatter(df, x="sepal_length", y="sepal_width",
                              color="species"),
        ),
        vm.Table(id="table_filtered", figure=df),
    ],
    controls=[
        vm.Filter(
            id="species_filter",
            column="species",       # 按 species 列筛选
            targets=["scatter_filtered", "table_filtered"],
        ),
        vm.Parameter(
            id="opacity_param",
            targets=["scatter_filtered"],
            selector=vm.RangeSlider(
                min=0, max=1, step=0.1, value=[0.3, 1.0],
            ),
            mapping="opacity",
        ),
    ],
)
```

### 4. 多页面仪表盘

```python
page1 = vm.Page(
    title="概览",
    components=[vm.Graph(id="overview", figure=...)],  # 填入实际 figure
)

page2 = vm.Page(
    title="详情",
    components=[vm.Table(id="detail", figure=...)],
)

dashboard = vm.Dashboard(pages=[page1, page2])
Vizro().build(dashboard).run()
```

---

## 组件参考

### 组件表

| 组件 | 类名 | 描述 | 必填参数 |
|:----:|:----:|:----|:---------|
| 📊 图表 | `vm.Graph` | Plotly 图表（任何 plotly figure） | `id`, `figure` |
| 📋 表格 | `vm.Table` | AG Grid 表格，支持排序/筛选 | `id`, `figure` (DataFrame) |
| 🃏 卡片 | `vm.Card` | Markdown 文本卡片 | `text` (Markdown 字符串) |
| 📈 KPI | `vm.KPI` | 关键绩效指标数字展示 | `id`, `value`, `title` |
| 🔽 筛选器 | `vm.Filter` | 筛选组件，按列过滤数据 | `column`, `targets` |
| 🎛️ 参数 | `vm.Parameter` | 控制组件参数（颜色、透明度等） | `targets`, `selector`, `mapping` |

### 筛选器类型

| 筛选器组件 | 使用方式 | 说明 |
|:----------:|:--------:|:----|
| 下拉筛选 | `vm.Filter(column="category", targets=[...])` | 按分类列筛选 |
| 数值范围筛选 | `vm.Filter(column="price", targets=[...])` | 价格范围滑块 |
| 多选筛选 | `vm.Filter(column="region", selector=vm.Select(multi=True), targets=[...])` | 多区域选择 |

### 参数控制器

| 参数组件 | 示例 | 说明 |
|:--------:|:----|:----|
| `vm.RangeSlider` | `vm.RangeSlider(min=0, max=1, value=[0.2, 0.8])` | 范围滑块 |
| `vm.Dropdown` | `vm.Dropdown(options=["a","b","c"], value="a")` | 下拉选择 |
| `vm.RadioItems` | `vm.RadioItems(options=["red","green","blue"], value="red")` | 单选按钮 |
| `vm.Checklist` | `vm.Checklist(options=["x","y"], value=["x"])` | 多选框 |
| `vm.Slider` | `vm.Slider(min=0, max=100, value=50)` | 单值滑块 |

### KPI 修饰

```python
vm.KPI(
    id="revenue_kpi",
    value=1250000,
    title="总收入 (¥)",
    icon="attach_money",              # Material icon 名称
    color="rgba(0, 200, 100, 1)",     # 颜色
    agg_func="sum",                   # 聚合函数
    prefix="¥",                       # 前缀
    suffix="",                        # 后缀
    decimal_places=0,                 # 小数位数
)
```

---

## 布局控制

### 网格布局 (Grid)

默认布局为网格，通过 `h` / `w` 控制组件大小：

```python
from vizro.models.types import ComponentType

components: list[ComponentType] = [
    vm.Graph(id="chart1", figure=..., h=4, w=6),   # 占 4行×6列
    vm.Graph(id="chart2", figure=..., h=4, w=6),   # 占 4行×6列
    vm.Table(id="table1", figure=..., h=8, w=12),  # 占 8行×12列
]
```

### Flex 布局

```python
from vizro import Vizro
from vizro.models import Dashboard, Layout

dashboard = vm.Dashboard(
    pages=[vm.Page(..., layout=vm.Layout(grid=[[0, 1], [2, 2]]))],
)
```

布局网格是一个二维列表，数字索引指向 `components` 列表中的组件。

---

## 主题

```python
# 默认暗色主题
Vizro().build(dashboard).run()

# 自定义主题
vizro_instance = Vizro()
vizro_instance.build(dashboard)
vizro_instance.run(theme="vizro_light")   # 亮色
# vizro_instance.run(theme="vizro_dark")  # 暗色
```

---

## 数据源接入

### 从 CSV

```python
import pandas as pd
import vizro.plotly.express as px

df = pd.read_csv("sales_data.csv")
page = vm.Page(
    title="销售分析",
    components=[vm.Graph(id="sales", figure=px.line(df, x="date", y="revenue"))],
)
```

### 从 SQL 数据库

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect("analytics.db")
df = pd.read_sql("SELECT * FROM monthly_sales", conn)

page = vm.Page(
    title="数据库看板",
    components=[vm.Table(id="data", figure=df)],
)
```

### 从 API

```python
import requests
import pandas as pd

resp = requests.get("https://api.example.com/metrics")
data = resp.json()
df = pd.DataFrame(data)

page = vm.Page(
    title="API 数据看板",
    components=[vm.KPI(id="live_metric", value=df["value"].iloc[-1], title="实时指标")],
)
```

---

## 实用示例

### 销售 KPI 看板

```python
import pandas as pd
import vizro.plotly.express as px
import vizro.models as vm
from vizro import Vizro

# 模拟销售数据
np.random.seed(42)
dates = pd.date_range("2025-01-01", periods=365, freq="D")
df = pd.DataFrame({
    "date": dates,
    "revenue": np.random.randint(5000, 15000, 365),
    "orders": np.random.randint(50, 200, 365),
    "category": np.random.choice(["A", "B", "C"], 365),
})

# 计算 KPI
total_revenue = df["revenue"].sum()
total_orders = df["orders"].sum()
avg_order_value = round(total_revenue / total_orders, 2)

page = vm.Page(
    title="销售仪表盘",
    components=[
        vm.Graph(
            id="revenue_trend",
            figure=px.line(df, x="date", y="revenue", title="收入趋势"),
            h=4, w=6,
        ),
        vm.Graph(
            id="orders_trend",
            figure=px.bar(df, x="date", y="orders", title="订单趋势"),
            h=4, w=6,
        ),
        vm.Graph(
            id="category_pie",
            figure=px.pie(df, names="category", title="品类分布"),
            h=4, w=6,
        ),
        vm.Graph(
            id="revenue_by_cat",
            figure=px.box(df, x="category", y="revenue", title="各品类收入分布"),
            h=4, w=6,
        ),
        vm.KPI(id="kpi_revenue", value=total_revenue, title="总收入 (¥)"),
        vm.KPI(id="kpi_orders", value=total_orders, title="总订单"),
        vm.KPI(id="kpi_avg", value=avg_order_value, title="客单价 (¥)"),
        vm.Card(text=f"""
        ### 数据摘要
        - 日期范围: {df['date'].min().date()} ~ {df['date'].max().date()}
        - 日均收入: **{df['revenue'].mean():.0f}** ¥
        - 日均订单: **{df['orders'].mean():.0f}**
        - 数据记录数: **{len(df)}**
        """),
    ],
)

dashboard = vm.Dashboard(pages=[page])
Vizro().build(dashboard).run()
```

### 多页面 + 筛选

```python
page1 = vm.Page(
    title="概览",
    components=[
        vm.Graph(
            id="overview_trend",
            figure=px.line(df, x="date", y="revenue"),
        ),
        vm.Graph(
            id="overview_bar",
            figure=px.bar(df.groupby("category")["revenue"].sum().reset_index(),
                          x="category", y="revenue"),
        ),
    ],
    controls=[vm.Filter(column="category", targets=["overview_trend"])],
)

page2 = vm.Page(
    title="详细数据",
    components=[vm.Table(id="detail_table", figure=df)],
    controls=[vm.Filter(column="category", targets=["detail_table"])],
)

dashboard = vm.Dashboard(pages=[page1, page2])
Vizro().build(dashboard).run()
```

---

## vizro-mcp (AI 辅助构建)

Vizro 提供 MCP 服务，允许 AI 助手直接生成仪表盘配置。

```bash
# 启动 MCP 服务
python -m vizro_mcp
```

MCP 服务暴露的工具：

| 工具 | 描述 |
|:----|:----|
| `create_dashboard` | 根据描述创建完整仪表盘 |
| `add_page` | 添加新页面 |
| `add_component` | 向页面添加组件 |
| `update_component` | 更新现有组件 |
| `delete_component` | 删除组件 |
| `list_pages` | 列出所有页面 |
| `get_component_details` | 查看组件详情 |

MCP 集成在支持 MCP 协议的客户端中可直接调用（如 Claude Desktop、Cursor 等）。

---

## 常见陷阱

1. **Graph 的 figure 必须是 plotly Figure 对象** — 不能传 DataFrame，需用 `px.*` 或 `go.*` 创建
2. **Table 的 figure 参数接收 DataFrame**（不是 plotly figure）— `vm.Table(figure=df)` 直接传 DataFrame
3. **Filter 必须指定 targets** — 明确哪些组件受该筛选器影响
4. **Dashboard 的 pages 参数必须是列表** — `pages=[page1, page2]` 而非 `pages=page1`
5. **KPI 的 value 要格式化** — 数字直接传入，Vizro 会渲染大号字体展示
6. **多个 KPI 并排展示** — KPI 组件自动使用 Grid 布局排布
7. **布局问题检查** — 确保 Grid 的 w/h 和总数与组件数匹配
8. **启动时端口占用** — `run(port=8051)` 指定不同端口避免冲突

---

## 验证清单

- [ ] vizro 已安装 (`python -c "import vizro; print(vizro.__version__)"`)
- [ ] 数据源已加载（CSV/SQL/API/模拟数据）
- [ ] 页面结构已定义（Page 对象）
- [ ] 组件已添加（Graph/Table/KPI/Card）
- [ ] 筛选/参数控件已配置
- [ ] 布局已调整（Grid h/w）
- [ ] Dashboard 构建通过 (`Vizro().build(dashboard)`)
- [ ] 仪表盘可正常访问 (http://localhost:8050)
- [ ] 多页面导航正常

---

## 参考

- Vizro 官方文档: https://vizro.readthedocs.io/
- GitHub: https://github.com/mckinsey/vizro
- PyPI: https://pypi.org/project/vizro/
- vizro-mcp: https://pypi.org/project/vizro-mcp/
- Plotly 图表类型: https://plotly.com/python/
- AG Grid (表格组件): https://www.ag-grid.com/
- Dash 框架: https://dash.plotly.com/
- Pydantic 验证: https://docs.pydantic.dev/