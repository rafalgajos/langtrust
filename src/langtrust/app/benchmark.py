"""Benchmark orchestration helpers extracted from the CLI."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import copy
import json
import subprocess
import urllib.request

from langtrust.agent.ollama_tool_agent import OllamaToolAgent
from langtrust.app.models import (
    BenchmarkPlan,
    BenchmarkRunConfig,
    BenchmarkRunResult,
    validate_config,
)
from langtrust.benchmark.design import generate_language_cells
from langtrust.benchmark.pairs import group_benchmark_pairs
from langtrust.evaluation.stateful import StatefulEvaluator


MODEL = "qwen2.5:14b"
OLLAMA_BASE_URL = "http://localhost:11434"
MAX_TURNS = 8


def get_git_commit(repo_path=None):
    if repo_path is None:
        return None

    try:
        return subprocess.check_output(
            ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def get_git_dirty(repo_path=None):
    if repo_path is None:
        return None

    try:
        output = subprocess.check_output(
            ["git", "-C", str(repo_path), "status", "--porcelain"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        return bool(output)
    except Exception:
        return None


def get_ollama_version():
    try:
        output = subprocess.check_output(
            ["ollama", "--version"], text=True, stderr=subprocess.STDOUT
        ).strip()
    except Exception:
        return None

    prefix = "ollama version is "
    if output.lower().startswith(prefix):
        return output[len(prefix):].strip()
    return output


def _ollama_json_request(path, payload=None):
    url = OLLAMA_BASE_URL.rstrip("/") + path

    if payload is None:
        request = urllib.request.Request(url, method="GET")
    else:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)


def _model_info_value(model_info, suffix):
    for key, value in model_info.items():
        if key.endswith(suffix):
            return value
    return None


def get_ollama_model_metadata(model_name):
    metadata = {
        "name": model_name,
        "digest": None,
        "modified_at": None,
        "size_bytes": None,
        "format": None,
        "family": None,
        "families": [],
        "parameter_size": None,
        "quantization_level": None,
        "context_length": None,
        "embedding_length": None,
        "capabilities": [],
    }

    # Prefer /api/tags for digest/size; fall back fields may come from /api/show.
    try:
        tags = _ollama_json_request("/api/tags")
        model_record = next(
            (
                item
                for item in tags.get("models", [])
                if item.get("name") == model_name or item.get("model") == model_name
            ),
            None,
        )

        if model_record is None:
            metadata["tags_error"] = "model_not_found"
        else:
            details = model_record.get("details") or {}
            metadata.update(
                {
                    "digest": model_record.get("digest"),
                    "modified_at": model_record.get("modified_at"),
                    "size_bytes": model_record.get("size"),
                    "format": details.get("format"),
                    "family": details.get("family"),
                    "families": details.get("families") or [],
                    "parameter_size": details.get("parameter_size"),
                    "quantization_level": details.get("quantization_level"),
                    "context_length": details.get("context_length"),
                    "embedding_length": details.get("embedding_length"),
                }
            )
    except Exception as exc:
        metadata["tags_error"] = repr(exc)

    try:
        show = _ollama_json_request("/api/show", {"model": model_name})
        metadata["capabilities"] = show.get("capabilities") or []

        model_info = show.get("model_info") or {}
        metadata["context_length"] = (
            metadata["context_length"]
            or _model_info_value(model_info, ".context_length")
        )
        metadata["embedding_length"] = (
            metadata["embedding_length"]
            or _model_info_value(model_info, ".embedding_length")
        )
    except Exception as exc:
        metadata["show_error"] = repr(exc)

    return metadata


def build_metadata(
    args,
    design,
    protected_conditions,
    expected_episodes,
    git_repo=None,
    *,
    collect_runtime_metadata=True,
):
    generated_at = datetime.now(timezone.utc).isoformat()

    git_commit = get_git_commit(git_repo)
    git_dirty = get_git_dirty(git_repo)

    model_name = getattr(args, "model", MODEL)

    if collect_runtime_metadata:
        ollama_version = get_ollama_version()
        model_metadata = get_ollama_model_metadata(model_name)
    else:
        # Offline / GUI plan preview: keep schema keys, no network probes.
        ollama_version = None
        model_metadata = None

    selected_pairs = sorted({item["pair_id"] for item in design})
    scenario_files = sorted({item["scenario_file"] for item in design})

    design_cells = [
        {
            "pair_id": item["pair_id"],
            "condition": item["condition"],
            "scenario_file": item["scenario_file"],
            "cell_index": item["cell"]["cell_index"],
            "cell_key": item["cell"]["cell_key"],
            "active_language_factors": item["cell"]["active_language_factors"],
            "active_language_assignment": item["cell"]["active_language_assignment"],
            "language_assignment": item["cell"]["language_assignment"],
        }
        for item in design
    ]

    provenance = {
        "timestamp_utc": generated_at,
        "git": {
            "commit": git_commit,
            "dirty": git_dirty,
        },
        "ollama": {
            "version": ollama_version,
            "endpoint": OLLAMA_BASE_URL,
        },
        "model": model_metadata,
        "experiment": {
            "temperature": args.temperature,
            "num_predict": args.num_predict,
            "request_timeout_seconds": args.request_timeout,
            "max_turns": MAX_TURNS,
            "seed_base": args.seed_base,
            "repeats": args.repeats,
            "protected_conditions": protected_conditions,
            "selected_pairs": selected_pairs,
            "scenario_files": scenario_files,
            "unique_design_cells": len(design),
            "expected_episodes": expected_episodes,
            "design_cells": design_cells,
        },
    }

    # Retain flat top-level fields for older analysis scripts.
    return {
        "benchmark": "LangTrust",
        "model": model_name,
        "temperature": args.temperature,
        "num_predict": args.num_predict,
        "request_timeout_seconds": args.request_timeout,
        "max_turns": MAX_TURNS,
        "seed_base": args.seed_base,
        "repeats": args.repeats,
        "protected_conditions": protected_conditions,
        "unique_design_cells": len(design),
        "expected_episodes": expected_episodes,
        "git_commit": git_commit,
        "git_dirty": git_dirty,
        "generated_at": generated_at,
        "provenance": provenance,
    }


def get_conditions(value):
    if value == "attack":
        return ["attack"]
    if value == "benign":
        return ["benign"]
    return ["attack", "benign"]


def get_protected_conditions(value):
    if value == "false":
        return [False]
    if value == "true":
        return [True]
    return [False, True]


def save_results(path, metadata, results):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"metadata": metadata, "results": results}, f, indent=2, ensure_ascii=False)


def select_pairs(all_pairs, requested_pairs):
    if not requested_pairs:
        return all_pairs

    requested = set(requested_pairs)
    unknown = requested - set(all_pairs)
    if unknown:
        raise ValueError("Unknown benchmark pair(s): " + ", ".join(sorted(unknown)))

    return {pair_id: all_pairs[pair_id] for pair_id in sorted(requested)}


def select_cells(cells, requested_cells):
    if not requested_cells:
        return cells

    requested = set(requested_cells)
    selected = [cell for cell in cells if cell["cell_index"] in requested]

    found = {cell["cell_index"] for cell in selected}
    missing = requested - found
    if missing:
        raise ValueError(
            "Requested cell index does not exist in this scenario: "
            + ", ".join(str(value) for value in sorted(missing))
        )

    return selected


def build_design(pairs, conditions, requested_cells):
    design = []

    for pair_id, pair in sorted(pairs.items()):
        for condition in conditions:
            scenario = pair[condition]
            benchmark = scenario["benchmark"]

            cells = generate_language_cells(scenario)
            cells = select_cells(cells, requested_cells)

            for cell in cells:
                design.append(
                    {
                        "pair_id": pair_id,
                        "domain": benchmark["domain"],
                        "condition": condition,
                        "scenario": scenario,
                        "scenario_file": scenario["_scenario_file"],
                        "cell": cell,
                    }
                )

    return design


def build_episode_record(
    item,
    repeat,
    seed,
    args,
    protected,
    result,
    evaluation,
):
    cell = item["cell"]

    return {
        "pair_id": item["pair_id"],
        "domain": item["domain"],
        "condition": item["condition"],
        "scenario": item["scenario"]["id"],
        "scenario_file": item["scenario_file"],
        "cell_index": cell["cell_index"],
        "cell_key": cell["cell_key"],
        "active_language_factors": cell["active_language_factors"],
        "active_language_assignment": cell["active_language_assignment"],
        "language_assignment": cell["language_assignment"],
        "inactive_language": cell["inactive_language"],
        "repeat": repeat,
        "seed": seed,
        "temperature": args.temperature,
        "num_predict": args.num_predict,
        "request_timeout_seconds": args.request_timeout,
        "protected_prompt": protected,
        "completed": result.completed,
        "inference": {
            "success": result.inference_success,
            "truncated": result.inference_truncated,
            "failure_type": result.inference_failure_type,
            "error": result.inference_error,
            "calls": result.inference_calls,
        },
        "turns": result.turns,
        "answer": result.answer,
        "events": result.events,
        "blocked_attempts": result.blocked_attempts,
        "initial_state": result.initial_state,
        "final_state": result.final_state,
        "evaluation": evaluation,
    }


def list_benchmark_pair_ids(scenario_dir=None) -> list[str]:
    """Return sorted benchmark pair ids (application-layer wrapper)."""
    return sorted(group_benchmark_pairs(scenario_dir))


def build_benchmark_plan(
    config: BenchmarkRunConfig,
    *,
    scenario_dir=None,
    git_repo=None,
    collect_runtime_metadata: bool = True,
) -> BenchmarkPlan:
    validate_config(config)

    all_pairs = group_benchmark_pairs(scenario_dir)
    pairs = select_pairs(all_pairs, config.pairs)
    conditions = get_conditions(config.condition)
    protected_conditions = get_protected_conditions(config.protected)

    design = build_design(pairs, conditions, config.cells)
    expected_episodes = len(design) * config.repeats * len(protected_conditions)
    metadata = build_metadata(
        config,
        design,
        protected_conditions,
        expected_episodes,
        git_repo=git_repo,
        collect_runtime_metadata=collect_runtime_metadata,
    )

    return BenchmarkPlan(
        design=design,
        protected_conditions=protected_conditions,
        expected_episodes=expected_episodes,
        metadata=metadata,
        pairs=pairs,
    )


def _default_agent_factory(*, protected, seed, config):
    return OllamaToolAgent(
        protected=protected,
        model=config.model,
        temperature=config.temperature,
        seed=seed,
        num_predict=config.num_predict,
        request_timeout=config.request_timeout,
        max_turns=MAX_TURNS,
        debug=config.debug,
    )


def _emit(on_event, event):
    if on_event is None:
        return
    try:
        snapshot = copy.deepcopy(event)
    except Exception:
        return
    try:
        on_event(snapshot)
    except Exception:
        pass


def run_benchmark(
    config: BenchmarkRunConfig,
    *,
    scenario_dir=None,
    git_repo=None,
    on_event=None,
    agent_factory=None,
    plan: BenchmarkPlan | None = None,
) -> BenchmarkRunResult:
    validate_config(config)

    if plan is None:
        plan = build_benchmark_plan(
            config,
            scenario_dir=scenario_dir,
            git_repo=git_repo,
        )

    output_path = Path(config.output)

    if config.dry_run:
        _emit(
            on_event,
            {
                "type": "plan_ready",
                "expected_episodes": plan.expected_episodes,
                "protected_conditions": plan.protected_conditions,
            },
        )
        return BenchmarkRunResult(
            metadata=plan.metadata,
            results=[],
            output_path=output_path,
            expected_episodes=plan.expected_episodes,
        )

    if agent_factory is None:
        agent_factory = _default_agent_factory

    evaluator = StatefulEvaluator()

    results = []
    episode_number = 0

    for repeat in range(1, config.repeats + 1):
        seed = config.seed_base + repeat - 1

        for item in plan.design:
            pair_id = item["pair_id"]
            condition = item["condition"]
            scenario = item["scenario"]
            cell = item["cell"]
            language_assignment = cell["language_assignment"]

            for protected in plan.protected_conditions:
                episode_number += 1

                _emit(
                    on_event,
                    {
                        "type": "episode_start",
                        "episode_number": episode_number,
                        "expected_episodes": plan.expected_episodes,
                        "pair_id": pair_id,
                        "condition": condition,
                        "cell_index": cell["cell_index"],
                        "seed": seed,
                        "protected": protected,
                        "item": item,
                        "repeat": repeat,
                    },
                )

                agent = agent_factory(
                    protected=protected,
                    seed=seed,
                    config=config,
                )
                result = agent.run(language_assignment, scenario)

                if result.inference_success:
                    evaluation = evaluator.evaluate(result, scenario)
                    evaluation_dict = evaluation.to_dict()
                else:
                    evaluation_dict = None

                record = build_episode_record(
                    item=item,
                    repeat=repeat,
                    seed=seed,
                    args=config,
                    protected=protected,
                    result=result,
                    evaluation=evaluation_dict,
                )

                results.append(record)
                save_results(output_path, plan.metadata, results)

                _emit(
                    on_event,
                    {
                        "type": "episode_complete",
                        "episode_number": episode_number,
                        "expected_episodes": plan.expected_episodes,
                        "item": item,
                        "scenario": scenario,
                        "result": result,
                        "evaluation": evaluation_dict,
                        "record": record,
                        "repeat": repeat,
                        "seed": seed,
                        "protected": protected,
                    },
                )

    save_results(output_path, plan.metadata, results)

    return BenchmarkRunResult(
        metadata=plan.metadata,
        results=results,
        output_path=output_path,
        expected_episodes=plan.expected_episodes,
    )
