"""Tk-independent offline helpers for the LangTrust GUI.

These helpers call the G9C1 application layer and local filesystem only.
They must not perform model inference or require a live Ollama service.
"""

from __future__ import annotations

import json
from importlib import metadata, resources
from pathlib import Path
from typing import Any

from langtrust.app.benchmark import MODEL, build_benchmark_plan, list_benchmark_pair_ids
from langtrust.app.models import BenchmarkRunConfig, validate_config

DOC_CANDIDATES = (
    "README.md",
    "ARTIFACTS.md",
    "PROVENANCE.md",
    "REPRODUCIBILITY.md",
    "CITATION.cff",
    "SHA256SUMS",
)

PACKAGED_DOC_PREFIX = "package://langtrust.resources/docs/"

OVERVIEW_TEXT = """LangTrust provides a controlled Polish–English security evaluation framework for tool-using LLM agents under indirect prompt injection.

The GUI provides both offline inspection/planning tools and an optional Live Run interface.

Offline tools:
- browse scenarios and configuration;
- preview a DRY-RUN benchmark plan (no model inference);
- inspect existing result JSON;
- open local documentation when present.

Live Run performs actual model inference through the configured LangTrust application/backend stack. Consequential tool effects remain confined to the LangTrust sandbox and do not invoke real external e-mail, calendar, or filesystem services.

Metric reminders:
- unauthorized native tool request (UTRR-relevant) is not the same as unauthorized execution;
- security success is not task success;
- authorized execution is not necessarily correct consequential action;
- baseline still uses runtime ToolPolicyEngine; protected adds fixed English SECURITY RULES (not language-matched).
"""


def package_version() -> str:
    try:
        return metadata.version("langtrust")
    except metadata.PackageNotFoundError:
        return "0.2.0"


def list_pair_ids(scenario_dir: str | Path | None = None) -> list[str]:
    return list_benchmark_pair_ids(scenario_dir)


def make_config(
    *,
    pairs: list[str] | None = None,
    condition: str = "both",
    protected: str = "both",
    cells: list[int] | None = None,
    repeats: int = 1,
    temperature: float = 0.0,
    num_predict: int = 1024,
    request_timeout: float = 120,
    seed_base: int = 1000,
    output: str = "results/langtrust_benchmark.json",
    model: str = MODEL,
) -> BenchmarkRunConfig:
    config = BenchmarkRunConfig(
        pairs=pairs,
        condition=condition,
        protected=protected,
        cells=cells,
        repeats=repeats,
        temperature=temperature,
        num_predict=num_predict,
        request_timeout=request_timeout,
        seed_base=seed_base,
        output=output,
        dry_run=True,
        debug=False,
        model=model,
    )
    validate_config(config)
    return config


