"""Headless Live Run GUI controller tests without Tk or inference-core access."""

from __future__ import annotations

import ast
import inspect
import threading
import time
from pathlib import Path

import pytest

from langtrust.app import BenchmarkPlan, BenchmarkRunConfig, BenchmarkRunResult
from langtrust.app import ModelCompatibilityError
from langtrust.gui.live import (
    AUTHORITATIVE_RESULT_BASENAMES,
    DEFAULT_LIVE_OUTPUT,
    LiveRunController,
    drain_queue,
    make_live_config,
    normalize_app_event,
)


def _pass_compat(model):
    """No-op Live Run preflight for unit tests (never contacts Ollama)."""
    return None


def _wait_for(predicate, timeout=2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    raise AssertionError("timed out waiting for condition")


def test_make_live_config_defaults_and_validation():
    config = make_live_config(pairs=["invoice_email_001"], condition="attack", protected="true")
    assert isinstance(config, BenchmarkRunConfig)
    assert config.dry_run is False
    assert config.output == DEFAULT_LIVE_OUTPUT
    assert Path(config.output).name not in AUTHORITATIVE_RESULT_BASENAMES
    assert config.condition == "attack"
    assert config.protected == "true"
    assert config.repeats == 1
    assert config.model == "qwen2.5:14b"

    with pytest.raises(ValueError, match="condition"):
        make_live_config(condition="maybe")
    with pytest.raises(ValueError, match="authoritative"):
        make_live_config(output="results/langtrust_3domains_t0_n1_bounded_run2.json")
    with pytest.raises(ValueError, match="--model must be a non-empty string"):
        make_live_config(model="")
    with pytest.raises(ValueError, match="--model must be a non-empty string"):
        make_live_config(model="   ")


def test_live_module_has_no_direct_core_imports():
    live_path = Path(__file__).resolve().parents[1] / "src" / "langtrust" / "gui" / "live.py"
    tree = ast.parse(live_path.read_text(encoding="utf-8"))
    banned_prefixes = (
        "langtrust.agent",
        "langtrust.backend",
        "langtrust.environment",
        "langtrust.evaluation",
        "langtrust.benchmark",
    )
    banned_names = {
        "OllamaBackend",
        "QwenBackend",
        "OllamaToolAgent",
        "QwenToolAgent",
        "StatefulEvaluator",
        "StatefulSandbox",
        "ToolPolicyEngine",
        "tkinter",
    }
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            imported.append(mod)
            for alias in node.names:
                imported.append(alias.name)
    for name in imported:
        assert name not in banned_names, name
        assert not any(name == p or name.startswith(p + ".") for p in banned_prefixes), name
    assert any(n == "langtrust.app" or n.startswith("langtrust.app") for n in imported)


def test_single_plan_object_passed_to_run_benchmark():
    plans = []
    runs = []

    fake_plan = BenchmarkPlan(
        design=[{"pair_id": "x"}],
        protected_conditions=[True],
        expected_episodes=1,
        metadata={"benchmark": "LangTrust"},
        pairs={"x": {}},
    )

    def fake_build(config, *, scenario_dir=None, git_repo=None, **kwargs):
        plans.append({"config": config, "kwargs": kwargs})
        assert "collect_runtime_metadata" not in kwargs or kwargs.get(
            "collect_runtime_metadata", True
        ) is True
        assert kwargs.get("collect_runtime_metadata", True) is not False
        return fake_plan

    def fake_run(config, *, scenario_dir=None, git_repo=None, on_event=None, plan=None, **kwargs):
        runs.append({"plan": plan, "on_event": on_event})
        assert plan is fake_plan
        return BenchmarkRunResult(
            metadata=plan.metadata,
            results=[{"ok": True}],
            output_path=Path(config.output),
            expected_episodes=plan.expected_episodes,
        )

    controller = LiveRunController(build_plan=fake_build, run=fake_run, check_model_compat=_pass_compat)
    config = make_live_config(pairs=["invoice_email_001"], output="results/tmp_gui_live.json")
    controller.start(config)
    _wait_for(lambda: not controller.is_running)
    msgs = drain_queue(controller.messages)
    types = [m["type"] for m in msgs]
    assert types.count("worker_started") == 1
    assert types.count("plan_ready") == 1
    assert types.count("worker_complete") == 1
    assert len(plans) == 1
    assert len(runs) == 1
    assert runs[0]["plan"] is fake_plan
    complete = next(m for m in msgs if m["type"] == "worker_complete")
    assert complete["result_count"] == 1
    assert complete["output_path"].endswith("tmp_gui_live.json")


def test_event_forwarding_through_queue():
    fake_plan = BenchmarkPlan(
        design=[],
        protected_conditions=[False],
        expected_episodes=2,
        metadata={},
        pairs={},
    )

    def fake_build(config, **kwargs):
        return fake_plan

    def fake_run(config, *, on_event=None, plan=None, **kwargs):
        on_event(
            {
                "type": "episode_start",
                "episode_number": 1,
                "expected_episodes": 2,
                "pair_id": "invoice_email_001",
                "condition": "attack",
                "cell_index": 0,
                "seed": 1000,
                "protected": True,
                "repeat": 1,
            }
        )
        on_event(
            {
                "type": "episode_complete",
                "episode_number": 1,
                "expected_episodes": 2,
                "record": {
                    "pair_id": "invoice_email_001",
                    "condition": "attack",
                    "cell_index": 0,
                    "seed": 1000,
                    "protected_prompt": True,
                    "repeat": 1,
                    "inference": {"success": True, "calls": [{"done_reason": "stop"}]},
                    "evaluation": {
                        "security": {
                            "unauthorized_tool_attempt": False,
                            "unauthorized_execution": False,
                        },
                        "utility": {"task_success": True},
                    },
                },
            }
        )
        return BenchmarkRunResult(
            metadata={},
            results=[{}],
            output_path=Path(config.output),
            expected_episodes=2,
        )

    controller = LiveRunController(build_plan=fake_build, run=fake_run, check_model_compat=_pass_compat)
    controller.start(make_live_config(output="results/tmp_gui_live.json"))
    _wait_for(lambda: not controller.is_running)
    msgs = drain_queue(controller.messages)
    app_events = [m for m in msgs if m["type"] == "app_event"]
    assert len(app_events) == 2
    assert app_events[0]["event"]["type"] == "episode_start"
    assert app_events[1]["display"]["inference_success"] is True
    assert app_events[1]["display"]["done_reasons"] == ["stop"]
    # original event semantics preserved
    assert app_events[1]["event"]["record"]["evaluation"]["utility"]["task_success"] is True


def test_build_plan_failure_surfaces_and_skips_run():
    def boom_build(*args, **kwargs):
        raise RuntimeError("plan failed")

    def boom_run(*args, **kwargs):
        raise AssertionError("run_benchmark must not be called")

    controller = LiveRunController(build_plan=boom_build, run=boom_run, check_model_compat=_pass_compat)
    controller.start(make_live_config(output="results/tmp_gui_live.json"))
    _wait_for(lambda: not controller.is_running)
    msgs = drain_queue(controller.messages)
    assert any(m["type"] == "worker_error" and m["error_type"] == "RuntimeError" for m in msgs)
    assert not any(m["type"] == "worker_complete" for m in msgs)


def test_run_benchmark_failure_surfaces():
    fake_plan = BenchmarkPlan(
        design=[], protected_conditions=[], expected_episodes=0, metadata={}, pairs={}
    )

    def fake_build(*args, **kwargs):
        return fake_plan

    def boom_run(*args, **kwargs):
        raise ValueError("inference blew up")

    controller = LiveRunController(build_plan=fake_build, run=boom_run, check_model_compat=_pass_compat)
    controller.start(make_live_config(output="results/tmp_gui_live.json"))
    _wait_for(lambda: not controller.is_running)
    msgs = drain_queue(controller.messages)
    err = next(m for m in msgs if m["type"] == "worker_error")
    assert err["error_type"] == "ValueError"
    assert "inference blew up" in err["error"]
    assert err["plan_built"] is True


def test_no_double_start():
    started = threading.Event()
    release = threading.Event()

    fake_plan = BenchmarkPlan(
        design=[], protected_conditions=[], expected_episodes=1, metadata={}, pairs={}
    )

    def fake_build(*args, **kwargs):
        return fake_plan

    def slow_run(*args, **kwargs):
        started.set()
        release.wait(timeout=2)
        return BenchmarkRunResult(
            metadata={},
            results=[],
            output_path=Path("results/tmp_gui_live.json"),
            expected_episodes=1,
        )

    controller = LiveRunController(build_plan=fake_build, run=slow_run, check_model_compat=_pass_compat)
    config = make_live_config(output="results/tmp_gui_live.json")
    controller.start(config)
    _wait_for(started.is_set)
    with pytest.raises(RuntimeError, match="already in progress"):
        controller.start(config)
    release.set()
    _wait_for(lambda: not controller.is_running)


def test_controller_uses_only_injected_app_callables():
    """Production LiveRunController stores injected build/run callables only.

    Architectural guarantee: the worker invokes self._build_plan / self._run,
    not langtrust.agent / backend / Ollama helpers. Unit tests inject fakes so
    no real inference or localhost:11434 contact occurs.
    """
    import langtrust.gui.live as live_mod

    src = inspect.getsource(LiveRunController._worker)
    assert "self._build_plan(" in src
    assert "self._run(" in src
    assert "self._check_model_compat(" in src
    # Must not hard-call module-level run_benchmark/build_benchmark_plan inside worker
    # (defaults are injected at __init__; worker uses the instance callables).
    assert "build_benchmark_plan(" not in src.replace("self._build_plan(", "")
    assert "run_benchmark(" not in src.replace("self._run(", "")
    assert "check_ollama_model_tool_compatibility(" not in src.replace(
        "self._check_model_compat(", ""
    )

    # Source-level: live module must not import core inference stack.
    live_path = Path(live_mod.__file__)
    tree = ast.parse(live_path.read_text(encoding="utf-8"))
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            names.append(node.module or "")
            names.extend(a.name for a in node.names)
        elif isinstance(node, ast.Import):
            names.extend(a.name for a in node.names)
    banned = {
        "langtrust.agent",
        "langtrust.backend",
        "OllamaBackend",
        "QwenBackend",
        "OllamaToolAgent",
        "QwenToolAgent",
        "requests",
        "urllib",
        "socket",
        "httpx",
    }
    for name in names:
        assert name not in banned
        assert not any(name.startswith(b + ".") for b in banned if "." in b)

    calls = {"build": 0, "run": 0}

    def fake_build(*args, **kwargs):
        calls["build"] += 1
        return BenchmarkPlan(
            design=[], protected_conditions=[], expected_episodes=0, metadata={}, pairs={}
        )

    def fake_run(*args, **kwargs):
        calls["run"] += 1
        return BenchmarkRunResult(
            metadata={},
            results=[],
            output_path=Path("results/x.json"),
            expected_episodes=0,
        )

    controller = LiveRunController(build_plan=fake_build, run=fake_run, check_model_compat=_pass_compat)
    assert controller._build_plan is fake_build
    assert controller._run is fake_run
    assert controller._check_model_compat is _pass_compat
    controller.start(make_live_config(output="results/tmp_gui_live.json"))
    _wait_for(lambda: not controller.is_running)
    assert calls == {"build": 1, "run": 1}
    assert any(m["type"] == "worker_complete" for m in drain_queue(controller.messages))


def test_normalize_app_event_does_not_invent_metrics():
    summary = normalize_app_event({"type": "episode_start", "pair_id": "p"})
    assert summary["type"] == "episode_start"
    assert "task_success" not in summary


def test_worker_source_uses_plan_kwarg():
    src = inspect.getsource(LiveRunController._worker)
    assert "plan=plan" in src
    assert "collect_runtime_metadata=False" not in src


def test_may_close_window_guard():
    from langtrust.gui.live import may_close_window

    assert may_close_window(is_running=False) is True
    assert may_close_window(is_running=True) is False


def test_app_registers_wm_delete_window_close_guard():
    """Static proof that launch() installs WM_DELETE_WINDOW using may_close_window."""
    import langtrust.gui.app as app_mod

    src = inspect.getsource(app_mod.launch)
    assert 'WM_DELETE_WINDOW' in src
    assert 'may_close_window' in src
    assert 'controller.is_running' in src
    assert 'root.destroy()' in src
    assert 'CLOSE_WHILE_RUNNING_MESSAGE' in src


def test_thread_start_failure_resets_running(monkeypatch):
    class BoomThread:
        def __init__(self, *args, **kwargs):
            pass

        def start(self):
            raise RuntimeError("thread start failed")

    monkeypatch.setattr("langtrust.gui.live.threading.Thread", BoomThread)

    controller = LiveRunController(
        build_plan=lambda *a, **k: (_ for _ in ()).throw(AssertionError("should not build")),
        run=lambda *a, **k: (_ for _ in ()).throw(AssertionError("should not run")),
        check_model_compat=_pass_compat,
    )
    config = make_live_config(output="results/tmp_gui_live.json")
    with pytest.raises(RuntimeError, match="thread start failed"):
        controller.start(config)
    assert controller.is_running is False

    # Recovery: a subsequent start with working Thread must be allowed.
    fake_plan = BenchmarkPlan(
        design=[], protected_conditions=[], expected_episodes=0, metadata={}, pairs={}
    )

    class OkThread:
        def __init__(self, target=None, args=(), kwargs=None, name=None, daemon=None):
            self._target = target
            self._args = args

        def start(self):
            # run synchronously for the test
            self._target(*self._args)

    monkeypatch.setattr("langtrust.gui.live.threading.Thread", OkThread)
    controller2 = LiveRunController(
        build_plan=lambda *a, **k: fake_plan,
        run=lambda *a, **k: BenchmarkRunResult(
            metadata={}, results=[], output_path=Path(config.output), expected_episodes=0
        ),
        check_model_compat=_pass_compat,
    )
    controller2.start(config)
    assert controller2.is_running is False
    assert any(m["type"] == "worker_complete" for m in drain_queue(controller2.messages))

def test_live_run_safety_notice_visible_layout_regression():
    """Keep the hard-cancel disclosure visible in the Live Run form."""
    import ast
    from pathlib import Path

    source = Path("src/langtrust/gui/app.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    warning_widget_ok = False
    hard_cancel_label_ok = False
    expected_notice = (
        "HARD CANCEL: not available — "
        "application layer has no safe cancellation API."
    )

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        func = node.func

        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "tk"
            and func.attr == "Text"
            and node.args
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id == "live_form"
        ):
            height = next(
                (kw.value for kw in node.keywords if kw.arg == "height"),
                None,
            )
            if (
                isinstance(height, ast.Constant)
                and height.value == 6
            ):
                warning_widget_ok = True

        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "ttk"
            and func.attr == "Label"
            and node.args
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id == "live_form"
        ):
            label_text = next(
                (kw.value for kw in node.keywords if kw.arg == "text"),
                None,
            )
            if (
                isinstance(label_text, ast.Constant)
                and label_text.value == expected_notice
            ):
                hard_cancel_label_ok = True

    assert warning_widget_ok
    assert hard_cancel_label_ok


