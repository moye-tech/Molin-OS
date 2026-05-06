"""
墨麟AIOS — SEOTool
SEO关键词研究、标题优化、内容分析工具
参考吸收: Agent-Reach (Jina Reader), CowAgent (多渠道适配)
"""

import re
import math
from typing import Optional


class SEOTool:
    """SEO研究与内容优化工具"""

    # 吸引词库（点击率增强）
    POWER_WORDS = [
        "终极", "必备", "惊人", "颠覆", "秘密", "免费", "独家",
        "完整", "权威", "高效", "立即", "重磅", "深度", "实战",
        "零基础", "从0到1", "保姆级", "超全", "2025", "最新",
        "推荐", "必看", "收藏", "干货", "建议", "指南", "教程",
    ]

    # 常见中文标题前缀数字模式
    NUMBER_PREFIX_PATTERNS = [
        "{n}个", "{n}种", "{n}大", "{n}步", "{n}招",
        "从{n}个", "这{n}个",
    ]

    @staticmethod
    def _extract_core_topic(topic: str) -> str:
        """从主题中提取核心词（去掉修饰词）"""
        stop_words = ["如何", "怎么", "怎样", "什么", "哪个", "多少", "为什么", "是否"]
        words = re.split(r"[,，\s]+", topic.strip())
        for w in words:
            if w not in stop_words:
                return w
        return topic.strip()

    @staticmethod
    def _simulate_keyword_search(topic: str, count: int) -> list[dict]:
        """
        模拟关键词研究逻辑（基于真实SEO方法论）：
        1. 核心词：主题本身 + 简短变体
        2. 长尾词：核心词 + 修饰/场景/人群
        3. 问题词：疑问句式关键词
        4. 相关词：语义相关词汇
        """
        core = SEOTool._extract_core_topic(topic)

        # 种子词（核心词衍生）
        seed_variants = [
            core,
            f"{core}教程",
            f"{core}入门",
            f"{core}进阶",
            f"{core}技巧",
            f"{core}方法",
            f"{core}工具",
            f"{core}平台",
            f"{core}软件",
            f"{core}课程",
        ]

        # 长尾词构建器（场景+人群+意图）
        longtail_modifiers = [
            "零基础学", "新手", "高手", "2025最新",
            "效率提升", "免费", "在线", "实战",
            "从入门到精通", "怎么用", "推荐",
        ]

        # 问题词
        question_stems = [
            f"{core}是什么",
            f"{core}如何入门",
            f"{core}怎么学",
            f"{core}多少钱",
            f"{core}哪个好",
            f"{core}和{core}的区别",
            f"{core}值不值得学",
            f"{core}适合什么人",
            f"{core}就业前景",
            f"{core}有哪些坑",
        ]

        # 相关词（基于常见语义关联）
        related_modifiers = [
            f"最好的{core}",
            f"{core}与AI",
            f"{core}自动化",
            f"{core}未来趋势",
            f"{core}案例",
            f"{core}实战经验",
        ]

        # 组装并去重
        keyword_pool: list[str] = []
        keyword_pool.extend(seed_variants)
        for base in seed_variants[:5]:
            for mod in longtail_modifiers[:4]:
                keyword_pool.append(f"{mod}{base}")
        keyword_pool.extend(question_stems)
        keyword_pool.extend(related_modifiers)

        # 去重并限制数量
        seen = set()
        unique_keywords: list[str] = []
        for kw in keyword_pool:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)

        # 按类别打标签
        result: list[dict] = []
        for i, kw in enumerate(unique_keywords[:count]):
            if kw in question_stems:
                kw_type = "question"
            elif any(mod in kw for mod in longtail_modifiers[:6]) or len(kw) > len(core) + 4:
                kw_type = "longtail"
            else:
                kw_type = "core"
            result.append({"keyword": kw, "type": kw_type, "rank": i + 1})

        return result

    def generate_keywords(self, topic: str, count: int = 10) -> list[str]:
        """
        基于主题生成关键词簇（核心词+长尾词+问题词）

        Args:
            topic: 主题关键词
            count: 返回关键词数量（默认10）

        Returns:
            关键词列表
        """
        if not topic or not topic.strip():
            return []
        if count < 1:
            count = 1

        result = self._simulate_keyword_search(topic, count)
        return [item["keyword"] for item in result]

    def optimize_title(self, title: str, keywords: Optional[list[str]] = None) -> str:
        """
        优化标题：数字前缀、关键词前置、吸引词增强

        Args:
            title: 原标题
            keywords: 可选关键词列表

        Returns:
            优化后的标题
        """
        if not title or not title.strip():
            return ""

        # 1. 关键词前置：如果提供了关键词，确保核心关键词出现在标题前15个字符内
        if keywords:
            core_kw = keywords[0]
            # 如果核心词不在标题前部，尝试前置
            pos = title.find(core_kw)
            if pos > 15 or pos == -1:
                title = f"{core_kw}｜{title}"

        # 2. 吸引词增强：为标题前部添加吸引词（如果还没包含）
        has_power_word = any(pw in title for pw in self.POWER_WORDS)
        if not has_power_word:
            # 随机选择一个吸引词插入（但保持确定性，基于标题hash）
            idx = hash(title) % len(self.POWER_WORDS)
            title = f"{self.POWER_WORDS[idx]}！{title}"

        # 3. 数字前缀：如果标题不含数字，尝试添加数字前缀
        if not re.search(r"\d+", title):
            idx = abs(hash(title + "num")) % 5
            num = [3, 5, 7, 10, 12][idx]
            prefixes = [
                f"{num}个{title}",
                f"{num}种{title}方式",
                f"{num}步搞定{title}",
            ]
            prefix = prefixes[idx % len(prefixes)]
            title = prefix

        return title

    def analyze_seo(self, text: str, keywords: list[str]) -> dict:
        """
        分析文本SEO质量

        Args:
            text: 待分析文本
            keywords: 目标关键词列表

        Returns:
            dict: 包含关键词密度、标题优化度、可读性评分等
        """
        if not text or not text.strip():
            return {
                "total_words": 0,
                "keyword_density": {},
                "avg_density": 0.0,
                "title_optimization_score": 0,
                "readability_score": 0,
                "suggestions": ["文本为空"],
            }

        # 分词（粗略中文分词：按2-gram + 单字）
        text_clean = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9]", "", text)
        # 中文字符计数
        chinese_chars = len(re.findall(r"[\u4e00-\u9fa5]", text_clean))
        # 英文单词
        english_words = len(re.findall(r"[a-zA-Z]+", text))
        total_words = chinese_chars + english_words

        if total_words == 0:
            return {
                "total_words": 0,
                "keyword_density": {},
                "avg_density": 0.0,
                "title_optimization_score": 0,
                "readability_score": 0,
                "suggestions": ["文本不含可分析内容"],
            }

        # 关键词密度计算
        keyword_density: dict[str, float] = {}
        for kw in keywords:
            count = text.count(kw)
            # 中文字符计算：关键词长度/总字符数
            kw_len = len(kw)
            density = round((count * kw_len) / max(total_words, 1) * 100, 2)
            keyword_density[kw] = density

        avg_density = round(
            sum(keyword_density.values()) / max(len(keyword_density), 1), 2
        )

        # 标题优化度评分 (0-100)
        title_score = 0
        # 检查关键词是否在文本前10%出现
        first_10pct = text[:max(len(text) // 10, 100)]
        kw_in_first_part = sum(1 for kw in keywords if kw in first_10pct)
        title_score += min(kw_in_first_part * 15, 60)

        # 检查关键词密度是否在合理范围(2%-8%)
        if 2.0 <= avg_density <= 8.0:
            title_score += 20
        elif avg_density > 8.0:
            title_score += 5  # 过高扣分
        else:
            title_score += 10  # 过低

        # 检查是否有数字（提高可信度）
        if re.search(r"\d+", text):
            title_score += 10

        # 检查是否有吸引词
        power_count = sum(1 for pw in self.POWER_WORDS if pw in text)
        title_score += min(power_count * 2, 10)

        title_score = min(title_score, 100)

        # 可读性评分 (0-100)
        readability_score = 0

        # 段落长度：短段落利于阅读（中文每段<=200字为好）
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        if paragraphs:
            avg_para_len = sum(len(p) for p in paragraphs) / len(paragraphs)
            if avg_para_len <= 200:
                readability_score += 30
            elif avg_para_len <= 400:
                readability_score += 20
            else:
                readability_score += 10

        # 句子长度：平均15-30字最优
        sentences = re.split(r"[。！？.!?]", text)
        sentences = [s for s in sentences if len(s.strip()) > 0]
        if sentences:
            avg_sent_len = sum(len(s) for s in sentences) / len(sentences)
            if 15 <= avg_sent_len <= 30:
                readability_score += 25
            elif 10 <= avg_sent_len <= 40:
                readability_score += 15
            else:
                readability_score += 5
        else:
            readability_score += 5

        # 文章长度
        if total_words >= 500:
            readability_score += 20
        elif total_words >= 200:
            readability_score += 10
        else:
            readability_score += 5

        # 标题/分段：有小标题更好读
        heading_count = len(re.findall(r"^#{1,4}\s", text, re.MULTILINE))
        if heading_count >= 3:
            readability_score += 15
        elif heading_count >= 1:
            readability_score += 8

        # 列表/标点多样性
        list_count = len(re.findall(r"[-\*\d+\.]\s", text))
        if list_count >= 3:
            readability_score += 10

        readability_score = min(readability_score, 100)

        # 优化建议生成
        suggestions = []
        if avg_density < 2:
            suggestions.append(f"关键词密度偏低({avg_density}%)，建议增加关键词出现频次")
        elif avg_density > 8:
            suggestions.append(f"关键词密度偏高({avg_density}%)，建议适当分散，避免堆砌")
        if title_score < 60:
            suggestions.append("标题优化度不足，建议将核心关键词前置")
        if readability_score < 50:
            suggestions.append("可读性偏低，建议缩短段落和句子")
        if not re.search(r"\d+", text):
            suggestions.append("建议添加数据/数字增强可信度")

        return {
            "total_words": total_words,
            "keyword_density": keyword_density,
            "avg_density": avg_density,
            "title_optimization_score": title_score,
            "readability_score": readability_score,
            "suggestions": suggestions,
        }
