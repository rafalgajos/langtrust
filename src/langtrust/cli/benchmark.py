"""CLI entrypoint for the LangTrust stateful security benchmark."""

from __future__ import annotations

import argparse

from langtrust.app.benchmark import (
    MAX_TURNS,
    MODEL,
    OLLAMA_BASE_URL,
    build_design,
    build_episode_record,
    build_metadata,
    get_conditions,
    get_git_commit,
    get_git_dirty,
    get_ollama_model_metadata,
    get_ollama_version,
    get_protected_conditions,
    run_benchmark,
    save_results,
    select_cells,
    select_pairs,
)
from langtrust.app.models import (
    config_from_namespace,
    validate_config,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the factor-aware LangTrust stateful security benchmark."
    )

    parser.add_argument(
        "--pair",
        action="append",
        dest="pairs",
        help="Run only the selected benchmark pair. May be supplied multiple times.",
    )
    parser.add_argument("--condition", choices=["both", "attack", "benign"], default="both")
    parser.add_argument("--protected", choices=["both", "false", "true"], default="both")
    parser.add_argument(
        "--cell",
        action="append",
        type=int,
        dest="cells",
        help=(
            "Run only the selected cell index within each scenario. "
            "May be supplied multiple times."
        ),
    )
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--num-predict", type=int, default=1024)
    parser.add_argument("--request-timeout", type=float, default=120)
    parser.add_argument("--seed-base", type=int, default=1000)
    parser.add_argument(
        "--model",
        default=MODEL,
        help="Ollama model name to use for benchmark inference.",
    )
    parser.add_argument("--output", default="results/langtrust_benchmark.json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--debug", action="store_true")

    return parser.parse_args()


def validate_args(args):
    validate_config(args)


def print_provenance(metadata):
    provenance = metadata["provenance"]
    git_info = provenance["git"]
    ollama_info = provenance["ollama"]
    model_info = provenance["model"]
    experiment_info = provenance["experiment"]

    print()
    print("=" * 80)
    print("BENCHMARK PROVENANCE")
    print("=" * 80)
    print("git commit:", git_info["commit"])
    print("git dirty:", git_info["dirty"])
    print("ollama version:", ollama_info["version"])
    print("ollama endpoint:", ollama_info["endpoint"])
    print("num predict:", experiment_info["num_predict"])
    print("request timeout:", experiment_info["request_timeout_seconds"], "seconds")
    print("max turns:", experiment_info["max_turns"])
    print("model:", model_info["name"])
    print("model digest:", model_info["digest"])
    print("family:", model_info["family"])
    print("parameters:", model_info["parameter_size"])
    print("quantization:", model_info["quantization_level"])
    print("context length:", model_info["context_length"])
    print("capabilities:", model_info["capabilities"])
    print("scenario files:", len(experiment_info["scenario_files"]))
    print("design cells:", experiment_info["unique_design_cells"])


def print_design_summary(design):
    print()
    print("=" * 80)
    print("LANGTRUST BENCHMARK DESIGN")
    print("=" * 80)

    counts = {}
    for item in design:
        key = (item["pair_id"], item["condition"])
        counts[key] = counts.get(key, 0) + 1

    for (pair_id, condition), count in sorted(counts.items()):
        print(pair_id, condition, "cells=", count)

    print()
    print("unique design cells:", len(design))


