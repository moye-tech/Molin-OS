#!/usr/bin/env python3
"""
CH7-I: 语音合成器 — 阿里云TTS + edge-tts降级
零外部依赖，使用subprocess调用curl
"""
import os
import sys
import json
import uuid
import subprocess
from pathlib import Path
from typing import Optional, Dict

# ──────────────────────────────────────────────
# 配置
# ──────────────────────────────────────────────

DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")

OUTPUT_DIR = "/tmp/hermes-tts"

# 阿里云TTS语音列表
ALIYUN_VOICES = {
    "zhitian": "知甜 — 温柔女声",
    "zhixia": "知夏 — 活力女声",
    "zhijing": "知婧 — 知性女声",
    "zhibei": "知贝 — 可爱童声",
    "zhiqiang": "知强 — 稳重男声",
    "zhihao": "知浩 — 磁性男声",
    "zhihan": "知涵 — 温柔女声（英文）",
    "zhiwei": "知薇 — 轻柔女声",
}

# edge-tts 语音列表（常见）
EDGE_VOICES = {
    "zh-CN-XiaoxiaoNeural": "晓晓 — 默认女声",
    "zh-CN-YunxiNeural": "云希 — 阳光男声",
    "zh-CN-YunjianNeural": "云健 — 稳重男声",
    "zh-CN-XiaoyiNeural": "晓伊 — 活泼女声",
    "zh-CN-YunyangNeural": "云扬 — 磁性男声",
    "zh-CN-XiaochenNeural": "晓辰 — 温柔女声",
    "en-US-JennyNeural": "Jenny — 美式女声",
    "en-US-GuyNeural": "Guy — 美式男声",
}


# ──────────────────────────────────────────────
# 后端1: 阿里云TTS (通过DashScope API)
# ──────────────────────────────────────────────

def _call_aliyun_tts(text: str, voice: str, output_path: str) -> Optional[str]:
    """
    通过DashScope API调用阿里云TTS。

    API: POST https://dashscope.aliyuncs.com/api/v1/services/aigc/text2speech/tts
    """
    if not DASHSCOPE_API_KEY:
        print("  [aliyun-tts] ⚠️  DASHSCOPE_API_KEY 未配置")
        return None

    if voice not in ALIYUN_VOICES:
        # 默认用知甜
        voice = "zhitian"
        print(f"  [aliyun-tts] 使用默认语音: {voice}")

    payload = {
        "model": "cosyvoice-v2",
        "input": {
            "text": text
        },
        "parameters": {
            "voice": voice,
            "format": "mp3",
            "sample_rate": 24000,
            "rate": 1.0,
            "pitch": 1.0,
        }
    }

    tmp_json = f"/tmp/hermes_tts_req_{uuid.uuid4().hex[:8]}.json"
    with open(tmp_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)

    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2speech/tts"
    cmd = [
        "curl", "-s", "-X", "POST", url,
        "-H", f"Authorization: Bearer {DASHSCOPE_API_KEY}",
        "-H", "Content-Type: application/json",
        "-d", f"@{tmp_json}"
    ]

    print(f"  [aliyun-tts] 🎤 调用阿里云TTS cosyvoice-v2...")
    print(f"  [aliyun-tts]    语音: {voice} ({ALIYUN_VOICES.get(voice, '')})")
    print(f"  [aliyun-tts]    文本长度: {len(text)}字")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        os.unlink(tmp_json)

        if result.returncode != 0:
            print(f"  [aliyun-tts] ❌ curl失败: {result.stderr[:200]}")
            return None

        # 检查响应
        stdout = result.stdout

        # 尝试JSON解析（可能返回audio二进制而是JSON包装）
        try:
            response = json.loads(stdout)
            if "output" in response and "audio" in response["output"]:
                import base64
                audio_b64 = response["output"]["audio"]
                audio_data = base64.b64decode(audio_b64)
                Path(output_path).write_bytes(audio_data)
                size_kb = len(audio_data) / 1024
                print(f"  [aliyun-tts] ✅ 已保存: {output_path} ({size_kb:.0f}KB)")
                return output_path
            else:
                print(f"  [aliyun-tts] ⚠️  响应格式异常: {json.dumps(response, ensure_ascii=False)[:300]}")
                return None
        except json.JSONDecodeError:
            # 可能直接返回音频二进制
            if len(stdout.encode()) > 100:
                Path(output_path).write_bytes(stdout.encode() if isinstance(stdout, str) else stdout)
                size_kb = os.path.getsize(output_path) / 1024
                print(f"  [aliyun-tts] ✅ 已保存(原始): {output_path} ({size_kb:.0f}KB)")
                return output_path
            else:
                print(f"  [aliyun-tts] ⚠️  响应异常: {stdout[:200]}")
                return None

    except subprocess.TimeoutExpired:
        print(f"  [aliyun-tts] ⏰ 请求超时")
        try: os.unlink(tmp_json)
        except: pass
        return None
    except Exception as e:
        print(f"  [aliyun-tts] ❌ 异常: {e}")
        try: os.unlink(tmp_json)
        except: pass
        return None


