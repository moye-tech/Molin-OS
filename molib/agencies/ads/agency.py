import json
import asyncio
import time
from datetime import datetime, date
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List

from ..base import AgencyResult, BaseAgency, Task

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "ads_system.txt"
if PROMPT_PATH.exists():
    SYSTEM = PROMPT_PATH.read_text(encoding="utf-8")
else:
    SYSTEM = """你是广告投放专家，负责管理墨麟的广告账户。
你的目标：以最低的CAC获取最高质量的线索和转化。
决策规则：
- ROI ≥ 3.0 → SCALE（立即扩大投入）
- ROI 1.5–3.0 → OPTIMIZE（保持并优化）
- ROI 1.0–1.5 → MONITOR（观察）
- ROI < 1.0 → STOP（停止）
- CAC > 目标值 × 1.5 → ALERT
- CAC > 目标值 × 2.0 → STOP

输出格式：
{
  "summary": "一句话总结",
  "cac_status": "OK/OVER/CRITICAL",
  "roi_decision": "SCALE/OPTIMIZE/MONITOR/STOP",
  "top_issues": ["问题1", "问题2"],
  "actions": [{"action": "操作", "reason": "原因", "priority": "high/medium/low"}],
  "next_review": "明日关注重点"
}"""

@dataclass
class AdsMetrics:
    date: str
    spend_cny: float
    leads: int
    m0_orders: int
    m1_orders: int
    m2_orders: int
    cac_cny: float
    roi: float
    ctr: float
    cvr: float

