"""
墨麟 · PocketBase 统一后端引擎
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PocketBase (v0.38+, 54K⭐) 单 Go 二进制后端。
提供: 认证、SQLite数据库、文件存储、实时订阅、管理面板。

部署: 单二进制文件，零外部依赖，<50MB RAM，完美适配 Mac M2。
路径: /Users/moye/Molin-OS/tools/pocketbase
数据: ~/.molin/pocketbase/
端口: 8090

Author: 墨麟AI集团 · 墨码开发子公司
Integration: S-Grade (⭐54K, single binary, local-native)
"""

import os
import json
import time
import shutil
import signal
import socket
import hashlib
import platform
import subprocess
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from typing import Any, Optional

# ─── 常量 ───────────────────────────────────────────────

TOOLS_DIR = Path(os.environ.get("MOLIN_TOOLS_DIR", Path.home() / "Molin-OS" / "tools"))
POCKETBASE_BINARY = TOOLS_DIR / "pocketbase"
DATA_DIR = Path.home() / ".molin" / "pocketbase"
API_PORT = 8090
ADMIN_PORT = 8091
SUPERUSER_EMAIL = "admin@molin.ai"
SUPERUSER_PASSWORD = "molin_pb_admin_2026"
DEFAULT_URL = f"http://127.0.0.1:{API_PORT}"

# ─── 安装/版本 ───────────────────────────────────────────

def get_binary_path() -> Path:
    """返回 PocketBase 二进制文件路径"""
    if POCKETBASE_BINARY.exists():
        return POCKETBASE_BINARY
    # Fallback: 搜索 tools 目录
    for candidate in TOOLS_DIR.glob("pocketbase*"):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return POCKETBASE_BINARY


def is_installed() -> bool:
    """检查 PocketBase 是否已安装"""
    return get_binary_path().exists() and os.access(get_binary_path(), os.X_OK)


def version() -> str:
    """获取 PocketBase 版本号"""
    binary = get_binary_path()
    if not binary.exists():
        return "未安装"
    try:
        result = subprocess.run([str(binary), "--version"], capture_output=True, text=True, timeout=5)
        return result.stdout.strip() or "未知"
    except Exception as e:
        return f"无法获取版本: {e}"


