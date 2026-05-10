---
name: money-printer-turbo
description: 一键短视频生成工具 — 基于 MoneyPrinterTurbo (57K⭐)，提供主题即可自动生成脚本、素材、字幕、配音和完整视频
version: 0.1.0
tags:
- video
- short-video
- automation
- tts
- subtitle
- ai
metadata:
  hermes:
    molin_owner: 墨播短视频
    source: https://github.com/harry0703/MoneyPrinterTurbo
    stars: 57000
    repo_path: /home/ubuntu/MoneyPrinterTurbo
min_hermes_version: 0.13.0
---

# MoneyPrinterTurbo — 一键短视频生成

## 概述

MoneyPrinterTurbo（57K⭐）是一个只需提供视频主题或关键词，即可全自动生成视频文案、视频素材、视频字幕、视频背景音乐，并合成高清短视频的工具。

- **仓库位置**: `/home/ubuntu/MoneyPrinterTurbo`
- **GitHub**: https://github.com/harry0703/MoneyPrinterTurbo
- **物主**: 墨播短视频
- **依赖**: Docker（推荐）或 Python 3.10+、至少 2GB 内存

## 安装与启动

### 方案 A：Docker（推荐）

```bash
# 拉取镜像
docker pull harry0703/moneyprinterturbo

# 启动容器
docker run -d \
  --name mpt \
  -p 8080:8080 \
  -v /home/ubuntu/MoneyPrinterTurbo/config.toml:/app/config.toml \
  harry0703/moneyprinterturbo
```

### 方案 B：本地部署

```bash
cd /home/ubuntu/MoneyPrinterTurbo

# 安装依赖
pip install -r requirements.txt

# 配置文件
cp config.example.toml config.toml
# 编辑 config.toml，配置 LLM API Key（推荐 deepseek）和 Pexels API Key

# 启动 WebUI
python main.py
# 浏览器打开 http://localhost:8501

# 或启动 API 服务
python -m uvicorn app.asgi:app --host 0.0.0.0 --port 8080
```

## 核心 API

### API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/videos` | 全自动视频生成 |
| POST | `/api/v1/subtitle` | 字幕生成 |
| POST | `/api/v1/audio` | 音频生成 |
| GET | `/api/v1/tasks` | 任务列表查询 |
| GET | `/api/v1/tasks/{id}` | 任务详情查询 |

### 视频生成参数

```json
POST /api/v1/videos
{
  "video_subject": "AI 改变教育",
  "video_script": "",           // 留空则自动生成
  "video_aspect": "9:16",       // 竖屏
  "voice_name": "zh-CN-XiaoyiNeural-Female",
  "video_clip_duration": 5,     // 每个素材片段时长（秒）
  "video_count": 1,
  "video_concat_mode": "smart", // smart: 智能拼接, random: 随机
  "video_language": "zh-CN",
  "video_style": "auto",        // 风格：auto/realistic/cartoon
  "subtitle_enabled": true,
  "subtitle_position": "bottom",
  "bgm_enabled": true,
  "bgm_type": "random"
}
```

### Python 直接调用

```python
import sys
sys.path.insert(0, "/home/ubuntu/MoneyPrinterTurbo")

from app.models.schema import VideoParams
from app.services.task import start
import uuid

task_id = str(uuid.uuid4())
params = VideoParams(
    video_subject="深度学习入门",
    voice_name="zh-CN-XiaoyiNeural-Female",
    video_aspect="9:16",
    video_clip_duration=5,
)

result = start(task_id, params, stop_at="video")
# 返回: {script, terms, audio_file, subtitle_path, materials, videos, audio_duration}
```

## Hermes 集成

### 通过 short_video Worker 调用（墨播短视频）

```bash
# 使用 MoneyPrinterTurbo 引擎生成视频
python -m molib video generate --topic "AI Agent 入门" --engine mpt

# 仅生成脚本
python -m molib video script --topic "量子计算科普" --duration 60
```

### 通过 HTTP API 集成

```python
import requests

def generate_video(topic: str, duration: int = 60) -> dict:
    """调用 MPT 生成短视频"""
    resp = requests.post(
        "http://localhost:8080/api/v1/videos",
        json={"video_subject": topic, "video_clip_duration": duration}
    )
    return resp.json()

# 批量生成
def batch_generate(topics: list[str]):
    for topic in topics:
        result = generate_video(topic)
        print(f"✅ {topic}: {result.get('videos', [None])[0]}")
```

## 管线流程

```
输入: 主题/关键词
    │
    ▼
┌──────────────┐
│ LLM 生成文案  │  → 脚本优化（开头黄金3秒）
└──────┬───────┘
       ▼
┌──────────────┐
│ 素材自动搜索  │  → Pexels/本地素材库
└──────┬───────┘
       ▼
┌──────────────┐
│ TTS 语音合成  │  → 中文多音色（edge-tts）
└──────┬───────┘
       ▼
┌──────────────┐
│ 字幕自动生成  │  → 精确对齐语音
└──────┬───────┘
       ▼
┌──────────────┐
│ 背景音乐     │  → 自动匹配时长
└──────┬───────┘
       ▼
┌──────────────┐
│ FFmpeg 合成  │  → 最终视频输出
└──────────────┘
```

## 视频参数详解

| 参数 | 说明 | 可选值 |
|------|------|--------|
| 主题 | 视频内容主题 | 任何中文/英文文本 |
| 语言 | 生成语言 | `zh-CN`, `en-US`, `ja-JP` 等 |
| 音色 | TTS 语音 | `zh-CN-XiaoyiNeural-Female`, `zh-CN-YunxiNeural-Male`, `en-US-JennyNeural` 等 |
| 时长 | 每个素材片段时长 | 3-10 秒（推荐 5） |
| 字幕 | 是否开启字幕 | `true` / `false` |
| 字幕位置 | 字幕显示位置 | `bottom` / `top` |
| 画面比例 | 视频宽高比 | `9:16`（竖屏）, `16:9`（横屏）, `1:1` |

## 前置条件

- Docker（推荐）或 Python 3.10+
- 至少 2GB 可用内存
- LLM API Key（推荐 DeepSeek）
- Pexels API Key（素材搜索，免费注册 https://www.pexels.com/api/）
- 网络连接（下载素材和生成 TTS）

## 注意事项

- 首次生成需要下载模型和依赖，速度较慢
- 视频素材质量取决于搜索关键词和 Pexels 图库
- 如需高质量画面，建议搭配 Pixelle-Video（ComfyUI AI 生成）
- 中文 TTS 效果优秀，适合小红书/抖音内容
- 批量生成时注意 API 调用限额