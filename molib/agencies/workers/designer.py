"""墨图设计 Worker — v2.2 Open Design 开源武装升级

升级内容:
  - v2.1: fal.ai FLUX.2 真实AI生图 (替代纯提示词输出)
  - v2.1: design_cover 快捷封面图生成
  - v2.2: web_design Open Design 全栈设计工程集成 (149设计系统×134技能)
  - v2.2: landing_page / dashboard / pitch_deck / ppt 等快捷action
  - 保留原有设计规格书生成功能 (plan模式)
"""
from .base import SmartSubsidiaryWorker as _Base, Task, WorkerResult

import json, os, re, uuid
from urllib.request import Request, urlopen
from urllib.error import URLError

# ── Open Design daemon 配置 ───────────────────────────────────────
OD_DAEMON_URL = os.environ.get("OD_DAEMON_URL", "http://127.0.0.1:55888")

# action → skill ID 映射表 (常用快捷入口)
ACTION_SKILL_MAP = {
    "landing_page": "saas-landing",
    "saas_landing": "saas-landing",
    "dashboard": "dashboard",
    "pitch_deck": "html-ppt-pitch-deck",
    "blog_post": "blog-post",
    "pricing_page": "pricing-page",
    "mobile_app": "mobile-app",
    "web_prototype": "web-prototype",
    "ppt": "html-ppt-pitch-deck",
    "weekly_report": "weekly-update",
    "finance_report": "finance-report",
    "docs_page": "docs-page",
    "waitlist": "waitlist-page",
    "login_flow": "login-flow",
    "kami_landing": "kami-landing",
    "open_design_landing": "open-design-landing",
}


