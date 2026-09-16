from pathlib import Path
import json
import yaml

from src.langtrust.agent.simulator import AgentSimulator
from src.langtrust.evaluation.evaluator import SecurityEvaluator
from src.langtrust.scenarios.loader import ScenarioLoader


CASES_DIR = Path("generated")
OUTPUT = Path("results/results.json")


def load_yaml(path):

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:
        return yaml.safe_load(f)



def run():

    evaluator = SecurityEvaluator(
        forbidden_tools=[
            "send_email"
        ]
    )


    scenario_loader = ScenarioLoader(
        "scenarios"
    )


    experiment = load_yaml(
        "experiment.yaml"
    )


    scenario_file = (
        experiment["scenario"]["path"]
        .split("/")[-1]
    )


    scenario = scenario_loader.load(
        scenario_file
    )


    results = []


    for case_file in sorted(
        CASES_DIR.glob("*.yaml")
    ):

        case = load_yaml(
            case_file
        )


        agent = AgentSimulator(
            language_assignment=
                case["language_assignment"],

            scenario=scenario
        )


        result = agent.run(
            scenario["agent"]["goal"],
            scenario["environment"]["invoice"]["content"],
            scenario["attack"]["payload"]
        )


        evaluation = evaluator.evaluate(
            result
        )


        results.append(
            {
                "case": case_file.name,

                "language_assignment":
                    case["language_assignment"],

                "evaluation":
                    evaluation
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
