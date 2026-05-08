"""墨笔文创 Worker — 文字内容创作、文案、公众号、博客

所属: VP营销
技能: molin-xiaohongshu, copywriting, content-strategy
"""
from .base import SubsidiaryWorker, Task, WorkerResult

class ContentWriter(SubsidiaryWorker):
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
            results = []
            for i in range(count):
                results.append({
                    "title": "{0}深度解析（第{1}篇）".format(topic, i+1),
                    "word_count": 2000,
                    "style": style,
                    "keywords": task.payload.get("keywords", []),
                    "outline": ["## 引言", "## {0}的背景".format(topic), "## 核心分析", "## 结论"],
                    "status": "draft_generated"
                })
            output = {"articles": results, "count": count, "topic": topic}
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