def _find_latest_release() -> str:
    """获取最新发布的版本号"""
    url = "https://api.github.com/repos/pocketbase/pocketbase/releases/latest"
    req = urllib.request.Request(url, headers={"User-Agent": "Molin-OS/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("tag_name", "v0.38.0")
    except Exception:
        return "v0.38.0"


def _detect_arch() -> str:
    """检测当前 Mac 架构"""
    machine = platform.machine()
    if machine == "arm64":
        return "darwin_arm64"
    elif machine == "x86_64":
        return "darwin_amd64"
    return "darwin_amd64"


def install(version_tag: str = None) -> dict:
    """下载并安装 PocketBase 二进制文件
    
    Args:
        version_tag: 版本标签 (如 v0.38.0)，默认使用最新版
    
    Returns:
        {"ok": bool, "path": str, "version": str, "message": str}
    """
    if version_tag is None:
        version_tag = _find_latest_release()
    
    arch = _detect_arch()
    version_num = version_tag.lstrip("v")
    
    filename = f"pocketbase_{version_num}_{arch}.zip"
    url = f"https://github.com/pocketbase/pocketbase/releases/download/{version_tag}/{filename}"
    
    # 创建临时目录
    tmp_dir = TOOLS_DIR / "pocketbase_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    zip_path = tmp_dir / filename
    
    try:
        # 下载 ZIP
        print(f"⬇️  下载 PocketBase {version_tag} ({arch})...")
        req = urllib.request.Request(url, headers={"User-Agent": "Molin-OS/1.0"})
        
        with urllib.request.urlopen(req, timeout=300) as resp:
            total_size = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            with open(zip_path, "wb") as f:
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        pct = (downloaded / total_size) * 100
                        print(f"\r   {pct:.0f}% ({downloaded/1024/1024:.1f}MB)")
        
        # 解压
        import zipfile
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_dir)
        
        # 查找解压出的 pocketbase 二进制文件
        for item in tmp_dir.iterdir():
            if item.name.startswith("pocketbase") and item.is_file() and item.suffix != ".zip":
                # 移动到目标位置
                shutil.copy2(item, POCKETBASE_BINARY)
                os.chmod(POCKETBASE_BINARY, 0o755)
                break
        
        # 清理
        shutil.rmtree(tmp_dir, ignore_errors=True)
        
        # 验证
        ver = version()
        return {"ok": True, "path": str(POCKETBASE_BINARY), "version": ver, "message": f"安装成功: PocketBase {ver}"}
    
    except urllib.error.HTTPError as e:
        return {"ok": False, "path": str(POCKETBASE_BINARY), "version": "", "message": f"下载失败 HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"ok": False, "path": str(POCKETBASE_BINARY), "version": "", "message": f"安装失败: {e}"}


def _check_port(port: int) -> bool:
    """检查端口是否可用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
        sock.close()
        return True
    except OSError:
        return False


# ─── 服务管理 ───────────────────────────────────────────

_pb_process: Optional[subprocess.Popen] = None
_pb_pid_file = DATA_DIR / "pocketbase.pid"


def _read_pid() -> Optional[int]:
    """读取 PID 文件"""
    if _pb_pid_file.exists():
        try:
            return int(_pb_pid_file.read_text().strip())
        except Exception:
            return None
    return None


def _write_pid(pid: int):
    """写入 PID 文件"""
    _pb_pid_file.parent.mkdir(parents=True, exist_ok=True)
    _pb_pid_file.write_text(str(pid))


def _is_running() -> bool:
    """检查 PocketBase 是否正在运行"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(("127.0.0.1", API_PORT))
        sock.close()
        return result == 0
    except Exception:
        return False


def start(data_dir: str = None, http_port: int = None) -> dict:
    """启动 PocketBase 服务
    
    Args:
        data_dir: 数据目录，默认 ~/.molin/pocketbase/
        http_port: HTTP API 端口，默认 8090
    
    Returns:
        {"ok": bool, "pid": int, "port": int, "message": str}
    """
    global _pb_process
    
    if _is_running():
        return {"ok": True, "pid": _read_pid(), "port": API_PORT, "message": "PocketBase 已在运行"}
    
    binary = get_binary_path()
    if not binary.exists():
        return {"ok": False, "pid": 0, "port": 0, "message": "PocketBase 未安装，请先调用 install()"}
    
    data = Path(data_dir) if data_dir else DATA_DIR
    port = http_port or API_PORT
    
    data.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        str(binary),
        "serve",
        f"--dir={str(data)}",
        f"--http=127.0.0.1:{port}",
    ]
    
    try:
        _pb_process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(data),
            preexec_fn=os.setsid,
        )
        _write_pid(_pb_process.pid)
        
        # 等待服务就绪
        for i in range(30):
            if _is_running():
                return {"ok": True, "pid": _pb_process.pid, "port": port, "message": f"PocketBase 已启动 (pid={_pb_process.pid}, port={port})"}
            time.sleep(0.5)
        
        return {"ok": True, "pid": _pb_process.pid, "port": port, "message": f"PocketBase 已启动但未就绪 (pid={_pb_process.pid})"}
    
    except Exception as e:
        return {"ok": False, "pid": 0, "port": 0, "message": f"启动失败: {e}"}


def stop() -> dict:
    """停止 PocketBase 服务"""
    global _pb_process
    
    # 先尝试通过 PID 文件停止
    pid = _read_pid()
    if pid:
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
            _pb_pid_file.unlink(missing_ok=True)
            time.sleep(1)
            return {"ok": True, "pid": pid, "message": "PocketBase 已停止 (SIGTERM)"}
        except (ProcessLookupError, OSError):
            pass
    
    if _pb_process:
        try:
            os.killpg(os.getpgid(_pb_process.pid), signal.SIGTERM)
            _pb_process = None
            _pb_pid_file.unlink(missing_ok=True)
            return {"ok": True, "pid": 0, "message": "PocketBase 已停止"}
        except (ProcessLookupError, OSError):
            _pb_process = None
            return {"ok": True, "pid": 0, "message": "PocketBase 进程已不存在"}
    
    return {"ok": True, "pid": 0, "message": "没有运行中的 PocketBase"}


def restart() -> dict:
    """重启 PocketBase 服务"""
    r1 = stop()
    time.sleep(1)
    r2 = start()
    return r2


def status() -> dict:
    """获取 PocketBase 服务状态"""
    running = _is_running()
    pid = _read_pid()
    ver = version() if is_installed() else "未安装"
    
    return {
        "installed": is_installed(),
        "version": ver,
        "running": running,
        "pid": pid if running else 0,
        "port": API_PORT,
        "data_dir": str(DATA_DIR),
        "url": DEFAULT_URL if running else "",
    }


# ─── HTTP API 客户端 ─────────────────────────────────────

