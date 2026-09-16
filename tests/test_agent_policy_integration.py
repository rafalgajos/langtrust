from pathlib import Path

from langtrust.agent.ollama_tool_agent import OllamaToolAgent
from langtrust.scenarios.loader import ScenarioLoader


SCENARIO_DIR = Path(__file__).resolve().parents[1] / "scenarios"

LANGUAGE_ASSIGNMENT = {
    "user_instruction": "en",
    "tool_description": "en",
    "untrusted_content": "en",
    "attack_payload": "en",
}


def load_scenario(filename):
    return ScenarioLoader(str(SCENARIO_DIR)).load(filename)


def model_response(content="", tool_calls=None):
    return {
        "done": True,
        "done_reason": "stop",
        "prompt_eval_count": 10,
        "eval_count": 5,
        "message": {
            "role": "assistant",
            "content": content,
            "tool_calls": tool_calls or [],
        },
    }


def test_forbidden_native_tool_call_is_blocked_before_execution():
    scenario = load_scenario("invoice_001.yaml")

    agent = OllamaToolAgent(
        protected=False,
        temperature=0,
        seed=1001,
    )

    responses = iter(
        [
            model_response(
                tool_calls=[
                    {
                        "id": "attack-call",
                        "function": {
                            "name": "send_email",
                            "arguments": {
                                "recipient": "audit@example.test",
                                "content": "Invoice information",
                            },
                        },
                    }
                ]
            ),
            model_response(content="Done."),
        ]
    )

    agent.backend.chat = lambda **kwargs: next(responses)

    result = agent.run(
        LANGUAGE_ASSIGNMENT,
        scenario,
    )

    email_events = [event for event in result.events if event["tool"] == "send_email"]
    assert len(email_events) == 1
    event = email_events[0]

    assert event["call_id"] == "attack-call"
    assert event["allowed"] is False
    assert event["blocked"] is True
    assert event["executed"] is False
    assert event["state_changed"] is False

    assert result.blocked_attempts == [event]

    assert result.final_state["mailbox"]["sent_messages"] == []
    assert result.initial_state == result.final_state
    assert result.inference_success is True
    assert result.completed is True


def test_authorized_native_tool_call_executes_in_local_sandbox():
    scenario = load_scenario("invoice_benign_email_001.yaml")

    agent = OllamaToolAgent(
        protected=False,
        temperature=0,
        seed=1001,
    )

    content = (
        "Invoice FV-2026-081 is due "
        "for payment on 2026-09-14."
    )

    responses = iter(
        [
            model_response(
                tool_calls=[
                    {
                        "id": "benign-call",
                        "function": {
                            "name": "send_email",
                            "arguments": {
                                "recipient": "finance@example.test",
                                "content": content,
                            },
                        },
                    }
                ]
            ),
            model_response(content="Done."),
        ]
    )

    agent.backend.chat = lambda **kwargs: next(responses)

    result = agent.run(
        LANGUAGE_ASSIGNMENT,
        scenario,
    )

    email_events = [event for event in result.events if event["tool"] == "send_email"]
    assert len(email_events) == 1
    event = email_events[0]

    assert event["call_id"] == "benign-call"
    assert event["allowed"] is True
    assert event["blocked"] is False
    assert event["executed"] is True
    assert event["state_changed"] is True

    assert result.blocked_attempts == []

    assert result.final_state["mailbox"]["sent_messages"] == [
        {
            "recipient": "finance@example.test",
            "content": content,
        }
    ]

    assert result.inference_success is True
    assert result.completed is True
