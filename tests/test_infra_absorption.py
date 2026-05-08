"""全链路集成测试 — 事件总线 + 凭证保险柜 + 审批引擎 + SOP引擎"""
import asyncio
import logging
import sys

sys.path.insert(0, "/home/ubuntu/hermes-os")
logging.basicConfig(level=logging.WARNING)

from molib.infra.event_bus import get_event_bus
from molib.infra.credential_vault import get_credential_vault
from molib.infra.deep_approval import get_approval_workflow
from molib.sop.engine import get_sop_engine


async def test_event_bus():
    bus = get_event_bus()
    received = []
    async def on_test(event):
        received.append(event.event_type)
    bus.subscribe("test.event", on_test)
    await bus.publish_quick("test.event", "test", {"msg": "hello"})
    await asyncio.sleep(0.1)
    assert len(received) == 1, f"Expected 1 event, got {received}"
    print(f"  ✅ EventBus publish+subscribe: received={received}")
    print(f"  ✅ handlers: {bus.get_handler_count()}")


async def test_credential_vault():
    vault = get_credential_vault()
    rid = vault.store_credential(
        "xianyu", "test_user", "my_secret_token", "token", expires_in_days=30
    )
    stored = vault.list_credentials("xianyu")
    assert len(stored) == 1, f"Expected 1 credential, got {stored}"
    print(f"  ✅ store: {rid}")

    decoded = vault.get_credential(rid, "cs")
    assert decoded == "my_secret_token", f"Decrypt failed: {decoded}"
    print(f"  ✅ get(ACL cs→xianyu): decoded={decoded}")

    denied = vault.get_credential(rid, "dev")
    assert denied is None, f"ACL should deny dev→xianyu: {denied}"
    print(f"  ✅ get(ACL dev→xianyu deny): denied correctly")

    audit = vault.get_audit_log()
    print(f"  ✅ audit log: {len(audit)} entries")


async def test_approval():
    wf = get_approval_workflow()

    risk, rules = wf.evaluate_risk({"amount": 100, "action": "approve"})
    assert risk == "low", f"Expected low, got {risk}"
    print(f"  ✅ low risk: {risk}")

    risk, rules = wf.evaluate_risk({"action": "delete_data"})
    assert risk == "critical", f"Expected critical, got {risk}"
    print(f"  ✅ critical risk: {risk}")

    risk, rules = wf.evaluate_risk({"action": "update_sop"})
    assert risk == "high", f"Expected high, got {risk}"
    print(f"  ✅ high risk: {risk}")

    req = await wf.create_approval(
        "测试审批", "desc", {"action": "delete_data"}, "cs", "task1"
    )
    assert req is not None, "Approval should be created for high risk"
    assert req.risk_level == "critical", f"Expected critical, got {req.risk_level}"
    print(f"  ✅ create approval: {req.approval_id} (risk={req.risk_level})")

    approved = wf.approve(req.approval_id)
    assert approved and approved.status == "approved"
    print(f"  ✅ approve: OK")

    stats = wf.get_stats()
    print(f"  ✅ stats: {stats}")


async def test_sop_with_approval():
    eng = get_sop_engine()
    eng.definitions["approval_flow_test"] = {
        "id": "approval_flow_test",
        "name": "审批集成测试",
        "version": "1.0",
        "enabled": True,
        "steps": [
            {"name": "分析", "type": "automated", "action": "analyze"},
            {"name": "审批", "type": "approval", "action": "delete_data", "agency": "cs", "description": "删除测试数据"},
            {"name": "发布", "type": "automated", "action": "publish"},
        ],
    }
    pid = await eng.start_procedure("approval_flow_test", {"topic": "X"})
    await asyncio.sleep(2)
    status = eng.get_procedure_status(pid)
    assert status is not None, "Procedure not found"
    assert status["status"] == "completed", f"Expected completed, got {status['status']}"
    steps = status["steps_history"]
    print(f"  ✅ SOP+Approval: {len(steps)} steps executed")
    for s in steps:
        result = s["result"]
        print(f"    - {s['step_name']}: success={result['success']} type={result.get('type', result.get('action', '?'))}")


async def main():
    print("=== 1. EventBus ===")
    await test_event_bus()
    print("\n=== 2. CredentialVault ===")
    await test_credential_vault()
    print("\n=== 3. ApprovalWorkflow ===")
    await test_approval()
    print("\n=== 4. SOP + Approval 集成 ===")
    await test_sop_with_approval()
    print("\n=== ✅ ALL INFRA TESTS PASSED ===")


if __name__ == "__main__":
    asyncio.run(main())
