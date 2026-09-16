"""Unit tests for Live Run Ollama model tool-compatibility preflight (G9C9)."""

from __future__ import annotations

import pytest

from langtrust.app import (
    ModelCompatibilityError,
    check_ollama_model_tool_compatibility,
)


def test_tools_capability_passes():
    meta = {
        "name": "tooly:latest",
        "capabilities": ["completion", "tools"],
    }

    def fake_get(name):
        assert name == "tooly:latest"
        return meta

    out = check_ollama_model_tool_compatibility(
        "tooly:latest", get_metadata=fake_get
    )
    assert out is meta
    assert "tools" in out["capabilities"]


def test_no_tools_capability_fails():
    def fake_get(name):
        return {"name": name, "capabilities": ["completion", "embedding"]}

    with pytest.raises(ModelCompatibilityError, match="does not advertise native tool"):
        check_ollama_model_tool_compatibility("plain:7b", get_metadata=fake_get)


@pytest.mark.parametrize(
    "capabilities",
    [
        None,
        "tools",
        {},
        [],
    ],
)
def test_unknown_or_empty_capabilities_fail(capabilities):
    def fake_get(name):
        return {"name": name, "capabilities": capabilities}

    with pytest.raises(ModelCompatibilityError, match="[Cc]apabilit"):
        check_ollama_model_tool_compatibility("mystery:1", get_metadata=fake_get)


def test_model_not_found_with_show_error_fails():
    def fake_get(name):
        return {
            "name": name,
            "capabilities": [],
            "tags_error": "model_not_found",
            "show_error": "ConnectionError('show failed')",
        }

    with pytest.raises(ModelCompatibilityError, match="not found"):
        check_ollama_model_tool_compatibility("missing:latest", get_metadata=fake_get)


def test_connection_like_tags_and_show_error_fails():
    def fake_get(name):
        return {
            "name": name,
            "capabilities": [],
            "tags_error": "ConnectionError('refused')",
            "show_error": "ConnectionError('refused')",
        }

    with pytest.raises(ModelCompatibilityError, match="Ollama unavailable"):
        check_ollama_model_tool_compatibility("any:latest", get_metadata=fake_get)


def test_get_metadata_raise_is_ollama_unavailable():
    def boom(name):
        raise OSError("network down")

    with pytest.raises(ModelCompatibilityError, match="Ollama unavailable"):
        check_ollama_model_tool_compatibility("x:1", get_metadata=boom)


def test_show_error_alone_capabilities_unknown():
    def fake_get(name):
        return {
            "name": name,
            "capabilities": [],
            "show_error": "TimeoutError('show')",
        }

    with pytest.raises(ModelCompatibilityError, match="Could not retrieve metadata"):
        check_ollama_model_tool_compatibility("opaque:1", get_metadata=fake_get)


def test_custom_model_name_passed_to_get_metadata_exactly():
    seen = []

    def fake_get(name):
        seen.append(name)
        return {"name": name, "capabilities": ["tools"]}

    check_ollama_model_tool_compatibility(
        "custom-exact:tag", get_metadata=fake_get
    )
    assert seen == ["custom-exact:tag"]


def test_is_subclass_of_value_error():
    assert issubclass(ModelCompatibilityError, ValueError)
