---
name: molin-xiaohongshu
description: '墨影 · 小红书AI发布引擎 — 智能内容创作、AI驱动封面生成、热点采集、定时发布、多账户管理。基于 BetaStreetOmnis/xhs_ai_publisher
  ⭐1.9k。Use when: 用户需要发布小红书笔记、采集热点、生成封面图片、管理多个账号。'
version: 1.0.0
author: Hermes Agent + xhs_ai_publisher
license: MIT
metadata:
  hermes:
    tags:
    - xiaohongshu
    - social-media
    - content-publishing
    - ai-content
    - image-generation
    - automation
    - molin
    related_skills:
    - molin-wechat
    - content-creation
    - seo-content-optimizer
    - image-generation
    molin_owner: 墨影（IP孵化）
min_hermes_version: 0.13.0
---

# 墨影 · 小红书AI发布引擎

## 概述

墨影基于 **xhs_ai_publisher**（BetaStreetOmnis/xhs_ai_publisher ⭐1.9k），提供从内容创作、封面生成、热点采集到定时发布、多账户管理的一站式小红书发布解决方案。适用于个人博主、品牌运营、IP孵化等场景。

### 核心工作流

```
热点采集 → AI内容生成 → 封面/配图制作 → 定时发布 → 多账号矩阵管理
```

---

## 何时使用

- 用户说："帮我写一篇小红书笔记"、"生成一个封面图"
- 用户说："采集今天的微博/百度热点"、"有什么热门话题"
- 用户说："定时发布这篇笔记"、"帮我管理多个小红书账号"
- 用户说："从公众号链接导入内容"、"用AI生成标题和标签"
- 用户说："配置OpenAI/Claude来写文章"

---

## 安装

### 环境要求

- Python 3.8+
- PyQt5（GUI依赖）
- 操作系统: Windows / macOS / Linux

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/BetaStreetOmnis/xhs_ai_publisher.git
cd xhs_ai_publisher

# 运行安装脚本（自动安装依赖 + 初始化配置）
chmod +x install.sh
./install.sh

# 或手动安装
pip install -r requirements.txt
```

### 数据目录

```
~/.xhs_system/           # 系统数据目录
├── config.json          # 全局配置（含AI API Key等）
├── accounts/            # 多账户 Cookie 文件
├── drafts/              # 草稿笔记
├── templates/           # 封面模板
├── published/           # 已发布记录
└── logs/                # 操作日志
```

> **安全提示**: API Key 和 Cookie 以加密方式存储在本地 `~/.xhs_system/`，不会上传到任何远程服务器。

---

## 快速开始

### 1. 启动应用

```bash
python main.py
```

启动后出现 PyQt5 GUI 主界面，包含以下功能面板。

### 2. 添加小红书账号

**方式一：扫码登录**
- 在「账号管理」面板点击「添加账号」
- 使用小红书 App 扫描二维码
- Cookie 自动保存到 `~/.xhs_system/accounts/`

**方式二：手动导入 Cookie**
- 从浏览器开发者工具复制 Cookie（格式: `a1=xxx; webId=xxx; ...`）
- 在「账号管理」粘贴并保存

### 3. 配置AI引擎

在「设置」→「AI配置」中：

| 提供商 | API地址 | 模型 | 说明 |
|:------:|:--------:|:----:|:----:|
| OpenAI | `https://api.openai.com/v1` | gpt-4 / gpt-3.5-turbo | 官方或代理 |
| Claude | `https://api.anthropic.com` | claude-3-opus / claude-3-sonnet | Anthropic |
| Ollama | `http://localhost:11434` | llama3 / qwen / 其他本地模型 | 本地部署,免费 |

配置示例（OpenAI）:
```json
{
  "ai_provider": "openai",
  "api_key": "sk-xxxxxxxxxxxxxxxxxxxx",
  "api_base": "https://api.openai.com/v1",
  "model": "gpt-4",
  "temperature": 0.8
}
```

---

## 核心功能

### 1. AI智能生成内容

在「AI创作」面板：

**标题生成**
```
输入主题/关键词 → AI生成10个备选标题 → 选择/编辑
```

