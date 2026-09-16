from importlib.resources import files

import requests
import yaml


DEFAULT_NUM_PREDICT = 1024
DEFAULT_REQUEST_TIMEOUT = 120


class OllamaBackend:
    """Ollama backend using native tool calling."""

    def __init__(
        self,
        model="qwen2.5:14b",
        temperature=0,
        seed=None,
        num_predict=DEFAULT_NUM_PREDICT,
        request_timeout=DEFAULT_REQUEST_TIMEOUT,
    ):
        self.model = model
        self.temperature = temperature
        self.seed = seed
        self.num_predict = num_predict
        self.request_timeout = request_timeout

    def load_language_pack(self, language):
        path = (
            files("langtrust.resources")
            .joinpath("languages")
            .joinpath(f"{language}.yaml")
        )

        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def build_tools(self, language_assignment, scenario):
        """Build native Ollama tool schemas from scenario definitions."""
        tool_language = language_assignment["tool_description"]
        tools = []

        for tool_name, definition in scenario["tools"].items():
            descriptions = definition.get("description", {})

            if tool_language not in descriptions:
                raise KeyError(
                    f"Tool {tool_name!r} has no description for language "
                    f"{tool_language!r}"
                )

            parameters = definition.get("parameters")

            if parameters is None:
                raise KeyError(
                    f"Tool {tool_name!r} does not define 'parameters'"
                )

            if not isinstance(parameters, dict):
                raise TypeError(
                    f"Tool {tool_name!r} 'parameters' must be a dictionary"
                )

            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": descriptions[tool_language].strip(),
                        "parameters": parameters,
                    },
                }
            )

        return tools

    def chat(self, messages, tools=None):
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.num_predict,
            },
        }

        if self.seed is not None:
            payload["options"]["seed"] = self.seed

        if tools is not None:
            payload["tools"] = tools

        response = requests.post(
            "http://localhost:11434/api/chat",
            json=payload,
            timeout=self.request_timeout,
        )
        response.raise_for_status()

        return response.json()

    def parse_native_tool_calls(self, message):
        tool_calls = []

        for call in message.get("tool_calls", []):
            function = call.get("function", {})

            tool_calls.append(
                {
                    "tool": function.get("name", ""),
                    "arguments": function.get("arguments", {}),
                    "call_id": call.get("id", ""),
                    "source": "native_tool_call",
                }
            )

        return tool_calls
