import json
import time
from datetime import date
from pathlib import Path
from typing import Dict, Any, Optional

from loguru import logger

from molib.infra.data_brain.analytics import DataBrain
from .model_router import ModelRouter
from .intent_processor import IntentProcessor
from molib.infra.memory.memory_manager import get_memory_manager, MemoryScenario, get_agency_namespace
from strategy.strategy_engine import StrategyEngine
from molib.utils.alerts import send_alert

# Evolution 引擎（可选）
try:
    from molib.core.evolution.engine import EvolutionEngine
    EVOLUTION_AVAILABLE = True
except ImportError:
    EVOLUTION_AVAILABLE = False

# 导入Manager模块（可选）
try:
    from molib.core.managers.manager_dispatcher import get_dispatcher
    from molib.agencies.base import Task
    MANAGER_DISPATCHER_AVAILABLE = True
except ImportError as e:
    MANAGER_DISPATCHER_AVAILABLE = False
    logger.debug(f"ManagerDispatcher not available: {e}")

# SOP 反馈管道
try:
    from molib.sop.sop_feedback import get_sop_feedback
    SOP_FEEDBACK_AVAILABLE = True
except ImportError:
    SOP_FEEDBACK_AVAILABLE = False
    logger.debug("SOP feedback pipeline not available")

# Manager路由启用标志（可从配置读取）
MANAGER_ROUTING_ENABLED = True

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "ceo_system.txt"

