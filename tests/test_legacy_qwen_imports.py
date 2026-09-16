"""Compatibility tests for former Qwen-named import paths."""

from langtrust.agent.ollama_tool_agent import OllamaToolAgent, ToolAgentResult
from langtrust.agent.qwen_tool_agent import (
    QwenToolAgent,
    ToolAgentResult as LegacyToolAgentResult,
)
from langtrust.backend.ollama_backend import OllamaBackend
from langtrust.backend.qwen_backend import QwenBackend


def test_qwen_backend_alias_points_to_ollama_backend():
    assert QwenBackend is OllamaBackend


def test_qwen_tool_agent_alias_points_to_ollama_tool_agent():
    assert QwenToolAgent is OllamaToolAgent
    assert LegacyToolAgentResult is ToolAgentResult
