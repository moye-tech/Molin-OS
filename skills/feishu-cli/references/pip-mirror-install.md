# Hermes Python 依赖安装 — 镜像加速

## 问题

Hermes Agent 的 venv 中 pip 版本较旧（24.0），从 PyPI 直连下载 `files.pythonhosted.org`
经常 ReadTimeout（国内网络环境 100KB/s 以下）。

## 解决方案

使用阿里云 PyPI 镜像（速度快 10-50 倍）：

```bash
# 1. 升级 pip（必须先升级，旧版 pip 24.0 有性能问题）
/Users/moye/.hermes/hermes-agent/venv/bin/python -m pip install --upgrade pip \
  -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# 2. 安装依赖
/Users/moye/.hermes/hermes-agent/venv/bin/python -m pip install \
  -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com \
  httpx pandas numpy openai markdown ffmpeg-python loguru schedule flask flask-cors
```

## 其他可用镜像

- 清华: `https://pypi.tuna.tsinghua.edu.cn/simple/`
- 中科大: `https://pypi.mirrors.ustc.edu.cn/simple/`
- 腾讯: `https://mirrors.cloud.tencent.com/pypi/simple/`

## Molin-OS 完整依赖清单

```txt
# 核心（已安装）
pyyaml>=6.0
python-dotenv>=1.0.0
click>=8.1.0
rich>=13.0.0
requests>=2.31.0

# 网络（需安装）
httpx>=0.25.0
aiohttp>=3.9.0

# 数据处理
pandas>=2.0.0
numpy>=1.24.0

# 内容生成
openai>=1.0.0
markdown>=3.5

# 视频
ffmpeg-python>=0.2.0

# 监控日志
loguru>=0.7.0
schedule>=1.2.0

# Web仪表盘（可选）
flask>=3.0.0
flask-cors>=4.0.0

# 测试
pytest>=8.0.0
pytest-cov>=4.0.0
```