**正文生成**
```
输入大纲/要点 → AI生成正文（支持小红书风格） → 手动润色
```

**标签推荐**
```
AI分析正文内容 → 推荐热门标签（#xxx格式） → 一键添加
```

**支持风格定制**:
- 语气: 亲切/专业/趣味/文艺
- 长度: 短(100-200字)/中(300-500字)/长(800+字)
- 类型: 种草/测评/教程/Vlog/攻略

### 2. 封面/内容图模板

在「封面制作」面板，内置多种模板：

| 模板类型 | 适用场景 | 尺寸 |
|:--------:|:--------:|:----:|
| 营销海报 | 促销/活动通知 | 1080×1440 |
| 促销横幅 | 限时优惠/折扣 | 1080×600 |
| 产品展示 | 好物推荐/开箱 | 1080×1080 |
| 图文教程 | 步骤/攻略 | 1080×1440 |
| 个人分享 | 日常/Vlog | 1080×1440 |
| 知识卡片 | 知识科普/书单 | 1080×1440 |

**操作流程**:
1. 选择模板 → 2. 编辑文字/颜色/图片 → 3. AI优化排版 → 4. 导出/直接使用

**AI封面增强**:
- AI智能构图：自动优化布局和视觉重心
- AI配色建议：根据内容主题推荐配色方案
- AI文字排版：自动调整字体大小和行距

### 3. 热点采集

在「热点」面板，支持多个数据源：

```bash
# 采集微博热搜
# 采集百度热点
# 采集头条热榜
# 采集B站热门
```

**采集配置**:
```json
{
  "hot_sources": ["weibo", "baidu", "toutiao", "bilibili"],
  "auto_refresh_interval": 30,    # 自动刷新间隔(分钟)
  "max_hot_items": 50,            # 每源最多采集条数
  "keyword_filter": ["小红书", "穿搭", "美妆"],  # 关键词过滤
  "ai_analysis": true             # AI分析热点关联性
}
```

**热门话题分析**:
- AI自动分析热点与账号定位的匹配度
- 生成热点选题建议（含标题、角度、标签）
- 热门话题趋势图

### 4. 笔记发布

在「发布」面板：

**发布流程**:
1. 编辑标题（最多20字）
2. 编辑正文（支持富文本、emoji、话题标签）
3. 选择/生成封面图片（最多9张）
4. 设置发布方式 → 立即发布 或 定时发布

**定时发布（无人值守）**:
```json
{
  "scheduled_posts": [
    {
      "account": "账号1",
      "content_id": "draft_001",
      "publish_time": "2026-05-05 10:00:00",
      "status": "pending"
    }
  ]
}
```

- 支持指定精确时间（精确到分钟）
- 支持队列管理（多篇笔记排序发布）
- 系统自动在指定时间发布，无需人工值守

### 5. 多账户管理

**功能**:
- 添加/删除/切换账号
- 每个账号独立Cookie和配置
- 批量发布（选择多个账号同时发布相同内容）
- 账号分组（如：穿搭号、美食号、生活号）
- 发布记录（每个账号的历史发布）

**管理面板**:
```
账号列表:
├── 穿搭小能手 (穿搭号)  ← 在线
│   ├── 已发布: 128篇
│   ├── 粉丝: 15.2k
│   └── 最后发布: 2026-05-03
├── 美食探险家 (美食号)  ← 离线(Cookie过期)
│   ├── 已发布: 67篇
│   ├── 粉丝: 8.7k
│   └── 最后发布: 2026-04-20
└── 生活碎片集 (生活号)  ← 在线
    ├── 已发布: 203篇
    ├── 粉丝: 22.1k
    └── 最后发布: 2026-05-04
```

### 6. 网页链接导入

支持从外部链接导入内容并自动转换为小红书笔记格式：

**导入来源**:
- **公众号文章**: 粘贴公众号链接 → 自动抓取正文/图片 → AI重写为小红书风格
- **通用网页**: 任意网页链接 → 提取正文 → AI摘要 + 重新排版

