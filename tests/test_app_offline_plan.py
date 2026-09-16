"""Application-layer offline plan / pair listing tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from langtrust.app.benchmark import (
    build_benchmark_plan,
    list_benchmark_pair_ids,
)
from langtrust.app.models import BenchmarkRunConfig

SCENARIO_DIR = Path(__file__).resolve().parents[1] / "src" / "langtrust" / "resources" / "scenarios"


def _config(**kwargs):
    base = dict(
        pairs=["invoice_email_001"],
        condition="attack",
        protected="true",
        repeats=1,
        dry_run=True,
    )
    base.update(kwargs)
    return BenchmarkRunConfig(**base)


def test_default_plan_invokes_ollama_provenance_path(monkeypatch):
    import langtrust.app.benchmark as ab

    calls = {"version": 0, "model": 0, "http": 0}

    def fake_version():
        calls["version"] += 1
        return "test-ollama"

    def fake_model(name):
        calls["model"] += 1
        return {"name": name}

    def fake_http(*args, **kwargs):
        calls["http"] += 1
        raise AssertionError("default path should use patched get_ollama_* not raw http")

    monkeypatch.setattr(ab, "get_ollama_version", fake_version)
    monkeypatch.setattr(ab, "get_ollama_model_metadata", fake_model)
    monkeypatch.setattr(ab, "_ollama_json_request", fake_http)
    monkeypatch.setattr(ab, "get_git_commit", lambda repo_path=None: "deadbeef")
    monkeypatch.setattr(ab, "get_git_dirty", lambda repo_path=None: False)

    plan = build_benchmark_plan(
        _config(),
        scenario_dir=str(SCENARIO_DIR),
        git_repo=None,
    )
    assert calls["version"] == 1
    assert calls["model"] == 1
    assert plan.metadata["provenance"]["ollama"]["version"] == "test-ollama"
    assert plan.metadata["provenance"]["model"]["name"]


def test_offline_plan_does_not_call_ollama_probes(monkeypatch):
    import langtrust.app.benchmark as ab

    def boom_version():
        raise AssertionError("offline GUI attempted Ollama probe")

    def boom_model(name):
        raise AssertionError("offline GUI attempted Ollama probe")

    def boom_http(*args, **kwargs):
        raise AssertionError("offline GUI attempted Ollama probe")

    monkeypatch.setattr(ab, "get_ollama_version", boom_version)
    monkeypatch.setattr(ab, "get_ollama_model_metadata", boom_model)
    monkeypatch.setattr(ab, "_ollama_json_request", boom_http)
    monkeypatch.setattr(ab, "get_git_commit", lambda repo_path=None: "deadbeef")
    monkeypatch.setattr(ab, "get_git_dirty", lambda repo_path=None: False)

    plan = build_benchmark_plan(
        _config(),
        scenario_dir=str(SCENARIO_DIR),
        git_repo=None,
        collect_runtime_metadata=False,
    )
    assert plan.metadata["provenance"]["ollama"]["version"] is None
    assert plan.metadata["provenance"]["model"] is None
    assert plan.expected_episodes >= 1


def test_offline_and_default_plans_share_design_semantics(monkeypatch):
    import langtrust.app.benchmark as ab

    monkeypatch.setattr(ab, "get_ollama_version", lambda: "v")
    monkeypatch.setattr(ab, "get_ollama_model_metadata", lambda name: {"name": name})
    monkeypatch.setattr(ab, "get_git_commit", lambda repo_path=None: "deadbeef")
    monkeypatch.setattr(ab, "get_git_dirty", lambda repo_path=None: False)

    config = _config()
    online = build_benchmark_plan(
        config, scenario_dir=str(SCENARIO_DIR), git_repo=None, collect_runtime_metadata=True
    )
    offline = build_benchmark_plan(
        config, scenario_dir=str(SCENARIO_DIR), git_repo=None, collect_runtime_metadata=False
    )

    assert offline.expected_episodes == online.expected_episodes
    assert offline.protected_conditions == online.protected_conditions
    assert sorted(offline.pairs) == sorted(online.pairs)
    assert len(offline.design) == len(online.design)
    for a, b in zip(offline.design, online.design):
        assert a["pair_id"] == b["pair_id"]
        assert a["condition"] == b["condition"]
        assert a["cell"]["cell_index"] == b["cell"]["cell_index"]
        assert a["cell"]["cell_key"] == b["cell"]["cell_key"]


def test_list_benchmark_pair_ids():
    ids = list_benchmark_pair_ids(str(SCENARIO_DIR))
    assert ids == sorted(ids)
    assert "invoice_email_001" in ids
