import json
from pathlib import Path

import pytest

from langtrust.environment.sandbox import StatefulSandbox
from langtrust.scenarios.loader import ScenarioLoader


SCENARIO_DIR = Path(__file__).resolve().parents[1] / "scenarios"

TARGET_PATH = "/workspace/release_status.txt"
TARGET_CONTENT = "APPROVED-FOR-RELEASE"

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
        "files_benign_write_001.yaml"
    )

    return StatefulSandbox(
        scenario,
        LANGUAGE_ASSIGNMENT,
    )


def test_write_file_overwrites_existing_file_exactly(
    sandbox,
):
    before = sandbox.snapshot()

    assert len(before["files"]) == 1
    assert before["files"][0]["path"] == TARGET_PATH

    raw_result = sandbox.execute(
        "write_file",
        {
            "path": TARGET_PATH,
            "content": TARGET_CONTENT,
        },
    )

    result = json.loads(raw_result)
    after = sandbox.snapshot()

    assert result == {
        "status": "written_in_sandbox",
        "path": TARGET_PATH,
    }

    assert after["files"] == [
        {
            "path": TARGET_PATH,
            "content": TARGET_CONTENT,
        }
    ]


def test_read_file_returns_exact_overwritten_content(
    sandbox,
):
    sandbox.execute(
        "write_file",
        {
            "path": TARGET_PATH,
            "content": TARGET_CONTENT,
        },
    )

    content = sandbox.execute(
        "read_file",
        {
            "path": TARGET_PATH,
        },
    )

    assert content == TARGET_CONTENT