def summarize(results):
    inference_failures = [
        result for result in results if not result.get("inference", {}).get("success", True)
    ]

    valid_results = [
        result
        for result in results
        if result.get("evaluation") is not None
        and result.get("inference", {}).get("success", True)
    ]

    attack = [result for result in valid_results if result["condition"] == "attack"]
    benign = [result for result in valid_results if result["condition"] == "benign"]

    print()
    print("=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)

    print()
    print("recorded episodes:", len(results))
    print("inference-valid episodes:", len(valid_results))
    print("inference failures:", len(inference_failures))

    if inference_failures:
        failure_counts = {}
        for result in inference_failures:
            failure_type = result.get("inference", {}).get("failure_type") or "unknown"
            failure_counts[failure_type] = failure_counts.get(failure_type, 0) + 1
        print("inference failure types:", failure_counts)

    if attack:
        attempts = sum(
            int(result["evaluation"]["security"]["unauthorized_tool_attempt"])
            for result in attack
        )
        executions = sum(
            int(result["evaluation"]["security"]["unauthorized_execution"]) for result in attack
        )
        task_successes = sum(
            int(result["evaluation"]["utility"]["task_success"]) for result in attack
        )

        print()
        print("ATTACK")
        print("episodes:", len(attack))
        print("unauthorized attempts:", attempts)
        print("UTRR:", round(attempts / len(attack), 4))
        print("unauthorized executions:", executions)
        print("task successes:", task_successes)

    if benign:
        required_executed = sum(
            int(result["evaluation"]["utility"]["required_tools_executed"]) for result in benign
        )
        overblocked = sum(
            int(result["evaluation"]["utility"]["policy_overblocking"]) for result in benign
        )
        underaction = sum(
            int(result["evaluation"]["utility"]["model_underaction"]) for result in benign
        )
        task_successes = sum(
            int(result["evaluation"]["utility"]["task_success"]) for result in benign
        )

        print()
        print("BENIGN")
        print("episodes:", len(benign))
        print("required tool executed:", required_executed)
        print("policy overblocking:", overblocked)
        print("model underaction:", underaction)
        print("task successes:", task_successes)


def print_episode_result(scenario, result, evaluation):
    if evaluation is None:
        print("  inference success =", result.inference_success)
        print("  inference truncated =", result.inference_truncated)
        print("  inference failure =", result.inference_failure_type)
        return

    security = evaluation["security"]
    utility = evaluation["utility"]
    required_tools = scenario["evaluation"]["expected"].get("required_tools", [])
    required_tool_display = (
        utility["required_tools_executed"] if required_tools else "n/a"
    )

    print("  unauthorized attempt =", security["unauthorized_tool_attempt"])
    print("  unauthorized execution =", security["unauthorized_execution"])
    print("  required tool executed =", required_tool_display)
    print("  policy overblocking =", utility["policy_overblocking"])
    print("  model underaction =", utility["model_underaction"])
    print("  task success =", utility["task_success"])


def _cli_on_event(event):
    if event.get("type") == "episode_start":
        print()
        print(
            f"[{event['episode_number']}/{event['expected_episodes']}] "
            f"{event['pair_id']} {event['condition']} cell={event['cell_index']} "
            f"seed={event['seed']} protected={event['protected']}"
        )
        return

    if event.get("type") == "episode_complete":
        print_episode_result(
            event["scenario"],
            event["result"],
            event["evaluation"],
        )


def main(scenario_dir=None, git_repo=None):
    from langtrust.app.benchmark import build_benchmark_plan

    args = parse_args()
    config = config_from_namespace(args)
    validate_config(config)

    plan = build_benchmark_plan(
        config,
        scenario_dir=scenario_dir,
        git_repo=git_repo,
    )

    print_design_summary(plan.design)

    print("protected conditions:", plan.protected_conditions)
    print("repeats:", config.repeats)
    print("expected episodes:", plan.expected_episodes)

    print_provenance(plan.metadata)

    if config.dry_run:
        print()
        print("DRY RUN: no model inference performed.")
        return

    run_result = run_benchmark(
        config,
        scenario_dir=scenario_dir,
        git_repo=git_repo,
        on_event=_cli_on_event,
        plan=plan,
    )

    summarize(run_result.results)

    valid_episode_count = sum(
        1
        for result in run_result.results
        if result.get("evaluation") is not None
        and result.get("inference", {}).get("success", True)
    )
    inference_failure_count = len(run_result.results) - valid_episode_count

    print()
    print("Recorded:", len(run_result.results), "episodes")
    print("Inference-valid:", valid_episode_count, "episodes")
    print("Inference failures:", inference_failure_count)
    print("Saved:", run_result.output_path)


if __name__ == "__main__":
    main()
