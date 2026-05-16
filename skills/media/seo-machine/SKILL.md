# seo-machine · SEO优化引擎
# 归属: Agent A (media) · 版本: v1.0

## 触发词
触发词: SEO|搜索优化|关键词|排名|百度|谷歌|搜索量
触发词: 内容优化|标题优化|元描述|h1|alt标签

## 不调用时机
- 小红书/抖音内的关键词优化 → 各平台有专属逻辑，用对应技能

## 调用格式
INPUT: { "content": "待优化内容", "target_keywords": ["主关键词"], "platform": "blog|zhihu|wechat" }
OUTPUT: { "optimized_title": "优化后标题", "keywords_density": {...}, "suggestions": ["优化建议×5"], "score": 85 }

## 执行步骤
Step 1: 分析现有内容的关键词密度
Step 2: 检查标题、小标题、首段是否含目标关键词
Step 3: 检查图片alt文本、内部链接
Step 4: 生成优化建议（最多5条，按优先级排序）
Step 5: 输出优化评分（0-100）

## E-E-A-T检查项
- Experience: 有没有一手数据/亲身经历
- Expertise: 有没有专业术语/数据支撑
- Authoritativeness: 有没有引用来源
- Trustworthiness: 有没有客观局限性说明
