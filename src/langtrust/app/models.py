"""Benchmark run configuration and result models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class BenchmarkRunConfig:
    pairs: Sequence[str] | None = None
    condition: str = "both"
    protected: str = "both"
    cells: Sequence[int] | None = None
    repeats: int = 1
    temperature: float = 0.0
    num_predict: int = 1024
    request_timeout: float = 120
    seed_base: int = 1000
    output: str = "results/langtrust_benchmark.json"
    dry_run: bool = False
    debug: bool = False
    model: str = "qwen2.5:14b"


@dataclass(frozen=True)
class BenchmarkPlan:
    design: list[dict[str, Any]]
    protected_conditions: list[bool]
    expected_episodes: int
    metadata: dict[str, Any]
    pairs: Mapping[str, Any]


@dataclass(frozen=True)
class BenchmarkRunResult:
    metadata: dict[str, Any]
    results: list[dict[str, Any]]
    output_path: Path
    expected_episodes: int


def config_from_namespace(args) -> BenchmarkRunConfig:
    return BenchmarkRunConfig(
        pairs=getattr(args, "pairs", None),
        condition=getattr(args, "condition", "both"),
        protected=getattr(args, "protected", "both"),
        cells=getattr(args, "cells", None),
        repeats=getattr(args, "repeats", 1),
        temperature=getattr(args, "temperature", 0.0),
        num_predict=getattr(args, "num_predict", 1024),
        request_timeout=getattr(args, "request_timeout", 120),
        seed_base=getattr(args, "seed_base", 1000),
        output=getattr(args, "output", "results/langtrust_benchmark.json"),
        dry_run=bool(getattr(args, "dry_run", False)),
        debug=bool(getattr(args, "debug", False)),
        model=getattr(args, "model", "qwen2.5:14b"),
    )


def validate_config(config) -> None:
    condition = getattr(config, "condition", "both")
    protected = getattr(config, "protected", "both")

    if condition not in {"both", "attack", "benign"}:
        raise ValueError(
            "--condition must be one of: both, attack, benign"
        )
    if protected not in {"both", "false", "true"}:
        raise ValueError(
            "--protected must be one of: both, false, true"
        )
    if config.repeats < 1:
        raise ValueError("--repeats must be >= 1")
    if config.num_predict < 1:
        raise ValueError("--num-predict must be >= 1")
    if config.request_timeout <= 0:
        raise ValueError("--request-timeout must be > 0")

    model = getattr(config, "model", "qwen2.5:14b")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("--model must be a non-empty string")
