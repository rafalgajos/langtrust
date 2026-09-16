from pathlib import Path
import json
import yaml

from src.langtrust.backend.qwen_backend import QwenBackend
from src.langtrust.scenarios.loader import ScenarioLoader
from src.langtrust.security.pipeline import SecurityPipeline


CASES_DIR = Path("generated")
OUTPUT = Path("results/qwen_results.json")


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run():

    scenario_loader = ScenarioLoader(
        "scenarios"
    )

    scenario = scenario_loader.load(
        "invoice_001.yaml"
    )

    security = SecurityPipeline(
        scenario
    )

    results = []


    for case_file in sorted(
        CASES_DIR.glob("*.yaml")
    ):

        case = load_yaml(
            case_file
        )

        language_assignment = (
            case["language_assignment"]
        )


        for protected in [False, True]:

            backend = QwenBackend(
                protected=protected
            )

            result = backend.run(
                language_assignment,
                scenario
            )

            decision = security.evaluate(
                result.answer
            )


            attack_intent_detected = (
                decision.tool_name != ""
            )

            runtime_blocked = (
                attack_intent_detected
                and decision.blocked
            )

            attack_success_after_enforcement = (
                attack_intent_detected
                and not runtime_blocked
            )


            results.append(
                {
                    "case": case_file.name,

                    "protected": protected,

                    "language_assignment":
                        language_assignment,

                    "answer":
                        result.answer,

                    # Diagnostic information produced
                    # directly by the backend.
                    "backend_tool_calls":
                        result.tool_calls,

                    # Canonical model-behaviour measurement.
                    "model_behavior": {
                        "attack_intent_detected":
                            attack_intent_detected,

                        "tool_name":
                            decision.tool_name
                    },

                    # Runtime LangTrust enforcement.
                    "security_enforcement": {
                        "blocked":
                            runtime_blocked,

                        "reason":
                            decision.reason
                    },

                    # Attack succeeds only if malicious
                    # intent reaches execution.
                    "attack_success_after_enforcement":
                        attack_success_after_enforcement
                }
            )


    OUTPUT.parent.mkdir(
        exist_ok=True
    )

    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            indent=2,
            ensure_ascii=False
        )


    print(
        f"Executed {len(results)} cases"
    )

    print(
        f"Saved results to {OUTPUT}"
    )


if __name__ == "__main__":
    run()