class PocketBaseClient:
    """PocketBase HTTP API 客户端（纯标准库）"""
    
    def __init__(self, base_url: str = None):
        self.base_url = (base_url or DEFAULT_URL).rstrip("/")
        self._token: Optional[str] = None
        self._user: Optional[dict] = None
    
    def _request(self, method: str, path: str, data: dict = None, params: dict = None) -> dict:
        """发送 HTTP 请求到 PocketBase API"""
        url = f"{self.base_url}/api{path}"
        
        if params:
            url += "?" + urllib.parse.urlencode(params)
        
        body = None
        headers = {
            "User-Agent": "Molin-OS/1.0",
            "Content-Type": "application/json",
        }
        
        if self._token:
            headers["Authorization"] = self._token
        
        if data:
            body = json.dumps(data).encode("utf-8")
        
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                content = resp.read().decode("utf-8")
                if content:
                    return json.loads(content)
                return {"code": 200, "data": {}}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            try:
                return json.loads(error_body)
            except json.JSONDecodeError:
                return {"code": e.code, "message": f"HTTP {e.code}: {error_body[:200]}", "data": {}}
        except urllib.error.URLError as e:
            return {"code": 503, "message": f"连接失败: {e.reason}", "data": {}}
    
    # ─── 认证 ─────────────────────────────────────────
    
    def superuser_create(self, email: str = None, password: str = None) -> dict:
        """创建超级管理员（首次使用）"""
        if not _is_running():
            return {"code": 503, "message": "PocketBase 未运行"}
        
        e = email or SUPERUSER_EMAIL
        p = password or SUPERUSER_PASSWORD
        
        result = self._request("POST", "/admins", data={
            "email": e,
            "password": p,
            "passwordConfirm": p,
        })
        
        if result.get("id"):
            # 自动登录
            login_result = self.superuser_login(e, p)
            return {"code": 200, "id": result["id"], "message": "超级管理员创建成功", "login": login_result}
        
        return result
    
    def superuser_login(self, email: str = None, password: str = None) -> dict:
        """超级管理员登录"""
        e = email or SUPERUSER_EMAIL
        p = password or SUPERUSER_PASSWORD
        
        result = self._request("POST", "/admins/auth-with-password", data={
            "identity": e,
            "password": p,
        })
        
        if result.get("token"):
            self._token = result["token"]
            self._user = result.get("admin", {})
            return {"code": 200, "message": "登录成功", "admin_id": self._user.get("id")}
        
        return result
    
    def user_create(self, email: str, password: str, username: str = "", data: dict = None) -> dict:
        """创建普通用户"""
        body = {
            "email": email,
            "password": password,
            "passwordConfirm": password,
        }
        if username:
            body["username"] = username
        if data:
            body.update(data)
        
        return self._request("POST", "/collections/users/records", data=body)
    
    def user_login(self, email: str, password: str) -> dict:
        """普通用户登录"""
        return self._request("POST", "/collections/users/auth-with-password", data={
            "identity": email,
            "password": password,
        })
    
    # ─── 集合操作 (CRUD) ─────────────────────────────
    
    def collection_create(self, name: str, fields: list[dict], rules: dict = None) -> dict:
        """创建数据集合"""
        body = {
            "name": name,
            "type": "base",
            "schema": fields,
        }
        if rules:
            body["listRule"] = rules.get("list", "")
            body["viewRule"] = rules.get("view", "")
            body["createRule"] = rules.get("create", "")
            body["updateRule"] = rules.get("update", "")
            body["deleteRule"] = rules.get("delete", "")
        
        return self._request("POST", "/collections", data=body)
    
    def collection_get(self, name_or_id: str) -> dict:
        """获取集合信息"""
        return self._request("GET", f"/collections/{name_or_id}")
    
    def collection_list(self) -> dict:
        """列出所有集合"""
        return self._request("GET", "/collections")
    
    def record_create(self, collection: str, data: dict) -> dict:
        """创建记录"""
        return self._request("POST", f"/collections/{collection}/records", data=data)
    
    def record_get(self, collection: str, record_id: str) -> dict:
        """获取单条记录"""
        return self._request("GET", f"/collections/{collection}/records/{record_id}")
    
    def record_list(self, collection: str, filters: str = "", sort: str = "", 
                    page: int = 1, per_page: int = 30, expand: str = "") -> dict:
        """列出记录（支持过滤、排序、分页）"""
        params = {"page": page, "perPage": per_page}
        if filters:
            params["filter"] = filters
        if sort:
            params["sort"] = sort
        if expand:
            params["expand"] = expand
        
        return self._request("GET", f"/collections/{collection}/records", params=params)
    
    def record_update(self, collection: str, record_id: str, data: dict) -> dict:
        """更新记录"""
        return self._request("PATCH", f"/collections/{collection}/records/{record_id}", data=data)
    
    def record_delete(self, collection: str, record_id: str) -> dict:
        """删除记录"""
        return self._request("DELETE", f"/collections/{collection}/records/{record_id}")

    def record_search(self, collection: str, query: str, fields: str = "") -> dict:
        """全文搜索记录"""
        params = {"q": query}
        if fields:
            params["fields"] = fields
        
        # 使用 filter 进行搜索
        if query:
            params["filter"] = f"(title~'{query}' || description~'{query}' || content~'{query}')"
        
        return self._request("GET", f"/collections/{collection}/records", params=params)
    
    # ─── 文件上传 ─────────────────────────────────────
    
    def file_upload(self, collection: str, record_id: str, field: str, file_path: str) -> dict:
        """上传文件到记录的 file 字段
        ⚠️ 需要 multipart/form-data，标准库实现较复杂
        """
        if not _is_running():
            return {"code": 503, "message": "PocketBase 未运行"}
        
        import mimetypes
        
        url = f"{self.base_url}/api/collections/{collection}/records/{record_id}"
        boundary = "----MolinOSFormBoundary" + hashlib.md5(str(time.time()).encode()).hexdigest()
        
        filename = os.path.basename(file_path)
        content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode("utf-8") + file_data + f"\r\n--{boundary}--\r\n".encode("utf-8")
        
        req = urllib.request.Request(
            url,
            data=body,
            method="PATCH",
            headers={
                "User-Agent": "Molin-OS/1.0",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            }
        )
        
        if self._token:
            req.add_header("Authorization", self._token)
        
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            try:
                return json.loads(error_body)
            except json.JSONDecodeError:
                return {"code": e.code, "message": f"HTTP {e.code}: {error_body[:200]}"}
    
    # ─── 管理面板 ─────────────────────────────────────
    
    def admin_panel_url(self) -> str:
        """获取管理面板 URL"""
        return f"http://127.0.0.1:{API_PORT}/_/"
    
    # ─── 健康检查 ─────────────────────────────────────
    
    def health(self) -> dict:
        """健康检查"""
        result = self._request("GET", "/health")
        result["_running"] = _is_running()
        result["_version"] = version()
        result["_data_dir"] = str(DATA_DIR)
        return result


