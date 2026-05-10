"""
墨麟OS v2.1 — 外部开源项目集成层
===================================
整合 GitHub 顶级开源项目，通过统一接口供 Worker 调用。

已集成：
  gpt-researcher  ⭐18k  — 实时联网深度调研
  firecrawl       ⭐70k  — AI网页抓取与结构化提取
  browser-use     ⭐50k  — AI浏览器自动化
  DashScope CosyVoice ⭐21k — 中文TTS配音 (API替代本地部署)
  fal.ai FLUX.2   ⭐20k  — SOTA图像生成 (API替代ComfyUI)
  STORM           ⭐22k  — 维基百科级别深度报告

设计原则：
  - 所有模块 lazy import，避免启动时加载重型依赖
  - 统一返回 dict 格式，失败不抛异常
  - Mac M2 8GB 物理约束：GPU重型任务走云API
"""
