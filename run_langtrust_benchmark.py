from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import subprocess
import urllib.request

from src.langtrust.agent.qwen_tool_agent import (
    QwenToolAgent,
)
from src.langtrust.benchmark.design import (
    generate_language_cells,
)
from src.langtrust.benchmark.pairs import (
    group_benchmark_pairs,
)
from src.langtrust.evaluation.stateful import (
    StatefulEvaluator,
)


MODEL = "qwen2.5:14b"
OLLAMA_BASE_URL = "http://localhost:11434"


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



def get_git_dirty():
    try:
        output = subprocess.check_output(
            [
                "git",
                "status",
                "--porcelain",
            ],
            text=True,
        ).strip()

        return bool(output)

    except Exception:
        return None


def get_ollama_version():
    try:
        output = subprocess.check_output(
            [
                "ollama",
                "--version",
            ],
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()

    except Exception:
        return None


    prefix = "ollama version is "

    if output.lower().startswith(
        prefix
    ):
        return output[
            len(prefix):
        ].strip()

    return output


def _ollama_json_request(
    path,
    payload=None,
):
    url = (
        OLLAMA_BASE_URL.rstrip("/")
        + path
    )


    if payload is None:

        request = urllib.request.Request(
            url,
            method="GET",
        )

    else:

        body = json.dumps(
            payload
        ).encode(
            "utf-8"
        )

        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type":
                    "application/json",
            },
            method="POST",
        )


    with urllib.request.urlopen(
        request,
        timeout=10,
    ) as response:

        return json.load(
            response
        )


def get_ollama_model_metadata(
    model_name,
):
    metadata = {
        "name":
            model_name,

        "digest":
            None,

        "modified_at":
            None,

        "size_bytes":
            None,

        "format":
            None,

        "family":
            None,

        "families":
            [],

        "parameter_size":
            None,

        "quantization_level":
            None,

        "context_length":
            None,

        "embedding_length":
            None,

        "capabilities":
            [],
    }


    #
    # /api/tags
    #

    try:

        tags = _ollama_json_request(
            "/api/tags"
        )


        model_record = next(
            (
                item
                for item
                in tags.get(
                    "models",
                    []
                )
                if (
                    item.get(
                        "name"
                    )
                    == model_name
                    or
                    item.get(
                        "model"
                    )
                    == model_name
                )
            ),
            None,
        )


        if model_record is None:

            metadata[
                "tags_error"
            ] = (
                "model_not_found"
            )

        else:

            details = (
                model_record.get(
                    "details"
                )
                or {}
            )


            metadata.update(
                {
                    "digest":
                        model_record.get(
                            "digest"
                        ),

                    "modified_at":
                        model_record.get(
                            "modified_at"
                        ),

                    "size_bytes":
                        model_record.get(
                            "size"
                        ),

                    "format":
                        details.get(
                            "format"
                        ),

                    "family":
                        details.get(
                            "family"
                        ),

                    "families":
                        details.get(
                            "families"
                        )
                        or [],

                    "parameter_size":
                        details.get(
                            "parameter_size"
                        ),

                    "quantization_level":
                        details.get(
                            "quantization_level"
                        ),

                    "context_length":
                        details.get(
                            "context_length"
                        ),

                    "embedding_length":
                        details.get(
                            "embedding_length"
                        ),
                }
            )


    except Exception as exc:

        metadata[
            "tags_error"
        ] = repr(
            exc
        )


    #
    # /api/show
    #

    try:

        show = _ollama_json_request(
            "/api/show",
            {
                "model":
                    model_name,
            },
        )


        metadata[
            "capabilities"
        ] = (
            show.get(
                "capabilities"
            )
            or []
        )


    except Exception as exc:

        metadata[
            "show_error"
        ] = repr(
            exc
        )


    return metadata


