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
    scenario = loader.load(
        "calendar_benign_delete_001.yaml"
    )

    return StatefulSandbox(
        scenario,
        LANGUAGE_ASSIGNMENT,
    )


def test_delete_event_removes_event_from_calendar_state(
    sandbox,
):
    before = sandbox.snapshot()

    assert [
        event["id"]
        for event in before["calendar"]["events"]
    ] == [
        "EVT-2026-091"
    ]

    raw_result = sandbox.execute(
        "delete_event",
        {
            "event_id": "EVT-2026-091",
        },
    )

    result = json.loads(raw_result)
    after = sandbox.snapshot()

    assert result["status"] == "deleted_in_sandbox"
    assert result["event_id"] == "EVT-2026-091"

    assert after["calendar"]["events"] == []


def test_deleted_event_can_no_longer_be_read(
    sandbox,
):
    sandbox.execute(
        "delete_event",
        {
            "event_id": "EVT-2026-091",
        },
    )

    raw_result = sandbox.execute(
        "read_event",
        {
            "event_id": "EVT-2026-091",
        },
    )

    result = json.loads(raw_result)

    assert result == {
        "error": "event_not_found",
        "event_id": "EVT-2026-091",
    }
