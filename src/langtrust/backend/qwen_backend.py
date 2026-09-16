"""Backward-compatible imports for the former Qwen-named backend."""

from langtrust.backend.ollama_backend import (
    DEFAULT_NUM_PREDICT,
    DEFAULT_REQUEST_TIMEOUT,
    OllamaBackend,
)

QwenBackend = OllamaBackend

__all__ = [
    "DEFAULT_NUM_PREDICT",
    "DEFAULT_REQUEST_TIMEOUT",
    "OllamaBackend",
    "QwenBackend",
]