def build_metadata(
    args,
    design,
    protected_conditions,
    expected_episodes,
):
    generated_at = datetime.now(
        timezone.utc
    ).isoformat()


    git_commit = (
        get_git_commit()
    )

    git_dirty = (
        get_git_dirty()
    )


    ollama_version = (
        get_ollama_version()
    )


    model_metadata = (
        get_ollama_model_metadata(
            MODEL
        )
    )


    selected_pairs = sorted(
        {
            item[
                "pair_id"
            ]
            for item
            in design
        }
    )


    scenario_files = sorted(
        {
            item[
                "scenario_file"
            ]
            for item
            in design
        }
    )


    design_cells = []

    for item in design:

        cell = item[
            "cell"
        ]

        design_cells.append(
            {
                "pair_id":
                    item[
                        "pair_id"
                    ],

                "condition":
                    item[
                        "condition"
                    ],

                "scenario_file":
                    item[
                        "scenario_file"
                    ],

                "cell_index":
                    cell[
                        "cell_index"
                    ],

                "cell_key":
                    cell[
                        "cell_key"
                    ],

                "active_language_factors":
                    cell[
                        "active_language_factors"
                    ],

                "active_language_assignment":
                    cell[
                        "active_language_assignment"
                    ],

                "language_assignment":
                    cell[
                        "language_assignment"
                    ],
            }
        )


    provenance = {
        "timestamp_utc":
            generated_at,

        "git": {
            "commit":
                git_commit,

            "dirty":
                git_dirty,
        },

        "ollama": {
            "version":
                ollama_version,

            "endpoint":
                OLLAMA_BASE_URL,
        },

        "model":
            model_metadata,

        "experiment": {
            "temperature":
                args.temperature,

            "num_predict":
                args.num_predict,

            "request_timeout_seconds":
                args.request_timeout,

            "seed_base":
                args.seed_base,

            "repeats":
                args.repeats,

            "protected_conditions":
                protected_conditions,

            "selected_pairs":
                selected_pairs,

            "scenario_files":
                scenario_files,

            "unique_design_cells":
                len(
                    design
                ),

            "expected_episodes":
                expected_episodes,

            "design_cells":
                design_cells,
        },
    }


    #
    # Keep old top-level fields for compatibility
    # with existing analysis scripts.
    #

    return {
        "benchmark":
            "LangTrust",

        "model":
            MODEL,

        "temperature":
            args.temperature,

        "num_predict":
            args.num_predict,

        "request_timeout_seconds":
            args.request_timeout,

        "seed_base":
            args.seed_base,

        "repeats":
            args.repeats,

        "protected_conditions":
            protected_conditions,

        "unique_design_cells":
            len(
                design
            ),

        "expected_episodes":
            expected_episodes,

        "git_commit":
            git_commit,

        "git_dirty":
            git_dirty,

        "generated_at":
            generated_at,

        "provenance":
            provenance,
    }


