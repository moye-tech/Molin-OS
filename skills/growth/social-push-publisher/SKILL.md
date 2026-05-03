---
name: social-push-publisher
description: Multi-platform social media publishing workflow — post content to 小红书/知乎/微博/公众号/掘金/X using agent-browser automation. Self-evolution: auto-adapts to page changes. Safety: draft-only, no auto-publish.
version: 1.0.0
tags: [social-media, publishing, xiaohongshu, automation, agent-browser]
category: growth
source: https://github.com/jihe520/social-push
---

# Social Push Publisher — 多平台发布管线

## Overview

Automated social media publishing using agent-browser. Posts content to 7 Chinese platforms. The missing piece of our content pipeline: generate → publish.

## Supported Platforms

| 平台 | 类型 | 发布方式 |
|------|------|----------|
| 小红书 | 图文 | creator.xiaohongshu.com |
| 小红书 | 长文 | creator.xiaohongshu.com |
| 知乎 | 想法 | zhihu.com |
| 微博 | 微博 | weibo.com |
| 微信公众号 | 文章 | mp.weixin.qq.com |
| 掘金 | 文章 | juejin.cn |
| X/Twitter | 推文 | x.com |

## Prerequisites

```bash
npm install -g agent-browser
agent-browser install  # Download Chromium
```

Enable remote debugging: Chrome → `chrome://inspect/#remote-debugging` → Allow

## Publishing Workflow

### Xiaohongshu Image Post
```
1. Open: https://creator.xiaohongshu.com/publish/publish?source=official
2. Upload image: agent-browser upload @e1 "{path}"
3. Fill title: agent-browser fill @e1 "{title}"
4. Fill body: agent-browser fill ".ProseMirror" "{content}"
5. Add tags: agent-browser type ".ProseMirror" "#{tag}" + Enter
6. Save draft: agent-browser click save-button
```

### Safety Rules
- **Draft only** — Never auto-click "Publish"
- User confirms each post before going live
- Agent-browser uses user's existing Chrome session (already logged in)

## Integration with Content Pipeline

```
xiaohongshu-content-engine  →  generates JSON post
        ↓
ffmpeg-video-engine         →  generates video/image assets
        ↓
social-push-publisher       →  posts to platforms (draft)
        ↓
You                         →  review & publish
```

## Self-Evolution

When page structure changes:
1. Run `agent-browser snapshot` to see current elements
2. Fix interaction path
3. Update workflow reference files

## Limitations

- Requires agent-browser (npm global install)
- Requires Chrome with remote debugging enabled
- Cannot run headless (needs logged-in browser)
- References are Claude Code skill format — adapt for Hermes
