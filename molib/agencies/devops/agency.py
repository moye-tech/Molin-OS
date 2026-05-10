"""墨维运维子公司 — 系统健康监控、自动故障恢复、性能调优、Docker容器管理"""
import json
import time
from pathlib import Path

from molib.agencies.base import BaseAgency, Task, AgencyResult

DEVOPS_SYSTEM_PROMPT = """你是墨维运维子公司的运维工程师。
根据需求进行系统监控、故障响应、性能调优或部署操作。

输出必须是严格的 JSON 格式：
{
  "ops_type": "monitoring|incident|performance|deployment",
  "service_status": "healthy|degraded|critical|unknown",
  "affected_services": ["受影响服务1", "受影响服务2"],
  "diagnosis": "诊断分析",
  "action_taken": "已执行操作",
  "recommended_actions": [
    {"action": "操作", "priority": "high|medium|low", "command": "命令(如有)"}
  ],
  "prevention_measures": ["预防措施1", "预防措施2"],
  "quality_score": 质量评分(1-10)
}"""

PROMPTS_DIR = Path(__file__).parent / "prompts"
WORKER_PROMPTS = {}
for _wt, _wf in {
    "health_monitor": "health_monitor.txt",
    "incident_responder": "incident_responder.txt",
    "performance_tuner": "performance_tuner.txt",
    "deploy_engineer": "deploy_engineer.txt",
}.items():
    _fp = PROMPTS_DIR / _wf
    if _fp.exists():
        WORKER_PROMPTS[_wt] = _fp.read_text(encoding="utf-8")


class DevopsAgency(BaseAgency):
    agency_id = "devops"
    trigger_keywords = ["部署", "宕机", "服务异常", "性能", "监控", "容器", "重启", "运维", "服务器", "Docker", "故障", "异常"]
    approval_level = "medium"
    cost_level = "medium"

    def _select_worker(self, desc: str) -> str:
        desc_l = desc.lower()
        if any(k in desc_l for k in ["故障", "宕机", "异常", "恢复", "incident"]):
            return "incident_responder"
        if any(k in desc_l for k in ["性能", "优化", "调优", "慢", "延迟"]):
            return "performance_tuner"
        if any(k in desc_l for k in ["部署", "升级", "发布", "回滚", "docker"]):
            return "deploy_engineer"
        return "health_monitor"

    def _parse_devops_json(self, text: str) -> dict:
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            if "```json" in text:
                try:
                    start = text.index("```json") + 7
                    end = text.index("```", start)
                    return json.loads(text[start:end].strip())
                except Exception:
                    pass
        return {
            "ops_type": "monitoring",
            "service_status": "unknown",
            "affected_services": [],
            "diagnosis": text[:300],
            "action_taken": "",
            "recommended_actions": [],
            "prevention_measures": [],
            "quality_score": 5.0,
        }

    async def execute(self, task: Task) -> AgencyResult:
        desc = task.payload.get("description", "")
        worker_type = self._select_worker(desc)

        system_prompt = WORKER_PROMPTS.get(worker_type, DEVOPS_SYSTEM_PROMPT)
        system_prompt += "\n\n" + DEVOPS_SYSTEM_PROMPT

        start = time.time()
        res = await self.router.call_async(
            prompt=desc, system=system_prompt,
            task_type="devops", team="devops",
        )
        parsed = self._parse_devops_json(res.get("text", ""))

        score = parsed.get("quality_score", 5.0)
        return AgencyResult(
            task_id=task.task_id, agency_id=self.agency_id, status="success",
            output={
                "ops_type": parsed.get("ops_type", "monitoring"),
                "service_status": parsed.get("service_status", "unknown"),
                "affected_services": parsed.get("affected_services", []),
                "diagnosis": parsed.get("diagnosis", ""),
                "recommended_actions": parsed.get("recommended_actions", []),
                "prevention_measures": parsed.get("prevention_measures", []),
                "worker_type": worker_type,
                "quality_score": score,
                "model_used": res.get("model", "unknown"),
            },
            cost=res.get("cost", 0.0),
            latency=round(time.time() - start, 2),
        )
