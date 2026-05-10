---
name: moneymaker-turbo
description: 中文短视频批量生成引擎 — 基于 harry0703/MoneyPrinterTurbo (57K⭐)。只需提供主题或关键词，自动生成视频文案、素材、字幕、背景音乐并合成高清短视频。Pixelle-Video
  的备选/补充管线。墨迹（内容工厂）视频工具。
version: 1.0.0
tags:
- video
- automation
- chinese
- short-video
- tts
- subtitle
- ai
category: content
metadata:
  hermes:
    source: https://github.com/harry0703/MoneyPrinterTurbo
    stars: 57000
    upstream_fork: https://github.com/moye-tech/MoneyPrinterTurbo
    alternative_to: pixelle-video
    molin_owner: 墨迹（内容工厂）
min_hermes_version: 0.13.0
---

# MoneyMaker Turbo — 中文短视频生成引擎

## 概述

**MoneyPrinterTurbo** 只需提供一个视频主题或关键词，就可以全自动生成视频文案、视频素材、视频字幕、视频背景音乐，然后合成一个高清的短视频。

与 Pixelle-Video 的定位：
- **Pixelle-Video**：英文为主，AI Art（SD/ComfyUI）驱动
- **MoneyPrinterTurbo**：中文为主，素材库驱动 + WebUI
- **互补使用**：中文内容用 MPT，英文内容用 Pixelle

## 快速开始

```bash
cd ~/MoneyPrinterTurbo

# 安装依赖
pip install -r requirements.txt

# 配置文件
cp config.example.toml config.toml
# 编辑 config.toml 配置 API Key（llm / tts 等）

# 启动 Web UI
python main.py
# 浏览器打开 http://localhost:8501

# 或通过 API
curl -X POST http://localhost:8080/api/v1/video \
  -H "Content-Type: application/json" \
  -d '{"keyword": "AI改变教育", "duration": 60}'
```

## 配置说明

```toml
# config.toml 关键配置
[llm]
# 文案生成模型（支持 OpenAI / DeepSeek / 通义千问）
provider = "deepseek"
api_key = "sk-xxx"

[tts]
# 语音生成（Edge TTS / Azure / 讯飞）
provider = "edge_tts"
voice = "zh-CN-XiaoxiaoNeural"

[video]
# 素材来源（pexels / 本地 / AI生成）
material_source = "pexels"
resolution = "1080x1920"  # 竖屏
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
│ TTS 语音合成  │  → 中文多音色
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

## Hermes 集成

```python
# 通过 API 调用
import requests

def generate_video(topic, duration=60):
    """调用 MPT 生成短视频"""
    resp = requests.post(
        "http://localhost:8080/api/v1/video",
        json={"keyword": topic, "duration": duration}
    )
    return resp.json()  # 返回视频文件路径

# 与 ffmpeg-video-engine 组合使用
def batch_generate(topics):
    """批量生成多个主题的短视频"""
    for topic in topics:
        result = generate_video(topic)
        print(f"✅ {topic}: {result['video_path']}")
```

## 使用场景

| 场景 | 推荐管线 |
|:----|:---------|
| 小红书中文种草视频 | MPT（中文TTS更自然） |
| 抖音短视频批量 | MPT（WebUI 批量操作） |
| 英文科普动画 | Pixelle-Video |
| 需要高质量画面 | Pixelle（ComfyUI SD生成） |
| 快速原型测试 | MPT（最快出片） |
| 无 GPU 环境 | MPT（素材库不需要 GPU） |