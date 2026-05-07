# 墨播短视频模块 — 双引擎整合方案

## 1. 现状分析

### 1.1 molib 现有架构

- **Worker 文件**: `molib/agencies/workers/short_video.py`
- **CLI 入口**: `molib/__main__.py` — 目前 `video script` 命令映射到 ShortVideo Worker
- **Worker 基类**: `molib/agencies/workers/base.py` — `SubsidiaryWorker` 抽象类
- **当前状态**: short_video.py 只有 mock 实现，输出固定模板脚本

### 1.2 MoneyPrinterTurbo 安装状态

| 项目 | 状态 |
|------|------|
| 安装位置 | `/home/ubuntu/MoneyPrinterTurbo/` |
| 是否 pip 安装 | ❌ 未安装，是独立仓库（git clone） |
| 是否可导入 | ❌ 不能 `import`，需要 sys.path 注入或子进程调用 |
| config.toml | ❌ 不存在（只有 config.example.toml） |
| LLM 配置 | 未配置 API Key |
| 核心依赖 | FastAPI + uvicorn + moviepy + edge-tts |
| 当前端口 | 默认 8080 |

**MoneyPrinterTurbo 架构**:
```
main.py → app/asgi.py (FastAPI)
├── POST /videos          — 视频生成（全自动管线）
├── POST /subtitle        — 字幕生成
├── POST /audio           — 音频生成
├── GET  /tasks           — 任务查询
├── GET  /tasks/{id}      — 任务详情
└── app/services/task.py  — 核心管线
    ├── 1. generate_script()     — LLM 生成脚本
    ├── 2. generate_terms()      — LLM 生成搜索词
    ├── 3. generate_audio()      — edge-tts 配音
    ├── 4. generate_subtitle()   — 字幕生成
    ├── 5. get_video_materials() — Pexels 下载素材
    └── 6. generate_final_videos() — moviepy 合成
```

**核心入口函数**（可在 Python 中直接调用）:
```python
from app.services.task import start
from app.models.schema import VideoParams

params = VideoParams(video_subject="主题", voice_name="zh-CN-XiaoyiNeural-Female")
result = start(task_id, params, stop_at="video")
# 返回: {script, terms, audio_file, audio_duration, subtitle_path, materials, videos}
```

### 1.3 Pixelle-Video 安装状态

| 项目 | 状态 |
|------|------|
| 安装位置 | `/home/ubuntu/pixelle-video/` |
| 是否 pip 安装 | ❌ 未安装（`pip show pixelle-video` 无结果） |
| 是否可导入 | ✅ 可以 `from pixelle_video import pixelle_video`（需 sys.path） |
| config.yaml | ❌ 不存在（只有 config.example.yaml） |
| LLM 配置 | 未配置 API Key |
| ComfyUI 配置 | 未配置（默认连 localhost:8188） |
| 核心依赖 | fastmcp + comfykit + moviepy + edge-tts + streamlit |
| pyproject.toml | 定义 CLI: `pixelle-video` / `pvideo` → `pixelle_video.cli:main` |

**注意**: `pixelle_video/cli.py` 文件不存在！pyproject.toml 中声明的 CLI 入口尚未实现。必须通过 Python API 调用。

**Pixelle-Video 架构**:
```
pixelle_video/PixelleVideoCore (全局实例 pixelle_video)
├── initialize() — 初始化所有服务
├── generate_video(text, pipeline="standard", **kwargs) — 全自动视频生成
├── pipelines
│   ├── standard     — 通用短视频管线
│   ├── custom       — 自定义模板
│   └── asset_based  — 自定义素材
├── llm              — LLM 服务（OpenAI SDK）
├── tts              — TTS 服务（ComfyKit）
├── media            — 图片/视频生成（ComfyKit）
└── video            — 视频合成（moviepy）
```

## 2. 整合方案

### 2.1 统一原则

