"""
Pixelle-Video Pipeline — 轻量级 CPU 可运行版
============================================

从 AIDC-AI/Pixelle-Video (10.7K⭐) 提取的管线设计模式:

  Topic ─→ LLM ─→ Script + Prompts ─→ edge-tts ─→ Images ─→ FFmpeg ─→ 视频
        ① 脚本生成         ② 图片提示词     ③ TTS语音      ④ 图→视频片段
                                                           ⑤ 拼接+BGM

依赖: edge-tts, pillow, httpx + FFmpeg(系统命令)   |   不依赖: ComfyUI, moviepy, GPU

Usage:
    import asyncio
    from molib.video.pixelle_pipeline import gen_video
    path = asyncio.run(gen_video("AI 时代的学习方法", style="minimal"))
"""

import asyncio, json, os, re, subprocess, tempfile, textwrap, time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional
from PIL import Image, ImageDraw, ImageFont

# =============================================================================
# 配置
# =============================================================================
DEFAULT_WIDTH, DEFAULT_HEIGHT, DEFAULT_FPS = 1080, 1920, 24
DEFAULT_N_SCENES = 5
DEFAULT_NARR_MIN, DEFAULT_NARR_MAX = 8, 25
OUTPUT_DIR = Path.home() / "hermes-os" / "relay" / "videos"
BAILIAN_API_KEY = os.environ.get("BAILIAN_API_KEY", "")
BAILIAN_MODEL = "qwen-image-2.0-pro"
DEFAULT_TTS_VOICE = "zh-CN-YunjianNeural"
DEFAULT_TTS_RATE = "+15%"

STYLE_DESCS = {
    "minimal": "简洁现代有洞察力",
    "story": "叙事性强用故事打动人心",
    "educational": "知识科普风格逻辑清晰",
    "motivational": "激励人心有感染力",
    "humorous": "幽默风趣轻松活泼",
}

# =============================================================================
# 数据模型
# =============================================================================
@dataclass
class VideoProject:
    topic: str
    style: str = "minimal"
    n_scenes: int = DEFAULT_N_SCENES
    width: int = DEFAULT_WIDTH
    height: int = DEFAULT_HEIGHT
    fps: int = DEFAULT_FPS
    title: str = ""
    narrations: List[str] = field(default_factory=list)
    image_prompts: List[str] = field(default_factory=list)
    image_paths: List[str] = field(default_factory=list)
    audio_paths: List[str] = field(default_factory=list)
    output_path: str = ""

    @property
    def work_dir(self) -> Path:
        safe = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff_-]', '_', self.topic)[:20]
        return OUTPUT_DIR / f"{int(time.time())}_{safe}"


# =============================================================================
# 1. 脚本生成 — Topic → [narrations, title]
# =============================================================================
# 借用 Pixelle 的 TOPIC_NARRATION_PROMPT 设计模式:
#   - LLM 接收 topic + n_scenes + min/max_words
#   - 输出 JSON: {"title": "...", "narrations": ["...", ...]}
#   - 每段自然口语化，形成完整观点表达链

SCRIPT_PROMPT = textwrap.dedent("""\
你是一位短视频脚本专家。根据主题生成 {n} 段解说词。

要求:
- 每段 {min_w}~{max_w} 字, 自然口语化, 像朋友聊天
- 各段递进: 引人注意→提出观点→深入解释→带来启发
- 段落结尾不要标点
- 风格: {style_desc}

主题: {topic}

仅输出JSON:
```json
{{"title": "标题(≤15字)", "narrations": ["段1", "段2", ...]}}
```""")

FALLBACKS = {
    "默认": {"title": "一个值得思考的话题", "narrations": [
        "今天我们来聊一个值得深思的话题",
        "很多时候我们被惯性思维束缚了想象力",
        "试着换个角度你会发现不一样的风景",
        "行动比空想更重要哪怕是微小的一步",
        "希望这个视频能给你带来一些启发",
    ]},
}


