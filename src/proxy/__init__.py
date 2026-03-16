"""
Agent Skills Benchmark - Proxy Module
Module C: Agent interaction proxy, responsible for secure sandbox execution.
Supports the OpenAI and Anthropic (Claude) APIs, as well as the Claude Code CLI.
"""

from .claude_code_proxy import ClaudeCodeProxy, ClaudeCodeResult

__all__ = [
    "ClaudeCodeProxy",
    "ClaudeCodeResult",
]
