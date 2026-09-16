"""Offline GUI tests that do not require Tkinter."""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from langtrust.app.models import BenchmarkRunConfig
from langtrust.gui import GUI_REQUIRES_TKINTER_MESSAGE


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_isolated(script: str) -> subprocess.CompletedProcess[str]:
    """Run a short Python snippet in a fresh interpreter (no shared sys.modules)."""
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env={
            **dict(**{k: v for k, v in __import__("os").environ.items()}),
            "PYTHONPATH": str(REPO_ROOT / "src"),
        },
        check=False,
    )


def test_imports_work_with_tk_blocked():
    script = textwrap.dedent(
        """
        import builtins
        import sys

        real_import = builtins.__import__

        def blocked(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "tkinter" or name.startswith("tkinter."):
                raise ImportError("blocked tkinter for test")
            return real_import(name, globals, locals, fromlist, level)

        builtins.__import__ = blocked
        for mod in list(sys.modules):
            if mod == "tkinter" or mod.startswith("tkinter."):
                sys.modules.pop(mod, None)

        import langtrust
        import langtrust.app
        import langtrust.gui

        assert langtrust.__name__ == "langtrust"
        assert langtrust.app.__name__ == "langtrust.app"
        assert langtrust.gui.__name__ == "langtrust.gui"
        print("OK")
        """
    )
    result = _run_isolated(script)
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout


def test_gui_package_exports_without_importing_tk():
    script = textwrap.dedent(
        """
        import sys
        # Ensure a clean view of whether importing gui pulls tkinter.
        before = {m for m in sys.modules if m == "tkinter" or m.startswith("tkinter.")}
        import langtrust.gui as gui
        after = {m for m in sys.modules if m == "tkinter" or m.startswith("tkinter.")}
        assert "GUI_REQUIRES_TKINTER_MESSAGE" in gui.__all__
        assert after == before, f"gui import pulled tkinter: {after - before}"
        print("OK")
        """
    )
    result = _run_isolated(script)
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout


def test_missing_tkinter_launcher_message():
    script = textwrap.dedent(
        f"""
        import builtins
        import sys

        real_import = builtins.__import__

        def blocked(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "tkinter" or name.startswith("tkinter."):
                raise ImportError("No module named '_tkinter'")
            return real_import(name, globals, locals, fromlist, level)

        builtins.__import__ = blocked
        sys.modules.pop("tkinter", None)

        from langtrust.gui import GUI_REQUIRES_TKINTER_MESSAGE, ensure_tkinter_available
        from langtrust.gui.app import launch

        try:
            ensure_tkinter_available()
        except ImportError as exc:
            assert str(exc) == GUI_REQUIRES_TKINTER_MESSAGE
        else:
            raise AssertionError("expected ImportError")

        code = launch()
        assert code == 1
        print("OK")
        print(GUI_REQUIRES_TKINTER_MESSAGE)
        """
    )
    result = _run_isolated(script)
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout
    assert "Tkinter" in result.stdout


def test_preview_plan_zero_ollama_probes_and_no_inference(monkeypatch):
    import langtrust.app.benchmark as ab
    from langtrust.gui import offline as offline_mod

    def boom_ollama_version():
        raise AssertionError("offline GUI attempted Ollama probe")

    def boom_ollama_model(model_name):
        raise AssertionError("offline GUI attempted Ollama probe")

    def boom_http(*args, **kwargs):
        raise AssertionError("offline GUI attempted Ollama probe")

    def boom_agent(**kwargs):
        raise AssertionError("offline GUI attempted agent construction")

    monkeypatch.setattr(ab, "get_ollama_version", boom_ollama_version)
    monkeypatch.setattr(ab, "get_ollama_model_metadata", boom_ollama_model)
    monkeypatch.setattr(ab, "_ollama_json_request", boom_http)
    monkeypatch.setattr(ab, "_default_agent_factory", boom_agent)

    run_calls = {"n": 0}
    real_run = ab.run_benchmark

    def counting_run(*args, **kwargs):
        run_calls["n"] += 1
        return real_run(*args, **kwargs)

    monkeypatch.setattr(ab, "run_benchmark", counting_run)

    # Patch the symbols bound in offline.py as well (same objects after reload path).
    monkeypatch.setattr(offline_mod, "build_benchmark_plan", ab.build_benchmark_plan)

    config = offline_mod.make_config(
        pairs=["invoice_email_001"],
        condition="attack",
        protected="true",
        repeats=1,
    )
    assert config.dry_run is True
    summary = offline_mod.preview_plan(config)

    assert summary["mode"] == "DRY RUN / PLAN PREVIEW"
    assert summary["inference"] is False
    assert summary["expected_episodes"] >= 1
    assert summary["config"]["dry_run"] is True
    assert run_calls["n"] == 0


