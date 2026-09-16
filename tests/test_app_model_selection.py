"""Unit tests for multi-model selection wiring."""

from __future__ import annotations

from types import SimpleNamespace

import pytest


def test_benchmark_run_config_default_model():
    from langtrust.app.models import BenchmarkRunConfig

    assert BenchmarkRunConfig().model == "qwen2.5:14b"


def test_config_from_namespace_missing_model_defaults():
    from langtrust.app.models import config_from_namespace

    args = SimpleNamespace(
        pairs=None,
        condition="both",
        protected="both",
        cells=None,
        repeats=1,
        temperature=0.0,
        num_predict=1024,
        request_timeout=120,
        seed_base=1000,
        output="results/langtrust_benchmark.json",
        dry_run=False,
        debug=False,
    )
    config = config_from_namespace(args)
    assert config.model == "qwen2.5:14b"


def test_config_from_namespace_custom_model():
    from langtrust.app.models import config_from_namespace

    args = SimpleNamespace(model="custom-model:7b")
    config = config_from_namespace(args)
    assert config.model == "custom-model:7b"


def test_validate_config_rejects_empty_and_non_string_model():
    from langtrust.app.models import validate_config

    for bad in ("", "   ", 123, None):
        with pytest.raises(ValueError, match="--model must be a non-empty string"):
            validate_config(SimpleNamespace(
                condition="both",
                protected="both",
                repeats=1,
                num_predict=1024,
                request_timeout=120,
                model=bad,
            ))


def test_cli_parse_args_model_and_config(monkeypatch):
    from langtrust.app.models import config_from_namespace
    from langtrust.cli import benchmark as cli_benchmark

    monkeypatch.setattr(
        "sys.argv",
        ["benchmark", "--model", "example-model:latest"],
    )
    args = cli_benchmark.parse_args()
    assert args.model == "example-model:latest"
    config = config_from_namespace(args)
    assert config.model == "example-model:latest"


def test_cli_benchmark_model_constant():
    from langtrust.cli import benchmark as cli_benchmark

    assert cli_benchmark.MODEL == "qwen2.5:14b"


def test_build_metadata_uses_custom_model(monkeypatch):
    from langtrust.app import benchmark as ab

    captured = {}

    def fake_meta(model_name):
        captured["name"] = model_name
        return {"name": model_name, "digest": "abc"}

    monkeypatch.setattr(ab, "get_ollama_version", lambda: "v-test")
    monkeypatch.setattr(ab, "get_ollama_model_metadata", fake_meta)
    monkeypatch.setattr(ab, "get_git_commit", lambda repo_path=None: None)
    monkeypatch.setattr(ab, "get_git_dirty", lambda repo_path=None: None)

    args = SimpleNamespace(
        model="custom-ollama:latest",
        temperature=0.0,
        num_predict=1024,
        request_timeout=120,
        seed_base=1000,
        repeats=1,
    )
    metadata = ab.build_metadata(
        args,
        design=[],
        protected_conditions=[False],
        expected_episodes=0,
        collect_runtime_metadata=True,
    )
    assert captured["name"] == "custom-ollama:latest"
    assert metadata["model"] == "custom-ollama:latest"
    assert metadata["provenance"]["model"]["name"] == "custom-ollama:latest"


def test_build_metadata_offline_sets_flat_model_without_probe(monkeypatch):
    from langtrust.app import benchmark as ab

    def boom_model(name):
        raise AssertionError("offline path must not probe Ollama")

    def boom_version():
        raise AssertionError("offline path must not probe Ollama")

    monkeypatch.setattr(ab, "get_ollama_version", boom_version)
    monkeypatch.setattr(ab, "get_ollama_model_metadata", boom_model)
    monkeypatch.setattr(ab, "get_git_commit", lambda repo_path=None: None)
    monkeypatch.setattr(ab, "get_git_dirty", lambda repo_path=None: None)

    args = SimpleNamespace(
        model="offline-model:tag",
        temperature=0.0,
        num_predict=1024,
        request_timeout=120,
        seed_base=1000,
        repeats=1,
    )
    metadata = ab.build_metadata(
        args,
        design=[],
        protected_conditions=[False],
        expected_episodes=0,
        collect_runtime_metadata=False,
    )
    assert metadata["model"] == "offline-model:tag"
    assert metadata["provenance"]["model"] is None


def test_default_agent_factory_uses_config_model(monkeypatch):
    from langtrust.app import benchmark as ab
    from langtrust.app.models import BenchmarkRunConfig

    captured = {}

    class FakeAgent:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(ab, "OllamaToolAgent", FakeAgent)

    config = BenchmarkRunConfig(model="factory-model:9b")
    agent = ab._default_agent_factory(protected=True, seed=42, config=config)
    assert isinstance(agent, FakeAgent)
    assert captured["model"] == "factory-model:9b"
    assert captured["protected"] is True
    assert captured["seed"] == 42
    assert captured["temperature"] == config.temperature
    assert captured["num_predict"] == config.num_predict
    assert captured["request_timeout"] == config.request_timeout
    assert captured["max_turns"] == ab.MAX_TURNS
    assert captured["debug"] == config.debug
