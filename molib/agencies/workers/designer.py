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
            prompt_text = task.payload.get("prompt", "")
            count = task.payload.get("count", 1)

            system = (
                "你是墨图设计——墨麟AI集团旗下的专业视觉设计子公司。"
                "你的专长是：封面图与海报设计、UI界面视觉设计、多风格输出（商务/卡通/插画/扁平/3D）、"
                "批量化图片生成与排版。你精通设计规范、色彩理论和构图原则。"
                "你协助生成结构化的设计规格书，用于后续实际出图。"
            )
            prompt = (
                f"请为以下设计需求生成详细的设计规格书：\n\n"
                f"设计类型：{design_type}\n"
                f"规格要求：{specs}\n"
                f"设计描述：{prompt_text if prompt_text else '无额外描述'}\n"
                f"需要数量：{count}\n\n"
                f"请输出JSON格式，包含：\n"
                f"- design_type（设计类型）\n"
                f"- specs（规格，含：尺寸、风格、主色、字体、构图描述）\n"
                f"- outputs（数组，每项含：format格式、resolution分辨率、style_description风格描述）\n"
                f"- color_palette（推荐色板，数组含hex值和用途）\n"
                f"- design_notes（设计说明文字）\n"
                f"- visual_prompt（可直接用于文生图模型的英文prompt）"
            )

            result = await self.llm_chat_json(prompt, system=system)
            if result:
                outputs = result.get("outputs", [])
                if not outputs:
                    outputs = [{"format": "png", "resolution": specs.get("尺寸", "1080x1080"), "style_description": specs.get("风格", ""), "ready": True}]
                output = {
                    "design_type": result.get("design_type", design_type),
                    "specs": result.get("specs", specs),
                    "outputs": outputs,
                    "color_palette": result.get("color_palette", []),
                    "design_notes": result.get("design_notes", ""),
                    "visual_prompt": result.get("visual_prompt", ""),
                    "status": "design_spec_ready",
                    "source": "llm",
                }
            else:
                # fallback: 原有 mock 输出
                output = {
                    "design_type": design_type,
                    "specs": specs,
                    "outputs": [
                        {"format": "png", "resolution": specs.get("尺寸", "1080x1080"), "ready": True},
                        {"format": "svg", "resolution": "矢量", "ready": True},
                    ],
                    "status": "design_ready",
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