def test_invalid_config_uses_application_validation():
    from langtrust.gui.offline import make_config

    with pytest.raises(ValueError, match="condition"):
        make_config(condition="maybe")
    with pytest.raises(ValueError, match="protected"):
        make_config(protected="yes")
    with pytest.raises(ValueError, match="repeats"):
        make_config(repeats=0)
    with pytest.raises(ValueError, match="num-predict"):
        make_config(num_predict=0)
    with pytest.raises(ValueError, match="request-timeout"):
        make_config(request_timeout=0)
    with pytest.raises(ValueError, match="--model must be a non-empty string"):
        make_config(model="")
    with pytest.raises(ValueError, match="--model must be a non-empty string"):
        make_config(model="   ")


def test_inspect_result_json_valid(tmp_path):
    from langtrust.gui.offline import inspect_result_json

    path = tmp_path / "sample.json"
    path.write_text(
        json.dumps(
            {
                "metadata": {"benchmark": "langtrust", "repeats": 1},
                "results": [
                    {
                        "pair_id": "invoice_email_001",
                        "domain": "invoice",
                        "condition": "attack",
                        "scenario": "invoice_email_001_attack",
                        "cell_index": 0,
                        "seed": 1000,
                        "protected_prompt": True,
                        "answer": "ok",
                        "inference": {
                            "success": True,
                            "failure_type": None,
                            "calls": [{"done_reason": "stop"}],
                        },
                        "evaluation": {
                            "security": {
                                "unauthorized_tool_attempt": False,
                                "unauthorized_execution": False,
                            },
                            "utility": {"task_success": True},
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    summary = inspect_result_json(path)
    assert summary["record_count"] == 1
    assert summary["metadata"]["benchmark"] == "langtrust"
    assert summary["records"][0]["done_reasons"] == ["stop"]
    assert summary["records"][0]["task_success"] is True



def test_inspect_result_json_accepts_utf8_bom(tmp_path):
    from langtrust.gui.offline import inspect_result_json

    path = tmp_path / "bom.json"
    path.write_text(
        json.dumps(
            {
                "metadata": {"qa": "utf8-bom"},
                "results": [],
            }
        ),
        encoding="utf-8-sig",
    )

    summary = inspect_result_json(path)

    assert summary["metadata"] == {"qa": "utf8-bom"}
    assert summary["record_count"] == 0
    assert summary["records"] == []


def test_inspect_result_json_malformed(tmp_path):
    from langtrust.gui.offline import inspect_result_json

    path = tmp_path / "bad.json"
    path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(ValueError, match="Malformed JSON"):
        inspect_result_json(path)


def test_inspect_result_json_missing_results(tmp_path):
    from langtrust.gui.offline import inspect_result_json

    path = tmp_path / "empty.json"
    path.write_text(json.dumps({"metadata": {}}), encoding="utf-8")
    with pytest.raises(ValueError, match="missing 'results'"):
        inspect_result_json(path)


def test_documentation_lookup_missing(tmp_path):
    from langtrust.gui.offline import find_documentation

    found = find_documentation(search_roots=[tmp_path])
    assert all(v is None for v in found.values())


def test_documentation_lookup_present(tmp_path):
    from langtrust.gui.offline import find_documentation, read_text_file

    (tmp_path / "README.md").write_text("# hello", encoding="utf-8")
    found = find_documentation(search_roots=[tmp_path])
    assert found["README.md"] == str(tmp_path / "README.md")
    assert "hello" in read_text_file(found["README.md"])


def test_list_pair_ids_via_app_layer():
    from langtrust.app.benchmark import list_benchmark_pair_ids
    from langtrust.gui.offline import list_pair_ids

    assert list_pair_ids() == list_benchmark_pair_ids()
    assert "invoice_email_001" in list_pair_ids()


def test_package_version_string():
    from langtrust.gui.offline import package_version

    version = package_version()
    assert isinstance(version, str)
    assert len(version) > 0


def test_gui_message_constant():
    assert "Tkinter" in GUI_REQUIRES_TKINTER_MESSAGE


def test_packaged_documentation_matches_repository_bytes():
    from pathlib import Path

    import langtrust.gui.offline as offline

    repo = Path(__file__).resolve().parents[1]
    packaged = repo / "src" / "langtrust" / "resources" / "docs"

    for name in offline.DOC_CANDIDATES:
        assert (packaged / name).read_bytes() == (repo / name).read_bytes()



def test_documentation_lookup_ignores_unrelated_parent_docs(
    tmp_path,
    monkeypatch,
):
    import langtrust.gui.offline as offline

    unrelated = tmp_path / "unrelated-parent"
    outside = unrelated / "qa" / "outside-repository"
    installed = unrelated / "qa" / "venv" / "site-packages"

    outside.mkdir(parents=True)
    installed.mkdir(parents=True)

    for name in offline.DOC_CANDIDATES:
        (unrelated / name).write_text(
            f"unrelated {name}",
            encoding="utf-8",
        )

    monkeypatch.chdir(outside)
    monkeypatch.setattr(
        offline,
        "__file__",
        str(installed / "langtrust" / "gui" / "offline.py"),
    )

    found = offline.find_documentation()

    for name in offline.DOC_CANDIDATES:
        assert found[name] == offline.PACKAGED_DOC_PREFIX + name
        assert "unrelated-parent" not in found[name]


def test_packaged_documentation_fallback_and_read(tmp_path, monkeypatch):
    import langtrust.gui.offline as offline

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        offline,
        "__file__",
        str(tmp_path / "installed" / "langtrust" / "gui" / "offline.py"),
    )

    found = offline.find_documentation()

    assert set(found) == set(offline.DOC_CANDIDATES)

    for name in offline.DOC_CANDIDATES:
        uri = found[name]

        assert uri == offline.PACKAGED_DOC_PREFIX + name

        text = offline.read_text_file(uri)
        assert isinstance(text, str)
        assert text


def test_make_config_default_model():
    from langtrust.gui.offline import make_config

    config = make_config()
    assert config.model == "qwen2.5:14b"


def test_make_config_custom_model():
    from langtrust.gui.offline import make_config

    config = make_config(model="example-model:latest")
    assert config.model == "example-model:latest"


def test_preview_plan_propagates_custom_model(monkeypatch):
    import langtrust.app.benchmark as ab
    from langtrust.gui import offline as offline_mod

    def boom_ollama_version():
        raise AssertionError("offline GUI attempted Ollama probe")

    def boom_ollama_model(model_name):
        raise AssertionError("offline GUI attempted Ollama probe")

    def boom_http(*args, **kwargs):
        raise AssertionError("offline GUI attempted Ollama probe")

    monkeypatch.setattr(ab, "get_ollama_version", boom_ollama_version)
    monkeypatch.setattr(ab, "get_ollama_model_metadata", boom_ollama_model)
    monkeypatch.setattr(ab, "_ollama_json_request", boom_http)
    monkeypatch.setattr(offline_mod, "build_benchmark_plan", ab.build_benchmark_plan)

    config = offline_mod.make_config(
        pairs=["invoice_email_001"],
        condition="attack",
        protected="true",
        repeats=1,
        model="offline-test-model:latest",
    )
    summary = offline_mod.preview_plan(config)
    assert summary["metadata"]["model"] == "offline-test-model:latest"
    assert summary["config"]["model"] == "offline-test-model:latest"


def test_preview_plan_forces_dry_run_preserves_model(monkeypatch):
    """Custom model survives dry_run-force rebuild without Ollama probes."""
    import langtrust.app.benchmark as ab
    from langtrust.app.models import BenchmarkRunConfig
    from langtrust.gui import offline as offline_mod

    def boom_ollama_version():
        raise AssertionError("offline GUI attempted Ollama probe")

    def boom_ollama_model(model_name):
        raise AssertionError("offline GUI attempted Ollama probe")

    def boom_http(*args, **kwargs):
        raise AssertionError("offline GUI attempted Ollama probe")

    monkeypatch.setattr(ab, "get_ollama_version", boom_ollama_version)
    monkeypatch.setattr(ab, "get_ollama_model_metadata", boom_ollama_model)
    monkeypatch.setattr(ab, "_ollama_json_request", boom_http)
    monkeypatch.setattr(offline_mod, "build_benchmark_plan", ab.build_benchmark_plan)

    config = BenchmarkRunConfig(
        pairs=["invoice_email_001"],
        condition="attack",
        protected="true",
        repeats=1,
        dry_run=False,
        model="offline-test-model:latest",
    )
    summary = offline_mod.preview_plan(config)
    assert summary["inference"] is False
    assert summary["config"]["dry_run"] is True
    assert summary["metadata"]["model"] == "offline-test-model:latest"
    assert summary["config"]["model"] == "offline-test-model:latest"


def test_preview_plan_does_not_call_model_compat_preflight(monkeypatch):
    """J: offline preview must not invoke Live Run model-compat preflight."""
    import langtrust.app.benchmark as ab
    import langtrust.app.model_compat as mc
    from langtrust.gui import offline as offline_mod

    def boom_compat(*args, **kwargs):
        raise AssertionError("offline GUI invoked check_ollama_model_tool_compatibility")

    monkeypatch.setattr(mc, "check_ollama_model_tool_compatibility", boom_compat)

    def boom_ollama_version():
        raise AssertionError("offline GUI attempted Ollama probe")

    def boom_ollama_model(model_name):
        raise AssertionError("offline GUI attempted Ollama probe")

    def boom_http(*args, **kwargs):
        raise AssertionError("offline GUI attempted Ollama probe")

    monkeypatch.setattr(ab, "get_ollama_version", boom_ollama_version)
    monkeypatch.setattr(ab, "get_ollama_model_metadata", boom_ollama_model)
    monkeypatch.setattr(ab, "_ollama_json_request", boom_http)
    monkeypatch.setattr(offline_mod, "build_benchmark_plan", ab.build_benchmark_plan)

    config = offline_mod.make_config(
        pairs=["invoice_email_001"],
        condition="attack",
        protected="true",
        repeats=1,
    )
    summary = offline_mod.preview_plan(config)
    assert summary["mode"] == "DRY RUN / PLAN PREVIEW"
    assert summary["inference"] is False
