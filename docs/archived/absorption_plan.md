# CH6: 第11轮 GitHub吸收计划 — 10个项目分批评分与吸收

> 生成时间: 2026-05-08
> 使用 `~/hermes-os/bots/absorption_pipeline.py` 三步管线评估

## 评分标准

| 维度 | 权重 | 说明 |
|------|------|------|
| ⭐ 星数 | 30% | 对数映射：1→10, 10→30, 100→50, 1k→70, 10k+→90 |
| 🎯 匹配度 | 40% | 对Hermes技能域的语义匹配度 |
| ⚡ 可执行性 | 30% | README完整性 + API可调用性 + 示例质量 |

| 等级 | 分数 | 策略 |
|------|------|------|
| S级 | 80-100 | 优先吸收，立即生成SKILL.md |
| A级 | 60-79 | 推荐吸收，排入本周计划 |
| B级 | 40-59 | 可吸收，排入下月计划 |
| C级 | 20-39 | 观察，暂缓吸收 |
| D级 | 0-19 | 不推荐 |

---

## 第11批：10个项目

### 1. AUTOMATIC1111/stable-diffusion-webui
- **URL**: https://github.com/AUTOMATIC1111/stable-diffusion-webui
- **Stars**: ~190,000
- **匹配关键词**: image, generation, ai, api, pipeline
- **评估**:
  - ⭐ 星数: 190k → 95/100
  - 🎯 匹配度: image+generation+api+pipeline+ai → 80/100
  - ⚡ 可执行性: README✅ API✅ 示例✅ → 100/100
  - **总分: 95×0.3 + 80×0.4 + 100×0.3 = 90.5 → S级**
- **吸收策略**: ✅ 优先吸收 — 最强的本地生图能力，补全百炼API的不足
- **计划**: 吸收为 stable-diffusion-webui 技能，提供本地SD WebUI封装

### 2. openai/whisper
- **URL**: https://github.com/openai/whisper
- **Stars**: ~75,000
- **匹配关键词**: voice, stt, audio, ai, cli
- **评估**:
  - ⭐ 星数: 75k → 88/100
  - 🎯 匹配度: voice+stt+audio+ai+cli → 80/100
  - ⚡ 可执行性: README✅ API✅ 示例✅ → 100/100
  - **总分: 88×0.3 + 80×0.4 + 100×0.3 = 88.4 → S级**
- **吸收策略**: ✅ 优先吸收 — 语音识别核心能力，补充Hermes语音管线
- **计划**: 吸收为 whisper-stt 技能，对接Hermes语音转写管线

### 3. langflow-ai/langflow
- **URL**: https://github.com/langflow-ai/langflow
- **Stars**: ~40,000
- **匹配关键词**: workflow, automation, pipeline, agent, api
- **评估**:
  - ⭐ 星数: 40k → 82/100
  - 🎯 匹配度: workflow+automation+pipeline+agent+api → 90/100
  - ⚡ 可执行性: README✅ API✅ 示例✅ → 100/100
  - **总分: 82×0.3 + 90×0.4 + 100×0.3 = 90.6 → S级**
- **吸收策略**: ✅ 优先吸收 — 可视化工作流引擎，扩展Hermes自动化能力
- **计划**: 吸收为 langflow 技能，提供工作流编排能力

### 4. n8n-io/n8n
- **URL**: https://github.com/n8n-io/n8n
- **Stars**: ~55,000
- **匹配关键词**: automation, workflow, notification, api, bot
- **评估**:
  - ⭐ 星数: 55k → 85/100
  - 🎯 匹配度: automation+workflow+notification+api+bot → 85/100
  - ⚡ 可执行性: README✅ API✅ 示例✅ → 95/100
  - **总分: 85×0.3 + 85×0.4 + 95×0.3 = 87.0 → S级**
- **吸收策略**: ✅ 优先吸收 — 企业级自动化平台，与飞书/闲鱼集成
- **计划**: 吸收为 n8n 技能，对接Hermes cron和飞轮管线

### 5. ytdl-org/youtube-dl
- **URL**: https://github.com/ytdl-org/youtube-dl
- **Stars**: ~135,000
- **匹配关键词**: media, content, cli, 下载
- **评估**:
  - ⭐ 星数: 135k → 92/100
  - 🎯 匹配度: media+content+cli → 45/100
  - ⚡ 可执行性: README✅ API✅ 示例✅ → 100/100
  - **总分: 92×0.3 + 45×0.4 + 100×0.3 = 75.6 → A级**
- **吸收策略**: ✅ 推荐吸收 — 视频下载核心工具，辅助短视频管线
- **计划**: 吸收为 youtube-dl 技能，用于内容采集

