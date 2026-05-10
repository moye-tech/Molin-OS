"""
Claude Code CLI Executor
Direct CLI integration for executing Claude Code commands as subprocesses.
"""

import asyncio
import json
import subprocess
from typing import Dict, Any, Optional
from loguru import logger


class ClaudeCodeError(Exception):
    """Claude Code 执行错误"""
    pass


class ClaudeCodeCLIExecutor:
    """Claude Code CLI 执行器"""

    def __init__(self, cli_path: str = "claude", timeout: int = 30):
        """
        初始化 CLI 执行器

        Args:
            cli_path: Claude Code CLI 路径（默认为 'claude'）
            timeout: 命令执行超时时间（秒）
        """
        self.cli_path = cli_path
        self.timeout = timeout

    async def execute_command(self, args: list, input_data: str = None) -> Dict[str, Any]:
        """
        执行 Claude Code CLI 命令

        Args:
            args: CLI 参数列表
            input_data: 输入数据（作为标准输入）

        Returns:
            Dict[str, Any]: 解析后的 JSON 输出或原始输出

        Raises:
            ClaudeCodeError: 执行失败或超时
        """
        try:
            cmd = [self.cli_path] + args

            logger.debug(f"Executing Claude Code command: {' '.join(cmd)}")

            # 准备子进程
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE if input_data else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # 执行命令
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=input_data.encode() if input_data else None),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                # 超时，终止进程
                process.terminate()
                await process.wait()
                logger.error(f"Claude Code CLI timeout after {self.timeout}s")
                raise ClaudeCodeError(f"CLI execution timeout after {self.timeout} seconds")

            # 检查返回码
            if process.returncode == 0:
                output = stdout.decode().strip()

                # 尝试解析 JSON 输出
                if output:
                    try:
                        return json.loads(output)
                    except json.JSONDecodeError:
                        # 如果不是 JSON，返回原始输出
                        logger.debug("CLI output is not JSON, returning raw output")
                        return {"output": output}
                else:
                    logger.warning("Claude Code CLI returned empty output")
                    return {"output": ""}
            else:
                error_msg = stderr.decode().strip()
                logger.error(f"Claude Code CLI failed with return code {process.returncode}: {error_msg}")
                raise ClaudeCodeError(f"CLI execution failed: {error_msg}")

        except FileNotFoundError:
            logger.error(f"Claude Code CLI not found at path: {self.cli_path}")
            raise ClaudeCodeError(f"Claude Code CLI not found at path: {self.cli_path}")
        except Exception as e:
            logger.error(f"Unexpected error executing Claude Code CLI: {e}")
            raise ClaudeCodeError(f"Unexpected error: {e}")

    async def analyze_task(self, task_description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用 Claude Code 分析任务并分解为子任务

        Args:
            task_description: 任务描述
            context: 上下文信息

        Returns:
            Dict[str, Any]: 包含子任务分解的结果
        """
        prompt = f"""
请分析以下任务并分解为可执行的子任务：

任务：{task_description}

上下文：{json.dumps(context, ensure_ascii=False, indent=2)}

请输出 JSON 格式：
{{
  "subtasks": [
    {{"id": "subtask_1", "description": "...", "worker_type": "...", "estimated_time": 300}},
    ...
  ],
  "dependencies": [],
  "estimated_total_time": 1800
}}
"""
        try:
            result = await self.execute_command(
                ["--print", "--thinking=adaptive"],
                prompt
            )
            return result
        except ClaudeCodeError as e:
            logger.error(f"Task analysis failed: {e}")
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
        prompt = f"""
请审查以下{language}代码：

```{language}
{code}
```

请输出 JSON 格式的审查报告：
{{
  "issues": [
    {{"type": "bug|warning|suggestion", "line": 1, "description": "...", "suggestion": "..."}},
    ...
  ],
  "score": 85,
  "summary": "..."
}}
"""
        try:
            result = await self.execute_command(
                ["--print", "--thinking=adaptive"],
                prompt
            )
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
        prompt = f"""
请为以下需求生成详细的实现计划：

{requirements}

请输出 JSON 格式的计划：
{{
  "phases": [
    {{"name": "...", "tasks": [...], "duration_hours": 2, "dependencies": []}},
    ...
  ],
  "total_duration_hours": 8,
  "resources_needed": [...],
  "risks": [...]
}}
"""
        try:
            result = await self.execute_command(
                ["--print", "--thinking=adaptive"],
                prompt
            )
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
        prompt = f"""
请分析以下错误并提供调试建议：

错误信息：{error_message}

代码上下文：
{code_context}

请输出 JSON 格式的调试报告：
{{
  "root_cause": "...",
  "possible_solutions": [
    {{"solution": "...", "confidence": 0.9, "implementation_steps": [...]}},
    ...
  ],
  "prevention_tips": [...]
}}
"""
        try:
            result = await self.execute_command(
                ["--print", "--thinking=adaptive"],
                prompt
            )
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
        prompt = f"""
请优化以下提示词以更好地完成任务：

任务描述：{task_description}

原始提示词：
{original_prompt}

请输出 JSON 格式的优化结果：
{{
  "optimized_prompt": "...",
  "improvements": [...],
  "expected_impact": "..."
}}
"""
        try:
            result = await self.execute_command(
                ["--print", "--thinking=adaptive"],
                prompt
            )
            return result
        except ClaudeCodeError as e:
            logger.error(f"Prompt optimization failed: {e}")
            raise


# 全局执行器实例
_executor_instance: Optional[ClaudeCodeCLIExecutor] = None


async def get_cli_executor(cli_path: str = "claude", timeout: int = 30) -> ClaudeCodeCLIExecutor:
    """
    获取全局 CLI 执行器实例

    Args:
        cli_path: Claude Code CLI 路径
        timeout: 超时时间

    Returns:
        ClaudeCodeCLIExecutor: CLI 执行器实例
    """
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = ClaudeCodeCLIExecutor(cli_path=cli_path, timeout=timeout)
        logger.info(f"Claude Code CLI executor initialized with path: {cli_path}")
    return _executor_instance