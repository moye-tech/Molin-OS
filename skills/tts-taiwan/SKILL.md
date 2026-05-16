# tts-taiwan · 台湾腔TTS配音
# 归属: Agent E (global) 独占 · 版本: v1.0

## 技能身份
为出海内容生成台湾腔普通话配音。
使用fish-speech/CosyVoice等引擎。

## 触发词
触发词: 台湾腔|台语|台湾配音|繁体配音|出海配音
触发词: 配音|语音合成|台湾语音

## 引擎选择
首选: fish-speech（台湾腔支持优秀，¥15/百万字符）
备选: CosyVoice（阿里达摩院，18+方言，台湾普通话可用）

## 调用方式
```python
# fish-speech 调用示例
from fish_audio_sdk import FishAudioSDK
client = FishAudioSDK(api_key="...")
result = client.synthesize(text="内容", voice="taiwan-female-01")
```

## 适配场景
- 视频配音（配合 ffmpeg-video-engine 生成口播视频）
- 音频课程（教育出海，台湾用户偏好音频学习）
- 广告配音（Shopee商品推广音频）

## 当前经验规则（动态更新）
- 台湾用户偏好女声，语速比大陆慢15%
- 「喔」「唷」「欸」等语气词增加亲切感
