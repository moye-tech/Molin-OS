---
name: pixelle-video
description: 'AI fully automated short video engine: Topic→Script→AI art→TTS→music→composite
  video pipeline.'
version: 1.0.0
author: Hermes Agent (based on AIDC-AI/Pixelle-Video)
license: MIT
metadata:
  hermes:
    tags:
    - video
    - automation
    - ai-art
    - tts
    - pipeline
    - content-creation
    - comfyui
    related_skills:
    - ffmpeg-video-engine
    - moneymaker-turbo
    category: creative
    money_printer_turbo:
      source: https://github.com/harry0703/MoneyPrinterTurbo
      stars: 57000
      upstream_fork: https://github.com/moye-tech/MoneyPrinterTurbo
      alternative_pipeline: true
      value: 提供 Pixelle 之外的完整中文短视频管线备选方案
    molin_owner: 墨影（IP孵化）
min_hermes_version: 0.13.0
---

# Pixelle-Video

## Overview

Pixelle-Video is an AI-powered fully automated short video production engine. It takes a topic or idea as input and produces a complete, publish-ready short video by chaining together AI-driven stages: script generation, AI image/art creation, text-to-speech narration, background music selection, and final video compositing.

The architecture follows a **ComfyUI-style modular pipeline** — each stage is an independent node that can be swapped, configured, or extended independently. The engine also supports **digital human broadcasting** for talking-head style videos.

**Core principle:** Topic in, video out. Every stage is AI-driven with configurable quality gates.

## When to Use

Use this skill when:
- Creating short-form video content (YouTube Shorts, TikTok, Instagram Reels, etc.)
- Automating content production at scale (batch video generation)
- Building AI-powered video pipelines for marketing, education, or entertainment
- Need a digital human / AI avatar to deliver scripted content
- Prototyping video concepts rapidly before manual production
- Setting up a hands-off content channel

**vs. manual video editing:**
- 100x faster turnaround (minutes vs. hours/days)
- Consistent output quality at scale
- No video editing expertise required
- Batch generation for A/B testing content variations
- Full reproducibility — regenerate identical video from the same seed

## The Pipeline

```
Topic/Idea
    │
    ▼
┌─────────────┐
│ 1. SCRIPT   │  LLM generates engaging short video script
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 2. AI ART   │  Stable Diffusion / ComfyUI creates scene visuals
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 3. TTS      │  Text-to-speech generates voiceover narration
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 4. MUSIC    │  AI music generation or curated royalty-free music
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 5. COMPOSITE│  FFmpeg/MoviePy assembles final video with timing
└──────┬──────┘
       │
       ▼
   Final Video
```

### Stage 1: Script Generation

Convert a topic/idea into a structured video script:

**Input:** Topic string, target duration (15s, 30s, 60s), tone, language, platform

**Process:**
1. LLM generates a hook (first 2-3 seconds to grab attention)
2. Core message / storyline with natural pacing
3. Call-to-action (CTA) tailored to the platform
4. Scene breaks annotated with visual descriptions for AI art stage
5. Word count optimized for target duration (roughly 2.5 words/second)

**Script structure:**
```yaml
script:
  title: "How AI is changing everything"
  duration_seconds: 30
  language: en
  scenes:
    - scene_id: 1
      narration: "Did you know AI can now create videos like this one?"
      visual_prompt: "Futuristic cityscape, neon lights, cyberpunk aesthetic, 4K"
      duration_seconds: 5
    - scene_id: 2
      narration: "In just seconds, from a single idea to a complete video."
      visual_prompt: "AI neural network visualization, glowing nodes, abstract"
      duration_seconds: 8
    - scene_id: 3
      narration: "Welcome to the future of content creation."
      visual_prompt: "Sleek modern studio, creative workspace, warm lighting"
      duration_seconds: 7
    - scene_id: 4
      narration: "Follow for more AI magic. ✨"
      visual_prompt: "Brand logo reveal, polished animation style"
      duration_seconds: 5
      cta: true
```

**Quality controls:**
- Hook strength score (0-10): does the opening grab attention?
- Pacing check: no scene exceeds 10 seconds without action
- Platform optimization: vertical (9:16) vs. horizontal (16:9)
- Readability: narration sounds natural when spoken aloud

### Stage 2: AI Art Generation

Generate visuals for each scene using Stable Diffusion / ComfyUI:

**Input:** Scene visual prompts from script, style guide, aspect ratio

**Process:**
1. Prompt enrichment: expand visual prompts with quality keywords and negative prompts
2. ComfyUI workflow execution:
   - Model selection (SDXL, Flux, etc.)
   - LoRA application for style consistency
   - ControlNet for pose/composition guidance
   - Upscaling to target resolution
3. Batch generation (multiple variants per scene for selection)
4. Quality scoring and best-variant selection

**ComfyUI modular node setup:**
```yaml
comfyui_workflow:
  model: "sdxl_base"
  loras:
    - "cinematic_lighting_v2"
    - "detailed_faces_v1"
  steps: 30
  cfg: 7.0
  width: 1080
  height: 1920  # 9:16 vertical
  upscale_factor: 1.5
  negative_prompt: "blurry, low quality, distorted, watermark, text"
```

**Style consistency techniques:**
- Shared seed across scenes (with small variations)
- Consistent LoRA stack
- Unified color palette via prompt guidance
- IP-Adapter for reference image styling

**Supported styles:** realistic, anime, 3D render, pixel art, cinematic, minimalist, sketch, watercolor

### Stage 3: Text-to-Speech (TTS)

Convert script narration to natural-sounding voiceover:

**Input:** Narration text per scene, voice profile, language