def print_provenance(
    metadata,
):
    provenance = metadata[
        "provenance"
    ]

    git_info = provenance[
        "git"
    ]

    ollama_info = provenance[
        "ollama"
    ]

    model_info = provenance[
        "model"
    ]

    experiment_info = provenance[
        "experiment"
    ]


    print()
    print("=" * 80)
    print("BENCHMARK PROVENANCE")
    print("=" * 80)

    print(
        "git commit:",
        git_info[
            "commit"
        ],
    )

    print(
        "git dirty:",
        git_info[
            "dirty"
        ],
    )

    print(
        "ollama version:",
        ollama_info[
            "version"
        ],
    )

    print(
        "ollama endpoint:",
        ollama_info[
            "endpoint"
        ],
    )

    print(
        "num predict:",
        experiment_info[
            "num_predict"
        ],
    )

    print(
        "request timeout:",
        experiment_info[
            "request_timeout_seconds"
        ],
        "seconds",
    )

    print(
        "model:",
        model_info[
            "name"
        ],
    )

    print(
        "model digest:",
        model_info[
            "digest"
        ],
    )

    print(
        "family:",
        model_info[
            "family"
        ],
    )

    print(
        "parameters:",
        model_info[
            "parameter_size"
        ],
    )

    print(
        "quantization:",
        model_info[
            "quantization_level"
        ],
    )

    print(
        "context length:",
        model_info[
            "context_length"
        ],
    )

    print(
        "capabilities:",
        model_info[
            "capabilities"
        ],
    )

    print(
        "scenario files:",
        len(
            provenance[
                "experiment"
            ][
                "scenario_files"
            ]
        ),
    )

    print(
        "design cells:",
        provenance[
            "experiment"
        ][
            "unique_design_cells"
        ],
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run the factor-aware LangTrust "
            "stateful security benchmark."
        )
    )


    parser.add_argument(
        "--pair",
        action="append",
        dest="pairs",
        help=(
            "Run only the selected benchmark pair. "
            "May be supplied multiple times."
        ),
    )


    parser.add_argument(
        "--condition",
        choices=[
            "both",
            "attack",
            "benign",
        ],
        default="both",
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
        "--cell",
        action="append",
        type=int,
        dest="cells",
        help=(
            "Run only the selected cell index "
            "within each scenario. "
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
        "--num-predict",
        type=int,
        default=1024,
    )


    parser.add_argument(
        "--request-timeout",
        type=float,
        default=120,
    )


    parser.add_argument(
        "--seed-base",
        type=int,
        default=1000,
    )


    parser.add_argument(
        "--output",
        default=(
            "results/"
            "langtrust_benchmark.json"
        ),
    )


    parser.add_argument(
        "--dry-run",
        action="store_true",
    )


    parser.add_argument(
        "--debug",
        action="store_true",
    )


    return parser.parse_args()


def get_conditions(value):
    if value == "attack":
        return [
            "attack"
        ]

    if value == "benign":
        return [
            "benign"
        ]

    return [
        "attack",
        "benign",
    ]


def get_protected_conditions(
    value,
):
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


def save_results(
    path,
    metadata,
    results,
):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        path,
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


def select_pairs(
    all_pairs,
    requested_pairs,
):
    if not requested_pairs:
        return all_pairs


    requested = set(
        requested_pairs
    )

    unknown = (
        requested
        - set(all_pairs)
    )

    if unknown:
        raise ValueError(
            "Unknown benchmark pair(s): "
            + ", ".join(
                sorted(unknown)
            )
        )


    return {
        pair_id:
            all_pairs[
                pair_id
            ]
        for pair_id
        in sorted(requested)
    }


def select_cells(
    cells,
    requested_cells,
):
    if not requested_cells:
        return cells


    requested = set(
        requested_cells
    )


    selected = [
        cell
        for cell in cells
        if cell[
            "cell_index"
        ]
        in requested
    ]


    found = {
        cell[
            "cell_index"
        ]
        for cell
        in selected
    }


    missing = (
        requested
        - found
    )

    if missing:
        raise ValueError(
            "Requested cell index does not "
            "exist in this scenario: "
            + ", ".join(
                str(value)
                for value
                in sorted(missing)
            )
        )


    return selected


def build_design(
    pairs,
    conditions,
    requested_cells,
):
    design = []


    for pair_id, pair in sorted(
        pairs.items()
    ):

        for condition in conditions:

            scenario = pair[
                condition
            ]

            benchmark = scenario[
                "benchmark"
            ]


            cells = (
                generate_language_cells(
                    scenario
                )
            )


            cells = select_cells(
                cells,
                requested_cells,
            )


            for cell in cells:

                design.append(
                    {
                        "pair_id":
                            pair_id,

                        "domain":
                            benchmark[
                                "domain"
                            ],

                        "condition":
                            condition,

                        "scenario":
                            scenario,

                        "scenario_file":
                            scenario[
                                "_scenario_file"
                            ],

                        "cell":
                            cell,
                    }
                )


    return design


def print_design_summary(
    design,
):
    print()
    print("=" * 80)
    print("LANGTRUST BENCHMARK DESIGN")
    print("=" * 80)


    counts = {}


    for item in design:

        key = (
            item[
                "pair_id"
            ],
            item[
                "condition"
            ],
        )

        counts[
            key
        ] = (
            counts.get(
                key,
                0,
            )
            + 1
        )


    for (
        pair_id,
        condition,
    ), count in sorted(
        counts.items()
    ):

        print(
            pair_id,
            condition,
            "cells=",
            count,
        )


    print()
    print(
        "unique design cells:",
        len(design),
    )


def summarize(
    results,
):
    inference_failures = [
        result
        for result in results
        if not result.get(
            "inference",
            {}
        ).get(
            "success",
            True,
        )
    ]


    valid_results = [
        result
        for result in results
        if (
            result.get(
                "evaluation"
            )
            is not None
            and
            result.get(
                "inference",
                {}
            ).get(
                "success",
                True,
            )
        )
    ]


    attack = [
        result
        for result in valid_results
        if result[
            "condition"
        ]
        == "attack"
    ]

    benign = [
        result
        for result in valid_results
        if result[
            "condition"
        ]
        == "benign"
    ]


    print()
    print("=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)

    print()
    print(
        "recorded episodes:",
        len(results),
    )

    print(
        "inference-valid episodes:",
        len(valid_results),
    )

    print(
        "inference failures:",
        len(inference_failures),
    )


    if inference_failures:

        failure_counts = {}

        for result in inference_failures:

            failure_type = (
                result.get(
                    "inference",
                    {}
                ).get(
                    "failure_type"
                )
                or "unknown"
            )

            failure_counts[
                failure_type
            ] = (
                failure_counts.get(
                    failure_type,
                    0,
                )
                + 1
            )

        print(
            "inference failure types:",
            failure_counts,
        )


    if attack:

        attempts = sum(
            int(
                result[
                    "evaluation"
                ][
                    "security"
                ][
                    "unauthorized_tool_attempt"
                ]
            )
            for result
            in attack
        )

        executions = sum(
            int(
                result[
                    "evaluation"
                ][
                    "security"
                ][
                    "unauthorized_execution"
                ]
            )
            for result
            in attack
        )

        task_successes = sum(
            int(
                result[
                    "evaluation"
                ][
                    "utility"
                ][
                    "task_success"
                ]
            )
            for result
            in attack
        )


        print()
        print("ATTACK")

        print(
            "episodes:",
            len(attack),
        )

        print(
            "unauthorized attempts:",
            attempts,
        )

        print(
            "UTRR:",
            round(
                attempts
                / len(attack),
                4,
            ),
        )

        print(
            "unauthorized executions:",
            executions,
        )

        print(
            "task successes:",
            task_successes,
        )


    if benign:

        required_executed = sum(
            int(
                result[
                    "evaluation"
                ][
                    "utility"
                ][
                    "required_tools_executed"
                ]
            )
            for result
            in benign
        )

        overblocked = sum(
            int(
                result[
                    "evaluation"
                ][
                    "utility"
                ][
                    "policy_overblocking"
                ]
            )
            for result
            in benign
        )

        underaction = sum(
            int(
                result[
                    "evaluation"
                ][
                    "utility"
                ][
                    "model_underaction"
                ]
            )
            for result
            in benign
        )

        task_successes = sum(
            int(
                result[
                    "evaluation"
                ][
                    "utility"
                ][
                    "task_success"
                ]
            )
            for result
            in benign
        )


        print()
        print("BENIGN")

        print(
            "episodes:",
            len(benign),
        )

        print(
            "required tool executed:",
            required_executed,
        )

        print(
            "policy overblocking:",
            overblocked,
        )

        print(
            "model underaction:",
            underaction,
        )

        print(
            "task successes:",
            task_successes,
        )


def main():
    args = parse_args()


    if args.repeats < 1:
        raise ValueError(
            "--repeats must be >= 1"
        )


    if args.num_predict < 1:
        raise ValueError(
            "--num-predict must be >= 1"
        )


    if args.request_timeout <= 0:
        raise ValueError(
            "--request-timeout must be > 0"
        )


    all_pairs = (
        group_benchmark_pairs(
            "scenarios"
        )
    )


    pairs = select_pairs(
        all_pairs,
        args.pairs,
    )


    conditions = get_conditions(
        args.condition
    )


    protected_conditions = (
        get_protected_conditions(
            args.protected
        )
    )


    design = build_design(
        pairs,
        conditions,
        args.cells,
    )


    print_design_summary(
        design
    )


    expected_episodes = (
        len(design)
        * args.repeats
        * len(
            protected_conditions
        )
    )


    print(
        "protected conditions:",
        protected_conditions,
    )

    print(
        "repeats:",
        args.repeats,
    )

    print(
        "expected episodes:",
        expected_episodes,
    )


    metadata = build_metadata(
        args,
        design,
        protected_conditions,
        expected_episodes,
    )


    print_provenance(
        metadata
    )


    if args.dry_run:
        print()
        print(
            "DRY RUN: no model calls performed."
        )
        return


    evaluator = (
        StatefulEvaluator()
    )

    output_path = Path(
        args.output
    )


    results = []

    episode_number = 0


    for repeat in range(
        1,
        args.repeats + 1,
    ):

        seed = (
            args.seed_base
            + repeat
            - 1
        )


        for item in design:

            pair_id = (
                item[
                    "pair_id"
                ]
            )

            domain = (
                item[
                    "domain"
                ]
            )

            condition = (
                item[
                    "condition"
                ]
            )

            scenario = (
                item[
                    "scenario"
                ]
            )

            scenario_file = (
                item[
                    "scenario_file"
                ]
            )

            cell = (
                item[
                    "cell"
                ]
            )

            language_assignment = (
                cell[
                    "language_assignment"
                ]
            )


            for protected in (
                protected_conditions
            ):

                episode_number += 1


                print()
                print(
                    f"[{episode_number}/"
                    f"{expected_episodes}] "
                    f"{pair_id} "
                    f"{condition} "
                    f"cell={cell['cell_index']} "
                    f"seed={seed} "
                    f"protected={protected}"
                )


                agent = QwenToolAgent(
                    protected=
                        protected,

                    model=
                        MODEL,

                    temperature=
                        args.temperature,

                    seed=
                        seed,

                    num_predict=
                        args.num_predict,

                    request_timeout=
                        args.request_timeout,

                    max_turns=
                        8,

                    debug=
                        args.debug,
                )


                result = agent.run(
                    language_assignment,
                    scenario,
                )


                if result.inference_success:

                    evaluation = (
                        evaluator.evaluate(
                            result,
                            scenario,
                        )
                    )

                    evaluation_dict = (
                        evaluation.to_dict()
                    )

                else:

                    evaluation_dict = None


                record = {
                    "pair_id":
                        pair_id,

                    "domain":
                        domain,

                    "condition":
                        condition,

                    "scenario":
                        scenario["id"],

                    "scenario_file":
                        scenario_file,

                    "cell_index":
                        cell[
                            "cell_index"
                        ],

                    "cell_key":
                        cell[
                            "cell_key"
                        ],

                    "active_language_factors":
                        cell[
                            "active_language_factors"
                        ],

                    "active_language_assignment":
                        cell[
                            "active_language_assignment"
                        ],

                    "language_assignment":
                        language_assignment,

                    "inactive_language":
                        cell[
                            "inactive_language"
                        ],

                    "repeat":
                        repeat,

                    "seed":
                        seed,

                    "temperature":
                        args.temperature,

                    "num_predict":
                        args.num_predict,

                    "request_timeout_seconds":
                        args.request_timeout,

                    "protected_prompt":
                        protected,

                    "completed":
                        result.completed,

                    "inference": {
                        "success":
                            result.inference_success,

                        "truncated":
                            result.inference_truncated,

                        "failure_type":
                            result.inference_failure_type,

                        "error":
                            result.inference_error,

                        "calls":
                            result.inference_calls,
                    },

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


                if evaluation_dict is None:

                    print(
                        "  inference success =",
                        result.inference_success,
                    )

                    print(
                        "  inference truncated =",
                        result.inference_truncated,
                    )

                    print(
                        "  inference failure =",
                        result.inference_failure_type,
                    )

                    continue


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


                required_tools = (
                    scenario[
                        "evaluation"
                    ][
                        "expected"
                    ].get(
                        "required_tools",
                        []
                    )
                )

                if required_tools:
                    required_tool_display = (
                        utility[
                            "required_tools_executed"
                        ]
                    )
                else:
                    required_tool_display = "n/a"


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
                    "  required tool executed =",
                    required_tool_display,
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


    save_results(
        output_path,
        metadata,
        results,
    )


    summarize(
        results
    )


    valid_episode_count = sum(
        1
        for result in results
        if (
            result.get(
                "evaluation"
            )
            is not None
            and
            result.get(
                "inference",
                {}
            ).get(
                "success",
                True,
            )
        )
    )

    inference_failure_count = (
        len(results)
        - valid_episode_count
    )


    print()
    print(
        "Recorded:",
        len(results),
        "episodes"
    )

    print(
        "Inference-valid:",
        valid_episode_count,
        "episodes"
    )

    print(
        "Inference failures:",
        inference_failure_count,
    )

    print(
        "Saved:",
        output_path
    )


if __name__ == "__main__":
    main()
