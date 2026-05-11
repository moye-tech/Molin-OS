# 闲鱼竞品定价监控工作流

> 用于 cron 定时作业的标准化竞品定价巡检流程。每条 SKU 对比自有定价与市场价格，检测异常变动（>15% 即告警），输出 Feishu 卡片报告。

## 数据源

| 层级 | 方法 | 说明 |
|------|------|------|
| 首选 | Scrapling / goofish_apis | 直接抓取闲鱼搜索结果，但要先检查 API 方法是否存在 |
| 降级 | web_search | 搜索 "闲鱼 <SKU名称> 价格 2026" 等关键词，从搜索结果提取价格带 |
| 辅助 | web_extract | 从搜索结果中的高价值文章提取详细定价信息，但注意部分 URL 被 block |
| 趋势 | web_search + mirofish | 搜索小红书热点话题，结合 mirofish-trends 技能做方向判断 |

## 数据存储

- 定价缓存：`~/.hermes/xianyu_bot/pricing_cache.json`
- 基准数据：`~/.hermes/skills/.../competitor-analysis/references/benchmark-pricing-YYYYMMDD.md`
- 产品数据：`~/.hermes/molin/business/custom_service_products.md`

### pricing_cache.json 结构

```json
{
  "last_check": "ISO datetime",
  "source": "web_search + scrapling",
  "products": {
    "<sku>": {
      "name": "商品名称",
      "our_price": int,
      "market_low": int,
      "market_median": int,
      "market_high": int,
      "trend": "stable|rising|falling|crashing|bifurcation",
      "note": "一句话说明"
    }
  },
  "market_trends": { "direction": "...", "note": "..." },
  "platform_changes": { "xianyu": "...", "xiaohongshu": "..." },
  "xhs_hot_topics": ["...", "..."],
  "mirofish_prediction": { "best_case_pct": int, "base_case_pct": int, "worst_case_pct": int },
  "anomalies": [{ "sku": "...", "metric": "market_median|market_low", "previous": int, "current": int, "delta_pct": float, "severity": "HIGH|MEDIUM" }],
  "recommendations": [{ "sku": "...", "action": "price_up|add_tier|reposition|none", "suggested": "...", "urgency": "HIGH|MEDIUM|LOW", "reason": "..." }]
}
```

## 异常检测规则

- 对比指标：market_median 和 market_low（上一次 vs 本次）
- 阈值：变动 > 15% 标记 MEDIUM，> 30% 标记 HIGH
- 发现 HIGH 异常必须输出 T4 告警卡片

## 输出规范

遵循 cron-output-formatter 和 feishu-message-formatter：
- 使用分隔线卡片模板，禁止 Markdown 格式
- T4 告警用三句话原则：发生什么 / 影响什么 / 需要做什么
- 总长度控制在 20 行以内
- 定价调整建议注明 urgency（HIGH 需立即行动）

## 已知限制

1. **goofish_apis 无 search_items**：`XianyuApis` 类没有 `search_items` 方法，不支持按关键词搜索商品。当前仅用于 token 验证和消息监听。
2. **molib intel trending 未就绪**：`python -m molib intel trending` 返回「功能仍在建设中」，降级到 `web_search`。
3. **web_extract 部分 URL 被 block**：huacidea.com、taokeshow.com、zhuanlan.zhihu.com 等域名被安全策略拦截。优先使用 web_search 摘要 + 人工合成价格带。
4. **Scrapling 需预安装**：`pip3 install scrapling`，当前已安装 v0.4.8。

## 执行检查清单

- [ ] Scrapling 已安装（`python3 -c "import scrapling"`）
- [ ] pricing_cache.json 存在且有上次数据
- [ ] goofish_apis cookies 有效（`python scripts/xianyu_check.py`）
- [ ] 4 个 SKU 都覆盖到：BP代写、PPT美化、LOGO设计、AI数字人
- [ ] web_search 关键词包含「闲鱼」+ SKU 名称 + 「价格」
- [ ] 异常检测对比上次缓存，输出 anomalies 数组
- [ ] 调价建议写入 recommendations 数组
- [ ] 最终输出为 cron 标准卡片格式（飞书纯文本）