1. **仓库独立**: MoneyPrinterTurbo 和 Pixelle-Video 保持完整 git 仓库，不做代码合并
2. **Worker 封装**: 通过 `short_video.py` Worker 封装两个引擎，通过 `--engine mpt|pixelle` 参数选择
3. **配置独立**: 两个引擎使用各自的配置文件（config.toml / config.yaml），Worker 只传递参数
4. **路径约定**: 引擎路径通过常量或环境变量设定，不硬编码

### 2.2 文件修改清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `molib/agencies/workers/short_video.py` | **重写** | 添加双引擎支持 |
| `molib/__main__.py` | **修改** | 添加 `video generate` 子命令 |
| 新建: `molib/agencies/workers/short_video_engines.py` | **新建** | 双引擎调用实现 |
| 新建: `config/short_video.toml` | **新建** | 引擎路径与默认参数配置 |

### 2.3 核心代码设计

#### 2.3.1 配置 (`config/short_video.toml`)

```toml
[engine]
default = "mpt"  # "mpt" | "pixelle"

[mpt]
repo_path = "/home/ubuntu/MoneyPrinterTurbo"
host = "127.0.0.1"
port = 8080
use_api = true  # true=通过HTTP API调用, false=直接import调用

[pixelle]
repo_path = "/home/ubuntu/pixelle-video"
```

#### 2.3.2 引擎封装层 (`short_video_engines.py`)

```python
"""短视颜双引擎封装层"""

import sys, json, os
from pathlib import Path
from typing import Optional

# ──────────────────── MoneyPrinterTurbo 引擎 ────────────────────

class MPTEngine:
    """MoneyPrinterTurbo 引擎封装"""
    
    def __init__(self, repo_path: str = "/home/ubuntu/MoneyPrinterTurbo"):
        self.repo_path = Path(repo_path)
        self._ensure_on_path()
    
    def _ensure_on_path(self):
        """将 MPT 仓库加入 sys.path"""
        if str(self.repo_path) not in sys.path:
            sys.path.insert(0, str(self.repo_path))
    
    async def generate_video(
        self,
        topic: str,
        script: str = "",
        aspect: str = "9:16",
        voice: str = "zh-CN-XiaoyiNeural-Female",
        duration: int = 60,
        output_dir: Optional[str] = None,
    ) -> dict:
        """
        调用 MoneyPrinterTurbo 生成视频
        
        方法 A: 直接调用 task.start() (推荐)
        方法 B: 通过 HTTP API 调用 (需先启动服务)
        
        当前使用方法 A — 直接 Python 调用
        """
        from app.models.schema import VideoParams
        from app.services.task import start
        import uuid
        
        task_id = str(uuid.uuid4())
        params = VideoParams(
            video_subject=topic,
            video_script=script or "",
            video_aspect=aspect,
            voice_name=voice,
            video_clip_duration=5,
            video_count=1,
        )
        
        result = start(task_id, params, stop_at="video")
        return {
            "engine": "mpt",
            "task_id": task_id,
            "status": "success" if result and "videos" in result else "error",
            "video_path": result.get("videos", [None])[0] if result else None,
            "script": result.get("script", ""),
            "duration": result.get("audio_duration", 0),
            "raw": result,
        }


# ──────────────────── Pixelle-Video 引擎 ────────────────────

class PixelleEngine:
    """Pixelle-Video 引擎封装"""
    
    def __init__(self, repo_path: str = "/home/ubuntu/pixelle-video"):
        self.repo_path = Path(repo_path)
        self._ensure_on_path()
        self._core = None
    
    def _ensure_on_path(self):
        if str(self.repo_path) not in sys.path:
            sys.path.insert(0, str(self.repo_path))
    
    async def _get_core(self):
        if self._core is None:
            from pixelle_video import pixelle_video
            await pixelle_video.initialize()
            self._core = pixelle_video
        return self._core
    
    async def generate_video(
        self,
        topic: str,
        script: str = "",
        n_scenes: int = 5,
        mode: str = "generate",  # "generate" | "fixed"
        tts_voice: str = "zh-CN-YunjianNeural",
        aspect: str = "1080x1920",
    ) -> dict:
        """
        调用 Pixelle-Video 生成视频
        """
        core = await self._get_core()
        
        result = await core.generate_video(
            text=script or topic,
            pipeline="standard",
            mode=mode if not script else "fixed",
            n_scenes=n_scenes,
            tts_voice=tts_voice,
            frame_template=f"{aspect}/image_default.html",
        )
        
        return {
            "engine": "pixelle",
            "task_id": result.storyboard.config.task_id if result.storyboard else None,
            "status": "success",
            "video_path": result.video_path,
            "duration": result.duration,
            "file_size": result.file_size,
            "raw": result,
        }
```

