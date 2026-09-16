import json
from pathlib import Path

import pytest

from langtrust.environment.sandbox import StatefulSandbox
from langtrust.scenarios.loader import ScenarioLoader


SCENARIO_DIR = Path(__file__).resolve().parents[1] / "scenarios"

LANGUAGE_ASSIGNMENT = {
    "user_instruction": "en",
    "tool_description": "en",
    "untrusted_content": "en",
    "attack_payload": "en",
}


@pytest.fixture
def sandbox():
    loader = ScenarioLoader(str(SCENARIO_DIR))
    scenario = loader.load("invoice_benign_email_001.yaml")

    return StatefulSandbox(
        scenario,
        LANGUAGE_ASSIGNMENT,
    )


def test_send_email_changes_only_local_mailbox_state(sandbox):
    before = sandbox.snapshot()

    raw_result = sandbox.execute(
        "send_email",
        {
            "recipient": "finance@example.test",
            "content": (
                "Invoice FV-2026-081 is due "
                "for payment on 2026-09-14."
            ),
        },
    )

    after = sandbox.snapshot()
    result = json.loads(raw_result)

    assert before["mailbox"]["sent_messages"] == []

    assert after["mailbox"]["sent_messages"] == [
        {
            "recipient": "finance@example.test",
            "content": (
                "Invoice FV-2026-081 is due "
                "for payment on 2026-09-14."
            ),
        }
    ]

    assert result["status"] == "sent_in_sandbox"
    assert result["message_index"] == 0
    assert result["recipient"] == "finance@example.test"


def test_snapshot_is_independent_deep_copy(sandbox):
    snapshot = sandbox.snapshot()

    snapshot["mailbox"]["sent_messages"].append(
        {
            "recipient": "fake@example.test",
            "content": "mutation",
        }
    )

    assert sandbox.state["mailbox"]["sent_messages"] == []


def test_unknown_sandbox_tool_raises_runtime_error(sandbox):
    with pytest.raises(
        RuntimeError,
        match="Unknown sandbox tool",
    ):
        sandbox.execute(
            "definitely_not_a_tool",
            {},
        )
