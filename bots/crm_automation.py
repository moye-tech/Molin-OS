"""
CRM自动化系统 — CH5私域复购体系
纯标准库，零外部依赖。
功能：
1. buyer_segmentation() — 分层：high/medium/low 基于消费金额+频次
2. touch_sequence() — 触达序列：7天/14天/30天自动发跟进
3. re_engagement() — 30天未复购→推送新品+优惠
4. referral_program() — 转介绍激励，积分系统
"""

import os, sys, json, time, csv
from pathlib import Path

# ── 数据目录 ───────────────────────────────────────
DATA_DIR = Path.home() / ".hermes" / "crm"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BUYERS_FILE = DATA_DIR / "buyers.json"
TOUCH_FILE = DATA_DIR / "touch_log.json"
REFERRAL_FILE = DATA_DIR / "referral.json"
LOG_FILE = DATA_DIR / "crm_activity.log"

# ── 默认数据 ───────────────────────────────────────

DEFAULT_BUYERS = {}
DEFAULT_TOUCH_LOG = {}
DEFAULT_REFERRAL = {
    "referrers": {},       # user_id -> {"points": 0, "invited": [], "rewards": []}
    "points_rules": {
        "per_referral": 100,       # 每邀请一人得100积分
        "per_purchase_pct": 0.1,   # 被邀请人消费金额的10%给邀请人
        "redeem_rate": 10,         # 10积分=¥1
    }
}

# ── 日志 ───────────────────────────────────────────

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [CRM] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# ── 持久化 ─────────────────────────────────────────