#### 2.3.3 Worker 重写 (`short_video.py`)

```python
"""墨播短视频 Worker — 双引擎支持"""
from .base import SubsidiaryWorker, Task, WorkerResult
from .short_video_engines import MPTEngine, PixelleEngine

class ShortVideo(SubsidiaryWorker):
    worker_id = "short_video"
    worker_name = "墨播短视频"
    description = "短视频脚本与全自动生成 (引擎: MoneyPrinterTurbo / Pixelle-Video)"
    oneliner = "短视频脚本与全自动生成"

    def __init__(self):
        self._mpt = MPTEngine()
        self._pixelle = PixelleEngine()

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            topic = task.payload.get("topic", "")
            engine = task.payload.get("engine", "mpt")  # mpt | pixelle
            mode = task.payload.get("mode", "script")    # script | full

            if mode == "script":
                # 仅生成脚本
                from molib.shared.content.video_script import generate_script
                script = await generate_script(topic)
                return WorkerResult(
                    task_id=task.task_id,
                    worker_id=self.worker_id,
                    status="success",
                    output={"topic": topic, "script": script, "status": "script_ready"},
                )

            # 全自动视频生成
            if engine == "pixelle":
                result = await self._pixelle.generate_video(
                    topic=topic,
                    script=task.payload.get("script", ""),
                    n_scenes=task.payload.get("scenes", 5),
                    tts_voice=task.payload.get("voice", "zh-CN-YunjianNeural"),
                )
            else:
                result = await self._mpt.generate_video(
                    topic=topic,
                    script=task.payload.get("script", ""),
                    aspect=task.payload.get("aspect", "9:16"),
                    voice=task.payload.get("voice", "zh-CN-XiaoyiNeural-Female"),
                )

            return WorkerResult(
                task_id=task.task_id,
                worker_id=self.worker_id,
                status=result["status"],
                output=result,
            )
        except Exception as e:
            return WorkerResult(
                task_id=task.task_id,
                worker_id=self.worker_id,
                status="error",
                output={},
                error=str(e),
            )
```

#### 2.3.4 CLI 入口修改 (`__main__.py`)

新增 `video generate` 子命令：

```python
async def cmd_video(args: list[str]) -> dict:
    """视频命令 — script | generate"""
    if not args:
        return {"error": "子命令: script | generate", "hint": "python -m molib video generate --topic T [--engine mpt|pixelle]"}
    
    subcmd = args[0]
    rest = args[1:]
    
    topic = ""
    engine = "mpt"
    mode = "full"
    
    i = 0
    while i < len(rest):
        if rest[i] == "--topic" and i + 1 < len(rest):
            topic = rest[i + 1]; i += 2
        elif rest[i] == "--engine" and i + 1 < len(rest):
            engine = rest[i + 1]; i += 2
        elif rest[i] == "--mode" and i + 1 < len(rest):
            mode = rest[i + 1]; i += 2
        else:
            i += 1
    
    if not topic:
        return {"error": "请指定 --topic 参数"}
    
    from molib.agencies.workers.short_video import ShortVideo
    from molib.agencies.workers.base import Task
    import uuid
    
    worker = ShortVideo()
    task = Task(
        task_id=str(uuid.uuid4()),
        task_type="video_generation",
        payload={"topic": topic, "engine": engine, "mode": mode},
    )
    result = await worker.execute(task)
    
    if result.status == "success":
        return {
            "action": "video_generated",
            "engine": engine,
            "topic": topic,
            "video_path": result.output.get("video_path"),
            "script": result.output.get("script"),
            "status": "success",
        }
    return {"error": result.error, "status": "error"}
```

