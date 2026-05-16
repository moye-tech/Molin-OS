# tts-taiwan · 台湾腔TTS配音
# 归属: Agent E (global)
## 触发词
触发词: 台湾腔|台语|台湾配音|繁体配音|出海配音
## 引擎选择
首选: fish-speech S2 Pro（ELO 1339，台湾腔支持优秀，¥15/百万字符）
备选: CosyVoice v3（阿里，18+方言，台湾普通话可用）
## 调用
pip install fish-audio-sdk
fish_audio.synthesize(text=content, voice="taiwan-female-01")
