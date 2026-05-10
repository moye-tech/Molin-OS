#!/usr/bin/env python3
"""
墨麟AI v6.6 — 全子公司 + 全工具穷举验证脚本
逐一触发 20 个子公司，验证 CEO → Manager/LLM → Worker → Tools 全链路。

用法: python3 tests/full_system_test.py
"""

import asyncio
import json
import sys
import time

import httpx

BASE_URL = "http://localhost:28000"

TESTS = [
    # === 有 Manager 的 12 个子公司 ===
    {"id": "test-edu-001",     "agency": "edu",     "has_manager": True,
     "input": "帮我设计一套AI培训课程的招生方案，包含课程大纲、完课率提升策略和训练营招生话术"},
    {"id": "test-order-002",   "agency": "order",   "has_manager": True,
     "input": "请帮我给客户写一份项目报价方案，包含交付周期和合同条款，客户需要一个完整的报价"},
    {"id": "test-ip-003",      "agency": "ip",      "has_manager": True,
     "input": "帮我写一篇小红书爆款文案，主题是AI工具推荐，需要吸引人的标题和脚本内容"},
    {"id": "test-dev-004",     "agency": "dev",     "has_manager": True,
     "input": "帮我开发一个Python自动化部署Docker的脚本，包含API调用和bug修复功能"},
    {"id": "test-ai-005",      "agency": "ai",      "has_manager": True,
     "input": "帮我设计一个RAG知识库的Agent方案，包含Prompt提示词工程和AI咨询建议"},
    {"id": "test-shop-006",    "agency": "shop",    "has_manager": True,
     "input": "帮我制定一套电商定价策略，包含成交话术和私域转化方案"},
    {"id": "test-data-007",    "agency": "data",    "has_manager": True,
     "input": "帮我分析上个月的运营数据报表，计算ROI、CAC、LTV指标，生成漏斗分析"},
    {"id": "test-ads-008",     "agency": "ads",     "has_manager": True,
     "input": "帮我制定广告投放计划，包含CAC优化、出价策略和广告素材创意"},
    {"id": "test-growth-009",  "agency": "growth",  "has_manager": True,
     "input": "帮我设计一个用户增长裂变方案，包含渠道拓展、转介绍机制和A/B测试实验"},
    {"id": "test-secure-010",  "agency": "secure",  "has_manager": True,
     "input": "帮我做一次安全合规审查，检查权限设置、隐私合规和广告法合规性"},
    {"id": "test-research-011","agency": "research","has_manager": True,
     "input": "帮我做一份竞品市场调研报告，分析行业趋势和竞争对手情报"},
    {"id": "test-product-012", "agency": "product", "has_manager": True,
     "input": "帮我把AI功能产品化，设计一个SaaS标准化MVP，包含模板打包方案"},
    # === 无 Manager 的 8 个子公司（LLM fallback） ===
    {"id": "test-finance-013", "agency": "finance", "has_manager": False,
     "input": "帮我做一份财务成本分析，包含预算规划、利润核算和ROI盈亏评估"},
    {"id": "test-crm-014",     "agency": "crm",     "has_manager": False,
     "input": "帮我制定私域用户运营方案，包含会员复购激活、RFM用户分层和流失预警"},
    {"id": "test-knowledge-015","agency": "knowledge","has_manager": False,
     "input": "帮我做一次项目复盘总结，提炼最佳实践经验，更新SOP文档归档到知识库"},
    {"id": "test-cs-016",      "agency": "cs",      "has_manager": False,
     "input": "帮我处理用户投诉和退款问题，制定客服应答话术和用户反馈闭环方案"},
    {"id": "test-legal-017",   "agency": "legal",   "has_manager": False,
     "input": "帮我审查一份外包合同的版权合规条款，起草NDA协议和隐私政策"},
    {"id": "test-bd-018",      "agency": "bd",      "has_manager": False,
     "input": "帮我制定商务合作谈判策略，包含合作方资质筛查和外包项目报价方案"},
    {"id": "test-global-019",  "agency": "global",  "has_manager": False,
     "input": "帮我制定出海东南亚的内容本地化方案，包含繁体翻译和TikTok海外运营"},
    {"id": "test-devops-020",  "agency": "devops",  "has_manager": False,
     "input": "帮我排查服务器宕机故障，检查Docker容器性能和内存监控，制定运维重启方案"},
]


