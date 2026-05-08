#!/usr/bin/env python3.12
"""
墨域私域沉淀 · 每日运营报告 v1.0

功能：
- 读取 CRM 数据（买家分层/触达日志/沉睡唤醒/转介绍）
- 生成格式化的运营报告
- 输出至 relay/crm_daily_report.md（飞书适配格式）

数据源：~/.hermes/crm/
输出格式：飞书消息格式（纯文本段落、•列表、表情分节）

子公司参与：墨域私域(数据采集) → 墨笔文创(报告润色)
时区：北京时间 (UTC+8)
"""

import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

# ── 路径 ───────────────────────────────────────────
CRM_DIR = Path.home() / ".hermes" / "crm"
RELAY_DIR = Path.home() / "hermes-os" / "relay"
RELAY_DIR.mkdir(parents=True, exist_ok=True)

BUYERS_FILE = CRM_DIR / "buyers.json"
TOUCH_FILE = CRM_DIR / "touch_log.json"
REFERRAL_FILE = CRM_DIR / "referral.json"
LOG_FILE = CRM_DIR / "crm_daily_report.log"

# ── 日服常量 ───────────────────────────────────────
DAYS_THRESHOLD_DORMANT = 30    # 超过30天未复购→沉睡
WEEKLY_NEW_CUSTOMERS = 0       # 本周新增（由闲鱼等来源填充）
MONTHLY_REVENUE_TARGET = 52000
TODAY = datetime.now().strftime("%Y-%m-%d")
TODAY_CN = f"{datetime.now().month}月{datetime.now().day}日"

# ── 日志 ───────────────────────────────────────────

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [CRM-REPORT] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# ── 数据加载 ──────────────────────────────────────

def load_json(path, default=None):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except:
            return default or {}
    return default or {}

# ── 指标计算 ──────────────────────────────────────

def calc_crm_metrics():
    """计算CRM核心运营指标"""
    buyers = load_json(BUYERS_FILE, {})
    touches = load_json(TOUCH_FILE, {})
    referral = load_json(REFERRAL_FILE, {})

    # 1. 买家总数与分层
    total_buyers = len(buyers)
    segments = {"high": 0, "medium": 0, "low": 0}
    total_revenue = 0.0
    total_orders = 0
    dormant_count = 0
    today_new = 0
    this_week_new = 0
    now_ts = time.time()
    week_start = now_ts - 7 * 86400

    for uid, info in buyers.items():
        seg = info.get("segment", "low")
        segments[seg] = segments.get(seg, 0) + 1
        total_revenue += info.get("total_spent", 0)
        total_orders += info.get("order_count", 0)

        # 沉睡检测
        last_str = info.get("last_order", "")
        if last_str:
            try:
                last_ts = time.mktime(time.strptime(last_str, "%Y-%m-%d"))
                days_since = (now_ts - last_ts) / 86400
                if days_since >= DAYS_THRESHOLD_DORMANT:
                    dormant_count += 1
                if days_since <= 1:
                    today_new += 1
                if days_since <= 7:
                    this_week_new += 1
            except:
                pass

    # 2. 触达执行情况
    total_planned = 0
    total_sent = 0
    for uid, record in touches.items():
        plan = record.get("plan", [])
        total_planned += len(plan)
        for entry in plan:
            if entry.get("sent"):
                total_sent += 1

    # 3. 转介绍数据
    referrers = referral.get("referrers", {})
    total_referrers = len(referrers)
    total_invited = sum(len(r.get("invited", [])) for r in referrers.values())
    total_points = sum(r.get("points", 0) for r in referrers.values())

    # 4. 唤醒数据
    reng_file = CRM_DIR / "re_engagement_latest.json"
    reng_data = load_json(reng_file, [])
    pending_wakeup = len([r for r in reng_data if r.get("days_since", 0) >= DAYS_THRESHOLD_DORMANT])

    # 5. 复购率（有过2次及以上订单的 / 总买家）
    repeat_count = sum(1 for info in buyers.values() if info.get("order_count", 0) >= 2)
    repeat_rate = round(repeat_count / total_buyers * 100, 1) if total_buyers > 0 else 0

    # 6. ARPU
    arpu = round(total_revenue / total_buyers, 1) if total_buyers > 0 else 0

    return {
        "total_buyers": total_buyers,
        "segments": segments,
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "repeat_count": repeat_count,
        "repeat_rate": repeat_rate,
        "arpu": arpu,
        "dormant_count": dormant_count,
        "today_new": today_new,
        "this_week_new": this_week_new,
        "total_planned_touches": total_planned,
        "total_sent_touches": total_sent,
        "total_referrers": total_referrers,
        "total_invited": total_invited,
        "total_points": total_points,
        "pending_wakeup": pending_wakeup,
        "monthly_progress_pct": round(total_revenue / MONTHLY_REVENUE_TARGET * 100, 1) if MONTHLY_REVENUE_TARGET > 0 else 0,
    }

