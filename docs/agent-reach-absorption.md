# Agent-Reach 核心设计模式提取报告

> 分析日期: 2026-05-07
> 仓库: https://github.com/Panniantong/Agent-Reach (ver 1.4.0, 19K⭐)
> 目标: 提取可复用的"零API费"社交爬虫设计模式，用于 molib

---

## 一、架构总览

Agent-Reach 是一个**脚手架（scaffolding）而非框架**。它的核心理念是：

> 不包装上游工具，只负责安装、检测、配置。Agent 直接调用上游 CLI。

```
┌──────────────────────────────────────────────────────┐
│                    AI Agent                          │
│   (Claude Code / OpenClaw / Cursor / etc.)           │
└──────────┬─────────────┬──────────────┬──────────────┘
           │             │              │
    ┌──────┴──────┐ ┌───┴────┐  ┌─────┴──────┐
    │ agent-reach │ │ SKILL  │  │  Upstream  │
    │ CLI/doctor  │ │ .md    │  │  Tools     │
    └──────┬──────┘ └────────┘  │  (direct)  │
           │                    └──────┬─────┘
    ┌──────┴──────────────────────────┴──────┐
    │           channels/ 注册表              │
    │   (每个渠道 = 一个 Channel 子类)         │
    └─────────────────────────────────────────┘
```

### 核心文件结构

```
agent_reach/
├── cli.py              # CLI 入口（argparse），安装/配置/诊断
├── core.py             # AgentReach 门面类
├── config.py           # YAML 配置管理 (~/.agent-reach/config.yaml)
├── doctor.py           # 诊断引擎：遍历 channels 执行 check()
├── cookie_extract.py   # 从浏览器自动提取 Cookie（rookiepy/browser_cookie3）
├── channels/
│   ├── base.py         # 抽象基类 Channel
│   ├── __init__.py     # 渠道注册表 ALL_CHANNELS
│   ├── web.py          # Jina Reader — 读任意网页
│   ├── twitter.py      # twitter-cli / bird CLI
│   ├── reddit.py       # rdt-cli
│   ├── youtube.py      # yt-dlp
│   ├── github.py       # gh CLI
│   ├── bilibili.py     # yt-dlp + bili-cli + B站公开API
│   ├── xiaohongshu.py  # xhs-cli
│   ├── weibo.py        # mcporter + mcp-server-weibo
│   ├── wechat.py       # Exa + Camoufox
│   ├── linkedin.py     # linkedin-scraper-mcp + Jina Reader
│   ├── douyin.py       # douyin-mcp-server
│   ├── rss.py          # feedparser
│   ├── exa_search.py   # Exa MCP (语义搜索)
│   ├── v2ex.py         # V2EX 公开 API + 数据提取方法
│   ├── xueqiu.py       # 雪球 API + Cookie 注入
│   └── xiaoyuzhou.py   # Groq Whisper API
└── integrations/
    └── mcp_server.py   # MCP 服务器（暴露 doctor 状态）
```

---

## 二、核心设计模式

### 模式 1: Channel 抽象基类（策略模式）

所有平台继承同一个 `Channel` 抽象基类：

```python
class Channel(ABC):
    name: str = ""              # "twitter", "youtube"...
    description: str = ""       # 人类可读描述
    backends: List[str] = []    # 使用的上游工具
    tier: int = 0               # 0=零配置, 1=需免费key, 2=需复杂安装

    @abstractmethod
    def can_handle(self, url: str) -> bool: ...

    def check(self, config=None) -> Tuple[str, str]:
        return "ok", "..."      # 返回 "ok" / "warn" / "off" / "error"
```

**可复用点**: molib 可以直接复用这个策略模式，每个社交平台一个独立的 Channel 类。

### 模式 2: 渠道注册表（插件发现）

`channels/__init__.py` 显式注册所有 Channel：

```python
ALL_CHANNELS: List[Channel] = [
    GitHubChannel(), TwitterChannel(), YouTubeChannel(), ...
]

def get_channel(name: str) -> Optional[Channel]: ...
def get_all_channels() -> List[Channel]: ...
```

**可复用点**: 这本质是一个"插件注册表"，molib 可以照搬。

### 模式 3: 分层数据获取策略（Tier 系统）

| Tier | 含义 | 示例 |
|------|------|------|
| 0 | 零配置，装好即用 | Jina Reader, yt-dlp, V2EX公开API, RSS |
| 1 | 需免费Key或Cookie登录 | twitter-cli, xhs-cli, Weibo MCP |
| 2 | 需复杂配置 | Douyin MCP, LinkedIn MCP |

