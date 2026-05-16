# research-engine · 实时情报调研引擎
# 归属: Agent D (shared) 提供，A/B/C/E均可调用（跨线请求）
## 触发词
触发词: 竞品|市场调研|行业趋势|最新数据|联网搜索
触发词: 分析市场|情报|扫描|实时信息
## 核心引擎（gpt-researcher集成）
主引擎: gpt-researcher（自动多源联网搜索+综合分析）
辅助: web-scraper（定向页面抓取）
缓存: 相同查询24小时内复用结果（节省API）
## 调用格式（跨Agent请求）
写入 relay/shared/cross_request.json:
{ "requester_agent": "media", "service": "research", "task": "调研内容", "priority": "L0" }
## 输出格式
{ "query": "", "sources": ["URL×N"], "summary": "300字摘要", "key_findings": ["关键发现×5"], "data_points": [...] }
## 安装要求
pip install gpt-researcher
设置 OPENAI_API_KEY 或 DEEPSEEK_API_KEY（gpt-researcher支持自定义LLM）
