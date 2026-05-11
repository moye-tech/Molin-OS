# Node.js Daemon Bridge — Open Design 部署手册

> 2026-05-11 — Open Design v0.6.0 daemon 部署 + Molin-OS Worker 集成验证

## 启动命令

```bash
# 1. 克隆
git clone https://github.com/nexu-io/open-design.git ~/Projects/open-design

# 2. 安装依赖 (直连, 不用代理)
cd ~/Projects/open-design
corepack pnpm@10.33.2 install    # 861 packages, ~3m36s

# 3. 启动 daemon
pnpm tools-dev start daemon       # → http://127.0.0.1:55888, ~161MB RSS

# 4. 验证
curl http://127.0.0.1:55888/api/health
# → {"ok":true,"version":"0.6.0"}
```

## API 端点目录

| Method | Path | 用途 | 响应 |
|--------|------|------|------|
| GET | `/api/health` | 健康检查 | `{"ok":true,"version":"0.6.0"}` |
| GET | `/api/skills` | 技能列表 | `{"skills":[{id,name,description,triggers,...}]}` — 134个内置 |
| GET | `/api/skills/:id` | 技能详情 | `{id,name,description,body,systemPrompt,craftRequires,...}` |
| GET | `/api/design-systems` | 设计系统列表 | `{"designSystems":[{id,...}]}` — 149个系统 |
| GET | `/api/design-systems/:id` | 设计系统详情 | `{id,body}` — body 为 DESIGN.md 全文 (15-30KB) |
| GET | `/api/design-systems/:id/preview` | 设计系统预览 | HTML |
| POST | `/api/artifacts/save` | 保存制品 | `{identifier,title,html}` → `{path,url,lint}` |
| POST | `/api/artifacts/lint` | 独立 lint | `{html}` → `{findings,agentMessage}` |
| GET | `/api/agents` | 检测的 Agent | `{agents:[{id,name,available},...]}` — 16种 |
| GET | `/api/active` | 当前活跃 Agent | `{active:bool}` |
| POST | `/api/projects` | 创建项目 | `{id,name,skillId,designSystemId,pendingPrompt}` |
| GET | `/api/templates` | 模板列表 | `{templates:[]}` |

## 可用技能 (部分常用)

| skill ID | 类别 | 触发词 |
|----------|------|--------|
| `saas-landing` | web | saas landing, marketing page, product landing |
| `dashboard` | web | admin dashboard, analytics dashboard |
| `blog-post` | web | blog post, article, long-form |
| `pricing-page` | web | pricing page, plan tiers |
| `html-ppt-pitch-deck` | ppt | pitch deck, investor deck, 10-slide |
| `html-ppt-weekly-report` | ppt | weekly report, status update |
| `html-ppt-product-launch` | ppt | product launch, keynote |
| `open-design-landing` | web | world-class landing, editorial landing |
| `kami-landing` | web | 紙 (kami) print-grade document |
| `mobile-app` | mobile | mobile app screen, iPhone prototype |
| `mobile-onboarding` | mobile | onboarding flow, 3-screen |
| `web-prototype` | web | desktop web prototype, general purpose |
| `waitlist-page` | web | pre-launch landing, email capture |
| `docs-page` | web | documentation page, API reference |
| `finance-report` | report | quarterly report, financial report |
| `team-okrs` | report | OKR tracker, quarterly objectives |

## 可用设计系统 (部分)

| ID | 风格 | Body大小 |
|----|------|----------|
| `apple` | Premium white space, SF Pro, cinematic | 17,764 chars |
| `stripe` | Gradient-heavy, developer-focused | 20,552 chars |
| `airbnb` | Warm, human-centric, illustration-heavy | — |
| `arc` | Browser-native, colorful, playful | — |
| `ant` | Enterprise design system, table-heavy | — |
| `bento` | Grid-based, Apple-inspired card layout | — |
| `linear` | Dark, minimal, task-oriented | — |
| `notion` | Clean, block-based, monochrome | — |
| `vercel` | Dark, geometric, developer-first | — |

