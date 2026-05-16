# web-scraper · 智能网页抓取
# 归属: 全部5个Agent共享（通过Agent D跨线调用最优）
## 触发词
触发词: 抓取|爬取|搜索网络|最新信息|实时数据|联网查询
触发词: 竞品价格|热榜|热搜|最新文章
## 引擎策略
优先: crawl4ai（本地，零成本，M1原生）
降级: firecrawl CLI（API，免费500页/月）
## 调用
python3.11 ~/Molin-OS/tools/web_scraper.py 
python3.11 ~/Molin-OS/tools/web_scraper.py  --engine firecrawl
## 禁止
- 禁止用于需要登录的平台（改用browser-use）
- 禁止频繁抓取同一页面（>1次/小时）
