#!/usr/bin/env python3
"""
墨麟视频生成器 v2.5 — 多后端自动降级
支持:
  1. DashScope HappyHorse-1.0-T2V (百炼文生视频，异步任务模式)
  2. moviepy+ffmpeg 本地幻灯片视频 (轻量级，无额外依赖)
  3. MoneyPrinterTurbo (本地部署，需启动服务)

用法:
  python video_generator.py "话题" [时长]
  python video_generator.py --check  # 检查各后端状态
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

# ── v2.5: 自动加载 .env ──
try:
    from molib.shared.env_loader import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── 配置 ──────────────────────────────────────────────────────────

BASE_DIR = Path.home() / "hermes-os"
FORK_REPOS_DIR = BASE_DIR / "fork_repos"
MPT_DIR = FORK_REPOS_DIR / "MoneyPrinterTurbo"

MPT_API_BASE = os.environ.get("MPT_API_BASE", "http://localhost:8899")

DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE = "https://dashscope.aliyuncs.com"

# v2.5: 后端顺序（HappyHorse云 → moviepy本地 → MPT本地）
BACKENDS = ["happyhorse", "moviepy_slideshow", "mpt"]

OUTPUT_DIR = "/tmp/hermes-videos"
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


# ── 后端 1: DashScope HappyHorse ─────────────────────────────────


def _check_happyhorse() -> bool:
    """检查 HappyHorse API 是否可用（API Key 存在）"""
    return bool(DASHSCOPE_API_KEY)


def _call_happyhorse(prompt: str, duration: int = 5,
                     size: str = "1280*720") -> Optional[str]:
    """
    通过 DashScope API 调用 HappyHorse 文生视频。
    异步任务模式：提交 → 轮询任务状态 → 返回视频URL。

    Args:
        prompt: 视频描述
        duration: 视频时长（秒）
        size: 分辨率

    Returns:
        视频文件路径，失败返回 None
    """
    if not DASHSCOPE_API_KEY:
        return None

    print(f"  [happyhorse] 提交文生视频任务: {prompt[:50]}...")

    # Step 1: 提交视频生成任务
    payload = json.dumps({
        "model": "happyhorse-1.0-t2v",
        "input": {"prompt": prompt},
        "parameters": {
            "duration": duration,
            "size": size,
        },
    }, ensure_ascii=False)

    cmd = [
        "curl", "-s", "-w", "\n%{http_code}",
        f"{DASHSCOPE_BASE}/api/v1/services/aigc/video-generation/video",
        "-H", f"Authorization: Bearer {DASHSCOPE_API_KEY}",
        "-H", "Content-Type: application/json",
        "-d", payload,
        "--connect-timeout", "10",
        "--max-time", "30",
    ]

    r = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
    lines = r.stdout.strip().split("\n")
    http_code = lines[-1].strip() if lines else "000"
    body = "\n".join(lines[:-1])

    if http_code != "200":
        print(f"  [happyhorse] ❌ HTTP {http_code}: {body[:200]}")
        return None

    try:
        resp = json.loads(body)
        task_id = resp.get("output", {}).get("task_id", "")
        if not task_id:
            print(f"  [happyhorse] ❌ 未返回 task_id: {body[:200]}")
            return None
    except json.JSONDecodeError:
        print(f"  [happyhorse] ❌ 响应非JSON: {body[:200]}")
        return None

    print(f"  [happyhorse] ✅ 任务已提交: task_id={task_id[:16]}...")

    # Step 2: 轮询任务状态（最多等 5 分钟）
    max_wait = 300
    poll_interval = 10
    waited = 0

    while waited < max_wait:
        time.sleep(poll_interval)
        waited += poll_interval
        print(f"  [happyhorse]  ⏳ 轮询中... ({waited}s)")

        status_cmd = [
            "curl", "-s",
            f"{DASHSCOPE_BASE}/api/v1/services/aigc/video-generation/video/task/{task_id}",
            "-H", f"Authorization: Bearer {DASHSCOPE_API_KEY}",
            "--connect-timeout", "5",
            "--max-time", "10",
        ]

        sr = subprocess.run(status_cmd, capture_output=True, text=True, timeout=15)
        if sr.returncode != 0:
            continue

        try:
            sdata = json.loads(sr.stdout)
            status = sdata.get("output", {}).get("task_status", "")
            if status == "SUCCEEDED":
                video_url = sdata.get("output", {}).get("video_url", "")
                if video_url:
                    print(f"  [happyhorse] ✅ 视频生成完成!")
                    return _download_video(video_url, f"happyhorse_{task_id[:8]}")
            elif status == "FAILED":
                err = sdata.get("output", {}).get("message", "未知错误")
                print(f"  [happyhorse] ❌ 生成失败: {err}")
                return None
            elif status == "CANCELED":
                print(f"  [happyhorse] ❌ 任务被取消")
                return None
        except (json.JSONDecodeError, KeyError):
            continue

    print(f"  [happyhorse] ⏰ 轮询超时（{max_wait}s）")
    return None


# ── 后端 2: moviepy+ffmpeg 本地幻灯片 ─────────────────────────────

def _check_moviepy_slideshow() -> bool:
    """检查 moviepy 和 ffmpeg 是否可用"""
    try:
        from moviepy import VideoFileClip  # noqa: F401
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False


def _call_moviepy_slideshow(
    prompt: str, duration: int = 5,
    size: str = "1280*720",
) -> Optional[str]:
    """
    本地幻灯片视频生成（无云端依赖）。

    流程: 纯色背景 + 文字标题 → mp4 视频。
    适合: 快速生成简单视频（标题卡/宣传片/课程封面）。
    """
    try:
        from moviepy import (
            ColorClip, TextClip, CompositeVideoClip,
        )
    except ImportError:
        print("  [moviepy] ⚠️ moviepy 未安装 (pip install moviepy)")
        return None

    try:
        w, h = (int(x) for x in size.split("*"))
    except (ValueError, AttributeError):
        w, h = 1280, 720

    output_path = f"{OUTPUT_DIR}/slideshow_{int(time.time())}.mp4"

    print(f"  [moviepy] 🎨 生成幻灯片视频: {prompt[:50]}...")

    try:
        # 背景色
        bg = ColorClip(size=(w, h), color=(15, 25, 50), duration=duration)

        # 标题文字
        title_text = prompt[:80]
        title = (
            TextClip(
                text=title_text,
                font_size=min(60, int(w / 18)),
                color="white",
                font="PingFang-SC-Regular",
                size=(int(w * 0.85), None),
                method="caption",
            )
            .with_position("center")
            .with_duration(duration)
        )

        # 副标题
        subtitle = (
            TextClip(
                text="墨麟OS · AI 自动生成",
                font_size=24,
                color="rgba(200,168,75,0.8)",
                font="PingFang-SC-Regular",
            )
            .with_position(("center", h - 60))
            .with_duration(duration)
        )

        video = CompositeVideoClip([bg, title, subtitle])
        video.write_videofile(
            output_path, fps=24, codec="libx264",
            audio_codec="aac", logger=None,
        )
        video.close()

        if Path(output_path).exists():
            print(f"  [moviepy] ✅ 幻灯片视频完成: {output_path}")
            return output_path

    except Exception as e:
        # 降级到 ffmpeg
        print(f"  [moviepy] ⚠️ MoviePy失败 ({e})，降级 ffmpeg...")
        return _call_ffmpeg_slideshow(prompt, duration, size, output_path)

    return None


def _call_ffmpeg_slideshow(
    prompt: str, duration: int, size: str, output_path: str
) -> Optional[str]:
    """ffmpeg 纯命令行版本（moviepy 降级方案）"""
    try:
        w, h = (int(x) for x in size.split("*"))
    except (ValueError, AttributeError):
        w, h = 1280, 720

    safe_title = prompt[:60].replace("'", "'\\\\''")

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=0x0F1932:s={w}x{h}:d={duration},"
              f"drawtext=text='{safe_title}':"
              f"fontsize={min(48, int(w/20))}:"
              f"fontcolor=white:"
              f"x=(w-text_w)/2:y=(h-text_h)/2-40,"
              f"drawtext=text='墨麟OS · AI生成':"
              f"fontsize=20:fontcolor=#c8a84b:"
              f"x=(w-text_w)/2:y=h-th-50",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-an",
        output_path,
    ]

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if Path(output_path).exists() and Path(output_path).stat().st_size > 1024:
            print(f"  [ffmpeg] ✅ 幻灯片视频完成: {output_path}")
            return output_path
    except Exception as e:
        print(f"  [ffmpeg] ❌ {e}")

    return None


# ── 后端 3: MoneyPrinterTurbo ────────────────────────────────────


def _check_mpt() -> bool:
    """检查 MPT 是否已部署且服务运行"""
    if not (MPT_DIR.exists() and (MPT_DIR / "app.py").exists()):
        return False
    try:
        cmd = ["curl", "-s", "--connect-timeout", "5", "--max-time", "10",
               f"{MPT_API_BASE}/health"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return r.returncode == 0
    except Exception:
        return False


def _call_mpt(prompt: str, duration: str = "60s") -> Optional[str]:
    """调用 MPT API 生成视频"""
    payload = json.dumps({
        "topic": prompt,
        "duration": duration,
        "style": "科技感",
        "resolution": "1920x1080",
        "bgm_type": "auto",
        "subtitle_enabled": True,
    }, ensure_ascii=False)

    cmd = [
        "curl", "-s", "-w", "\n%{http_code}",
        "-X", "POST",
        f"{MPT_API_BASE}/api/v1/video",
        "-H", "Content-Type: application/json",
        "-d", payload,
        "--connect-timeout", "10",
        "--max-time", "600",
    ]

    r = subprocess.run(cmd, capture_output=True, text=True, timeout=610)
    lines = r.stdout.strip().split("\n")
    http_code = lines[-1].strip() if lines else "000"
    body = "\n".join(lines[:-1])

    if http_code != "200":
        print(f"  [mpt] ❌ HTTP {http_code}: {body[:200]}")
        return None

    try:
        resp = json.loads(body)
        video_path = resp.get("data", {}).get("video_url",
                       resp.get("video_path", ""))
        return video_path or body.strip()
    except json.JSONDecodeError:
        return body.strip()


# ── 通用工具 ──────────────────────────────────────────────────────


def _download_video(url: str, prefix: str = "video") -> Optional[str]:
    """下载视频文件到本地"""
    output = f"{OUTPUT_DIR}/{prefix}_{int(time.time())}.mp4"
    cmd = ["curl", "-s", "-o", output, "-L", url,
           "--connect-timeout", "30", "--max-time", "120"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=130)
    if r.returncode == 0 and Path(output).exists() and Path(output).stat().st_size > 0:
        print(f"  [download] ✅ 保存到 {output} ({Path(output).stat().st_size / 1024:.0f}KB)")
        return output
    print(f"  [download] ❌ 下载失败")
    return None


# ── 主接口 ────────────────────────────────────────────────────────


def generate_video(topic: str, duration: str = "60s") -> dict:
    """
    多后端自动降级视频生成。

    Args:
        topic: 视频主题/文案
        duration: 时长（如 "60s" 或秒数）

    Returns:
        {"success": bool, "video_path": str|None, "backend": str, "message": str}
    """
    print(f"🎬 墨麟视频生成器")
    print(f"   话题: {topic}")
    print(f"   时长: {duration}")
    print("=" * 50)

    # 解析秒数
    dur_seconds = 5
    if duration.endswith("s"):
        try:
            dur_seconds = int(duration[:-1])
        except ValueError:
            pass
    else:
        try:
            dur_seconds = int(duration)
        except ValueError:
            pass
    dur_seconds = min(max(dur_seconds, 5), 60)  # 5-60s

    for backend in BACKENDS:
        print(f"\n🔄 尝试后端: {backend}")
        if backend == "happyhorse":
            if not _check_happyhorse():
                print(f"   [happyhorse] ⚠️  DASHSCOPE_API_KEY 未配置")
                continue
            video_path = _call_happyhorse(topic, duration=dur_seconds)
        elif backend == "moviepy_slideshow":
            if not _check_moviepy_slideshow():
                print(f"   [moviepy] ⚠️  moviepy/ffmpeg 不可用")
                continue
            video_path = _call_moviepy_slideshow(topic, duration=dur_seconds)
        elif backend == "mpt":
            if not _check_mpt():
                print(f"   [mpt] ⚠️  MPT 未部署或未运行")
                continue
            video_path = _call_mpt(topic, duration=duration)

        if video_path:
            print(f"\n✅ 视频生成成功! (后端: {backend})")
            print(f"   路径: {video_path}")
            return {
                "success": True,
                "video_path": video_path,
                "backend": backend,
                "message": f"视频生成成功 ({backend})",
            }
        print(f"   [info] {backend} 失败，尝试下一后端...")

    msg = "所有后端均不可用:\n"
    if not _check_happyhorse():
        msg += "  - HappyHorse: DASHSCOPE_API_KEY 未配置\n"
    if not _check_moviepy_slideshow():
        msg += "  - moviepy: pip install moviepy && brew install ffmpeg\n"
    if not _check_mpt():
        msg += "  - MPT: 本地服务未运行\n"
    msg += "\n💡 推荐: HappyHorse(云端) > moviepy(本地轻量) > MPT(本地重服务)"

    print(f"\n❌ {msg}")
    return {"success": False, "video_path": None, "backend": "none", "message": msg}


def check_status() -> dict:
    """检查所有后端状态"""
    print("📊 视频生成后端状态检查")
    print("=" * 40)
    for backend in BACKENDS:
        if backend == "happyhorse":
            ok = _check_happyhorse()
            print(f"  HappyHorse (百炼云): {'✅' if ok else '❌'} Key={DASHSCOPE_API_KEY[:8]}...")
        elif backend == "moviepy_slideshow":
            ok = _check_moviepy_slideshow()
            print(f"  moviepy幻灯片 (本地): {'✅' if ok else '❌'} 零依赖本地生成")
        elif backend == "mpt":
            ok = _check_mpt()
            print(f"  MPT (本地服务): {'✅' if ok else '❌'} {MPT_API_BASE}")
    return {
        "happyhorse": _check_happyhorse(),
        "moviepy_slideshow": _check_moviepy_slideshow(),
        "mpt": _check_mpt(),
    }


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python video_generator.py <话题> [时长]")
        print("  python video_generator.py 'AI Agent入门教程'")
        print("  python video_generator.py 'Python数据分析' 120s")
        print("  python video_generator.py --check")
        sys.exit(1)

    if sys.argv[1] == "--check":
        check_status()
        return

    topic = sys.argv[1]
    duration = sys.argv[2] if len(sys.argv) > 2 else "60s"
    result = generate_video(topic, duration)

    if result["success"]:
        print(f"\n✅ 完成！使用后端: {result['backend']}")
    else:
        print(f"\n❌ 失败: {result['message']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
