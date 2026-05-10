# 墨麟OS 环境清单

> 生成时间：2026-05-10 17:02
> 主机：macOS 26.4.1 (25E253)
> 架构：Apple Silicon (arm64)

## 系统软件

| 软件 | 版本 | 路径 |
|:-----|:-----|:-----|
| macOS | 26.4.1 | — |
| Homebrew | 5.1.10 | /opt/homebrew |
| Git | 2.50.1 | /usr/bin/git |
| Node.js | v24.14.0 | /opt/homebrew |
| npm | 11.9.0 | /opt/homebrew |
| Python 3.11 | 3.11.15 | /Users/moye/.local/share/uv/python/cpython-3.11.15-macos-aarch64-none |
| Python 3.12 | 3.12.13 | /opt/homebrew/bin/python3.12 |
| FFmpeg | 8.1.1 | /usr/local/bin/ffmpeg |

## Homebrew 已安装包

```
ca-certificates  dav1d  ffmpeg  lame  libvmaf  libvpx  
mpdecimal  openssl@3  opus  pcre2  python@3.12  
readline  ripgrep  sdl2  sqlite  svt-av1  
x264  x265  xz
```

## Hermes Agent

- 版本：v0.13.0 (2026.5.7)
- 项目路径：/Users/moye/.hermes/hermes-agent
- Python：3.11.15 (venv)
- OpenAI SDK：2.36.0
- Gateway：PID 15484 (launchd 托管)
- web-ui：v0.5.16 (:8648)
- CLI 模式：Feishu 私聊通道

## molib

- 版本：v5.0.0
- 安装方式：editable (pip install -e ~/Molin-OS/molib)
- 健康检查：9/9 ok
- CLI 命令：25+

## feishu-cli

- 版本：v1.23.0
- 构建日期：2026-05-09
- 17 个模块：doc/wiki/file/user/board/media/comment/perm/msg/bitable/task/approval/calendar/vc/minutes/mail/drive

## Hermes venv 关键依赖

```
firecrawl-py==4.25.2
httpx, aiohttp, pandas, numpy, openai, markdown
ffmpeg-python, loguru, schedule, flask, flask-cors
blackboxprotobuf, PyExecJS, websockets, requests
pydantic, PyYAML, rich, tqdm
```

## Python 3.12 环境 (xianyu)

```
certifi, charset-normalizer, idna, requests, urllib3
```

## npm 全局包

```
hermes-web-ui@0.5.16
```

## 配置密钥

| 密钥 | 状态 |
|:-----|:----:|
| DEEPSEEK_API_KEY | ✅ |
| DASHSCOPE_API_KEY | ✅ |
| OPENROUTER_API_KEY | ✅ |
| GITHUB_TOKEN | ✅ |
| FEISHU_APP_ID/SECRET | ✅ |
| SUPERMEMORY_API_KEY | ✅ |
| FIRECRAWL_API_KEY | ❌ 待配置 |

## Xianyu 闲鱼

- Cookies：✅ 已配置 (17个)
- Python 3.12：✅ 3.12.13
- XianYuApis：✅ ~/xianyu_agent/
- Cron：每30分钟 (15,45 9-21)

## Cron 作业 (9个)

| 时间 | 作业 | 状态 |
|:-----|:-----|:----:|
| 03:00 | 每日系统备份 | ✅ |
| 08:00 | 墨思情报银行 | ✅ |
| 09:00 | CEO每日简报 | ✅ |
| 09:00 | 墨迹内容工厂 | ✅ |
| 10:00 | 墨增增长引擎 | ✅ |
| 10:00 | 每日治理合规 | ✅ |
| 12:00 | 系统健康快照 | ✅ |
| 15,45 9-21 | 闲鱼消息检测 | ✅ |
| 周五 10:00 | 自学习每周进化 | ✅ |

## 备份

- GitHub：https://github.com/moye-tech/Molin-OS
- 本地硬盘：/Volumes/MolinOS/hermes/ (330MB)
- 还原脚本：scripts/restore.sh
