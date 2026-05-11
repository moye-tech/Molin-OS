"""
墨麟OS v2.5 — 墨笔文创 升级：crawl4ai 爆款对标写作

升级内容:
  - crawl4ai 实时抓取同类爆款文章作为写作对标参考
  - 提取标题公式、段落结构、高频词、情绪标签
  - 注入 ContentWriter prompt，实现"数据对标写作"
  - 保留原有 firecrawl + Research 协作 + 经验注入

用法:
    from molib.shared.content.reference_engine import ReferenceEngine
    ref = ReferenceEngine()
    references = await ref.fetch_references("AI副业", platform="xiaohongshu")
    # → [{title, structure, keywords, emotion_tags, engagement_data}]
"""

from __future__ import annotations

import logging
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


class ReferenceEngine:
    """
    爆款对标参考引擎：crawl4ai 抓取 + 结构提取。

    工作流：
      1. 搜索平台对应关键词
      2. crawl4ai 异步抓取 TOP N 爆款文章
      3. 提取：标题公式、段落结构、高频词、情绪词、话题标签
      4. 构建结构化参考注入 ContentWriter prompt

    平台支持:
      - xiaohongshu (小红书)
      - douyin (抖音)
      - zhihu (知乎)
      - gongzhonghao (公众号)
      - toutiao (头条)
    """

    # 平台搜索 URL 模板
    PLATFORM_SEARCH = {
        "xiaohongshu": "https://www.xiaohongshu.com/search_result?keyword={query}&type=51",
        "zhihu": "https://www.zhihu.com/search?type=content&q={query}",
        "toutiao": "https://www.toutiao.com/search/?keyword={query}",
    }

    # 小红书爆款标题公式（Autoxhs 参考）
    XHS_TITLE_FORMULAS = {
        "数字悬念": "【{N}个/种/招】+ 核心利益点",
        "痛点直击": "{痛点场景}？1个方法解决",
        "对比反差": "{错误做法} vs {正确做法}",
        "清单式": "{场景}必看的{N}个{类别}",
        "身份标签": "{身份}才知道的{N}个{秘密}",
        "结果晒图": "花了{N}{时间}，终于{成果}",
    }

    # 情绪词库（中文互联网高频）
    EMOTION_WORDS = {
        "好奇": ["到底", "竟然", "原来", "没想到", "居然"],
        "紧迫": ["限时", "最后", "错过", "再不", "紧急"],
        "惊喜": ["太值了", "赚到了", "宝藏", "神了", "绝了"],
        "认同": ["我懂", "就是", "确实", "同感", "一个人"],
        "收藏": ["先收藏", "马住", "存下来", "留着", "以后用"],
    }

    def __init__(self, use_crawl4ai: bool = True):
        self._crawl4ai_available = self._check_crawl4ai() if use_crawl4ai else False

    def _check_crawl4ai(self) -> bool:
        try:
            from crawl4ai import AsyncWebCrawler  # noqa: F401
            return True
        except ImportError:
            logger.warning("crawl4ai 未安装，将使用简化分析模式")
            return False

    async def fetch_references(
        self,
        topic: str,
        platform: str = "xiaohongshu",
        count: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        抓取同类爆款文章作为写作参考。

        Args:
            topic: 写作主题
            platform: 目标平台
            count: 抓取数量

        Returns:
            [{"title": str, "structure": list, "keywords": list, "emotion_tags": list, "url": str}, ...]
        """
        if not self._crawl4ai_available:
            return await self._analyze_offline(topic, platform, count)

        try:
            from crawl4ai import AsyncWebCrawler

            results = []
            async with AsyncWebCrawler() as crawler:
                # 搜索并抓取
                search_url = self.PLATFORM_SEARCH.get(
                    platform,
                    f"https://www.google.com/search?q={topic}+{platform}"
                )
                formatted_url = search_url.format(query=topic)

                result = await crawler.arun(url=formatted_url)
                if result and result.markdown:
                    # 从搜索结果中提取文章链接并批量抓取
                    # 简化版：直接从搜索结果页提取信息
                    references = self._extract_from_search_results(
                        result.markdown, topic, platform, count
                    )
                    results.extend(references)

            return results[:count]

        except Exception as e:
            logger.warning(f"crawl4ai 抓取失败: {e}，降级到离线分析")
            return await self._analyze_offline(topic, platform, count)

    async def _analyze_offline(
        self, topic: str, platform: str, count: int
    ) -> List[Dict[str, Any]]:
        """离线模式：基于平台特征和标题公式生成参考结构"""
        results = []

        if platform == "xiaohongshu":
            formulas = list(self.XHS_TITLE_FORMULAS.keys())
            for i in range(min(count, len(formulas))):
                formula_name = formulas[i]
                formula_template = self.XHS_TITLE_FORMULAS[formula_name]
                results.append({
                    "title_formula": formula_name,
                    "title_template": formula_template,
                    "structure": [
                        "1. 痛点/场景引入 (50字内)",
                        "2. 核心观点/方法 (3-5点，每点配emoji)",
                        "3. 案例/数据支撑 (1-2个)",
                        "4. 总结/行动建议 (30字内)",
                    ],
                    "keywords": self._generate_keywords(topic, platform),
                    "emotion_tags": self._detect_emotion_tags(topic),
                    "hashtags": self._generate_hashtags(topic, platform, count=5),
                    "url": f"(离线分析: {topic} @ {platform})",
                })
        else:
            # 通用平台模板
            results.append({
                "title_formula": "通用",
                "title_template": f"关于{topic}的深度分析",
                "structure": ["引子 → 分析 → 结论"],
                "keywords": self._generate_keywords(topic, platform),
                "emotion_tags": self._detect_emotion_tags(topic),
                "hashtags": [],
                "url": f"(离线分析: {topic} @ {platform})",
            })

        return results

    def build_reference_context(
        self,
        references: List[Dict[str, Any]],
        platform: str = "xiaohongshu",
    ) -> str:
        """
        将参考数据构建为可注入 ContentWriter prompt 的上下文。

        Args:
            references: fetch_references() 的返回结果
            platform: 目标平台

        Returns:
            结构化参考文本，适合注入 LLM prompt
        """
        if not references:
            return ""

        lines = ["📊 同类爆款对标参考（数据驱动写作）", ""]

        for i, ref in enumerate(references, 1):
            lines.append(f"📌 参考 {i}: {ref.get('title_formula', '通用')}")
            if ref.get("title_template"):
                lines.append(f"   标题公式: {ref['title_template']}")
            if ref.get("structure"):
                lines.append(f"   文章结构:")
                for s in ref["structure"]:
                    lines.append(f"     • {s}")
            if ref.get("keywords"):
                lines.append(f"   高频词: {', '.join(ref['keywords'][:10])}")
            if ref.get("emotion_tags"):
                lines.append(f"   情绪标签: {', '.join(ref['emotion_tags'])}")
            if ref.get("hashtags"):
                lines.append(f"   推荐话题: {' '.join(ref['hashtags'])}")
            lines.append("")

        # 平台写作提示
        platform_tips = {
            "xiaohongshu": "• 标题12-18字最佳\n• 封面图占比>60%\n• 正文含3-5个emoji\n• 话题标签4-6个",
            "douyin": "• 前3秒抓注意力\n• 节奏快，信息密度高\n• 字幕必加\n• 话题标签2-3个",
            "zhihu": "• 开头建立专业度\n• 分段清晰，有逻辑推演\n• 数据/引用支撑观点\n• 结尾有行动建议",
            "gongzhonghao": "• 标题<20字\n• 封面图4:3比例\n• 正文800-2000字\n• 底部引导关注",
        }
        if platform in platform_tips:
            lines.append(f"📝 {platform} 平台写作规范:")
            lines.append(platform_tips[platform])

        return "\n".join(lines)

    def _extract_from_search_results(
        self, markdown: str, topic: str, platform: str, count: int
    ) -> List[Dict[str, Any]]:
        """从搜索结果 markdown 中提取文章信息"""
        results = []
        # 简单提取标题和链接
        import re
        # 匹配 markdown 链接 [title](url)
        links = re.findall(r'\[(.+?)\]\((https?://[^)]+)\)', markdown)
        for title, url in links[:count]:
            if any(kw in title.lower() for kw in topic.lower().split()):
                results.append({
                    "title_formula": "搜索匹配",
                    "title_template": title[:100],
                    "structure": ["(需深度抓取)"],
                    "keywords": self._generate_keywords(topic, platform),
                    "emotion_tags": self._detect_emotion_tags(title),
                    "hashtags": [],
                    "url": url,
                })
        return results

    def _generate_keywords(
        self, topic: str, platform: str, count: int = 10
    ) -> List[str]:
        """根据主题和平台生成推荐关键词"""
        base = topic.split()
        # 平台常用后缀
        suffixes = {
            "xiaohongshu": ["推荐", "测评", "攻略", "避坑", "好物", "分享", "教程", "测评"],
            "douyin": ["挑战", "教程", "vlog", "日常", "好物"],
            "zhihu": ["分析", "盘点", "解读", "思考", "经验"],
        }
        platform_suffixes = suffixes.get(platform, ["分析", "推荐"])
        return base + platform_suffixes[: count - len(base)]

    def _detect_emotion_tags(self, text: str) -> List[str]:
        """检测文本中的情绪标签"""
        matched = []
        for emotion, words in self.EMOTION_WORDS.items():
            if any(w in text for w in words):
                matched.append(emotion)
        return matched or ["好奇"]

    def _generate_hashtags(
        self, topic: str, platform: str, count: int = 5
    ) -> List[str]:
        """生成推荐话题标签"""
        base = topic.replace(" ", "")
        tags = [f"#{base}", f"#{base}分享", f"#{base}推荐"]
        if platform == "xiaohongshu":
            tags += ["#小红书推荐", "#好物分享"]
        elif platform == "douyin":
            tags += ["#抖音好物", "#干货分享"]
        return tags[:count]

    @property
    def available(self) -> bool:
        return self._crawl4ai_available

    @property
    def title_formulas(self) -> Dict[str, str]:
        """返回所有标题公式"""
        return dict(self.XHS_TITLE_FORMULAS)