def preview_plan(
    config: BenchmarkRunConfig,
    *,
    scenario_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Build an offline dry-run plan summary via langtrust.app (no inference)."""
    if not config.dry_run:
        # GUI planning always uses dry_run semantics; force safety.
        config = BenchmarkRunConfig(
            pairs=config.pairs,
            condition=config.condition,
            protected=config.protected,
            cells=config.cells,
            repeats=config.repeats,
            temperature=config.temperature,
            num_predict=config.num_predict,
            request_timeout=config.request_timeout,
            seed_base=config.seed_base,
            output=config.output,
            dry_run=True,
            debug=config.debug,
            model=config.model,
        )
    validate_config(config)
    plan = build_benchmark_plan(
        config,
        scenario_dir=scenario_dir,
        git_repo=None,
        collect_runtime_metadata=False,
    )
    design_summary: list[dict[str, Any]] = []
    for item in plan.design:
        cell = item["cell"]
        design_summary.append(
            {
                "pair_id": item["pair_id"],
                "domain": item["domain"],
                "condition": item["condition"],
                "scenario": item["scenario"]["id"],
                "scenario_file": item["scenario_file"],
                "cell_index": cell["cell_index"],
                "cell_key": cell["cell_key"],
                "language_assignment": cell["language_assignment"],
            }
        )
    return {
        "mode": "DRY RUN / PLAN PREVIEW",
        "inference": False,
        "selected_pairs": sorted(plan.pairs),
        "protected_conditions": list(plan.protected_conditions),
        "expected_episodes": plan.expected_episodes,
        "unique_design_cells": len(plan.design),
        "design": design_summary,
        "config": {
            "condition": config.condition,
            "protected": config.protected,
            "repeats": config.repeats,
            "temperature": config.temperature,
            "num_predict": config.num_predict,
            "request_timeout": config.request_timeout,
            "seed_base": config.seed_base,
            "dry_run": True,
            "model": config.model,
        },
        "metadata": {
            "benchmark": plan.metadata.get("benchmark"),
            "model": plan.metadata.get("model"),
            "temperature": plan.metadata.get("temperature"),
            "num_predict": plan.metadata.get("num_predict"),
            "request_timeout_seconds": plan.metadata.get("request_timeout_seconds"),
            "max_turns": plan.metadata.get("max_turns"),
            "seed_base": plan.metadata.get("seed_base"),
            "repeats": plan.metadata.get("repeats"),
            "protected_conditions": plan.metadata.get("protected_conditions"),
            "unique_design_cells": plan.metadata.get("unique_design_cells"),
            "expected_episodes": plan.metadata.get("expected_episodes"),
            "generated_at": plan.metadata.get("generated_at"),
        },
    }


def inspect_result_json(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Result file not found: {path}")
    try:
        raw = path.read_text(encoding="utf-8-sig")
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Unsupported result JSON: expected a top-level object")

    metadata = data.get("metadata")
    results = data.get("results")
    if results is None:
        raise ValueError("Unsupported result JSON: missing 'results' list")
    if not isinstance(results, list):
        raise ValueError("Unsupported result JSON: 'results' must be a list")

    record_summaries = []
    for index, record in enumerate(results):
        if not isinstance(record, dict):
            record_summaries.append({"index": index, "error": "non-object record"})
            continue
        inference = record.get("inference") or {}
        evaluation = record.get("evaluation")
        security = (evaluation or {}).get("security") if isinstance(evaluation, dict) else None
        utility = (evaluation or {}).get("utility") if isinstance(evaluation, dict) else None
        calls = inference.get("calls") if isinstance(inference, dict) else None
        done_reasons = []
        if isinstance(calls, list):
            for call in calls:
                if isinstance(call, dict) and call.get("done_reason") is not None:
                    done_reasons.append(call.get("done_reason"))
        record_summaries.append(
            {
                "index": index,
                "pair_id": record.get("pair_id"),
                "domain": record.get("domain"),
                "condition": record.get("condition"),
                "scenario": record.get("scenario"),
                "cell_index": record.get("cell_index"),
                "seed": record.get("seed"),
                "protected_prompt": record.get("protected_prompt"),
                "inference_success": inference.get("success") if isinstance(inference, dict) else None,
                "inference_failure_type": inference.get("failure_type") if isinstance(inference, dict) else None,
                "done_reasons": done_reasons,
                "unauthorized_tool_attempt": (security or {}).get("unauthorized_tool_attempt") if security else None,
                "unauthorized_execution": (security or {}).get("unauthorized_execution") if security else None,
                "task_success": (utility or {}).get("task_success") if utility else None,
                "answer": record.get("answer"),
            }
        )

    return {
        "path": str(path),
        "metadata": metadata if isinstance(metadata, dict) else metadata,
        "record_count": len(results),
        "records": record_summaries,
    }


def _find_repository_root(start: Path) -> Path | None:
    """Return a LangTrust repository root containing the source tree."""
    start = start.resolve()

    if start.is_file():
        start = start.parent

    for candidate in (start, *start.parents):
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "CITATION.cff").is_file()
            and (candidate / "src/langtrust/gui/offline.py").is_file()
        ):
            return candidate

    return None


def find_documentation(
    search_roots: list[str | Path] | None = None,
) -> dict[str, str | None]:
    """Locate repository docs, with packaged docs as the install fallback."""
    roots: list[Path] = []

    if search_roots:
        roots.extend(Path(p) for p in search_roots)
    else:
        for candidate in (
            _find_repository_root(Path.cwd()),
            _find_repository_root(Path(__file__)),
        ):
            if candidate is not None and candidate not in roots:
                roots.append(candidate)

    found: dict[str, str | None] = {
        name: None for name in DOC_CANDIDATES
    }

    for root in roots:
        for name in DOC_CANDIDATES:
            if found[name] is not None:
                continue

            candidate = root / name
            if candidate.is_file():
                found[name] = str(candidate)

    if search_roots is None:
        packaged_root = resources.files(
            "langtrust.resources"
        ).joinpath("docs")

        for name in DOC_CANDIDATES:
            if found[name] is not None:
                continue

            candidate = packaged_root.joinpath(name)
            if candidate.is_file():
                found[name] = PACKAGED_DOC_PREFIX + name

    return found

def read_text_file(path: str | Path, *, max_chars: int = 200_000) -> str:
    path_text = str(path)

    if path_text.startswith(PACKAGED_DOC_PREFIX):
        name = path_text.removeprefix(PACKAGED_DOC_PREFIX)

        if name not in DOC_CANDIDATES:
            raise FileNotFoundError(
                f"Unknown packaged documentation file: {name}"
            )

        resource = (
            resources.files("langtrust.resources")
            .joinpath("docs")
            .joinpath(name)
        )

        if not resource.is_file():
            raise FileNotFoundError(
                f"Packaged documentation file not found: {name}"
            )

        text = resource.read_text(encoding="utf-8")
    else:
        disk_path = Path(path)

        if not disk_path.is_file():
            raise FileNotFoundError(f"File not found: {disk_path}")

        text = disk_path.read_text(encoding="utf-8")

    if len(text) > max_chars:
        return text[:max_chars] + "\n\n[truncated]"

    return text
