from pathlib import Path

from langtrust.backend.ollama_backend import OllamaBackend
from langtrust.scenarios.loader import ScenarioLoader


SCENARIO_DIR = Path(__file__).resolve().parents[1] / "scenarios"

ASSIGNMENT_EN = {
    "user_instruction": "en",
    "tool_description": "en",
    "untrusted_content": "en",
    "attack_payload": "en",
}

ASSIGNMENT_PL = {
    "user_instruction": "pl",
    "tool_description": "pl",
    "untrusted_content": "pl",
    "attack_payload": "pl",
}


def load_invoice_scenario():
    return ScenarioLoader(str(SCENARIO_DIR)).load("invoice_001.yaml")


def tools_by_name(tools):
    return {
        item["function"]["name"]: item["function"]
        for item in tools
    }


def test_build_tools_uses_scenario_names_and_parameters():
    scenario = load_invoice_scenario()
    backend = OllamaBackend()

    tools = tools_by_name(
        backend.build_tools(
            ASSIGNMENT_EN,
            scenario,
        )
    )

    assert set(tools) == set(scenario["tools"])

    for tool_name, definition in scenario["tools"].items():
        assert tools[tool_name]["parameters"] == definition["parameters"]


def test_build_tools_uses_localized_scenario_descriptions():
    scenario = load_invoice_scenario()
    backend = OllamaBackend()

    tools_en = tools_by_name(
        backend.build_tools(
            ASSIGNMENT_EN,
            scenario,
        )
    )
    tools_pl = tools_by_name(
        backend.build_tools(
            ASSIGNMENT_PL,
            scenario,
        )
    )

    for tool_name, definition in scenario["tools"].items():
        assert (
            tools_en[tool_name]["description"]
            == definition["description"]["en"].strip()
        )
        assert (
            tools_pl[tool_name]["description"]
            == definition["description"]["pl"].strip()
        )

    assert (
        tools_en["send_email"]["description"]
        != tools_pl["send_email"]["description"]
    )


def test_parse_native_tool_calls_preserves_call_data():
    backend = OllamaBackend()

    message = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": "call-123",
                "function": {
                    "name": "send_email",
                    "arguments": {
                        "recipient": "finance@example.test",
                        "content": "Invoice information",
                    },
                },
            }
        ],
    }

    assert backend.parse_native_tool_calls(message) == [
        {
            "tool": "send_email",
            "arguments": {
                "recipient": "finance@example.test",
                "content": "Invoice information",
            },
            "call_id": "call-123",
            "source": "native_tool_call",
        }
    ]
