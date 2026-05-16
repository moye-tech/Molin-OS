# video-script-engine · 短视频脚本引擎
# 归属: Agent A (media) · 版本: v1.0

## 触发词
触发词: 视频脚本|抖音|视频号|口播|分镜|短视频
触发词: 视频大纲|开头钩子|视频结构

## 调用格式
INPUT: { "topic": "主题", "duration_sec": 60, "platform": "douyin|shipinhao|bilibili", "style": "口播|图文混剪|vlog" }
OUTPUT: { "hook": "开头钩子（前3秒）", "structure": ["分镜×N"], "script": "完整台词", "bgm_mood": "音乐氛围建议", "cover_concept": "封面概念" }

## 视频黄金结构（Hook-Story-CTA）
- 0-3秒 Hook: 数字/反差/问题/悬念（决定完播率）
- 4-50秒 Story: 核心内容（每10秒一个节奏点）
- 最后5秒 CTA: 关注/评论/收藏引导（具体动作）

## 平台差异
抖音: 完播率第一，节奏快，BGM重要
视频号: 可稍慢，注重真实感，转发>完播
B站: 可长，知识点密度高，弹幕互动

## 数字人适配说明
生成脚本后，调用MuseTalk/CosyVoice制作数字人口播
台词需要：短句为主（≤15字/句）、无需屏幕显示的内容
