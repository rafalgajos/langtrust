"""Tk-independent Live Run controller for the LangTrust GUI (G9C3).

Orchestrates langtrust.app only. Does not import Tkinter or scientific core.
"""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from langtrust.app import (
    MODEL,
    OLLAMA_BASE_URL,
    BenchmarkPlan,
    BenchmarkRunConfig,
    BenchmarkRunResult,
    build_benchmark_plan,
    check_ollama_model_tool_compatibility,
    run_benchmark,
    validate_config,
)

DEFAULT_LIVE_OUTPUT = "results/langtrust_gui_live.json"

LIVE_RUN_WARNING = (
    "Live Run performs actual model inference.\n"
    "The configured local Ollama backend will be contacted.\n"
    "Result JSON will be written to disk.\n"
    "Consequential tool effects remain inside LangTrust's sandbox — "
    "this does not send real e-mail, modify real calendars, or manipulate "
    "the user's real filesystem through LangTrust tools.\n"
    "Hard cancellation is not available in this version."
)

CLOSE_WHILE_RUNNING_MESSAGE = """A Live Run is still active.

Hard cancellation is not supported in this version.
Closing the window would terminate the process and interrupt the benchmark, so the window will stay open.

Please wait until the run completes or fails."""


def may_close_window(*, is_running: bool) -> bool:
    """Return True if the Tk root may be destroyed.

    Closing while a Live Run is active would kill a daemon worker and act as
    hard cancellation, which G9C3 explicitly does not implement.
    """
    return not bool(is_running)


AUTHORITATIVE_RESULT_BASENAMES = frozenset(
    {
        "langtrust_3domains_t0_n1_bounded_run2.json",
        "langtrust_3domains_t02_n5.json",
        "invoice_attack_protected_t02_n20.json",
    }
)


@dataclass(frozen=True)
class LiveReadOnlyBackendInfo:
    model: str
    endpoint: str


def backend_info() -> LiveReadOnlyBackendInfo:
    return LiveReadOnlyBackendInfo(model=MODEL, endpoint=OLLAMA_BASE_URL)


def make_live_config(
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
    output: str = DEFAULT_LIVE_OUTPUT,
    debug: bool = False,
    model: str = MODEL,
) -> BenchmarkRunConfig:
    """Build a Live Run config (dry_run=False) validated by langtrust.app."""
    basename = Path(output).name
    if basename in AUTHORITATIVE_RESULT_BASENAMES:
        raise ValueError(
            f"Refusing Live Run output that targets authoritative artifact: {basename}"
        )
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
        dry_run=False,
        debug=debug,
        model=model,
    )
    validate_config(config)
    return config


def normalize_app_event(event: dict[str, Any]) -> dict[str, Any]:
    """Extract display-oriented fields without inventing metrics."""
    etype = event.get("type")
    summary: dict[str, Any] = {"type": etype}
    for key in (
        "episode_number",
        "expected_episodes",
        "pair_id",
        "condition",
        "cell_index",
        "seed",
        "protected",
        "repeat",
        "scenario",
    ):
        if key in event:
            summary[key] = event[key]

    item = event.get("item")
    if isinstance(item, dict):
        summary.setdefault("pair_id", item.get("pair_id"))
        summary.setdefault("condition", item.get("condition"))
        cell = item.get("cell")
        if isinstance(cell, dict):
            summary.setdefault("cell_index", cell.get("cell_index"))

    record = event.get("record")
    if isinstance(record, dict):
        summary.setdefault("pair_id", record.get("pair_id"))
        summary.setdefault("condition", record.get("condition"))
        summary.setdefault("cell_index", record.get("cell_index"))
        summary.setdefault("seed", record.get("seed"))
        summary.setdefault("protected", record.get("protected_prompt"))
        summary.setdefault("repeat", record.get("repeat"))
        inference = record.get("inference") or {}
        if isinstance(inference, dict):
            summary["inference_success"] = inference.get("success")
            summary["inference_failure_type"] = inference.get("failure_type")
            calls = inference.get("calls")
            if isinstance(calls, list):
                summary["done_reasons"] = [
                    c.get("done_reason")
                    for c in calls
                    if isinstance(c, dict) and c.get("done_reason") is not None
                ]
        evaluation = record.get("evaluation") or {}
        if isinstance(evaluation, dict):
            security = evaluation.get("security") or {}
            utility = evaluation.get("utility") or {}
            if isinstance(security, dict):
                summary["unauthorized_tool_attempt"] = security.get(
                    "unauthorized_tool_attempt"
                )
                summary["unauthorized_execution"] = security.get(
                    "unauthorized_execution"
                )
            if isinstance(utility, dict):
                summary["task_success"] = utility.get("task_success")
    return summary