# ──────────────────────────────────────────────
# 后端2: edge-tts (降级)
# ──────────────────────────────────────────────

def _call_edge_tts(text: str, voice: str, output_path: str) -> Optional[str]:
    """
    使用edge-tts命令行工具作为降级方案。
    
    edge-tts 不是标准库，但可以通过 pip 安装。
    这里通过 subprocess 调用 edge-tts CLI。
    """
    edge_voice = voice if voice in EDGE_VOICES else "zh-CN-XiaoxiaoNeural"

    # 先检查 edge-tts 是否可用
    check = subprocess.run(
        ["which", "edge-tts"],
        capture_output=True, text=True, timeout=5
    )
    if check.returncode != 0:
        # 尝试 pip install edge-tts
        print(f"  [edge-tts] ⚠️  edge-tts 未安装，尝试安装...")
        install = subprocess.run(
            [sys.executable, "-m", "pip", "install", "edge-tts", "-q"],
            capture_output=True, text=True, timeout=60
        )
        if install.returncode != 0:
            print(f"  [edge-tts] ❌ 安装失败: {install.stderr[:200]}")
            return None
        print(f"  [edge-tts] ✅ 安装成功")

    print(f"  [edge-tts] 🎤 调用 edge-tts...")
    print(f"  [edge-tts]    语音: {edge_voice} ({EDGE_VOICES.get(edge_voice, '')})")

    try:
        # edge-tts 可以用 python -m edge_tts 调用
        cmd = [
            sys.executable, "-m", "edge_tts",
            "--text", text,
            "--voice", edge_voice,
            "--write-media", output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode == 0 and os.path.getsize(output_path) > 100:
            size_kb = os.path.getsize(output_path) / 1024
            print(f"  [edge-tts] ✅ 已保存: {output_path} ({size_kb:.0f}KB)")
            return output_path
        else:
            print(f"  [edge-tts] ❌ 失败: {result.stderr[:200]}")
            return None

    except subprocess.TimeoutExpired:
        print(f"  [edge-tts] ⏰ 超时")
        return None
    except Exception as e:
        print(f"  [edge-tts] ❌ 异常: {e}")
        return None


# ──────────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────────

def generate_speech(
    text: str,
    voice: str = "zhitian",
    output_path: Optional[str] = None,
    preferred_backend: str = "aliyun",
) -> Optional[str]:
    """
    生成语音，支持自动降级到edge-tts。

    Args:
        text: 要合成的文本
        voice: 语音ID
        output_path: 输出MP3路径
        preferred_backend: 首选后端 (aliyun / edge)

    Returns:
        str: 输出文件路径，失败返回None
    """
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    if not output_path:
        output_path = os.path.join(OUTPUT_DIR, f"tts_{uuid.uuid4().hex[:12]}.mp3")

    # 确保扩展名是.mp3
    if not output_path.endswith(".mp3"):
        output_path = output_path + ".mp3"

    backends = []
    if preferred_backend == "aliyun":
        backends = ["aliyun", "edge"]
    else:
        backends = ["edge", "aliyun"]

    print(f"🎤 语音合成")
    print(f"   文本: {text[:100]}{'...' if len(text) > 100 else ''}")
    print(f"   语音: {voice}")
    print(f"   输出: {output_path}")
    print(f"   降级顺序: {' → '.join(backends)}")
    print()

    for backend_name in backends:
        print(f"── [{backend_name}] 尝试 ──")
        if backend_name == "aliyun":
            result = _call_aliyun_tts(text, voice, output_path)
        else:
            result = _call_edge_tts(text, voice, output_path)

        if result:
            print(f"\n✅ 语音已生成: {result}")
            return result
        print()

    print(f"❌ 所有后端均失败")
    return None


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="CH7-I: 语音合成器 — 阿里云TTS + edge-tts降级"
    )
    parser.add_argument("--text", "-t", required=True, help="要合成的文本")
    parser.add_argument("--voice", "-v", default="zhitian",
                        help=f"语音ID (阿里云: {', '.join(ALIYUN_VOICES.keys())})")
    parser.add_argument("--output", "-o", help="输出MP3文件路径")
    parser.add_argument("--backend", default="aliyun",
                        choices=["aliyun", "edge"], help="首选后端")

    args = parser.parse_args()

    result = generate_speech(
        text=args.text,
        voice=args.voice,
        output_path=args.output,
        preferred_backend=args.backend,
    )

    if result:
        print(f"\n📎 输出: {result}")
    else:
        print(f"\n❌ 合成失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
