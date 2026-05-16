# research-engine · 实时调研引擎
# 归属: Agent D (shared) 提供，A/B/C/E均可跨线调用 · 版本: v1.0

## 技能身份
基于 gpt-researcher 的深度联网调研引擎。
自动多源搜索+综合分析，返回结构化报告。

## 触发词
触发词: 竞品|市场调研|行业趋势|最新数据|联网搜索
触发词: 分析市场|情报|扫描|实时信息|最新动态
触发词: research|调研|调查|查询|查一下

## 不调用时机
- 只是问观点/建议（不需要联网数据时）→ 直接回答
- 需要登录的平台数据 → 用 browser-use

## 核心引擎
主引擎: gpt-researcher（自动多源联网搜索+综合分析）
辅助: web-scraper（定向页面抓取）
缓存: 相同查询24小时内复用结果（节省API）

## 调用格式（跨Agent请求）
写入 relay/shared/cross_request.json:
```json
{ "requester": "media", "service": "research", "task": "调研主题", "priority": "L0" }
```
或者直接调用：
```bash
python3 ~/Molin-OS/tools/research_engine.py "调研主题"
```

## 输出格式
```json
{
  "query": "调研主题",
  "sources": ["来源URL"],
  "summary": "300字摘要",
  "key_findings": ["关键发现×5"],
  "report": "完整报告"
}
```

## 当前经验规则（动态更新）
- query越具体结果越有用（如「2026年AI Agent市场中国区TOP5玩家」好于「AI市场怎么样」）
- 相同query 24h内缓存，不要重复请求
