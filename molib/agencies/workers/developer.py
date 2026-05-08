"""墨码开发 Worker — 软件开发、代码编写

所属: VP技术
技能: agent-engineering-backend-architect, cli-anything
"""
from .base import SubsidiaryWorker, Task, WorkerResult

class Developer(SubsidiaryWorker):
    worker_id = "developer"
    worker_name = "墨码开发"
    description = "软件开发、代码编写"
    oneliner = "软件开发、代码编写"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "代码生成与自动化PR",
            "多语言开发（Python/TS/Go等）",
            "架构设计与代码审查",
            "技术方案评估与选型",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨码开发",
            "vp": "技术",
            "description": "软件开发、代码编写",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            requirement = task.payload.get("requirement", "未指定")
            tech_stack = task.payload.get("tech_stack", ["python", "fastapi"])
            language = task.payload.get("language", tech_stack[0] if tech_stack else "python")
            complexity = task.payload.get("complexity", "中等")

            system = (
                "你是墨码开发——墨麟AI集团旗下的专业软件开发子公司。"
                "你的专长是：代码生成与自动化PR、多语言开发（Python/TypeScript/Go/Rust/Java等）、"
                "架构设计与代码审查、技术方案评估与选型。"
                "你精通Clean Architecture、DDD、微服务、RESTful API设计等最佳实践。"
                "请输出结构化的技术方案供开发团队执行。"
            )
            prompt = (
                f"请为以下需求生成一个完整的技术方案：\n\n"
                f"需求描述：{requirement}\n"
                f"技术栈：{', '.join(tech_stack)}\n"
                f"主要语言：{language}\n"
                f"复杂度：{complexity}\n\n"
                f"请输出JSON格式，包含：\n"
                f"- requirement（需求描述）\n"
                f"- tech_stack（技术栈数组）\n"
                f"- architecture（架构设计，含：pattern架构模式, layers层级数组, description描述）\n"
                f"- files（文件列表，每项含：path路径, purpose用途, estimated_lines估计行数）\n"
                f"- key_components（关键组件列表，每项含：name名称, responsibility职责）\n"
                f"- design_decisions（设计决策说明）\n"
                f"- estimated_effort（预估工作量）\n"
                f"- risks（潜在风险与缓解方案）"
            )

            result = await self.llm_chat_json(prompt, system=system)
            if result:
                output = {
                    "requirement": result.get("requirement", requirement),
                    "tech_stack": result.get("tech_stack", tech_stack),
                    "architecture": result.get("architecture", {
                        "pattern": "Clean Architecture",
                        "layers": ["domain", "application", "infrastructure"],
                        "description": "标准分层架构",
                    }),
                    "files": result.get("files", []),
                    "key_components": result.get("key_components", []),
                    "design_decisions": result.get("design_decisions", ""),
                    "estimated_effort": result.get("estimated_effort", "待评估"),
                    "risks": result.get("risks", []),
                    "status": "tech_design_ready",
                    "source": "llm",
                }
            else:
                # fallback: 原有 mock 输出
                output = {
                    "requirement": requirement,
                    "tech_stack": tech_stack,
                    "architecture": {
                        "pattern": "Clean Architecture",
                        "layers": ["domain", "application", "infrastructure"],
                    },
                    "files": [
                        {"path": "src/main.py", "lines": 50},
                        {"path": "src/models.py", "lines": 80},
                    ],
                    "status": "code_plan_ready",
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
