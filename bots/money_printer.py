#!/usr/bin/env python3
"""
MoneyPrinterTurbo Lite — 轻量级 CLI 短视频批量生成工具

核心逻辑提取自 harry0703/MoneyPrinterTurbo (57K⭐)
功能：
  - edge-tts 语音合成（含 SRT 字幕生成）
  - 本地素材 / PIL 占位图视频合成
  - moviepy 字幕叠加 + BGM 混音
  - CLI 一键调用

依赖:
  pip install moviepy edge-tts Pillow httpx

用法:
  python money_printer.py --topic "春天的花海" --count 1
  python money_printer.py --topic "AI Technology" --count 2 --voice "en-US-AriaNeural"
"""

import argparse
import asyncio
import glob
import json
import os
import random
import re
import shutil
import sys
import tempfile
import textwrap
import uuid
from datetime import timedelta
from pathlib import Path
from typing import List, Optional, Tuple

# ── 三方依赖 ──────────────────────────────────────────────────────────────
try:
    from moviepy import (
        AudioFileClip,
        ColorClip,
        CompositeAudioClip,
        CompositeVideoClip,
        ImageClip,
        TextClip,
        VideoFileClip,
        afx,
        concatenate_videoclips,
    )
    from moviepy.video.tools.subtitles import SubtitlesClip
except ImportError:
    print("请安装 moviepy: pip install moviepy")
    sys.exit(1)

try:
    import edge_tts
    from edge_tts import SubMaker
except ImportError:
    print("请安装 edge-tts: pip install edge-tts")
    sys.exit(1)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("请安装 Pillow: pip install Pillow")
    sys.exit(1)


# ── 常量 ───────────────────────────────────────────────────────────────────
FPS = 30
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"

DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"
DEFAULT_FONT = None  # 自动探测
DEFAULT_VIDEO_ASPECT = "9:16"       # portrait
DEFAULT_BGM_VOLUME = 0.2
DEFAULT_VOICE_VOLUME = 1.0
DEFAULT_VOICE_RATE = 1.0
DEFAULT_CLIP_DURATION = 5
DEFAULT_STROKE_WIDTH = 1.5
DEFAULT_FONT_SIZE = 60
DEFAULT_TEXT_COLOR = "#FFFFFF"
DEFAULT_STROKE_COLOR = "#000000"

MONKEY_PRINTER_DIR = os.path.expanduser("~/MoneyPrinterTurbo")
RESOURCE_DIR = os.path.join(MONKEY_PRINTER_DIR, "resource")
SONGS_DIR = os.path.join(RESOURCE_DIR, "songs")
FONTS_DIR = os.path.join(RESOURCE_DIR, "fonts")
STORAGE_DIR = os.path.join(MONKEY_PRINTER_DIR, "storage")


# ── 工具函数 ───────────────────────────────────────────────────────────────

