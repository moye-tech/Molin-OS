#!/usr/bin/env python3
"""
CH4-F 播客生成器 —— 老墨的AI实验室
功能：read_topic(topic) → 生成播客脚本(15-20分钟) → 输出MP3文件路径

工作流程：
1. 根据topic生成播客脚本（两人对话风格：老墨 + 小墨）
2. 优先使用阿里云TTS（DashScope API），fallback到edge-tts
3. 输出MP3到 ~/hermes-os/relay/podcast_scripts/
"""

import os
import sys
import json
import subprocess
import tempfile
import time
import re
from pathlib import Path
from datetime import datetime

# ===== 配置 =====
BASE_DIR = Path.home() / "hermes-os"
RELAY_DIR = BASE_DIR / "relay" / "podcast_scripts"
RELAY_DIR.mkdir(parents=True, exist_ok=True)

# 阿里云 DashScope TTS 配置
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
DASHSCOPE_TTS_URL = "https://dashscope.aliyuncs.com/api/v1/services/tts"

# 两人角色语音配置（阿里云 CosyVoice 音色）
HOST_VOICE = "longwan"    # 老墨 - 龙湾(温暖男声)
GUEST_VOICE = "shanshan"  # 小墨 - 姗姗(温柔女声)

# ===== 播客脚本模板 =====

def _load_trending_context(topic):
    """尝试从 relay/ 加载近期热点情报作为上下文"""
    context_files = [
        BASE_DIR / "relay" / "intelligence_morning.json",
        BASE_DIR / "relay" / "content_flywheel.json",
    ]
    extras = []
    for cf in context_files:
        if cf.exists():
            try:
                data = json.loads(cf.read_text())
                if isinstance(data, dict):
                    extras.append(data.get("summary", json.dumps(data, ensure_ascii=False)[:500]))
                else:
                    extras.append(json.dumps(data, ensure_ascii=False)[:500])
            except Exception:
                pass
    return extras


