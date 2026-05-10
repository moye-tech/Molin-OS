"""Level 4 · 飞书端到端冒烟测试

端到端验收脚本：发消息到本地 CEO API → 验证回复内容。
运行命令：python tests/test_e2e_feishu.py

注意：此测试需要本地 CEO 服务正在运行（curl http://localhost:28000/health 返回 200）。
如果服务未运行，此测试会 SKIP 而非 FAIL。
"""

import asyncio
import httpx
import time
import sys
import json

HERMES_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:28000"
CHAT_URL = f"{HERMES_URL}/api/chat"
HEALTH_URL = f"{HERMES_URL}/health"

E2E_CASES = [
    # (输入, 预期关键词列表, 超时秒)
    ("结合我们的系统，把猪八戒网上我们能接的需求梳理出来",
     ["猪八戒", "AI"], 90),
    ("帮我分析竞品最近的动态",
     ["竞品", "分析"], 60),
    ("你好",
     ["你", "你好"], 10),   # trivial 请求应快速响应
]


async def check_health() -> bool:
    """检查服务是否可用"""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(HEALTH_URL)
            return resp.status_code == 200
    except Exception:
        return False


async def test_case(user_input: str, expected_keywords: list, timeout: int) -> bool:
    """单个 E2E 测试用例"""
    start = time.time()
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            CHAT_URL,
            json={"session_id": f"e2e_test_{int(time.time())}_{id(user_input)}", "input": user_input},
        )
        resp.raise_for_status()
        result = resp.json()

    elapsed = time.time() - start
    reply = result.get("message", "")

    # 检查关键词覆盖
    missing = [kw for kw in expected_keywords if kw not in reply]
    if missing:
        print(f"❌ FAIL [{elapsed:.1f}s] Missing keywords: {missing} in reply: {reply[:200]}")
        return False

    # 检查不是状态摘要
    if "个成功" in reply:
        print(f"❌ FAIL [{elapsed:.1f}s] Reply contains status summary")
        return False

    # 检查内容长度（实质方案应 >300 字）
    if len(expected_keywords) > 2 and len(reply) < 300:
        print(f"❌ FAIL [{elapsed:.1f}s] Reply too short ({len(reply)} chars)")
        return False

    print(f"✅ PASS [{elapsed:.1f}s] '{user_input[:30]}...'")
    return True


async def run_all():
    """运行所有 E2E 测试"""
    # 先检查服务健康
    if not await check_health():
        print(f"⚠️  SKIP: CEO 服务不可用 ({HEALTH_URL})")
        print("请先启动服务: docker compose up -d")
        sys.exit(0)  # SKIP 而非 FAIL

    print(f"\n{'='*60}")
    print(f"飞书端到端冒烟测试 — {HERMES_URL}")
    print(f"{'='*60}\n")

    passed = 0
    failed = 0

    for inp, kws, tout in E2E_CASES:
        ok = await test_case(inp, kws, tout)
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"结果: {passed} passed, {failed} failed, {passed + failed} total")
    print(f"{'='*60}\n")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_all())
