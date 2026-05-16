#!/bin/bash
# 用法: bash add_agent.sh  "<中文名>" "<飞书机器人名>"
# 示例: bash add_agent.sh ip "IP孵化线" "墨麟·IP孵化"
PROFILE="${1:?'缺少profile名'}"
CNAME="${2:?'缺少中文名'}"
BOTNAME="${3:-墨麟·$CNAME}"
MOLIN="$HOME/Molin-OS"

echo "🚀 新增Agent: $CNAME (profile: $PROFILE)"

# 1. 创建Profile
hermes profile create "$PROFILE" 2>/dev/null || true

# 2. 创建配置目录
mkdir -p "$MOLIN/config/$PROFILE" "$MOLIN/skills/$PROFILE" "$MOLIN/relay/$PROFILE"

# 3. 生成SOUL.md模板
cat > "$MOLIN/config/$PROFILE/SOUL_${PROFILE^^}.md" << SOULEOF
# 墨麟AI · ${CNAME}Agent · 核心身份框架
# Profile: ${PROFILE} · 飞书机器人: ${BOTNAME}

## 我是谁
[TODO: 描述这个Agent的定位和专长]

## 核心使命
[TODO: 这条业务线的核心价值是什么？]

## DARE决策协议
D-解构目标 / A-分析缺口 / R-智能编排 / E-超预期

## 记忆积累重点
[TODO: 这条业务线最有价值的经验是什么？]
SOULEOF

# 4. 生成cron模板
cat > "$MOLIN/config/$PROFILE/cron_jobs.yaml" << CRONEOF
# ${CNAME} · 定时任务配置
jobs:
  - id: ${PROFILE}_daily
    name: "${CNAME}每日简报"
    schedule: "28 9 * * 1-5"
    prompt: |
      [${CNAME}] 生成今日业务简报。
      [TODO: 完善简报内容]
    skills: [feishu-message-formatter]
    toolset: [file]
    delivery: feishu
    timeout_minutes: 5
CRONEOF

# 5. 配置API + 注入公共技能
set -a; source "$MOLIN/.env" 2>/dev/null || true; set +a
hermes -p "$PROFILE" config set DEEPSEEK_API_KEY "$DEEPSEEK_API_KEY"
hermes -p "$PROFILE" config set DASHSCOPE_API_KEY "$DASHSCOPE_API_KEY"
hermes -p "$PROFILE" config set MEMORY_BACKEND "sqlite"
bash "$MOLIN/scripts/deploy_all_profiles.sh" --only "$PROFILE" 2>/dev/null || true

echo ""
echo "✅ $CNAME 基础配置完成！"
echo "剩余手动步骤："
echo "  1. 完善 $MOLIN/config/$PROFILE/SOUL_${PROFILE^^}.md"
echo "  2. 在飞书创建机器人「${BOTNAME}」"
echo "  3. hermes -p $PROFILE gateway setup --platform feishu --app-id  --app-secret  --mode websocket"
echo "  4. hermes -p $PROFILE gateway start --daemon"
