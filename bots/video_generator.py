#!/usr/bin/env python3
"""
CH4-G MoneyPrinterTurbo 视频生成器 —— 占位脚本

MoneyPrinterTurbo fork 尚未部署到 ~/hermes-os/fork_repos/。
本脚本提供：
1. generate_video() 接口占位 —— 部署后可调用
2. 部署指引，引导用户执行部署流程

完整部署步骤请见：~/hermes-os/docs/mpt_deployment.md
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime

# ===== 配置 =====
BASE_DIR = Path.home() / "hermes-os"
FORK_REPOS_DIR = BASE_DIR / "fork_repos"
MPT_DIR = FORK_REPOS_DIR / "MoneyPrinterTurbo"

# MPT API 配置（部署后生效）
MPT_API_BASE = os.environ.get("MPT_API_BASE", "http://localhost:8899")
MPT_API_KEY = os.environ.get("MPT_API_KEY", "")


# ===== 检查部署状态 =====

def check_mpt_installed() -> bool:
    """检查 MoneyPrinterTurbo 是否已部署"""
    if not MPT_DIR.exists():
        return False
    # 检查关键文件
    required = [
        MPT_DIR / "main.py",
        MPT_DIR / "app.py",
        MPT_DIR / "requirements.txt",
    ]
    return all(p.exists() for p in required)


def check_mpt_running() -> bool:
    """检查 MPT 服务是否在运行（通过 curl 健康检查）"""
    if not check_mpt_installed():
        return False
    try:
        cmd = ["curl", "-s", "--connect-timeout", "5", "--max-time", "10",
               f"{MPT_API_BASE}/health"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return result.returncode == 0
    except Exception:
        return False


# ===== 主接口 =====

def generate_video(topic: str, duration: str = "60s") -> dict:
    """
    调用 MoneyPrinterTurbo API 生成视频

    Args:
        topic: 视频主题/文案
        duration: 视频时长（如 "60s", "120s"）

    Returns:
        dict: {
            "success": bool,
            "video_path": str or None,
            "message": str,
            "task_id": str or None
        }
    """
    print(f"🎬 MoneyPrinterTurbo 视频生成器")
    print(f"   话题: {topic}")
    print(f"   时长: {duration}")
    print("=" * 50)

    # Step 1: 检查是否已部署
    if not check_mpt_installed():
        msg = (
            "MoneyPrinterTurbo 尚未部署到本地。\n"
            f"  Fork目录: {MPT_DIR}\n"
            "  请参阅部署文档: ~/hermes-os/docs/mpt_deployment.md\n"
            "  或运行: cat ~/hermes-os/docs/mpt_deployment.md"
        )
        print(f"❌ {msg}")
        return {"success": False, "video_path": None, "message": msg, "task_id": None}

    if not check_mpt_running():
        msg = (
            "MoneyPrinterTurbo 已安装但服务未运行。\n"
            f"  请启动服务: cd {MPT_DIR} && python app.py\n"
            f"  服务默认运行在 {MPT_API_BASE}"
        )
        print(f"❌ {msg}")
        return {"success": False, "video_path": None, "message": msg, "task_id": None}

    # Step 2: 调用 MPT API
    print("⏳ 正在提交视频生成任务...")

    # MPT API 接口: POST /api/v1/video
    # 不同版本的 MPT 接口可能略有差异
    payload = json.dumps({
        "topic": topic,
        "duration": duration,
        "style": "科技感",
        "resolution": "1920x1080",
        "bgm_type": "auto",
        "subtitle_enabled": True,
    }, ensure_ascii=False)

    cmd = [
        "curl", "-s", "-w", "\n%{{http_code}}",
        "-X", "POST",
        f"{MPT_API_BASE}/api/v1/video",
        "-H", "Content-Type: application/json",
        "-H", f"Authorization: Bearer {MPT_API_KEY}" if MPT_API_KEY else "-H",
        "-d", payload,
        "--connect-timeout", "10",
        "--max-time", "600",  # 视频生成可能需要较长时间
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=610)
        lines = result.stdout.strip().split("\n")
        http_code = lines[-1].strip() if lines else "000"
        body = "\n".join(lines[:-1])

        if http_code == "200":
            try:
                resp = json.loads(body)
                video_path = resp.get("data", {}).get("video_url", resp.get("video_path", ""))
                task_id = resp.get("data", {}).get("task_id", resp.get("task_id", ""))
                print(f"✅ 视频生成成功!")
                print(f"   视频路径: {video_path}")
                print(f"   任务ID: {task_id}")
                return {
                    "success": True,
                    "video_path": video_path,
                    "message": "视频生成成功",
                    "task_id": task_id,
                }
            except json.JSONDecodeError:
                print(f"⚡ API返回非JSON内容，原始响应: {body[:200]}")
                return {
                    "success": True,
                    "video_path": body.strip(),
                    "message": "视频生成成功（原始响应）",
                    "task_id": None,
                }
        else:
            error_msg = f"API返回HTTP {http_code}: {body[:300]}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "video_path": None,
                "message": error_msg,
                "task_id": None,
            }

    except subprocess.TimeoutExpired:
        msg = "视频生成请求超时（>10分钟）"
        print(f"❌ {msg}")
        return {"success": False, "video_path": None, "message": msg, "task_id": None}
    except Exception as e:
        msg = f"请求异常: {e}"
        print(f"❌ {msg}")
        return {"success": False, "video_path": None, "message": msg, "task_id": None}


def check_status():
    """检查 MPT 部署和运行状态"""
    installed = check_mpt_installed()
    running = check_mpt_running()

    print("📊 MoneyPrinterTurbo 状态检查")
    print("=" * 40)
    print(f"  已安装: {'✅' if installed else '❌'} {MPT_DIR}")
    print(f"  运行中: {'✅' if running else '❌'} {MPT_API_BASE}")
    if not installed:
        print(f"  📋 部署指南: cat ~/hermes-os/docs/mpt_deployment.md")
    return {"installed": installed, "running": running}


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python video_generator.py <话题> [时长]")
        print("示例:")
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
        print(f"\n✅ 完成！视频路径: {result['video_path']}")
    else:
        print(f"\n❌ 失败: {result['message']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
