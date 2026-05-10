"""墨算财务 Worker — 记账、预算、成本控制、股票分析

所属: VP财务
"""

from .base import SmartSubsidiaryWorker as _Base, Task, WorkerResult
from molib.shared.finance.stock_engine import StockPipeline, Pipeline, Stage, TaskQueue

class Finance(_Base):
    worker_id = "finance"
    worker_name = "墨算财务"
    description = "记账、预算、成本控制"
    oneliner = "记账、预算、成本控制"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "API成本追踪与月报生成",
            "收支记录与分类统计",
            "预算管理与超支预警",
            "成本优化建议与模型路由降级分析",
            "股票分析（来自 daily_stock_analysis 34K⭐引擎）",
            "Pipeline阶段隔离降级编排",
            "多渠道通知广播",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨算财务",
            "vp": "财务",
            "description": "记账、预算、成本控制",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            task_type = task.task_type
            task_payload = task.payload or {}

            # ── 股票分析分支 ────────────────────────────────────────
            if task_type == "stock_analyze":
                symbol = task_payload.get("symbol", "AAPL")
                engine = StockPipeline()
                result = engine.analyze(symbol)
                return WorkerResult(
                    task_id=task.task_id,
                    worker_id=self.worker_id,
                    status="success",
                    output={
                        "type": "stock_analysis",
                        "symbol": symbol,
                        "pipeline_result": result,
                        "source": "stock_engine:daily_stock_analysis",
                    },
                )

            # ── Pipeline测试分支 ────────────────────────────────────
            if task_type == "pipeline_test":
                p = Pipeline()
                p.add_stage(
                    Stage("stage1", lambda ctx: {"data": ctx.get("input", "") + "_processed"},
                           is_critical=False)
                )
                ctx = p.run({"input": "test"})
                return WorkerResult(
                    task_id=task.task_id,
                    worker_id=self.worker_id,
                    status="success",
                    output={"type": "pipeline_test", "context": ctx, "source": "stock_engine"},
                )

            # ── 财务分析分支（原有逻辑） ──────────────────────────────
            period = task_payload.get("period", "本月")
            revenue = task_payload.get("revenue", 0)
            api_costs = task_payload.get("api_costs", 0)
            tool_costs = task.payload.get("tool_costs", 0)
            total_costs = task.payload.get("total_costs", 0)

            system = (
                "你是墨算财务——墨麟AI集团旗下的专业财务子公司。"
                "你的专长是：API成本追踪与月报生成、收支记录与分类统计、"
                "预算管理与超支预警、成本优化建议与模型路由降级分析。"
                "你精通财务分析，能给出可执行的降本增效建议。"
                "请输出结构化的财务分析报告。"
            )
            prompt = (
                f"请对以下财务数据进行深度分析：\n\n"
                f"周期：{period}\n"
                f"收入：¥{revenue}\n"
                f"API成本：¥{api_costs}\n"
                f"工具成本：¥{tool_costs}\n"
                f"总成本：¥{total_costs}\n"
                f"收入目标：¥48,000\n\n"
                f"请输出JSON格式，包含：\n"
                f"- period（分析周期）\n"
                f"- revenue（收入对象，含：total总收入, target目标收入）\n"
                f"- costs（成本对象，含：api API成本, tools工具成本, total总成本）\n"
                f"- profit_margin（利润率，字符串如'65%'）\n"
                f"- budget_status（预算状态，如'正常'/'超支'/'临近上限'）\n"
                f"- cost_breakdown（成本明细分析，简要说明各项成本构成）\n"
                f"- recommendation（成本优化建议）\n"
                f"- status（固定为'finance_ready'）"
            )

            llm_result = await self.llm_chat_json(prompt, system=system)
            if llm_result:
                output = {
                    "period": llm_result.get("period", period),
                    "revenue": llm_result.get("revenue", {"total": revenue, "target": 48000}),
                    "costs": llm_result.get("costs", {
                        "api": api_costs,
                        "tools": tool_costs,
                        "total": total_costs,
                    }),
                    "profit_margin": llm_result.get("profit_margin", "65%"),
                    "budget_status": llm_result.get("budget_status", "正常"),
                    "cost_breakdown": llm_result.get("cost_breakdown", ""),
                    "recommendation": llm_result.get("recommendation", "模型路由降级可省30%"),
                    "status": "finance_ready",
                    "source": "llm",
                }
            else:
                # fallback: 原有 mock 输出
                output = {
                    "period": period,
                    "revenue": {"total": revenue, "target": 48000},
                    "costs": {
                        "api": api_costs,
                        "tools": tool_costs,
                        "total": total_costs,
                    },
                    "profit_margin": "65%",
                    "recommendation": "模型路由降级可省30%",
                    "status": "finance_ready",
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
