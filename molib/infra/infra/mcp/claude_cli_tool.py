import asyncio
import os
from pathlib import Path
from loguru import logger
from typing import Dict, Any

class ClaudeCodeTool:
    """
    墨麟ai智能系统v6.6 - Claude CLI 集成工具
    允许系统调用本地 Claude CLI 进程执行复杂编码任务
    """
    
    def __init__(self):
        self.source_dir = Path(__file__).resolve().parent.parent / "upstream" / "claude-code-source"
        self.enabled = self.source_dir.exists()
        
    async def run_task(self, task_prompt: str, target_dir: str) -> Dict[str, Any]:
        """
        调用 Claude Code 执行任务
        
        参数:
            task_prompt: 要让 Claude 执行的任务
            target_dir: 目标工作目录
        """
        if not self.enabled:
            return {"status": "error", "message": "Claude source not found in upstream/claude-code-source"}
            
        target_path = Path(target_dir).resolve()
        if not target_path.exists():
            return {"status": "error", "message": f"Target directory {target_dir} does not exist"}
            
        logger.info(f"Invoking Claude Code engine in {target_dir}...")
        
        # 构建一个临时的 shell 脚本或直接通过 subprocess 调用 node
        # 这里假设 upstream/claude-code-source 中有启动入口，例如 index.js 或者通过 bun/npm
        entry_point = self.source_dir / "src" / "index.js" # 假设入口
        
        if not entry_point.exists():
            # 尝试找其他常见的入口
            possible_entries = list(self.source_dir.rglob("cli.js")) + list(self.source_dir.rglob("index.js"))
            if possible_entries:
                entry_point = possible_entries[0]
            else:
                return {"status": "error", "message": "Could not determine Claude Code entry point."}

        # 构造非交互式的调用
        # 这里我们假定 claude code 接受参数的方式
        cmd = [
            "node", str(entry_point),
            "--prompt", task_prompt,
            "--non-interactive"
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(target_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "CLAUDE_API_KEY": os.getenv("CLAUDE_API_KEY", "")}
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {
                    "status": "success",
                    "output": stdout.decode(),
                    "code": 0
                }
            else:
                return {
                    "status": "failed",
                    "output": stderr.decode() or stdout.decode(),
                    "code": process.returncode
                }
        except Exception as e:
            logger.error(f"Failed to execute Claude Code tool: {e}")
            return {"status": "error", "message": str(e)}

# 注册单例
claude_tool = ClaudeCodeTool()