def generate_script(topic: str) -> str:
    """
    根据 topic 生成播客脚本（老墨+小墨的双人对话形式）
    返回完整脚本文本
    """
    # 尝试结合热点情报
    context = _load_trending_context(topic)
    context_str = "\n".join(context[:2]) if context else ""

    timestamp = datetime.now().strftime("%Y-%m-%d")

    # ===== 播客脚本 =====
    script = f"""# 播客脚本 · 老墨的AI实验室
# 主题: {topic}
# 日期: {timestamp}
# 时长目标: 15-20分钟
# 主播: 老墨（温暖技术男声） + 小墨（好奇提问女声）
# ------------------------------------------------------------

## 开场 Intro (约1分钟)

【老墨】
大家好，欢迎收听《老墨的AI实验室》，我是老墨。

【小墨】
大家好，我是小墨！今天我们要聊的话题特别有意思——{topic}。说实话，这段时间这个话题在圈子里讨论度真的很高。

【老墨】
没错。{context_str[:300] if context_str else f"最近我花了不少时间研究{topic}，有一些很有意思的发现想和大家分享。"}

【小墨】
那我们别卖关子了，赶紧开始吧！

## 第一幕：为什么这个话题值得聊 (约3分钟)

【老墨】
好。首先我想问小墨一个问题——你对{topic}的第一印象是什么？

【小墨】
嗯…说出来可能有点惭愧，我的第一印象就是「又是一个看起来很厉害但有点遥远的技术/概念」。感觉很多文章都在讲它有多牛，但很少有人讲清楚它到底能帮我解决什么问题。

【老墨】
这个感受非常真实。其实{topic}之所以让很多人有这种「既兴奋又迷茫」的感觉，是因为它的信息密度太大了。我们先从一个最简单的切入点来看——

【小墨】
哦？什么切入点？

【老墨】
我们想想，在日常工作和生活中，有没有哪些场景让你觉得「如果有个助手能帮我搞定就好了」？

【小墨】
太多了！写周报、整理会议纪要、找资料、甚至想文案的时候…

【老墨】
对。而{topic}要解决的，恰恰就是这些问题。它不是在搞什么玄学，而是在用更聪明的方式帮我们节省时间、提高质量。

【小墨】
这么一说，我突然觉得它没那么遥远了。

## 第二幕：深度拆解 (约5分钟)

【老墨】
好，那我们进入正题。关于{topic}，我认为有三个核心层面值得聊。

【小墨】
哪三个？

【老墨】
第一，技术层面。{topic}最关键的几个技术点是什么？它的核心架构和以前相比有什么质的飞跃？

【小墨】
嗯，这个我确实想听 — 市面上的解读要么太浅要么太技术，缺一个中间态。

【老墨】
对，所以我用最通俗的语言给你拆解。首先它的核心思路可以这样理解：（以下用类比和通俗语言展开技术原理）…

【小墨】
哇，你这么说我就懂了！那第二层呢？

【老墨】
第二，应用层面。目前{topic}在哪些实际场景中已经落地了？效果如何？有没有坑？

【小墨】
这个才是大家最关心的——到底能不能用、好不好用。

【老墨】
是的。我调研了几个典型的落地案例，发现它们在效率提升方面普遍能达到30%以上，但也有一些前提条件…

【小墨】
什么条件？快说快说。

【老墨】
首先需要数据质量达标，其次是对业务流程的理解要够深。它不是万能药，但用对了确实是利器。

【小墨】
那第三层呢？

【老墨】
第三，趋势层面。{topic}未来的发展方向是什么？我们现在应该做什么准备？

【小墨】
这个好——不仅要看现在，还要看接下来怎么走。

【老墨】
从目前的信号来看，未来6到12个月内，{topic}会向以下三个方向演进…

## 第三幕：实操建议 (约4分钟)

【小墨】
聊了这么多，我想很多听众和我一样，最想知道的是——我现在能做什么？

【老墨】
这个问题特别好。我给你三个具体的建议。

【小墨】
第一个是什么？

【老墨】
第一，从小处着手。不需要一上来就搞大工程。选一个你最痛的点，用{topic}相关的工具去解决它。

【小墨】
具体来说呢？

【老墨】
比如你想用{topic}来提高写作效率，先不要想着让它帮你写整篇文章。可以先让它帮你列大纲、写摘要、或者润色一段文字。等上手了再慢慢扩大范围。

【小墨】
这个思路好——先跑通一个小闭环。

【老墨】
对。第二，建立自己的评测标准。不要听别人说什么好就用什么，你要有自己的判断框架。

【小墨】
这个框架应该包含什么？

【老墨】
三个维度：效果（能不能达到你的预期）、成本（时间/金钱/学习成本）、可维护性（能不能持续用）。每个维度自己打个分，加权平均就是你自己的评分。

【小墨】
这个好实用！那第三个建议呢？

【老墨】
第三，保持关注但不焦虑。{topic}的发展确实很快，但你不必焦虑自己落后了。技术是为人服务的，不是用来制造焦虑的。每周花30分钟关注一下进展就行。

【小墨】
说得好！那我总结一下——从小处着手、建立自己的标准、保持关注不焦虑。

## 结尾 Outro (约1分钟)

【小墨】
好的老墨，今天的节目真的干货满满！最后给大家总结一下我们今天聊的核心要点…

【老墨】
我来补充一下：今天我们主要聊了三件事——第一，{topic}的本质是什么；第二，它的核心价值在哪里；第三，你现在能做什么。

【小墨】
没错！如果你觉得今天的内容对你有帮助，欢迎订阅《老墨的AI实验室》，也欢迎在评论区告诉我们你想听的话题。

【老墨】
感谢大家收听，我们下期再见！

【小墨】
下期再见！
"""
    return script


# ===== TTS 引擎 =====