def _load_json(path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default

def _save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

def load_buyers():
    return _load_json(BUYERS_FILE, DEFAULT_BUYERS)

def save_buyers(data):
    _save_json(BUYERS_FILE, data)

def load_touches():
    return _load_json(TOUCH_FILE, DEFAULT_TOUCH_LOG)

def save_touches(data):
    _save_json(TOUCH_FILE, data)

def load_referral():
    return _load_json(REFERRAL_FILE, DEFAULT_REFERRAL)

def save_referral(data):
    _save_json(REFERRAL_FILE, data)

# ── 买家数据结构 ──────────────────────────────────

"""
buyers = {
    "user_id_xxx": {
        "name": "张三",
        "phone": "",
        "wechat": "",
        "total_spent": 599.0,       # 总消费金额
        "order_count": 3,           # 下单次数
        "first_order": "2025-01-15",
        "last_order": "2025-04-20",
        "segment": "high",          # high / medium / low
        "tags": ["AI工具", "PPT"],
        "notes": ""
    }
}
"""

# ── 1. 买家分层 ───────────────────────────────────

def buyer_segmentation(save=True):
    """
    基于消费金额+频次对买家分层。
    分层规则：
      - high:  累计消费>=¥500 OR 下单>=3次
      - medium: 累计消费>=¥100 OR 下单>=2次
      - low:   其余
    返回分层统计和每个买家的分层结果。
    """
    buyers = load_buyers()
    if not buyers:
        log("⚠️ 没有买家数据，使用示例数据初始化")
        buyers = _init_sample_buyers()
        if save:
            save_buyers(buyers)

    stats = {"high": 0, "medium": 0, "low": 0, "total": len(buyers)}
    results = []

    for uid, info in buyers.items():
        total = info.get("total_spent", 0)
        orders = info.get("order_count", 0)

        if total >= 500 or orders >= 3:
            segment = "high"
        elif total >= 100 or orders >= 2:
            segment = "medium"
        else:
            segment = "low"

        info["segment"] = segment
        stats[segment] += 1
        results.append({"uid": uid, "name": info.get("name", uid), "segment": segment,
                        "total_spent": total, "order_count": orders})

    if save:
        save_buyers(buyers)

    log(f"📊 买家分层完成: HIGH={stats['high']}, MEDIUM={stats['medium']}, LOW={stats['low']} (共{stats['total']}人)")

    return {"stats": stats, "buyers": results}

def _init_sample_buyers():
    """初始化示例买家数据"""
    return {
        "buyer_001": {"name": "王大力", "total_spent": 1280.0, "order_count": 5,
                      "first_order": "2025-01-10", "last_order": "2025-04-28", "tags": ["AI工具", "BP"], "notes": ""},
        "buyer_002": {"name": "李小明", "total_spent": 350.0, "order_count": 2,
                      "first_order": "2025-02-15", "last_order": "2025-03-20", "tags": ["PPT"], "notes": ""},
        "buyer_003": {"name": "赵四", "total_spent": 59.0, "order_count": 1,
                      "first_order": "2025-04-01", "last_order": "2025-04-01", "tags": ["LOGO"], "notes": ""},
        "buyer_004": {"name": "陈姐", "total_spent": 880.0, "order_count": 4,
                      "first_order": "2025-01-20", "last_order": "2025-05-01", "tags": ["AI工具", "视频"], "notes": ""},
        "buyer_005": {"name": "刘老师", "total_spent": 199.0, "order_count": 1,
                      "first_order": "2025-03-10", "last_order": "2025-03-10", "tags": ["PPT"], "notes": ""},
        "buyer_006": {"name": "老周", "total_spent": 1500.0, "order_count": 7,
                      "first_order": "2025-01-05", "last_order": "2025-04-30", "tags": ["AI工具", "定制"], "notes": "长期合作"},
        "buyer_007": {"name": "小美", "total_spent": 45.0, "order_count": 1,
                      "first_order": "2025-04-18", "last_order": "2025-04-18", "tags": ["模板"], "notes": ""},
    }

# ── 2. 触达序列 ───────────────────────────────────

# 触达策略模板
TOUCH_TEMPLATES = {
    "high": {
        "7d": "🎉 {name}，上次的服务还满意吗？我们最近出了新品，给你预留了优先体验名额！私信我看看~",
        "14d": "💡 {name}，分享一个你可能用到的AI效率技巧：[技巧内容]。需要的话我帮你定制方案~",
        "30d": "🌟 {name}，老客户专属福利！本月下单享8折优惠，附赠一次免费升级服务。私信我领取！",
    },
    "medium": {
        "7d": "👋 {name}，上次的服务你觉得怎么样？有任何想法随时找我聊~",
        "14d": "📢 {name}，最近我们上新了！{product}现在有优惠活动，要不要看看？",
        "30d": "🎁 {name}，感谢你一直以来的支持！送你一张¥20优惠券，下单直接抵扣~",
    },
    "low": {
        "7d": "😊 {name}，上次的体验如何？有需要随时找我！",
        "14d": "💬 {name}，我们最近在搞活动，新客户专享9折优惠，有兴趣了解一下吗？",
        "30d": "🏷️ {name}，好久不见！送你一张¥10新人券，随时可用哦~",
    }
}

def touch_sequence():
    """
    触达序列：对每个分层的买家按7天/14天/30天自动生成跟进文案。
    返回每个买家的触达计划。
    """
    # 先运行分层确保数据最新
    seg_result = buyer_segmentation()
    buyers = load_buyers()
    touches = load_touches()
    now = time.time()
    plan = []

    for uid, info in buyers.items():
        segment = info.get("segment", "low")
        name = info.get("name", "亲")
        last_order = info.get("last_order", "2025-01-01")
        days_since = (time.mktime(time.strptime(last_order, "%Y-%m-%d"))
                      if last_order else now) if isinstance(last_order, str) else 0

        # 获取对应分层的触达模板
        templates = TOUCH_TEMPLATES.get(segment, TOUCH_TEMPLATES["low"])

        # 生成触达计划
        touch_plan = []
        for interval_key, template in templates.items():
            interval_days = int(interval_key.replace("d", ""))
            product = "AI系统定制服务" if segment == "high" else "PPT美化/LOGO设计"

            message = template.format(name=name, product=product)

            # 记录计划
            entry = {
                "uid": uid,
                "name": name,
                "segment": segment,
                "interval": interval_key,
                "message": message,
                "planned_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "sent": False
            }
            touch_plan.append(entry)
            plan.append(entry)

        # 更新触达日志
        if uid not in touches:
            touches[uid] = {"name": name, "segment": segment,
                           "touches_sent": 0, "last_touch": "", "plan": touch_plan}
        else:
            touches[uid]["plan"] = touch_plan
            touches[uid]["segment"] = segment

    save_touches(touches)
    log(f"📋 触达序列生成完成: 共{len(plan)}条计划, 覆盖{len(buyers)}个买家")
    return plan

def execute_touches():
    """
    执行当前应该发送的触达消息。
    根据上次触达时间和间隔判断。
    """
    touches = load_touches()
    buyers = load_buyers()
    now = time.time()
    executed = []

    for uid, record in touches.items():
        plan = record.get("plan", [])
        for entry in plan:
            if entry.get("sent"):
                continue

            interval_days = int(entry["interval"].replace("d", ""))
            last_touch_str = record.get("last_touch", "")

            if last_touch_str:
                last_touch = time.mktime(time.strptime(last_touch_str, "%Y-%m-%d"))
            else:
                # 首次触达，用最后一次订单时间
                info = buyers.get(uid, {})
                last_order_str = info.get("last_order", "2025-01-01")
                if isinstance(last_order_str, str):
                    last_touch = time.mktime(time.strptime(last_order_str, "%Y-%m-%d"))
                else:
                    last_touch = now

            days_passed = (now - last_touch) / 86400
            if days_passed >= interval_days:
                message = entry["message"]
                log(f"📤 触达 {record['name']}({uid}): {message[:60]}...")
                record["touches_sent"] += 1
                record["last_touch"] = time.strftime("%Y-%m-%d")
                entry["sent"] = True
                executed.append({"uid": uid, "name": record["name"], "message": message})

    if executed:
        save_touches(touches)
        log(f"✅ 执行触达 {len(executed)} 条")
    else:
        log("📭 当前无需要触达的买家")

    return executed

# ── 3. 沉睡唤醒 ───────────────────────────────────

def re_engagement():
    """
    30天未复购 → 推送新品+优惠
    检测所有买家，找出最后下单距今>30天的，生成唤醒文案。
    """
    buyers = load_buyers()
    now = time.time()
    reengaged = []

    for uid, info in buyers.items():
        last_order_str = info.get("last_order", "")
        if not last_order_str:
            continue

        try:
            last_order = time.mktime(time.strptime(last_order_str, "%Y-%m-%d"))
        except:
            continue

        days_since = (now - last_order) / 86400

        if days_since >= 30:
            name = info.get("name", "亲")
            segment = info.get("segment", "low")

            # 根据分层定制唤醒文案
            if segment == "high":
                message = (
                    f"🌟 {name}，好久不见！你有一个月没来啦~\n"
                    f"我们最近推出了全新的{get_new_products(segment)}，老客户专享价！\n"
                    f"🎁 送你一张¥50专属优惠券，下单直接抵扣，今天有效！"
                )
            elif segment == "medium":
                message = (
                    f"👋 {name}，最近忙什么呢？\n"
                    f"我们刚上线了{get_new_products(segment)}，很多客户都说好用！\n"
                    f"🎁 送你一张¥30优惠券，回来看看吧~"
                )
            else:
                message = (
                    f"💌 {name}，好久不见！还记得我们上次的合作吗？\n"
                    f"现在新人回归专享{get_new_products(segment)}，首单立减¥20！"
                )

            info["re_engagement_sent"] = True
            reengaged.append({"uid": uid, "name": name, "segment": segment,
                             "days_since": int(days_since), "message": message})
            log(f"🔄 唤醒 {name}({uid}): 已{int(days_since)}天未复购")

    if reengaged:
        save_buyers(buyers)
        # 保存唤醒记录
        reng_file = DATA_DIR / "re_engagement_latest.json"
        reng_file.write_text(json.dumps(reengaged, ensure_ascii=False, indent=2))
        log(f"✅ 唤醒 {len(reengaged)} 个沉睡买家")
    else:
        log("📭 无需要唤醒的买家")

    return reengaged

def get_new_products(segment="low"):
    """根据分层推荐新品"""
    products = {
        "high": "AI全流程自动化系统 v2.0、企业定制数字人、VIP年费服务",
        "medium": "AI系统定制基础版、PPT高级模板包、短视频脚本服务",
        "low": "AI新手入门包、LOGO设计特惠、内容飞轮模板",
    }
    return products.get(segment, "AI效率提升服务")

# ── 4. 转介绍激励 ─────────────────────────────────

def referral_program():
    """
    转介绍激励，积分系统。
    管理推荐关系、积分累计、兑换。
    """
    referral = load_referral()
    rules = referral.get("points_rules", DEFAULT_REFERRAL["points_rules"])
    referrers = referral.get("referrers", {})

    log(f"🏆 转介绍系统运行中")
    log(f"   当前推荐人: {len(referrers)}人")
    log(f"   规则: 每邀请1人得{rules['per_referral']}积分, 消费返{rules['per_purchase_pct']*100}%")

    stats = {
        "total_referrers": len(referrers),
        "total_invited": sum(len(r.get("invited", [])) for r in referrers.values()),
        "total_points": sum(r.get("points", 0) for r in referrers.values()),
        "rules": rules
    }

    return stats

def add_referral(inviter_id, new_user_id, new_user_name=""):
    """
    记录一次转介绍。
    inviter_id: 邀请人ID
    new_user_id: 新用户ID
    """
    referral = load_referral()
    referrers = referral.get("referrers", {})
    rules = referral.get("points_rules", DEFAULT_REFERRAL["points_rules"])

    if inviter_id not in referrers:
        referrers[inviter_id] = {"points": 0, "invited": [], "rewards": []}

    # 记录邀请
    referrers[inviter_id]["invited"].append({
        "user_id": new_user_id,
        "user_name": new_user_name,
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "purchase_amount": 0
    })

    # 加积分
    referrers[inviter_id]["points"] += rules["per_referral"]
    referrers[inviter_id]["rewards"].append({
        "type": "referral_bonus",
        "points": rules["per_referral"],
        "reason": f"邀请新用户 {new_user_name}",
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    })

    referral["referrers"] = referrers
    save_referral(referral)
    log(f"🎉 转介绍: {inviter_id} 邀请 {new_user_name}({new_user_id}), +{rules['per_referral']}积分")
    return referrers[inviter_id]["points"]

def record_referral_purchase(new_user_id, amount):
    """
    被邀请人消费后，给邀请人返积分。
    遍历找匹配的邀请记录。
    """
    referral = load_referral()
    referrers = referral.get("referrers", {})
    rules = referral.get("points_rules", DEFAULT_REFERRAL["points_rules"])

    earned_points = int(amount * rules["per_purchase_pct"] * rules.get("redeem_rate", 10) / 10)

    for inviter_id, data in referrers.items():
        for invite in data.get("invited", []):
            if invite["user_id"] == new_user_id and invite["purchase_amount"] == 0:
                invite["purchase_amount"] = amount
                data["points"] += earned_points
                data["rewards"].append({
                    "type": "purchase_commission",
                    "points": earned_points,
                    "amount": amount,
                    "reason": f"被邀请人 {new_user_id} 消费 ¥{amount}",
                    "time": time.strftime("%Y-%m-%d %H:%M:%S")
                })
                log(f"💰 推荐返利: {inviter_id} 获得 {earned_points} 积分 (来自 {new_user_id} 消费 ¥{amount})")
                break

    referral["referrers"] = referrers
    save_referral(referral)
    return earned_points

def get_leaderboard(top_n=10):
    """获取转介绍排行榜"""
    referral = load_referral()
    referrers = referral.get("referrers", {})

    # 导入买家数据获取姓名
    buyers = load_buyers()

    ranking = []
    for uid, data in referrers.items():
        name = buyers.get(uid, {}).get("name", uid)
        ranking.append({
            "uid": uid,
            "name": name,
            "points": data.get("points", 0),
            "invited_count": len(data.get("invited", [])),
            "total_purchase_amount": sum(i.get("purchase_amount", 0) for i in data.get("invited", []))
        })

    ranking.sort(key=lambda x: x["points"], reverse=True)
    return ranking[:top_n]

# ── 综合报告 ───────────────────────────────────────

def generate_crm_report():
    """生成CRM综合运营报告"""
    seg_result = buyer_segmentation()
    touch_plan = touch_sequence()
    reng_result = re_engagement()
    ref_stats = referral_program()

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "segmentation": seg_result,
        "touch_plan_count": len(touch_plan),
        "re_engagement_count": len(reng_result) if isinstance(reng_result, list) else 0,
        "referral": ref_stats,
        "leaderboard": get_leaderboard(5)
    }

    report_file = DATA_DIR / "crm_report_latest.json"
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    log("📊 CRM综合报告已生成")
    return report