**Process:**
1. Voice profile selection (gender, age, accent, style)
2. SSML markup for emphasis, pauses, and intonation
3. Audio generation per scene
4. Silence padding for scene transitions
5. Speed adjustment to match scene duration

**Voice profiles:**
```yaml
voices:
  narrator_male:
    provider: "edge_tts"  # or elevenlabs, openai, bark
    voice_id: "en-US-GuyNeural"
    speed: 1.0
    pitch: 0
  narrator_female:
    provider: "edge_tts"
    voice_id: "en-US-JennyNeural"
    speed: 1.05
    pitch: 2
  digital_human:
    provider: "elevenlabs"
    voice_id: "cloned_voice_id"
    stability: 0.5
    similarity_boost: 0.75
```

**Digital human broadcasting:**
- Lip-sync generation (Wav2Lip or SadTalker)
- Avatar animation driven by audio waveform
- Background compositing with generated art
- Real-time or pre-rendered modes

### Stage 4: Music & Sound Design

Add background music and sound effects:

**Input:** Video mood/tone, duration, platform requirements

**Process:**
1. Mood classification from script (energetic, calm, dramatic, etc.)
2. AI music generation (MusicGen, Suno, etc.) or royalty-free library selection
3. Ducking: automatically lower music volume during narration
4. Sound effects for transitions and emphasis moments
5. Intro/outro stingers

**Audio mixing rules:**
- Background music: -18dB to -22dB during narration
- Sound effects: -12dB peaks
- Narration: -3dB to -6dB normalized
- Fade in/out: 0.5s for smooth transitions

### Stage 5: Video Compositing

Assemble all assets into final video:

**Input:** All generated assets (images, audio, music), timing script

**Process:**
1. Scene assembly with Ken Burns effect (subtle zoom/pan on still images)
2. Audio track mixing (narration + music + SFX)
3. Transitions between scenes (crossfade, slide, zoom)
4. Caption/subtitle overlay (auto-generated from TTS)
5. Brand watermark/logo placement
6. Export with platform-optimized encoding

**FFmpeg composition command template:**
```bash
ffmpeg \
  -loop 1 -i scene_1.png -i narration_1.wav -i bgm.mp3 \
  -filter_complex "\
    [0:v]zoompan=z='min(zoom+0.0015,1.5)':d=150:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',fade=t=out:st=4.5:d=0.5[v1]; \
    [1:a]volume=1.0[a1]; \
    [2:a]volume=0.15,afade=t=in:d=0.5,afade=t=out:st=28.5:d=1.5[bgm]; \
    [a1][bgm]amix=inputs=2:duration=first:dropout_transition=2[audio]
  " \
  -map "[v1]" -map "[audio]" \
  -c:v libx264 -preset medium -crf 23 \
  -c:a aac -b:a 128k \
  -t 30 -r 30 \
  output.mp4
```

## Digital Human Broadcasting

For talking-head style content with an AI avatar:

```
Script → TTS (voice) → Wav2Lip (lip sync) → Avatar render → Composite
```

**Setup:**
1. Choose or train a digital human avatar (pre-rendered or real-time)
2. Link TTS output to lip-sync model
3. Composite avatar onto generated background
4. Add gesture/posture variation for natural appearance

**Tools:** SadTalker, Wav2Lip, MuseTalk, HeyGen API

## Batch Generation Mode

For content at scale:

```yaml
batch_config:
  topics_file: "topics.csv"  # One topic per line
  variants_per_topic: 3      # A/B test variations
  platforms: [tiktok, youtube_shorts, instagram_reels]
  output_dir: "./output/2026-05-03-batch/"
  parallel_workers: 4
  quality_threshold: 0.7     # Auto-reject below this score
```

**Batch workflow:**
1. Load topic list
2. For each topic, generate N variants
3. Quality-score each variant
4. Reject below threshold, keep top candidates
5. Platform-specific rendering per variant
6. Generate metadata (titles, descriptions, hashtags, thumbnails)

## Quality Scoring

Auto-score generated videos on:
- **Visual quality (25%)**: image sharpness, aesthetic score, consistency
- **Audio quality (25%)**: voice clarity, music fit, mix balance
- **Engagement potential (30%)**: hook strength, pacing, CTA effectiveness
- **Technical quality (20%)**: encoding, resolution, captions accuracy

Scores below 0.7 trigger auto-rejection in batch mode.

## Platform-Specific Presets

| Platform | Aspect Ratio | Max Duration | Caption Style | CTA Style |
|----------|-------------|-------------|---------------|-----------|
| TikTok | 9:16 | 3 min | Bold center | Text + voice |
| YouTube Shorts | 9:16 | 60 sec | Bottom-safe zone | Subscribe |
| Instagram Reels | 9:16 | 90 sec | Clean overlay | Link in bio |
| YouTube | 16:9 | Unlimited | Optional CC | End cards |

## Quick Start

```python
from pixelle_video import Pipeline

# Single video
pipeline = Pipeline(
    style="cinematic",
    voice="narrator_male",
    platform="tiktok",
    duration=30
)

video = pipeline.generate("How AI is transforming healthcare")
pipeline.save(video, "output/healthcare_ai.mp4")
```

## Tips

- **Hook first:** Spend extra effort on the first 2-3 seconds — it determines retention
- **Style consistency:** Use the same LoRA/seed approach across all scenes
- **Voice matters:** Test different TTS voices for your audience; some convert better
- **Caption everything:** 85%+ of short-form video is watched without sound
- **Batch test:** Generate 3-5 variations of each topic and let analytics pick winners
- **Repurpose:** Extract the best-performing segments and re-compose into new videos