from pathlib import Path

import pytest

from langtrust.scenarios.loader import ScenarioLoader
from langtrust.security.policy import ToolPolicyEngine


SCENARIO_DIR = Path(__file__).resolve().parents[1] / "scenarios"


@pytest.fixture(scope="module")
def loader():
    return ScenarioLoader(str(SCENARIO_DIR))


@pytest.mark.parametrize(
    ("tool_name", "expected_allowed"),
    [
        ("search_invoice", True),
        ("read_invoice", True),
        ("send_email", False),
    ],
)
def test_invoice_attack_policy_respects_permissions(
    loader,
    tool_name,
    expected_allowed,
):
    scenario = loader.load("invoice_001.yaml")
    policy = ToolPolicyEngine(scenario)

    decision = policy.check(tool_name)

    assert decision.allowed is expected_allowed


def test_invoice_benign_policy_allows_required_email(
    loader,
):
    scenario = loader.load("invoice_benign_email_001.yaml")
    policy = ToolPolicyEngine(scenario)

    decision = policy.check("send_email")

    assert decision.allowed is True


def test_policy_denies_unknown_tool(loader):
    scenario = loader.load("invoice_benign_email_001.yaml")
    policy = ToolPolicyEngine(scenario)

    decision = policy.check("definitely_not_a_tool")

    assert decision.allowed is False
    assert decision.reason == "Unknown tool"


@pytest.mark.parametrize(
    ("scenario_file", "tool_name", "expected_allowed"),
    [
        ("calendar_001.yaml", "delete_event", False),
        ("calendar_benign_delete_001.yaml", "delete_event", True),
        ("files_001.yaml", "write_file", False),
        ("files_benign_write_001.yaml", "write_file", True),
    ],
)
def test_calendar_and_files_policy_respects_permissions(
    loader,
    scenario_file,
    tool_name,
    expected_allowed,
):
    scenario = loader.load(scenario_file)
    policy = ToolPolicyEngine(scenario)

    decision = policy.check(tool_name)

    assert decision.allowed is expected_allowed
