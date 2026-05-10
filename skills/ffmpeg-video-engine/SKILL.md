---

name: ffmpeg-video-engine
description: GPU-free automated short video pipeline — script→images→TTS voiceover→background music→FFmpeg composition. Produces Xiaohongshu-ready vertical videos without any GPU. Uses Edge-TTS (free), Pillow, and FFmpeg.
version: 1.0.0
tags: [video, ffmpeg, tts, content, automation, xiaohongshu]
category: content
metadata:
  hermes:
    molin_owner: 墨迹（内容工厂）
---

# FFmpeg Video Engine — 无 GPU 视频管线

## 管线流程

```
Step 1: 脚本生成 → xiaohongshu-content-engine
Step 2: 图片准备 → Pillow 生成/ComfyUI API/外部API
Step 3: TTS配音   → edge-tts (免费, zh-CN-XiaoxiaoNeural)
Step 4: 背景音乐  → 下载 royalty-free 或本地库
Step 5: FFmpeg合成 → 图片+音频+字幕+转场 → MP4
```

## Step-by-Step Commands

### 1. TTS Voiceover
```bash
edge-tts --voice zh-CN-XiaoxiaoNeural \
  --text "这里是你的视频文案内容" \
  --write-media output/voice.mp3
```

Available Chinese voices:
- `zh-CN-XiaoxiaoNeural` — 女声，温柔
- `zh-CN-YunxiNeural` — 男声，自然
- `zh-CN-XiaoyiNeural` — 女声，活泼

### 2. Generate Cover/Slide Images
Using Pillow:
```python
from PIL import Image, ImageDraw, ImageFont
# Create cover image with text overlay
img = Image.new('RGB', (1080, 1920), color=(255,255,255))
draw = ImageDraw.Draw(img)
# Add text, gradients, etc.
img.save('output/frame_000.png')
```

### 3. Compose Video with FFmpeg

**Single image + audio (slideshow):**
```bash
ffmpeg -loop 1 -i image.png -i voice.mp3 \
  -c:v libx264 -tune stillimage -preset fast \
  -c:a aac -b:a 128k -pix_fmt yuv420p \
  -shortest -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2" \
  output.mp4
```

**Multiple images with fade transitions:**
```bash
# Create image list
# duration 3 seconds per image, fade 0.5s
ffmpeg \
  -loop 1 -t 3 -i frame_001.png \
  -loop 1 -t 3 -i frame_002.png \
  -loop 1 -t 3 -i frame_003.png \
  -i voice.mp3 \
  -filter_complex "\
    [0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fade=t=out:st=2.5:d=0.5[v0];\
    [1:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fade=t=in:st=0:d=0.5,fade=t=out:st=2.5:d=0.5[v1];\
    [2:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fade=t=in:st=0:d=0.5[v2];\
    [v0][v1][v2]concat=n=3:v=1:a=0[outv]" \
  -map "[outv]" -map 3:a -c:v libx264 -preset fast -c:a aac -b:a 128k -pix_fmt yuv420p \
  output.mp4
```

**Add text subtitles:**
```bash
ffmpeg -i input.mp4 -vf "drawtext=text='你的字幕':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=h-th-100:box=1:boxcolor=black@0.5:boxborderw=10" output.mp4
```

## Presets

| 平台 | 分辨率 | 时长 | 格式建议 |
|------|--------|------|----------|
| 小红书 | 1080×1920 (9:16) | 15-60s | 竖屏+大字幕 |
| 抖音 | 1080×1920 (9:16) | 15-60s | 快速剪辑+热门BGM |
| 视频号 | 1080×1920 | 30-90s | 信息密度高 |

## Voice Selection by Content Type

| 内容类型 | 推荐语音 | 语速 |
|----------|---------|------|
| AI工具教程 | Xiaoxiao/Yunxi | +10% |
| 收入分享 | Xiaoxiao | 正常 |
| 产品展示 | Xiaoyi | +5% |
| 故事讲述 | Xiaoxiao | -5% |

## Limitations

- No AI video generation (no GPU)
- Images must be pre-generated (via external API or Pillow)
- No complex animations
- Voice is TTS quality, not human
