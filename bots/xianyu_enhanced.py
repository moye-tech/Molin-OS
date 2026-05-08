"""
闲鱼增强模块 — CH5升级
不破坏现有 xianyu_bot.py，提供额外高级功能：
- 定时自动执行 detect/review/price
- 批量上架模板生成
- 综合监控仪表盘

纯标准库，零外部依赖。
"""

import os, sys, json, time, threading
from pathlib import Path

# 复用 xianyu_bot 的状态目录和日志
STATE_DIR = Path.home() / ".hermes" / "xianyu_bot"
STATE_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = STATE_DIR / "enhanced_activity.log"

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [ENHANCED] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# ── 1. 定时自动执行器 ──────────────────────────────

SCHEDULE_FILE = STATE_DIR / "enhanced_schedule.json"

DEFAULT_SCHEDULE = {
    "detect_interval_hours": 48,
    "review_interval_hours": 72,
    "price_interval_hours": 24,
    "enabled": True
}

def load_schedule():
    if SCHEDULE_FILE.exists():
        return json.loads(SCHEDULE_FILE.read_text())
    return DEFAULT_SCHEDULE.copy()

def save_schedule(sched):
    SCHEDULE_FILE.write_text(json.dumps(sched, ensure_ascii=False, indent=2))

def run_scheduled_tasks():
    """按计划运行 detect/review/price 任务"""
    from xianyu_bot import detect_browsing_no_order, auto_review_request, dynamic_pricing

    sched = load_schedule()
    if not sched.get("enabled", True):
        log("⏸️ 定时任务已禁用")
        return

    log("🔄 运行增强模块定时任务...")
    try:
        detect_browsing_no_order()
        log("✅ detect 完成")
    except Exception as e:
        log(f"⚠️ detect 异常: {e}")

    try:
        auto_review_request()
        log("✅ review 完成")
    except Exception as e:
        log(f"⚠️ review 异常: {e}")

    try:
        dynamic_pricing()
        log("✅ price 完成")
    except Exception as e:
        log(f"⚠️ price 异常: {e}")

    log("✅ 增强模块定时任务全部完成")

# ── 2. 批量上架模板 ────────────────────────────────

SKU_TEMPLATES = {
    "bp": {
        "title": "商业计划书/BP代写 专业级 ¥199",
        "price": 199,
        "category": "设计服务",
        "desc": "专业商业计划书代写服务，含行业研究+市场分析+财务预测。适合创业者融资、路演、申报项目。提供PPT+Word双版本。"
    },
    "ppt": {
        "title": "PPT美化/代做 汇报路演课件 ¥99",
        "price": 99,
        "category": "设计服务",
        "desc": "专业PPT美化设计，适合工作汇报、路演融资、课程课件。含3次修改，包满意。"
    },
    "logo": {
        "title": "LOGO/VI设计 简约专业 ¥59",
        "price": 59,
        "category": "设计服务",
        "desc": "简约专业LOGO设计，含3次修改。提供源文件+透明底PNG+多种配色方案。"
    },
    "ai_avatar": {
        "title": "AI数字人/视频剪辑 企业级 ¥199",
        "price": 199,
        "category": "视频制作",
        "desc": "AI数字人形象定制+视频制作。适合企业宣传、课程讲解、短视频带货。含形象训练+5条成品视频。"
    }
}

def generate_batch_from_templates(template_keys=None):
    """从模板生成批量上架数据"""
    if template_keys is None:
        template_keys = list(SKU_TEMPLATES.keys())

    skus = []
    for key in template_keys:
        if key in SKU_TEMPLATES:
            skus.append(SKU_TEMPLATES[key].copy())
            log(f"📋 加载模板: {key} → {SKU_TEMPLATES[key]['title']}")

    return skus

# ── 3. 综合监控仪表盘 ──────────────────────────────