**关键洞察**: 诊断系统根据 tier 决定如何渲染报告，用户可以一眼看出哪些渠道需要额外配置。

### 模式 4: 四种"零API费"获取数据的子模式

这是最核心的部分——每个平台都用了不同的技术来绕开官方付费API。

#### 子模式 4a: Jina Reader 代理（通用网页读取）

文件: `channels/web.py`

```
用户输入 URL → https://r.jina.ai/URL → Jina Reader 渲染并清洗 → 返回 Markdown
```

原理: Jina Reader (jina.ai) 免费提供网页→Markdown 转换服务，不需要 API Key。它相当于一个"渲染后抓取"代理——在服务端执行 JS，提取主要内容，返回干净的 Markdown。

**适用场景**: 任何公开网页，包括微信文章（配合 site:mp.weixin.qq.com 搜索）

#### 子模式 4b: 第三方 CLI 工具包装（社区逆向工程）

| 平台 | 工具 | 原理 |
|------|------|------|
| Twitter/X | twitter-cli | 使用 Cookie (auth_token + ct0) 模拟浏览器访问，抓取 Twitter API 返回 JSON |
| Reddit | rdt-cli | 使用 Cookie (reddit_session) 通过 Reddit 图 API 获取帖子+评论 |
| 小红书 | xhs-cli | 使用 Cookie 登录后调用小红书内部 API |
| B站 | bili-cli | 调用 Bilibili 公开搜索 API (api.bilibili.com) |

**共同模式**: 这些 CLI 工具都是用 Python/JS 写的、GitHub 上开源的"逆向工程"工具。它们不需要官方 API Key，只需要用户从浏览器导出的 Cookie。

#### 子模式 4c: 利用公开的第三方免费 API

| 平台 | 服务 | 原理 |
|------|------|------|
| 网页 | Jina Reader | r.jina.ai 免费渲染服务，用于读取任意网页 |
| 全网搜索 | Exa | 提供免费 MCP endpoint (mcp.exa.ai)，AI 搜索无需 Key |
| YouTube | yt-dlp | 154K Star 的开源下载器，直接解析 YouTube 页面提取字幕 |
| B站视频 | yt-dlp | 同上，也支持 Bilibili |
| RSS | feedparser | 标准 RSS/Atom XML 解析 |

**关键洞察**: 使用"免费但有限额"的第三方 AI 服务（Exa、Jina）作为搜索和读取后端。

#### 子模式 4d: 直接调用平台的公开/未文档化 API

| 文件 | 平台 | API 端点 | 是否需要认证 |
|------|------|----------|-------------|
| v2ex.py | V2EX | api.v2ex.com/topics/hot.json | ❌ 完全公开 |
| bilibili.py | B站 | api.bilibili.com/x/web-interface/search/all/v2 | ❌ 公开 |
| xueqiu.py | 雪球 | stock.xueqiu.com/v5/stock/batch/quote.json | ✅ 需要 Cookie |

**关键洞察**: 部分平台在 Web 前端使用内部 JSON API，访问这些 API 不需要认证或只需要简单的 Cookie。xueqiu.py 是这种模式的典型——它直接调用雪球的 v5 JSON API，用 `urllib` 发送请求，注入从浏览器获取的 Cookie。

### 模式 5: Cookie 管理策略

文件: `cookie_extract.py`

```
Cookie 获取优先级:
  1. 从配置文件 ~/.agent-reach/config.yaml 读取
  2. 从浏览器自动提取（rookiepy > browser_cookie3）
  3. 用户手动导出（Cookie-Editor Chrome 插件）

支持的浏览器: Chrome, Firefox, Edge, Brave, Opera
支持提取Cookie的平台: Twitter, 小红书, B站, 雪球
```

**Cookie 注入方式**:
- **环境变量**: Twitter (TWITTER_AUTH_TOKEN, TWITTER_CT0)
- **配置文件直接存储**: 雪球 (xueqiu_cookie string)
- **配置文件分字段存储**: B站 (bilibili_sessdata, bilibili_csrf)

**安全措施**:
- `config.yaml` 创建时设 600 权限
- Token/Cookie 只存在本地，不上传
- `to_dict()` 方法自动掩码敏感字段

### 模式 6: 诊断即文档（Doctor 引擎）

