#!/usr/bin/env python3
"""
CH7-H: 图片生成器 — 多后端自动降级
支持: qwen-image-2.0-pro (百炼DashScope) → 即梦 → Stability AI
零外部依赖，使用subprocess调用curl
"""
import os
import sys
import json
import time
import uuid
import subprocess
from pathlib import Path
from typing import Optional, List, Dict

# ──────────────────────────────────────────────
# 配置
# ──────────────────────────────────────────────

DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
# 即梦API配置 — 可以在.env中设置
JIMENG_API_KEY = os.environ.get("JIMENG_API_KEY", "")
STABILITY_API_KEY = os.environ.get("STABILITY_API_KEY", "")

OUTPUT_DIR = "/tmp/hermes-images"
BACKENDS = ["qwen", "jimeng", "stability"]  # 降级顺序

VALID_SIZES = {
    "qwen": ["1024*1024", "1440*1440", "720*1280", "1280*720"],
    "jimeng": ["1024x1024", "1024x768", "768x1024", "1280x720", "720x1280"],
    "stability": ["1024x1024", "1152x896", "896x1152", "1216x832", "832x1216",
                  "1344x768", "768x1344", "1536x640", "640x1536"],
}

STYLE_MAP = {
    "写实": "写实摄影风格，真实光影，细节丰富",
    "卡通": "卡通动漫风格，明亮色彩，线条清晰",
    "3D": "3D渲染风格，Blender质感，立体感强",
    "水墨": "中国传统水墨画风格，意境淡雅",
    "插画": "手绘插画风格，温暖质感",
    "电商": "白底商品图，8K产品摄影，商业摄影",
    "油画": "油画风格，厚重笔触，古典质感",
}


# ──────────────────────────────────────────────
# 后端1: 百炼 DashScope (qwen-image-2.0-pro)
# ──────────────────────────────────────────────