然后在 `run()` 函数中添加映射：
```python
async_commands = {
    "intel": cmd_intel,
    "video": cmd_video,  # ← 新增
}
```

同时更新 `cmd_help()` 中的视频命令说明：
```python
"video script --topic T --duration D": "生成视频脚本（墨播短视频）",
"video generate --topic T [--engine mpt|pixelle]": "全自动生成视频（墨播短视频）",
```

### 2.4 双引擎对比

| 维度 | MoneyPrinterTurbo | Pixelle-Video |
|------|-------------------|---------------|
| Star | ⭐ 57K (上游) | ⭐ 13K (上游) |
| 核心管线 | topic→LLM脚本→Pexels素材→TTS→合成 | topic→LLM脚本→ComfyUI生图→TTS→合成 |
| 素材来源 | Pexels / Pixabay 无版权视频 | ComfyUI AI 生成图片/视频 |
| TTS | edge-tts (Azure) / 本地语音 | edge-tts / ComfyUI TTS 工作流 |
| 中文支持 | ✅ 优秀 | ✅ 优秀 |
| 需要 GPU | ❌ 不需要 | ✅ 需要 ComfyUI (可外连) |
| 调用方式 | 直接 `import` / HTTP API | 直接 `import` (异步) |
| 配置复杂度 | 低（配置 API Key 即可） | 中（需配置 LLM + ComfyUI 或 RunningHub） |
| 适用场景 | 快速出片、素材混剪 | AI 原创配图、数字人、风格化 |

### 2.5 使用示例

```bash
# 仅生成脚本
python -m molib video script --topic "AI Agent 入门"

# 使用 MoneyPrinterTurbo 全自动生成
python -m molib video generate --topic "深度学习基础" --engine mpt

# 使用 Pixelle-Video 全自动生成
python -m molib video generate --topic "如何提高学习效率" --engine pixelle --mode full

# CLI + Worker 结合
python -m molib video generate --topic "量子计算科普" --engine mpt --mode full
```

## 3. 安装与配置步骤

### 3.1 配置 MoneyPrinterTurbo

```bash
cd ~/MoneyPrinterTurbo
cp config.example.toml config.toml
# 编辑 config.toml，填入:
# - pexels_api_keys (免费注册 https://www.pexels.com/api/)
# - llm_provider + api_key (推荐 deepseek)
```

### 3.2 配置 Pixelle-Video

```bash
cd ~/pixelle-video
cp config.example.yaml config.yaml
# 编辑 config.yaml，填入:
# - llm.api_key + llm.base_url + llm.model
# - comfyui.comfyui_url (或使用 runninghub workflow)
```

### 3.3 安装依赖

```bash
# MPT 依赖
cd ~/MoneyPrinterTurbo && pip install -r requirements.txt

# Pixelle 依赖
cd ~/pixelle-video && pip install -e .
```

### 3.4 验证安装

```bash
python -m molib video generate --topic "测试" --engine mpt
python -m molib video generate --topic "测试" --engine pixelle
```

## 4. 风险与注意事项

1. **sys.path 注入**: 直接 import 两个仓库可能导致包名冲突。如果出现问题，回退到子进程调用方式 (subprocess + CLI)
2. **Pixelle-Video CLI 缺失**: pyproject.toml 中声明了 `pixelle_video.cli:main` 但文件不存在。如果要用子进程方式，需要先创建该入口
3. **异步兼容**: Pixelle-Video 全异步，MPT 的 `task.start()` 是同步函数。Worker 中需要用 `asyncio.to_thread()` 包装
4. **ComfyUI 依赖**: Pixelle-Video 默认需要 ComfyUI 服务（本地或 RunningHub），否则只能使用静态模板模式
5. **配置管理**: 两个引擎各自管理自己的配置，建议在 molib CLI 中增加 `python -m molib video config --engine mpt` 来快速编辑
