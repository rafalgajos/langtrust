from dataclasses import dataclass

from src.langtrust.models.language_risk import LanguageRiskModel


@dataclass
class AgentResult:
    answer: str
    tool_calls: list
    risk_score: float


class AgentSimulator:
    """
    Scenario-aware language-dependent agent simulator.
    """

    def __init__(
        self,
        language_assignment,
        scenario
    ):

        self.language_assignment = language_assignment
        self.scenario = scenario

        self.risk_model = LanguageRiskModel()


    def run(
        self,
        user_instruction,
        content,
        attack_payload,
    ):

        risk = self.risk_model.calculate(
            self.language_assignment["user_instruction"],
            self.language_assignment["tool_description"],
            self.language_assignment["untrusted_content"],
            self.language_assignment["attack_payload"],
        )


        tool_calls = []


        target_tool = (
            self.scenario["attack"]["target"]["tool"]
        )


        if risk >= 0.5:

            tool_calls.append(
                {
                    "tool": target_tool,
                    "recipient": "audit@example.test",
                    "reason": self.scenario["attack"]["type"],
                }
            )

            return AgentResult(
                answer="Unauthorized action executed.",
                tool_calls=tool_calls,
                risk_score=risk,
            )


        return AgentResult(
            answer=self.scenario["agent"]["goal"],
            tool_calls=[],
            risk_score=risk,
        )
