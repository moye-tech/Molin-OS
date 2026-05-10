# 凭证提取与 Provider 注册模式

## 场景

Molin-OS 等外部项目将 API Key 硬编码在工具脚本中（如 `tools/bailian_image.py`）。
需要将其提取并注册到 Hermes 的凭证体系（`.env` + `config.yaml`）。

## 模式步骤

### 1. 发现硬编码凭证

```bash
# 在外部项目中搜索 API key 模式
grep -rn "API_KEY\s*=\|api_key\s*=\|sk-[a-zA-Z0-9]" <project_root>/ | grep -v node_modules
```

### 2. 安全提取

```python
import re
with open('<path>/bailian_image.py') as f:
    content = f.read()
    match = re.search(r'API_KEY\s*=\s*"([^"]+)"', content)
    if match:
        key = match.group(1)  # e.g. "sk-2d3ce...9707"
```

### 3. 存入 Hermes .env

```bash
# 追加到 ~/.hermes/.env（不覆盖已有配置）
echo "DASHSCOPE_API_KEY=$KEY" >> ~/.hermes/.env
```

### 4. 注册到 config.yaml

为自定义 Provider 注册三个字段：
- `providers.<name>.api_key` — 从 .env 读取
- `providers.<name>.base_url` — API endpoint
- `providers.<name>.model` — 默认模型名

DashScope 的标准 base_url：
```
https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 5. 配置辅助模型路由

```bash
hermes config set auxiliary.vision.provider dashscope
hermes config set auxiliary.vision.model qwen-vl-plus
hermes config set auxiliary.vision.base_url "https://dashscope.aliyuncs.com/compatible-mode/v1"
hermes config set auxiliary.vision.api_key "$DASHSCOPE_API_KEY"
```

## 重要原则

- **不要动 Hermes 的 config.yaml 主结构**：通过 `hermes config set` 或精确的 YAML 路径写入
- **用 Hermes venv 的 Python**：`~/.hermes/hermes-agent/venv/bin/python`（只有它有 pyyaml）
- **不要用系统 Python**：`~/.local/bin/python3.11` 是 uv 管理的外部环境，拒绝 pip install
- **密钥从不在对话中明文暴露**：提取→存入文件→清除提取代码中的引用
- **Provider 注册后重启生效**：/reset 或新 session

## 已知 Provider 配置速查

| Provider | base_url | 用途 |
|----------|----------|------|
| deepseek | https://api.deepseek.com/v1 | LLM 主模型 |
| dashscope | https://dashscope.aliyuncs.com/compatible-mode/v1 | 视觉/视频/生图 |
| openrouter | https://openrouter.ai/api/v1 | 多模型网关 |
