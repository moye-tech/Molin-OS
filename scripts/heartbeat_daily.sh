#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# 墨麟 Hermes OS — 每日心跳任务
# 调度: 每天 09:00
# 内容: 闲鱼状态检查 + 情报简报生成
# ═══════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="${HOME}/.molin/logs"
mkdir -p "${LOG_DIR}"

LOG_FILE="${LOG_DIR}/heartbeat_$(date +%Y%m%d).log"

{
    echo "════════════════════════════════════════"
    echo "  墨麟每日心跳 — $(date '+%Y-%m-%d %H:%M:%S')"
    echo "════════════════════════════════════════"
    echo ""

    cd "${REPO_DIR}"

    # 1. 健康检查
    echo "🩺 系统健康检查..."
    python3 -c "
from molin.core.engine import engine
import json
result = engine.health_check()
print(json.dumps(result, indent=2, ensure_ascii=False))
" 2>/dev/null || echo "  ⚠ 核心引擎未响应"

    echo ""

    # 2. 闲鱼店铺状态
    echo "🏪 闲鱼店铺状态..."
    python3 -c "
from molin.publish.xianyu import store
products = store.list_products()
stats = store.get_stats()
print(f'  商品总数: {stats[\"total_products\"]}')
print(f'  已发布: {stats[\"published\"]}')
print(f'  草稿: {stats[\"draft\"]}')
" 2>/dev/null || echo "  ⚠ 闲鱼模块未响应"

    echo ""

    # 3. 趋势简报
    echo "🔭 趋势简报..."
    python3 -c "
from molin.intelligence.trends import trends
result = trends.run()
for t in result.get('top_trends', []):
    print(f'  {t.get(\"momentum\", \"\")} {t.get(\"topic\", \"\")} — {t.get(\"relevance\", \"\")}')
if result.get('opportunities'):
    print(f'')
    print(f'  💡 机会发现:')
    for o in result['opportunities']:
        print(f'     • {o}')
" 2>/dev/null || echo "  ⚠ 趋势模块未响应"

    echo ""
    echo "════════════════════════════════════════"
    echo "  心跳完成 — $(date '+%H:%M:%S')"
    echo "════════════════════════════════════════"

} >> "${LOG_FILE}" 2>&1

echo "📝 日志: ${LOG_FILE}"

# Hermes Agent 集成说明:
# 此脚本可由 Hermes cronjob 调用，或直接添加系统 crontab:
#   0 9 * * * bash /path/to/cron/heartbeat_daily.sh