async def _llm(prompt: str, temperature=0.7, max_tokens=2000) -> str:
    """通用 LLM 调用 (OpenAI 兼容 API)"""
    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("需要设置 OPENROUTER_API_KEY 或 DEEPSEEK_API_KEY")
    base = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1")
    model = os.environ.get("LLM_MODEL", "deepseek-chat")
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(f"{base}/chat/completions", headers={
            "Authorization": f"Bearer {api_key}", "Content-Type": "application/json",
        }, json={"model": model, "messages": [{"role": "user", "content": prompt}],
                 "max_tokens": max_tokens, "temperature": temperature})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()


def _parse_json(text: str) -> dict:
    """从 LLM 回复提取 JSON (兼容 markdown 代码块)"""
    for p in [lambda t: json.loads(t),
              lambda t: json.loads(re.search(r'```(?:json)?\s*([\s\S]*?)```', t).group(1)),
              lambda t: json.loads(re.search(r'\{[^{}]*(?:"title"|"narrations")[^{}]*\}', t).group())]:
        try:
            return p(text)
        except (json.JSONDecodeError, AttributeError):
            continue
    raise ValueError(f"无法解析 JSON: {text[:200]}...")


async def generate_script(p: VideoProject, cb=None) -> VideoProject:
    """Step 1: Topic → narrations + title (LLM, 降级到 fallback)"""
    if cb: cb("generating_script", 0.05)
    prompt = SCRIPT_PROMPT.format(
        n=p.n_scenes, min_w=DEFAULT_NARR_MIN, max_w=DEFAULT_NARR_MAX,
        style_desc=STYLE_DESCS.get(p.style, STYLE_DESCS["minimal"]), topic=p.topic)
    try:
        d = _parse_json(await _llm(prompt, temperature=0.8))
        p.title, p.narrations = d.get("title", "")[:15], d.get("narrations", [])[:p.n_scenes]
        if not p.narrations: raise ValueError("empty")
    except Exception as e:
        print(f"  ⚠ LLM 失败 ({e}), 用 fallback")
        fb = next((v for k, v in FALLBACKS.items() if k in p.topic), FALLBACKS["默认"])
        p.title, p.narrations = fb["title"], fb["narrations"][:p.n_scenes]
    if cb: cb("generating_script", 0.10)
    return p


# =============================================================================
# 2. 图片提示词 — Narrations → Image Prompts
# =============================================================================
async def generate_image_prompts(p: VideoProject, cb=None) -> VideoProject:
    """Step 2: 每段解说词 → 图片提示词 (复用 Pixelle image_generation.py 风格)"""
    if cb: cb("image_prompts", 0.15)
    # 使用 Pixelle 默认 stick_figure 风格提示词模板
    p.image_prompts = [
        f"stick figure style sketch, black and white lines, pure white background, "
        f"a scene representing: {n[:30]}, minimalist hand-drawn feel, clear composition"
        for n in p.narrations
    ]
    if cb: cb("image_prompts", 0.20)
    return p


# =============================================================================
# 3. 图片生成 — 百炼 API / Pillow 占位图
# =============================================================================
async def _bailian_img(prompt: str, w: int, h: int) -> Optional[bytes]:
    """百炼 API 生图 (异步轮询)"""
    if not BAILIAN_API_KEY: return None
    async with httpx.AsyncClient(timeout=120) as c:
        try:
            r = await c.post("https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis",
                headers={"Authorization": f"Bearer {BAILIAN_API_KEY}", "Content-Type": "application/json",
                         "X-DashScope-Async": "enable"},
                json={"model": BAILIAN_MODEL, "input": {"prompt": prompt}, "parameters": {"size": f"{w}x{h}", "n": 1}})
            r.raise_for_status()
            tid = r.json().get("output", {}).get("task_id", "")
            for _ in range(30):
                await asyncio.sleep(2)
                sr = await c.get(f"https://dashscope.aliyuncs.com/api/v1/tasks/{tid}",
                                 headers={"Authorization": f"Bearer {BAILIAN_API_KEY}"})
                if sr.status_code != 200: continue
                st = sr.json().get("output", {}).get("task_status", "")
                if st == "SUCCEEDED":
                    url = sr.json().get("output", {}).get("results", [{}])[0].get("url")
                    if url: return (await c.get(url)).content
                elif st in ("FAILED", "CANCELED"): return None
        except Exception: return None


