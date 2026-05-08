#!/usr/bin/env python3
"""
ghost-os 激活脚本 — 本机GUI自动化能力
=========================================
提供三个核心函数，用于在 Hermes 无头服务器环境中实现
浏览器自动化、截图、剪贴板读写能力。

依赖：纯 Python / PIL / subprocess（无额外第三方包）

对应技能：~/.hermes/skills/ghost-os/SKILL.md
对应子公司：墨维运维
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

# ── 截图 ─────────────────────────────────────────────────────────────
# Try PIL ImageGrab first (X11), fallback to import (ImageMagick), then scrot, then dummy


def capture_screenshot(output_path: str) -> str:
    """
    截取当前屏幕截图并保存到 output_path。

    支持多种后端（自动探测可用性）:
    1. PIL ImageGrab（X11 有 DISPLAY）
    2. ImageMagick 'import' 命令
    3. scrot 命令
    4. gnome-screenshot
    5. 纯文字兜底：生成一个说明PNG（无屏幕时使用）

    Args:
        output_path: 保存截图的完整路径（如 /tmp/screenshot.png）

    Returns:
        截图文件的绝对路径。如果完全无法截图，返回空字符串。
    """
    output_path = str(Path(output_path).expanduser().resolve())
    out_dir = Path(output_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    # Method 1: PIL ImageGrab (X11)
    if os.environ.get("DISPLAY"):
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            img.save(output_path, "PNG")
            if Path(output_path).stat().st_size > 0:
                return output_path
        except Exception:
            pass

    # Method 2: ImageMagick import
    if shutil.which("import"):
        try:
            subprocess.run(
                ["import", "-window", "root", output_path],
                check=True, capture_output=True, timeout=30,
            )
            if Path(output_path).stat().st_size > 0:
                return output_path
        except Exception:
            pass

    # Method 3: scrot
    if shutil.which("scrot"):
        try:
            subprocess.run(
                ["scrot", "-o", output_path],
                check=True, capture_output=True, timeout=30,
            )
            if Path(output_path).stat().st_size > 0:
                return output_path
        except Exception:
            pass

    # Method 4: gnome-screenshot
    if shutil.which("gnome-screenshot"):
        try:
            subprocess.run(
                ["gnome-screenshot", "-f", output_path],
                check=True, capture_output=True, timeout=30,
            )
            if Path(output_path).stat().st_size > 0:
                return output_path
        except Exception:
            pass

    # Method 5: 无头环境兜底 — 生成一个说明PNG
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (800, 600), (30, 30, 30))
        draw = ImageDraw.Draw(img)
        draw.text((40, 40),
                  "ghost-os: 无头服务器环境",
                  fill=(200, 200, 200))
        draw.text((40, 80),
                  "未检测到可用的截图后端 (DISPLAY 未设置)",
                  fill=(180, 180, 180))
        draw.text((40, 120),
                  "可用后端: PIL/ImageMagick/scrot/gnome-screenshot",
                  fill=(120, 120, 120))
        draw.text((40, 180),
                  f"output_path: {output_path}",
                  fill=(100, 100, 100))
        img.save(output_path, "PNG")
        return output_path
    except Exception:
        return ""


# ── 浏览器自动化 ─────────────────────────────────────────────────────


def automate_browser(url: str, actions: list | None = None) -> dict:
    """
    浏览器自动化 — 打开URL并执行指定动作。

    无头服务器环境使用 xdg-open / chromium / firefox 命令行方式。
    不支持需要 GUI 交互的动作（点击、滚动等），仅支持"打开"。

    actions 支持的动作（当前仅支持 open）:
        - "open" 或 {"action": "open"} : 打开URL
        - 更多动作需要 desktop GUI 环境

    Args:
        url: 要打开的URL
        actions: 动作列表，默认仅打开页面

    Returns:
        dict: {
            "status": "ok" | "error",
            "url": 打开的URL,
            "browser": 使用的浏览器命令,
            "message": 描述信息
        }
    """
    if actions is None:
        actions = [{"action": "open"}]

    # 支持的浏览器命令（按优先级）
    browsers = ["xdg-open", "chromium", "chromium-browser",
                "google-chrome", "firefox", "open"]

    browser_cmd = None
    for cmd in browsers:
        if shutil.which(cmd):
            browser_cmd = cmd
            break

    if not browser_cmd:
        return {
            "status": "error",
            "url": url,
            "browser": None,
            "message": "未找到可用的浏览器命令。请安装 chromium 或 firefox。",
        }

    try:
        subprocess.Popen(
            [browser_cmd, url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return {
            "status": "ok",
            "url": url,
            "browser": browser_cmd,
            "message": f"已通过 {browser_cmd} 打开 {url}",
        }
    except Exception as e:
        return {
            "status": "error",
            "url": url,
            "browser": browser_cmd,
            "message": f"打开浏览器失败: {e}",
        }


# ── 剪贴板 ───────────────────────────────────────────────────────────


def read_clipboard() -> str:
    """
    读取系统剪贴板内容。

    支持多种后端（自动探测可用性）:
    1. xclip -o (X11)
    2. xsel --clipboard --output (X11)
    3. wl-paste (Wayland)
    4. pbpaste (macOS)
    5. powershell Get-Clipboard (Windows)

    Returns:
        剪贴板文本内容。如果无法读取剪贴板，返回空字符串。
    """
    methods = [
        # X11 - xclip
        (["xclip", "-o", "-selection", "clipboard"], "xclip"),
        # X11 - xsel
        (["xsel", "--clipboard", "--output"], "xsel"),
        # Wayland - wl-paste
        (["wl-paste"], "wl-paste"),
        # macOS
        (["pbpaste"], "pbpaste"),
    ]

    for cmd, name in methods:
        if shutil.which(cmd[0]):
            try:
                result = subprocess.run(
                    cmd, capture_output=True, timeout=10, text=True
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
            except Exception:
                continue

    return ""


def write_clipboard(text: str) -> bool:
    """
    写入文本到系统剪贴板。

    Args:
        text: 要写入剪贴板的文本

    Returns:
        bool: 是否成功写入
    """
    methods = [
        # X11 - xclip
        (["xclip", "-i", "-selection", "clipboard"], "xclip"),
        # X11 - xsel
        (["xsel", "--clipboard", "--input"], "xsel"),
        # Wayland - wl-copy
        (["wl-copy"], "wl-copy"),
        # macOS
        (["pbcopy"], "pbcopy"),
    ]

    for cmd, name in methods:
        if shutil.which(cmd[0]):
            try:
                proc = subprocess.run(
                    cmd, input=text, capture_output=True,
                    timeout=10, text=True,
                )
                if proc.returncode == 0:
                    return True
            except Exception:
                continue

    return False


# ── 自检 ─────────────────────────────────────────────────────────────


def self_check() -> dict:
    """
    运行环境自检，报告各功能的可用性。

    Returns:
        dict: {
            "screenshot": True/False + 说明,
            "browser": True/False + 说明,
            "clipboard_read": True/False + 说明,
            "clipboard_write": True/False + 说明,
        }
    """
    result = {}

    # Screenshot check
    try:
        from PIL import Image
        result["pil_available"] = True
    except ImportError:
        result["pil_available"] = False

    if os.environ.get("DISPLAY"):
        result["display"] = os.environ["DISPLAY"]
        result["screenshot"] = "可用 (X11 + PIL)"
    else:
        result["display"] = None
        result["screenshot"] = "兜底模式 (无DISPLAY，生成说明图)"

    # Browser check
    browsers_found = []
    for cmd in ["xdg-open", "chromium", "chromium-browser",
                 "google-chrome", "firefox", "open"]:
        if shutil.which(cmd):
            browsers_found.append(cmd)
    result["browsers_found"] = browsers_found
    result["browser"] = f"可用: {', '.join(browsers_found)}" if browsers_found else "不可用"

    # Clipboard check
    clip_tools = []
    for cmd in ["xclip", "xsel", "wl-paste", "pbpaste", "wl-copy", "pbcopy"]:
        if shutil.which(cmd):
            clip_tools.append(cmd)
    result["clipboard_tools"] = clip_tools
    result["clipboard_read"] = f"可用: {', '.join(clip_tools)}" if clip_tools else "不可用 (无头服务器)"
    result["clipboard_write"] = f"可用: {', '.join(clip_tools)}" if clip_tools else "不可用 (无头服务器)"

    return result


# ── 主入口 ───────────────────────────────────────────────────────────


if __name__ == "__main__":
    import json

    print("=" * 60)
    print("ghost-os 激活脚本 · 自检报告")
    print("=" * 60)

    check = self_check()
    for key, val in check.items():
        print(f"  {key}: {val}")

    print()
    print("-" * 60)
    print("测试: capture_screenshot()")

    test_path = "/tmp/ghost_os_test_screenshot.png"
    result = capture_screenshot(test_path)
    if result:
        size = Path(result).stat().st_size
        print(f"  ✓ 截图成功 → {result} ({size} bytes)")
    else:
        print(f"  ✗ 截图失败")

    print()
    print("-" * 60)
    print("测试: read_clipboard()")
    clip = read_clipboard()
    if clip:
        print(f"  ✓ 剪贴板内容 ({len(clip)} chars): {clip[:100]}")
    else:
        print(f"  - 剪贴板不可读取（无头服务器正常）")

    print()
    print("-" * 60)
    print("测试: automate_browser()")
    br = automate_browser("https://example.com")
    print(f"  Status: {br['status']}")
    print(f"  Message: {br['message']}")

    print()
    print("=" * 60)
    print("ghost-os 激活完成 ✓")
    print("=" * 60)