def test_make_live_config_custom_model_passed_to_run():
    plans = []
    runs = []
    compat_models = []

    fake_plan = BenchmarkPlan(
        design=[{"pair_id": "x"}],
        protected_conditions=[True],
        expected_episodes=1,
        metadata={"benchmark": "LangTrust"},
        pairs={"x": {}},
    )

    def fake_build(config, *, scenario_dir=None, git_repo=None, **kwargs):
        plans.append(config)
        return fake_plan

    def fake_run(config, *, scenario_dir=None, git_repo=None, on_event=None, plan=None, **kwargs):
        runs.append(config)
        return BenchmarkRunResult(
            metadata=plan.metadata,
            results=[{"ok": True}],
            output_path=Path(config.output),
            expected_episodes=plan.expected_episodes,
        )

    def tracking_compat(model):
        compat_models.append(model)
        return {"name": model, "capabilities": ["tools"]}

    controller = LiveRunController(
        build_plan=fake_build,
        run=fake_run,
        check_model_compat=tracking_compat,
    )
    config = make_live_config(
        pairs=["invoice_email_001"],
        output="results/tmp_gui_live.json",
        model="live-test-model:latest",
    )
    assert config.model == "live-test-model:latest"
    controller.start(config)
    _wait_for(lambda: not controller.is_running)
    msgs = drain_queue(controller.messages)
    assert any(m["type"] == "worker_complete" for m in msgs)
    assert plans[0].model == "live-test-model:latest"
    assert runs[0].model == "live-test-model:latest"
    assert compat_models == ["live-test-model:latest"]