class LiveRunController:
    """Worker-thread Live Run orchestrator (Tk-independent)."""

    def __init__(
        self,
        *,
        build_plan: Callable[..., BenchmarkPlan] = build_benchmark_plan,
        run: Callable[..., BenchmarkRunResult] = run_benchmark,
        check_model_compat: Callable[..., Any] = check_ollama_model_tool_compatibility,
        scenario_dir=None,
        git_repo=None,
    ) -> None:
        self._build_plan = build_plan
        self._run = run
        self._check_model_compat = check_model_compat
        self._scenario_dir = scenario_dir
        self._git_repo = git_repo
        self.messages: queue.Queue = queue.Queue()
        self._running = False
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def start(self, config: BenchmarkRunConfig) -> None:
        if config.dry_run:
            raise ValueError("Live Run requires dry_run=False")
        validate_config(config)
        with self._lock:
            if self._running:
                raise RuntimeError("A Live Run is already in progress")
            self._running = True
        try:
            self._thread = threading.Thread(
                target=self._worker,
                args=(config,),
                name="langtrust-gui-live-run",
                daemon=True,
            )
            self._thread.start()
        except Exception:
            with self._lock:
                self._running = False
                self._thread = None
            raise

    def _emit(self, message: dict[str, Any]) -> None:
        self.messages.put(message)

    def _worker(self, config: BenchmarkRunConfig) -> None:
        self._emit({"type": "worker_started", "output": config.output})
        plan = None
        try:
            model = config.model
            self._emit({"type": "compat_check_started", "model": model})
            self._check_model_compat(model)  # may raise ModelCompatibilityError
            self._emit({"type": "compat_check_passed", "model": model})
            plan = self._build_plan(
                config,
                scenario_dir=self._scenario_dir,
                git_repo=self._git_repo,
            )
            self._emit(
                {
                    "type": "plan_ready",
                    "expected_episodes": plan.expected_episodes,
                    "protected_conditions": list(plan.protected_conditions),
                    "selected_pairs": sorted(plan.pairs),
                }
            )

            def on_event(event):
                payload = event if isinstance(event, dict) else {"raw": event}
                self._emit(
                    {
                        "type": "app_event",
                        "event": payload,
                        "display": normalize_app_event(payload)
                        if isinstance(payload, dict)
                        else {},
                    }
                )

            result = self._run(
                config,
                scenario_dir=self._scenario_dir,
                git_repo=self._git_repo,
                on_event=on_event,
                plan=plan,
            )
            self._emit(
                {
                    "type": "worker_complete",
                    "output_path": str(result.output_path),
                    "result_count": len(result.results),
                    "expected_episodes": result.expected_episodes,
                }
            )
        except Exception as exc:  # noqa: BLE001 - surface to UI
            self._emit(
                {
                    "type": "worker_error",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "plan_built": plan is not None,
                }
            )
        finally:
            with self._lock:
                self._running = False


def drain_queue(q: queue.Queue, *, max_items: int = 1000) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for _ in range(max_items):
        try:
            items.append(q.get_nowait())
        except queue.Empty:
            break
    return items
