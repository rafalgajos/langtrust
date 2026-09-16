"""Pre-extraction locks for langtrust.cli.benchmark orchestration helpers.

After extraction, the same assertions continue to apply via CLI re-exports,
and additional tests cover langtrust.app.run_benchmark.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from langtrust.benchmark.pairs import group_benchmark_pairs
from langtrust.cli import benchmark as cli_benchmark


SCENARIO_DIR = Path(__file__).resolve().parents[1] / "scenarios"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("attack", ["attack"]),
        ("benign", ["benign"]),
        ("both", ["attack", "benign"]),
    ],
)
def test_get_conditions_mapping(value, expected):
    assert cli_benchmark.get_conditions(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("false", [False]),
        ("true", [True]),
        ("both", [False, True]),
    ],
)
def test_get_protected_conditions_mapping(value, expected):
    assert cli_benchmark.get_protected_conditions(value) == expected


def test_select_pairs_unknown_raises():
    all_pairs = {"invoice_email_001": {"attack": {}, "benign": {}}}

    with pytest.raises(ValueError) as exc_info:
        cli_benchmark.select_pairs(all_pairs, ["invoice_email_001", "missing_pair"])

    assert str(exc_info.value) == "Unknown benchmark pair(s): missing_pair"


def test_select_pairs_returns_sorted_requested_keys():
    all_pairs = {
        "z_pair": {"attack": {}, "benign": {}},
        "a_pair": {"attack": {}, "benign": {}},
        "m_pair": {"attack": {}, "benign": {}},
    }

    selected = cli_benchmark.select_pairs(all_pairs, ["z_pair", "a_pair"])

    assert list(selected) == ["a_pair", "z_pair"]


def test_design_ordering_invoice_email_001_attack_has_16_cells():
    all_pairs = group_benchmark_pairs(str(SCENARIO_DIR))
    pairs = cli_benchmark.select_pairs(all_pairs, ["invoice_email_001"])
    conditions = cli_benchmark.get_conditions("attack")
    design = cli_benchmark.build_design(pairs, conditions, requested_cells=None)

    assert len(design) == 16
    assert all(item["pair_id"] == "invoice_email_001" for item in design)
    assert all(item["condition"] == "attack" for item in design)
    assert [item["cell"]["cell_index"] for item in design] == list(range(1, 17))


def test_expected_episode_count_formula():
    design_len = 16
    repeats = 2
    protected_conditions = cli_benchmark.get_protected_conditions("both")

    expected_episodes = design_len * repeats * len(protected_conditions)

    assert len(protected_conditions) == 2
    assert expected_episodes == 64


def test_seed_sequence_for_repeats():
    seed_base = 1000
    repeats = 3
    seeds = [seed_base + repeat - 1 for repeat in range(1, repeats + 1)]

    assert seeds == [1000, 1001, 1002]


def test_build_episode_record_exact_schema():
    item = {
        "pair_id": "invoice_email_001",
        "domain": "invoice",
        "condition": "attack",
        "scenario": {"id": "invoice_001"},
        "scenario_file": "invoice_001.yaml",
        "cell": {
            "cell_index": 3,
            "cell_key": "example-cell",
            "active_language_factors": ["user_instruction"],
            "active_language_assignment": {"user_instruction": "pl"},
            "language_assignment": {
                "user_instruction": "pl",
                "tool_description": "en",
                "untrusted_content": "en",
                "attack_payload": "en",
            },
            "inactive_language": "en",
        },
    }

    args = SimpleNamespace(
        temperature=0.2,
        num_predict=1024,
        request_timeout=120,
    )

    result = SimpleNamespace(
        completed=True,
        inference_success=True,
        inference_truncated=False,
        inference_failure_type=None,
        inference_error=None,
        inference_calls=[{"turn": 1, "success": True}],
        turns=2,
        answer="done",
        events=[{"type": "tool"}],
        blocked_attempts=[],
        initial_state={"before": True},
        final_state={"after": True},
    )

    evaluation = {
        "security": {"unauthorized_execution": False},
        "utility": {"task_success": True},
    }

    record = cli_benchmark.build_episode_record(
        item=item,
        repeat=4,
        seed=1003,
        args=args,
        protected=True,
        result=result,
        evaluation=evaluation,
    )

    assert record == {
        "pair_id": "invoice_email_001",
        "domain": "invoice",
        "condition": "attack",
        "scenario": "invoice_001",
        "scenario_file": "invoice_001.yaml",
        "cell_index": 3,
        "cell_key": "example-cell",
        "active_language_factors": ["user_instruction"],
        "active_language_assignment": {"user_instruction": "pl"},
        "language_assignment": {
            "user_instruction": "pl",
            "tool_description": "en",
            "untrusted_content": "en",
            "attack_payload": "en",
        },
        "inactive_language": "en",
        "repeat": 4,
        "seed": 1003,
        "temperature": 0.2,
        "num_predict": 1024,
        "request_timeout_seconds": 120,
        "protected_prompt": True,
        "completed": True,
        "inference": {
            "success": True,
            "truncated": False,
            "failure_type": None,
            "error": None,
            "calls": [{"turn": 1, "success": True}],
        },
        "turns": 2,
        "answer": "done",
        "events": [{"type": "tool"}],
        "blocked_attempts": [],
        "initial_state": {"before": True},
        "final_state": {"after": True},
        "evaluation": evaluation,
    }



def test_config_from_namespace_and_validate_defaults():
    from langtrust.app.models import BenchmarkRunConfig, config_from_namespace, validate_config

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
    assert isinstance(config, BenchmarkRunConfig)
    assert config.condition == "both"
    assert config.protected == "both"
    assert config.repeats == 1
    assert config.temperature == 0.0
    assert config.num_predict == 1024
    assert config.request_timeout == 120
    assert config.seed_base == 1000
    assert config.output == "results/langtrust_benchmark.json"
    validate_config(config)


def test_build_benchmark_plan_expected_episodes(tmp_path, monkeypatch):
    from langtrust.app.models import BenchmarkRunConfig
    from langtrust.app.benchmark import build_benchmark_plan

    monkeypatch.setattr(
        "langtrust.app.benchmark.get_ollama_version",
        lambda: None,
    )
    monkeypatch.setattr(
        "langtrust.app.benchmark.get_ollama_model_metadata",
        lambda model_name: {"name": model_name},
    )

    config = BenchmarkRunConfig(
        pairs=["invoice_email_001"],
        condition="attack",
        protected="true",
        cells=[1],
        repeats=2,
        seed_base=1000,
        output=str(tmp_path / "out.json"),
    )

    plan = build_benchmark_plan(config, scenario_dir=str(SCENARIO_DIR), git_repo=None)

    assert len(plan.design) == 1
    assert plan.protected_conditions == [True]
    assert plan.expected_episodes == 2
    assert plan.metadata["expected_episodes"] == 2
    assert list(plan.pairs) == ["invoice_email_001"]


def test_run_benchmark_with_fake_agent(tmp_path, monkeypatch):
    from langtrust.agent.ollama_tool_agent import ToolAgentResult
    from langtrust.app.benchmark import run_benchmark
    from langtrust.app.models import BenchmarkRunConfig

    monkeypatch.setattr(
        "langtrust.app.benchmark.get_ollama_version",
        lambda: None,
    )
    monkeypatch.setattr(
        "langtrust.app.benchmark.get_ollama_model_metadata",
        lambda model_name: {"name": model_name},
    )

    calls = []
    events = []

    class FakeAgent:
        def __init__(self, *, protected, seed, config):
            self.protected = protected
            self.seed = seed
            self.config = config

        def run(self, language_assignment, scenario):
            calls.append(
                {
                    "protected": self.protected,
                    "seed": self.seed,
                    "temperature": self.config.temperature,
                    "scenario_id": scenario["id"],
                    "language_assignment": language_assignment,
                }
            )
            return ToolAgentResult(
                answer="fake",
                events=[],
                blocked_attempts=[],
                turns=1,
                completed=True,
                initial_state={},
                final_state={},
                inference_success=False,
                inference_truncated=False,
                inference_failure_type="injected_failure",
                inference_error="fake",
                inference_calls=[],
            )

    def agent_factory(*, protected, seed, config):
        return FakeAgent(protected=protected, seed=seed, config=config)

    def on_event(event):
        events.append(event["type"])
        if event["type"] == "episode_start":
            raise RuntimeError("callback errors must not abort")

    output_path = tmp_path / "results.json"
    config = BenchmarkRunConfig(
        pairs=["invoice_email_001"],
        condition="attack",
        protected="both",
        cells=[1],
        repeats=3,
        temperature=0.0,
        num_predict=1024,
        request_timeout=120,
        seed_base=1000,
        output=str(output_path),
        dry_run=False,
        debug=False,
    )

    result = run_benchmark(
        config,
        scenario_dir=str(SCENARIO_DIR),
        git_repo=None,
        on_event=on_event,
        agent_factory=agent_factory,
    )

    assert result.expected_episodes == 6
    assert len(result.results) == 6
    assert [call["seed"] for call in calls] == [1000, 1000, 1001, 1001, 1002, 1002]
    assert [call["protected"] for call in calls] == [False, True, False, True, False, True]
    assert all(record["evaluation"] is None for record in result.results)
    assert all(record["inference"]["success"] is False for record in result.results)
    assert events.count("episode_start") == 6
    assert events.count("episode_complete") == 6
    assert output_path.exists()

    import json

    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert len(saved["results"]) == 6
    assert saved["metadata"]["expected_episodes"] == 6


def test_cli_reexports_orchestration_helpers():
    assert cli_benchmark.get_conditions is not None
    assert cli_benchmark.build_design is not None
    assert cli_benchmark.build_episode_record is not None
    assert cli_benchmark.MODEL == "qwen2.5:14b"
    assert cli_benchmark.OLLAMA_BASE_URL == "http://localhost:11434"
    assert cli_benchmark.MAX_TURNS == 8



def test_run_benchmark_reuses_provided_plan_metadata(tmp_path, monkeypatch):
    """Live path must not rebuild plan/metadata when a plan is supplied."""
    from langtrust.agent.ollama_tool_agent import ToolAgentResult
    from langtrust.app.benchmark import build_benchmark_plan, build_metadata, run_benchmark
    from langtrust.app.models import BenchmarkRunConfig

    monkeypatch.setattr(
        "langtrust.app.benchmark.get_ollama_version",
        lambda: None,
    )
    monkeypatch.setattr(
        "langtrust.app.benchmark.get_ollama_model_metadata",
        lambda model_name: {"name": model_name},
    )

    build_metadata_calls = {"count": 0}
    original_build_metadata = build_metadata

    def counting_build_metadata(*args, **kwargs):
        build_metadata_calls["count"] += 1
        return original_build_metadata(*args, **kwargs)

    monkeypatch.setattr(
        "langtrust.app.benchmark.build_metadata",
        counting_build_metadata,
    )

    class FakeAgent:
        def __init__(self, *, protected, seed, config):
            pass

        def run(self, language_assignment, scenario):
            return ToolAgentResult(
                answer="fake",
                events=[],
                blocked_attempts=[],
                turns=1,
                completed=True,
                initial_state={},
                final_state={},
                inference_success=False,
                inference_truncated=False,
                inference_failure_type="injected_failure",
                inference_error="fake",
                inference_calls=[],
            )

    output_path = tmp_path / "once.json"
    config = BenchmarkRunConfig(
        pairs=["invoice_email_001"],
        condition="attack",
        protected="true",
        cells=[1],
        repeats=1,
        output=str(output_path),
        dry_run=False,
    )

    plan = build_benchmark_plan(config, scenario_dir=str(SCENARIO_DIR), git_repo=None)
    assert build_metadata_calls["count"] == 1
    printed_generated_at = plan.metadata["generated_at"]

    result = run_benchmark(
        config,
        scenario_dir=str(SCENARIO_DIR),
        git_repo=None,
        plan=plan,
        agent_factory=lambda **kwargs: FakeAgent(**kwargs),
    )

    assert build_metadata_calls["count"] == 1
    assert result.metadata is plan.metadata
    assert result.metadata["generated_at"] == printed_generated_at

    import json

    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved["metadata"]["generated_at"] == printed_generated_at
    assert saved["metadata"] is not None
    # Same object identity through save/load is lost; compare content key
    assert saved["metadata"]["generated_at"] == plan.metadata["generated_at"]


def test_run_benchmark_dry_run_skips_agent_factory(tmp_path, monkeypatch):
    from langtrust.app.benchmark import build_benchmark_plan, run_benchmark
    from langtrust.app.models import BenchmarkRunConfig

    monkeypatch.setattr(
        "langtrust.app.benchmark.get_ollama_version",
        lambda: None,
    )
    monkeypatch.setattr(
        "langtrust.app.benchmark.get_ollama_model_metadata",
        lambda model_name: {"name": model_name},
    )

    def boom_factory(**kwargs):
        raise AssertionError("agent_factory must not be called for dry_run")

    config = BenchmarkRunConfig(
        pairs=["invoice_email_001"],
        condition="attack",
        protected="true",
        cells=[1],
        repeats=1,
        output=str(tmp_path / "dry.json"),
        dry_run=True,
    )
    plan = build_benchmark_plan(config, scenario_dir=str(SCENARIO_DIR), git_repo=None)

    result = run_benchmark(
        config,
        scenario_dir=str(SCENARIO_DIR),
        git_repo=None,
        plan=plan,
        agent_factory=boom_factory,
    )

    assert result.results == []
    assert result.metadata is plan.metadata
    assert result.expected_episodes == plan.expected_episodes
    assert not (tmp_path / "dry.json").exists()


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("repeats", 0, "--repeats must be >= 1"),
        ("num_predict", 0, "--num-predict must be >= 1"),
        ("request_timeout", 0, "--request-timeout must be > 0"),
    ],
)
def test_build_benchmark_plan_validates_config(field, value, message):
    from langtrust.app.benchmark import build_benchmark_plan
    from langtrust.app.models import BenchmarkRunConfig

    kwargs = {
        "pairs": ["invoice_email_001"],
        "condition": "attack",
        "protected": "true",
        "cells": [1],
        "repeats": 1,
        "num_predict": 1024,
        "request_timeout": 120,
    }
    kwargs[field] = value
    config = BenchmarkRunConfig(**kwargs)

    with pytest.raises(ValueError) as exc_info:
        build_benchmark_plan(config, scenario_dir=str(SCENARIO_DIR), git_repo=None)

    assert str(exc_info.value) == message


def test_cli_live_path_passes_same_plan(monkeypatch, tmp_path):
    """CLI main must pass the presented plan into run_benchmark."""
    from langtrust.app.models import BenchmarkPlan, BenchmarkRunConfig, BenchmarkRunResult
    from langtrust.cli import benchmark as cli_benchmark

    captured = {}

    fake_plan = BenchmarkPlan(
        design=[],
        protected_conditions=[True],
        expected_episodes=0,
        metadata={"generated_at": "FIXED-TIMESTAMP", "expected_episodes": 0},
        pairs={},
    )

    def fake_parse_args():
        return type(
            "Args",
            (),
            {
                "pairs": ["invoice_email_001"],
                "condition": "attack",
                "protected": "true",
                "cells": [1],
                "repeats": 1,
                "temperature": 0.0,
                "num_predict": 1024,
                "request_timeout": 120.0,
                "seed_base": 1000,
                "output": str(tmp_path / "cli.json"),
                "dry_run": False,
                "debug": False,
            },
        )()

    def fake_build_plan(config, scenario_dir=None, git_repo=None):
        captured["build_calls"] = captured.get("build_calls", 0) + 1
        return fake_plan

    def fake_run_benchmark(config, scenario_dir=None, git_repo=None, on_event=None, agent_factory=None, plan=None):
        captured["plan"] = plan
        captured["run_calls"] = captured.get("run_calls", 0) + 1
        return BenchmarkRunResult(
            metadata=plan.metadata,
            results=[],
            output_path=tmp_path / "cli.json",
            expected_episodes=0,
        )

    monkeypatch.setattr(cli_benchmark, "parse_args", fake_parse_args)
    monkeypatch.setattr(
        "langtrust.app.benchmark.build_benchmark_plan",
        fake_build_plan,
    )
    # CLI imports build_benchmark_plan inside main locally — patch where used
    import langtrust.app.benchmark as app_benchmark

    monkeypatch.setattr(app_benchmark, "build_benchmark_plan", fake_build_plan)
    monkeypatch.setattr(cli_benchmark, "run_benchmark", fake_run_benchmark)
    monkeypatch.setattr(cli_benchmark, "print_design_summary", lambda design: None)
    monkeypatch.setattr(cli_benchmark, "print_provenance", lambda metadata: None)
    monkeypatch.setattr(cli_benchmark, "summarize", lambda results: None)

    cli_benchmark.main()

    assert captured["build_calls"] == 1
    assert captured["run_calls"] == 1
    assert captured["plan"] is fake_plan
    assert captured["plan"].metadata["generated_at"] == "FIXED-TIMESTAMP"



def test_validate_config_rejects_invalid_condition_and_protected():
    from langtrust.app.models import BenchmarkRunConfig, validate_config

    with pytest.raises(ValueError) as exc_info:
        validate_config(BenchmarkRunConfig(condition="ATTACK"))
    assert str(exc_info.value) == "--condition must be one of: both, attack, benign"

    with pytest.raises(ValueError) as exc_info:
        validate_config(BenchmarkRunConfig(protected="yes"))
    assert str(exc_info.value) == "--protected must be one of: both, false, true"


def test_on_event_callback_cannot_mutate_scientific_state(tmp_path, monkeypatch):
    """Callbacks receive deep copies; mutations must not affect results or I/O."""
    import copy
    import json

    from langtrust.agent.ollama_tool_agent import ToolAgentResult
    from langtrust.app.benchmark import build_benchmark_plan, run_benchmark
    from langtrust.app.models import BenchmarkRunConfig

    monkeypatch.setattr(
        "langtrust.app.benchmark.get_ollama_version",
        lambda: None,
    )
    monkeypatch.setattr(
        "langtrust.app.benchmark.get_ollama_model_metadata",
        lambda model_name: {"name": model_name},
    )

    seen_assignments = []

    class FakeAgent:
        def __init__(self, *, protected, seed, config):
            self.protected = protected

        def run(self, language_assignment, scenario):
            # Capture the live objects the agent actually received.
            seen_assignments.append(copy.deepcopy(language_assignment))
            # Prove scenario id remains intact for execution.
            assert scenario["id"] == "invoice_001"
            return ToolAgentResult(
                answer="canonical-answer",
                events=[{"tool": "read_invoice", "blocked": False, "executed": True}],
                blocked_attempts=[],
                turns=1,
                completed=True,
                initial_state={"ok": True},
                final_state={"ok": True},
                inference_success=False,
                inference_truncated=False,
                inference_failure_type="injected_failure",
                inference_error="fake",
                inference_calls=[{"turn": 1, "done_reason": "stop"}],
            )

    def mutating_callback(event):
        # Mutate every nested scientific payload we can reach.
        if "item" in event:
            event["item"]["pair_id"] = "MUTATED_PAIR"
            event["item"]["cell"]["cell_index"] = -999
            event["item"]["cell"]["language_assignment"]["user_instruction"] = "MUTATED"
        if "scenario" in event:
            event["scenario"]["id"] = "mutated_scenario"
            event["scenario"]["evaluation"] = {"expected": {"required_tools": ["hack"]}}
        if "record" in event:
            event["record"]["answer"] = "mutated-answer"
            event["record"]["pair_id"] = "MUTATED_PAIR"
            event["record"]["inference"]["success"] = True
        if "result" in event and hasattr(event["result"], "answer"):
            event["result"].answer = "mutated-agent-answer"
        # Also raise to ensure exception isolation still holds.
        raise RuntimeError("callback mutation noise")

    output_path = tmp_path / "immutable.json"
    config = BenchmarkRunConfig(
        pairs=["invoice_email_001"],
        condition="attack",
        protected="true",
        cells=[1],
        repeats=1,
        output=str(output_path),
        dry_run=False,
    )
    plan = build_benchmark_plan(config, scenario_dir=str(SCENARIO_DIR), git_repo=None)
    # Keep a pristine copy of the plan design cell for comparison.
    original_cell = copy.deepcopy(plan.design[0]["cell"])
    original_pair_id = plan.design[0]["pair_id"]
    original_scenario_id = plan.design[0]["scenario"]["id"]

    result = run_benchmark(
        config,
        scenario_dir=str(SCENARIO_DIR),
        git_repo=None,
        plan=plan,
        on_event=mutating_callback,
        agent_factory=lambda **kwargs: FakeAgent(**kwargs),
    )

    assert len(result.results) == 1
    record = result.results[0]
    assert record["answer"] == "canonical-answer"
    assert record["pair_id"] == original_pair_id
    assert record["scenario"] == original_scenario_id
    assert record["cell_index"] == original_cell["cell_index"]
    assert record["language_assignment"] == original_cell["language_assignment"]
    assert record["inference"]["success"] is False

    # Plan design objects used during execution must remain intact.
    assert plan.design[0]["pair_id"] == original_pair_id
    assert plan.design[0]["scenario"]["id"] == original_scenario_id
    assert plan.design[0]["cell"] == original_cell

    # Agent saw the original language assignment, not a mutated callback copy.
    assert seen_assignments[0] == original_cell["language_assignment"]

    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved["results"][0]["answer"] == "canonical-answer"
    assert saved["results"][0]["pair_id"] == original_pair_id
    assert saved["results"][0]["inference"]["success"] is False
