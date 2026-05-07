"""墨播 — 短视频脚本生成"""
import json


async def generate_script(topic: str, duration: int = 60, platform: str = "抖音") -> str:
    """生成短视频脚本"""
    return (
        f"【{topic}】短视频脚本 ({platform}, {duration}秒)\n\n"
        f"开场（0-5秒）：抓住注意力\n"
        f"  「今天我们来聊一聊{topic}」\n\n"
        f"正文（5-{duration-10}秒）：核心内容\n"
        f"  · 第一点：什么是{topic}？\n"
        f"  · 第二点：为什么这个很重要？\n"
        f"  · 第三点：如何开始？\n\n"
        f"结尾（{duration-10}-{duration}秒）：行动号召\n"
        f"  「关注我，了解更多{topic}相关内容」"
    )


async def generate_video(topic: str, engine: str = "mpt") -> dict:
    """全自动生成短视频（调用外部引擎）"""
    script = await generate_script(topic)
    return {
        "topic": topic,
        "script": script,
        "engine": engine,
        "status": "script_ready",
        "next_step": f"python -m molib video render --topic '{topic}' --engine {engine}",
    }
