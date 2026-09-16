import pytest
import requests
import yaml

from langtrust.agent.ollama_tool_agent import OllamaToolAgent
from langtrust.backend.ollama_backend import OllamaBackend


def load_invoice_scenario():
    with open("scenarios/invoice_benign_email_001.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def language_assignment():
    return {
        "user_instruction": "en",
        "tool_description": "en",
        "untrusted_content": "en",
        "attack_payload": "en",
    }



@pytest.mark.parametrize(
    ("exception", "expected"),
    [
        (requests.exceptions.ReadTimeout("timeout"), "read_timeout"),
        (requests.exceptions.Timeout("timeout"), "timeout"),
        (requests.exceptions.ConnectionError("connection"), "request_error"),
    ],
)
def test_request_failure_classification(exception, expected):
    assert OllamaToolAgent._classify_request_failure(exception) == expected

def test_backend_sends_generation_budget_and_timeout(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "done": True,
                "done_reason": "stop",
                "message": {"role": "assistant", "content": "OK"},
            }

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["payload"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)

    backend = OllamaBackend(
        model="qwen2.5:14b",
        temperature=0,
        seed=1001,
        num_predict=1024,
        request_timeout=120,
    )
    backend.chat(messages=[{"role": "user", "content": "test"}], tools=[])

    options = captured["payload"]["options"]
    assert options["num_predict"] == 1024
    assert options["seed"] == 1001
    assert captured["timeout"] == 120


def test_generation_limit_is_inference_failure_and_executes_nothing():
    scenario = load_invoice_scenario()
    agent = OllamaToolAgent(protected=True, num_predict=1024, request_timeout=120)

    agent.backend.chat = lambda **kwargs: {
        "done": True,
        "done_reason": "length",
        "prompt_eval_count": 100,
        "eval_count": 1024,
        "message": {
            "role": "assistant",
            "content": "truncated",
            "tool_calls": [
                {
                    "function": {
                        "name": "send_email",
                        "arguments": {
                            "recipient": "finance@example.test",
                            "content": "SHOULD NOT EXECUTE",
                        },
                    }
                }
            ],
        },
    }

    result = agent.run(language_assignment(), scenario)

    assert result.inference_success is False
    assert result.inference_truncated is True
    assert result.inference_failure_type == "generation_limit"
    assert result.completed is False
    assert result.events == []
    assert result.initial_state == result.final_state
    assert len(result.inference_calls) == 1
    assert result.inference_calls[0]["done_reason"] == "length"


def test_read_timeout_is_recorded_as_inference_failure():
    scenario = load_invoice_scenario()
    agent = OllamaToolAgent(protected=False, num_predict=1024, request_timeout=120)

    def fail_chat(**kwargs):
        raise requests.exceptions.ReadTimeout("synthetic timeout")

    agent.backend.chat = fail_chat
    result = agent.run(language_assignment(), scenario)

    assert result.inference_success is False
    assert result.inference_truncated is False
    assert result.inference_failure_type == "read_timeout"
    assert result.completed is False
    assert result.events == []
    assert result.initial_state == result.final_state
    assert len(result.inference_calls) == 1
    assert result.inference_calls[0]["success"] is False


def test_normal_completion_remains_inference_valid():
    scenario = load_invoice_scenario()
    agent = OllamaToolAgent(protected=False, num_predict=1024, request_timeout=120)

    agent.backend.chat = lambda **kwargs: {
        "done": True,
        "done_reason": "stop",
        "prompt_eval_count": 100,
        "eval_count": 20,
        "message": {
            "role": "assistant",
            "content": "Normal completion.",
            "tool_calls": [],
        },
    }

    result = agent.run(language_assignment(), scenario)

    assert result.inference_success is True
    assert result.inference_truncated is False
    assert result.inference_failure_type is None
    assert result.completed is True
    assert len(result.inference_calls) == 1
    assert result.inference_calls[0]["done_reason"] == "stop"