def _placeholder_img(prompt: str, idx: int, w: int, h: int, path: Path) -> str:
    """Pillow 占位图 — 继承 Pixelle 的 stick_figure 极简黑白风格"""
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", w // 25)
    except: font = ImageFont.load_default()
    m = w // 10
    draw.rectangle([m, m, w - m, h - m], outline="black", width=3)
    cx, cy, r = w // 2, h // 3, min(w, h) // 6
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline="black", width=3)
    draw.line([cx, cy + r, cx, cy + 3 * r], fill="black", width=3)
    draw.line([cx, cy + 2 * r, cx - r, cy + 3 * r], fill="black", width=3)
    draw.line([cx, cy + 2 * r, cx + r, cy + 3 * r], fill="black", width=3)
    fp = path / f"frame_{idx:04d}.png"
    img.save(str(fp)); return str(fp)


async def generate_images(p: VideoProject, cb=None) -> VideoProject:
    """Step 3: Image Prompts → 图片文件 (百炼 API 降级到 Pillow)"""
    p.work_dir.mkdir(parents=True, exist_ok=True)
    for i, pr in enumerate(p.image_prompts):
        if cb: cb("images", 0.25 + (i / len(p.image_prompts)) * 0.25)
        data = await _bailian_img(pr, p.width, p.height)
        if data:
            fp = p.work_dir / f"frame_{i:04d}.png"
            with open(fp, "wb") as f: f.write(data)
            p.image_paths.append(str(fp))
        else:
            p.image_paths.append(_placeholder_img(pr, i, p.width, p.height, p.work_dir))
    if cb: cb("images", 0.50)
    return p


# =============================================================================
# 4. TTS 语音 — edge-tts (纯 CPU)
# =============================================================================
async def _tts(text: str, voice: str, rate: str, out: str) -> str:
    """edge-tts 调用 (含重试机制, 源自 Pixelle tts_util.py 设计)"""
    import edge_tts as et
    for at in range(3):
        try:
            chunks, comm = [], et.Communicate(text=text, voice=voice, rate=rate)
            async for c in comm.stream():
                if c["type"] == "audio": chunks.append(c["data"])
            with open(out, "wb") as f: f.write(b"".join(chunks))
            return out
        except Exception as e:
            if at < 2: await asyncio.sleep(1.5 * (at + 1))
            else: raise


def _silent_audio(path: str, dur=3.0):
    """FFmpeg 静音 fallback"""
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono",
                    "-t", str(dur), "-acodec", "libmp3lame", path], capture_output=True)


async def generate_audio(p: VideoProject, cb=None) -> VideoProject:
    """Step 4: Narrations → MP3 (edge-tts, 失败降级到静音)"""
    p.work_dir.mkdir(parents=True, exist_ok=True)
    for i, n in enumerate(p.narrations):
        if cb: cb("audio", 0.55 + (i / len(p.narrations)) * 0.15)
        ap = str(p.work_dir / f"audio_{i:04d}.mp3")
        try:
            await _tts(n, DEFAULT_TTS_VOICE, DEFAULT_TTS_RATE, ap)
            p.audio_paths.append(ap)
        except Exception as e:
            print(f"  ⚠ TTS 失败 ({e}), 用静音")
            _silent_audio(ap); p.audio_paths.append(ap)
    if cb: cb("audio", 0.70)
    return p


# =============================================================================
# 5. 视频合成 — FFmpeg 图片序列 + 音频 → 最终视频
# =============================================================================
def _segment(img: str, aud: str, out: str, fps: int = 24):
    """图片+音频 → 视频片段 (等价 Pixelle VideoService.create_video_from_image)"""
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", img, "-i", aud,
                    "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p",
                    "-shortest", "-vf", f"fps={fps}", out], check=True, capture_output=True)