def _call_qwen(prompt: str, style: str, size: str, output_path: str) -> Optional[str]:
    """通过curl调用百炼DashScope API生成图片"""
    if not DASHSCOPE_API_KEY:
        print("  [qwen] ⚠️  DASHSCOPE_API_KEY 未配置")
        return None

    # 合并风格
    style_desc = STYLE_MAP.get(style, style)
    full_prompt = f"{prompt}，{style_desc}" if style else prompt

    # 转换size格式: 1024*1024
    size_qwen = size.replace("x", "*").replace("X", "*")
    if size_qwen not in VALID_SIZES["qwen"]:
        # 尝试转换
        if "*" in size_qwen:
            pass  # 保持原样
        else:
            size_qwen = "1024*1024"

    # 准备请求体
    payload = {
        "model": "qwen-image-2.0-pro",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": full_prompt}]
                }
            ]
        },
        "parameters": {
            "size": size_qwen,
            "n": 1
        }
    }

    tmp_json = f"/tmp/hermes_qwen_req_{uuid.uuid4().hex[:8]}.json"
    with open(tmp_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)

    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
    cmd = [
        "curl", "-s", "-X", "POST", url,
        "-H", f"Authorization: Bearer {DASHSCOPE_API_KEY}",
        "-H", "Content-Type: application/json",
        "-d", f"@{tmp_json}"
    ]

    print(f"  [qwen] 🎨 调用百炼 qwen-image-2.0-pro...")
    print(f"  [qwen]    尺寸: {size_qwen}, 风格: {style or '默认'}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        os.unlink(tmp_json)

        if result.returncode != 0:
            print(f"  [qwen] ❌ curl失败: {result.stderr[:200]}")
            return None

        response = json.loads(result.stdout)

        # 解析响应
        if "output" in response and "results" in response["output"]:
            results = response["output"]["results"]
            if results and len(results) > 0:
                img_url = results[0].get("url", "")
                if img_url:
                    return _download_image(img_url, output_path, "qwen")
        
        # 尝试另一种响应格式
        if "output" in response:
            output = response["output"]
            if hasattr(output, "choices") or "choices" in str(output):
                choices = output.get("choices", [])
                if choices:
                    for choice in choices:
                        if "message" in choice:
                            content = choice["message"].get("content", [])
                            for item in content:
                                if isinstance(item, dict) and "image" in item:
                                    img_url = item["image"]
                                    return _download_image(img_url, output_path, "qwen")

        print(f"  [qwen] ⚠️  响应格式异常: {json.dumps(response, ensure_ascii=False)[:300]}")
        return None

    except subprocess.TimeoutExpired:
        print(f"  [qwen] ⏰ 请求超时")
        try: os.unlink(tmp_json)
        except: pass
        return None
    except Exception as e:
        print(f"  [qwen] ❌ 异常: {e}")
        try: os.unlink(tmp_json)
        except: pass
        return None


# ──────────────────────────────────────────────
# 后端2: 即梦 API
# ──────────────────────────────────────────────

def _call_jimeng(prompt: str, style: str, size: str, output_path: str) -> Optional[str]:
    """通过curl调用即梦API生成图片"""
    if not JIMENG_API_KEY:
        print("  [jimeng] ⚠️  JIMENG_API_KEY 未配置")
        return None

    style_desc = STYLE_MAP.get(style, style)
    full_prompt = f"{prompt}，{style_desc}" if style else prompt
    
    # 即梦size格式: 1024x1024
    size_jm = size.replace("*", "x").replace("X", "x")
    # 检查是否支持
    valid_sizes = VALID_SIZES["jimeng"]
    if size_jm not in valid_sizes:
        size_jm = "1024x1024"

    payload = {
        "model": "jimeng-v2",
        "prompt": full_prompt,
        "size": size_jm,
        "n": 1,
    }

    tmp_json = f"/tmp/hermes_jimeng_req_{uuid.uuid4().hex[:8]}.json"
    with open(tmp_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)

    url = "https://api.jimeng.ai/v1/images/generations"
    cmd = [
        "curl", "-s", "-X", "POST", url,
        "-H", f"Authorization: Bearer {JIMENG_API_KEY}",
        "-H", "Content-Type: application/json",
        "-d", f"@{tmp_json}"
    ]

    print(f"  [jimeng] 🎨 调用即梦 jimage-v2...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        os.unlink(tmp_json)

        if result.returncode != 0:
            print(f"  [jimeng] ❌ curl失败: {result.stderr[:200]}")
            return None

        response = json.loads(result.stdout)
        
        # 响应格式: { "data": [ { "url": "..." } ] }
        if "data" in response and len(response["data"]) > 0:
            img_url = response["data"][0].get("url", "")
            if img_url:
                return _download_image(img_url, output_path, "jimeng")

        print(f"  [jimeng] ⚠️  响应格式异常: {json.dumps(response, ensure_ascii=False)[:300]}")
        return None

    except subprocess.TimeoutExpired:
        print(f"  [jimeng] ⏰ 请求超时")
        try: os.unlink(tmp_json)
        except: pass
        return None
    except Exception as e:
        print(f"  [jimeng] ❌ 异常: {e}")
        try: os.unlink(tmp_json)
        except: pass
        return None


# ──────────────────────────────────────────────
# 后端3: Stability AI
# ──────────────────────────────────────────────

def _call_stability(prompt: str, style: str, size: str, output_path: str) -> Optional[str]:
    """通过curl调用Stability AI API生成图片"""
    if not STABILITY_API_KEY:
        print("  [stability] ⚠️  STABILITY_API_KEY 未配置")
        return None

    style_desc = STYLE_MAP.get(style, style)
    full_prompt = f"{prompt}，{style_desc}" if style else prompt
    
    # Stability size格式: 1024x1024
    size_st = size.replace("*", "x").replace("X", "x")
    valid_sizes = VALID_SIZES["stability"]
    if size_st not in valid_sizes:
        size_st = "1024x1024"

    payload = json.dumps({
        "text_prompts": [{"text": full_prompt, "weight": 1}],
        "cfg_scale": 7,
        "height": int(size_st.split("x")[1]),
        "width": int(size_st.split("x")[0]),
        "samples": 1,
        "steps": 30,
    })

    url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
    cmd = [
        "curl", "-s", "-X", "POST", url,
        "-H", f"Authorization: Bearer {STABILITY_API_KEY}",
        "-H", "Content-Type: application/json",
        "-H", "Accept: application/json",
        "-d", payload,
    ]

    print(f"  [stability] 🎨 调用 Stability AI SDXL...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            print(f"  [stability] ❌ curl失败: {result.stderr[:200]}")
            return None

        response = json.loads(result.stdout)
        
        if "artifacts" in response and len(response["artifacts"]) > 0:
            import base64
            img_b64 = response["artifacts"][0].get("base64", "")
            if img_b64:
                img_data = base64.b64decode(img_b64)
                Path(output_path).write_bytes(img_data)
                print(f"  [stability] ✅ 已保存: {output_path} ({len(img_data)/1024:.0f}KB)")
                return output_path

        print(f"  [stability] ⚠️  响应格式异常: {json.dumps(response, ensure_ascii=False)[:300]}")
        return None

    except subprocess.TimeoutExpired:
        print(f"  [stability] ⏰ 请求超时")
        return None
    except Exception as e:
        print(f"  [stability] ❌ 异常: {e}")
        return None


# ──────────────────────────────────────────────
# 通用下载
# ──────────────────────────────────────────────

def _download_image(url: str, output_path: str, backend: str) -> Optional[str]:
    """使用curl下载图片"""
    cmd = [
        "curl", "-s", "-L", url,
        "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "-H", "Accept: image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        "-o", output_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        if result.returncode == 0 and os.path.getsize(output_path) > 200:
            size_kb = os.path.getsize(output_path) / 1024
            print(f"  [{backend}] ✅ 已保存: {output_path} ({size_kb:.0f}KB)")
            return output_path
        else:
            print(f"  [{backend}] ⚠️  下载失败或文件过小")
            return None
    except Exception as e:
        print(f"  [{backend}] ❌ 下载异常: {e}")
        return None


# ──────────────────────────────────────────────
# 主入口: 多后端降级生成
# ──────────────────────────────────────────────

def generate_image(
    prompt: str,
    style: str = "",
    size: str = "1024*1024",
    preferred_backend: str = "qwen",
    output_path: Optional[str] = None,
) -> Optional[str]:
    """
    生成图片，支持多后端自动降级。

    Args:
        prompt: 图片描述提示词
        style: 风格 (写实/卡通/3D/水墨/插画/电商/油画)
        size: 尺寸 (如 1024*1024)
        preferred_backend: 首选后端 (qwen/jimeng/stability)
        output_path: 保存路径，默认 /tmp/hermes_images/hermes_<uuid>.png

    Returns:
        str: 图片保存路径，失败返回 None
    """
    # 确保输出目录存在
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    if not output_path:
        output_path = os.path.join(OUTPUT_DIR, f"hermes_{uuid.uuid4().hex[:12]}.png")

    # 后端映射
    backend_funcs = {
        "qwen": _call_qwen,
        "jimeng": _call_jimeng,
        "stability": _call_stability,
    }

    # 构建降级顺序
    if preferred_backend in BACKENDS:
        idx = BACKENDS.index(preferred_backend)
        backends = BACKENDS[idx:] + BACKENDS[:idx]
    else:
        backends = BACKENDS

    print(f"🎨 图片生成")
    print(f"   提示词: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
    print(f"   风格: {style or '默认'}")
    print(f"   尺寸: {size}")
    print(f"   首选后端: {preferred_backend}")
    print(f"   降级顺序: {' → '.join(backends)}")
    print()

    # 尝试每个后端
    for backend in backends:
        print(f"── [{backend}] 尝试 ──")
        func = backend_funcs.get(backend)
        if func:
            result = func(prompt, style, size, output_path)
            if result:
                print(f"\n✅ 图片已生成: {result}")
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
        description="CH7-H: 图片生成器 — 多后端自动降级"
    )
    parser.add_argument("--prompt", "-p", required=True, help="图片描述提示词")
    parser.add_argument("--style", "-s", default="",
                        choices=list(STYLE_MAP.keys()) + [""],
                        help="风格: " + "/".join(STYLE_MAP.keys()))
    parser.add_argument("--size", default="1024*1024", help="尺寸 (如 1024*1024)")
    parser.add_argument("--backend", default="qwen",
                        choices=BACKENDS, help="首选后端")
    parser.add_argument("--output", "-o", help="输出文件路径")

    args = parser.parse_args()

    result = generate_image(
        prompt=args.prompt,
        style=args.style,
        size=args.size,
        preferred_backend=args.backend,
        output_path=args.output,
    )

    if result:
        print(f"\n📎 输出: {result}")
    else:
        print(f"\n❌ 生成失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
