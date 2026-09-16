from dataclasses import dataclass


@dataclass
class ToolPolicyDecision:
    allowed: bool
    reason: str


class ToolPolicyEngine:
    """Evaluate whether a tool request is permitted by the scenario policy."""

    def __init__(self, scenario):
        self.scenario = scenario

    def check(self, tool_name):
        definition = self.scenario["tools"].get(tool_name)

        if definition is None:
            return ToolPolicyDecision(allowed=False, reason="Unknown tool")

        if definition["permission"]["allowed"]:
            return ToolPolicyDecision(allowed=True, reason="Tool explicitly allowed")

        return ToolPolicyDecision(
            allowed=False,
            reason="Tool permission denied by scenario",
        )
