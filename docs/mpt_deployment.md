# MoneyPrinterTurbo 部署文档

> **目标**: 部署 MoneyPrinterTurbo (harry0703/MoneyPrinterTurbo) 视频生成服务，
> 通过 Docker 或源码方式运行，并接入 Hermes OS 的 `short_video.py` Worker。

---

## 一、快速方案：Docker 部署（推荐）

### 1.1 拉取镜像

```bash
docker pull harry0703/money-printer-turbo:latest
```

### 1.2 创建配置文件目录

```bash
mkdir -p ~/hermes-os/config/mpt
```

### 1.3 创建环境变量文件

创建 `~/hermes-os/config/mpt/.env`：

```bash
# ============================================
# MoneyPrinterTurbo 环境变量配置
# ============================================

# --- LLM 配置（必填）---
# 用于脚本生成、文案优化等
LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

# 备用: 阿里百炼（如果使用国产模型）
# LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
# LLM_MODEL=qwen-plus

# --- TTS 配置（可选，默认 edge-tts）---
TTS_PROVIDER=edge-tts
# 阿里云语音合成（替代方案）
# TTS_PROVIDER=aliyun
# ALIYUN_ACCESS_KEY_ID=your-ak-id
# ALIYUN_ACCESS_KEY_SECRET=your-ak-secret
# ALIYUN_TTS_VOICE=xiaoyun

# --- 火山引擎（可选，用于视频素材/字幕）---
# VOLC_ACCESS_KEY_ID=your-volc-ak-id
# VOLC_SECRET_ACCESS_KEY=your-volc-sk

# --- 视频素材源 ---
# pexels: 默认，需要 API Key（免费）
PEXELS_API_KEY=your-pexels-api-key
# PIXABAY_API_KEY=your-pixabay-api-key（备用）

# --- 服务配置 ---
HOST=0.0.0.0
PORT=8899
WORKERS=1
LOG_LEVEL=info
```

### 1.4 启动 Docker 容器

```bash
docker run -d \
  --name money-printer-turbo \
  --restart unless-stopped \
  -p 8899:8899 \
  -v ~/hermes-os/config/mpt/.env:/app/.env \
  harry0703/money-printer-turbo:latest
```

### 1.5 验证服务

```bash
# 健康检查
curl -s http://localhost:8899/health | python3 -m json.tool

# 预期返回: {"status": "ok", "version": "x.x.x"}
```

### 1.6 查看日志

```bash
docker logs -f money-printer-turbo
```

---

## 二、备选方案：源码部署（无 Docker 环境时）

### 2.1 克隆仓库

```bash
cd ~/hermes-os/fork_repos
git clone https://github.com/harry0703/MoneyPrinterTurbo.git
cd MoneyPrinterTurbo
```

### 2.2 创建虚拟环境并安装依赖

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.3 配置环境变量

```bash
cp config.example.toml config.toml
# 编辑 config.toml 填入 API Key 等配置
```

### 2.4 启动服务

```bash
source venv/bin/activate
# 后台运行
nohup python app.py > mpt.log 2>&1 &
```

---

## 三、API 调用示例

### 3.1 生成视频

```bash
curl -s -X POST http://localhost:8899/api/v1/video \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AI Agent入门教程：从零搭建你的第一个Agent",
    "duration": 60,
    "style": "科技感",
    "tts_voice": "zh-CN-XiaoxiaoNeural"
  }' | python3 -m json.tool
```

### 3.2 仅生成脚本

```bash
curl -s -X POST http://localhost:8899/api/v1/script \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "2026年AI趋势速览",
    "duration": 30
  }' | python3 -m json.tool
```

### 3.3 查詢任务状态

```bash
curl -s http://localhost:8899/api/v1/task/<task_id> | python3 -m json.tool
```

---

## 四、接入 short_video.py Worker

MoneyPrinterTurbo 已集成到 `short_video.py` 的 MPT 引擎中。
部署后可通过 Hermes OS 的 CLI 统一入口调用：

### 4.1 生成脚本

```bash
python -m molib video generate --topic "AI Agent入门" --mode script
```

### 4.2 生成完整视频（需 MPT 服务运行中）

```bash
python -m molib video generate --topic "AI Agent入门" --mode generate --engine mpt --duration 60
```

### 4.3 short_video.py 接入代码示例

在 `short_video.py` 的 `_render_video` 方法中，实际调用 MPT API 的示例：

