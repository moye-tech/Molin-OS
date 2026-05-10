"""
Claude Code Integration Module
Provides direct CLI integration with Claude Code as the Base Reasoning Engine.
"""

from .cli_executor import ClaudeCodeCLIExecutor
from .client import ClaudeCodeClient

__all__ = [
    'ClaudeCodeCLIExecutor',
    'ClaudeCodeClient',
]

__version__ = '6.6.0'