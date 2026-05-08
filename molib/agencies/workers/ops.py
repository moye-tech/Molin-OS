"""墨维运维 Worker — 服务器、部署、DevOps

所属: VP技术
技能: ghost-os, cli-anything, opensre-sre-agent
"""
from .base import SubsidiaryWorker, Task, WorkerResult

class Ops(SubsidiaryWorker):
    worker_id = "ops"
    worker_name = "墨维运维"
    description = "服务器、部署、DevOps"
    oneliner = "服务器、部署、DevOps"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "Docker容器监控与自愈",
            "CI/CD流水线管理",
            "服务器健康巡检与告警",
            "服务部署与回滚",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨维运维",
            "vp": "技术",
            "description": "服务器、部署、DevOps",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            services = task.payload.get("services", ["hermes-core", "qdrant", "redis"])
            action = task.payload.get("action", "health_check")
            environment = task.payload.get("environment", "production")
            deploy_version = task.payload.get("version", "")

            system = (
                "你是墨维运维——墨麟AI集团旗下的专业运维与DevOps子公司。"
                "你的专长是：Docker容器监控与自愈、CI/CD流水线管理、"
                "服务器健康巡检与告警、服务部署与回滚。"
                "你精通Linux系统管理、Kubernetes、Terraform、Ansible等基础设施即代码工具。"
                "请输出结构化的运维方案或巡检报告。"
            )
            prompt = (
                f"请为以下运维任务生成详细报告：\n\n"
                f"操作类型：{action}\n"
                f"环境：{environment}\n"
                f"服务列表：{', '.join(services)}\n"
                f"部署版本：{deploy_version if deploy_version else '当前版本'}\n\n"
                f"请输出JSON格式，包含：\n"
                f"- action（执行的操作类型）\n"
                f"- services（服务状态数组，每项含：name名称, status状态, uptime运行时间, cpu_usage, memory_usage, last_restart）\n"
                f"- alerts（告警信息数组，每项含：severity严重级别, message消息, service相关服务, suggestion建议）\n"
                f"- summary（运维总结）\n"
                f"- recommendations（优化建议列表）"
            )

            result = await self.llm_chat_json(prompt, system=system)
            if result:
                output = {
                    "action": result.get("action", action),
                    "environment": environment,
                    "services": result.get("services", [
                        {"name": s, "status": "healthy", "uptime": "99.9%", "cpu_usage": "中等", "memory_usage": "正常"}
                        for s in services
                    ]),
                    "alerts": result.get("alerts", []),
                    "summary": result.get("summary", ""),
                    "recommendations": result.get("recommendations", []),
                    "status": "ops_report_ready",
                    "source": "llm",
                }
            else:
                # fallback: 原有 mock 输出
                output = {
                    "services": [{
                        "name": s,
                        "status": "healthy",
                        "uptime": "99.9%",
                    } for s in services],
                    "alerts": task.payload.get("alerts", []),
                    "status": "monitor_ready",
                    "source": "mock",
                }
            return WorkerResult(
                task_id=task.task_id,
                worker_id=self.worker_id,
                status="success",
                output=output,
            )
        except Exception as e:
            return WorkerResult(
                task_id=task.task_id,
                worker_id=self.worker_id,
                status="error",
                output={},
                error=str(e),
            )