```python
# short_video.py 中 _render_video 的 MPT 引擎实现参考
import aiohttp
import os

MPT_BASE_URL = os.getenv("MPT_BASE_URL", "http://localhost:8899")

async def _render_video_with_mpt(self, script: str, topic: str, duration: int) -> dict:
    """调用 MoneyPrinterTurbo API 生成视频"""
    async with aiohttp.ClientSession() as session:
        payload = {
            "topic": topic,
            "script": script,
            "duration": duration,
            "style": "科技感",
        }
        async with session.post(
            f"{MPT_BASE_URL}/api/v1/video",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=300),  # 5分钟超时
        ) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                return {
                    "engine": "MoneyPrinterTurbo",
                    "status": "error",
                    "error": f"MPT API returned {resp.status}: {error_text}",
                }
            result = await resp.json()
            return {
                "engine": "MoneyPrinterTurbo",
                "status": "success",
                "video_url": result.get("video_url", ""),
                "task_id": result.get("task_id", ""),
                "duration_seconds": duration,
            }
```

> **注意**: 当前 `short_video.py` 的 MPT 引擎返回的是占位信息。
> 部署 MPT 服务后，将 `_render_video` 方法中的 MPT 分支替换为上述实际 API 调用代码即可。

---

## 五、环境变量速查表

| 变量 | 必填 | 说明 | 示例值 |
|------|------|------|--------|
| `LLM_API_KEY` | ✅ | 大模型 API Key（脚本生成用） | `sk-xxx` |
| `LLM_BASE_URL` | ✅ | 大模型 API 地址 | `https://api.deepseek.com/v1` |
| `LLM_MODEL` | ✅ | 模型名称 | `deepseek-chat` |
| `PEXELS_API_KEY` | ✅ | Pexels 素材 API Key（免费注册） | `your-key` |
| `TTS_PROVIDER` | ❌ | TTS 提供商 | `edge-tts`（默认） |
| `ALIYUN_ACCESS_KEY_ID` | ❌ | 阿里云语音合成 AK | — |
| `ALIYUN_ACCESS_KEY_SECRET` | ❌ | 阿里云语音合成 SK | — |
| `ALIYUN_TTS_VOICE` | ❌ | 阿里云 TTS 音色 | `xiaoyun` |
| `VOLC_ACCESS_KEY_ID` | ❌ | 火山引擎 AK（视频字幕） | — |
| `VOLC_SECRET_ACCESS_KEY` | ❌ | 火山引擎 SK | — |
| `PIXABAY_API_KEY` | ❌ | Pixabay 备用素材源 | — |
| `HOST` | ❌ | 监听地址（默认 0.0.0.0） | `0.0.0.0` |
| `PORT` | ❌ | 监听端口（默认 8899） | `8899` |

### 获取 API Key

- **DeepSeek**: https://platform.deepseek.com/api_keys
- **阿里百炼**: https://bailian.console.aliyun.com/ → API Key 管理
- **火山引擎**: https://console.volcengine.com/accessKey/
- **Pexels**: https://www.pexels.com/api/ （免费注册即可）
- **阿里云语音合成**: https://nls.console.aliyun.com/ → AccessKey

---

## 六、飞轮集成

部署后可将视频生成加入每日飞轮管线：

在 `~/hermes-os/cron/jobs.yaml` 中添加：

```yaml
- name: daily_video_generation
  schedule: "30 10 * * *"  # 每天10:30（飞轮内容生成后）
  command: "python -m molib video generate --topic '$(python -c \"import json; d=json.load(open(os.path.expanduser('~/hermes-os/relay/content_flywheel.json'))); print(d.get('topic', ['AI每日资讯'])[0])\")' --mode generate --engine mpt --duration 60"
  description: "基于飞轮内容自动生成短视频"
```

---

## 七、故障排查

### 7.1 Docker 容器启动失败

```bash
# 查看日志
docker logs money-printer-turbo

# 常见原因: .env 文件缺失或格式错误
# 检查 .env 文件是否存在且包含至少 LLM_API_KEY
```

### 7.2 API 返回 401/403

```
原因: API Key 无效或未配置
解决: 检查 LLM_API_KEY 和 PEXELS_API_KEY 是否正确
```

### 7.3 端口冲突

```bash
# 检查 8899 端口是否被占用
sudo lsof -i :8899
# 如冲突，修改 .env 中的 PORT 并重启容器
```

### 7.4 视频生成超时

```
原因: 视频生成通常需要 1-3 分钟
解决: 
  1. 检查网络能否访问 Pexels
  2. 检查 Docker 资源限制（内存 >= 2GB）
  3. API 请求设置 timeout >= 300s
```

### 7.5 Docker 未安装

```bash
# Ubuntu 安装 Docker
sudo apt update
sudo apt install -y docker.io
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
# 登出后重新登录生效
```

---

> 📅 文档生成时间: 2026-05-08
> ✅ 状态: 待部署 — 需要 docker pull + 配置 .env 后启动
> 🐳 镜像: `harry0703/money-printer-turbo:latest`（约 2-4GB）
> ⚠️ 磁盘需求: 容器镜像约 2-4GB，运行时额外 1-2GB 缓存
