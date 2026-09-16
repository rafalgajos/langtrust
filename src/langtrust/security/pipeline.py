from dataclasses import dataclass

from src.langtrust.security.tool_detector import ToolIntentDetector
from src.langtrust.security.policy import ToolPolicyEngine


@dataclass
class SecurityDecision:
    blocked: bool
    tool_name: str
    reason: str


class SecurityPipeline:
    """
    Executes LangTrust security checks after model generation.
    """

    def __init__(self, scenario):

        self.detector = ToolIntentDetector()
        self.policy = ToolPolicyEngine(scenario)


    def evaluate(self, model_output):

        intent = self.detector.detect(
            model_output
        )


        if not intent.detected:

            return SecurityDecision(
                blocked=False,
                tool_name="",
                reason="No tool intent detected"
            )


        decision = self.policy.check(
            intent.tool_name
        )


        if not decision.allowed:

            return SecurityDecision(
                blocked=True,
                tool_name=intent.tool_name,
                reason=decision.reason
            )


        return SecurityDecision(
            blocked=False,
            tool_name=intent.tool_name,
            reason=decision.reason
        )