def check_response(resp: dict, test: dict) -> list:
    """检查响应，返回 (passed, issues) 列表"""
    issues = []

    # 基本检查
    if resp.get("decision") not in ("GO", "DIRECT_RESPONSE"):
        issues.append(f"decision={resp.get('decision')}, 期望 GO 或 DIRECT_RESPONSE")

    # target_agency 检查（LLM 可能输出不同的 agency）
    actual_agency = resp.get("target_agency", "")
    expected = test["agency"]
    if actual_agency != expected:
        issues.append(f"target_agency={actual_agency}, 期望={expected}")

    # execution_result 检查
    exec_result = resp.get("execution_result")
    if not exec_result:
        issues.append("execution_result 缺失")
    else:
        status = exec_result.get("status", "")
        results = exec_result.get("results", [])

        if test["has_manager"]:
            if status != "executed":
                issues.append(f"execution_result.status={status}, 期望=executed")
        else:
            if status == "skipped":
                issues.append(f"execution_result.status=skipped, 期望=llm_executed (reason: {exec_result.get('reason', '')})")

        # 检查输出是否为空
        if results:
            for r in results:
                output = r.get("output", "")
                if not output or len(output) < 20:
                    issues.append(f"输出过短 (len={len(output)})")

    # message 检查
    msg = resp.get("message", "")
    if not msg or len(msg) < 5:
        issues.append("message 过短或缺失")

    return issues


async def run_test(client: httpx.AsyncClient, test: dict, timeout: int = 120) -> dict:
    """运行单个测试"""
    start = time.time()
    try:
        resp = await client.post(
            f"{BASE_URL}/api/chat",
            json={"input": test["input"], "session_id": test["id"]},
            timeout=timeout,
        )
        elapsed = time.time() - start
        data = resp.json()
        issues = check_response(data, test)
        return {
            "id": test["id"],
            "agency": test["agency"],
            "passed": len(issues) == 0,
            "issues": issues,
            "decision": data.get("decision", "N/A"),
            "target_agency": data.get("target_agency", "N/A"),
            "exec_status": data.get("execution_result", {}).get("status", "N/A"),
            "latency": round(elapsed, 2),
            "message_preview": data.get("message", "")[:80],
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "id": test["id"],
            "agency": test["agency"],
            "passed": False,
            "issues": [f"请求异常: {e}"],
            "decision": "N/A",
            "target_agency": "N/A",
            "exec_status": "N/A",
            "latency": round(elapsed, 2),
            "message_preview": "",
        }


def print_results(results: list):
    """打印汇总报告"""
    print("\n" + "=" * 90)
    print("墨麟AI v6.6 — 全系统验证报告")
    print("=" * 90)

    passed = 0
    failed = 0

    # 分组打印
    print(f"\n{'#':>2} {'子公司':<12} {'ID':<22} {'Decision':<16} {'Exec Status':<16} {'耗时':<10} {'状态':<8}")
    print("-" * 90)

    for i, r in enumerate(results, 1):
        status_icon = "PASS" if r["passed"] else "FAIL"
        if r["passed"]:
            passed += 1
        else:
            failed += 1

        print(f"{i:>2} {r['agency']:<12} {r['id']:<22} {r['decision']:<16} {r['exec_status']:<16} {r['latency']:<10} {status_icon:<8}")

    print("-" * 90)
    total = len(results)
    print(f"\n总计: {total} 个测试 | 通过: {passed} | 失败: {failed} | 通过率: {passed/total*100:.0f}%")

    # 打印失败详情
    failed_results = [r for r in results if not r["passed"]]
    if failed_results:
        print(f"\n失败详情:")
        for r in failed_results:
            print(f"\n  ❌ {r['id']} ({r['agency']}):")
            for issue in r["issues"]:
                print(f"     - {issue}")

    print("\n" + "=" * 90)


async def main():
    print("墨麟AI v6.6 — 全系统验证开始")
    print(f"共 {len(TESTS)} 个测试，分 {len(TESTS) // 4 + 1} 批并发执行\n")

    batch_size = 1  # 逐个测试，避免限流
    all_results = []

    async with httpx.AsyncClient(timeout=120.0) as client:
        for batch_start in range(0, len(TESTS), batch_size):
            batch = TESTS[batch_start:batch_start + batch_size]
            batch_num = batch_start // batch_size + 1
            agencies = [t["agency"] for t in batch]
            print(f"批次 {batch_num}: {', '.join(agencies)} ...")

            # 并发执行当前批次
            tasks = [run_test(client, t) for t in batch]
            results = await asyncio.gather(*tasks)
            all_results.extend(results)

            # 打印当前批次结果
            for r in results:
                icon = "PASS" if r["passed"] else "FAIL"
                print(f"  {icon} {r['agency']}: decision={r['decision']}, exec={r['exec_status']}, {r['latency']}s")
                if not r["passed"]:
                    for issue in r["issues"]:
                        print(f"       - {issue}")

    # 打印完整报告
    print_results(all_results)

    # 判断退出码
    failed = sum(1 for r in all_results if not r["passed"])
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    asyncio.run(main())
