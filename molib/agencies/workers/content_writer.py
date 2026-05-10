"""墨笔文创 Worker — 文字内容创作、文案、公众号、博客

所属: VP营销
技能: molin-xiaohongshu, copywriting, content-strategy
v2.0升级: SmartSubsidiaryWorker基类 + 主动协作(Research) + 经验注入 + 链路上下文
"""
from .base import Task, WorkerResult
from .base import SmartSubsidiaryWorker as _Base


class ContentWriter(_Base):
    worker_id = "content_writer"
    worker_name = "墨笔文创"
    description = "文字内容创作、文案、公众号、博客"
    oneliner = "文字内容创作、文案、公众号、博客"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "生成小红书/公众号/博客文章",
            "SEO 关键词优化与内容策略",
            "多风格文案创作（专业/亲和/幽默）",
            "批量内容生产与草稿管理",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨笔文创",
            "vp": "营销",
            "description": "文字内容创作、文案、公众号、博客",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            topic = task.payload.get("topic", "未指定主题")
            count = task.payload.get("count", 1)
            style = task.payload.get("style", "专业科普")
            platform = task.payload.get("platform", "公众号")
            keywords = task.payload.get("keywords", [])
            word_count = task.payload.get("word_count", 1500)

            # ── v2.0: 主动向Research请求热词/竞品洞察（营销场景）──
            research_ctx = ""
            if platform in ("小红书", "抖音", "公众号"):
                try:
                    r = await self.request_collaboration(
                        "research",
                        {"action": "trend_scan", "topic": topic, "platform": platform}
                    )
                    research_ctx = r.get("summary", "") if isinstance(r, dict) else ""
                except Exception:
                    pass

            # ── v2.0: 读取历史经验（SmartWorkerMixin Pre-flight注入）──
            exp_hint = (context or {}).get("exp_hint", "")
            # ── v2.0: 读取WorkerChain上游产出 ──
            chain_ctx = task.payload.get("__context__", "")

            # LLM 生成真实内容
            system = (
                "你是墨笔文创——墨麟AI集团旗下的专业内容创作子公司。"
                "你的专长是中文内容创作：包括小红书种草文案、公众号深度文章、"
                "博客技术文章、SEO优化文案等。你精通多风格写作（专业科普/亲和日常/幽默段子/营销软文），"
                "熟悉中文互联网的内容调性和传播规律。"
                "请根据用户的需求生成高质量、结构化的文章内容。"
            )
            # v2.0: 富上下文注入
            if research_ctx:
                system += f"\n\n【趋势洞察】\n{research_ctx}"
            if exp_hint:
                system += f"\n\n【历史成功经验】\n{exp_hint}"
            if chain_ctx:
                system += f"\n\n【上游协作背景】\n{chain_ctx}"

            prompt = (
                f"请为以下主题创作一篇{platform}风格的文章：\n\n"
                f"主题：{topic}\n"
                f"风格：{style}\n"
                f"目标字数：{word_count}字左右\n"
                f"关键词：{', '.join(keywords) if keywords else '无特定'}\n\n"
                f"请输出JSON格式，包含：title（文章标题）, content（完整文章正文，含Markdown格式）, "
                f"outline（大纲列表）, summary（一句话摘要）, word_count（实际字数）, tags（3-5个标签）"
            )

            result = await self.llm_chat_json(prompt, system=system)
            if result:
                articles = [{
                    "title": result.get("title", f"{topic}深度解析"),
                    "content": result.get("content", ""),
                    "outline": result.get("outline", []),
                    "summary": result.get("summary", ""),
                    "word_count": result.get("word_count", word_count),
                    "style": style,
                    "tags": result.get("tags", []),
                    "status": "draft_generated",
                    "v2_contexts": {
                        "research_used": bool(research_ctx),
                        "experience_used": bool(exp_hint),
                        "chain_used": bool(chain_ctx),
                    },
                }]
                for i in range(1, count):
                    extra_prompt = prompt + f"\n\n这是第{i+1}篇，请换一个不同的角度和标题来创作。"
                    extra = await self.llm_chat_json(extra_prompt, system=system)
                    if extra:
                        articles.append({
                            "title": extra.get("title", f"{topic}多角度分析（第{i+1}篇）"),
                            "content": extra.get("content", ""),
                            "outline": extra.get("outline", []),
                            "summary": extra.get("summary", ""),
                            "word_count": extra.get("word_count", word_count),
                            "style": style,
                            "tags": extra.get("tags", []),
                            "status": "draft_generated",
                        })
                output = {"articles": articles, "count": count, "topic": topic, "platform": platform, "source": "llm"}
            else:
                results = []
                for i in range(count):
                    results.append({
                        "title": "{}深度解析（第{}篇）".format(topic, i+1),
                        "word_count": 2000,
                        "style": style,
                        "keywords": keywords,
                        "outline": ["## 引言", "## {}的背景".format(topic), "## 核心分析", "## 结论"],
                        "status": "draft_generated"
                    })
                output = {"articles": results, "count": count, "topic": topic, "platform": platform, "source": "mock"}
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
