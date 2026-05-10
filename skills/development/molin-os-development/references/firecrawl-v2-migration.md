# Firecrawl v2 API Migration (2026-05-11)

## What Changed

The `firecrawl-py` package (v4.x) migrated from dict-based returns to typed `Document` objects. Our bridge module at `molib/infra/external/firecrawl.py` needed fixes.

### Breaking Changes

| Old (v1 dict API) | New (v2 typed API) | Fix |
|---|---|---|
| `app.scrape_url(url, params={...})` | `app.scrape(url, formats=[...])` | Method name changed, params→direct kwargs |
| `app.search(query, params={...})` | `app.search(query, limit=N, sources=[...])` | params→direct kwargs |
| Returns `dict` with `{"data": {"markdown": "..."}}` | Returns `Document` object with `.markdown` attribute | Check `hasattr(result, 'markdown')` |
| `result["data"]["metadata"]["title"]` | `result.metadata.title` | Attribute access, not dict[key] |

### Bridge Module Fix Pattern

```python
result = app.scrape(url, formats=["markdown", "links"])

# Handle v2 Document objects
if hasattr(result, 'markdown'):
    return {
        "url": url,
        "markdown": result.markdown or "",
        "title": getattr(result.metadata, 'title', '') if result.metadata else '',
        "links": result.links or [],
        "status": "success",
        "source": "firecrawl",
    }

# Fallback for old v1 dict API
data = result.get("data", result) if isinstance(result, dict) else {}
return {
    "url": url,
    "markdown": data.get("markdown", ""),
    "title": data.get("metadata", {}).get("title", ""),
    ...
}
```

### Verification

```bash
# Firecrawl v2 works through Clash proxy
python3 -c "
from firecrawl import FirecrawlApp
app = FirecrawlApp(api_key='fc-...')
result = app.scrape('https://httpbin.org/html', formats=['markdown'])
print(type(result).__name__)  # 'Document'
print(result.markdown[:100])
"  # ~1.1s response time
```

### Affected Files

- `molib/infra/external/firecrawl.py` — fixed 2026-05-11 (commit 61553db)