class CEO:
    def __init__(self, daily_budget_cny: float = 50.0):
        self.router = ModelRouter()
        self.data_brain = DataBrain()
        self.strategy_engine = StrategyEngine()
        self.intent_processor = IntentProcessor(daily_budget_cny=daily_budget_cny)
        self.system_prompt = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.exists() else ""
        self.system_prompt += f"\n\n【时间上下文】当前日期：{date.today().isoformat()}。所有数据、搜索和分析必须基于此日期判断时效性，知识截止日期之后的信息需通过工具获取，不得编造。"

        # Evolution 引擎
        if EVOLUTION_AVAILABLE:
            self.evolution_engine = EvolutionEngine()
        else:
            self.evolution_engine = None

        # 记忆管理器（异步初始化）
        self.memory_manager = None
        # SQLite客户端向后兼容
        self.db = None  # 将在异步初始化中设置

    async def initialize(self):
        """异步初始化记忆系统"""
        if self.memory_manager is None:
            self.memory_manager = await get_memory_manager()
            # 向后兼容：保持self.db指向SQLiteClient
            from molib.infra.memory.sqlite_client import SQLiteClient
            self.db = SQLiteClient()
            logger.info("MolinCEO记忆系统初始化完成")

    async def run_async(self, user_input, budget=None,
                        timeline=None, target_revenue=None, context=None):
        # 确保记忆系统已初始化
        if self.memory_manager is None:
            await self.initialize()

        # 1. 使用意图处理器进行预处理
        context_dict = context or {}
        if budget is not None:
            context_dict['budget'] = budget
        if timeline is not None:
            context_dict['timeline'] = timeline
        if target_revenue is not None:
            context_dict['target_revenue'] = target_revenue

        intent_result = self.intent_processor.process(user_input, context_dict)

        # 2. 根据意图结果处理
        if intent_result.response:  # 有直接响应（如trivial请求）
            return {
                "decision": "DIRECT_RESPONSE",
                "message": intent_result.response,
                "intent_type": intent_result.intent_type.value,
                "should_pass_to_ceo": intent_result.should_pass_to_ceo,
                "model_used": "intent_processor",
                "cost": intent_result.estimated_cost_cny,
                "latency": 0.0
            }

        # 3. 检查是否需要补充信息
        if intent_result.missing_fields:
            questions = self.intent_processor.get_questions_for_missing_fields(intent_result.missing_fields)
            return {
                "decision": "NEED_INFO",
                "questions": questions,
                "intent_type": intent_result.intent_type.value,
                "missing_fields": intent_result.missing_fields,
                "target_agency": intent_result.target_agency,
                "score": {"roi": 0, "scalability": 0, "difficulty": 0, "composite": 0},
                "strategy": [], "tasks": [], "risks": [], "metrics": [],
                "next_review": "待补充信息后重新评估",
                "model_used": "intent_processor",
                "cost": intent_result.estimated_cost_cny,
                "latency": 0.0
            }

        # 4. 检查是否应该传递给CEO
        if not intent_result.should_pass_to_ceo:
            # 不需要CEO，直接路由到相应Agency/Manager执行
            target_agency = intent_result.target_agency
            if target_agency and MANAGER_DISPATCHER_AVAILABLE:
                try:
                    dispatcher = await get_dispatcher()
                    task = Task(
                        task_id=f"ceo_ar_{int(time.time())}_{target_agency}",
                        task_type=target_agency,
                        payload={
                            "description": intent_result.preprocessed_task,
                            "budget": context_dict.get('budget'),
                            "timeline": context_dict.get('timeline'),
                            "target_revenue": context_dict.get('target_revenue'),
                            "context": context_dict,
                        },
                        priority=intent_result.priority,
                        requester="ceo",
                    )

                    manager = await dispatcher.get_manager(target_agency)
                    if manager:
                        logger.info(f"CEO 直接路由到 {target_agency} Manager: {intent_result.preprocessed_task}")
                        execution_result = await manager.delegate_task(task)

                        return {
                            "decision": "GO",
                            "message": f"任务已委派到 {target_agency} 子公司执行",
                            "intent_type": intent_result.intent_type.value,
                            "target_agency": target_agency,
                            "executed_by": f"manager:{target_agency}",
                            "execution_result": {
                                "status": execution_result.status,
                                "output": getattr(execution_result, "aggregated_output", {}),
                                "error": getattr(execution_result, "error", None),
                            },
                            "score": {"roi": 0, "scalability": 0, "difficulty": 0, "composite": 0},
                            "model_used": f"manager:{target_agency}",
                            "cost": getattr(execution_result, "total_cost", 0.0),
                            "latency": getattr(execution_result, "total_latency", 0.0),
                        }
                    else:
                        logger.warning(f"未找到 {target_agency} Manager，回退到 CEO 决策")
                except Exception as e:
                    logger.error(f"Manager 直接路由失败 [{target_agency}]: {e}，回退到 CEO 决策")
            # 回退：Manager 不可用时直接调用 Python Agency 执行
            if target_agency and target_agency in AGENCY_MAP:
                logger.info(f"Manager 不可用，降级为 Agency 直接执行: {target_agency}")
                from molib.agencies.base import Task as AgencyTask
                agency_task = AgencyTask(
                    task_id=f"ceo_direct_{intent_result.preprocessed_task[:30]}",
                    task_type=target_agency,
                    payload={"description": intent_result.preprocessed_task},
                )
                try:
                    result = await AGENCY_MAP[target_agency].safe_execute(agency_task)
                    return {
                        "decision": "GO",
                        "message": result.output.get("summary", str(result.output)),
                        "intent_type": intent_result.intent_type.value,
                        "execution_result": {"results": [result.output]},
                        "should_pass_to_ceo": False,
                        "model_used": f"agency_direct:{target_agency}",
                        "cost": result.cost,
                        "latency": result.latency,
                    }
                except Exception as e:
                    logger.error(f"Agency 直接执行失败 [{target_agency}]: {e}")
            return {
                "decision": "FAILED",
                "message": f"无法处理该任务：Manager 路由和 Agency 直接执行均失败 (target={target_agency})",
                "intent_type": intent_result.intent_type.value,
                "error": f"No manager or agency available for {target_agency}",
                "should_pass_to_ceo": False,
                "model_used": "none",
                "cost": 0.0,
                "latency": 0.0,
            }

        # 5. 需要CEO决策，构建输入
        # 不再强制要求 budget/timeline/target_revenue，CEO 通过 LLM 用自然语言推理
        full_input = f"用户需求：{user_input}"
        input_parts = [full_input]
        if budget is not None:
            input_parts.append(f"预算：{budget}元")
        if timeline is not None:
            input_parts.append(f"周期：{timeline}")
        if target_revenue is not None:
            input_parts.append(f"目标收入：{target_revenue}元")
        if context:
            input_parts.append(f"背景：{json.dumps(context, ensure_ascii=False)}")
        full_input = "\n".join(input_parts)
        start = time.time()
        result = await self.router.call_async(
            prompt=full_input, system=self.system_prompt, task_type="ceo_decision")

        text = result["text"]
        s, e = text.find("{"), text.rfind("}") + 1
        try:
            parsed = json.loads(text[s:e] if s >= 0 else text)
        except json.JSONDecodeError:
            logger.error(f"CEO response parse failed: {text[:500]}")
            raise

        # 综合评分低于 5 强制 NO_GO
        score = parsed.get("score", {})
        composite = (score.get("roi", 0) * 0.5 + score.get("scalability", 0) * 0.3
                      - score.get("difficulty", 0) * 0.2)
        score["composite"] = round(composite, 2)
        if composite < 5 and parsed.get("decision") == "GO":
            parsed["decision"] = "NO_GO"
            parsed.setdefault("risks", []).append(
                {"risk": "综合评分低于5分", "mitigation": "重新评估商业模型"})

        # 使用记忆管理器存储决策（分层记忆）
        decision_data = {
            "action": parsed.get("decision"),
            "roi": score.get("roi", 0),
            "confidence": parsed.get("confidence_score", 0.7),
            "input_summary": user_input[:200],
            "output_json": parsed,
            "composite_score": score.get("composite", 0),
            "model_used": result.get("model", "unknown"),
            "cost": result.get("cost", 0.0),
            "latency": result.get("latency", 0.0),
            "intent_processing": {
                "intent_type": intent_result.intent_type.value,
                "priority": intent_result.priority,
                "estimated_cost_cny": intent_result.estimated_cost_cny,
                "missing_fields": intent_result.missing_fields,
                "target_agency": intent_result.target_agency,
                "preprocessed_task": intent_result.preprocessed_task,
                "should_pass_to_ceo": intent_result.should_pass_to_ceo
            }
        }

        # 存储到事务性记忆（SQLite）
        await self.memory_manager.store(
            key=f"decision_{int(time.time())}",
            data=decision_data,
            scenario=MemoryScenario.TRANSACTIONAL,
            metadata={"task_type": "ceo_decision", "user_input": user_input[:100]}
        )

        # 如果决策是GO且分数高，也存储到长期记忆
        if parsed.get("decision") == "GO" and score.get("composite", 0) > 7:
            await self.memory_manager.store(
                key=f"successful_decision_{int(time.time())}",
                data=decision_data,
                scenario=MemoryScenario.LONG_TERM,
                metadata={"high_value": True, "composite_score": score.get("composite", 0)}
            )

        # 向后兼容：保持原有的SQLite日志
        await self.db.log_decision(
            action=parsed.get("decision"), roi=score.get("roi", 0),
            confidence=parsed.get("confidence_score", 0.7),
            input_summary=user_input[:200], output_json=parsed)

        # 添加意图处理信息
        parsed.update({
            "model_used": result.get("model", "unknown"),
            "cost": result.get("cost", 0.0),
            "latency": round(time.time() - start, 2),
            "intent_processing": {
                "intent_type": intent_result.intent_type.value,
                "priority": intent_result.priority,
                "estimated_cost_cny": intent_result.estimated_cost_cny,
                "missing_fields": intent_result.missing_fields,
                "target_agency": intent_result.target_agency,
                "preprocessed_task": intent_result.preprocessed_task,
                "should_pass_to_ceo": intent_result.should_pass_to_ceo,
                "budget_check": intent_result.budget_check
            }
        })

        # ManagerDispatcher集成：如果决策为GO且启用了Manager路由，则委派给相应的Manager
        if (MANAGER_DISPATCHER_AVAILABLE and MANAGER_ROUTING_ENABLED and
            parsed.get("decision") == "GO"):

            try:
                # 确定目标子公司
                target_subsidiary = self._determine_subsidiary(intent_result, parsed)

                if target_subsidiary:
                    # 获取ManagerDispatcher实例
                    manager_dispatcher = await get_dispatcher()

                    # 创建Task对象
                    task = Task(
                        task_id=f"ceo_{int(time.time())}_{target_subsidiary}",
                        task_type=target_subsidiary,
                        payload={
                            "description": user_input,
                            "budget": budget,
                            "timeline": timeline,
                            "target_revenue": target_revenue,
                            "context": context,
                            "ceo_decision": parsed,
                            "intent_processing": parsed.get("intent_processing", {})
                        },
                        priority=intent_result.priority,
                        requester="ceo"
                    )

                    # 获取Manager并委派任务
                    manager = await manager_dispatcher.get_manager(target_subsidiary)
                    if manager:
                        logger.info(f"CEO将任务委派给 {target_subsidiary} Manager")
                        # 按 namespace 检索历史记忆
                        ns = get_agency_namespace(target_subsidiary)
                        try:
                            history = await self.memory_manager.retrieve(
                                key=target_subsidiary,
                                scenario=MemoryScenario.TRANSACTIONAL,
                                limit=5,
                                namespace=ns
                            )
                            if history:
                                logger.info(f"检索到 {len(history)} 条 {ns} namespace 历史记忆")
                        except Exception as e:
                            logger.debug(f"检索历史记忆失败: {e}")
                        execution_result = await manager.delegate_task(task)

                        # 将执行结果集成到parsed响应中
                        parsed["execution_result"] = execution_result
                        parsed["executed_by"] = f"manager:{target_subsidiary}"
                        parsed["manager_execution"] = {
                            "status": "delegated",
                            "manager_id": target_subsidiary,
                            "timestamp": time.time()
                        }
                    else:
                        logger.warning(f"未找到 {target_subsidiary} Manager，任务将不会被执行")
                        parsed["execution_result"] = {"error": f"Manager {target_subsidiary} not found"}
                        parsed["executed_by"] = "none"
                else:
                    logger.warning("无法确定目标子公司，任务将不会被委派")
                    parsed["execution_result"] = {"error": "Cannot determine target subsidiary"}
                    parsed["executed_by"] = "none"

            except ImportError as e:
                logger.warning(f"ManagerDispatcher导入失败: {e}")
                parsed["execution_result"] = {"error": f"ManagerDispatcher import failed: {e}"}
            except Exception as e:
                logger.error(f"ManagerDispatcher集成失败: {e}")
                parsed["execution_result"] = {"error": f"ManagerDispatcher integration failed: {e}"}
                parsed["executed_by"] = "error"

        # SOP 反馈管道: 任务完成后自动提炼知识、检查 SOP 偏差
        if SOP_FEEDBACK_AVAILABLE and parsed.get("decision") == "GO":
            try:
                feedback = get_sop_feedback()
                await feedback.post_task_hook(
                    task_result=parsed,
                    task_meta={
                        "task_type": intent_result.target_agency or "unknown",
                        "description": user_input[:200],
                        "sop_id": context_dict.get("sop_id") if context_dict else None,
                    },
                )
            except Exception as e:
                logger.warning(f"SOP 反馈管道执行失败: {e}")

        # P1-5: Redis Streams — 写入 CEO 决策事件
        try:
            from molib.infra.data_brain.redis_streams import get_streams_client
            streams_client = await get_streams_client()
            await streams_client.publish_decision({
                "decision": parsed.get("decision"),
                "target_agency": intent_result.target_agency,
                "cost": parsed.get("cost", 0.0),
                "latency": parsed.get("latency", 0.0),
                "input_summary": user_input[:200],
            })
        except Exception:
            pass

        return parsed

    def _determine_subsidiary(self, intent_result, parsed_decision) -> Optional[str]:
        """
        确定目标子公司

        Args:
            intent_result: 意图处理结果
            parsed_decision: CEO决策结果

        Returns:
            Optional[str]: 子公司ID，如果无法确定则返回None
        """
        # 1. 首先检查intent_result中是否有预路由目标
        if intent_result.target_agency:
            return intent_result.target_agency

        # 2. 检查parsed_decision中是否包含目标子公司信息
        if isinstance(parsed_decision, dict):
            # 检查常见的子公司字段
            for field in ['target_agency', 'target_subsidiary', 'subsidiary', 'agency']:
                if parsed_decision.get(field):
                    return parsed_decision.get(field)

            # 检查决策类型是否暗示了子公司
            decision_type = parsed_decision.get('decision_type', '')
            if decision_type in ['广告投放', '营销活动']:
                return 'ads'
            elif decision_type in ['产品开发', '功能设计']:
                return 'product'
            elif decision_type in ['市场研究', '竞品分析']:
                return 'research'
            elif decision_type in ['安全审计', '风险评估']:
                return 'secure'

        # 3. 根据决策任务描述推断
        tasks = parsed_decision.get('tasks', [])
        if tasks:
            task_desc = str(tasks[0]).lower() if isinstance(tasks, list) and len(tasks) > 0 else ''
            # 简单的关键词匹配
            keyword_mapping = {
                'ads': ['广告', '投放', '营销', '创意'],
                'product': ['产品', '设计', '功能', '界面'],
                'research': ['研究', '市场', '调研', '趋势'],
                'secure': ['安全', '合规', '风险', '审计'],
                'dev': ['开发', '代码', '部署', 'API'],
                'ai': ['AI', '提示', '模型', '智能'],
                'growth': ['增长', '获客', '转化', '漏斗'],
                'ip': ['IP', '内容', '文案', '创作'],
                'data': ['数据', '分析', '报表', '指标'],
                'order': ['订单', '客户', '销售', '成交'],
                'shop': ['电商', '店铺', '商品', '购物'],
                'edu': ['教育', '课程', '培训', '学习']
            }

            for subsidiary, keywords in keyword_mapping.items():
                for keyword in keywords:
                    if keyword in task_desc:
                        return subsidiary

            # 4. 新增子公司关键词映射
            new_keyword_mapping = {
                'finance': ['财务', '成本', '预算', 'ROI', '利润', '账单'],
                'crm': ['私域', '会员', '复购', '流失', '用户分层', 'RFM'],
                'knowledge': ['知识库', '复盘', '总结', 'SOP更新', '经验沉淀'],
                'cs': ['客服', '投诉', '售后', '退款', '用户反馈'],
                'legal': ['合同', '版权', '合规', '法律', 'NDA', '隐私政策'],
                'bd': ['合作', '报价', '谈判', 'BD', '接单', '商务'],
                'global': ['出海', '繁体', '翻译', '台湾', '东南亚', 'TikTok'],
                'devops': ['部署', '嬕机', '监控', 'Docker', '故障', '重启'],
            }
            for subsidiary, keywords in new_keyword_mapping.items():
                for keyword in keywords:
                    if keyword in task_desc:
                        return subsidiary

        logger.warning(f"无法确定目标子公司，intent.target_agency: {intent_result.target_agency}")
        return None

    async def daily_loop(self):
        logger.info("墨麟 daily loop started")
        if self.memory_manager is None:
            await self.initialize()

        data = await self.db.get_daily_summary()
        try:
            historical_decisions = await self.memory_manager.retrieve(
                key="successful_decision",
                scenario=MemoryScenario.LONG_TERM,
                query="高ROI成功决策",
                limit=5
            )
            if historical_decisions:
                logger.info(f"从长期记忆中检索到 {len(historical_decisions)} 条历史成功决策")
        except Exception as e:
            logger.warning(f"从长期记忆检索失败: {e}")

        # Evolution 引擎评估
        if self.evolution_engine and data.get("total_revenue", 0) > 0:
            try:
                eval_result = await self.evolution_engine.evaluate({
                    "status": "success" if data.get("deals", 0) > 0 else "partial_success",
                    "score": min(10, data.get("roi", 0) * 2),
                    "output": data,
                    "metadata": {"source": "daily_loop"},
                })
                logger.info(f"Evolution engine: {eval_result.outcome.value} (score={eval_result.score})")
            except Exception as e:
                logger.debug(f"Evolution engine error: {e}")

        analysis = await self.data_brain.analyze_daily()
        alerts = self._check_alerts(data)
        if data.get("total_revenue", 0) > 0:
            decision = await self.run_async(
                user_input=f"今日数据：{json.dumps(data, ensure_ascii=False)}，请给出明日策略建议",
                budget=data.get("remaining_budget", 100),
                timeline="明天", target_revenue=data.get("target_revenue", 1000))
            strategy = await self.strategy_engine.generate(decision)
            await send_alert("墨麟每日循环完成", f"决策：{decision.get('decision', 'unknown')}", "info")
            return {"status": "ok", "analysis": analysis, "decision": decision, "strategy": strategy, "alerts": alerts}
        return {"status": "insufficient_data", "analysis": analysis, "alerts": alerts}

    async def proactive_morning_scan(self):
        """每日早报：CEO 主动扫描各子公司状态，不需要人触发"""
        if self.memory_manager is None:
            await self.initialize()

        # 汇总关键指标
        try:
            data = await self.db.get_daily_summary()
        except Exception:
            data = {}

        states = {
            "date": data.get("date", "unknown"),
            "leads": data.get("leads", 0),
            "deals": data.get("deals", 0),
            "revenue": data.get("total_revenue", 0),
            "api_cost": data.get("api_cost", 0),
            "cvr": data.get("cvr", 0),
            "roi": data.get("roi", 0),
        }

        briefing = await self.router.call_async(
            prompt=f"当前状态：{json.dumps(states, ensure_ascii=False)}，生成今日执行优先级和行动清单",
            system=self.system_prompt,
            task_type="ceo_decision"
        )

        await send_alert("墨麟每日早报", f"今日状态：{json.dumps(states, ensure_ascii=False)}\n{briefing.get('text', '')[:500]}", "normal")
        return {"status": "morning_scan_complete", "states": states, "briefing": briefing}

    def _check_alerts(self, data):
        alerts = []
        if data.get("cvr", 0) < 0.03:
            alerts.append({"type": "CVR_LOW", "value": data["cvr"], "threshold": 0.03})
        if data.get("api_cost_rate", 0) > 0.3:
            alerts.append({"type": "API_COST_HIGH", "value": data["api_cost_rate"]})
        return alerts
