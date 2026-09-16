from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import subprocess
import yaml

from src.langtrust.agent.qwen_tool_agent import QwenToolAgent
from src.langtrust.evaluation.stateful import StatefulEvaluator
from src.langtrust.scenarios.loader import ScenarioLoader


CASES_DIR = Path("generated")


def load_yaml(path):
    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:
        return yaml.safe_load(f)


def get_git_commit():
    try:
        return subprocess.check_output(
            [
                "git",
                "rev-parse",
                "HEAD",
            ],
            text=True,
        ).strip()

    except Exception:
        return ""


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run stateful LangTrust Qwen "
            "native-tool experiments."
        )
    )

    parser.add_argument(
        "--scenario",
        default="invoice_001.yaml",
        help=(
            "Scenario YAML filename from scenarios/."
        ),
    )

    parser.add_argument(
        "--case",
        action="append",
        dest="cases",
        help=(
            "Run only this generated case. "
            "May be supplied multiple times."
        ),
    )

    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
    )

    parser.add_argument(
        "--seed-base",
        type=int,
        default=1000,
    )

    parser.add_argument(
        "--protected",
        choices=[
            "both",
            "false",
            "true",
        ],
        default="both",
    )

    parser.add_argument(
        "--output",
        default=(
            "results/"
            "qwen_native_stateful.json"
        ),
    )

    parser.add_argument(
        "--debug",
        action="store_true",
    )

    return parser.parse_args()


def save_results(
    output_path,
    metadata,
    results,
):
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            {
                "metadata":
                    metadata,

                "results":
                    results,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )


def get_conditions(value):
    if value == "false":
        return [
            False
        ]

    if value == "true":
        return [
            True
        ]

    return [
        False,
        True,
    ]


def main():
    args = parse_args()

    if args.repeats < 1:
        raise ValueError(
            "--repeats must be >= 1"
        )


    scenario = ScenarioLoader(
        "scenarios"
    ).load(
        args.scenario
    )


    case_files = sorted(
        CASES_DIR.glob(
            "*.yaml"
        )
    )


    if args.cases:

        requested = set(
            args.cases
        )

        case_files = [
            path
            for path in case_files
            if path.name
            in requested
        ]

        found = {
            path.name
            for path in case_files
        }

        missing = (
            requested
            - found
        )

        if missing:
            raise FileNotFoundError(
                "Cases not found: "
                + ", ".join(
                    sorted(
                        missing
                    )
                )
            )


    if not case_files:
        raise RuntimeError(
            "No experiment cases selected."
        )


    conditions = get_conditions(
        args.protected
    )

    output_path = Path(
        args.output
    )


    metadata = {
        "scenario":
            scenario["id"],

        "scenario_file":
            args.scenario,

        "model":
            "qwen2.5:14b",

        "temperature":
            args.temperature,

        "seed_base":
            args.seed_base,

        "repeats":
            args.repeats,

        "protected_conditions":
            conditions,

        "git_commit":
            get_git_commit(),

        "generated_at":
            datetime.now(
                timezone.utc
            ).isoformat(),
    }


    evaluator = StatefulEvaluator()

    results = []

    total = (
        len(
            case_files
        )
        * args.repeats
        * len(
            conditions
        )
    )

    episode_number = 0


    for repeat in range(
        1,
        args.repeats + 1
    ):

        seed = (
            args.seed_base
            + repeat
            - 1
        )


        for case_file in case_files:

            case = load_yaml(
                case_file
            )

            language_assignment = (
                case[
                    "language_assignment"
                ]
            )


            for protected in conditions:

                episode_number += 1


                print()
                print(
                    f"[{episode_number}/{total}] "
                    f"{args.scenario} "
                    f"{case_file.name} "
                    f"seed={seed} "
                    f"protected={protected}"
                )


                agent = QwenToolAgent(
                    protected=
                        protected,

                    model=
                        "qwen2.5:14b",

                    temperature=
                        args.temperature,

                    seed=
                        seed,

                    max_turns=
                        8,

                    debug=
                        args.debug,
                )


                result = agent.run(
                    language_assignment,
                    scenario,
                )


                evaluation = (
                    evaluator.evaluate(
                        result,
                        scenario,
                    )
                )


                evaluation_dict = (
                    evaluation.to_dict()
                )


                record = {
                    "scenario":
                        scenario["id"],

                    "case":
                        case_file.name,

                    "case_id":
                        case["case_id"],

                    "repeat":
                        repeat,

                    "seed":
                        seed,

                    "temperature":
                        args.temperature,

                    "protected_prompt":
                        protected,

                    "language_assignment":
                        language_assignment,

                    "completed":
                        result.completed,

                    "turns":
                        result.turns,

                    "answer":
                        result.answer,

                    "events":
                        result.events,

                    "blocked_attempts":
                        result.blocked_attempts,

                    "initial_state":
                        result.initial_state,

                    "final_state":
                        result.final_state,

                    "evaluation":
                        evaluation_dict,
                }


                results.append(
                    record
                )


                save_results(
                    output_path,
                    metadata,
                    results,
                )


                security = (
                    evaluation_dict[
                        "security"
                    ]
                )

                utility = (
                    evaluation_dict[
                        "utility"
                    ]
                )

                state = (
                    evaluation_dict[
                        "state"
                    ]
                )


                print(
                    "  unauthorized attempt =",
                    security[
                        "unauthorized_tool_attempt"
                    ],
                )

                print(
                    "  unauthorized execution =",
                    security[
                        "unauthorized_execution"
                    ],
                )

                print(
                    "  policy overblocking =",
                    utility[
                        "policy_overblocking"
                    ],
                )

                print(
                    "  model underaction =",
                    utility[
                        "model_underaction"
                    ],
                )

                print(
                    "  task success =",
                    utility[
                        "task_success"
                    ],
                )

                print(
                    "  mailbox =",
                    (
                        state[
                            "initial_mailbox_size"
                        ],
                        state[
                            "final_mailbox_size"
                        ],
                    ),
                )


    print()
    print(
        f"Completed {len(results)} episodes."
    )

    print(
        f"Saved results to {output_path}"
    )


if __name__ == "__main__":
    main()
