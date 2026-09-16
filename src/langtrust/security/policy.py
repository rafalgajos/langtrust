from dataclasses import dataclass


@dataclass
class ToolPolicyDecision:
    allowed: bool
    reason: str


class ToolPolicyEngine:
    """
    Evaluates whether an agent tool request is allowed.
    """

    def __init__(self, scenario):
        self.scenario = scenario


    def check(self, tool_name):

        for tool, definition in self.scenario["tools"].items():

            if tool == tool_name:

                allowed = definition["permission"]["allowed"]

                if allowed:
                    return ToolPolicyDecision(
                        allowed=True,
                        reason="Tool explicitly allowed"
                    )

                return ToolPolicyDecision(
                    allowed=False,
                    reason="Tool permission denied by scenario"
                )


        return ToolPolicyDecision(
            allowed=False,
            reason="Unknown tool"
        )