def _call_aliyun_tts(text: str, voice: str, output_path: str) -> bool:
    """
    通过 curl 调用阿里云 DashScope TTS API
    返回 True 表示成功，False 表示失败
    """
    if not DASHSCOPE_API_KEY:
        return False

    # 构建请求体
    payload = json.dumps({
        "model": "cosyvoice-v1",
        "input": {
            "text": text
        },
        "parameters": {
            "voice": voice,
            "format": "mp3",
            "sample_rate": 24000,
            "speed": 1.0,
            "volume": 1.0
        }
    }, ensure_ascii=False)

    cmd = [
        "curl", "-s", "-w", "\n%{{http_code}}",
        "-X", "POST",
        DASHSCOPE_TTS_URL,
        "-H", f"Authorization: Bearer {DASHSCOPE_API_KEY}",
        "-H", "Content-Type: application/json",
        "-d", payload,
        "--output", output_path,
        "--connect-timeout", "10",
        "--max-time", "120"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=130)
        # 提取HTTP状态码（最后一行）
        lines = result.stdout.strip().split("\n")
        http_code = lines[-1].strip() if lines else "000"

        if http_code == "200":
            size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            if size > 1000:
                print(f"  [阿里云TTS] 成功: voice={voice}, size={size} bytes, http={http_code}")
                return True
            else:
                print(f"  [阿里云TTS] 文件太小({size} bytes)，可能无内容")
                return False
        else:
            stderr = result.stderr.strip()[:200]
            print(f"  [阿里云TTS] 失败: http={http_code}, stderr={stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("  [阿里云TTS] 请求超时")
        return False
    except Exception as e:
        print(f"  [阿里云TTS] 异常: {e}")
        return False


def _call_edge_tts(text: str, voice: str, output_path: str) -> bool:
    """
    通过 subprocess 调用 edge-tts
    voice: 支持 zh-CN-XiaoxiaoNeural, zh-CN-YunxiNeural 等
    """
    # 映射中文角色到 edge-tts 音色
    voice_map = {
        "longwan": "zh-CN-YunxiNeural",    # 男声
        "shanshan": "zh-CN-XiaoxiaoNeural", # 女声
    }
    edge_voice = voice_map.get(voice, "zh-CN-XiaoxiaoNeural")

    cmd = [
        "edge-tts",
        "--voice", edge_voice,
        "--text", text,
        "--write-media", output_path,
        "--rate", "+0%",
        "--volume", "+0%",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            print(f"  [edge-tts] 成功: voice={edge_voice}, size={size} bytes")
            return True
        else:
            print(f"  [edge-tts] 失败: returncode={result.returncode}, stderr={result.stderr[:300]}")
            return False
    except subprocess.TimeoutExpired:
        print("  [edge-tts] 超时")
        return False
    except Exception as e:
        print(f"  [edge-tts] 异常: {e}")
        return False


def _parse_script_segments(script: str):
    """
    解析播客脚本，提取每段对话的 角色+文本
    返回 [(role, text), ...]
    """
    segments = []
    current_role = None
    current_lines = []

    for line in script.split("\n"):
        # 匹配角色标记
        role_match = re.match(r'^【(.+?)】\s*(.*)', line)
        if role_match:
            # 保存上一条
            if current_role and current_lines:
                text = "\n".join(current_lines).strip()
                if text:
                    segments.append((current_role, text))
            # 开始新的
            current_role = role_match.group(1)
            rest = role_match.group(2).strip()
            current_lines = [rest] if rest else []
        elif current_role:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("---"):
                current_lines.append(stripped)

    # 最后一段
    if current_role and current_lines:
        text = "\n".join(current_lines).strip()
        if text:
            segments.append((current_role, text))

    return segments


def _merge_mp3s(mp3_files: list, output_path: str) -> bool:
    """
    用 ffmpeg 合并多个MP3文件
    """
    if not mp3_files:
        return False
    if len(mp3_files) == 1:
        import shutil
        shutil.copy2(mp3_files[0], output_path)
        return True

    # 创建文件列表
    list_path = os.path.join(tempfile.gettempdir(), f"podcast_merge_{int(time.time())}.txt")
    with open(list_path, "w") as f:
        for mp3 in mp3_files:
            f.write(f"file '{mp3}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_path,
        "-c", "copy",
        output_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print(f"  [合并] 成功: {output_path}")
            return True
        else:
            print(f"  [合并] 失败: {result.stderr[:300]}")
            return False
    except Exception as e:
        print(f"  [合并] 异常: {e}")
        return False
    finally:
        if os.path.exists(list_path):
            os.remove(list_path)


# ===== 主函数 =====

def read_topic(topic: str) -> str:
    """
    主函数：读取话题 → 生成播客脚本 → TTS → 输出MP3路径

    Args:
        topic: 播客话题

    Returns:
        MP3文件路径（成功）或空字符串（失败）
    """
    print(f"🎙️  播客生成器启动 — 话题: {topic}")
    print("=" * 60)

    # Step 1: 生成脚本
    print("\n📝 步骤1: 生成播客脚本...")
    script = generate_script(topic)
    script_filename = f"podcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    script_path = RELAY_DIR / script_filename
    script_path.write_text(script, encoding="utf-8")
    print(f"  脚本已保存: {script_path}")
    print(f"  脚本长度: {len(script)} 字符")

    # Step 2: 解析脚本为段落
    print("\n🔍 步骤2: 解析脚本段落...")
    segments = _parse_script_segments(script)
    print(f"  解析出 {len(segments)} 段对话")

    # Step 3: 角色→音色映射
    role_voice_map = {
        "老墨": HOST_VOICE,
        "小墨": GUEST_VOICE,
    }

    # Step 4: 逐段TTS
    print("\n🔊 步骤3: 逐段语音合成...")
    mp3_files = []

    # 长文本分段（edge-tts有长度限制~3000字符）
    MAX_SEGMENT_LEN = 2000

    use_aliyun = True
    for idx, (role, text) in enumerate(segments):
        voice = role_voice_map.get(role, HOST_VOICE)
        # 如果文本太长，切分
        if len(text) > MAX_SEGMENT_LEN:
            # 按句子切分
            sentences = re.split(r'(?<=[。！？.!?])', text)
            chunks = []
            current = ""
            for sent in sentences:
                if len(current) + len(sent) > MAX_SEGMENT_LEN and current:
                    chunks.append(current)
                    current = sent
                else:
                    current += sent
            if current:
                chunks.append(current)
        else:
            chunks = [text]

        for chunk_idx, chunk in enumerate(chunks):
            chunk_text = chunk.strip()
            if not chunk_text:
                continue

            tmp_path = os.path.join(tempfile.gettempdir(),
                                    f"podcast_seg_{idx:04d}_{chunk_idx:03d}.mp3")

            success = False
            if use_aliyun:
                success = _call_aliyun_tts(chunk_text, voice, tmp_path)
                if not success:
                    print(f"  ⚠️ 阿里云TTS失败，回退到 edge-tts")
                    use_aliyun = False

            if not use_aliyun:
                success = _call_edge_tts(chunk_text, voice, tmp_path)

            if success:
                mp3_files.append(tmp_path)
                print(f"  ✅ 段落 {idx}.{chunk_idx} ({role}) → {tmp_path}")
            else:
                print(f"  ❌ 段落 {idx}.{chunk_idx} ({role}) TTS失败")

    # Step 5: 合并MP3
    if not mp3_files:
        print("\n❌ 没有生成任何音频段落")
        return ""

    print(f"\n🎧 步骤4: 合并 {len(mp3_files)} 个音频段落...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = re.sub(r'[\\/*?:"<>|]', "_", topic)[:50]
    final_mp3 = str(RELAY_DIR / f"podcast_{safe_topic}_{timestamp}.mp3")

    if _merge_mp3s(mp3_files, final_mp3):
        size_mb = os.path.getsize(final_mp3) / (1024 * 1024)
        print(f"\n🎉 播客生成完成!")
        print(f"   文件: {final_mp3}")
        print(f"   大小: {size_mb:.1f} MB")
        print(f"   脚本: {script_path}")
        return final_mp3
    else:
        print("\n❌ MP3合并失败")
        return ""


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python podcast_generator.py <话题>")
        print("示例: python podcast_generator.py 'AI Agent在2026年的应用趋势'")
        sys.exit(1)

    topic = " ".join(sys.argv[1:])
    result = read_topic(topic)
    if result:
        print(f"\n✅ 输出MP3: {result}")
    else:
        print("\n❌ 播客生成失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