```python
# doctor.py
def check_all(config: Config) -> Dict[str, dict]:
    for ch in get_all_channels():
        status, message = ch.check(config)
        results[ch.name] = {
            "status": status, "name": ch.description,
            "message": message, "tier": ch.tier, "backends": ch.backends,
        }
```

每个 Channel 的 `check()` 方法既做诊断又做文档——它返回的 message 直接告诉用户下一步该做什么。例如 Reddit 的 check() 会返回：

```
"rdt-cli 已安装但未登录。Reddit 自 2024 年起要求认证，未登录时所有请求均返回 403。\n\n方法一（自动）：运行 `rdt login`..."
```

### 模式 7: XHS 数据清洗器（响应规约化）

文件: `xiaohongshu.py` 中的 `format_xhs_result()` 和 `_clean_note()`

```python
def format_xhs_result(data):
    """Clean XHS API response, keeping only useful fields.
    Drastically reduces token usage by stripping structural redundancy."""
```

**作用**: 小红书 API 返回的 JSON 嵌套深、字段多（200+字段），通过这个清洗器减少到 15-20 个有用字段，大幅减少 LLM token 消耗。

**可复用点**: 这个模式对所有社交平台 API 响应都适用——每个平台都可以写一个 clean 函数。

---

## 三、关键依赖分析

### 运行时依赖（pyproject.toml）

```toml
dependencies = [
    "requests>=2.28",    # HTTP 请求（备注：实际用了 urllib 而非 requests）
    "feedparser>=6.0",   # RSS/Atom 解析
    "python-dotenv>=1.0", # .env 文件加载
    "loguru>=0.7",       # 日志
    "pyyaml>=6.0",       # YAML 配置
    "rich>=13.0",        # CLI 富文本输出
    "yt-dlp>=2024.0",    # 视频下载/字幕提取
]
```

**核心发现**: Agent-Reach 自身的依赖非常轻量。实际的"爬虫能力"由外部 CLI 工具提供，不内嵌在仓库中。

### 外部工具依赖

| 平台 | 外部工具 | 安装方式 |
|------|---------|---------|
| Web | Jina Reader | 无需安装，直接 curl https://r.jina.ai/URL |
| Twitter | twitter-cli | pipx install twitter-cli (+ Cookie) |
| Reddit | rdt-cli | pip install rdt-cli (+ `rdt login`) |
| YouTube/B站 | yt-dlp | pip install yt-dlp |
| GitHub | gh CLI | 官方安装 + `gh auth login` |
| 小红书 | xhs-cli | pipx install xiaohongshu-cli |
| 微博 | mcporter + mcp-server-weibo | npm + pip |
| 全网搜索 | mcporter + Exa MCP | npm + mcporter config |
| 抖音 | mcporter + douyin-mcp-server | npm + pip |
| LinkedIn | mcporter + linkedin-scraper-mcp | npm + pip |
| 小宇宙 | ffmpeg + Groq Whisper | ffmpeg + Groq API Key |

---

## 四、molib 轻量版实现方案

### 4.1 核心设计

```
molib_crawler/
├── channels/
│   ├── base.py          # Channel 基类（复用 Agent-Reach 模式）
│   ├── registry.py      # 渠道注册表
│   ├── jina_reader.py   # Web阅读（零配置）
│   ├── twitter.py       # 通过 twitter-cli
│   ├── bilibili.py      # 通过 B站公开 API + urllib
│   ├── v2ex.py          # 通过 V2EX 公开 API
│   ├── xueqiu.py        # 通过雪球 API
│   └── ...（按需添加）
├── cookie/
│   ├── extract.py       # 浏览器 Cookie 提取（复用模式）
│   └── manager.py       # Cookie 存储/管理
├── clean/
│   └── xhs_cleaner.py   # 响应清洗（参考 xiaohongshu.py）
├── config.py            # YAML 配置（直接复用 Agent-Reach Config 类）
└── doctor.py            # 诊断引擎（直接复用 Agent-Reach doctor.py 模式）
```

### 4.2 最小可用集（不需要任何外部工具）

| 渠道 | 实现方式 | 代码量 |
|------|---------|--------|
| 网页阅读 | Jina Reader: `urllib → r.jina.ai/URL` | ~30 行 |
| B站搜索 | `urllib → api.bilibili.com/x/web-interface/search/all/v2` | ~40 行 |
| V2EX | `urllib → api.v2ex.com` (热门/节点/用户) | ~200 行 |
| RSS | `feedparser` | ~20 行 |
| 雪球行情 | `urllib + Cookie → stock.xueqiu.com/v5` | ~100 行 |

