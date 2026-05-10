"""墨图设计 Worker — v2.1 开源武装升级 (fal.ai FLUX.2 ⭐20k)

升级内容:
  - generate: fal.ai FLUX.2 真实AI生图 (替代纯提示词输出)
  - design_cover: 快捷封面图生成
  - 保留原有设计规格书生成功能 (plan模式)
"""
from .base import SmartSubsidiaryWorker as _Base, Task, WorkerResult


class Designer(_Base):
    worker_id = "designer"
    worker_name = "墨图设计"
    description = "视觉设计 (v2.1: FLUX.2真实生图 + 设计规格书生成)"
    oneliner = "FLUX.2 SOTA生图+封面海报+多风格AI设计"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "真实AI图像生成 (FLUX.2 ⭐20k via fal.ai)",
            "封面图与海报设计规格书",
            "UI界面视觉设计",
            "多风格输出（商务/卡通/插画/3D）",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨图设计",
            "vp": "营销",
            "description": "视觉设计 (v2.1: FLUX.2真实生图)",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            action = task.payload.get("action", "plan")

            # ── v2.1: 真实AI生图 ──
            if action in ("generate", "生图", "image"):
                output = await self._generate_image(task.payload)
            elif action in ("design_cover", "封面"):
                output = await self._design_cover(task.payload)
            else:
                output = await self._design_spec(task.payload)

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

    async def _generate_image(self, payload: dict) -> dict:
        """fal.ai FLUX.2 真实AI生图"""
        prompt_text = payload.get("prompt", "")
        if not prompt_text:
            return {"error": "prompt不能为空", "status": "error"}

        try:
            from molib.infra.external.fal_flux import generate_image
            import os
            output_path = payload.get("output_path", os.path.expanduser("~/Desktop/flux_output.png"))
            result = generate_image(
                prompt=prompt_text,
                model=payload.get("model", "fast-flux"),
                width=payload.get("width", 1024),
                height=payload.get("height", 1024),
                num_images=payload.get("count", 1),
                output_path=output_path,
            )
            return result
        except Exception:
            return {"prompt": prompt_text, "error": "FLUX不可用(fal.ai API)", "status": "unavailable"}

    async def _design_cover(self, payload: dict) -> dict:
        """快捷封面图生成"""
        title = payload.get("title", "")
        subtitle = payload.get("subtitle", "")
        style = payload.get("style", "modern-clean")
        if not title:
            return {"error": "title不能为空", "status": "error"}
        try:
            from molib.infra.external.fal_flux import design_cover
            return design_cover(title, subtitle, style)
        except Exception:
            return {"title": title, "error": "封面生成不可用", "status": "unavailable"}

    async def _design_spec(self, payload: dict) -> dict:
        """设计规格书生成 (原有功能)"""
        design_type = payload.get("type", "封面图")
        specs = payload.get("specs", {"尺寸": "1080x1080", "风格": "简约商务"})
        prompt_text = payload.get("prompt", "")
        count = payload.get("count", 1)

        system = "你是墨图设计——墨麟AI集团专业视觉设计子公司。请生成结构化设计规格书。"
        prompt = (
            f"设计类型: {design_type}\n规格: {specs}\n描述: {prompt_text}\n数量: {count}\n"
            "输出JSON: design_type, specs(尺寸/风格/主色/字体/构图), outputs[{format,resolution,style_description}], color_palette, design_notes, visual_prompt(英文生图prompt)"
        )
        result = await self.llm_chat_json(prompt, system=system)
        if result:
            return {**result, "source": "llm"}
        return {"design_type": design_type, "specs": specs, "outputs": [{"format": "png", "resolution": "1080x1080"}], "status": "design_ready", "source": "mock"}
