"""molib.shared.finance — 成本监控与预算追踪

吸收自 phuryn/claude-usage (1.5K⭐)

核心模式：
1. UsageScanner: 扫描 JSONL 日志 → 提取 token/成本数据
2. CostTracker: 增量存储 + 成本估算
3. DashboardServer: 轻量 HTTP Dashboard (Chart.js)

零外部依赖，仅使用 Python 标准库 + Chart.js CDN。
"""

from .usage_scanner import UsageScanner, UsageRecord
from .cost_tracker import CostTracker, CostEstimate, BudgetReport

__all__ = [
    "UsageScanner", "UsageRecord",
    "CostTracker", "CostEstimate", "BudgetReport",
]
