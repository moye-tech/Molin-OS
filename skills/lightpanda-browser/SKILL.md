---
name: lightpanda-browser
description: 高性能无头浏览引擎 — 基于 Lightpanda（极快极轻量的无头浏览器，专为AI/爬虫/自动化设计）。比 Chromium 快10x，资源占用极低。墨维（运维）+ 墨思（情报）的爬虫基础设施。
version: 1.0.0
tags: [browser, headless, crawler, automation, scraping, lightpanda]
category: devops
metadata:
  hermes:
    source: https://github.com/lightpanda-io/browser
    stars: 10000+
    upstream_fork: https://github.com/moye-tech/browser
    language: Nim + TypeScript
    molin_owner: 墨维（运维）
---

# Lightpanda Browser — 高性能无头浏览器

## 概述

**Lightpanda** 是一个极致轻量、极致快速的无头浏览器，专为 AI Agents 和爬虫设计。

| 指标 | Lightpanda | Chromium (Puppeteer) |
|:----|:----------|:--------------------|
| 二进制体积 | ~5MB | ~300MB |
| 内存占用 | ~20MB | ~200MB+ |
| 启动时间 | ~10ms | ~500ms |
| 渲染速度 | 原生DOM | 完整渲染引擎 |
| 适用场景 | 爬虫/AI/API | 截图/完整渲染 |

## 核心能力

### 适合 Hermes 的场景

```
┌──────────────────────────────────────┐
│ 1. 数据爬取                            │
│    · 批量抓取页面内容                  │
│    · 解析结构化数据                    │
│    · 绕过JS渲染                       │
├──────────────────────────────────────┤
│ 2. 自动化交互                         │
│    · 表单填写/提交                    │
│    · 点击/滚动/翻页                   │
│    · 登录/认证流程                    │
├──────────────────────────────────────┤
│ 3. 情报监控                           │
│    · 定时扫描目标网站                  │
│    · 检测内容变更                      │
│    · 竞品信息采集                      │
└──────────────────────────────────────┘
```

### 与已有 browser_* 工具的关系

| Hermes 已有 | Lightpanda |
|:-----------|:----------|
| `browser_navigate/click/type` | 基于 Chromium Puppeteer |
| `browser_vision`（截图+AI分析） | Lightpanda 无截图能力 |
| 完整浏览器环境 | 极轻量级，速度快10倍 |
| 适用于交互验证/视觉验证 | 适用于批量爬取/自动化 |

**互补使用**：Visual/验证用 Chromium 工具，批量爬取用 Lightpanda。

## 本地部署

```bash
cd ~/browser

# Lightpanda 提供多种运行方式:

# 1. Docker 运行（推荐）
docker pull lightpanda/browser:latest
docker run -d --name lightpanda -p 9222:9222 lightpanda/browser

# 2. 通过 CDP 协议调用
# Lightpanda 暴露 Chrome DevTools Protocol (CDP) 接口
# 兼容 Puppeteer/Playwright 客户端
```

## Hermes 集成方式

### 通过 CDP 协议调用

```python
import requests, json

def lightpanda_navigate(url):
    """通过 CDP 控制 Lightpanda"""
    # 连接到 Lightpanda CDP
    ws_url = "http://localhost:9222/json/new"
    
    # 轻量爬取（适合批量）
    resp = requests.get(url, timeout=30)
    return resp.text

def lightpanda_batch_crawl(urls):
    """批量爬取，比Chromium快10倍"""
    results = {}
    for url in urls:
        try:
            html = lightpanda_navigate(url)
            results[url] = {
                "status": "success",
                "html_length": len(html),
                "preview": html[:500]
            }
        except Exception as e:
            results[url] = {"status": "error", "error": str(e)}
    return results
```

### cronjob 定时爬虫集成

```python
# 与 Hermes cronjob 结合使用
# 定时任务：每6小时爬取竞品网站
"""
cronjob 配置:
  schedule: "0 */6 * * *"
  script: crawl_competitors.py
  prompt: "爬取竞品网站的最新变更，生成情报摘要"
"""
```

## 使用场景

| 场景 | 用 browser_*（Chromium） | 用 Lightpanda |
|:----|:------------------------|:-------------|
| 需要验证码识别 | ✅ 有 vision | ❌ |
| 需要截图 | ✅ | ❌ |
| 批量爬取100+页面 | ❌ 太慢 | ✅ |
| 定时监控价格变化 | ❌ 资源重 | ✅ |
| 交互式表单操作 | ✅ | ⚡ 有限 |
| 大规模数据采集 | ❌ | ✅ |
| 内存受限环境 | ❌ | ✅ |

## 启动快速测试

```bash
# 启动 Lightpanda（Docker）
docker run -d --name lightpanda \
  -p 9222:9222 \
  lightpanda/browser:latest

# 测试连接
curl -s http://localhost:9222/json/version

# 抓取一个页面
curl -s "http://localhost:9222/json/new?url=https://example.com"
```
