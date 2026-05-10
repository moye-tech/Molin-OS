"""墨笔文创 Worker — v2.1 开源武装升级 (firecrawl ⭐70k)

升级内容:
  - firecrawl_reference: 自动抓取竞品爆款文章作为创作参考
  - 保留原有SmartSubsidiaryWorker + 主动协作 + 上下文注入
"""
from .base import SmartSubsidiaryWorker as _Base, Task, WorkerResult


class ContentWriter(_Base):
    worker_id = "content_writer"
    worker_name = "墨笔文创"
    description = "内容创作 (v2.1: firecrawl竞品参考 + Research协作 + 经验注入)"
    oneliner = "firecrawl竞品参考+Research协作+经验学习，智能内容创作"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "竞品爆款文章自动抓取与结构分析 (firecrawl ⭐70k)",
            "小红书/公众号/博客多平台创作",
            "Research协作热词洞察注入",
            "历史经验自动复用 (ExperienceVault)",
            "SEO关键词优化与内容策略",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨笔文创",
            "vp": "营销",
            "description": "内容创作 (v2.1: firecrawl竞品参考+Research协作)",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            action = task.payload.get("action", "write")
            topic = task.payload.get("topic", "未指定主题")
            platform = task.payload.get("platform", "公众号")
            style = task.payload.get("style", "专业科普")
            keywords = task.payload.get("keywords", [])
            word_count = task.payload.get("word_count", 1500)
            count = task.payload.get("count", 1)

            # ── v2.0: 历史经验 ──
            exp_hint = (context or {}).get("exp_hint", "")
            chain_ctx = task.payload.get("__context__", "")

            # ── v2.0: Research协作 ──
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

            # ── v2.1: Firecrawl竞品参考 ──
            firecrawl_ref = ""
            if action in ("write_with_firecrawl", "firecrawl_ref") or platform in ("小红书", "公众号"):
                try:
                    from molib.infra.external.firecrawl import search_and_scrape
                    f_result = search_and_scrape(f"{topic} {platform} 爆款", limit=3)
                    if f_result.get("status") == "success" and f_result.get("results"):
                        refs = []
                        for i, item in enumerate(f_result["results"][:3]):
                            if item.get("content"):
                                refs.append(f"参考{i+1}: {item.get('title','')}\n{item['content'][:500]}")
                        firecrawl_ref = "\n\n---\n".join(refs)
                except Exception:
                    pass

            # ── 构建增强system prompt ──
            system = (
                "你是墨笔文创——墨麟AI集团专业内容创作子公司。"
                "专长：小红书种草文案、公众号深度文章、博客技术文章、SEO优化文案。"
                "精通多风格写作，熟悉中文互联网内容调性和传播规律。"
            )
            if research_ctx:
                system += f"\n\n【趋势洞察】\n{research_ctx}"
            if exp_hint:
                system += f"\n\n【历史成功经验】\n{exp_hint}"
            if chain_ctx:
                system += f"\n\n【上游协作背景】\n{chain_ctx}"
            if firecrawl_ref:
                system += f"\n\n【竞品爆款参考】\n{firecrawl_ref}"

            prompt = (
                f"创作一篇{platform}风格文章：\n"
                f"主题：{topic}\n风格：{style}\n字数：{word_count}字\n关键词：{', '.join(keywords) if keywords else '无'}\n"
                f"输出JSON: title, content(完整正文Markdown), outline[], summary, word_count, tags[3-5个]"
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
                        "firecrawl_used": bool(firecrawl_ref),
                    },
                }]
                output = {"articles": articles, "count": 1, "topic": topic, "platform": platform, "source": "llm"}
            else:
                output = {
                    "articles": [{"title": f"{topic}深度解析", "word_count": 2000, "style": style, "outline": ["引言", f"{topic}背景", "核心分析", "结论"], "status": "draft_generated"}],
                    "count": 1, "topic": topic, "platform": platform, "source": "mock",
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
