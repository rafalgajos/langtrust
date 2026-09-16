from types import SimpleNamespace

import pytest

from langtrust.app import benchmark as app_benchmark
from langtrust.cli import benchmark


def test_git_provenance_is_not_inferred_from_current_directory(monkeypatch):
    def unexpected_git_call(*args, **kwargs):
        raise AssertionError("Git must not be queried without an explicit repository")

    monkeypatch.setattr(
        app_benchmark.subprocess,
        "check_output",
        unexpected_git_call,
    )

    assert benchmark.get_git_commit() is None
    assert benchmark.get_git_dirty() is None


def test_git_provenance_uses_explicit_repository(tmp_path, monkeypatch):
    calls = []

    def fake_check_output(command, text, stderr):
        calls.append(command)

        assert command[:3] == ["git", "-C", str(tmp_path)]

        if command[-2:] == ["rev-parse", "HEAD"]:
            return "abc123\n"

        if command[-2:] == ["status", "--porcelain"]:
            return " M example.py\n"

        raise AssertionError(command)

    monkeypatch.setattr(
        app_benchmark.subprocess,
        "check_output",
        fake_check_output,
    )

    assert benchmark.get_git_commit(tmp_path) == "abc123"
    assert benchmark.get_git_dirty(tmp_path) is True

    assert len(calls) == 2


def test_validate_args_accepts_valid_values():
    class Args:
        repeats = 1
        num_predict = 1024
        request_timeout = 120

    benchmark.validate_args(Args())


def test_validate_args_rejects_invalid_values():
    cases = [
        ("repeats", 0, "--repeats must be >= 1"),
        ("num_predict", 0, "--num-predict must be >= 1"),
        ("request_timeout", 0, "--request-timeout must be > 0"),
    ]

    for field, value, expected_message in cases:
        class Args:
            repeats = 1
            num_predict = 1024
            request_timeout = 120

        setattr(Args, field, value)

        with pytest.raises(ValueError) as exc_info:
            benchmark.validate_args(Args())

        assert str(exc_info.value) == expected_message


def test_build_episode_record_preserves_result_schema():
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

    record = benchmark.build_episode_record(
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


def test_print_episode_result_reports_inference_failure(capsys):
    result = SimpleNamespace(
        inference_success=False,
        inference_truncated=True,
        inference_failure_type="generation_limit",
    )

    benchmark.print_episode_result(
        scenario={},
        result=result,
        evaluation=None,
    )

    assert capsys.readouterr().out == (
        "  inference success = False\n"
        "  inference truncated = True\n"
        "  inference failure = generation_limit\n"
    )


def test_print_episode_result_reports_evaluation(capsys):
    scenario = {
        "evaluation": {
            "expected": {
                "required_tools": ["read_file"],
            }
        }
    }

    result = SimpleNamespace()

    evaluation = {
        "security": {
            "unauthorized_tool_attempt": True,
            "unauthorized_execution": False,
        },
        "utility": {
            "required_tools_executed": True,
            "policy_overblocking": False,
            "model_underaction": False,
            "task_success": True,
        },
    }

    benchmark.print_episode_result(
        scenario,
        result,
        evaluation,
    )

    assert capsys.readouterr().out == (
        "  unauthorized attempt = True\n"
        "  unauthorized execution = False\n"
        "  required tool executed = True\n"
        "  policy overblocking = False\n"
        "  model underaction = False\n"
        "  task success = True\n"
    )