## 集成架构

```
Molin-OS designer.py Worker
  └─ action=landing_page → skill=saas-landing + ds=apple
       ├─ GET /api/skills/saas-landing     → skill定义 (body: 3,954 chars)
       ├─ GET /api/design-systems/apple    → DESIGN.md (body: 17,764 chars)
       ├─ LLM (DeepSeek)                   → 生成 HTML (遵循skill规范+DS tokens)
       ├─ re.extract(```html...```)        → 提取代码块
       └─ POST /api/artifacts/save         → {url: "/artifacts/.../index.html"}
            └─ 本地存档 ~/Molin-OS/output/designs/od_*.html
```

## 集成测试结果

```python
# 测试: landing_page + apple design system
task = Task(payload={
    'action': 'landing_page',
    'prompt': '墨麟AI集团 — 22家AI子公司为企业提供全栈AI服务',
    'design_system': 'apple',
})

# 结果
{
    "status": "success",
    "engine": "Open Design v0.6.0",
    "skill": "saas-landing",
    "design_system": "apple",
    "html_size": 13025,  # 13KB 单文件 HTML
    "preview_url": "http://127.0.0.1:55888/artifacts/.../index.html",
    "lint": []            # 无P0问题
}
```

## 陷阱与修复

### 陷阱1: corepack enable 权限拒绝
```
Internal Error: EACCES: permission denied, symlink → /usr/local/bin/pnpm
```
**修复:** 不用 `corepack enable`，直接用 `corepack pnpm@10.33.2 install`

### 陷阱2: pnpm tools-dev 版本检查拒绝 corepack
```
[ERROR] This project is configured to use 10.33.2 of pnpm. Your current pnpm is v11.0.9
```
**修复:** 用系统 pnpm 11.0.9 直接调 `pnpm tools-dev start daemon`，系统 pnpm 自动处理版本切换

### 陷阱3: --pm-on-fail=ignore 被 tools-dev 误解析
```
Unknown option `--pmOnFail`
```
**原因:** `--pm-on-fail=ignore` 被 pnpm exec 层消费后，剩余参数传给 tools-dev。用系统 pnpm 直调即可避免。

### 陷阱4: pnpm install 通过代理超时
```
(通过 Clash 代理) pnpm install → 超 2 分钟未完成
```
**修复:** 关闭代理直连。检查 `env | grep -i proxy` 确认无代理变量。

## LLM Prompt 构建模式

```python
def _build_design_system_prompt(skill_def, ds_body, ds_id):
    """注入设计系统+技能规范的系统提示词"""
    lines = [
        "你是墨图设计——专业视觉设计子公司。",
        f"## 当前技能: {skill_def['name']}",
        f"{skill_def['description']}",
    ]
    if ds_body:
        lines.append(f"## 设计系统: {ds_id}")
        lines.append(ds_body[:4000])  # 截断避免token超限
    if skill_def.get('body'):
        lines.append("## 技能规范")
        lines.append(skill_def['body'][:3000])
    lines.append("## 输出规则")
    lines.append("- 单文件 HTML，内联所有 CSS")
    lines.append("- 系统字体栈，无 CDN")
    lines.append("- ```html ... ``` 代码块")
    return "\n".join(lines)
```

## Skill 管理

Open Design 技能存放在 `~/Projects/open-design/skills/` 目录，每个技能一个子目录：
```
skills/saas-landing/
  SKILL.md       # 技能定义 (YAML frontmatter + body)
```

设计系统存放在 `~/Projects/open-design/design-systems/`：
```
design-systems/apple/
  DESIGN.md      # Apple 设计规范
```

内置技能: 134个 | 内置设计系统: 149个 | 社区模板可通过 `/api/codex-pets/sync` 同步