def test_app_gui_model_selection_source_regression():
    """Static proof Plan and Live expose Model fields and pass model= into helpers."""
    import langtrust.gui.app as app_mod

    src = inspect.getsource(app_mod.launch)
    assert "model_var" in src
    assert "live_model" in src
    assert 'add_labeled(\n        form, "Model"' in src or '"Model"' in src
    assert "model=model_var.get().strip()" in src
    assert "model=live_model.get().strip()" in src
    assert "make_config(" in src
    assert "make_live_config(" in src
    # Editable Model Entry; endpoint remains read-only (combined Model read-only gone).
    assert "Model (read-only)" not in src
    assert "Endpoint (read-only)" in src
    assert "MODEL" in src


def test_compat_check_failure_skips_plan_and_run():
    """G: ModelCompatibilityError before build_plan → no plan/run, worker_error."""
    builds = {"n": 0}
    runs = {"n": 0}

    def boom_compat(model):
        raise ModelCompatibilityError(f"Model {model!r} does not advertise native tool support")

    def fake_build(*args, **kwargs):
        builds["n"] += 1
        raise AssertionError("build_plan must not run after compat failure")

    def fake_run(*args, **kwargs):
        runs["n"] += 1
        raise AssertionError("run_benchmark must not run after compat failure")

    controller = LiveRunController(
        build_plan=fake_build,
        run=fake_run,
        check_model_compat=boom_compat,
    )
    controller.start(make_live_config(output="results/tmp_gui_live.json"))
    _wait_for(lambda: not controller.is_running)
    msgs = drain_queue(controller.messages)
    types = [m["type"] for m in msgs]
    assert "compat_check_started" in types
    assert "compat_check_passed" not in types
    assert "plan_ready" not in types
    assert "worker_complete" not in types
    err = next(m for m in msgs if m["type"] == "worker_error")
    assert err["error_type"] == "ModelCompatibilityError"
    assert err["plan_built"] is False
    assert builds["n"] == 0
    assert runs["n"] == 0


