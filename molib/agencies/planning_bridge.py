"""
墨麟OS v2.0 — PlanningBridge Plan与执行流绑定
解决 BUG-06 (Planning孤立)
"""
from pathlib import Path
import json
from datetime import datetime


class PlanningBridge:
    """将Planning系统桥接到Worker执行流"""

    WORKER_DESCRIPTIONS = {
        "research":       "墨研竞情: 竞品/趋势分析",
        "content_writer": "墨笔文创: 内容创作",
        "designer":       "墨图设计: 视觉设计",
        "ecommerce":      "墨链电商: 上架发布",
        "short_video":    "墨播短视频: 视频制作",
        "legal":          "墨律法务: 合同审查",
        "finance":        "墨算财务: 财务分析",
        "education":      "墨学教育: 课程设计",
        "developer":      "墨码开发: 软件开发",
        "customer_service": "墨声客服: 客户服务",
        "global_marketing": "墨海出海: 全球化运营",
        "data_analyst":   "墨测数据: 数据分析",
        "security":       "墨安安全: 安全审计",
        "ops":            "墨维运维: 部署运维",
        "bd":             "墨商BD: 商务拓展",
        "crm":            "墨域私域: 客户管理",
        "ip_manager":     "墨韵IP: 品牌管理",
        "knowledge":      "墨脑知识: 知识管理",
        "voice_actor":    "墨声配音: 语音合成",
        "auto_dream":     "墨梦AutoDream: AI实验",
    }

    @staticmethod
    def create_chain_plan(task, worker_ids: list) -> str:
        """SmartDispatcher启动WorkerChain时自动创建执行计划"""
        desc = PlanningBridge.WORKER_DESCRIPTIONS
        title = str(getattr(task, 'payload', task))[:48]
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        plan = {
            "id": plan_id,
            "title": title,
            "created_at": datetime.now().isoformat(),
            "todos": [
                {
                    "id": f"{plan_id}_s{i}",
                    "content": desc.get(wid, wid),
                    "worker_id": wid,
                    "status": "pending",
                }
                for i, wid in enumerate(worker_ids)
            ]
        }

        plan_dir = Path.home() / ".hermes" / "plans"
        plan_dir.mkdir(parents=True, exist_ok=True)
        (plan_dir / f"{plan_id}.json").write_text(
            json.dumps(plan, ensure_ascii=False, indent=2)
        )
        return plan_id

    @staticmethod
    def mark_step_done(plan_id: str, worker_id: str):
        """WorkerChain每步完成后调用"""
        plan_dir = Path.home() / ".hermes" / "plans"
        plan_file = plan_dir / f"{plan_id}.json"
        if not plan_file.exists():
            return

        plan = json.loads(plan_file.read_text())
        desc = PlanningBridge.WORKER_DESCRIPTIONS.get(worker_id, worker_id)
        for todo in plan.get("todos", []):
            if worker_id in todo.get("content", "") or desc[:6] in todo.get("content", ""):
                todo["status"] = "completed"
                todo["completed_at"] = datetime.now().isoformat()
                break
        plan_file.write_text(json.dumps(plan, ensure_ascii=False, indent=2))

    @staticmethod
    def get_plan_status(plan_id: str) -> dict:
        """查询计划执行状态"""
        plan_file = Path.home() / ".hermes" / "plans" / f"{plan_id}.json"
        if not plan_file.exists():
            return {"error": "plan not found"}
        return json.loads(plan_file.read_text())