# ── 报告生成（飞书格式）──────────────────────────

def generate_report(metrics):
    """生成飞书适配的运营报告"""
    seg = metrics["segments"]

    # 趋势指示
    def trend(val, good_if_high=True):
        return "🟢" if good_if_high and val > 0 else "🔴"

    report = []
    report.append(f"📊 墨域私域沉淀 · 每日运营报告")
    report.append(f"📅 {TODAY_CN} ({TODAY})")
    report.append("")

    # ── 一、买家资产 ──
    report.append("━━━ 一、买家资产 ─━━")
    report.append(f"• 累计买家: {metrics['total_buyers']}人")
    report.append(f"• 高价值: {seg.get('high', 0)}人 | 中价值: {seg.get('medium', 0)}人 | 低价值: {seg.get('low', 0)}人")
    report.append(f"• 今日新增: +{metrics['today_new']}人  |  本周新增: +{metrics['this_week_new']}人")
    report.append(f"• 沉睡买家: {metrics['dormant_count']}人（{DAYS_THRESHOLD_DORMANT}天未复购）")
    report.append("")

    # ── 二、营收数据 ──
    report.append("━━━ 二、营收数据 ─━━")
    report.append(f"• 累计营收: ¥{metrics['total_revenue']:,.0f}")
    report.append(f"• 总订单数: {metrics['total_orders']}单")
    report.append(f"• ARPU: ¥{metrics['arpu']}/人")
    report.append(f"• 复购率: {metrics['repeat_rate']}%（{metrics['repeat_count']}人）")
    report.append(f"• 月目标进度: ¥{metrics['total_revenue']:,.0f} / ¥{MONTHLY_REVENUE_TARGET:,.0f} ({metrics['monthly_progress_pct']}%)")
    report.append("")

    # ── 三、触达运营 ──
    report.append("━━━ 三、触达运营 ─━━")
    report.append(f"• 触达计划: {metrics['total_planned_touches']}条")
    report.append(f"• 已执行触达: {metrics['total_sent_touches']}条 {trend(metrics['total_sent_touches'])}")
    report.append(f"• 待唤醒: {metrics['pending_wakeup']}人")
    report.append("")

    # ── 四、转介绍 ──
    report.append("━━━ 四、转介绍 ─━━")
    report.append(f"• 推荐人: {metrics['total_referrers']}人")
    report.append(f"• 被邀请: {metrics['total_invited']}人")
    report.append(f"• 累计积分: {metrics['total_points']}分")
    report.append("")

    # ── 五、行动建议 ──
    report.append("━━━ 五、今日行动建议 ─━━")
    actions = []
    if metrics['dormant_count'] > 0:
        actions.append(f"• 唤醒 {metrics['dormant_count']} 个沉睡买家（最近无触达）")
    if metrics['repeat_rate'] < 30:
        actions.append("• 复购率偏低，建议推送老客户优惠券")
    if metrics['total_sent_touches'] < metrics['total_planned_touches']:
        pending = metrics['total_planned_touches'] - metrics['total_sent_touches']
        actions.append(f"• 还有 {pending} 条触达未执行，请尽快推送")
    if metrics['total_invited'] < 3:
        actions.append("• 转介绍活跃度低，可发起邀请有奖活动")
    if metrics['today_new'] == 0:
        actions.append("• 今日暂无新客，建议加大引流力度")

    if not actions:
        actions.append("• 运营健康，保持节奏")

    report.extend(actions)
    report.append("")
    report.append("───")
    report.append(f"🕐 报告生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("墨域私域 · 自动化运营系统")

    return "\n".join(report)

# ── 主入口 ─────────────────────────────────────────

def main():
    log("开始生成墨域私域运营报告")
    metrics = calc_crm_metrics()
    report = generate_report(metrics)

    # 输出到文件
    report_file = RELAY_DIR / "crm_daily_report.md"
    report_file.write_text(report, encoding="utf-8")
    log(f"报告已写入 {report_file}")

    # 同时输出到stdout（供cron捕获投递）
    print("\n" + "=" * 48)
    print(report)
    print("=" * 48)

    # 记录指标快照
    snapshot_file = CRM_DIR / f"snapshot_{TODAY}.json"
    snapshot_file.write_text(json.dumps({
        "date": TODAY,
        "metrics": metrics,
        "report_preview": report[:200]
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    log("报告生成完成")
    return report

if __name__ == "__main__":
    main()