# ── CLI入口 ────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""CRM自动化系统 — CH5私域复购体系
用法:
  python3.12 crm_automation.py segment        买家分层 (high/medium/low)
  python3.12 crm_automation.py touch          生成触达序列 (7d/14d/30d)
  python3.12 crm_automation.py execute        执行触达消息
  python3.12 crm_automation.py reengagement   唤醒30天未复购买家
  python3.12 crm_automation.py referral       转介绍系统状态
  python3.12 crm_automation.py add_ref <邀请人ID> <新用户ID> [新用户名]  记录转介绍
  python3.12 crm_automation.py report         生成综合CRM报告
  python3.12 crm_automation.py all            运行全部CRM功能
""")
        sys.exit(1)

    action = sys.argv[1]

    if action == "segment":
        result = buyer_segmentation()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif action == "touch":
        plan = touch_sequence()
        print(json.dumps(plan[:5], ensure_ascii=False, indent=2))
        print(f"... (共{len(plan)}条触达计划)")
    elif action == "execute":
        executed = execute_touches()
        print(f"执行了 {len(executed)} 条触达")
    elif action == "reengagement":
        result = re_engagement()
        print(json.dumps(result[:5] if result else [], ensure_ascii=False, indent=2))
    elif action == "referral":
        stats = referral_program()
        lb = get_leaderboard(5)
        print(json.dumps({"stats": stats, "leaderboard": lb}, ensure_ascii=False, indent=2))
    elif action == "add_ref" and len(sys.argv) >= 4:
        inviter = sys.argv[2]
        new_user = sys.argv[3]
        name = sys.argv[4] if len(sys.argv) > 4 else ""
        points = add_referral(inviter, new_user, name)
        print(f"✅ 邀请记录完成, {inviter} 当前积分: {points}")
    elif action == "record_purchase" and len(sys.argv) >= 4:
        user_id = sys.argv[2]
        amount = float(sys.argv[3])
        earned = record_referral_purchase(user_id, amount)
        print(f"✅ 消费记录完成, 返积分: {earned}")
    elif action == "report":
        report = generate_crm_report()
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif action == "all":
        print("\n=== CRM综合运行 ===\n")
        seg = buyer_segmentation()
        print(f"买家分层: HIGH={seg['stats']['high']} MEDIUM={seg['stats']['medium']} LOW={seg['stats']['low']}")
        plan = touch_sequence()
        print(f"触达计划: {len(plan)}条")
        reng = re_engagement()
        print(f"唤醒买家: {len(reng) if isinstance(reng, list) else 0}人")
        ref = referral_program()
        print(f"转介绍系统: {ref['total_referrers']}推荐人, {ref['total_invited']}被邀请人")
        report = generate_crm_report()
        print(f"\n✅ CRM报告已保存到 {DATA_DIR / 'crm_report_latest.json'}")
    else:
        print(f"未知操作: {action}")
