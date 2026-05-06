"""墨域OS — CLI入口
一键运行整个一人公司操作系统

用法:
  python3 -m molib.cli "帮我写一篇小红书文章"
  python3 -m molib.cli analyze "检查服务器"
  python3 -m molib.cli vps          # 列出所有VP
  python3 -m molib.cli workers      # 列出所有子公司
  python3 -m molib.cli health       # 系统健康检查
"""
import asyncio
import sys
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent


async def cmd_run(text: str):
    """完整任务执行"""
    from molib.agencies.workers import register_all, get_worker, Task
    from molib.ceo.intent_router import IntentRouter
    from molib.ceo.risk_engine import RiskEngine
    from molib.ceo.sop_store import SOPStore

    register_all()

    print(f"\n{'═'*50}")
    print(f"  墨域OS — 任务执行")
    print(f"{'═'*50}")
    print(f"  输入: {text}\n")

    # Step 1: Intent Router
    router = IntentRouter()
    intent = await router.analyze(text)
    print(f"  🔍 意图: {intent.intent_type}")
    print(f"  📊 复杂度: {intent.complexity_score}/100")
    print(f"  🎯 目标VP: {', '.join(intent.target_vps)}")
    if intent.target_subsidiaries:
        print(f"  🏢 目标子公司: {', '.join(intent.target_subsidiaries)}")

    # Step 2: Risk Assessment
    re = RiskEngine()
    risk = re.assess(intent)
    print(f"  ⚠️  风险分: {risk.risk_score}")
    if risk.requires_approval:
        print(f"  🔴 需要审批! 原因: {risk.reason}")
        return {"status": "blocked", "reason": risk.reason}

    # Step 3: Execute Workers
    results = []
    for wid in intent.target_subsidiaries:
        worker = get_worker(wid)
        if worker:
            task = Task(task_id="cli_001", task_type=wid, payload={"topic": text})
            result = await worker.execute(task)
            results.append({"worker": wid, "status": result.status, "output": result.output})
            status_icon = "✅" if result.status == "success" else "❌"
            print(f"  {status_icon} {worker.worker_name}: {result.status}")

    print(f"\n{'═'*50}")
    print(f"  执行完成! {len(results)}个子公司参与")
    print(f"{'═'*50}")

    # Step 4: Save SOP
    sop = SOPStore()
    sop.save(f"cli_{id(text)}", intent.target_vps,
             [{"worker": r["worker"], "status": r["status"]} for r in results], 85.0, 1.0)

    return {"status": "done", "results": results}


async def cmd_analyze(text: str):
    """仅分析不执行"""
    from molib.ceo.intent_router import IntentRouter
    from molib.ceo.risk_engine import RiskEngine

    router = IntentRouter()
    intent = await router.analyze(text)
    re = RiskEngine()
    risk = re.assess(intent)

    print(json.dumps({
        "intent_type": intent.intent_type,
        "complexity": intent.complexity_score,
        "vps": intent.target_vps,
        "subsidiaries": intent.target_subsidiaries,
        "risk_level": intent.risk_level,
        "risk_score": risk.risk_score,
        "requires_approval": risk.requires_approval,
        "risk_reason": risk.reason,
    }, ensure_ascii=False, indent=2))


def cmd_vps():
    """列出所有VP及其子公司"""
    from molib.management.vp_registry import get_all_vps

    vps = get_all_vps()
    print(f"\n{'═'*50}")
    print(f"  墨域OS — VP管理层 ({len(vps)}位)")
    print(f"{'═'*50}")

    for vp in vps:
        print(f"\n  ▸ {vp.name}")
        print(f"    质量门控: {vp.quality_gate}/100  |  升级模型: {vp.escalation_model}")
        print(f"    子公司: {', '.join(s.name if hasattr(s,'name') else str(s) for s in vp.subsidiaries)}")


def cmd_workers():
    """列出所有子公司Worker"""
    from molib.agencies.workers import register_all, list_workers

    register_all()
    workers = list_workers()

    print(f"\n{'═'*50}")
    print(f"  墨域OS — 子公司 ({len(workers)}家)")
    print(f"{'═'*50}")

    # 按VP分组
    groups = {
        "VP营销": ["content_writer", "ip_manager", "designer", "short_video", "voice_actor"],
        "VP运营": ["crm", "customer_service", "ecommerce", "education"],
        "VP技术": ["developer", "ops", "security", "auto_dream"],
        "VP财务": ["finance"],
        "VP战略": ["bd", "global_marketing", "research"],
        "共同": ["legal", "knowledge", "data_analyst"],
    }

    seen = set()
    for group_name, wids in groups.items():
        print(f"\n  📂 {group_name}")
        for wid in wids:
            for w in workers:
                if w["id"] == wid and wid not in seen:
                    print(f"     ▸ {w['name']:12s} — {w['line']}")
                    seen.add(wid)


def cmd_health():
    """系统健康检查"""
    print(f"\n{'═'*50}")
    print(f"  墨域OS — 系统健康检查")
    print(f"{'═'*50}")

    checks = {}
    # Check molib modules
    for mod_name in ["molib.ceo.intent_router", "molib.ceo.risk_engine",
                     "molib.ceo.sop_store", "molib.ceo.ceo_orchestrator",
                     "molib.management.vp_agents", "molib.management.vp_registry",
                     "molib.agencies.workers.base"]:
        try:
            __import__(mod_name)
            checks[mod_name] = "✅"
        except Exception as e:
            checks[mod_name] = f"❌ {e}"

    # Check config files
    config_files = ["config/company.toml", "config/company.yaml",
                    "config/governance.yaml", "config/company_v2.yaml",
                    ".env.example"]
    for cf in config_files:
        p = ROOT / cf
        checks[f"config/{cf}"] = "✅" if p.exists() else "❌ 缺失"

    # Check workers
    from molib.agencies.workers import register_all, list_workers
    register_all()
    w_count = len(list_workers())
    checks[f"子公司Worker ({w_count}家)"] = "✅" if w_count == 20 else f"⚠️  {w_count}家"

    # VP count
    from molib.management.vp_registry import get_all_vps
    v_count = len(get_all_vps())
    checks[f"VP管理层 ({v_count}位)"] = "✅" if v_count == 5 else f"⚠️  {v_count}位"

    # Print results
    for name, status in checks.items():
        print(f"  {status} {name}")

    all_ok = all(v == "✅" for v in checks.values())
    print(f"\n{'═'*50}")
    print(f"  总体状态: {'✅ 全部正常' if all_ok else '⚠️  有异常'}")
    print(f"{'═'*50}")

    return all_ok


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 -m molib.cli \"你的指令\"    # 执行任务")
        print("  python3 -m molib.cli analyze \"...\" # 仅分析")
        print("  python3 -m molib.cli vps           # 列出VP")
        print("  python3 -m molib.cli workers       # 列出子公司")
        print("  python3 -m molib.cli health        # 健康检查")
        sys.exit(1)

    command = sys.argv[1]

    if command == "vps":
        cmd_vps()
    elif command == "workers":
        cmd_workers()
    elif command == "health":
        cmd_health()
    elif command == "analyze":
        text = " ".join(sys.argv[2:])
        if not text:
            print("请提供分析文本")
            sys.exit(1)
        asyncio.run(cmd_analyze(text))
    else:
        # 默认当做任务执行
        text = " ".join(sys.argv[1:])
        asyncio.run(cmd_run(text))


if __name__ == "__main__":
    main()
