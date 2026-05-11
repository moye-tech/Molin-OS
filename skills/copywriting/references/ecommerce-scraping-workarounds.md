# Chinese E-Commerce Scraping Workarounds

> Context: Tmall/JD/淘宝 product pages use aggressive anti-bot protection (captcha, login walls, browser detection). Direct scraping via web_extract or browser_navigate almost always fails.

## Confirmed Blockers (as of 2026-05)

| Platform | Blocker | Symptom |
|:--|:--|:--|
| **Tmall** (detail.tmall.com) | Slider captcha + login wall | `Blocked: URL targets a private or internal network address` |
| **Taobao search** (s.taobao.com) | Login-required overlay | Page loads but search results hidden behind login modal |
| **JD** (item.jd.com) | Similar captcha defense | `Blocked: URL targets a private or internal network address` |

## Workaround Strategy (Priority Order)

### 1. Third-Party Comparison Articles (Best ROI)
Search for competitor comparison content on platforms that ARE scrapable:
- **知乎** (zhuanlan.zhihu.com) — parent reviews comparing 火花/豌豆/斑马
- **什么值得买** (smzdm.com) — deal pages often include product specs and pricing
- **人人都是产品经理** (woshipm.com) — competitive analysis articles with pricing/marketing strategy data
- **小红书** — parent reviews with real classroom screenshots (use xiaohongshu-content-engine skill)

Search query template:
```
"竞品A" OR "竞品B" "主图" OR "详情页" OR "卖点" OR "slogan" OR "广告语" 天猫
"竞品名" "体验课" "价格" "评价" "跟竞品对比"
```

### 2. Firecrawl Search (Moderate ROI)
Use `molib.infra.external.firecrawl` search_and_scrape with specific competitor queries. Note: MUST call `load_dotenv()` from `molib.shared.env_loader` first to inject FIRECRAWL_API_KEY into os.environ.

```python
from molib.shared.env_loader import load_dotenv; load_dotenv()
from molib.infra.external.firecrawl import search_and_scrape
```

### 3. Competitor Official Websites
For brand-level data (pricing, curriculum, class sizes), scrape the competitor's OWN website:
- 斑马AI学: huohua.cn (competitor domain, check actual URL)
- 豌豆思维: wandou.cn (competitor domain, check actual URL)
- These typically have LESS anti-bot protection than e-commerce platforms

### 4. Industry Reports
Search for PDF reports from 多鲸资本/国金证券/华创证券 that include competitive matrices with pricing/size/strategy data.

## Data Points to Extract for Copy Benchmarking

When collecting competitor data for copy writing:
- 体验课价格 (trial course price)
- 正价课价格 (full course price range)
- 班型大小 (class size: 1V4, 1V6, 1V8, etc.)
- 课程级别数 (curriculum levels: L1-L9, S1-S3, etc.)
- 核心营销标语 (core marketing slogans)
- 差异化卖点 (differentiated selling points)
- 致命弱点 (fatal weakness — what they CAN'T do that we CAN)
