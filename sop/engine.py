"""
SOP (Standard Operating Procedure) 自动化引擎
支持YAML定义的标准化操作流程自动化
"""

import os
import time
import asyncio
from typing import Dict, Any, List, Optional
from enum import Enum
from pathlib import Path
from loguru import logger

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    logger.warning("PyYAML未安装，SOP定义将不可用。使用 'pip install pyyaml' 安装。")


class SOPStatus(Enum):
    """SOP执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class StepType(Enum):
    """步骤类型"""
    MANUAL = "manual"
    AUTOMATED = "automated"
    APPROVAL = "approval"
    NOTIFICATION = "notification"
    DECISION = "decision"


class SOPEngine:
    """SOP自动化引擎"""

    def __init__(self, definitions_dir: Optional[str] = None):
        self.definitions_dir = definitions_dir or os.path.join(
            Path(__file__).resolve().parent.parent, "sop", "definitions"
        )
        self.definitions: Dict[str, Dict[str, Any]] = {}
        self.active_procedures: Dict[str, Dict[str, Any]] = {}
        self.enabled = os.getenv("SOP_AUTOMATION_ENABLED", "false").lower() == "true"

        if not self.enabled:
            logger.info("SOP自动化已禁用")
            return

        self._load_definitions()

    def _load_definitions(self):
        """加载SOP定义"""
        if not YAML_AVAILABLE:
            logger.warning("YAML不可用，无法加载SOP定义")
            return

        definitions_path = Path(self.definitions_dir)
        if not definitions_path.exists():
            logger.info(f"SOP定义目录不存在: {self.definitions_dir}")
            return

        yaml_files = list(definitions_path.glob("**/*.yaml")) + list(definitions_path.glob("**/*.yml"))
        logger.info(f"发现 {len(yaml_files)} 个SOP定义文件")

        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    definition = yaml.safe_load(f)

                if not definition or "id" not in definition:
                    logger.warning(f"SOP定义文件缺少ID: {yaml_file}")
                    continue

                sop_id = definition["id"]
                self.definitions[sop_id] = definition
                logger.info(f"加载SOP定义: {sop_id} - {definition.get('name', '未命名')}")

            except Exception as e:
                logger.error(f"加载SOP定义文件失败 {yaml_file}: {e}")

        logger.info(f"共加载 {len(self.definitions)} 个SOP定义")

    def get_definition(self, sop_id: str) -> Optional[Dict[str, Any]]:
        """获取SOP定义"""
        return self.definitions.get(sop_id)

    def list_definitions(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出SOP定义"""
        definitions_list = []
        for sop_id, definition in self.definitions.items():
            if category and definition.get("category") != category:
                continue
            definitions_list.append({
                "id": sop_id,
                "name": definition.get("name", "未命名"),
                "description": definition.get("description", ""),
                "category": definition.get("category", "general"),
                "version": definition.get("version", "1.0"),
                "steps_count": len(definition.get("steps", [])),
                "enabled": definition.get("enabled", True)
            })
        return definitions_list

    async def start_procedure(self, sop_id: str, context: Dict[str, Any]) -> str:
        """启动SOP流程"""
        if not self.enabled:
            return "SOP自动化已禁用"

        definition = self.get_definition(sop_id)
        if not definition:
            return f"SOP定义不存在: {sop_id}"

        if not definition.get("enabled", True):
            return f"SOP已禁用: {sop_id}"

        # 生成流程ID
        import uuid
        procedure_id = f"{sop_id}_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        # 创建流程实例
        procedure = {
            "id": procedure_id,
            "sop_id": sop_id,
            "definition": definition,
            "context": context,
            "status": SOPStatus.RUNNING.value,
            "current_step": 0,
            "steps_history": [],
            "created_at": time.time(),
            "updated_at": time.time(),
            "variables": context.copy()
        }

        self.active_procedures[procedure_id] = procedure
        logger.info(f"启动SOP流程: {procedure_id} ({definition.get('name')})")

        # 异步执行流程
        asyncio.create_task(self._execute_procedure(procedure_id))

        return procedure_id

    async def _execute_procedure(self, procedure_id: str):
        """执行SOP流程"""
        if procedure_id not in self.active_procedures:
            return

        procedure = self.active_procedures[procedure_id]
        definition = procedure["definition"]
        steps = definition.get("steps", [])

        logger.info(f"执行SOP流程 {procedure_id}: 共 {len(steps)} 步")

        for step_index, step_def in enumerate(steps):
            if procedure["status"] != SOPStatus.RUNNING.value:
                logger.info(f"流程 {procedure_id} 状态变为 {procedure['status']}，停止执行")
                break

            # 更新当前步骤
            procedure["current_step"] = step_index
            procedure["updated_at"] = time.time()

            # 执行步骤
            step_result = await self._execute_step(procedure_id, step_def, step_index)

            # 记录步骤历史
            step_history = {
                "step_index": step_index,
                "step_name": step_def.get("name", f"步骤{step_index + 1}"),
                "step_type": step_def.get("type", "manual"),
                "result": step_result,
                "timestamp": time.time()
            }
            procedure["steps_history"].append(step_history)

            # 检查步骤结果，决定是否继续
            if not step_result.get("success", False):
                if step_def.get("critical", False):
                    # 关键步骤失败，停止流程
                    procedure["status"] = SOPStatus.FAILED.value
                    logger.error(f"SOP流程 {procedure_id} 关键步骤失败: {step_def.get('name')}")
                    break
                else:
                    logger.warning(f"SOP流程 {procedure_id} 非关键步骤失败: {step_def.get('name')}")

            # 步骤间延迟
            delay = step_def.get("delay_after", 0)
            if delay > 0:
                await asyncio.sleep(delay)

        # 流程完成
        if procedure["status"] == SOPStatus.RUNNING.value:
            procedure["status"] = SOPStatus.COMPLETED.value
            procedure["updated_at"] = time.time()
            logger.info(f"SOP流程完成: {procedure_id}")

            # SOP 反馈管道: 流程完成后自动提炼知识和检查偏差
            try:
                from sop.sop_feedback import get_sop_feedback
                feedback = get_sop_feedback()
                await feedback.post_task_hook(
                    task_result=procedure,
                    task_meta={
                        "task_type": "sop_execution",
                        "sop_id": procedure.get("sop_id"),
                        "description": definition.get("name", ""),
                    },
                )
            except Exception as e:
                logger.warning(f"SOP 反馈管道执行失败: {e}")

    async def _execute_step(self, procedure_id: str, step_def: Dict[str, Any], step_index: int) -> Dict[str, Any]:
        """执行单个步骤"""
        step_type = step_def.get("type", "manual")
        step_name = step_def.get("name", f"步骤{step_index + 1}")

        logger.info(f"执行SOP步骤: {procedure_id} - {step_name} ({step_type})")

        try:
            if step_type == "automated":
                return await self._execute_automated_step(procedure_id, step_def)
            elif step_type == "approval":
                return await self._execute_approval_step(procedure_id, step_def)
            elif step_type == "notification":
                return await self._execute_notification_step(procedure_id, step_def)
            elif step_type == "decision":
                return await self._execute_decision_step(procedure_id, step_def)
            else:  # manual
                return await self._execute_manual_step(procedure_id, step_def)
        except Exception as e:
            logger.error(f"执行SOP步骤失败 {step_name}: {e}")
            return {"success": False, "error": str(e), "step_type": step_type}

    async def _execute_automated_step(self, procedure_id: str, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """执行自动化步骤"""
        action = step_def.get("action", "")
        parameters = step_def.get("parameters", {})

        # 根据action类型执行不同的自动化操作
        if action == "call_api":
            # 调用API
            return {"success": True, "action": "call_api", "result": "API调用成功"}
        elif action == "send_email":
            # 发送邮件
            return {"success": True, "action": "send_email", "result": "邮件发送成功"}
        elif action == "create_task":
            # 创建任务
            return {"success": True, "action": "create_task", "result": "任务创建成功"}
        else:
            # 默认处理
            return {"success": True, "action": action, "result": "自动化步骤执行完成"}

    async def _execute_approval_step(self, procedure_id: str, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """执行审批步骤"""
        approvers = step_def.get("approvers", [])
        timeout = step_def.get("timeout", 86400)  # 默认24小时

        # 在实际实现中，这里会创建审批请求并等待审批
        logger.info(f"创建审批请求: 审批人={approvers}, 超时={timeout}秒")

        # 模拟审批过程
        await asyncio.sleep(2)  # 模拟等待

        # 模拟审批结果（实际中应根据用户输入决定）
        approved = True  # 假设批准

        return {
            "success": True,
            "type": "approval",
            "approved": approved,
            "approvers": approvers,
            "result": "批准" if approved else "拒绝"
        }

    async def _execute_notification_step(self, procedure_id: str, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """执行通知步骤"""
        channels = step_def.get("channels", ["email", "feishu"])
        message = step_def.get("message", "")
        recipients = step_def.get("recipients", [])

        logger.info(f"发送通知: 渠道={channels}, 接收人={recipients}, 消息={message[:50]}...")

        # 模拟发送通知
        return {
            "success": True,
            "type": "notification",
            "channels": channels,
            "recipients": recipients,
            "result": "通知发送成功"
        }

    async def _execute_decision_step(self, procedure_id: str, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """执行决策步骤"""
        decision_logic = step_def.get("logic", {})
        options = step_def.get("options", [])

        # 根据决策逻辑做出决策
        # 简化实现：总是选择第一个选项
        selected_option = options[0] if options else None

        return {
            "success": True,
            "type": "decision",
            "selected_option": selected_option,
            "options": options,
            "result": f"选择选项: {selected_option}"
        }

    async def _execute_manual_step(self, procedure_id: str, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """执行手动步骤"""
        instructions = step_def.get("instructions", "")
        estimated_time = step_def.get("estimated_time", 0)

        logger.info(f"等待手动操作: {instructions[:50]}..., 预计时间: {estimated_time}分钟")

        # 手动步骤需要人工干预，这里只是记录
        return {
            "success": True,
            "type": "manual",
            "instructions": instructions,
            "estimated_time": estimated_time,
            "result": "等待手动操作完成"
        }

    def get_procedure_status(self, procedure_id: str) -> Optional[Dict[str, Any]]:
        """获取流程状态"""
        if procedure_id not in self.active_procedures:
            return None

        procedure = self.active_procedures[procedure_id].copy()
        # 移除大字段以减少响应大小
        if "definition" in procedure:
            del procedure["definition"]
        if "context" in procedure:
            del procedure["context"]

        return procedure

    async def stop_procedure(self, procedure_id: str) -> bool:
        """停止流程"""
        if procedure_id not in self.active_procedures:
            return False

        procedure = self.active_procedures[procedure_id]
        if procedure["status"] == SOPStatus.RUNNING.value:
            procedure["status"] = SOPStatus.PAUSED.value
            procedure["updated_at"] = time.time()
            logger.info(f"SOP流程已暂停: {procedure_id}")
            return True

        return False

    async def resume_procedure(self, procedure_id: str) -> bool:
        """恢复流程"""
        if procedure_id not in self.active_procedures:
            return False

        procedure = self.active_procedures[procedure_id]
        if procedure["status"] == SOPStatus.PAUSED.value:
            procedure["status"] = SOPStatus.RUNNING.value
            procedure["updated_at"] = time.time()
            logger.info(f"SOP流程已恢复: {procedure_id}")

            # 继续执行
            asyncio.create_task(self._execute_procedure(procedure_id))
            return True

        return False


# 全局SOP引擎实例
_sop_engine_instance = None

def get_sop_engine() -> SOPEngine:
    """获取全局SOP引擎实例（单例）"""
    global _sop_engine_instance
    if _sop_engine_instance is None:
        _sop_engine_instance = SOPEngine()
    return _sop_engine_instance