**特点**: 只用 Python 标准库 + feedparser，无需安装任何外部 CLI 工具。

### 4.3 扩展集（需安装外部工具）

| 渠道 | 前置条件 | 特点 |
|------|---------|------|
| Twitter | pip install twitter-cli + Cookie | 功能最全 |
| Reddit | pip install rdt-cli + `rdt login` | 需 Reddit 账号 |
| 小红书 | pipx install xiaohongshu-cli + Cookie | 需小红书账号 |
| YouTube | yt-dlp（已在依赖中） | 字幕提取 |

### 4.4 关键代码骨架

```python
# channels/base.py
from abc import ABC, abstractmethod
from typing import List, Tuple

class Channel(ABC):
    name: str = ""
    description: str = ""
    backends: List[str] = []
    tier: int = 0  # 0=零配置, 1=需Key/登录, 2=复杂

    @abstractmethod
    def can_handle(self, url: str) -> bool: ...

    @abstractmethod
    def fetch(self, url: str, **kwargs) -> dict: ...
    
    def check(self, config=None) -> Tuple[str, str]:
        return "ok", f"{'、'.join(self.backends) if self.backends else '内置'}"

# channels/registry.py
_registry: List[Channel] = []

def register(ch: Channel):
    _registry.append(ch)

def get_all() -> List[Channel]: return _registry
def get_by_url(url: str) -> Optional[Channel]:
    for ch in _registry:
        if ch.can_handle(url): return ch
    return None

# channels/jina_reader.py
import urllib.request
class JinaReaderChannel(Channel):
    name = "web"
    description = "任意网页"
    tier = 0
    
    def can_handle(self, url: str) -> bool:
        return True  # 万能兜底
    
    def fetch(self, url: str, **kwargs) -> dict:
        jina_url = f"https://r.jina.ai/{url}"
        req = urllib.request.Request(jina_url, headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/plain",
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            return {"content": resp.read().decode("utf-8"), "source": url}
```

---

## 五、核心经验教训

### 为什么 Agent-Reach 能做到"零API费"

1. **不加抽象层** — 不包装上游工具，Agent 直接调用。省去了维护兼容层的成本
2. **社区逆向工程** — 每个平台都有开源社区维护的"非官方 CLI"（twitter-cli、xhs-cli、rdt-cli），这些工具已经破解了各平台的 API 封锁
3. **免费代理服务** — Jina Reader 和 Exa 提供免费的 AI 代理服务，覆盖了网页阅读和全网搜索两个最大的需求
4. **Cookie 代替 API Key** — 几乎所有需要认证的平台都走 Cookie 认证，这是"零费用"的核心
5. **公开 API 万岁** — 部分平台（V2EX、B站搜索接口）的 API 本身就不需要认证

### 在 molib 中复用的注意事项

1. **外部工具的脆弱性** — twitter-cli、rdt-cli 等依赖平台的反爬策略，随时可能被封。应该保持 Channel.check() 常运行
2. **Cookie 安全** — Cookie 存储在本地 config.yaml，必须设 600 权限
3. **响应清洗** — 社交平台 API 返回的原始 JSON 包含大量无用字段，必须清洗后再给 LLM 使用（参考 xiaohongshu.py 的 format_xhs_result）
4. **错误处理** — 所有网络请求必须有超时和降级策略。Jina Reader 应该作为所有渠道的兜底方案
5. **代理需求** — B站、Reddit 等平台在服务器 IP 上可能无法访问，需要可配置的 HTTP 代理

---

## 六、总结

Agent-Reach 的架构设计非常简洁，核心思想可以概括为三个模式：

| 模式 | 作用 | molib 直接复用量 |
|------|------|-----------------|
| Channel 抽象 + 注册表 | 插件化平台管理 | 90% 可直接复制 |
| Doctor 诊断引擎 | 自检+文档二合一 | 80% 可直接复制 |
| 四种零API费数据获取 | 爬虫策略 | 60% 可复制（需适配具体平台） |
| Cookie 管理 | 免 Key 认证 | 70% 可复制 |
| 响应清洗器 | 减少 LLM token 消耗 | 100% 可复制思路 |

**最小 molib 集成成本**: 约 300 行 Python 代码即可实现 Jina Reader + B站搜索 + V2EX + RSS 四个零配置渠道。