def _concat(paths: List[str], out: str):
    """视频片段拼接 (等价 Pixelle VideoService._concat_demuxer)"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        for v in paths: f.write(f"file '{Path(v).resolve()}'\n")
        fl = f.name
    try:
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                        "-i", fl, "-c", "copy", out], check=True, capture_output=True)
    finally: os.unlink(fl)


def _add_bgm(video: str, bgm: Optional[str], out: str, vol=0.15):
    """添加BGM (等价 Pixelle VideoService._add_bgm_to_video)"""
    if not bgm or not os.path.exists(bgm):
        subprocess.run(["cp", video, out], check=True); return
    subprocess.run(["ffmpeg", "-y", "-i", video, "-i", bgm,
                    "-filter_complex", f"[1:a]volume={vol}[bgm];[0:a][bgm]amix=inputs=2:duration=first[outa]",
                    "-map", "0:v", "-map", "[outa]", "-c:v", "copy", "-c:a", "aac",
                    "-shortest", out], check=True, capture_output=True)


async def compose_video(p: VideoProject, bgm: Optional[str] = None, cb=None) -> VideoProject:
    """Step 5: 图片+音频 → 片段 → 拼接 → BGM → 最终视频"""
    p.work_dir.mkdir(parents=True, exist_ok=True)
    seg_dir = p.work_dir / "segments"; seg_dir.mkdir(exist_ok=True)
    segs = []
    for i, (img, aud) in enumerate(zip(p.image_paths, p.audio_paths)):
        if cb: cb("compose", 0.75 + (i / len(p.image_paths)) * 0.15)
        sp = str(seg_dir / f"seg_{i:04d}.mp4")
        _segment(img, aud, sp, p.fps); segs.append(sp)
    if cb: cb("compose", 0.90)
    raw = str(p.work_dir / "raw.mp4")
    if len(segs) == 1: subprocess.run(["cp", segs[0], raw], check=True)
    else: _concat(segs, raw)
    if cb: cb("compose", 0.95)
    final = str(p.work_dir / "final.mp4")
    _add_bgm(raw, bgm, final)
    p.output_path = final
    for f in [raw] if os.path.exists(raw) else []: os.unlink(f)
    if cb: cb("compose", 1.0)
    return p


# =============================================================================
# 主入口
# =============================================================================
async def gen_video(
    topic: str,
    style: str = "minimal",
    n_scenes: int = DEFAULT_N_SCENES,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    fps: int = DEFAULT_FPS,
    bgm_path: Optional[str] = None,
    progress_callback: Optional[Callable[[str, float], None]] = None,
    bailian_api_key: Optional[str] = None,
) -> str:
    """
    全自动视频生成管线 (Pixelle-Video 设计模式提取)

    参数:
        topic: 视频主题
        style: 风格 (minimal/story/educational/motivational/humorous)
        n_scenes: 场景数 (默认5)
        width/height: 分辨率 (默认1080x1920竖屏)
        fps: 帧率 (默认24)
        bgm_path: 背景音乐路径
        progress_callback: 进度回调 fn(phase, 0~1)
        bailian_api_key: 百炼API Key

    返回: 最终视频文件路径

    管线:
        ① generate_script()    — Topic → LLM → Script
        ② generate_image_prompts() — Narrations → Image Prompts
        ③ generate_images()    — Prompts → 图片 (百炼API/Pillow)
        ④ generate_audio()     — Narrations → MP3 (edge-tts)
        ⑤ compose_video()      — 图片+音频 → FFmpeg → 视频
    """
    global BAILIAN_API_KEY
    if bailian_api_key: BAILIAN_API_KEY = bailian_api_key
    import shutil
    if not shutil.which("ffmpeg"):
        raise RuntimeError("需要安装 FFmpeg: apt-get install ffmpeg")

    p = VideoProject(topic=topic, style=style, n_scenes=n_scenes,
                     width=width, height=height, fps=fps)
    print(f"🎬 Pixelle 管线 | 主题: {topic} | 风格: {style} | 场景: {n_scenes}")

    p = await generate_script(p, progress_callback)
    print(f"  📝 标题: {p.title}")
    for i, n in enumerate(p.narrations): print(f"     {i+1}. {n}")

    p = await generate_image_prompts(p, progress_callback)
    p = await generate_images(p, progress_callback)
    p = await generate_audio(p, progress_callback)
    p = await compose_video(p, bgm_path, progress_callback)

    print(f"\n✅ 视频已生成: {p.output_path}")
    return p.output_path


if __name__ == "__main__":
    import sys
    topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "一个值得思考的话题"
    style = os.environ.get("PIXELLE_STYLE", "minimal")
    asyncio.run(gen_video(topic, style=style))
