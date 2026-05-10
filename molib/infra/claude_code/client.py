"""
Claude Code Client Library
Simplified client for interacting with Claude Code CLI.
"""

import asyncio
import json
from typing import Dict, Any, Optional
from loguru import logger

from .cli_executor import ClaudeCodeCLIExecutor, ClaudeCodeError


class ClaudeCodeClient:
    """Claude Code 客户端"""

    def __init__(self, cli_path: str = "claude", timeout: int = 30):
        """
        初始化客户端

        Args:
            cli_path: Claude Code CLI 路径
            timeout: 默认超时时间（秒）
        """
        self.executor = ClaudeCodeCLIExecutor(cli_path=cli_path, timeout=timeout)
        self.available = True
        logger.info(f"Claude Code client initialized with CLI path: {cli_path}")

    async def analyze_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用 Claude Code 分析任务

        Args:
            task: 任务字典，包含 'description' 和 'context' 字段

        Returns:
            Dict[str, Any]: 包含子任务分解的结果

        Raises:
            ClaudeCodeError: 分析失败
        """
        try:
            description = task.get("description", "")
            context = task.get("context", {})
            result = await self.executor.analyze_task(description, context)
            return result
        except ClaudeCodeError as e:
            logger.error(f"Task analysis failed: {e}")
            # 标记客户端不可用，触发降级
            self.available = False
            raise

    async def review_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        代码审查

        Args:
            code: 要审查的代码
            language: 编程语言

        Returns:
            Dict[str, Any]: 包含审查报告的结果
        """
        try:
            result = await self.executor.review_code(code, language)
            return result
        except ClaudeCodeError as e:
            logger.error(f"Code review failed: {e}")
            raise

    async def generate_plan(self, requirements: str) -> Dict[str, Any]:
        """
        生成实现计划

        Args:
            requirements: 需求描述

        Returns:
            Dict[str, Any]: 包含实施计划的结果
        """
        try:
            result = await self.executor.generate_plan(requirements)
            return result
        except ClaudeCodeError as e:
            logger.error(f"Plan generation failed: {e}")
            raise

    async def debug_error(self, error_message: str, code_context: str = "") -> Dict[str, Any]:
        """
        调试错误

        Args:
            error_message: 错误信息
            code_context: 代码上下文

        Returns:
            Dict[str, Any]: 包含调试建议的结果
        """
        try:
            result = await self.executor.debug_error(error_message, code_context)
            return result
        except ClaudeCodeError as e:
            logger.error(f"Error debugging failed: {e}")
            raise

    async def optimize_prompt(self, original_prompt: str, task_description: str) -> Dict[str, Any]:
        """
        优化提示词

        Args:
            original_prompt: 原始提示词
            task_description: 任务描述

        Returns:
            Dict[str, Any]: 包含优化后的提示词
        """
        try:
            result = await self.executor.optimize_prompt(original_prompt, task_description)
            return result
        except ClaudeCodeError as e:
            logger.error(f"Prompt optimization failed: {e}")
            raise

    async def aggregate_results(self, results_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        聚合多个任务结果

        Args:
            results_data: 包含原始任务和结果的数据

        Returns:
            Dict[str, Any]: 聚合后的结果
        """
        prompt = f"""
请聚合以下任务结果并生成综合报告：

原始任务：{json.dumps(results_data.get('original_task', {}), ensure_ascii=False, indent=2)}

结果列表：
{json.dumps(results_data.get('results', []), ensure_ascii=False, indent=2)}

请输出 JSON 格式的聚合报告：
{{
  "summary": "...",
  "key_insights": [...],
  "recommendations": [...],
  "success_rate": 0.95,
  "next_steps": [...]
}}
"""
        try:
            result = await self.executor.execute_command(
                ["--print", "--thinking=adaptive"],
                prompt
            )
            return result
        except ClaudeCodeError as e:
            logger.error(f"Results aggregation failed: {e}")
            raise

    async def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证配置

        Args:
            config: 配置字典

        Returns:
            Dict[str, Any]: 验证结果
        """
        prompt = f"""
请验证以下配置的合理性和完整性：

配置：
{json.dumps(config, ensure_ascii=False, indent=2)}

请输出 JSON 格式的验证报告：
{{
  "valid": true|false,
  "issues": [
    {{"type": "error|warning", "field": "...", "description": "...", "suggestion": "..."}},
    ...
  ],
  "recommendations": [...]
}}
"""
        try:
            result = await self.executor.execute_command(
                ["--print", "--thinking=adaptive"],
                prompt
            )
            return result
        except ClaudeCodeError as e:
            logger.error(f"Config validation failed: {e}")
            raise

    def is_available(self) -> bool:
        """
        检查 Claude Code 客户端是否可用

        Returns:
            bool: 客户端可用状态
        """
        return self.available

    def set_available(self, available: bool):
        """
        设置客户端可用状态

        Args:
            available: 可用状态
        """
        self.available = available
        logger.info(f"Claude Code client availability set to: {available}")


# 全局客户端实例
_client_instance: Optional[ClaudeCodeClient] = None


async def get_client(cli_path: str = "claude", timeout: int = 30) -> ClaudeCodeClient:
    """
    获取全局 Claude Code 客户端实例

    Args:
        cli_path: Claude Code CLI 路径
        timeout: 超时时间

    Returns:
        ClaudeCodeClient: 客户端实例
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = ClaudeCodeClient(cli_path=cli_path, timeout=timeout)
        logger.info(f"Global Claude Code client initialized")
    return _client_instance


async def test_connection(cli_path: str = "claude") -> bool:
    """
    测试 Claude Code CLI 连接

    Args:
        cli_path: CLI 路径

    Returns:
        bool: 连接是否成功
    """
    try:
        executor = ClaudeCodeCLIExecutor(cli_path=cli_path, timeout=5)
        # 执行简单命令测试连接
        result = await executor.execute_command(["--version"])
        logger.info(f"Claude Code connection test successful: {result}")
        return True
    except Exception as e:
        logger.error(f"Claude Code connection test failed: {e}")
        return False


