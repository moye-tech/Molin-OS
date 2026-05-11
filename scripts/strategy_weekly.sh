#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# 墨麟 Hermes OS — 每周战略审查
# 调度: 每周一 10:00
# 内容: OKR 审查 + 方向调整 + 蜂群任务分配
# ═══════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="${HOME}/.molin/logs"
mkdir -p "${LOG_DIR}"

WEEK=$(date +%Y-W%V)
LOG_FILE="${LOG_DIR}/strategy_${WEEK}.log"

{
    echo "════════════════════════════════════════"
    echo "  墨麟周度战略审查 — ${WEEK}"
    echo "  时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "════════════════════════════════════════"
    echo ""

    cd "${REPO_DIR}"

    # 1. CEO 战略决策
    echo "🧠 CEO 战略分析..."
    python3 -c "
from molin.agents.ceo import ceo
result = ceo.run_strategy()
print(f'使命: {result[\"mission\"]}')
print(f'')
print('OKR 当前状态:')
for k, v in result['okr'].items():
    print(f'  {k}: {v}')
print(f'')
print('6路分析:')
for dept, analysis in result['analysis'].items():
    print(f'  [{dept}] {analysis}')
print(f'')
print('本周决策:')
for d in result.get('decisions', []):
    print(f'  P{d[\"priority\"]} | {d[\"decision\"]} | ¥{d[\"cost\"]} | {d[\"level\"]}')
" 2>/dev/null || echo "  ⚠ CEO 模块未响应"

    echo ""

    # 2. 自学习循环
    echo "🧬 自学习循环..."
    python3 -c "
from molin.agents.learner import learner
result = learner.run()
print(f'  周期: #{result[\"cycle\"]}')
for phase, data in result['phases'].items():
    print(f'  [{phase}] {list(data.keys())}')
" 2>/dev/null || echo "  ⚠ 自学习模块未响应"

    echo ""

    # 3. 技能库统计
    echo "📚 知识库统计..."
    SKILLS_COUNT=$(find "${REPO_DIR}/skills/" -name "SKILL.md" 2>/dev/null | wc -l)
    echo "  当前技能总数: ${SKILLS_COUNT}"
    for domain in meta content business engineering growth intelligence; do
        count=$(find "${REPO_DIR}/skills/${domain}/" -name "SKILL.md" 2>/dev/null | wc -l)
        echo "    ${domain}: ${count}"
    done

    echo ""
    echo "════════════════════════════════════════"
    echo "  战略审查完成 — $(date '+%H:%M:%S')"
    echo "════════════════════════════════════════"

} >> "${LOG_FILE}" 2>&1

echo "📝 日志: ${LOG_FILE}"

# Hermes Agent 集成说明:
# 此脚本可由 Hermes cronjob 调用，或直接添加系统 crontab:
#   0 10 * * 1 bash /path/to/cron/strategy_weekly.sh
