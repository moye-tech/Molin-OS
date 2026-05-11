---
name: molin-open-design
description: Molin-OS Open Design 全栈设计工程集成 — 149设计系统×134技能，CLI/Worker/SmartDispatcher 三通道接入
triggers:
  - "Open Design"
  - "open-design"
  - "墨图设计 v2.2"
  - "design web"
  - "全栈网页设计"
  - "landing page 生成"
  - "dashboard 仪表盘"
  - "PPT 生成"
  - "设计网页"
  - "od daemon"
---

# Molin-OS × Open Design 集成

> **状态**: ✅ 已部署 · **版本**: v2.2 · **引擎**: Open Design v0.6.0

## 架构概览

```
用户自然语言 → SmartDispatcher (COLLAB_RULES 14条路由)
                    │
                    ▼
           HandoffManager.route("designer")
                    │
                    ▼
        Designer._web_design()  ←─ designer.py v2.2
          ├── GET  /api/skills/{id}           → 134 技能规范
          ├── GET  /api/design-systems/{id}   → 149 设计系统
          ├── LLM 生成 HTML                   → DeepSeek V4
          ├── POST /api/artifacts/save        → daemon 预览
          └── 💾 ~/Molin-OS/output/designs/   → 本地 HTML
```

## 环境依赖

| 组件 | 状态 | 位置 |
|:--|:--|:--|
| Open Design daemon | ✅ 运行中 | `http://127.0.0.1:55888` |
| 源码仓库 | ✅ | `~/Projects/open-design` |
| Daemon 启动命令 | | `cd ~/Projects/open-design && pnpm tools-dev start daemon` |
| pnpm 版本 | 10.33.2 (Corepack) | `corepack pnpm@10.33.2` |
| 内存占用 | ~161MB RSS | |

**启动 daemon (如果挂了):**
```bash
cd ~/Projects/open-design && pnpm tools-dev start daemon
```

**检查状态:**
```bash
curl -s http://127.0.0.1:55888/api/health
# → {"ok":true,"version":"0.6.0"}
```

## CLI 命令

### 全栈网页生成
```bash
# SaaS 落地页 (Apple 设计系统)
python -m molib design web --prompt="墨麟AI集团官网" --action=landing_page --ds=apple

# 数据仪表盘 (Stripe 设计系统)
python -m molib design web --prompt="销售数据看板" --action=dashboard --ds=stripe

# 投资人 PPT (Airbnb 设计系统)
python -m molib design web --prompt="融资计划书" --action=pitch_deck --ds=airbnb

# 自定义 skill + 设计系统
python -m molib design web --prompt="..." --action=web_design --skill=docs-page --ds=apple
```

### AI 生图
```bash
python -m molib design image --prompt="一只猫" --style=插画
```

## 支持的 Action → Skill 映射

| action | skill ID | 说明 |
|:--|:--|:--|
| `landing_page` | `saas-landing` | SaaS 落地页 |
| `dashboard` | `dashboard` | 数据分析仪表盘 |
| `pitch_deck` | `html-ppt-pitch-deck` | 投资人 Pitch Deck |
| `blog_post` | `blog-post` | 博客文章页 |
| `pricing_page` | `pricing-page` | 定价方案页 |
| `mobile_app` | `mobile-app` | 移动端原型 |
| `web_prototype` | `web-prototype` | 通用网页原型 |
| `docs_page` | `docs-page` | 文档/知识库页 |
| `waitlist` | `waitlist-page` | 预发布等待页 |
| `login_flow` | `login-flow` | 登录/认证流程 |
| `weekly_report` | `weekly-update` | 周报 |
| `finance_report` | `finance-report` | 财务报表 |
| `kami_landing` | `kami-landing` | 日式简约落地页 |
| `open_design_landing` | `open-design-landing` | Open Design 品牌落地页 |
| `ppt` | `html-ppt-pitch-deck` | PPT (同 pitch_deck) |

## SmartDispatcher 路由规则

触发词 → Worker 链：

| 触发词 | Worker 链 | 说明 |
|:--|:--|:--|
| "落地页", "landing" | `[designer]` | 单 Worker 直出 |
| "仪表盘", "dashboard" | `[designer, data_analyst]` | 设计+数据 |
| "PPT", "pitch" | `[designer, content_writer]` | 设计+文案 |
| "网页设计", "设计网页", "web设计" | `[designer]` | 单 Worker |
| "UI设计" | `[designer]` | |
| "原型" | `[designer]` | |
| "品牌视觉" | `[designer, ip_manager]` | 设计+品牌 |
| "定价页" | `[designer, bd]` | 设计+商务 |
| "文档页" | `[designer, knowledge]` | 设计+知识 |
| "博客" | `[content_writer, designer]` | 文案+设计 |
| "营销文案" | `[research, content_writer, designer]` | 三 Worker 协作 |

## Python API

```python
from molib.agencies.workers.designer import Designer
from molib.agencies.workers.base import Task

designer = Designer()

# 生成落地页
task = Task(
    task_id="my-landing",
    task_type="design",
    payload={
        "action": "landing_page",
        "prompt": "墨麟AI集团 — 22家AI子公司",
        "design_system": "apple",
    }
)
result = await designer.execute(task)
# result.output → {preview_url, local_path, html_size, skill, ...}
```

## 设计系统 Top 10

| ID | 风格 | 适用场景 |
|:--|:--|:--|
| `apple` | 极简白+SF Pro | 科技/SaaS 落地页 |
| `stripe` | 深蓝+渐变 | 金融/支付仪表盘 |
| `airbnb` | 暖色+Cereal | 社区/平台型产品 |
| `ant` | 蓝白+企业级 | 后台/中台系统 |
| `arc` | 暗色+霓虹 | 开发者工具 |
| `bento` | 网格卡片 | 产品展示 |
| `agentic` | AI 原生 | AI Agent 产品 |
| `notion` | 极简黑白 | 文档/知识库 |
| `linear` | 暗色+紫 | 项目管理工具 |
| `vercel` | 黑+几何 | 开发者平台 |

## 故障排查

### Daemon 挂了
```bash
# 检查
curl http://127.0.0.1:55888/api/health

# 重启
cd ~/Projects/open-design && pnpm tools-dev start daemon
```

### pnpm 版本问题
```bash
# 用 corepack 锁定版本
cd ~/Projects/open-design && corepack pnpm@10.33.2 install

# 或直接用系统 pnpm (忽略版本检查)
cd ~/Projects/open-design && pnpm tools-dev start daemon
```

### "技能不可用"
- 确认 daemon 运行中: `curl http://127.0.0.1:55888/api/health`
- 确认技能存在: `curl http://127.0.0.1:55888/api/skills | python3 -c "import sys,json;[print(s['id']) for s in json.load(sys.stdin)['skills']]"`

### LLM 生成超时
- 缩短 prompt
- 使用更快的 model (deepseek-v4-flash)
- 检查网络连接

## 输出位置

| 类型 | 路径 |
|:--|:--|
| Daemon 预览 | `http://127.0.0.1:55888/artifacts/{timestamp}-{slug}/index.html` |
| 本地 HTML | `~/Molin-OS/output/designs/od_{title}_{uuid}.html` |
| Daemon 日志 | `~/Projects/open-design/.tmp/tools-dev/default/logs/daemon/latest.log` |