### 6. facebookresearch/llama
- **URL**: https://github.com/facebookresearch/llama
- **Stars**: ~57,000
- **匹配关键词**: llm, ai, text
- **评估**:
  - ⭐ 星数: 57k → 85/100
  - 🎯 匹配度: llm+ai+text → 45/100
  - ⚡ 可执行性: README✅ API✅ 示例✅ → 90/100
  - **总分: 85×0.3 + 45×0.4 + 90×0.3 = 70.5 → A级**
- **吸收策略**: ✅ 推荐吸收 — LLM推理能力，但Hermes已通过API使用LLM
- **计划**: 吸收为 llama 技能，提供本地推理fallback

### 7. huggingface/diffusers
- **URL**: https://github.com/huggingface/diffusers
- **Stars**: ~27,000
- **匹配关键词**: image, generation, ai, api
- **评估**:
  - ⭐ 星数: 27k → 78/100
  - 🎯 匹配度: image+generation+ai+api → 60/100
  - ⚡ 可执行性: README✅ API✅ 示例✅ → 100/100
  - **总分: 78×0.3 + 60×0.4 + 100×0.3 = 77.4 → A级**
- **吸收策略**: ✅ 推荐吸收 — 图像生成全套管线，与百炼互补
- **计划**: 吸收为 diffusers 技能，提供本地生图能力

### 8. apache/airflow
- **URL**: https://github.com/apache/airflow
- **Stars**: ~38,000
- **匹配关键词**: pipeline, automation, workflow
- **评估**:
  - ⭐ 星数: 38k → 82/100
  - 🎯 匹配度: pipeline+automation+workflow → 45/100
  - ⚡ 可执行性: README✅ API✅ 示例✅ → 100/100
  - **总分: 82×0.3 + 45×0.4 + 100×0.3 = 72.6 → A级**
- **吸收策略**: ✅ 推荐吸收 — DAG调度能力，替代/补充cron
- **计划**: 吸收为 airflow 技能，用于复杂管线编排

### 9. RVC-Project/Retrieval-based-Voice-Conversion-WebUI
- **URL**: https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI
- **Stars**: ~25,000
- **匹配关键词**: voice, audio, ai
- **评估**:
  - ⭐ 星数: 25k → 77/100
  - 🎯 匹配度: voice+audio+ai → 45/100
  - ⚡ 可执行性: README✅ API❌ 示例✅ → 60/100
  - **总分: 77×0.3 + 45×0.4 + 60×0.3 = 59.1 → B级**
- **吸收策略**: 🔄 可吸收 — 语音转换，但需GPU且无API
- **计划**: 吸收为 rvc-voice-conversion 技能，排入下月计划

### 10. sox-developers/sox
- **URL**: https://github.com/sox-developers/sox
- **Stars**: ~1,800
- **匹配关键词**: audio, media
- **评估**:
  - ⭐ 星数: 1.8k → 32/100
  - 🎯 匹配度: audio+media → 30/100
  - ⚡ 可执行性: README✅ API✅ 示例✅ → 100/100
  - **总分: 32×0.3 + 30×0.4 + 100×0.3 = 51.6 → B级**
- **吸收策略**: 🔄 可吸收 — 音频处理瑞士军刀，基础工具
- **计划**: 吸收为 sox 技能，排入下月计划

---

## 批次评分排名

| 排名 | 项目 | 总分 | 等级 |
|------|------|------|------|
| 🥇 | langflow-ai/langflow | 90.6 | S级 |
| 🥇 | AUTOMATIC1111/stable-diffusion-webui | 90.5 | S级 |
| 🥉 | openai/whisper | 88.4 | S级 |
| 4 | n8n-io/n8n | 87.0 | S级 |
| 5 | huggingface/diffusers | 77.4 | A级 |
| 6 | ytdl-org/youtube-dl | 75.6 | A级 |
| 7 | apache/airflow | 72.6 | A级 |
| 8 | facebookresearch/llama | 70.5 | A级 |
| 9 | RVC-Project/rvc-webui | 59.1 | B级 |
| 10 | sox-developers/sox | 51.6 | B级 |

## 吸收排期

### 本周（优先级1 — 4个S级项目）
| 日 | 项目 | 预计工时 |
|----|------|---------|
| 周一 | langflow-ai/langflow | 2h |
| 周二 | AUTOMATIC1111/stable-diffusion-webui | 2h |
| 周三 | openai/whisper | 1.5h |
| 周四 | n8n-io/n8n | 2h |

### 下周（优先级2 — 4个A级项目）
| 日 | 项目 | 预计工时 |
|----|------|---------|
| 周一 | huggingface/diffusers | 1.5h |
| 周二 | ytdl-org/youtube-dl | 1h |
| 周三 | apache/airflow | 2h |
| 周四 | facebookresearch/llama | 1.5h |

### 下月（优先级3 — 2个B级项目）
| 项目 | 说明 |
|------|------|
| RVC-Project/rvc-webui | 需GPU资源，评估后执行 |
| sox-developers/sox | 基础工具，系统自带即可 |
