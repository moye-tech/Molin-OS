"""
墨麟AIOS — VideoScriptTool
短视频/长视频脚本生成与场景提取工具
参考吸收: Pixelle-Video (8步视频Pipeline: 脚本→语音→场景→渲染→字幕→合成→Shorts→发布)
"""

import re
import random
from typing import Any


class VideoScriptTool:
    """视频脚本创作与场景提取工具"""

    # 短视频时间结构（秒）
    SHORT_VIDEO_STRUCTURE = [
        ("钩子开场", 3, "hook"),
        ("主线展开", 10, "main"),
        ("案例/数据", 15, "case"),
        ("价值输出", 20, "value"),
        ("CTA结尾", 12, "cta"),
    ]

    # 长视频时间结构（秒）
    LONG_VIDEO_STRUCTURE = [
        ("开场Hook", 30),
        ("痛点共鸣", 60),
        ("核心方法论", 120),
        ("案例拆解", 90),
        ("数据支撑", 60),
        ("避坑指南", 60),
        ("实操演示", 90),
        ("价值总结", 60),
        ("CTA + 下期预告", 30),
    ]

    # 转场建议库
    TRANSITIONS = [
        "闪白过渡",
        "滑动转场",
        "缩放推进",
        "旋转切换",
        "抖动过渡",
        "淡入淡出",
        "推拉镜头",
        "划像转场",
        "动态模糊过渡",
        "分屏拼接",
    ]

    # BGM风格库
    BGM_STYLES = {
        "知识/教程": [
            {"style": "轻快电子", "bpm": 110, "mood": "专注"},
            {"style": "LoFi HipHop", "bpm": 85, "mood": "放松学习"},
            {"style": "钢琴背景", "bpm": 70, "mood": "沉稳"},
        ],
        "娱乐/搞笑": [
            {"style": "Funk/Disco", "bpm": 120, "mood": "欢乐"},
            {"style": "电子舞曲", "bpm": 128, "mood": "活力"},
            {"style": "滑稽音效为主", "bpm": 90, "mood": "轻松"},
        ],
        "情感/生活": [
            {"style": "原声吉他", "bpm": 75, "mood": "温馨"},
            {"style": "钢琴+弦乐", "bpm": 65, "mood": "感人"},
            {"style": "轻流行", "bpm": 95, "mood": "治愈"},
        ],
        "科技/数码": [
            {"style": "电子合成器", "bpm": 115, "mood": "科技感"},
            {"style": "Ambient", "bpm": 70, "mood": "未来感"},
            {"style": "Dubstep过渡", "bpm": 140, "mood": "高潮"},
        ],
        "默认": [
            {"style": "流行背景", "bpm": 100, "mood": "通用"},
            {"style": "轻量打击乐", "bpm": 95, "mood": "节奏感"},
        ],
    }

    # 平台短视频参数
    PLATFORM_PARAMS = {
        "抖音": {"aspect_ratio": "9:16", "resolution": "1080×1920", "max_duration": 180},
        "快手": {"aspect_ratio": "9:16", "resolution": "1080×1920", "max_duration": 120},
        "视频号": {"aspect_ratio": "9:16", "resolution": "1080×1920", "max_duration": 300},
        "YouTube Shorts": {"aspect_ratio": "9:16", "resolution": "1080×1920", "max_duration": 60},
        "Instagram Reels": {"aspect_ratio": "9:16", "resolution": "1080×1920", "max_duration": 90},
        "B站": {"aspect_ratio": "16:9", "resolution": "1920×1080", "max_duration": 600},
    }

    @staticmethod
    def _compute_time_segments(duration: int) -> list[dict]:
        """
        根据总时长动态计算各段落时间分配（秒）
        保证钩子3秒固定，其余按比例扩展
        """
        if duration <= 10:
            return [{"name": "完整视频", "start": 0, "end": duration, "duration": duration, "type": "all"}]

        # 基础结构（5段）
        base_structure = [
            ("钩子开场", 0.05, "hook"),
            ("主线展开", 0.18, "main"),
            ("案例/数据", 0.25, "case"),
            ("价值输出", 0.32, "value"),
            ("CTA结尾", 0.20, "cta"),
        ]

        segments = []
        current = 0.0
        for i, (name, ratio, seg_type) in enumerate(base_structure):
            if i == len(base_structure) - 1:
                # 最后一段取剩余时间
                seg_duration = duration - current
            else:
                seg_duration = max(2, round(duration * ratio))

            seg_type_name = seg_type if seg_type != "all" else "all"
            segments.append({
                "name": name,
                "start": round(current, 1),
                "end": round(current + seg_duration, 1),
                "duration": round(seg_duration, 1),
                "type": seg_type_name,
            })
            current += seg_duration

        # 调整最后一秒对齐
        diff = duration - segments[-1]["end"]
        if abs(diff) > 0.1:
            segments[-1]["end"] = duration
            segments[-1]["duration"] = round(segments[-1]["end"] - segments[-1]["start"], 1)

        return segments

    @staticmethod
    def _generate_short_content(topic: str, segments: list[dict], platform: str) -> list[dict]:
        """生成短视频各段落的内容"""
        contents = []

        hook_templates = [
            f"你敢信？{topic}居然可以这样！",
            f"直到今天我才发现，{topic}的真相是……",
            f"如果你正在做{topic}，请务必看完这{segments[-1]['duration']:.0f}秒",
            f"别再{random.choice(['瞎折腾', '走弯路了', '浪费时间'])}了！{topic}其实很简单",
            f"90%的人都不知道的{topic}秘密，今天全盘托出",
        ]

        main_templates = [
            f"今天要聊的{topic}，核心逻辑其实只有{random.choice(['3步', '2个关键', '一句话'])}。\n"
            f"第一，{random.choice(['搞清楚本质', '找到需求', '明确目标'])}；\n"
            f"第二，{random.choice(['选对方法', '用对工具', '找对方向'])}；\n"
            f"第三，{random.choice(['持续执行', '不断迭代', '坚持做下去'])}。",

            f"关于{topic}，我们先来看{random.choice(['一个数据', '一个事实', '一个现象'])}——\n"
            f"{random.choice(['70%的人', '大多数从业者', '很多新手'])}在{topic}上都会犯同样的错误："
            f"{random.choice(['方法不对', '认知不足', '坚持不够'])}。",
        ]

        case_templates = [
            f"给你分享一个真实案例。\n"
            f"我之前有一个{random.choice(['学员', '朋友', '客户'])}，"
            f"在尝试{topic}之前{random.choice(['毫无头绪', '屡屡碰壁', '效果很差'])}。\n"
            f"后来他用了这个方法，{random.choice(['效果提升了3倍', '一个月就见到成效', '轻松拿下目标'])}。",

            f"来看一组数据：\n"
            f"📊 使用{topic}方法后，{random.choice(['效率提升80%', '成本降低50%', '用户增长200%'])}\n"
            f"📊 {random.choice(['90%的用户反馈', '行业数据显示', '实践证明'])}这个方法确实有效。",
        ]

        value_templates = [
            f"重点来了！{topic}最核心的价值在于——\n"
            f"{random.choice(['认知升级', '效率革命', '方法创新', '思维转变'])}。\n"
            f"掌握了这个，你在{topic}上就能{random.choice(['碾压90%的人', '轻松超越同行', '领先一大步'])}。",

            f"干货时间到！{topic}需要掌握的{random.choice(['3个关键技能', '5个核心要点', '2个底层逻辑'])}：\n"
            f"🔑 {random.choice(['持续输入', '深度思考', '高效执行'])}\n"
            f"🔑 {random.choice(['迭代优化', '用户思维', '数据驱动'])}\n"
            f"🔑 {random.choice(['长期主义', '跨界融合', '系统思维'])}",
        ]

        cta_templates = [
            f"看完记得{random.choice(['点赞收藏', '关注我', '转发给需要的人'])}，"
            f"下次继续分享{topic}的更多干货！",
            f"如果你对{topic}还有疑问，欢迎在评论区留言～"
            f"我会一一回复！",
            f"关注我，下期带你看{topic}的{random.choice(['进阶玩法', '高阶技巧', '完整教程'])}！",
        ]

        content_funcs = {
            "hook": hook_templates,
            "main": main_templates,
            "case": case_templates,
            "value": value_templates,
            "cta": cta_templates,
        }

        # 镜头方向建议
        shot_types = [
            "特写镜头",
            "中景镜头",
            "远景镜头",
            "俯拍镜头",
            "跟拍镜头",
            "自拍视角",
            "屏幕录制",
            "AI生成画面",
            "实景拍摄",
            "产品特写",
        ]

        for seg in segments:
            seg_type = seg["type"]
            templates = content_funcs.get(seg_type, main_templates)
            idx = hash(topic + seg_type) % len(templates)
            text = templates[idx]

            # 为每个段落生成分镜头
            num_shots = max(1, round(seg["duration"] / 5))  # 每5秒一个镜头

            shots = []
            for s in range(num_shots):
                shot_type = shot_types[(hash(topic + str(s)) % len(shot_types))]
                shots.append({
                    "shot": s + 1,
                    "type": shot_type,
                    "description": f"{shot_type} - {seg['name']} 第{s+1}镜",
                    "estimated_duration": round(seg["duration"] / num_shots, 1),
                    "text_overlay": text[:50] if s == 0 else "",
                })

            contents.append({
                "segment": seg["name"],
                "type": seg_type,
                "start_time": seg["start"],
                "end_time": seg["end"],
                "duration": seg["duration"],
                "speech_text": text,
                "shots": shots,
                "visual_note": f"{seg['name']}阶段，建议使用{random.choice(shot_types)}突出{seg_type}信息",
            })

        return contents

    @staticmethod
    def _generate_subtitle_timeline(contents: list[dict]) -> list[dict]:
        """生成字幕时间轴"""
        subtitles = []
        for content in contents:
            text = content["speech_text"]
            # 按句分割
            sentences = re.split(r"[。！？\n]", text)
            sentences = [s.strip() for s in sentences if s.strip()]
            if not sentences:
                sentences = [text[:30]]

            # 分配时间
            segment_duration = content["duration"]
            per_sentence = segment_duration / max(len(sentences), 1)

            for i, sent in enumerate(sentences):
                start = content["start_time"] + i * per_sentence
                end = start + min(per_sentence, len(sent) * 0.25)  # 平均每秒4个字
                subtitles.append({
                    "start": round(start, 1),
                    "end": round(min(end, content["end_time"]), 1),
                    "text": sent[:80],  # 每行字幕最多80字
                })

        return subtitles

    def short_video(self, topic: str, duration: int = 60, platform: str = "抖音") -> dict:
        """
        生成短视频脚本（参考Pixelle-Video结构）

        Args:
            topic: 视频主题
            duration: 视频时长（秒，默认60）
            platform: 目标平台

        Returns:
            dict: 完整的短视频脚本（结构、分镜、BGM、字幕、转场）
        """
        # 平台参数适配
        if platform not in self.PLATFORM_PARAMS:
            platform = "抖音"
        platform_info = self.PLATFORM_PARAMS[platform]

        # 限制时长不超过平台最大时长
        max_duration = platform_info["max_duration"]
        duration = min(duration, max_duration)

        # 计算时间分段
        segments = self._compute_time_segments(duration)

        # 生成内容
        contents = self._generate_short_content(topic, segments, platform)

        # 生成字幕时间轴
        subtitles = self._generate_subtitle_timeline(contents)

        # BGM建议
        bgm = self._suggest_bgm(topic)

        # 转场建议
        transition_list = random.sample(self.TRANSITIONS, min(len(self.TRANSITIONS), 3))

        # 提取所有分镜头
        all_shots = []
        for c in contents:
            all_shots.extend(c["shots"])

        # 语音时长建议（语速约3字/秒）
        total_text = " ".join(c["speech_text"] for c in contents)
        estimated_speech_duration = round(len(total_text) / 3)  # 3字/秒

        return {
            "platform": platform,
            "topic": topic,
            "total_duration": duration,
            "aspect_ratio": platform_info["aspect_ratio"],
            "resolution": platform_info["resolution"],
            "estimated_speech_duration": estimated_speech_duration,
            "structure_summary": [
                {
                    "name": s["name"],
                    "duration": s["duration"],
                    "type": s["type"],
                    "percentage": f"{s['duration'] / duration * 100:.0f}%",
                }
                for s in segments
            ],
            "segments": contents,
            "subtitles": subtitles,
            "bgm_suggestions": bgm,
            "transitions": transition_list,
            "all_shots": all_shots,
            "thumbnail_suggestion": {
                "composition": f"{topic}核心{random.choice(['画面', '数据', '效果'])} + 大字标题",
                "text_overlay": random.choice([f"3秒看懂{topic}", f"{topic}真相", f"{topic}最强攻略"]),
                "color_scheme": random.choice(["高对比（红+白）", "科技蓝+渐变", "暖色调+自然光", "黑白极简"]),
            },
        }

    def long_video(self, topic: str, duration: int = 300) -> dict:
        """
        生成15-20分钟长视频脚本骨架

        Args:
            topic: 视频主题
            duration: 视频时长（秒，默认300=5分钟，实际可用于15-20min）

        Returns:
            dict: 长视频脚本骨架
        """
        # 长视频结构（9段）
        long_structure = [
            ("开场Hook", 0.08, "hook"),
            ("痛点共鸣", 0.10, "pain"),
            ("核心方法论", 0.20, "method"),
            ("案例拆解", 0.15, "case"),
            ("数据支撑", 0.10, "data"),
            ("避坑指南", 0.10, "pitfall"),
            ("实操演示", 0.15, "practice"),
            ("价值总结", 0.08, "summary"),
            ("CTA + 下期预告", 0.04, "cta"),
        ]

        segments = []
        current = 0.0
        for i, (name, ratio, seg_type) in enumerate(long_structure):
            if i == len(long_structure) - 1:
                seg_duration = duration - current
            else:
                seg_duration = max(5, round(duration * ratio))

            segments.append({
                "name": name,
                "type": seg_type,
                "start": round(current, 1),
                "end": round(current + seg_duration, 1),
                "duration": round(seg_duration, 1),
            })
            current += seg_duration

        # 对齐
        segments[-1]["end"] = duration
        segments[-1]["duration"] = round(segments[-1]["end"] - segments[-1]["start"], 1)

        # 为每个段落生成详细内容
        detailed_segments = []
        for seg in segments:
            content = self._generate_long_segment_content(seg, topic)
            detailed_segments.append(content)

        # BGM建议
        bgm = self._suggest_bgm(topic)

        # 转场序列
        transition_plan = []
        for i in range(len(segments) - 1):
            transition_plan.append({
                "from": segments[i]["name"],
                "to": segments[i + 1]["name"],
                "transition": random.choice(self.TRANSITIONS),
                "duration": 0.5,
            })

        # 章节时间戳
        chapters = [
            {
                "chapter": i + 1,
                "title": seg["name"],
                "start_time": seg["start"],
                "end_time": seg["end"],
            }
            for i, seg in enumerate(segments)
        ]

        return {
            "topic": topic,
            "total_duration": duration,
            "format": "长视频/中视频",
            "chapters": chapters,
            "segments": detailed_segments,
            "transition_plan": transition_plan,
            "bgm_suggestions": bgm,
            "aspect_ratio": "16:9",
            "resolution": "1920×1080",
            "guidelines": [
                "前30秒必须抓住观众注意力",
                "每3-5分钟设置一个小高潮/反转",
                "数据/案例交替出现避免枯燥",
                "每章结尾设置悬念引导继续观看",
                "评论区置顶核心观点+时间戳目录",
            ],
            "estimated_word_count": round(duration * 3.5),  # 长视频语速稍慢
        }

    @staticmethod
    def _generate_long_segment_content(seg: dict, topic: str) -> dict:
        """生成长视频段落内容"""
        content_templates = {
            "hook": [
                f"今天我们来深入聊聊{topic}这个话题。",
                f"你可能看过很多关于{topic}的内容，但今天这个角度你一定没见过。",
                f"大家好，欢迎来到本期视频。今天要讲的是一个很多人都误解的话题——{topic}。",
            ],
            "pain": [
                f"在做{topic}的过程中，大多数人都会遇到这几个问题：\n"
                f"1. 无从下手，不知道从哪里开始\n"
                f"2. 方法不对，努力白费\n"
                f"3. 坚持不下去，三天打鱼两天晒网",
                f"说实话，{topic}确实不容易。我自己也走过很多弯路……",
            ],
            "method": [
                f"经过长期的实践和总结，我把{topic}的核心方法论归纳为以下{random.choice(['3步', '5个阶段', '一个框架'])}：\n"
                f"第一步：{random.choice(['认知建立', '信息搜集', '目标设定'])}\n"
                f"第二步：{random.choice(['方案制定', '方法选择', '路径规划'])}\n"
                f"第三步：{random.choice(['执行落地', '持续迭代', '复盘优化'])}",
            ],
            "case": [
                f"来看一个真实的案例。\n"
                f"某{random.choice(['初创公司', '个人博主', '传统企业'])}在应用{topic}方法后，"
                f"{random.choice(['3个月内用户增长5倍', '半年内营收翻番', '效率提升300%'])}。\n"
                f"他们做对了什么？主要有这{random.choice(['3点', '2个关键决策', '一个核心差异'])}……",
            ],
            "data": [
                f"根据{random.choice(['行业报告', '市场调研', '权威数据'])}显示：\n"
                f"📊 {random.choice(['78%的企业', '65%的用户', '90%的从业者'])}认为{topic}至关重要\n"
                f"📊 {random.choice(['采用该方法后效率提升40%', '市场年增长率达25%', '用户满意度提高60%'])}",
            ],
            "pitfall": [
                f"在{topic}实践中，这{random.choice(['3个', '5个', '几个'])}坑一定要注意避开：\n"
                f"❌ {random.choice(['贪多求快', '方法生搬硬套', '忽视基础'])}\n"
                f"✅ 正确的做法是{random.choice(['循序渐进', '因地制宜', '打好基础'])}",
            ],
            "practice": [
                f"接下来我给大家实操演示一下{topic}的具体步骤。\n"
                f"打开{random.choice(['这个工具', '这个平台', '这个界面'])}，首先……\n"
                f"注意看这里的设置选项……\n"
                f"这样操作之后，效果立竿见影。",
            ],
            "summary": [
                f"好了，我们来总结一下本期视频的核心内容：\n"
                f"1. {topic}的本质是{random.choice(['认知升级', '效率提升', '方法优化'])}\n"
                f"2. 核心方法：{random.choice(['三步法', '五步框架', '系统思维'])}\n"
                f"3. 关键成功因素：{random.choice(['坚持+方法', '正确方向+持续投入', '认知+执行'])}",
            ],
            "cta": [
                f"以上就是关于{topic}的全部内容。如果你觉得有收获，"
                f"请**点赞、投币、收藏**，这对我非常重要！\n"
                f"下期视频我们来讲{random.choice(['进阶玩法', '更多案例', '行业趋势'])}，敬请期待！\n"
                f"有什么问题欢迎在评论区留言，我会一一回复～",
            ],
        }

        seg_type = seg["type"]
        templates = content_templates.get(seg_type, content_templates["hook"])
        idx = hash(topic + seg["name"]) % len(templates)
        text = templates[idx]

        # 视觉建议
        visual_suggestions = {
            "hook": "主播直面镜头 + 背景大标题",
            "pain": "痛点场景画面 + 暗调滤镜",
            "method": "思维导图/流程图动画",
            "case": "案例数据可视化 + 前后对比图",
            "data": "图表动画 + 数据标注",
            "pitfall": "红色警示标识 + 错误/正确对比",
            "practice": "屏幕录制/实操画面 + 步骤标注",
            "summary": "核心要点弹窗 + 思维导图收束",
            "cta": "主播直面镜头 + 关注按钮动效",
        }

        return {
            "segment_name": seg["name"],
            "type": seg_type,
            "start": seg["start"],
            "end": seg["end"],
            "duration": seg["duration"],
            "speech_text": text,
            "visual_suggestion": visual_suggestions.get(seg_type, "常规画面"),
            "key_message": text[:60] + "…" if len(text) > 60 else text,
        }

    @staticmethod
    def _suggest_bgm(topic: str) -> list[dict]:
        """根据主题推荐BGM"""
        topic_lower = topic.lower()

        # 基于关键词判断内容风格
        if any(kw in topic_lower for kw in ["知识", "教程", "学习", "课程", "教育", "课堂"]):
            style_key = "知识/教程"
        elif any(kw in topic_lower for kw in ["搞笑", "娱乐", "段子", "幽默", "趣味"]):
            style_key = "娱乐/搞笑"
        elif any(kw in topic_lower for kw in ["情感", "生活", "Vlog", "日常", "治愈"]):
            style_key = "情感/生活"
        elif any(kw in topic_lower for kw in ["科技", "数码", "AI", "编程", "代码", "互联网"]):
            style_key = "科技/数码"
        else:
            style_key = "默认"

        suggestions = VideoScriptTool.BGM_STYLES.get(style_key, VideoScriptTool.BGM_STYLES["默认"])

        # 添加过渡点建议
        result = []
        for s in suggestions:
            result.append({
                **s,
                "scene_suggestion": f"建议{style_key}风格在前30秒使用{s['style']}",
            })

        return result

    def extract_scenes(self, script: dict) -> list[dict]:
        """
        从脚本中提取关键帧描述（给AI绘图用）

        Args:
            script: short_video() 或 long_video() 返回的脚本dict

        Returns:
            list[dict]: 关键帧描述列表，每帧包含画面描述、风格、构图信息
        """
        scenes: list[dict] = []

        # 检查脚本类型
        if "segments" not in script:
            return scenes

        segments = script["segments"]
        topic = script.get("topic", "未知主题")

        # 视觉风格库
        visual_styles = [
            "写实摄影风格",
            "卡通插画风格",
            "3D渲染风格",
            "赛博朋克风格",
            "极简扁平风格",
            "水彩手绘风格",
            "电影胶片风格",
            "日系动漫风格",
        ]

        # 构图方式
        compositions = [
            "居中构图",
            "三分法构图",
            "对角线构图",
            "框架构图",
            "引导线构图",
            "对称构图",
            "留白构图",
            "黄金螺旋构图",
        ]

        # 颜色基调
        color_palettes = [
            "暖色调（橙黄为主）",
            "冷色调（蓝紫为主）",
            "高饱和对比色",
            "低饱和莫兰迪色",
            "黑白灰极简",
            "霓虹渐变色",
            "自然光真实色彩",
            "复古胶片暖色",
        ]

        for seg in segments:
            seg_name = seg.get("segment", seg.get("segment_name", "未知段落"))
            seg_type = seg.get("type", "general")
            text = seg.get("speech_text", "")
            shots = seg.get("shots", None)

            if shots:
                # 从shots中提取场景
                for shot in shots:
                    scene = {
                        "scene_id": len(scenes) + 1,
                        "segment": seg_name,
                        "segment_type": seg_type,
                        "description": shot.get("description", f"{topic}相关画面"),
                        "shot_type": shot.get("type", "中景镜头"),
                        "visual_style": visual_styles[len(scenes) % len(visual_styles)],
                        "composition": compositions[len(scenes) % len(compositions)],
                        "color_palette": color_palettes[len(scenes) % len(color_palettes)],
                        "text_overlay": shot.get("text_overlay", ""),
                        "estimated_duration": shot.get("estimated_duration", 5),
                        "ai_prompt": self._build_ai_prompt(
                            topic=topic,
                            segment=seg_name,
                            description=shot.get("description", ""),
                            style=visual_styles[len(scenes) % len(visual_styles)],
                            composition=compositions[len(scenes) % len(compositions)],
                        ),
                    }
                    scenes.append(scene)
            else:
                # 没有分镜头数据，按段落提取
                visual_suggestion = seg.get("visual_suggestion", "常规画面")
                scene = {
                    "scene_id": len(scenes) + 1,
                    "segment": seg_name,
                    "segment_type": seg_type,
                    "description": f"{topic} - {seg_name}",
                    "visual_suggestion": visual_suggestion,
                    "key_text": text[:100] if text else "",
                    "visual_style": visual_styles[len(scenes) % len(visual_styles)],
                    "composition": compositions[len(scenes) % len(compositions)],
                    "color_palette": color_palettes[len(scenes) % len(color_palettes)],
                    "estimated_duration": seg.get("duration", 10),
                    "ai_prompt": self._build_ai_prompt(
                        topic=topic,
                        segment=seg_name,
                        description=visual_suggestion,
                        style=visual_styles[len(scenes) % len(visual_styles)],
                        composition=compositions[len(scenes) % len(compositions)],
                    ),
                }
                scenes.append(scene)

        return scenes

    @staticmethod
    def _build_ai_prompt(
        topic: str,
        segment: str,
        description: str,
        style: str,
        composition: str,
    ) -> str:
        """构建AI绘图提示词"""
        prompt = (
            f"A {style} scene about {topic}, "
            f"focusing on {segment} moment. "
            f"{description}, "
            f"using {composition}, "
            f"high quality, detailed, 4K, cinematic lighting"
        )
        return prompt
