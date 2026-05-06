"""墨笔文创 Worker"""
from .base import SubsidiaryWorker, Task, WorkerResult

class ContentWriter(SubsidiaryWorker):
    worker_id = "content_writer"
    worker_name = "墨笔文创"
    description = "批量创作SEO文章"
    oneliner = "批量创作SEO文章"

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
