"""
墨麟AIOS — SocialWriter
多平台社交媒体内容生成器
参考吸收: xhs-cli (小红书笔记格式), CowAgent (多平台适配), Agent-Reach
"""

import re
import random
from typing import Optional


class SocialWriter:
    """社交媒体多平台内容创作工具"""

    # 小红书emoji词库
    XHS_EMOJI_TITLES = {
        "种草": ["✨", "🔥", "💖", "🌟", "🎯", "🎀", "💫", "🛍️", "💎"],
        "测评": ["📊", "🔍", "⚖️", "🧪", "🎯", "📋", "💡"],
        "教程": ["📚", "🎓", "✏️", "💻", "🛠️", "📖", "🔧"],
        "日常": ["☀️", "🌷", "🍃", "🌸", "☕", "📸", "🎬", "✨"],
        "穿搭": ["👗", "👠", "👜", "💄", "✨", "🧥", "👟", "🎀"],
    }
    XHS_EMOJI_BODY = ["✅", "👉", "💡", "📌", "🔑", "⚠️", "🌟", "🔥", "💯", "🎯"]
    XHS_HASHTAGS = {
        "通用": ["种草", "好物推荐", "测评", "开箱", "必入", "好物分享", "省钱", "性价比"],
        "美妆": ["美妆", "护肤", "化妆教程", "素颜", "变美"],
        "数码": ["数码评测", "黑科技", "效率工具", "App推荐", "桌面好物"],
        "学习": ["学习方法", "自我提升", "读书笔记", "知识分享", "干货"],
        "生活": ["生活方式", "极简主义", "家居好物", "收纳", "DIY"],
    }

    # 知乎风格词库
    ZHIHU_ANGLES = {
        "专业": ["从专业角度分析", "基于XX理论", "数据显示", "行业共识", "学术研究表明"],
        "通俗": ["简单来说", "打个比方", "类比一下", "用人话解释", "不扯虚的"],
        "犀利": ["醒醒吧", "真相是", "扎心了", "你被骗了", "别被忽悠了"],
        "温情": ["感同身受", "抱抱你", "慢慢来", "我理解", "没关系的"],
    }
    ZHIHU_GOLDEN_QUOTES = [
        "种一棵树最好的时间是十年前，其次是现在。",
        "信息差就是认知差，认知差就是财富差。",
        "真正的自由不是想做什么就做什么，而是不想做什么就可以不做什么。",
        "这世上只有一种成功，就是用自己喜欢的方式过一生。",
        "行动是治愈恐惧的良药，而犹豫和拖延将不断滋养恐惧。",
        "一个人的格局，是由他读过的书、走过的路、遇到的人决定的。",
    ]

    # 微信文章标题模式
    WECHAT_TITLE_PATTERNS = [
        "⚠️{prompt}，{result}",
        "{num}个{prompt}，第{n}个太{adj}了",
        "⎡干货⎦{topic}：{promise}",
        "{topic}，原来{reveal}",
        "为什么{prompt}？这是我见过最好的答案",
        "{topic}，看完我{reaction}",
    ]

    WECHAT_CTA_TEMPLATES = [
        "如果这篇文章对你有帮助，欢迎**点赞、在看、转发**三连支持 🙏",
        "你还有什么{prompt}的心得？欢迎在**评论区**分享～",
        "觉得有用？点个**关注**，不错过更多干货内容 🚀",
        "扫码添加我的微信，回复「{keyword}」领取完整资料包",
    ]

    # 内容规划模板
    PLATFORM_TEMPLATES = {
        "小红书": {"format": "图文笔记", "style_tips": "首图要吸引眼球，标题带emoji，正文分段+标签"},
        "知乎": {"format": "问答/专栏", "style_tips": "专业感优先，开头抓人，结构清晰，引用数据"},
        "微信公众号": {"format": "长文", "style_tips": "标题党适度，引言Hook，小标题分段，CTA收尾"},
        "抖音": {"format": "短视频(15-60s)", "style_tips": "前3秒定生死，节奏快，字幕+BGM"},
        "B站": {"format": "中视频(3-15min)", "style_tips": "封面标题党，开头设悬念，弹幕互动感"},
        "微博": {"format": "短文/Thread", "style_tips": "140字以内说重点，配图3-9张，热门话题标签"},
        "LinkedIn": {"format": "专业长文", "style_tips": "数据驱动，行业洞察，英文/中英双语"},
        "Twitter/X": {"format": "Thread", "style_tips": "1条引子+多条展开，每推<280字，附链接"},
    }

    @staticmethod
    def _pick_emoji(style: str) -> str:
        """根据风格选取emoji"""
        emojis = SocialWriter.XHS_EMOJI_TITLES.get(style, ["✨", "🔥"])
        idx = hash(style + str(random.random())) % len(emojis)
        return emojis[idx]

    @staticmethod
    def _generate_xhs_title(topic: str, style: str) -> str:
        """生成小红书标题（emoji + 吸睛文案）"""
        emoji = SocialWriter._pick_emoji(style)

        templates = [
            f"{emoji} {topic}｜{random.choice(['真的绝了', '后悔没早知道', '建议收藏', '亲测有效', '太好用了'])}",
            f"{emoji} 救命！{topic}也太{random.choice(['香了', '绝了', '好用了', '值得了'])}吧",
            f"{emoji} 为了{topic}我准备了{random.choice(['一整年', '三个月', '两个月', '半年'])}…",
            f"{emoji} {random.choice(['抄作业', '抄答案', '懒人包', '直接抄'])}！{topic}全攻略",
            f"{'｜'.join([emoji, topic, random.choice(['干货', '攻略', '教程', '推荐'])])}",
        ]
        idx = hash(topic + style) % len(templates)
        return templates[idx]

    @staticmethod
    def _generate_xhs_content(topic: str, style: str, num_paragraphs: int = 4) -> list[str]:
        """生成小红书正文段落"""
        paragraphs = []

        # 开头Hook
        hooks = [
            f"姐妹们！今天一定要跟大家分享{topic}的{random.choice(['心得', '经验', '宝藏发现', '超值推荐'])}～",
            f"终于把{topic}搞明白了！来交作业了📝",
            f"关于{topic}，我总结了{random.choice(['这几点', '这些干货', '这些经验'])}，全是干货🧾",
f'"好物要一起分享！{topic}我真的太爱了💕"',
        ]
        idx = hash(topic) % len(hooks)
        paragraphs.append(hooks[idx])

        # 中间内容段落
        content_lines = [
            f"👉 先说说我的{topic}经历吧……",
            f"📌 分享{random.choice(['3个', '5个', '几个'])}核心要点：",
            f"🌟 {random.choice(['用过之后', '体验下来', '对比之后'])}，最让我惊喜的是——",
            f"⚠️ {random.choice(['避坑指南', '注意事项', '别踩这些坑'])}：",
            f"💡 小tips：{random.choice(['坚持才是关键', '用量要足', '选对渠道很重要', '别贪便宜'])}",
            f"🔑 {random.choice(['核心逻辑', '底层原理', '关键方法'])}其实很简单——",
            f"📊 我做了{topic}的{random.choice(['测试', '对比', '数据统计'])}，结果如下：",
        ]

        # 随机选取3-5条作为中间段落
        selected = random.sample(content_lines, min(num_paragraphs - 2, len(content_lines)))
        for line in selected:
            # 为段落补充模拟内容
            detail_templates = [
                f"{line}\n{random.choice(['亲测有效！', '很多人不知道这一点', '我也是踩坑后才懂', '这个真的太重要了'])}",
                f"{line}\n{random.choice(['效果肉眼可见', '性价比超高', '省时又省力', '小白也能轻松上手'])}",
                f"{line}\n{random.choice(['建议先收藏再看', '看完记得点赞', '评论区见～', '还有更多干货往下看'])}",
            ]
            paragraphs.append(random.choice(detail_templates))

        # 结尾CTA
        ctas = [
            "今天就分享到这啦～希望对姐妹们有帮助！\n记得❤️点赞+⭐收藏，下次不迷路～",
            "你们还有什么好方法？评论区告诉我吧！\n👇👇👇",
            "整理不易，如果对你有用请给我一个小心心❤️\n下次继续分享更多干货！",
        ]
        paragraphs.append(random.choice(ctas))

        return paragraphs

    @staticmethod
    def _generate_xhs_tags(topic: str, count: int = 6) -> list[str]:
        """生成小红书标签"""
        # 基于主题推断内容类型
        topic_lower = topic.lower()

        # 通用标签池
        tags = [
            f"#{topic}",
            f"#{topic}心得",
            f"#{topic}分享",
        ]

        # 根据主题补充领域标签
        domain_tags = {
            "美妆": ["#美妆", "#护肤", "#好物推荐", "#变美"],
            "护肤": ["#护肤", "#好物分享", "#素颜", "#变美"],
            "数码": ["#数码好物", "#黑科技", "#效率工具", "#开箱"],
            "学习": ["#学习", "#自我提升", "#干货分享", "#知识"],
            "穿搭": ["#穿搭", "#OOTD", "#时尚", "#搭配"],
            "美食": ["#美食", "#探店", "#食谱", "#吃货"],
            "健身": ["#健身", "#运动", "#健康", "#自律"],
            "旅游": ["#旅行", "#旅游攻略", "#打卡", "#周末去哪儿"],
        }

        for domain, domain_list in domain_tags.items():
            if domain in topic_lower:
                tags.extend(domain_list)
                break

        # 补一些通用热门标签
        common_hashtags = ["#好物推荐", "#种草", "#测评", "#干货", "#推荐", "#必入"]
        while len(tags) < count:
            tag = random.choice(common_hashtags)
            if tag not in tags:
                tags.append(tag)

        return tags[:count]

    def xiaohongshu_post(self, topic: str, style: str = "种草") -> dict:
        """
        生成小红书笔记

        Args:
            topic: 笔记主题
            style: 风格（种草/测评/教程/日常/穿搭）

        Returns:
            dict: 标题、正文段落、标签、封面建议、统计信息
        """
        if style not in self.XHS_EMOJI_TITLES:
            style = "种草"

        title = self._generate_xhs_title(topic, style)
        paragraphs = self._generate_xhs_content(topic, style, num_paragraphs=4)
        tags = self._generate_xhs_tags(topic, count=7)

        # 封面建议
        cover_suggestions = {
            "构图": [
                f"{topic}实物平铺图（俯拍45°）",
                f"{topic}使用场景+产品合拍",
                f"Before/After对比图（冲击力更强）",
                f"纯色背景+{topic}居中特写",
            ],
            "文案": [
                f"大字: {topic}",
                f"花字: {random.choice(['绝了', '后悔没早买', '试试这个方法'])}",
                "加标签: 好物推荐/测评/开箱",
            ],
            "配色": [
                "亮色系突出主体（红/黄/蓝）",
                "低饱和莫兰迪色系（高级感）",
                "纯白背景+产品本身颜色",
            ],
        }

        # 计算总字数
        full_text = "\n".join(paragraphs)
        word_count = len(full_text.replace(" ", "").replace("\n", ""))

        return {
            "platform": "小红书",
            "style": style,
            "title": title,
            "content": paragraphs,
            "full_text": full_text,
            "tags": tags,
            "cover_suggestions": cover_suggestions,
            "statistics": {
                "paragraphs": len(paragraphs),
                "tags_count": len(tags),
                "word_count": word_count,
                "estimated_minutes": max(1, round(word_count / 300)),
            },
        }

    def zhihu_answer(self, question: str, angle: str = "专业") -> dict:
        """
        生成知乎回答

        Args:
            question: 问题描述
            angle: 角度（专业/通俗/犀利/温情）

        Returns:
            dict: 导语、分论点、总结金句、参考文献
        """
        if angle not in self.ZHIHU_ANGLES:
            angle = "专业"

        angle_phrases = self.ZHIHU_ANGLES[angle]

        # 导语
        intro_templates = [
            f"这个问题很有代表性。{random.choice(angle_phrases)}，我来聊聊我的看法。",
            f"看到这个问题，我想起{random.choice(['之前做过的研究', '自己的亲身经历', '一个经典的案例'])}。",
            f"谢邀。{random.choice(angle_phrases)}，我认为可以从以下几个维度来理解这个问题。",
        ]
        intro = random.choice(intro_templates)

        # 分论点 (3-4个)
        point_count = random.randint(3, 4)

        # 根据主题生成论点骨架
        point_templates = [
            {
                "title": f"第一，理解{question[:8]}的本质",
                "body": f"很多人对{question[:6]}存在误解。{random.choice(angle_phrases)}，"
                        f"我们需要先搞清楚核心概念。{random.choice(['根据行业数据', '从理论角度来说', '实践表明'])}，"
                        f"这个问题涉及的底层逻辑是{random.choice(['信息不对称', '供需关系', '认知差异', '系统效率'])}。"
            },
            {
                "title": f"第二，{question[:6]}的常见误区",
                "body": f"在实际操作中，{random.choice(['80%的人都会犯这个错', '大多数人忽略了这一点', '常见的做法其实是错的'])}。"
                        f"正确的方式应该是{random.choice(['从本质出发', '先找到问题根源', '换一个角度思考'])}。"
            },
            {
                "title": f"第三，我的{random.choice(['实操经验', '方法论', '解决方案'])}",
                "body": f"经过{random.choice(['长期实践', '多次验证', '系统研究'])}，我总结出以下{random.choice(['3步', '5个要点', '核心框架'])}：\n"
                        f"1. {random.choice(['明确目标', '收集信息', '建立认知'])}\n"
                        f"2. {random.choice(['深度分析', '拆解问题', '找到切入点'])}\n"
                        f"3. {random.choice(['行动验证', '持续迭代', '形成闭环'])}"
            },
            {
                "title": f"第四，{random.choice(['数据支撑', '案例分析', '延伸思考'])}",
                "body": f"从数据来看，{random.choice(['70%的案例表明', '行业报告显示', '调研结果指出'])}，"
                        f"这个问题的关键变量是{random.choice(['执行力度', '认知水平', '资源投入', '方法选择'])}。"
                        f"举一个实际案例：{random.choice(['某知名公司', '一个普通用户', '我自己的经历'])}……"
            },
        ]

        # 随机选取 (保证至少3个)
        selected_points = random.sample(point_templates, min(point_count, len(point_templates)))
        # 如果不够，复用第一个
        while len(selected_points) < point_count:
            selected_points.append(point_templates[0])

        # 论点数量调整为 point_count
        selected_points = selected_points[:point_count]

        arguments = []
        for i, pt in enumerate(selected_points):
            arguments.append({
                "index": i + 1,
                "title": pt["title"],
                "body": pt["body"],
            })

        # 总结金句
        golden_quote = random.choice(self.ZHIHU_GOLDEN_QUOTES)
        summary = (
            f"总结一下：\n\n"
            f"{random.choice(['最关键的是', '说到底', '归根结底'])}，"
            f"{question[:10]}的核心在于{random.choice(['认知差', '执行力', '信息差', '方法论'])}。\n\n"
            f"「{golden_quote}」"
        )

        # 参考文献（模拟）
        references = [
            f"《{random.choice(['认知觉醒', '深度工作', '刻意练习', '思考快与慢', '反脆弱'])}》",
            f"{random.choice(['行业白皮书', '年度报告', '市场调研'])}（{random.choice(['2024', '2025'])}）",
            f"{random.choice(['知乎高赞回答', '专业博客', '学术论文'])}：{question[:15]}",
        ]

        # 组装全文
        full_parts = [intro]
        for arg in arguments:
            full_parts.append(f"**{arg['title']}**\n{arg['body']}")
        full_parts.append(summary)

        full_text = "\n\n".join(full_parts)

        return {
            "platform": "知乎",
            "angle": angle,
            "question": question,
            "intro": intro,
            "arguments": arguments,
            "summary": summary,
            "golden_quote": golden_quote,
            "references": references,
            "full_text": full_text,
            "statistics": {
                "arguments_count": point_count,
                "references_count": len(references),
                "word_count": len(full_text.replace(" ", "").replace("\n", "")),
            },
        }

    def wechat_article(self, topic: str, word_count: int = 2000) -> dict:
        """
        生成微信公众号文章

        Args:
            topic: 文章主题
            word_count: 目标字数

        Returns:
            dict: 标题、引言、小标题分段、结语CTA
        """
        # 标题生成
        title = self._generate_wechat_title(topic)

        # 引言
        intro_templates = [
            f"不知道你有没有这样的感受：提到{topic}，很多人第一反应是……但其实并不是这样。",
            f"做{topic}这件事，我坚持了{random.choice(['3年', '5年', '很久'])}，今天想跟大家聊聊我的真实感受。",
            f"「{topic}」——这个话题最近频繁出现在我的视野里。到底什么是{topic}？它真的有用吗？",
            f"如果2025年只推荐一件事，那一定就是{topic}。为什么这么说？看完你就明白了。",
        ]
        intro = random.choice(intro_templates)

        # 计算需要多少个小标题分段
        num_sections = random.randint(4, 6)
        avg_section_len = max(200, word_count // num_sections)

        sections = []
        section_titles_templates = [
            f"一、什么是{topic}？",
            f"二、为什么{topic}如此重要？",
            f"三、{topic}的{random.choice(['核心方法论', '底层逻辑', '实操框架'])}",
            f"四、{topic}常见的{random.choice(['3大误区', '5个坑', '认知偏差'])}",
            f"五、如何快速上手{topic}？",
            f"六、{topic}的{random.choice(['未来趋势', '进阶之路', '高阶玩法'])}",
            f"七、我的{random.choice(['真实案例', '亲身经历', '实战心得'])}",
            f"八、{topic}与其他方法的{random.choice(['对比分析', '优劣对比'])}",
        ]

        # 内容生成模板
        body_templates = [
            f"{topic}这个概念，其实最早来自于{random.choice(['国外', '行业内', '实践中'])}。"
            f"简单来说，就是{random.choice(['一种思维方式', '一套方法论', '一个工具框架'])}。"
            f"它的核心价值在于{random.choice(['提高效率', '降低成本', '提升认知', '解决问题'])}。",

            f"根据{random.choice(['调研数据', '行业报告', '实践经验'])}显示，"
            f"{random.choice(['70%的用户', '大多数从业者', '成功案例'])}表明{topic}确实有效。"
            f"但前提是{random.choice(['方法要正确', '要坚持执行', '不能盲目套用'])}。",

            f"那么具体应该怎么做呢？首先，{random.choice(['明确目标', '收集信息', '搭建框架'])}。"
            f"其次，{random.choice(['深度分析', '拆解步骤', '制定计划'])}。"
            f"最后，{random.choice(['行动验证', '复盘迭代', '持续优化'])}。",

            f"在实际操作中，很多人容易犯以下错误：\n"
            f"❌ {random.choice(['急于求成', '方法不对', '半途而废'])}\n"
            f"✅ 正确的做法是{random.choice(['循序渐进', '找到适合自己的方法', '坚持+复盘'])}。",

            f"举一个真实的案例。我的朋友{random.choice(['小王', '小李', '小张'])}，"
            f"在尝试{topic}之前{random.choice(['效率很低', '效果不佳', '走了很多弯路'])}。"
            f"但当他掌握了正确方法后，{random.choice(['效果提升了3倍', '轻松达到了目标', '效率大幅提升'])}。",

            f"从长远来看，{topic}的意义不仅在于{random.choice(['短期收益', '当下效果', '表面改变'])}，"
            f"更在于{random.choice(['认知升级', '能力建设', '长期积累'])}。"
            f"这才是真正的壁垒。",
        ]

        for i in range(num_sections):
            title_text = section_titles_templates[i] if i < len(section_titles_templates) else f"{'一二三四五六七八九十'[i]}、关于{topic}的更多思考"
            body = random.choice(body_templates).replace("  ", "\n")
            # 补足到目标段落长度
            while len(body) < avg_section_len:
                body += f"\n\n{random.choice(['另外', '值得一提的是', '需要特别注意的是'])}，"
                body += f"{random.choice(['这个观点很重要', '这一点容易被忽略', '很多人并不知道'])}。"
                
            sections.append({
                "title": title_text,
                "body": body[:avg_section_len + 100],  # 稍微超长但不严重
            })

        # 结语CTA
        cta_list = [
            f"**写在最后**\n\n"
            f"{topic}不是一蹴而就的，需要持续的学习和实践。"
            f"希望这篇文章能给你一些启发。\n\n"
            f"{'你还有什么'}{random.choice(['疑问', '心得', '补充'])}？欢迎在评论区交流～\n\n"
            f"如果觉得有用，别忘了**点赞、在看、转发**，"
            f"让更多人看到这些干货 🙏",
        ]
        cta = random.choice(cta_list)

        # 组装全文
        full_parts = [intro]
        for sec in sections:
            full_parts.append(f"### {sec['title']}\n{sec['body']}")
        full_parts.append(cta)
        full_text = "\n\n".join(full_parts)

        return {
            "platform": "微信公众号",
            "title": title,
            "intro": intro,
            "sections": sections,
            "cta": cta,
            "full_text": full_text,
            "statistics": {
                "sections_count": num_sections,
                "word_count": len(full_text.replace(" ", "").replace("\n", "")),
                "target_word_count": word_count,
            },
        }

    @staticmethod
    def _generate_wechat_title(topic: str) -> str:
        """生成微信文章标题"""
        templates = [
            f"⎡干货⎦{topic}：这是我见过最{random.choice(['全面', '实用', '透彻', '靠谱'])}的指南",
            f"{topic}，看完我{random.choice(['沉默了', '后悔了', '悟了', '连夜整理'])}",
            f"为什么{topic}这么难？那是你没掌握{random.choice(['这个方法', '这个思维', '这个工具'])}",
            f"{random.choice(['2025最新', '超全', '保姆级'])} {topic}攻略，{random.choice(['建议收藏', '错过后悔', '值得N刷'])}",
            f"做{topic}{random.choice(['3年', '5年', '10年'])}，总结出{random.choice(['这5条', '这8条', '这些'])}经验",
        ]
        idx = hash(topic) % len(templates)
        return templates[idx]

    def generate_content_plan(self, topic: str, platforms: Optional[list[str]] = None, count: int = 5) -> list[dict]:
        """
        生成多平台内容矩阵规划

        Args:
            topic: 主题
            platforms: 目标平台列表（默认全平台）
            count: 内容数量

        Returns:
            list[dict]: 内容规划列表
        """
        if platforms is None:
            platforms = list(self.PLATFORM_TEMPLATES.keys())

        # 限平台到有效列表
        valid_platforms = [p for p in platforms if p in self.PLATFORM_TEMPLATES]

        if not valid_platforms:
            valid_platforms = ["小红书", "知乎"]

        # 内容形式池
        content_angles = [
            "入门指南", "深度解析", "避坑指南", "工具推荐",
            "案例分享", "进阶技巧", "行业趋势", "对比评测",
            "经验总结", "问题答疑", "资源合集", "实战记录",
        ]

        # 生成内容规划
        plans = []
        for i in range(count):
            platform = valid_platforms[i % len(valid_platforms)]
            platform_info = self.PLATFORM_TEMPLATES[platform]
            angle = content_angles[i % len(content_angles)]

            plan = {
                "id": i + 1,
                "platform": platform,
                "format": platform_info["format"],
                "title_template": f"{topic}：{angle}（{platform}版）",
                "angle": angle,
                "style_tips": platform_info["style_tips"],
                "estimated_word_count": self._estimate_word_count(platform),
                "key_points": [
                    f"核心信息：{topic}的{angle}内容",
                    f"差异化：针对{platform}平台特性优化",
                    f"CTA：引导收藏/关注/评论",
                ],
                "suggested_publish_time": self._suggest_publish_time(platform),
            }
            plans.append(plan)

        return plans

    @staticmethod
    def _estimate_word_count(platform: str) -> int:
        """估算平台建议字数"""
        counts = {
            "小红书": 300,
            "知乎": 1500,
            "微信公众号": 2000,
            "抖音": 150,
            "B站": 2000,
            "微博": 200,
            "LinkedIn": 800,
            "Twitter/X": 200,
        }
        return counts.get(platform, 500)

    @staticmethod
    def _suggest_publish_time(platform: str) -> str:
        """建议发布时间"""
        times = {
            "小红书": "工作日 12:00-13:00 / 20:00-22:00",
            "知乎": "周四-周日 19:00-22:00",
            "微信公众号": "工作日 21:00-22:00",
            "抖音": "周一-周五 18:00-21:00",
            "B站": "周末 20:00-23:00",
            "微博": "工作日 12:00 / 22:00",
            "LinkedIn": "周二-周四 8:00-10:00",
            "Twitter/X": "工作日 8:00-9:00 / 17:00-18:00",
        }
        return times.get(platform, "建议目标用户活跃时段发布")