class AdsAgency(BaseAgency):
    agency_id = "ads"
    trigger_keywords = ["广告", "投放", "CAC", "出价", "竞价", "创意", "素材", "M0", "M1", "M2", "广告费", "获客成本"]
    approval_level = "high"
    cost_level = "medium"

    def __init__(self):
        super().__init__()
        self.target_cac_cny = 80.0  # 默认值，可从配置读取
        self.daily_budget_cny = 300.0  # 默认值

    async def execute(self, task: Task) -> AgencyResult:
        start_time = time.time()
        task_str = task.payload.get("task", "") if isinstance(task.payload, dict) else str(task.payload)

        task_type = self._detect_task_type(task_str)

        try:
            if task_type == "daily_report":
                result = await self._generate_daily_report()
            elif task_type == "optimize":
                result = await self._optimize_campaign(task.payload if isinstance(task.payload, dict) else {})
            elif task_type == "scale_decision":
                result = await self._make_scale_decision(task.payload if isinstance(task.payload, dict) else {})
            elif task_type == "creative_analysis":
                result = await self._analyze_creatives(task.payload if isinstance(task.payload, dict) else {})
            else:
                result = await self._general_ads_task(task_str)

            return AgencyResult(
                task_id=task.task_id,
                agency_id=self.agency_id,
                status="success",
                output=result,
                cost=0.05,  # 模拟成本
                latency=round(time.time() - start_time, 2)
            )
        except Exception as e:
            return AgencyResult(
                task_id=task.task_id,
                agency_id=self.agency_id,
                status="error",
                output={"error": str(e)},
                error=str(e),
                cost=0.0,
                latency=round(time.time() - start_time, 2)
            )

    def _detect_task_type(self, task: str) -> str:
        task_lower = task.lower()
        if any(k in task_lower for k in ['日报', '每日', '今日广告', 'daily', 'report']):
            return "daily_report"
        if any(k in task_lower for k in ['优化', '出价', '调整', 'optimize', 'bid']):
            return "optimize"
        if any(k in task_lower for k in ['扩量', 'scale', '放量', '扩大']):
            return "scale_decision"
        if any(k in task_lower for k in ['素材', '创意', '文案效果', 'creative', 'content']):
            return "creative_analysis"
        return "general"

    async def _generate_daily_report(self) -> Dict[str, Any]:
        """生成广告日报"""
        # 模拟获取广告数据 - 实际实现中应连接广告平台API
        metrics = await self._fetch_metrics()

        # 计算状态
        cac_status = "OK"
        if metrics.cac_cny > self.target_cac_cny * 1.5:
            cac_status = "OVER"
        elif metrics.cac_cny > self.target_cac_cny * 2.0:
            cac_status = "CRITICAL"

        roi_status = "SCALE"
        if metrics.roi >= 3.0:
            roi_status = "SCALE"
        elif metrics.roi >= 1.5:
            roi_status = "OPTIMIZE"
        elif metrics.roi >= 1.0:
            roi_status = "MONITOR"
        else:
            roi_status = "STOP"

        prompt = f"""
你是广告分析师。请基于以下数据生成简洁的广告日报：
今日数据：
- 消耗：¥{metrics.spend_cny:.2f}
- 线索数：{metrics.leads}
- M0转化单：{metrics.m0_orders}
- M1转化单：{metrics.m1_orders}
- M2转化单：{metrics.m2_orders}
- CAC：¥{metrics.cac_cny:.2f}（目标：¥{self.target_cac_cny}，状态：{cac_status}）
- ROI：{metrics.roi:.2f}（决策：{roi_status}）
- CTR：{metrics.ctr:.2%}
- CVR：{metrics.cvr:.2%}

请输出JSON格式：
{{
  "summary": "一句话总结",
  "cac_status": "{cac_status}",
  "roi_decision": "{roi_status}",
  "top_issues": ["问题1", "问题2"],
  "actions": [{{"action": "具体操作", "reason": "原因", "priority": "high/medium/low"}}],
  "next_review": "明日关注重点"
}}
"""
        response = await self.router.call_async(prompt=prompt, system=SYSTEM, task_type="ads_analysis", team="ads")

        try:
            result = json.loads(response["text"])
        except json.JSONDecodeError:
            result = {
                "summary": f"今日广告消耗¥{metrics.spend_cny:.2f}，ROI={metrics.roi:.2f}",
                "cac_status": cac_status,
                "roi_decision": roi_status,
                "top_issues": ["数据解析失败，请检查格式"],
                "actions": [{"action": "检查广告API连接", "reason": "数据格式异常", "priority": "high"}],
                "next_review": "修复数据连接"
            }

        # 模拟推送到飞书（实际实现中应调用飞书API）
        await self._push_to_feishu(result, metrics)

        return result

    async def _optimize_campaign(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """优化广告活动"""
        metrics = await self._fetch_metrics(days=3)
        avg_roi = sum(m.roi for m in metrics) / len(metrics) if metrics else 0
        avg_cac = sum(m.cac_cny for m in metrics) / len(metrics) if metrics else 999

        prompt = f"""
广告活动优化分析：
- 3日平均ROI：{avg_roi:.2f}
- 3日平均CAC：¥{avg_cac:.2f}
- 目标CAC：¥{self.target_cac_cny}
- 当前状态：{'需优化' if avg_roi < 2.0 or avg_cac > self.target_cac_cny else '良好'}

请提供优化建议，输出JSON格式：
{{
  "analysis": "问题分析",
  "recommendations": ["建议1", "建议2", "建议3"],
  "expected_impact": "预期改善",
  "risk": "潜在风险"
}}
"""
        response = await self.router.call_async(prompt=prompt, system=SYSTEM, task_type="ads_optimization", team="ads")

        try:
            return json.loads(response["text"])
        except json.JSONDecodeError:
            return {
                "analysis": f"ROI={avg_roi:.2f}, CAC=¥{avg_cac:.2f}",
                "recommendations": ["调整出价策略", "测试新创意", "优化受众定位"],
                "expected_impact": "预计ROI提升20-30%",
                "risk": "测试期间成本可能暂时上升"
            }

    async def _make_scale_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """做出扩量决策"""
        metrics = await self._fetch_recent_metrics(days=7)
        avg_roi = sum(m.roi for m in metrics) / len(metrics) if metrics else 0
        avg_cac = sum(m.cac_cny for m in metrics) / len(metrics) if metrics else 999

        if avg_roi >= 3.0 and avg_cac <= self.target_cac_cny:
            decision = "SCALE"
            recommendation = f"7日平均ROI={avg_roi:.2f}，CAC=¥{avg_cac:.2f}，建议扩量30-50%"
        elif avg_roi >= 1.5:
            decision = "OPTIMIZE"
            recommendation = "ROI达标但有优化空间，建议小幅测试新素材"
        else:
            decision = "HOLD"
            recommendation = f"ROI={avg_roi:.2f}未达标，建议保持现状或优化"

        return {
            "decision": decision,
            "reason": recommendation,
            "metrics": {
                "avg_roi_7d": round(avg_roi, 2),
                "avg_cac_7d": round(avg_cac, 2),
                "target_cac": self.target_cac_cny
            },
            "action": "扩量" if decision == "SCALE" else "优化" if decision == "OPTIMIZE" else "保持"
        }

    async def _analyze_creatives(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """分析广告创意"""
        prompt = """
分析当前广告创意表现，包括：
1. 文案吸引力
2. 图片/视频质量
3. 受众匹配度
4. 转化路径清晰度

请提供创意优化建议，输出JSON格式：
{
  "strengths": ["优势1", "优势2"],
  "weaknesses": ["弱点1", "弱点2"],
  "optimization_ideas": ["优化想法1", "优化想法2"],
  "test_variants": ["变体A描述", "变体B描述"]
}
"""
        response = await self.router.call_async(prompt=prompt, system=SYSTEM, task_type="creative_analysis", team="ads")

        try:
            return json.loads(response["text"])
        except json.JSONDecodeError:
            return {
                "strengths": ["文案简洁明了", "视觉吸引力强"],
                "weaknesses": ["行动号召不明确", "目标受众不够精准"],
                "optimization_ideas": ["增加紧迫感文案", "测试不同图片风格"],
                "test_variants": ["强调节省时间", "强调赚钱效果"]
            }

    async def _general_ads_task(self, task: str) -> Dict[str, Any]:
        """处理一般广告任务"""
        prompt = f"""
处理以下广告相关任务：{task}

请提供专业建议和执行方案，输出JSON格式：
{{
  "understanding": "对任务的理解",
  "approach": "执行方法",
  "steps": ["步骤1", "步骤2", "步骤3"],
  "estimated_cost_cny": 0.00,
  "expected_roi": 0.00,
  "risks": ["风险1", "风险2"]
}}
"""
        response = await self.router.call_async(prompt=prompt, system=SYSTEM, task_type="ads_general", team="ads")

        try:
            return json.loads(response["text"])
        except json.JSONDecodeError:
            return {
                "understanding": f"处理广告任务：{task}",
                "approach": "常规广告优化流程",
                "steps": ["分析现状", "制定策略", "执行优化", "监控效果"],
                "estimated_cost_cny": 50.0,
                "expected_roi": 2.5,
                "risks": ["平台政策变化", "竞争加剧"]
            }

    async def _fetch_metrics(self, days: int = 1) -> AdsMetrics:
        """从 SQLite/Redis 读取真实广告指标，失败时回退到模拟数据"""
        today = date.today().isoformat()
        # 1. 优先从 SQLite 读取真实数据
        try:
            from molib.infra.memory.sqlite_client import SQLiteClient
            db = SQLiteClient()
            rows = await db.get_ads_metrics(days=days)
            if rows:
                r = rows[0]
                return AdsMetrics(
                    date=r["date"],
                    spend_cny=float(r["spend_cny"]),
                    leads=int(r["leads"]),
                    m0_orders=int(r["m0"]),
                    m1_orders=int(r["m1"]),
                    m2_orders=int(r["m2"]),
                    cac_cny=float(r["cac_cny"]),
                    roi=float(r["roi"]),
                    ctr=float(r["ctr"]),
                    cvr=float(r["cvr"]),
                )
        except Exception as e:
            logger.warning(f"广告数据读取失败，使用模拟数据: {e}")

        # 2. Fallback: 模拟数据（SQLite/Redis 不可用时）
        return AdsMetrics(
            date=today, spend_cny=150.0, leads=25, m0_orders=5, m1_orders=2,
            m2_orders=1, cac_cny=30.0, roi=2.8, ctr=0.045, cvr=0.20,
        )

    async def _fetch_recent_metrics(self, days: int = 7) -> List[AdsMetrics]:
        """从 SQLite 读取近 N 天广告指标，失败时回退到模拟数据"""
        try:
            from molib.infra.memory.sqlite_client import SQLiteClient
            db = SQLiteClient()
            rows = await db.get_ads_metrics(days=days)
            if rows:
                metrics = []
                for r in rows:
                    metrics.append(AdsMetrics(
                        date=r["date"],
                        spend_cny=float(r["spend_cny"]),
                        leads=int(r["leads"]),
                        m0_orders=int(r["m0"]),
                        m1_orders=int(r["m1"]),
                        m2_orders=int(r["m2"]),
                        cac_cny=float(r["cac_cny"]),
                        roi=float(r["roi"]),
                        ctr=float(r["ctr"]),
                        cvr=float(r["cvr"]),
                    ))
                return metrics
        except Exception as e:
            logger.warning(f"广告近期数据读取失败，使用模拟数据: {e}")

        # Fallback: 模拟数据（SQLite 不可用时）
        metrics = []
        for i in range(days):
            day = date.fromordinal(date.today().toordinal() - i).isoformat()
            metrics.append(AdsMetrics(
                date=day,
                spend_cny=120.0 + i * 5,
                leads=20 + i,
                m0_orders=4 + (i % 3),
                m1_orders=2,
                m2_orders=1,
                cac_cny=25.0 + i * 0.5,
                roi=2.5 + i * 0.1,
                ctr=0.04 + i * 0.001,
                cvr=0.18 + i * 0.005
            ))
        return metrics

    async def _push_to_feishu(self, report: Dict[str, Any], metrics: AdsMetrics) -> None:
        """推送广告报告到飞书 — 使用交互式卡片"""
        try:
            from molib.integrations.feishu.bridge import push_approval_card
            # 构建飞书卡片内容
            summary = (
                f"广告日报 {metrics.date}\n"
                f"消耗: ¥{metrics.spend_cny:.2f} | 线索: {metrics.leads}\n"
                f"ROI: {metrics.roi:.2f} | CAC: ¥{metrics.cac_cny:.2f}\n"
                f"CTR: {metrics.ctr:.2%} | CVR: {metrics.cvr:.2%}"
            )
            # 推送到飞书（使用信息类卡片，非审批卡片）
            import os
            import httpx
            from molib.integrations.feishu.token_manager import get_feishu_token
            token = await get_feishu_token()
            if not token:
                logger.warning("飞书 Token 不可用，跳过推送")
                return
            chat_id = os.getenv("FEISHU_ADS_CHAT_ID") or os.getenv("FEISHU_APPROVAL_CHAT_ID")
            if not chat_id:
                logger.debug("未配置飞书广告群聊 ID，跳过推送")
                return
            card = {
                "header": {"title": {"tag": "plain_text", "content": "广告日报"}, "template": "blue"},
                "elements": [
                    {"tag": "div", "text": {"tag": "lark_md", "content": summary}},
                    {"tag": "hr"},
                    {"tag": "note", "elements": [
                        {"tag": "plain_text", "content": f"墨麟 AI · {report.get('generated_at', 'auto')}"}
                    ]},
                ],
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json={"receive_id": chat_id, "msg_type": "interactive", "content": str(card)},
                )
                if resp.status_code == 200:
                    logger.info(f"广告报告已推送飞书: {metrics.date}")
                else:
                    logger.warning(f"飞书推送失败: {resp.status_code} {resp.text}")
        except Exception as e:
            logger.warning(f"飞书推送异常（非致命）: {e}")