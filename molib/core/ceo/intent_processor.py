"""
意图理解层（Intent Processor）v6.6
在CEO决策前进行轻量级预处理，降低无效调用成本约40%
"""

import re
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List
from loguru import logger


class IntentType(Enum):
    """意图类型枚举"""
    TRIVIAL = 'trivial'        # 不需要CEO的简单请求（问候、状态查询）
    QUERY = 'query'            # 状态查询（进度、结果）
    TASK = 'task'              # 需要Agency执行的任务
    DECISION = 'decision'      # 需要CEO决策
    EMERGENCY = 'emergency'    # 紧急任务（最高优先级）
    NEED_INFO = 'need_info'    # 缺少必要信息


@dataclass
class IntentResult:
    """意图处理结果"""
    intent_type: IntentType
    priority: int              # 1-10，数字越大优先级越高
    estimated_cost_cny: float  # 预估API调用费用（元）
    missing_fields: List[str]  # 缺失的必要字段
    target_agency: Optional[str]  # 预路由Agency
    preprocessed_task: str     # 规范化后的任务描述
    should_pass_to_ceo: bool   # 是否需要转发给CEO
    response: Optional[str] = None  # 直接响应（如trivial请求）
    budget_check: Dict[str, Any] = None  # 预算检查结果


class IntentProcessor:
    """
    意图理解处理器
    负责NLU预处理、任务拆解、预算预检、缺字段追问
    """

    # 简单请求模式（不需要CEO处理）
    TRIVIAL_PATTERNS = [
        r'^(你好|hi|hello|在吗|在不|好的|收到|ok|谢谢|thx|thanks|拜拜|再见)',
        r'^(查询|查一下|看看|查看|check).{0,10}(状态|进度|结果|status)$',
        r'^[？?]+$',  # 纯问号
        r'^test$',
    ]

    # v8 整改: 不再强制追问任何字段，CEO 会合理假设缺失信息
    REQUIRED_FIELDS = {}

    # Agency关键词映射（从 subsidiaries.toml 动态加载，消除硬编码 -- F6）
    AGENCY_KEYWORDS: Dict[str, List[str]] = {}

    # 简单响应映射
    TRIVIAL_RESPONSES = {
        'greeting': '你好！我是墨麟AI助理，请告诉我需要什么帮助？',
        'status_query': '系统运行正常，所有服务在线。',
        'thanks': '不客气，随时为您服务！',
        'goodbye': '再见，有问题随时找我！',
    }

    def __init__(self, daily_budget_cny: float = 50.0):
        self.daily_budget_cny = daily_budget_cny
        self.today_spent = 0.0
        self._load_agency_keywords()
        logger.info(f"意图处理器初始化完成，每日预算: ¥{daily_budget_cny}")

    def _load_agency_keywords(self):
        """F6: 从 subsidiaries.toml 动态加载关键词（唯一权威来源）"""
        if IntentProcessor.AGENCY_KEYWORDS:
            return
        try:
            import toml
            from pathlib import Path
            config_path = Path(__file__).resolve().parent.parent.parent / "config" / "subsidiaries.toml"
            if config_path.exists():
                data = toml.load(config_path)
                for agency in data.get("agencies", []):
                    aid = agency.get("id", "")
                    kws = agency.get("trigger_keywords", [])
                    if aid and kws:
                        IntentProcessor.AGENCY_KEYWORDS[aid] = kws[:8]
                logger.info(f"从 subsidiaries.toml 动态加载 {len(IntentProcessor.AGENCY_KEYWORDS)} 个子公司关键词")
        except Exception as e:
            logger.warning(f"加载关键词失败: {e}，回退到空字典")

    def process(self, message: str, context: Dict[str, Any] = None) -> IntentResult:
        """
        处理用户消息，返回意图分析结果

        Args:
            message: 用户输入消息
            context: 上下文信息（预算、时间线等）

        Returns:
            IntentResult: 意图分析结果
        """
        context = context or {}
        message = message.strip()
        start_time = time.time()

        # 1. 检查是否是trivial请求（带明确任务指示词的消息跳过，直接送CEO推理）
        if not self._has_clear_task(message):
            trivial_result = self._check_trivial(message)
            if trivial_result:
                trivial_result.priority = 1
                trivial_result.estimated_cost_cny = 0.001
                logger.debug(f"识别为trivial请求: {message}")
                return trivial_result

        # 2. 预算检查
        budget_check = self._check_budget(context.get('estimated_cost', 0.1))

        # 3. 预路由Agency
        target_agency = self._pre_route_agency(message)

        # 4. 检查必要字段
        missing_fields = self._check_required_fields(message, context, target_agency)

        # 5. 确定意图类型
        if missing_fields:
            intent_type = IntentType.NEED_INFO
        elif target_agency:
            intent_type = IntentType.TASK
        else:
            intent_type = IntentType.DECISION

        # 6. 计算优先级
        priority = self._calculate_priority(message, target_agency, intent_type)

        # 7. 估算成本
        estimated_cost = self._estimate_cost(intent_type, target_agency)

        # 8. 预处理任务描述
        preprocessed_task = self._preprocess_task(message, target_agency)

        # 9. 确定是否需要CEO
        should_pass_to_ceo = self._should_pass_to_ceo(intent_type, missing_fields, budget_check)

        result = IntentResult(
            intent_type=intent_type,
            priority=priority,
            estimated_cost_cny=estimated_cost,
            missing_fields=missing_fields,
            target_agency=target_agency,
            preprocessed_task=preprocessed_task,
            should_pass_to_ceo=should_pass_to_ceo,
            budget_check=budget_check
        )

        latency = (time.time() - start_time) * 1000
        logger.info(f"意图处理完成: {intent_type.value}, 目标: {target_agency}, 耗时: {latency:.1f}ms")

        return result

    def _check_trivial(self, message: str) -> Optional[IntentResult]:
        """检查是否是简单请求"""
        message_lower = message.lower()

        # 匹配问候语
        if re.match(r'^(你好|hi|hello|hey|嗨)', message_lower):
            return IntentResult(
                intent_type=IntentType.TRIVIAL,
                priority=1,
                estimated_cost_cny=0.001,
                missing_fields=[],
                target_agency=None,
                preprocessed_task=message,
                should_pass_to_ceo=False,
                response=self.TRIVIAL_RESPONSES['greeting']
            )

        # 匹配状态查询（避免匹配"在线教育"等复合词）
        if re.search(r'(状态|进度|结果|运行正常|一切正常|是否正常|在线状态|status)', message_lower):
            return IntentResult(
                intent_type=IntentType.QUERY,
                priority=1,
                estimated_cost_cny=0.001,
                missing_fields=[],
                target_agency=None,
                preprocessed_task=message,
                should_pass_to_ceo=False,
                response=self.TRIVIAL_RESPONSES['status_query']
            )

        # 匹配感谢
        if re.search(r'(谢谢|感谢|thx|thanks|thank you)', message_lower):
            return IntentResult(
                intent_type=IntentType.TRIVIAL,
                priority=1,
                estimated_cost_cny=0.001,
                missing_fields=[],
                target_agency=None,
                preprocessed_task=message,
                should_pass_to_ceo=False,
                response=self.TRIVIAL_RESPONSES['thanks']
            )

        # 匹配再见
        if re.search(r'(再见|拜拜|bye|goodbye)', message_lower):
            return IntentResult(
                intent_type=IntentType.TRIVIAL,
                priority=1,
                estimated_cost_cny=0.001,
                missing_fields=[],
                target_agency=None,
                preprocessed_task=message,
                should_pass_to_ceo=False,
                response=self.TRIVIAL_RESPONSES['goodbye']
            )

        return None

    def _check_budget(self, estimated_cost: float) -> Dict[str, Any]:
        """检查预算状态"""
        # 模拟今日花费（实际应从数据库读取）
        remaining = max(0, self.daily_budget_cny - self.today_spent)
        budget_ratio = remaining / self.daily_budget_cny if self.daily_budget_cny > 0 else 1.0

        status = "OK"
        if budget_ratio < 0.2:  # 剩余20%
            status = "WARNING"
        elif budget_ratio < 0.05:  # 剩余5%
            status = "CRITICAL"

        return {
            "daily_budget_cny": self.daily_budget_cny,
            "today_spent_cny": self.today_spent,
            "remaining_cny": remaining,
            "budget_ratio": budget_ratio,
            "status": status,
            "can_proceed": estimated_cost <= remaining or status == "OK"
        }

    def _pre_route_agency(self, message: str) -> Optional[str]:
        """预路由到合适的Agency"""
        for agency, keywords in self.AGENCY_KEYWORDS.items():
            if any(keyword in message for keyword in keywords):
                logger.debug(f"预路由到Agency: {agency}, 关键词匹配")
                return agency
        return None

    # 明确任务指示词：包含这些词的消息视为已明确的行动任务，不强制追问字段
    _TASK_INDICATORS = [
        '做', '制作', '编写', '写', '开发', '设计', '创建', '调研', '分析',
        '帮我', '我要', '我想', '帮我做', '给我', '请', '需要', '帮忙',
        '产品', '工具', '方案', 'SaaS', 'MVP', 'APP', '小程序', '系统', '平台',
        '报价', '接单', '竞品', '报告', '文档', '计划', '策略', '优化',
        '配置', '部署', '搭建', '启动', '上线', '发布',
    ]

    def _has_clear_task(self, message: str) -> bool:
        """检测消息是否包含明确的执行意图"""
        return any(indicator in message for indicator in self._TASK_INDICATORS)

    def _check_required_fields(self, message: str, context: Dict[str, Any], target_agency: Optional[str]) -> List[str]:
        # 明确任务：不要追问，CEO 会合理假设缺失信息
        if self._has_clear_task(message):
            return []

        missing = []

        # 检查预算字段
        if not context.get('budget') and '预算' not in message:
            if target_agency in ['ads', 'growth', 'order']:
                missing.append('budget（预算）')

        # 检查时间线字段
        if not context.get('timeline') and '时间' not in message and '天' not in message and '周' not in message:
            if target_agency in ['dev', 'order', 'product']:
                missing.append('timeline（时间线）')

        # 检查目标收入字段（仅限CEO决策，无目标子公司的场景）
        if not context.get('target_revenue') and '收入' not in message and 'ROI' not in message:
            if not target_agency:
                missing.append('target_revenue（目标收入）')

        return missing

    def _calculate_priority(self, message: str, target_agency: Optional[str], intent_type: IntentType) -> int:
        """计算任务优先级（1-10）"""
        priority = 5  # 默认优先级

        # 紧急关键词
        if '紧急' in message or '急' in message[:4] or 'urgent' in message.lower():
            priority = 9

        # 高价值Agency优先级更高
        if target_agency == 'ads':
            priority = max(priority, 8)  # 广告任务优先
        elif target_agency == 'order':
            priority = max(priority, 7)  # 订单任务次优先

        # 意图类型影响优先级
        if intent_type == IntentType.EMERGENCY:
            priority = 10
        elif intent_type == IntentType.DECISION:
            priority = max(priority, 6)

        return min(max(priority, 1), 10)  # 确保在1-10范围内

    def _estimate_cost(self, intent_type: IntentType, target_agency: Optional[str]) -> float:
        """估算API调用成本"""
        base_cost = 0.02  # 基础成本

        # 根据意图类型调整
        if intent_type == IntentType.TRIVIAL:
            return 0.001
        elif intent_type == IntentType.QUERY:
            return 0.005
        elif intent_type == IntentType.TASK:
            return 0.05
        elif intent_type == IntentType.DECISION:
            return 0.15

        # 根据Agency调整
        if target_agency in ['ads', 'order', 'ai']:
            base_cost *= 1.5  # 高价值任务成本更高

        return base_cost

    def _preprocess_task(self, message: str, target_agency: Optional[str]) -> str:
        """预处理任务描述"""
        # 添加Agency标签
        if target_agency:
            return f'[{target_agency}] {message}'
        return f'[CEO决策] {message}'

    def _should_pass_to_ceo(self, intent_type: IntentType, missing_fields: List[str],
                           budget_check: Dict[str, Any]) -> bool:
        """确定是否需要传递给CEO"""
        # trivial和query不需要CEO
        if intent_type in [IntentType.TRIVIAL, IntentType.QUERY]:
            return False

        # v8 整改: 缺失信息不阻断 CEO，CEO 会合理假设或追问
        if missing_fields:
            return True  # 让 CEO 决定是否需要追问，而不是拦截

        # 预算不足且非紧急任务
        if not budget_check.get('can_proceed', True) and intent_type != IntentType.EMERGENCY:
            return False

        return True

    def get_questions_for_missing_fields(self, missing_fields: List[str]) -> List[str]:
        """为缺失字段生成追问问题"""
        questions_map = {
            'budget（预算）': '请问预算是多少？',
            'timeline（时间线）': '请问时间要求是怎样的？',
            'target_revenue（目标收入）': '请问目标收入是多少？',
        }

        return [questions_map.get(field, f'请提供 {field}') for field in missing_fields]

    def update_spending(self, amount_cny: float):
        """更新花费记录（模拟）"""
        self.today_spent += amount_cny
        logger.debug(f"更新花费: ¥{amount_cny:.4f}, 今日总计: ¥{self.today_spent:.2f}")