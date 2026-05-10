# 墨麟OS 模型路由策略

> 配置于 2026-05-10，融合 Molin-OS config/models.toml 到 Hermes config.yaml

## 四级路由

| 任务类型 | 模型 | Provider | 成本 ¥/1K input |
|:---------|:-----|:---------|:---:|
| 简单（分类/提取/问答） | deepseek-v4-flash | DeepSeek | 0.00014 |
| 复杂（推理/决策/规划） | deepseek-v4-pro | DeepSeek | 0.0004 |
| 视觉（图片分析/OCR） | qwen-vl-plus | DashScope | 0.0015 |
| 视频生成 | HappyHorse-1.0-T2V | DashScope | 0.01 |

## Hermes 配置要点

```yaml
# ~/.hermes/config.yaml
model:
  default: deepseek-v4-pro
  provider: deepseek

auxiliary:
  vision:
    provider: dashscope
    model: qwen-vl-plus
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    api_key: <from DASHSCOPE_API_KEY>

providers:
  dashscope:
    api_key: <DASHSCOPE_API_KEY>
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    model: qwen-vl-plus
```

## 密钥来源

百炼 API Key 从 `Molin-OS/tools/bailian_image.py` 第 17 行提取：
```python
API_KEY = "sk-xxx"  # 硬编码，需迁移到环境变量
```

提取后写入 `~/.hermes/.env`：`DASHSCOPE_API_KEY=sk-xxx`
