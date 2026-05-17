# Agent Registry

> 索引文件 · 所有 Agent 的 SOP 定义见 SYSTEM.md

| AgentID | 名称 | 职责 | 调度 |
|---------|------|------|------|
| content | 墨笔文创 | 内容矩阵生产 | `30 8 * * 1-5` |
| design | 墨图设计 | 视觉设计 | 接内容生产后 |
| video | 墨播短视频 | 短视频 | 接内容生产后 |
| voice | 墨声配音 | 语音合成 | 跟随 video/edu |
| ip | 墨韵IP | 品牌管理 | `0 10 * * 1` |
| crm | 墨域私域 | CRM运营 | `0 9 * * 3` |
| service | 墨声客服 | 客服 | `*/15 * * * *` |
| ecommerce | 墨链电商 | 订单管理 | `0 21 * * *` |
| edu | 墨学教育 | 教育课程 | 按需 |
| developer | 墨码开发 | 软件开发 | 按需 |
| ops | 墨维运维 | 运维 | `*/30 * * * *` |
| security | 墨安安全 | 安全审计 | `0 3 * * 1` |
| autodream | 墨梦AutoDream | 进化引擎 | `0 7 * * 1` / `0 21 * * 0` |
| finance | 墨算财务 | 财务分析 | `0 23 * * *` |
| bd | 墨商BD | 商务拓展 | `0 8 * * *` |
| global | 墨海出海 | 出海本地化 | 接内容后 |
| research | 墨研竞情 | 情报竞品 | `0 6 * * *` |
| legal | 墨律法务 | 法务合规 | 按需 |
| data | 墨测数据 | 数据分析 | `0 22 * * *` |
| knowledge | 墨脑知识 | 知识管理 | 自动 |
| gatekeeper | Gatekeeper | 合规门禁 | 嵌入所有输出 |
| kpi-tracker | KPI Tracker | 指标采集 | 嵌入 22:00 |

总计: 22 Agent · 13 定时调度
