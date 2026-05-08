"""墨图设计 Worker — 图片/UI/封面/视觉设计

所属: VP营销
技能: molin-design, excalidraw, pixel-art
"""
from .base import SubsidiaryWorker, Task, WorkerResult

class Designer(SubsidiaryWorker):
    worker_id = "designer"
    worker_name = "墨图设计"
    description = "图片/UI/封面/视觉设计"
    oneliner = "图片/UI/封面/视觉设计"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "封面图与海报设计",
            "UI界面视觉设计",
            "多风格输出（商务/卡通/插画）",
            "批量化图片生成与排版",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨图设计",
            "vp": "营销",
            "description": "图片/UI/封面/视觉设计",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            design_type = task.payload.get("type", "封面图")
            specs = task.payload.get("specs", {"尺寸": "1080x1080", "风格": "简约商务", "主色": "#534AB7"})
            output = {
                "design_type": design_type,
                "specs": specs,
                "outputs": [
                    {"format": "png", "resolution": specs.get("尺寸", "1080x1080"), "ready": True},
                    {"format": "svg", "resolution": "矢量", "ready": True},
                ],
                "status": "design_ready"
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