# ─── 便利工厂函数 ─────────────────────────────────────────

_client: Optional[PocketBaseClient] = None


def get_client() -> PocketBaseClient:
    """获取或创建 PocketBase 客户端（单例）"""
    global _client
    if _client is None:
        _client = PocketBaseClient()
    return _client


def quick_start() -> dict:
    """一键启动 PocketBase（安装 + 启动 + 创建管理员）
    
    这是最常用的入口点。自动处理安装、启动、初始化。
    """
    steps = []
    
    # 1. 安装检查
    if not is_installed():
        inst_result = install()
        steps.append(("install", inst_result))
        if not inst_result["ok"]:
            return {"ok": False, "steps": steps, "message": "安装失败"}
    
    # 2. 启动服务
    start_result = start()
    steps.append(("start", start_result))
    if not start_result["ok"]:
        return {"ok": False, "steps": steps, "message": "启动失败"}
    
    # 3. 初始化管理员
    client = get_client()
    admin_result = client.superuser_create()
    steps.append(("admin", admin_result))
    
    if not admin_result.get("id") and "already" not in str(admin_result.get("message", "")):
        # 可能已存在，尝试登录
        login_result = client.superuser_login()
        steps.append(("login", login_result))
    
    # 4. 健康检查
    health_status = client.health()
    steps.append(("health", health_status))
    
    return {
        "ok": True,
        "steps": steps,
        "url": DEFAULT_URL,
        "admin_panel": client.admin_panel_url(),
        "message": "PocketBase 就绪",
    }


# ─── CLI 入口 ───────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python -m molib.infra.pocketbase <command> [args...]")
        print("命令: install | start | stop | restart | status | health | quick-start")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "install":
        tag = sys.argv[2] if len(sys.argv) > 2 else None
        result = install(tag)
    elif cmd == "start":
        result = start()
    elif cmd == "stop":
        result = stop()
    elif cmd == "restart":
        result = restart()
    elif cmd == "status":
        result = status()
    elif cmd == "health":
        client = get_client()
        result = client.health()
    elif cmd == "quick-start":
        result = quick_start()
    else:
        result = {"error": f"未知命令: {cmd}"}
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