**导入流程**:
```
粘贴链接 → 抓取内容 → AI摘要 → 选择图片 → 生成笔记草稿 → 编辑发布
```

### 7. AI配置

| 设置项 | 说明 | 推荐值 |
|:------:|:----:|:------:|
| `provider` | AI提供商 | openai / claude / ollama |
| `api_key` | API密钥 | 本地加密存储 |
| `api_base` | API端点地址 | 各提供商默认地址 |
| `model` | 模型名称 | gpt-4 / claude-3-sonnet / llama3 |
| `temperature` | 创造力(0~2) | 0.7~0.9 |
| `max_tokens` | 最大输出长度 | 2048~4096 |
| `system_prompt` | 系统提示词 | 自定义小红书风格指令 |

---

## 数据安全

### 加密存储

所有敏感信息本地加密：

| 数据类型 | 加密方式 | 存储位置 |
|:--------:|:--------:|:--------:|
| API Key | AES-256-GCM | `~/.xhs_system/config.json` |
| 账号Cookie | AES-256-GCM | `~/.xhs_system/accounts/*.enc` |
| 本地配置 | JSON明文 | `~/.xhs_system/config.json` |

### 安全建议

1. **定期更新Cookie**: 小红书Cookie通常7~30天过期
2. **不要分享 `~/.xhs_system/`**: 该目录包含账号凭据
3. **使用本地AI（Ollama）**: 如需最高安全性，推荐使用本地模型
4. **API Key权限最小化**: 只赋予内容生成等必要权限

---

## 配置详解

### 全局配置 (`~/.xhs_system/config.json`)

```json
{
  "ai": {
    "provider": "openai",
    "api_key": "encrypted:xxx",
    "api_base": "https://api.openai.com/v1",
    "model": "gpt-4",
    "temperature": 0.8,
    "max_tokens": 2048,
    "system_prompt": "你是一个小红书内容创作助手..."
  },
  "publisher": {
    "default_interval": 180,
    "max_images": 9,
    "image_quality": 0.9
  },
  "hot_trends": {
    "sources": ["weibo", "baidu", "toutiao", "bilibili"],
    "auto_refresh": 30,
    "max_items": 50
  },
  "scheduler": {
    "enabled": true,
    "check_interval": 60
  }
}
```

### 账号Cookie格式

```
a1=xxx; webId=xxx; web_session=xxx; ...
```

> 获取方式：登录小红书网页版 → F12开发者工具 → Application → Cookies → 复制所有Cookie值

---

## 常见问题

### 1. 登录后提示"Cookie过期"
- 原因：小红书Cookie有有效期（通常7~30天）
- 解决：重新扫码登录或更新Cookie

### 2. 发布失败（图片上传失败）
- 检查图片格式（支持 JPG/PNG/WebP）
- 检查图片大小（单张不超过20MB）
- 检查网络连接

### 3. AI生成内容质量不佳
- 调整 `temperature` 值（降低使内容更保守）
- 自定义 `system_prompt` 提供更详细的写作指导
- 增加输入信息量（提供更多背景/要点）

### 4. 定时发布未触发
- 检查系统时间是否正确
- 检查定时任务进程是否在运行
- 检查 `check_interval` 配置（默认每60秒检查一次）

### 5. 多账号切换不生效
- 确认所有账号Cookie均有效
- 重启应用后重试
- 检查单个账号是否被小红书限流

---

## 验证清单

- [ ] 应用已安装并可启动 (`python main.py`)
- [ ] 至少一个小红书账号已添加（Cookie有效）
- [ ] AI配置已完成（至少配置一个提供商）
- [ ] 能成功生成一篇测试笔记（AI内容）
- [ ] 封面图模板可正常打开和编辑
- [ ] 热点采集功能可正常获取数据
- [ ] 定时发布功能可正常设置
- [ ] 数据目录 `~/.xhs_system/` 已创建

---

## 参考

- GitHub: https://github.com/BetaStreetOmnis/xhs_ai_publisher
- 小红书开放平台: https://open.xiaohongshu.com/
- PyQt5 文档: https://www.riverbankcomputing.com/static/Docs/PyQt5/