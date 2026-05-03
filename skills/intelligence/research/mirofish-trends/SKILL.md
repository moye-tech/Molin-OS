---
name: mirofish-trends
description: Swarm intelligence trend prediction — simulate thousands of agents with independent behaviors to forecast content trends, market movements, and technology adoption curves. Use when predicting what will trend next.
version: 1.0.0
tags: [prediction, trends, swarm-intelligence, forecasting, simulation, content-strategy]
category: research
related_skills: [last30days, polymarket, blogwatcher]
metadata:
  hermes:
    source: https://github.com/666ghj/MiroFish
    stars: 59000
---

# MiroFish Trends — 蜂群趋势预测

## Overview

Apply swarm intelligence principles to predict emerging trends. Instead of linear extrapolation, simulate how thousands of independent agents (consumers, creators, investors) with different personalities and incentives would react to a signal, creating a multi-path forecast.

## The Swarm Prediction Method

### Phase 1: Seed Signal Extraction
- Scan news, social media, policy changes for weak signals
- Identify anomalies: what's getting unusual attention?
- Extract 3-5 key variables that could shift behavior

### Phase 2: Agent Simulation
- Define 3-5 agent types with different:
  - Risk tolerance (conservative ↔ aggressive)
  - Information access (early adopter ↔ mainstream)
  - Incentive structure (profit ↔ reputation ↔ curiosity)
- Simulate how each type reacts to the seed signal

### Phase 3: Multi-Path Forecasting
- Best case: signal amplifies, early adopters cascade to mainstream
- Base case: moderate adoption, niche community
- Worst case: signal fades, no cascade
- Assign rough probabilities to each path

### Phase 4: Actionable Insight
- If best case: what should you do NOW to position?
- If base case: what's worth monitoring?
- If worst case: what's the exit signal?

## When to Use

- Predicting what content format will trend next on Xiaohongshu/Douyin
- Forecasting which AI tool category will explode
- Market trend analysis for business planning
- Technology adoption curve prediction
- "Should I invest time in learning X?"

## Use Cases for 一人公司

1. **Content trends**: "Will AI video tools be the next big Xiaohongshu trend?" → simulate creator adoption curve
2. **Service demand**: "Is demand for resume optimization rising or falling?" → simulate job market + AI awareness
3. **Platform shifts**: "Should I focus on Xiaohongshu or Douyin?" → simulate platform growth trajectories
4. **Pricing strategy**: "What price will the market bear for AI consulting?" → simulate buyer willingness

## Integration

- Combine with `last30days` for seed signal extraction
- Combine with `polymarket` for real-money probability calibration
- Use output to inform `xiaohongshu-content-engine` content calendar
