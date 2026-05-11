"""
墨麟OS v2.5 — 数字人口播生成器 (DigitalHumanGenerator)

全新能力：从0到1实现 AI 数字人口播，替代 HeyGen（月省 $29+）。

Pipeline:
  1. CosyVoice 生成配音（或声音克隆墨烨本人声线）
  2. MuseTalk 唇形同步（腾讯出品，30fps）
  3. LivePortrait 头部运动增强（快手出品，表情+眼神）
  4. MoviePy 后处理（字幕叠加/BGM/9:16竖版裁切）
  → 输出：可直接发布的口播视频 MP4

适用场景:
  - 课程讲解口播视频（不露脸、不录音）
  - 小红书/抖音口播内容
  - 24小时直播数字人（配合 Linly-Talker）

用法:
    from molib.content.digital_human import DigitalHumanGenerator
    dh = DigitalHumanGenerator()
    result = await dh.generate(
        script="今天跟大家分享AI副业的三个核心思维...",
        avatar_image="/path/to/moye_photo.jpg",
        voice="moye_cloned",
    )
"""

from __future__ import annotations

import logging
from typing import Dict, Optional, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


class DigitalHumanGenerator:
    """
    AI 数字人口播视频生成器。

    三阶段流水线:
      Stage 1: TTS 配音（CosyVoice / 声音克隆）
      Stage 2: 口播合成（MuseTalk 唇形同步 + LivePortrait 头部运动）
      Stage 3: 后处理（MoviePy 字幕+BGM+裁切）

    部署要求:
      - MuseTalk: 本地 GPU 或 Docker（M1 Mac 可通过 MPS 运行轻量版）
      - LivePortrait: 本地 GPU 或 Docker
      - 降级方案: 无 GPU 时使用 DashScope API 替代
    """

    def __init__(
        self,
        musetalk_endpoint: Optional[str] = None,
        liveportrait_endpoint: Optional[str] = None,
        comfyui_endpoint: Optional[str] = None,
        avatar_image_path: Optional[str] = None,
    ):
        """
        Args:
            musetalk_endpoint: MuseTalk API 地址 (默认 http://localhost:8898)
            liveportrait_endpoint: LivePortrait API 地址 (默认 http://localhost:8899)
            comfyui_endpoint: ComfyUI API 地址 (默认 http://localhost:8188)
            avatar_image_path: 默认数字人形象图片路径
        """
        self.musetalk_endpoint = musetalk_endpoint or "http://localhost:8898"
        self.liveportrait_endpoint = liveportrait_endpoint or "http://localhost:8899"
        self.comfyui_endpoint = comfyui_endpoint or "http://localhost:8188"
        self.avatar_image_path = avatar_image_path

    async def generate(
        self,
        script: str,
        avatar_image: Optional[str] = None,
        voice: str = "zhihao",
        emotion: Optional[str] = None,
        bgm_path: Optional[str] = None,
        add_subtitles: bool = True,
        output_format: str = "mp4",
        output_dir: str = "/tmp/hermes-digital-human",
        # 平台适配
        platform: str = "default",
    ) -> Dict[str, Any]:
        """
        生成数字人口播视频。

        Args:
            script: 口播脚本文本
            avatar_image: 数字人形象图片（不传则用默认）
            voice: TTS 声音（cosyvoice 声音名 / "moye_cloned" / 系统默认）
            emotion: 情绪标签（happy/sad/excited/serious）
            bgm_path: 背景音乐路径
            add_subtitles: 是否添加字幕
            output_format: 输出视频格式
            output_dir: 输出目录
            platform: 目标平台，影响视频参数
                - "douyin": 9:16 竖版, 15-60s
                - "xiaohongshu": 3:4, 30-60s
                - "shipinhao": 16:9 横版, 30s-3min
                - "default": 16:9 横版

        Returns:
            {"video_path": str, "duration": float, "pipeline": list, "success": bool}
        """
        import time
        from pathlib import Path

        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        pipeline_steps = []
        timestamp = int(time.time())

        # 平台视频参数
        platform_params = self._get_platform_params(platform)

        try:
            # ── Stage 1: TTS 配音 ──
            tts_result = await self._stage_1_tts(script, voice, emotion, out_dir, timestamp)
            if not tts_result.get("success"):
                return {"success": False, "error": f"TTS 失败: {tts_result.get('error')}"}
            pipeline_steps.append("tts")
            audio_path = tts_result["audio_path"]

            # ── Stage 2: 口播合成 ──
            avatar_img = avatar_image or self.avatar_image_path
            if not avatar_img:
                return {"success": False, "error": "未提供数字人形象图片"}

            # 2a: MuseTalk 唇形同步
            musetalk_result = await self._stage_2a_musetalk(
                avatar_img, audio_path, out_dir, timestamp
            )
            pipeline_steps.append("musetalk_lipsync")

            # 2b: LivePortrait 头部运动增强
            if musetalk_result.get("success"):
                liveportrait_result = await self._stage_2b_liveportrait(
                    musetalk_result["video_path"], out_dir, timestamp
                )
                if liveportrait_result.get("success"):
                    pipeline_steps.append("liveportrait_motion")
                    intermediate_video = liveportrait_result["video_path"]
                else:
                    intermediate_video = musetalk_result["video_path"]
            else:
                # MuseTalk 不可用时的降级方案
                intermediate_video = await self._stage_2_fallback(
                    avatar_img, audio_path, out_dir, timestamp
                )
                pipeline_steps.append("fallback_static")

            # ── Stage 3: MoviePy 后处理 ──
            final_video = await self._stage_3_postprocess(
                intermediate_video,
                script if add_subtitles else None,
                bgm_path,
                platform_params,
                out_dir,
                timestamp,
            )
            pipeline_steps.append("postprocess")

            return {
                "success": True,
                "video_path": str(final_video),
                "duration": tts_result.get("duration", 0),
                "pipeline": pipeline_steps,
                "platform": platform,
                "note": f"数字人口播视频 ({platform})",
            }

        except Exception as e:
            logger.error(f"数字人视频生成失败: {e}")
            return {"success": False, "error": str(e), "pipeline": pipeline_steps}

    # ── Stage 1: TTS ──

    async def _stage_1_tts(
        self, script: str, voice: str, emotion: Optional[str],
        out_dir: Path, timestamp: int
    ) -> Dict[str, Any]:
        """TTS 配音"""
        try:
            from molib.shared.tts.cosyvoice_tts import CosyVoiceTTS
            tts = CosyVoiceTTS()
            result = await tts.generate(
                text=script, voice=voice, emotion=emotion, output_format="wav"
            )
            return result
        except ImportError:
            # 降级：使用现有 tts_generator
            import subprocess
            audio_path = out_dir / f"tts_{timestamp}.wav"
            script_file = out_dir / f"script_{timestamp}.txt"
            script_file.write_text(script[:2000])
            subprocess.run(
                ["python3", "/Users/moye/Molin-OS/bots/tts_generator.py",
                 str(script_file), str(audio_path)],
                capture_output=True, timeout=60,
            )
            if audio_path.exists():
                return {"success": True, "audio_path": str(audio_path)}
            return {"success": False, "error": "TTS 生成失败"}

    # ── Stage 2a: MuseTalk 唇形同步 ──

    async def _stage_2a_musetalk(
        self, avatar_img: str, audio_path: str,
        out_dir: Path, timestamp: int
    ) -> Dict[str, Any]:
        """MuseTalk 唇形同步"""
        import subprocess
        import json

        output_path = out_dir / f"musetalk_{timestamp}.mp4"

        try:
            # 尝试调用 MuseTalk API（本地部署或 Docker）
            payload = {
                "avatar_image": avatar_img,
                "audio_path": audio_path,
                "fps": 30,
            }

            result = subprocess.run(
                [
                    "curl", "-s", "-X", "POST",
                    f"{self.musetalk_endpoint}/generate",
                    "-H", "Content-Type: application/json",
                    "-d", json.dumps(payload),
                    "-o", str(output_path),
                    "--connect-timeout", "5", "--max-time", "300",
                ],
                capture_output=True, text=True, timeout=310,
            )

            if output_path.exists() and output_path.stat().st_size > 1024:
                return {"success": True, "video_path": str(output_path)}

            # 尝试 ComfyUI + MuseTalk 工作流
            return await self._musetalk_via_comfyui(avatar_img, audio_path, output_path)

        except subprocess.TimeoutExpired:
            logger.warning("MuseTalk API 超时")
            return {"success": False, "error": "MuseTalk API 超时"}
        except Exception as e:
            logger.warning(f"MuseTalk 不可用: {e}")
            return {"success": False, "error": str(e)}

    async def _musetalk_via_comfyui(
        self, avatar_img: str, audio_path: str, output_path: Path
    ) -> Dict[str, Any]:
        """通过 ComfyUI 的 MuseTalk 工作流节点生成"""
        try:
            from molib.shared.comfyui_client import ComfyUIClient
            client = ComfyUIClient(base_url=self.comfyui_endpoint)
            result = await client.run_workflow(
                workflow_name="musetalk_lipsync",
                inputs={
                    "avatar_image": avatar_img,
                    "audio_path": audio_path,
                },
                output_path=str(output_path),
            )
            if result.get("success"):
                return {"success": True, "video_path": str(output_path)}
        except ImportError:
            pass

        return {"success": False, "error": "MuseTalk 不可用（本地未部署且 ComfyUI 未安装）"}

    # ── Stage 2b: LivePortrait 头部运动 ──

    async def _stage_2b_liveportrait(
        self, input_video: str, out_dir: Path, timestamp: int
    ) -> Dict[str, Any]:
        """LivePortrait 头部运动 + 表情增强"""
        import subprocess
        import json

        output_path = out_dir / f"liveportrait_{timestamp}.mp4"

        try:
            payload = {
                "source_video": input_video,
                "motion_scale": 1.0,
                "eye_enhance": True,
                "head_motion": True,
            }

            result = subprocess.run(
                [
                    "curl", "-s", "-X", "POST",
                    f"{self.liveportrait_endpoint}/animate",
                    "-H", "Content-Type: application/json",
                    "-d", json.dumps(payload),
                    "-o", str(output_path),
                    "--connect-timeout", "5", "--max-time", "120",
                ],
                capture_output=True, text=True, timeout=130,
            )

            if output_path.exists() and output_path.stat().st_size > 1024:
                return {"success": True, "video_path": str(output_path)}

        except Exception as e:
            logger.warning(f"LivePortrait 不可用，跳过头部运动增强: {e}")

        return {"success": False, "error": "LivePortrait 不可用"}

    async def _stage_2_fallback(
        self, avatar_img: str, audio_path: str,
        out_dir: Path, timestamp: int
    ) -> Path:
        """
        降级方案：静态图 + 音频 → 视频。
        使用 ffmpeg 将图片和音频合成为静态视频（无唇形同步）。
        """
        import subprocess

        output_path = out_dir / f"static_{timestamp}.mp4"
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-loop", "1", "-i", avatar_img,
                "-i", audio_path,
                "-c:v", "libx264", "-tune", "stillimage",
                "-c:a", "aac", "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-shortest", str(output_path),
            ],
            capture_output=True, timeout=120,
        )
        return output_path if output_path.exists() else Path(audio_path)

    # ── Stage 3: MoviePy 后处理 ──

    async def _stage_3_postprocess(
        self, input_video: Path, script: Optional[str],
        bgm_path: Optional[str], platform_params: dict,
        out_dir: Path, timestamp: int,
    ) -> Path:
        """MoviePy 后处理：字幕 + BGM + 平台适配裁切"""
        output_path = out_dir / f"final_{timestamp}.mp4"

        try:
            from moviepy import (
                VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
            )

            video = VideoFileClip(str(input_video))

            # 平台裁切
            target_size = platform_params.get("size")
            if target_size:
                video = video.resized(target_size)

            # 字幕叠加
            if script:
                subtitle_clip = self._create_subtitle_clip(script, video.duration)
                video = CompositeVideoClip([video, subtitle_clip])

            # BGM 混合
            if bgm_path and Path(bgm_path).exists():
                bgm = AudioFileClip(bgm_path).with_volume_scaled(0.15)  # 15% 音量
                if bgm.duration < video.duration:
                    bgm = bgm.loop(duration=video.duration)
                else:
                    bgm = bgm.subclipped(0, video.duration)
                video.audio = video.audio.with_volume_scaled(0.85).mixed_with(bgm)

            video.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac",
                fps=platform_params.get("fps", 30),
            )
            video.close()
            return output_path

        except ImportError:
            # 降级：ffmpeg
            return self._postprocess_ffmpeg(
                input_video, script, bgm_path, platform_params, output_path
            )
        except Exception as e:
            logger.warning(f"MoviePy 后处理失败: {e}")
            return input_video

    def _create_subtitle_clip(self, script: str, duration: float):
        """创建字幕 clip（简化版，单行居中滚动）"""
        from moviepy import TextClip

        # 按句号/换行分割字幕
        sentences = [s.strip() for s in script.replace("\n", "。").split("。") if s.strip()]
        if not sentences:
            sentences = [script[:50]]

        chars_per_sec = len(script) / max(duration, 1)
        # 简化：单条字幕居中
        return TextClip(
            text=script[:200],
            font_size=36,
            color="white",
            stroke_color="black",
            stroke_width=2,
            font="PingFang-SC-Regular",
            size=(1080, None),
        ).with_position(("center", "bottom")).with_duration(duration)

    def _postprocess_ffmpeg(
        self, input_video: Path, script: Optional[str],
        bgm_path: Optional[str], platform_params: dict,
        output_path: Path,
    ) -> Path:
        """ffmpeg 降级后处理"""
        import subprocess

        cmd = ["ffmpeg", "-y", "-i", str(input_video)]

        # BGM
        if bgm_path and Path(bgm_path).exists():
            cmd += ["-i", bgm_path, "-filter_complex",
                    "[1:a]volume=0.15[bgm];[0:a]volume=0.85[main];[main][bgm]amix=inputs=2:duration=first"]

        # 字幕（使用 drawtext 滤镜）
        if script:
            subtitle_text = script[:100].replace("'", "'\\\\''")
            vf = (
                f"drawtext=text='{subtitle_text}':"
                f"fontfile=/System/Library/Fonts/PingFang.ttc:"
                f"fontsize=36:fontcolor=white:borderw=2:bordercolor=black:"
                f"x=(w-text_w)/2:y=h-th-60"
            )
            if "-filter_complex" in cmd:
                # 已有滤镜链
                cmd[cmd.index("-filter_complex") + 1] += f";[0:v]{vf}[vout]"
            else:
                cmd += ["-vf", vf]

        cmd += ["-c:v", "libx264", "-c:a", "aac", "-shortest", str(output_path)]
        subprocess.run(cmd, capture_output=True, timeout=120)
        return output_path if output_path.exists() else input_video

    # ── 平台适配 ──

    def _get_platform_params(self, platform: str) -> dict:
        """获取平台视频参数"""
        params = {
            "douyin": {
                "size": (1080, 1920),    # 9:16
                "fps": 30,
                "max_duration": 60,
                "bitrate": "4M",
            },
            "xiaohongshu": {
                "size": (1080, 1440),    # 3:4
                "fps": 30,
                "max_duration": 60,
                "bitrate": "3M",
            },
            "shipinhao": {
                "size": (1920, 1080),    # 16:9
                "fps": 30,
                "max_duration": 180,
                "bitrate": "5M",
            },
            "default": {
                "size": (1920, 1080),
                "fps": 30,
                "max_duration": 300,
                "bitrate": "4M",
            },
        }
        return params.get(platform, params["default"])

    # ── 健康检查 ──

    @property
    def status(self) -> Dict[str, Any]:
        """系统健康状态"""
        import subprocess

        musetalk_ok = False
        liveportrait_ok = False
        comfyui_ok = False

        try:
            r = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                 f"{self.musetalk_endpoint}/health"],
                capture_output=True, text=True, timeout=3,
            )
            musetalk_ok = r.stdout.strip() == "200"
        except Exception:
            pass

        try:
            r = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                 f"{self.liveportrait_endpoint}/health"],
                capture_output=True, text=True, timeout=3,
            )
            liveportrait_ok = r.stdout.strip() == "200"
        except Exception:
            pass

        try:
            r = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                 f"{self.comfyui_endpoint}/system_stats"],
                capture_output=True, text=True, timeout=3,
            )
            comfyui_ok = r.stdout.strip() == "200"
        except Exception:
            pass

        return {
            "musetalk_available": musetalk_ok,
            "liveportrait_available": liveportrait_ok,
            "comfyui_available": comfyui_ok,
            "mode": (
                "完整 (MuseTalk + LivePortrait)"
                if musetalk_ok and liveportrait_ok
                else "降级 (静态图+音频)"
                if not musetalk_ok
                else "部分 (仅唇形同步)"
            ),
            "avatar_configured": bool(self.avatar_image_path),
        }
