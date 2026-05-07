"""9Router Worker — Token-Saving AI Proxy Layer

Runs 9router (decolua/9router ⭐4K) as a local HTTP proxy on port 20128.
Provides: FREE AI routing to 40+ providers, RTK Token Saver (20-40% compression),
multi-tier auto-fallback, and multi-account round-robin.

Exposes an OpenAI-compatible /v1 endpoint for Hermes clients.
"""

import os
import json
import time
import signal
import socket
import asyncio
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from dataclasses import dataclass
from typing import Any

from .base import SubsidiaryWorker, Task, WorkerResult

# ---------------------------------------------------------------------------
# 9router binary path
# ---------------------------------------------------------------------------
_NPM_PREFIX = os.environ.get("NPM_CONFIG_PREFIX") or os.path.expanduser("~/.npm-global")
_ROUTER_BIN = Path(_NPM_PREFIX) / "bin" / "9router"
_DEFAULT_PORT = 20128
_DEFAULT_HOST = "0.0.0.0"
_DATA_DIR = Path.home() / ".9router"


def _port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Quick TCP check to see if something is listening on the port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex((host, port)) == 0


def _find_router_pid(port: int = _DEFAULT_PORT) -> int | None:
    """Find the PID of a running 9router process via ps."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", f"9router.*--port {port}"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.strip().split()[0])
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass
    # Fallback: broader search
    try:
        result = subprocess.run(
            ["pgrep", "-f", "9router"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().splitlines():
                pid = int(line.strip())
                try:
                    cmdline = Path(f"/proc/{pid}/cmdline").read_text()
                    if "9router" in cmdline:
                        return pid
                except (OSError, FileNotFoundError):
                    pass
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass
    return None


def _save_pid(pid: int, port: int):
    """Write a PID marker so other processes know 9router is managed."""
    pid_dir = _DATA_DIR
    pid_dir.mkdir(parents=True, exist_ok=True)
    (pid_dir / "hermes.pid").write_text(f"{pid}\n{port}")


def _load_pid() -> tuple[int, int] | None:
    """Return (pid, port) if a hermes-managed 9router marker exists."""
    pid_file = _DATA_DIR / "hermes.pid"
    if pid_file.exists():
        parts = pid_file.read_text().strip().split()
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
    return None


def _clear_pid():
    pid_file = _DATA_DIR / "hermes.pid"
    if pid_file.exists():
        pid_file.unlink()


async def _check_health(port: int, timeout: float = 5.0) -> dict:
    """Ping 9router's /v1/models endpoint to verify it's alive."""
    url = f"http://127.0.0.1:{port}/v1/models"
    try:
        loop = asyncio.get_event_loop()
        req = urllib.request.Request(url, method="GET")
        resp = await loop.run_in_executor(
            None, lambda: urllib.request.urlopen(req, timeout=timeout)
        )
        body = resp.read().decode()
        data = json.loads(body)
        return {"status": "ok", "port": port, "models_count": len(data.get("data", []))}
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError) as exc:
        return {"status": "error", "port": port, "error": str(exc)}


async def _start(port: int = _DEFAULT_PORT, host: str = _DEFAULT_HOST) -> dict:
    """Start 9router as a detached background process (no-browser, log off)."""
    if _port_in_use(port):
        existing_pid = _find_router_pid(port)
        if existing_pid:
            _save_pid(existing_pid, port)
            return {"status": "ok", "message": f"9router already running on port {port} (pid={existing_pid})", "port": port}
        return {"status": "ok", "message": f"9router already listening on port {port}", "port": port}

    bin_path = str(_ROUTER_BIN)
    if not _ROUTER_BIN.exists():
        return {"status": "error", "error": f"9router binary not found at {bin_path}. Run: npm install -g 9router"}

    # Start in background — 9router detaches from parent so we use Popen
    proc = await asyncio.create_subprocess_exec(
        bin_path,
        "--port", str(port),
        "--host", host,
        "--no-browser",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )

    # Wait briefly for the process to start listening
    for _ in range(15):
        await asyncio.sleep(0.3)
        if _port_in_use(port):
            break

    if not _port_in_use(port):
        return {"status": "error", "error": "9router failed to start within timeout (server may launch in background)"}

    # Find the actual PID (9router may detach/fork)
    actual_pid = _find_router_pid(port) or (proc.pid if proc.returncode is None else None)
    if actual_pid:
        _save_pid(actual_pid, port)

    return {"status": "ok", "message": f"9router started on port {port}", "port": port}


async def _stop() -> dict:
    """Gracefully stop the managed 9router process."""
    # Try killing by PID file first
    pid_info = _load_pid()
    if pid_info:
        old_pid, port = pid_info
        try:
            os.kill(old_pid, signal.SIGTERM)
            # Wait a moment for graceful shutdown
            for _ in range(10):
                await asyncio.sleep(0.3)
                if not _port_in_use(port):
                    break
            if _port_in_use(port):
                try:
                    os.kill(old_pid, signal.SIGKILL)
                    await asyncio.sleep(0.5)
                except ProcessLookupError:
                    pass
            _clear_pid()
            return {"status": "ok", "message": f"9router (pid={old_pid}) stopped"}
        except ProcessLookupError:
            _clear_pid()

    # Fallback: find and kill any 9router process
    pid = _find_router_pid()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            for _ in range(10):
                await asyncio.sleep(0.3)
                if not _port_in_use(_DEFAULT_PORT):
                    break
            if _port_in_use(_DEFAULT_PORT):
                os.kill(pid, signal.SIGKILL)
            _clear_pid()
            return {"status": "ok", "message": f"9router (pid={pid}) stopped"}
        except ProcessLookupError:
            pass

    return {"status": "ok", "message": "9router is not running"}


async def _status() -> dict:
    """Return current status of the 9router service."""
    port = _DEFAULT_PORT
    listening = _port_in_use(port)

    pid = _find_router_pid(port)
    pid_info = _load_pid()

    managed = pid_info is not None
    orphan = False
    if pid and not managed:
        orphan = True

    health = await _check_health(port) if listening else {"status": "not_listening"}

    return {
        "status": "running" if listening else "stopped",
        "managed": managed,
        "orphan": orphan,
        "pid": pid,
        "port": port,
        "binary": str(_ROUTER_BIN),
        "binary_exists": _ROUTER_BIN.exists(),
        "health": health,
        "data_dir": str(_DATA_DIR),
        "endpoint_url": f"http://127.0.0.1:{port}/v1",
    }


async def _providers() -> dict:
    """Query provider/account info from the 9router DB file."""
    db_path = _DATA_DIR / "db.json"
    if db_path.exists():
        try:
            data = json.loads(db_path.read_text())
            providers = data.get("providers", data.get("accounts", {}))
            return {"status": "ok", "port": _DEFAULT_PORT, "providers": providers}
        except (json.JSONDecodeError, OSError) as exc:
            return {"status": "error", "error": f"Failed to read db.json: {exc}"}
    return {"status": "ok", "port": _DEFAULT_PORT, "providers": {}, "note": "No providers configured yet. Open http://localhost:20128 to set up."}


async def _token_stats() -> dict:
    """Return token savings stats from RTK Token Saver."""
    db_path = _DATA_DIR / "db.json"
    if db_path.exists():
        try:
            data = json.loads(db_path.read_text())
            stats = data.get("tokenStats", data.get("stats", {}))
            return {
                "status": "ok",
                "token_savings": stats,
                "note": "RTK Token Saver compresses tool_result content 20-40%",
            }
        except (json.JSONDecodeError, OSError) as exc:
            return {"status": "error", "error": f"Failed to read stats: {exc}"}
    return {"status": "ok", "token_savings": {}, "note": "No stats yet — start using the proxy."}


# ===================================================================
# Worker class (for Hermes subsidiary worker registry)
# ===================================================================

class Router9(SubsidiaryWorker):
    """9Router Proxy Worker — Token-saving AI routing layer."""

    worker_id = "router9"
    worker_name = "9Router代理"
    description = "FREE AI路由 + RTK Token Saver代理层，40+供应商/100+模型"
    oneliner = "跑在本地20128端口的AI代理，省token、免费用、自动回退"

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            action = task.payload.get("action", "status")
            port = task.payload.get("port", _DEFAULT_PORT)
            host = task.payload.get("host", _DEFAULT_HOST)

            if action == "start":
                result = await _start(port, host)
            elif action == "stop":
                result = await _stop()
            elif action == "status":
                result = await _status()
            elif action == "providers":
                result = await _providers()
            elif action == "tokens":
                result = await _token_stats()
            elif action == "restart":
                await _stop()
                await asyncio.sleep(1)
                result = await _start(port, host)
            else:
                result = {"status": "error", "error": f"Unknown action: {action}"}

            return WorkerResult(
                task_id=task.task_id,
                worker_id=self.worker_id,
                status="success" if result.get("status") != "error" else "error",
                output=result,
            )
        except Exception as e:
            return WorkerResult(
                task_id=task.task_id,
                worker_id=self.worker_id,
                status="error",
                output={"error": str(e)},
            )


# ===================================================================
# Standalone CLI helpers (called from __main__.py)
# ===================================================================

async def cmd_proxy(args: list[str]) -> dict:
    """CLI command: python -m molib proxy <subcommand> [options]

    Subcommands:
      start         Start the 9router proxy daemon
      stop          Stop the 9router proxy daemon
      status        Check if 9router is running
      restart       Restart the proxy
      providers     List configured AI providers
      tokens        Show RTK token savings statistics
    """
    if not args:
        return await _status()

    subcmd = args[0]
    rest = args[1:]

    port = _DEFAULT_PORT
    host = _DEFAULT_HOST

    i = 0
    while i < len(rest):
        if rest[i] == "--port" and i + 1 < len(rest):
            port = int(rest[i + 1])
            i += 2
        elif rest[i] == "--host" and i + 1 < len(rest):
            host = rest[i + 1]
            i += 2
        else:
            i += 1

    if subcmd == "start":
        return await _start(port, host)
    elif subcmd == "stop":
        return await _stop()
    elif subcmd == "status":
        return await _status()
    elif subcmd == "restart":
        await _stop()
        await asyncio.sleep(1)
        return await _start(port, host)
    elif subcmd == "providers":
        return await _providers()
    elif subcmd == "tokens":
        return await _token_stats()
    else:
        return {"status": "error", "error": f"Unknown proxy subcommand: {subcmd}"}
