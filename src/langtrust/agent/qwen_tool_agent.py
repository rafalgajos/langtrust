"""Backward-compatible imports for the former Qwen-named tool agent."""

from langtrust.agent.ollama_tool_agent import (
    OllamaToolAgent,
    ToolAgentResult,
)

QwenToolAgent = OllamaToolAgent

__all__ = [
    "OllamaToolAgent",
    "QwenToolAgent",
    "ToolAgentResult",
]