def generate_dashboard():
    """生成闲鱼运营综合仪表盘"""
    from xianyu_bot import load_state, load_config

    state = load_state()
    config = load_config()

    # 读取各模块状态
    browsing_file = STATE_DIR / "browsing_track.json"
    review_file = STATE_DIR / "review_track.json"
    pricing_file = STATE_DIR / "pricing_cache.json"

    browsing_data = json.loads(browsing_file.read_text()) if browsing_file.exists() else {}
    review_data = json.loads(review_file.read_text()) if review_file.exists() else {}
    pricing_data = json.loads(pricing_file.read_text()) if pricing_file.exists() else {"suggestions": []}

    browsing_pending = sum(1 for r in browsing_data.values() if not r.get("ordered") and not r.get("notified"))
    review_pending = sum(1 for r in review_data.values() if not r.get("requested"))

    dashboard = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "state": {
            "messages_handled": state.get("messages_handled", 0),
            "replies_sent": state.get("replies_sent", 0),
            "last_activity": state.get("last_activity", "从未"),
        },
        "browsing": {
            "total_tracked": len(browsing_data),
            "pending_touch": browsing_pending,
            "converted": sum(1 for r in browsing_data.values() if r.get("ordered"))
        },
        "reviews": {
            "total_orders": len(review_data),
            "pending_review": review_pending,
            "reviewed": sum(1 for r in review_data.values() if r.get("requested"))
        },
        "pricing": {
            "last_check": pricing_data.get("last_check", 0),
            "suggestions_count": len(pricing_data.get("suggestions", []))
        }
    }

    report_file = STATE_DIR / "dashboard_latest.json"
    report_file.write_text(json.dumps(dashboard, ensure_ascii=False, indent=2))
    log("📊 仪表盘已更新")
    return dashboard

# ── 4. 一键运行所有增强功能 ───────────────────────

def run_all_enhanced():
    """运行所有CH5增强功能"""
    log("🚀 启动闲鱼增强模块 (xianyu_enhanced)")

    # Step 1: 生成示例SKU模板并批量上架
    log("Step 1: 批量上架模板生成...")
    skus = generate_batch_from_templates()
    from xianyu_bot import batch_list
    results = batch_list(skus)
    log(f"已生成 {len(results)} 个商品上架数据")

    # Step 2: 运行定时任务
    log("Step 2: 运行定时任务...")
    run_scheduled_tasks()

    # Step 3: 生成仪表盘
    log("Step 3: 生成运营仪表盘...")
    dashboard = generate_dashboard()
    log(f"仪表盘: 消息={dashboard['state']['messages_handled']}, "
        f"待触达={dashboard['browsing']['pending_touch']}, "
        f"待催评={dashboard['reviews']['pending_review']}")

    log("✅ 增强模块执行完毕")
    return dashboard

# ── 5. 后台守护进程 ────────────────────────────────

def start_daemon(interval_seconds=3600):
    """启动后台守护进程，定期执行增强任务"""
    log(f"🛡️ 启动增强守护进程 (间隔={interval_seconds}s)")

    def loop():
        while True:
            run_scheduled_tasks()
            generate_dashboard()
            for i in range(interval_seconds // 10):
                time.sleep(10)
                # 每10秒检查一次是否应该退出（可通过文件标记控制）
                if not (STATE_DIR / ".daemon_alive").exists():
                    log("🛑 守护进程收到停止信号")
                    return

    t = threading.Thread(target=loop, daemon=True)
    t.start()

    # 创建存活标记
    (STATE_DIR / ".daemon_alive").write_text("1")
    log("✅ 增强守护进程已启动")
    return t

def stop_daemon():
    """停止守护进程"""
    marker = STATE_DIR / ".daemon_alive"
    if marker.exists():
        marker.unlink()
        log("🛑 守护进程停止信号已发送")
    else:
        log("ℹ️ 守护进程未运行")

# ── CLI入口 ────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""闲鱼增强模块 — CH5升级版
用法:
  python3.12 xianyu_enhanced.py all        运行所有增强功能 (batch+detect+review+price+dashboard)
  python3.12 xianyu_enhanced.py schedule   运行定时任务 (detect+review+price)
  python3.12 xianyu_enhanced.py dashboard  生成运营仪表盘
  python3.12 xianyu_enhanced.py daemon     启动后台守护进程 (每小时执行)
  python3.12 xianyu_enhanced.py stop       停止守护进程
  python3.12 xianyu_enhanced.py templates  查看可用SKU模板
""")
        sys.exit(1)

    action = sys.argv[1]

    if action == "all":
        run_all_enhanced()
    elif action == "schedule":
        run_scheduled_tasks()
    elif action == "dashboard":
        d = generate_dashboard()
        print(json.dumps(d, ensure_ascii=False, indent=2))
    elif action == "daemon":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 3600
        start_daemon(interval)
        # 保持主线程运行
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            stop_daemon()
    elif action == "stop":
        stop_daemon()
    elif action == "templates":
        print("可用SKU模板:")
        for key, tpl in SKU_TEMPLATES.items():
            print(f"  {key}: {tpl['title']} ¥{tpl['price']}")
    else:
        print(f"未知操作: {action}")
