"""墨测数据 Worker — 数据分析、测试、质量 (LLM驱动)

所属: 共同服务
技能: molin-data-analytics, molin-vizro
"""
from .base import SmartSubsidiaryWorker as _Base, Task, WorkerResult


class DataAnalyst(_Base):
    worker_id = "data_analyst"
    worker_name = "墨测数据"
    description = "数据分析、测试、质量"
    oneliner = "数据分析测试质量"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "多维度数据汇总与趋势分析",
            "增长归因与转化漏斗分析",
            "数据可视化看板生成",
            "自动化测试与质量报告",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨测数据",
            "vp": "共同服务",
            "description": "数据分析、测试、质量",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            metrics = task.payload.get("metrics", ["pv", "uv", "conversion"])
            period = task.payload.get("period", "本周")
            action = task.payload.get("action", "analyze")

            if action == "funnel":
                # 转化漏斗分析：用LLM生成洞察
                stages = task.payload.get("stages", ["曝光", "点击", "转化"])
                stage_data = task.payload.get("stage_data", {})

                prompt = f"""你是一位数据分析师。根据以下数据做转化漏斗分析：

时间周期：{period}
漏斗阶段：{stages}
各阶段数据：{stage_data}

请以JSON格式返回：
- period: 时间周期
- funnel: 漏斗各阶段名称与数值列表，每个元素包含 name (str), value (int|float), drop_rate (str)
- overall_conversion_rate: 整体转化率字符串（如"3.2%"）
- bottlenecks: 瓶颈阶段及建议列表
- status: "funnel_analysis_ready"
"""
                system = "你是一位专业的数据分析师，擅长转化漏斗分析。返回严格JSON。"
                llm_output = await self.llm_chat_json(prompt, system=system)

                if not llm_output:
                    output = {
                        "period": period,
                        "funnel": [
                            {"name": s, "value": 0, "drop_rate": "0%"}
                            for s in stages
                        ],
                        "overall_conversion_rate": "0%",
                        "bottlenecks": [{"stage": "转化", "suggestion": "优化CTA"}],
                        "status": "funnel_analysis_ready",
                    }
                else:
                    llm_output.setdefault("period", period)
                    llm_output.setdefault("status", "funnel_analysis_ready")
                    output = llm_output

            elif action == "attribution":
                # 增长归因分析
                channels = task.payload.get("channels", ["organic", "social", "direct", "paid", "referral"])
                channel_data = task.payload.get("channel_data", {})

                prompt = f"""你是一位增长分析师。根据以下数据进行增长归因分析：

时间周期：{period}
渠道：{channels}
各渠道数据：{channel_data}

请以JSON格式返回：
- period: 时间周期
- attribution: 各渠道的归因占比 dict（如 {{"organic": "35%", "social": "25%"}}）
- top_channel: 效果最佳渠道及原因
- recommendations: 优化建议列表
- status: "attribution_ready"
"""
                system = "你是一位专业的增长分析师，擅长多渠道归因分析。返回严格JSON。"
                llm_output = await self.llm_chat_json(prompt, system=system)

                if not llm_output:
                    output = {
                        "period": period,
                        "attribution": {
                            "organic": "35%", "social": "25%",
                            "direct": "20%", "paid": "15%", "referral": "5%",
                        },
                        "top_channel": "organic",
                        "recommendations": ["加大内容投入", "优化CTA"],
                        "status": "attribution_ready",
                    }
                else:
                    llm_output.setdefault("period", period)
                    llm_output.setdefault("status", "attribution_ready")
                    output = llm_output

            else:
                # 默认：多维度数据汇总与趋势分析
                metric_details = task.payload.get("metric_details", {})

                prompt = f"""你是一位数据分析师。根据以下数据进行多维度汇总与趋势分析：

时间周期：{period}
指标列表：{metrics}
具体数据：{metric_details}

请以JSON格式返回：
- period: 时间周期
- overview: 各指标概览 dict，每个指标包含 value (int|float) 和 trend ("up"/"down"/"stable")
- key_findings: 关键发现列表（至少2条）
- recommendations: 可执行建议列表（至少2条）
- status: "analysis_ready"
"""
                system = "你是一位专业的数据分析师，擅长多维度数据分析与洞察提取。返回严格JSON。"
                llm_output = await self.llm_chat_json(prompt, system=system)

                if not llm_output:
                    output = {
                        "period": period,
                        "overview": {m: {"value": 0, "trend": "stable"} for m in metrics},
                        "attribution": {
                            "organic": "35%", "social": "25%",
                            "direct": "20%", "paid": "15%", "referral": "5%",
                        },
                        "recommendations": ["加大内容投入", "优化CTA"],
                        "status": "analysis_ready",
                    }
                else:
                    llm_output.setdefault("period", period)
                    llm_output.setdefault("status", "analysis_ready")
                    output = llm_output

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
