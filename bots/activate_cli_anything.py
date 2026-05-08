#!/usr/bin/env python3
"""
cli-anything 激活脚本 — CLI Agent原生化引擎
=============================================
将任意命令包装为标准化CLI接口，让所有软件变成Agent原生CLI命令。

核心功能：
  - cli_fy(cmd_spec): 将任意命令包装为标准化CLI接口

对应技能：~/.hermes/skills/cli-anything/SKILL.md
对应子公司：墨码开发（软件开发、代码编写、技术实现）

依赖：纯 Python / subprocess / curl / hs（无额外第三方包）
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


# ═══════════════════════════════════════════════════════════════════
# 核心函数：cli_fy — 将任意命令包装为标准化CLI接口
# ═══════════════════════════════════════════════════════════════════

def cli_fy(cmd_spec: dict) -> dict:
    """
    将任意命令包装为标准化CLI接口。

    接收一个命令规格字典，按规范解析参数并执行，
    返回结构化的JSON输出。

    cmd_spec 格式：
    {
        "command": "要执行的命令字符串（支持 {param} 模板）",
        "params": {
            "param_name": {
                "type": "str|int|bool|choice",
                "default": "默认值",
                "choices": ["a", "b"],  # 仅 choice 类型需要
                "description": "参数说明"
            }
        },
        "required_params": ["param1"],
        "output_format": "json|text",    # 输出格式
        "description": "命令用途说明",
        "timeout": 30,                   # 超时秒数（默认30）
        "shell": false,                  # 是否使用shell执行
        "workdir": "/path/to/dir",       # 工作目录（可选）
    }

    返回：
    {
        "status": "ok" | "error",
        "command": "实际执行的命令",
        "stdout": "标准输出",
        "stderr": "标准错误",
        "return_code": 0,
        "parsed_output": {...}  # 如果是json格式，自动解析
    }
    """
    # ── 验证命令规格 ────────────────────────────────────────────────
    if not isinstance(cmd_spec, dict):
        return {
            "status": "error",
            "command": "",
            "stdout": "",
            "stderr": "cmd_spec 必须是字典类型",
            "return_code": -1,
            "parsed_output": None,
        }

    command_template = cmd_spec.get("command", "")
    if not command_template:
        return {
            "status": "error",
            "command": "",
            "stdout": "",
            "stderr": "cmd_spec 必须包含 command 字段",
            "return_code": -1,
            "parsed_output": None,
        }

    params = cmd_spec.get("params", {})
    required_params = cmd_spec.get("required_params", [])
    output_format = cmd_spec.get("output_format", "text")
    timeout = cmd_spec.get("timeout", 30)
    use_shell = cmd_spec.get("shell", False)
    workdir = cmd_spec.get("workdir")

    # ── 参数校验 ────────────────────────────────────────────────────
    missing = [p for p in required_params if p not in params]
    if missing:
        return {
            "status": "error",
            "command": "",
            "stdout": "",
            "stderr": f"缺少必需参数: {', '.join(missing)}",
            "return_code": -1,
            "parsed_output": None,
        }

    # ── 参数类型校验并填充模板 ────────────────────────────────────────
    filled_params = {}
    for param_name, param_spec in params.items():
        value = param_spec.get("default", "")
        param_type = param_spec.get("type", "str")
        choices = param_spec.get("choices", [])

        # 如果参数值就是提供的值（由调用者直接传入）
        if "value" in param_spec:
            value = param_spec["value"]

        # type check / coercion
        if param_type == "int":
            try:
                value = int(value)
            except (ValueError, TypeError):
                return {
                    "status": "error",
                    "command": "",
                    "stdout": "",
                    "stderr": f"参数 '{param_name}' 需要整数类型，但收到 '{value}'",
                    "return_code": -1,
                    "parsed_output": None,
                }
        elif param_type == "bool":
            if isinstance(value, str):
                value = value.lower() in ("true", "1", "yes", "y")
            value = str(value).lower()
        elif param_type == "choice":
            if choices and value not in choices:
                return {
                    "status": "error",
                    "command": "",
                    "stdout": "",
                    "stderr": f"参数 '{param_name}' 必须是 {choices} 之一，但收到 '{value}'",
                    "return_code": -1,
                    "parsed_output": None,
                }

        filled_params[param_name] = str(value)
        param_spec["value"] = value

    # ── 填充命令模板 ────────────────────────────────────────────────
    try:
        final_command = command_template.format(**filled_params)
    except KeyError as e:
        return {
            "status": "error",
            "command": command_template,
            "stdout": "",
            "stderr": f"命令模板缺少参数: {e}",
            "return_code": -1,
            "parsed_output": None,
        }

    # ── 检查命令是否可用 ─────────────────────────────────────────────
    base_cmd = final_command.split()[0]
    if not use_shell and not shutil.which(base_cmd):
        # 尝试 using /usr/bin/which or similar
        try:
            subprocess.run(
                ["which", base_cmd],
                capture_output=True, timeout=5,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {
                "status": "error",
                "command": final_command,
                "stdout": "",
                "stderr": f"命令 '{base_cmd}' 未找到，请先安装",
                "return_code": -1,
                "parsed_output": None,
            }

    # ── 执行命令 ────────────────────────────────────────────────────
    try:
        result = subprocess.run(
            final_command if use_shell else final_command.split(),
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=workdir,
            shell=use_shell,
        )

        stdout = result.stdout
        stderr = result.stderr
        return_code = result.returncode

        # ── 解析输出 ────────────────────────────────────────────────
        parsed_output = None
        if output_format == "json" and stdout.strip():
            try:
                parsed_output = json.loads(stdout)
            except json.JSONDecodeError:
                parsed_output = {"raw": stdout}

        status = "ok" if return_code == 0 else "error"

        return {
            "status": status,
            "command": final_command,
            "stdout": stdout,
            "stderr": stderr,
            "return_code": return_code,
            "parsed_output": parsed_output,
            "cmd_spec": cmd_spec,
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "command": final_command,
            "stdout": "",
            "stderr": f"命令执行超时（{timeout}秒）",
            "return_code": -1,
            "parsed_output": None,
        }
    except Exception as e:
        return {
            "status": "error",
            "command": final_command,
            "stdout": "",
            "stderr": f"执行失败: {e}",
            "return_code": -1,
            "parsed_output": None,
        }


# ═══════════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════════

def curl_fy(method: str = "GET", url: str = "",
            headers: dict = None, data: Any = None,
            timeout: int = 30) -> dict:
    """
    将 curl 请求包装为标准化CLI接口。

    Args:
        method: HTTP方法 (GET/POST/PUT/DELETE)
        url: 请求URL
        headers: 请求头字典
        data: 请求体数据（dict自动转JSON）
        timeout: 超时秒数

    Returns:
        cli_fy 标准返回
    """
    if headers is None:
        headers = {}

    # Build curl command parts
    parts = ["curl", "-s", "-L"]

    # Method
    if method.upper() != "GET":
        parts.extend(["-X", method.upper()])

    # Headers
    for key, val in headers.items():
        parts.extend(["-H", f"{key}: {val}"])

    # Data
    if data is not None:
        if isinstance(data, dict):
            data = json.dumps(data)
            parts.extend(["-H", "Content-Type: application/json"])
        parts.extend(["-d", data])

    # URL
    parts.append(url)

    # Timeout flags
    parts.extend(["--connect-timeout", "10", "--max-time", str(timeout)])

    cmd_spec = {
        "command": " ".join(parts),
        "params": {},
        "output_format": "text",
        "description": f"curl {method} {url}",
        "timeout": timeout + 10,
    }

    return cli_fy(cmd_spec)


def hs_fy(command: str, args: list = None) -> dict:
    """
    将 hs (Hermes Shell) 命令包装为标准化CLI接口。

    Args:
        command: hs 子命令 (如 "search", "memory", "skill")
        args: 额外参数列表

    Returns:
        cli_fy 标准返回
    """
    if args is None:
        args = []

    cmd_parts = ["hs", command] + args
    cmd_str = " ".join(cmd_parts)

    cmd_spec = {
        "command": cmd_str,
        "params": {},
        "output_format": "text",
        "description": f"hs {command} {' '.join(args)}",
        "timeout": 30,
    }

    return cli_fy(cmd_spec)


# ═══════════════════════════════════════════════════════════════════
# 自检
# ═══════════════════════════════════════════════════════════════════

def self_check() -> dict:
    """
    运行环境自检，报告cli-anything功能可用性。

    Returns:
        dict: 各功能检查结果
    """
    result = {}

    # Check core tools availability
    tools_to_check = ["curl", "python3", "sh", "which", "hs"]
    available_tools = {}
    for tool in tools_to_check:
        available_tools[tool] = shutil.which(tool) is not None
        if not available_tools[tool]:
            # Try 'which' as fallback
            try:
                subprocess.run(["which", tool], capture_output=True, timeout=3, check=True)
                available_tools[tool] = True
            except Exception:
                pass

    result["available_tools"] = available_tools

    # Test cli_fy with a simple echo command
    test_spec = {
        "command": "echo '{message}'",
        "params": {
            "message": {
                "type": "str",
                "default": "cli-anything test OK",
                "description": "测试消息"
            }
        },
        "output_format": "text",
        "description": "cli-anything 自检测试",
        "timeout": 10,
    }

    try:
        test_result = cli_fy(test_spec)
        result["cli_fy_test"] = test_result["status"] == "ok"
        result["cli_fy_output"] = test_result["stdout"].strip()
    except Exception as e:
        result["cli_fy_test"] = False
        result["cli_fy_error"] = str(e)

    # Test curl wrapper
    try:
        curl_result = curl_fy("GET", "https://httpbin.org/get", timeout=10)
        result["curl_fy_test"] = curl_result["status"] == "ok"
    except Exception:
        result["curl_fy_test"] = False

    return result


# ═══════════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("cli-anything 激活脚本 · 自检报告")
    print("=" * 60)

    check = self_check()
    for key, val in check.items():
        if isinstance(val, dict):
            print(f"\n  {key}:")
            for k, v in val.items():
                icon = "✓" if v else "✗"
                print(f"    {icon} {k}: {v}")
        else:
            icon = "✓" if val else "✗"
            print(f"  {icon} {key}: {val}")

    print()
    print("-" * 60)
    print("测试: cli_fy() — 基本命令包装")

    spec = {
        "command": "echo 'Hello from cli-anything! The time is $(date)'",
        "params": {},
        "output_format": "text",
        "description": "测试命令",
        "timeout": 10,
        "shell": True,
    }
    result = cli_fy(spec)
    print(f"  Status: {result['status']}")
    print(f"  Command: {result['command']}")
    print(f"  Output: {result['stdout'].strip()}")

    print()
    print("-" * 60)
    print("测试: cli_fy() — 带参数的curl包装")

    curl_spec = {
        "command": "curl -s -L 'https://httpbin.org/get' --connect-timeout 5 --max-time 10",
        "params": {},
        "output_format": "json",
        "description": "curl测试",
        "timeout": 15,
    }
    curl_result = cli_fy(curl_spec)
    print(f"  Status: {curl_result['status']}")
    if curl_result['status'] == 'ok' and curl_result['parsed_output']:
        print(f"  Parsed JSON keys: {list(curl_result['parsed_output'].keys())}")

    print()
    print("=" * 60)
    print("cli-anything 激活完成 ✓")
    print("=" * 60)