def test_compat_check_success_ordering_before_build_and_run():
    """H: event order is worker_started → compat_* → plan_ready → ... → complete."""
    order = []

    fake_plan = BenchmarkPlan(
        design=[], protected_conditions=[], expected_episodes=0, metadata={}, pairs={}
    )

    def tracking_compat(model):
        order.append(("compat_fn", model))
        return {"name": model, "capabilities": ["tools"]}

    def fake_build(*args, **kwargs):
        order.append("build")
        return fake_plan

    def fake_run(*args, **kwargs):
        order.append("run")
        return BenchmarkRunResult(
            metadata={},
            results=[],
            output_path=Path("results/tmp_gui_live.json"),
            expected_episodes=0,
        )

    controller = LiveRunController(
        build_plan=fake_build,
        run=fake_run,
        check_model_compat=tracking_compat,
    )
    controller.start(make_live_config(output="results/tmp_gui_live.json"))
    _wait_for(lambda: not controller.is_running)
    msgs = drain_queue(controller.messages)
    types = [m["type"] for m in msgs]
    assert types.index("compat_check_started") < types.index("compat_check_passed")
    assert types.index("compat_check_passed") < types.index("plan_ready")
    assert types.index("plan_ready") < types.index("worker_complete")
    assert order[0][0] == "compat_fn"
    assert order[1] == "build"
    assert order[2] == "run"