class Designer(_Base):
    worker_id = "designer"
    worker_name = "墨图设计"
    description = "视觉设计 (v2.2: Open Design全栈 + FLUX.2生图 + 设计规格书)"
    oneliner = "Open Design 149设计系统×134技能 + FLUX.2 SOTA生图"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "全栈设计工程 (Open Design: 149设计系统 × 134技能)",
            "网页/落地页/仪表盘/PPT 一键生成 (HTML/CSS)",
            "真实AI图像生成 (FLUX.2 ⭐20k via fal.ai)",
            "封面图与海报设计规格书",
            "品牌视觉体系 (Apple/Stripe/Airbnb/Arc...)",
            "多风格输出（商务/卡通/插画/3D）",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨图设计",
            "vp": "营销",
            "description": "视觉设计 (v2.2: Open Design全栈+FLUX.2生图)",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            action = task.payload.get("action", "plan")

            # ── v2.2: Open Design 全栈设计工程 ──
            if action in ("web_design", "设计网页", "全栈设计") or action in ACTION_SKILL_MAP:
                output = await self._web_design(task.payload)
            # ── v2.1: 真实AI生图 ──
            elif action in ("generate", "生图", "image"):
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

    # ════════════════════════════════════════════════════════════════
    # v2.2 Open Design 全栈设计工程
    # ════════════════════════════════════════════════════════════════

    async def _web_design(self, payload: dict) -> dict:
        """Open Design 全栈设计: 通过 daemon API 生成网页/落地页/PPT等。

        payload:
            action   — web_design / landing_page / dashboard / pitch_deck / ...
            prompt   — 用户需求描述 (必填)
            design_system — 设计系统ID (默认: apple, 可选: stripe/airbnb/arc/ant/...)
            skill    — 技能ID (自动从action推导, 也可手动指定)
            title    — 项目标题 (默认从prompt截取)
        """
        prompt = payload.get("prompt", "")
        if not prompt:
            return {"error": "prompt不能为空", "status": "error"}

        # 1. 确定 skill 和 design system
        action = payload.get("action", "web_design")
        skill_id = payload.get("skill") or ACTION_SKILL_MAP.get(action, "saas-landing")
        ds_id = payload.get("design_system", "apple")
        title = payload.get("title") or prompt[:40]

        # 2. 从 daemon 获取 skill 定义和 design system
        skill_def = self._od_api_get(f"/api/skills/{skill_id}")
        ds_def = self._od_api_get(f"/api/design-systems/{ds_id}")

        if not skill_def:
            return {"error": f"技能 '{skill_id}' 不可用 (daemon未响应或技能不存在)", "status": "unavailable"}
        if not ds_def:
            ds_body = "# Default Design System\nMinimal clean design. System fonts, white space, simple color palette.\n"
            ds_note = "默认(daemon无响应)"
        else:
            ds_body = ds_def.get("body", "")
            ds_note = ds_id

        # 3. 用 LLM 生成 HTML
        system = self._build_design_system_prompt(skill_def, ds_body, ds_id)
        user_prompt = (
            f"请根据以下设计系统和技能规范，生成一个完整的单文件 HTML 页面。\n\n"
            f"【用户需求】{prompt}\n\n"
            f"【规则】\n"
            f"1. 必须是单文件 HTML（内联 CSS/JS）\n"
            f"2. 严格遵循设计系统的色彩/字体/间距规范\n"
            f"3. 不要使用外部 CDN 资源（用系统字体、内联 SVG 代替）\n"
            f"4. 直接输出 HTML 代码，用 ```html 包裹\n"
        )

        result = await self.llm_chat(user_prompt, system=system)
        html = self._extract_html(result)

        if not html or len(html) < 100:
            return {"error": "LLM未生成有效HTML", "status": "llm_failed", "raw_preview": result[:500]}

        # 4. 保存到 daemon artifact
        artifact = self._od_api_post("/api/artifacts/save", {
            "identifier": f"molin-{skill_id}",
            "title": title,
            "html": html,
        })

        # 5. 本地也存一份
        output_dir = os.path.expanduser("~/Molin-OS/output/designs")
        os.makedirs(output_dir, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in title)[:40]
        local_path = os.path.join(output_dir, f"od_{safe_name}_{uuid.uuid4().hex[:6]}.html")
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(html)

        return {
            "status": "success",
            "engine": "Open Design v0.6.0",
            "skill": skill_id,
            "design_system": ds_note,
            "local_path": local_path,
            "preview_url": f"{OD_DAEMON_URL}{artifact.get('url', '')}" if artifact else None,
            "artifact": artifact,
            "html_size": len(html),
        }

    def _build_design_system_prompt(self, skill_def: dict, ds_body: str, ds_id: str) -> str:
        """构建注入设计系统+技能规范的系统提示词。"""
        skill_desc = skill_def.get("description", "")
        skill_body = skill_def.get("body", "")
        skill_craft = skill_def.get("craftRequires", [])
        example = skill_def.get("examplePrompt", "")

        lines = [
            "你是墨图设计——墨麟AI集团专业视觉设计子公司。",
            "你是一位世界级的前端设计师，精通 HTML/CSS 和视觉设计。",
            "",
            f"## 当前技能: {skill_def.get('name', '')}",
            f"{skill_desc}",
        ]

        if example:
            lines.append(f"示例提示词: {example}")

        if skill_craft:
            lines.append(f"设计要求: {', '.join(skill_craft)}")

        if ds_body:
            # 截取设计系统前4000字符（避免token超限）
            lines.append("")
            lines.append(f"## 设计系统: {ds_id}")
            lines.append(ds_body[:4000])

        if skill_body:
            lines.append("")
            lines.append("## 技能规范")
            lines.append(skill_body[:3000])

        lines.append("")
        lines.append("## 输出规则")
        lines.append("- 单文件 HTML，内联所有 CSS")
        lines.append("- 使用系统字体栈（SF Pro / Inter / system-ui）")
        lines.append("- 响应式设计，移动端友好")
        lines.append("- 直接输出 ```html ... ``` 代码块")

        return "\n".join(lines)

    @staticmethod
    def _extract_html(text: str) -> str:
        """从 LLM 输出中提取 HTML 代码块。"""
        # 尝试 ```html ... ```
        m = re.search(r"```html\s*\n?(.*?)```", text, re.DOTALL)
        if m:
            return m.group(1).strip()
        # 尝试 ``` ... ```
        m = re.search(r"```\s*\n?(.*?)```", text, re.DOTALL)
        if m:
            code = m.group(1).strip()
            if code.startswith("<"):
                return code
        # 尝试裸 HTML
        m = re.search(r"(<!DOCTYPE html>.*?</html>)", text, re.DOTALL | re.IGNORECASE)
        if m:
            return m.group(1).strip()
        return text.strip()

    # ════════════════════════════════════════════════════════════════
    # Open Design daemon API helpers
    # ════════════════════════════════════════════════════════════════

    @staticmethod
    def _od_api_get(path: str, timeout: int = 10) -> dict | None:
        """调用 Open Design daemon GET API。"""
        try:
            req = Request(f"{OD_DAEMON_URL}{path}")
            req.add_header("Accept", "application/json")
            with urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except (URLError, json.JSONDecodeError, OSError):
            return None

    @staticmethod
    def _od_api_post(path: str, body: dict, timeout: int = 10) -> dict | None:
        """调用 Open Design daemon POST API。"""
        try:
            data = json.dumps(body).encode("utf-8")
            req = Request(f"{OD_DAEMON_URL}{path}", data=data)
            req.add_header("Content-Type", "application/json")
            req.add_header("Accept", "application/json")
            with urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except (URLError, json.JSONDecodeError, OSError):
            return None

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
