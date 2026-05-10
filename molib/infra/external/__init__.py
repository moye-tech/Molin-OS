"""
墨麟OS v2.2 — 外部开源项目集成层
===================================
整合 GitHub 顶级开源项目，通过统一接口供 Worker 调用。

已集成：
  gpt-researcher  ⭐18k   — 实时联网深度调研
  firecrawl       ⭐70k   — AI网页抓取与结构化提取
  browser-use     ⭐50k   — AI浏览器自动化
  crawl4ai        ⭐30k   — 轻量批量内容扫描
  diffusers       ⭐30k+  — ComfyUI方案2 纯Python图像生成
  Fish-Speech S2  ⭐18k   — SOTA TTS (API, TTS Arena ELO 1339)
  fal.ai FLUX.2   ⭐20k   — SOTA图像生成 (API)
  STORM           ⭐22k   — 维基百科级别深度报告
  NeMo-Guardrails ⭐5k    — NVIDIA安全护栏
  n8n REST        ⭐65k   — 工作流自动化直连
  LangGraph       ⭐15k   — WorkerChain编排引擎
  Seed-X          ByteDance — 28语言翻译
  LightRAG        ⭐12k   — 图式RAG (无Docker替代RAGFlow)
  moviepy         ⭐13k   — 视频后处理

设计原则：
  - 所有模块 lazy import，避免启动时加载重型依赖
  - 统一返回 dict 格式，失败不抛异常
  - 无Docker / 无Redis / 纯Python替代方案
  - Mac M2 8GB 物理约束：GPU重型任务走云API
"""
