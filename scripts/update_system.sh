#!/bin/bash
# 墨麟OS · 全系统更新（三个独立仓库各自更新，互不影响）
echo "🔄 开始更新墨麟OS..."

echo "① 更新Hermes官方代码（Profile数据完全不动）..."
hermes update && echo "  ✅ Hermes: $(hermes --version)"

echo "② 更新Molin-OS仓库..."
cd ~/Molin-OS && git pull origin main && echo "  ✅ Molin-OS: $(git log --oneline -1)"

echo "③ 重新部署所有Profile（SOUL/技能/Cron更新生效）..."
bash ~/Molin-OS/scripts/deploy_all_profiles.sh

echo "④ 重启所有Agent..."
bash ~/Molin-OS/scripts/stop_all.sh
sleep 3
bash ~/Molin-OS/scripts/start_all.sh

echo "✅ 全系统更新完成！"