def _find_font() -> str:
    """从本地或 MoneyPrinter 资源中找到可用的中英文字体"""
    # 优先用 MoneyPrinter 自带的字体
    candidates = [
        os.path.join(FONTS_DIR, "STHeitiMedium.ttc"),
        os.path.join(FONTS_DIR, "MicrosoftYaHeiNormal.ttc"),
        os.path.join(FONTS_DIR, "Charm-Bold.ttf"),
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    # fallback: try any ttf/ttc
    for root, _dirs, files in os.walk("/usr/share/fonts"):
        for f in files:
            if f.endswith((".ttf", ".ttc")):
                return os.path.join(root, f)
    raise FileNotFoundError("未找到可用字体，请安装 fonts-wqy-zenhei 或 DejaVu Sans")


def get_font_path() -> str:
    global DEFAULT_FONT
    if DEFAULT_FONT is None:
        DEFAULT_FONT = _find_font()
    return DEFAULT_FONT


def time_to_srt(seconds: float) -> str:
    """将秒数转换为 SRT 时间格式 HH:MM:SS,mmm"""
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    millis = int((td.total_seconds() - total_seconds) * 1000)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def text_to_srt(idx: int, msg: str, start: float, end: float) -> str:
    return f"{idx}\n{time_to_srt(start)} --> {time_to_srt(end)}\n{msg}\n"


def split_by_punctuation(text: str) -> List[str]:
    """按标点符号分割文本为短句"""
    punct = set("。！？，、；：.!?,;:\n")
    result = []
    buf = ""
    for i, ch in enumerate(text):
        if ch == "\n":
            if buf.strip():
                result.append(buf.strip())
                buf = ""
            continue
        # 跳过数字间的点（小数）
        if ch == "." and i > 0 and i < len(text) - 1:
            if text[i - 1].isdigit() and text[i + 1].isdigit():
                buf += ch
                continue
        if ch in punct:
            if buf.strip():
                result.append(buf.strip())
            buf = ""
        else:
            buf += ch
    if buf.strip():
        result.append(buf.strip())
    return result


def wrap_text(text: str, max_width: int, font_path: str, fontsize: int) -> Tuple[str, int]:
    """按宽度换行文本，返回(换行后文本, 高度)"""
    font = ImageFont.truetype(font_path, fontsize)

    def tw(t):
        t = t.strip()
        left, top, right, bottom = font.getbbox(t)
        return right - left, bottom - top

    w, h = tw(text)
    if w <= max_width:
        return text, h

    words = text.split(" ")
    lines = []
    buf = ""
    for word in words:
        test = f"{buf} {word}".strip() if buf else word
        tw_, _ = tw(test)
        if tw_ <= max_width:
            buf = test
        else:
            if buf:
                lines.append(buf)
            buf = word
    if buf:
        lines.append(buf)

    # 如果空格分段太长，用字符级
    if any(tw(l)[0] > max_width for l in lines):
        lines = []
        buf = ""
        for ch in text:
            test = buf + ch
            tw_, _ = tw(test)
            if tw_ <= max_width:
                buf = test
            else:
                if buf:
                    lines.append(buf)
                buf = ch
        if buf:
            lines.append(buf)

    result = "\n".join(l.strip() for l in lines if l.strip())
    height = len(lines) * h
    return result, height


def parse_aspect(aspect_str: str) -> Tuple[int, int]:
    """解析画面比例，返回 (width, height)"""
    mapping = {
        "16:9": (1920, 1080),
        "9:16": (1080, 1920),
        "1:1": (1080, 1080),
    }
    if aspect_str in mapping:
        return mapping[aspect_str]
    try:
        w, h = aspect_str.split(":")
        return int(w), int(h)
    except (ValueError, AttributeError):
        return 1080, 1920


# ── 语音合成 (edge-tts) ───────────────────────────────────────────────────

async def _edge_tts(text: str, voice: str, rate: float, output_path: str) -> SubMaker:
    """使用 edge-tts 合成语音，返回 SubMaker（含时间戳）"""
    rate_str = f"+{int((rate - 1) * 100)}%" if rate >= 1 else f"{int((rate - 1) * 100)}%"
    communicate = edge_tts.Communicate(text, voice, rate=rate_str)
    sub_maker = SubMaker()
    with open(output_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                sub_maker.create_sub((chunk["offset"], chunk["duration"]), chunk["text"])
    return sub_maker


def synthesize_voice(text: str, voice: str, rate: float, output_path: str) -> SubMaker:
    """同步包装：edge-tts 语音合成"""
    return asyncio.run(_edge_tts(text, voice, rate, output_path))


# ── 字幕生成 ───────────────────────────────────────────────────────────────

def generate_subtitle(
    sub_maker: SubMaker,
    original_text: str,
    subtitle_path: str,
) -> str:
    """从 SubMaker 时间戳生成 SRT 字幕文件"""
    if not sub_maker.subs:
        return ""

    lines = split_by_punctuation(original_text)
    if not lines:
        return ""

    sub_items = []
    sub_idx = 0
    sub_line = ""
    start_time = -1.0

    for offset, sub in zip(sub_maker.offset, sub_maker.subs):
        _start, end_time = offset
        if start_time < 0:
            start_time = _start
        sub_line += sub

        # 尝试匹配当前累积文本到一个 script line
        if sub_idx < len(lines):
            target = lines[sub_idx]
            # clean matching
            clean_line = re.sub(r"[^\w\s]", "", sub_line).strip()
            clean_target = re.sub(r"[^\w\s]", "", target).strip()
            if clean_line == clean_target or sub_line.strip() == target.strip():
                sub_idx += 1
                srt_entry = text_to_srt(
                    sub_idx,
                    target.strip(),
                    start_time / 10000000,
                    end_time / 10000000,
                )
                sub_items.append(srt_entry)
                start_time = -1.0
                sub_line = ""

    # 如果匹配不完全，fallback：逐句分配等长时间
    if len(sub_items) < len(lines):
        sub_items = []
        total_duration = sub_maker.offset[-1][1] / 10000000 if sub_maker.offset else 1.0
        seg_dur = total_duration / len(lines)
        for i, line in enumerate(lines):
            s = i * seg_dur
            e = min((i + 1) * seg_dur, total_duration)
            sub_items.append(text_to_srt(i + 1, line.strip(), s, e))

    os.makedirs(os.path.dirname(subtitle_path) or ".", exist_ok=True)
    with open(subtitle_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sub_items) + "\n")
    return subtitle_path


# ── 素材获取 ───────────────────────────────────────────────────────────────

def get_local_videos(count: int = 5) -> List[str]:
    """从 resource/videos/ 或 test/resources/ 获取本地视频素材"""
    candidates = []

    # 从 MoneyPrinter test resources 找
    test_dir = os.path.join(MONKEY_PRINTER_DIR, "test", "resources")
    if os.path.isdir(test_dir):
        for f in sorted(glob.glob(os.path.join(test_dir, "*.png.mp4"))):
            candidates.append(f)

    # 也尝试从 resource/videos 找
    videos_dir = os.path.join(RESOURCE_DIR, "videos")
    if os.path.isdir(videos_dir):
        for ext in ("*.mp4", "*.mov", "*.avi"):
            for f in glob.glob(os.path.join(videos_dir, ext)):
                candidates.append(f)

    if candidates:
        random.shuffle(candidates)
        return candidates[:count]
    return []


def generate_placeholder_videos(output_dir: str, count: int, aspect: Tuple[int, int],
                                 duration: float = 5.0) -> List[str]:
    """用 PIL 生成彩色渐变占位图，转为视频片段"""
    w, h = aspect
    paths = []
    colors = [
        (70, 130, 180),   # steel blue
        (60, 179, 113),   # medium sea green
        (218, 165, 32),   # goldenrod
        (205, 92, 92),    # indian red
        (147, 112, 219),  # medium purple
        (0, 139, 139),    # dark cyan
        (210, 105, 30),   # chocolate
        (100, 149, 237),  # cornflower blue
    ]

    os.makedirs(output_dir, exist_ok=True)

    for i in range(count):
        color = colors[i % len(colors)]
        img = Image.new("RGB", (w, h), color)

        # 添加渐变效果
        draw = ImageDraw.Draw(img)
        r, g, b = color
        for y in range(h):
            fade = 1.0 - (y / h) * 0.4
            rc = min(255, int(r * fade))
            gc = min(255, int(g * fade))
            bc = min(255, int(b * fade))
            draw.line([(0, y), (w, y)], fill=(rc, gc, bc))

        # 添加一些装饰性文字
        try:
            font_path = get_font_path()
            font = ImageFont.truetype(font_path, 48)
            draw.text((w // 2 - 100, h // 2 - 30), f"Scene {i + 1}", fill=(255, 255, 255, 180), font=font)
        except Exception:
            pass

        img_path = os.path.join(output_dir, f"placeholder_{i}.png")
        img.save(img_path)

        # 转为 moviepy 视频片段
        clip = (
            ImageClip(img_path)
            .with_duration(duration)
            .with_position("center")
        )
        # zoom effect
        zoom_clip = clip.resized(lambda t: 1 + 0.03 * (t / duration))
        video_path = os.path.join(output_dir, f"placeholder_{i}.mp4")
        zoom_clip.write_videofile(video_path, fps=FPS, logger=None)
        clip.close()
        paths.append(video_path)

    return paths


def get_bgm_file() -> str:
    """随机选取背景音乐"""
    if not os.path.isdir(SONGS_DIR):
        return ""
    files = glob.glob(os.path.join(SONGS_DIR, "*.mp3"))
    if files:
        return random.choice(files)
    return ""


# ── 视频合成核心 ───────────────────────────────────────────────────────────

def combine_videos(
    video_paths: List[str],
    audio_path: str,
    output_path: str,
    aspect: Tuple[int, int] = (1080, 1920),
    max_clip_duration: int = 5,
    video_concat_mode: str = "random",
    threads: int = 2,
) -> str:
    """
    合并多个视频片段 + 音频，核心逻辑来自 MoneyPrinterTurbo 的 combine_videos()
    - 将视频裁剪为 max_clip_duration 秒片段
    - 随机排列或顺序排列
    - 缩放 + 居中裁剪适配目标分辨率
    - 循环片段直到匹配音频长度
    - 逐片段合并（防内存溢出）
    """
    audio_clip = AudioFileClip(audio_path)
    audio_duration = audio_clip.duration
    audio_clip.close()

    video_width, video_height = aspect
    output_dir = os.path.dirname(output_path) or "."

    # Step 1: 将每个视频切分为 max_clip_duration 秒的子片段
    subclips = []  # list of (file_path, start, end, width, height)
    for vp in video_paths:
        try:
            clip = VideoFileClip(vp)
            clip_dur = clip.duration
            clip_w, clip_h = clip.size
            clip.close()

            start = 0.0
            while start < clip_dur:
                end = min(start + max_clip_duration, clip_dur)
                subclips.append((vp, start, end, clip_w, clip_h))
                start = end
                if video_concat_mode == "sequential":
                    break
        except Exception as e:
            print(f"  跳过无效视频 {vp}: {e}")
            continue

    if video_concat_mode == "random":
        random.shuffle(subclips)

    # Step 2: 处理每个子片段（缩放、转场），写入临时文件
    processed = []  # list of (file_path, duration)
    video_duration = 0.0

    print(f"  处理 {len(subclips)} 个片段，需匹配音频时长 {audio_duration:.1f}s")

    for i, (vp, start, end, clip_w, clip_h) in enumerate(subclips):
        if video_duration >= audio_duration:
            break

        try:
            clip = VideoFileClip(vp).subclipped(start, end)
            clip_dur = clip.duration

            # 缩放适配目标分辨率
            if clip_w != video_width or clip_h != video_height:
                clip_ratio = clip_w / clip_h
                target_ratio = video_width / video_height

                if abs(clip_ratio - target_ratio) < 0.01:
                    clip = clip.resized(new_size=(video_width, video_height))
                else:
                    if clip_ratio > target_ratio:
                        scale = video_width / clip_w
                    else:
                        scale = video_height / clip_h
                    new_w = int(clip_w * scale)
                    new_h = int(clip_h * scale)
                    bg = ColorClip(size=(video_width, video_height), color=(0, 0, 0)).with_duration(clip_dur)
                    resized = clip.resized(new_size=(new_w, new_h)).with_position("center")
                    clip = CompositeVideoClip([bg, resized])

            if clip.duration > max_clip_duration:
                clip = clip.subclipped(0, max_clip_duration)

            temp_path = os.path.join(output_dir, f"_clip_{i}.mp4")
            clip.write_videofile(temp_path, logger=None, fps=FPS, codec=VIDEO_CODEC)
            clip.close()

            processed.append((temp_path, clip.duration))
            video_duration += clip.duration

        except Exception as e:
            print(f"  处理片段 {i} 失败: {e}")
            continue

    # Step 3: 如果视频不够长，循环已有片段
    if video_duration < audio_duration and processed:
        print(f"  视频总长 {video_duration:.1f}s < 音频 {audio_duration:.1f}s，循环补充")
        base = list(processed)
        idx = 0
        while video_duration < audio_duration:
            p = base[idx % len(base)]
            processed.append(p)
            video_duration += p[1]
            idx += 1

    # Step 4: 逐段合并视频
    print(f"  合并 {len(processed)} 个片段...")
    if not processed:
        raise RuntimeError("没有可用的视频片段")

    if len(processed) == 1:
        shutil.copy(processed[0][0], output_path)
        for p, _ in processed:
            try:
                os.remove(p)
            except OSError:
                pass
        return output_path

    # 迭代合并
    merged = os.path.join(output_dir, "_merged.mp4")
    shutil.copy(processed[0][0], merged)

    for i, (p, _) in enumerate(processed[1:], 1):
        base_clip = VideoFileClip(merged)
        next_clip = VideoFileClip(p)
        merged_clip = concatenate_videoclips([base_clip, next_clip])

        next_merged = os.path.join(output_dir, f"_merged_next.mp4")
        merged_clip.write_videofile(
            filename=next_merged,
            threads=threads,
            logger=None,
            temp_audiofile_path=output_dir,
            audio_codec=AUDIO_CODEC,
            fps=FPS,
        )
        base_clip.close()
        next_clip.close()
        merged_clip.close()

        os.remove(merged)
        os.rename(next_merged, merged)

    os.rename(merged, output_path)

    # 清理临时文件
    for p, _ in processed:
        try:
            os.remove(p)
        except OSError:
            pass

    return output_path


def compose_final_video(
    video_path: str,
    audio_path: str,
    subtitle_path: str,
    output_path: str,
    aspect: Tuple[int, int] = (1080, 1920),
    font_path: str = "",
    font_size: int = 60,
    text_color: str = "#FFFFFF",
    stroke_color: str = "#000000",
    stroke_width: float = 1.5,
    subtitle_position: str = "bottom",
    voice_volume: float = 1.0,
    bgm_file: str = "",
    bgm_volume: float = 0.2,
    threads: int = 2,
):
    """
    最终合成：视频 + 字幕 + 语音 + BGM
    核心逻辑来自 MoneyPrinterTurbo generate_video()
    """
    video_width, video_height = aspect

    print(f"  合成视频: {video_width}x{video_height}")
    print(f"  视频源: {video_path}")
    print(f"  音频源: {audio_path}")
    print(f"  字幕: {subtitle_path}")
    print(f"  输出: {output_path}")

    output_dir = os.path.dirname(output_path) or "."

    if not font_path or not os.path.exists(font_path):
        font_path = get_font_path()
    print(f"  字体: {font_path}")

    # 字幕 textclip 工厂
    def _make_textclip(text):
        return TextClip(
            text=text,
            font=font_path,
            font_size=font_size,
            color=text_color,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
        )

    # 加载视频（去声）
    video_clip = VideoFileClip(video_path).without_audio()

    # 叠加字幕
    if subtitle_path and os.path.exists(subtitle_path):
        try:
            sub = SubtitlesClip(subtitles=subtitle_path, encoding="utf-8", make_textclip=_make_textclip)
            text_clips = []
            for item in sub.subtitles:
                (t_start, t_end), txt = item
                max_width = int(video_width * 0.9)
                wrapped, txt_height = wrap_text(txt, max_width, font_path, font_size)

                clip = TextClip(
                    text=wrapped,
                    font=font_path,
                    font_size=font_size,
                    color=text_color,
                    stroke_color=stroke_color,
                    stroke_width=stroke_width,
                )
                clip = clip.with_start(t_start)
                clip = clip.with_end(t_end)
                clip = clip.with_duration(t_end - t_start)

                if subtitle_position == "bottom":
                    clip = clip.with_position(("center", video_height * 0.92 - clip.h))
                elif subtitle_position == "top":
                    clip = clip.with_position(("center", video_height * 0.05))
                else:  # center
                    clip = clip.with_position(("center", "center"))

                text_clips.append(clip)

            video_clip = CompositeVideoClip([video_clip, *text_clips])
        except Exception as e:
            print(f"  字幕叠加警告: {e}")

    # 语音
    audio_clip = AudioFileClip(audio_path).with_effects([afx.MultiplyVolume(voice_volume)])

    # BGM
    if bgm_file and os.path.exists(bgm_file):
        try:
            bgm = AudioFileClip(bgm_file).with_effects([
                afx.MultiplyVolume(bgm_volume),
                afx.AudioFadeOut(3),
                afx.AudioLoop(duration=video_clip.duration),
            ])
            audio_clip = CompositeAudioClip([audio_clip, bgm])
        except Exception as e:
            print(f"  BGM 添加失败: {e}")

    video_clip = video_clip.with_audio(audio_clip)
    video_clip.write_videofile(
        output_path,
        audio_codec=AUDIO_CODEC,
        temp_audiofile_path=output_dir,
        threads=threads,
        logger=None,
        fps=FPS,
    )
    video_clip.close()


# ── 主入口 ─────────────────────────────────────────────────────────────────

def generate_video(
    topic: str = "默认主题",
    count: int = 1,
    voice: str = DEFAULT_VOICE,
    voice_rate: float = DEFAULT_VOICE_RATE,
    aspect_str: str = DEFAULT_VIDEO_ASPECT,
    subtitle_enabled: bool = True,
    with_bgm: bool = True,
    output_dir: str = "",
    video_source: str = "auto",  # auto | placeholder
):
    """
    核心函数：生成短视频

    流程:
    1. 为每个视频准备文案（基于 topic）
    2. edge-tts 合成语音 + 提取时间戳
    3. 生成 SRT 字幕
    4. 获取/生成视频素材
    5. 合并视频 + 音频（裁剪、缩放）
    6. 最终合成（字幕叠加 + BGM）
    """
    aspect = parse_aspect(aspect_str)
    if not output_dir:
        output_dir = tempfile.mkdtemp(prefix="money_printer_")
    os.makedirs(output_dir, exist_ok=True)

    fonts_available = bool(glob.glob(os.path.join(FONTS_DIR, "*")))
    songs_available = bool(glob.glob(os.path.join(SONGS_DIR, "*.mp3")))

    print(f"\n{'='*60}")
    print(f"  MoneyPrinterTurbo Lite")
    print(f"  主题: {topic}")
    print(f"  数量: {count}")
    print(f"  语音: {voice}")
    print(f"  比例: {aspect_str} ({aspect[0]}x{aspect[1]})")
    print(f"  输出目录: {output_dir}")
    print(f"  字体可用: {'✅' if fonts_available else '❌'}")
    print(f"  BGM 可用: {'✅' if songs_available else '❌'}")
    print(f"{'='*60}\n")

    results = []

    for idx in range(1, count + 1):
        print(f"\n--- 生成视频 #{idx} ---")

        # 1. 文案
        script = f"欢迎收看{topic}。{topic}是一个非常有趣的话题，让我们一起来探索它的魅力吧！在这个视频中，我们将深入了解{topic}的各个方面。希望你喜欢这个视频，记得点赞和关注哦！"
        print(f"  文案: {script[:60]}...")

        # 2. TTS 语音合成
        voice_path = os.path.join(output_dir, f"voice_{idx}.mp3")
        print(f"  合成语音...")
        sub_maker = synthesize_voice(script, voice, voice_rate, voice_path)
        print(f"  语音已保存: {voice_path}")

        # 3. 字幕
        subtitle_path = ""
        if subtitle_enabled:
            subtitle_path = os.path.join(output_dir, f"subtitle_{idx}.srt")
            generate_subtitle(sub_maker, script, subtitle_path)
            print(f"  字幕已生成: {subtitle_path}")

        # 4. 素材
        video_paths = get_local_videos(count=5)
        if not video_paths or video_source == "placeholder":
            print(f"  生成占位素材 ({'强制占位' if video_source == 'placeholder' else '无本地素材'})...")
            video_paths = generate_placeholder_videos(
                output_dir, count=5, aspect=aspect, duration=DEFAULT_CLIP_DURATION
            )
        else:
            print(f"  使用 {len(video_paths)} 个本地素材")

        # 5. 合并视频 + 音频
        combined_path = os.path.join(output_dir, f"combined_{idx}.mp4")
        print(f"  合成视频片段...")
        combine_videos(
            video_paths=video_paths,
            audio_path=voice_path,
            output_path=combined_path,
            aspect=aspect,
            max_clip_duration=DEFAULT_CLIP_DURATION,
        )

        # 6. 最终合成（字幕 + BGM）
        final_path = os.path.join(output_dir, f"final_{idx}.mp4")
        bgm = get_bgm_file() if with_bgm else ""
        compose_final_video(
            video_path=combined_path,
            audio_path=voice_path,
            subtitle_path=subtitle_path,
            output_path=final_path,
            aspect=aspect,
            font_path=get_font_path(),
            bgm_file=bgm,
        )

        results.append(final_path)
        print(f"  ✅ 视频 #{idx}: {final_path}")

    print(f"\n{'='*60}")
    print(f"  完成! 生成了 {len(results)} 个视频:")
    for r in results:
        size = os.path.getsize(r) / (1024 * 1024)
        print(f"    {r} ({size:.1f} MB)")
    print(f"{'='*60}")

    return results


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="MoneyPrinterTurbo Lite — 轻量级短视频批量生成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            示例:
              python money_printer.py --topic "春天的花海" --count 1
              python money_printer.py --topic "AI Technology" --count 2 --voice "en-US-AriaNeural" --aspect "16:9"
              python money_printer.py --topic "摄影技巧" --no-bgm --no-subtitle
              python money_printer.py --topic "测试" --source placeholder
        """),
    )
    parser.add_argument("--topic", "-t", default="默认主题", help="视频主题")
    parser.add_argument("--count", "-c", type=int, default=1, help="生成视频数量 (默认: 1)")
    parser.add_argument("--voice", "-v", default=DEFAULT_VOICE, help="edge-tts 语音名称 (默认: zh-CN-XiaoxiaoNeural)")
    parser.add_argument("--rate", type=float, default=DEFAULT_VOICE_RATE, help="语速倍率 (默认: 1.0)")
    parser.add_argument("--aspect", "-a", default=DEFAULT_VIDEO_ASPECT, help="画面比例 (默认: 9:16)")
    parser.add_argument("--output", "-o", default="", help="输出目录 (默认: 临时目录)")
    parser.add_argument("--no-subtitle", action="store_true", help="禁用字幕")
    parser.add_argument("--no-bgm", action="store_true", help="禁用背景音乐")
    parser.add_argument("--source", choices=["auto", "placeholder"], default="auto",
                        help="素材来源: auto(本地优先) / placeholder(纯占位图)")
    parser.add_argument("--list-voices", action="store_true", help="列出常用 edge-tts 语音")

    args = parser.parse_args()

    if args.list_voices:
        print("常用 edge-tts 中文语音:")
        voices = [
            "zh-CN-XiaoxiaoNeural (女)",
            "zh-CN-XiaoyiNeural (女)",
            "zh-CN-YunyangNeural (男)",
            "zh-CN-YunxiNeural (男)",
            "zh-CN-XiaoxiaoMultilingualNeural (女,多语)",
            "en-US-AriaNeural (女,美式)",
            "en-US-GuyNeural (男,美式)",
            "en-GB-SoniaNeural (女,英式)",
            "ja-JP-NanamiNeural (女,日语)",
        ]
        for v in voices:
            print(f"  {v}")
        return

    generate_video(
        topic=args.topic,
        count=args.count,
        voice=args.voice,
        voice_rate=args.rate,
        aspect_str=args.aspect,
        subtitle_enabled=not args.no_subtitle,
        with_bgm=not args.no_bgm,
        output_dir=args.output,
        video_source=args.source,
    )


if __name__ == "__main__":
    main()
