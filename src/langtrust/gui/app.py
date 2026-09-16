"""Tkinter GUI for LangTrust (offline tools + Live Run).

Tkinter is imported lazily inside launch() so that importing this module does
not require a Tk-capable Python. Missing Tk yields a clear exit message.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from langtrust.gui import ensure_tkinter_available
from langtrust.gui.branding import (
    apply_window_icon,
    set_windows_app_user_model_id,
)
from langtrust.gui.live import (
    CLOSE_WHILE_RUNNING_MESSAGE,
    DEFAULT_LIVE_OUTPUT,
    LIVE_RUN_WARNING,
    MODEL,
    LiveRunController,
    backend_info,
    make_live_config,
    may_close_window,
)
from langtrust.gui.offline import (
    OVERVIEW_TEXT,
    find_documentation,
    inspect_result_json,
    list_pair_ids,
    make_config,
    package_version,
    preview_plan,
    read_text_file,
)


def launch() -> int:
    """Launch the GUI. Returns process exit code."""
    try:
        ensure_tkinter_available()
    except ImportError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    set_windows_app_user_model_id()
    root = tk.Tk()
    apply_window_icon(root)
    root.title(f"LangTrust GUI — {package_version()}")
    root.geometry("1000x760")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=8, pady=8)

    info = backend_info()

    # ----- Overview -----
    overview = ttk.Frame(notebook)
    notebook.add(overview, text="Overview")
    overview_text = tk.Text(overview, wrap="word", height=30)
    overview_text.pack(fill="both", expand=True)
    overview_text.insert(
        "1.0",
        f"Package version: {package_version()}\n"
        f"Configured model (read-only): {info.model}\n"
        f"Configured Ollama endpoint (read-only): {info.endpoint}\n\n"
        f"{OVERVIEW_TEXT}",
    )
    overview_text.configure(state="disabled")

    try:
        pair_ids = list_pair_ids()
    except Exception as exc:  # noqa: BLE001
        pair_ids = []
        messagebox.showwarning(
            "Scenario load", f"Could not list packaged pairs:\n{exc}"
        )

    def add_labeled(parent, label: str, factory) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=label, width=18).pack(side="left")
        factory(row).pack(side="left", fill="x", expand=True)

    # ----- Plan / Dry-run -----
    config_tab = ttk.Frame(notebook)
    notebook.add(config_tab, text="Plan / Dry-run")

    form = ttk.Frame(config_tab)
    form.pack(fill="x", padx=4, pady=4)

    pair_var = tk.StringVar(value=pair_ids[0] if pair_ids else "")
    condition_var = tk.StringVar(value="attack")
    protected_var = tk.StringVar(value="true")
    repeats_var = tk.StringVar(value="1")
    temperature_var = tk.StringVar(value="0.0")
    seed_var = tk.StringVar(value="1000")
    num_predict_var = tk.StringVar(value="1024")
    timeout_var = tk.StringVar(value="120")
    model_var = tk.StringVar(value=MODEL)

    add_labeled(
        form,
        "Pair",
        lambda parent: ttk.Combobox(
            parent, textvariable=pair_var, values=pair_ids, state="readonly"
        ),
    )
    add_labeled(
        form,
        "Condition",
        lambda parent: ttk.Combobox(
            parent,
            textvariable=condition_var,
            values=["both", "attack", "benign"],
            state="readonly",
        ),
    )
    add_labeled(
        form,
        "Protected",
        lambda parent: ttk.Combobox(
            parent,
            textvariable=protected_var,
            values=["both", "false", "true"],
            state="readonly",
        ),
    )
    add_labeled(form, "Repeats", lambda parent: ttk.Entry(parent, textvariable=repeats_var))
    add_labeled(
        form, "Temperature", lambda parent: ttk.Entry(parent, textvariable=temperature_var)
    )
    add_labeled(form, "Seed base", lambda parent: ttk.Entry(parent, textvariable=seed_var))
    add_labeled(
        form, "num_predict", lambda parent: ttk.Entry(parent, textvariable=num_predict_var)
    )
    add_labeled(
        form, "request_timeout", lambda parent: ttk.Entry(parent, textvariable=timeout_var)
    )
    add_labeled(
        form, "Model", lambda parent: ttk.Entry(parent, textvariable=model_var)
    )

    plan_out = tk.Text(config_tab, wrap="word")
    plan_out.pack(fill="both", expand=True, padx=4, pady=4)

    def run_plan_preview() -> None:
        plan_out.configure(state="normal")
        plan_out.delete("1.0", "end")
        try:
            pairs = [pair_var.get()] if pair_var.get() else None
            config = make_config(
                pairs=pairs,
                condition=condition_var.get(),
                protected=protected_var.get(),
                repeats=int(repeats_var.get()),
                temperature=float(temperature_var.get()),
                seed_base=int(seed_var.get()),
                num_predict=int(num_predict_var.get()),
                request_timeout=float(timeout_var.get()),
                model=model_var.get().strip(),
            )
            summary = preview_plan(config)
            plan_out.insert("1.0", json.dumps(summary, indent=2, ensure_ascii=False))
        except Exception as exc:  # noqa: BLE001
            plan_out.insert("1.0", f"Plan preview failed:\n{exc}")
            messagebox.showerror("Dry-run / plan preview", str(exc))
        plan_out.configure(state="disabled")

    ttk.Button(form, text="Build DRY-RUN plan preview", command=run_plan_preview).pack(
        anchor="w", pady=6
    )
    ttk.Label(
        config_tab,
        text="DRY RUN / PLAN PREVIEW only — no model inference, no live agent execution.",
    ).pack(anchor="w", padx=4)

    # ----- Live Run -----
    live_tab = ttk.Frame(notebook)
    notebook.add(live_tab, text="Live Run")

    live_form = ttk.Frame(live_tab)
    live_form.pack(fill="x", padx=4, pady=4)

    live_pair = tk.StringVar(value=pair_ids[0] if pair_ids else "")
    live_condition = tk.StringVar(value="attack")
    live_protected = tk.StringVar(value="true")
    live_cells = tk.StringVar(value="")
    live_repeats = tk.StringVar(value="1")
    live_temperature = tk.StringVar(value="0.0")
    live_seed = tk.StringVar(value="1000")
    live_num_predict = tk.StringVar(value="1024")
    live_timeout = tk.StringVar(value="120")
    live_output = tk.StringVar(value=DEFAULT_LIVE_OUTPUT)
    live_model = tk.StringVar(value=MODEL)

    add_labeled(
        live_form,
        "Pair",
        lambda parent: ttk.Combobox(
            parent, textvariable=live_pair, values=pair_ids, state="readonly"
        ),
    )
    add_labeled(
        live_form,
        "Condition",
        lambda parent: ttk.Combobox(
            parent,
            textvariable=live_condition,
            values=["both", "attack", "benign"],
            state="readonly",
        ),
    )
    add_labeled(
        live_form,
        "Protected",
        lambda parent: ttk.Combobox(
            parent,
            textvariable=live_protected,
            values=["both", "false", "true"],
            state="readonly",
        ),
    )
    add_labeled(
        live_form,
        "Cells (opt.)",
        lambda parent: ttk.Entry(parent, textvariable=live_cells),
    )
    ttk.Label(
        live_form,
        text="Cells: optional comma-separated cell indexes (empty = all).",
    ).pack(anchor="w")
    add_labeled(
        live_form, "Repeats", lambda parent: ttk.Entry(parent, textvariable=live_repeats)
    )
    add_labeled(
        live_form,
        "Temperature",
        lambda parent: ttk.Entry(parent, textvariable=live_temperature),
    )
    add_labeled(
        live_form, "Seed base", lambda parent: ttk.Entry(parent, textvariable=live_seed)
    )
    add_labeled(
        live_form,
        "num_predict",
        lambda parent: ttk.Entry(parent, textvariable=live_num_predict),
    )
    add_labeled(
        live_form,
        "request_timeout",
        lambda parent: ttk.Entry(parent, textvariable=live_timeout),
    )
    add_labeled(
        live_form, "Output JSON", lambda parent: ttk.Entry(parent, textvariable=live_output)
    )
    add_labeled(
        live_form, "Model", lambda parent: ttk.Entry(parent, textvariable=live_model)
    )

    ttk.Label(
        live_form,
        text=f"Endpoint (read-only): {info.endpoint}",
    ).pack(anchor="w", pady=4)

    warn = tk.Text(live_form, wrap="word", height=6)
    warn.pack(fill="x", pady=4)
    warn.insert("1.0", LIVE_RUN_WARNING)
    warn.configure(state="disabled")

    status_frame = ttk.LabelFrame(live_tab, text="Status")
    status_frame.pack(fill="x", padx=4, pady=4)
    state_var = tk.StringVar(value="Idle")
    progress_var = tk.StringVar(value="0 / 0 (0%)")
    current_var = tk.StringVar(value="—")
    output_status_var = tk.StringVar(value=DEFAULT_LIVE_OUTPUT)
    ttk.Label(status_frame, textvariable=state_var).pack(anchor="w")
    ttk.Label(status_frame, textvariable=progress_var).pack(anchor="w")
    ttk.Label(status_frame, textvariable=current_var).pack(anchor="w")
    ttk.Label(status_frame, textvariable=output_status_var).pack(anchor="w")

    live_log = tk.Text(live_tab, wrap="word", height=16)
    live_log.pack(fill="both", expand=True, padx=4, pady=4)

    controller = LiveRunController()
    completed_episodes = {"n": 0, "expected": 0}

    def set_live_controls(enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        start_btn.configure(state=state)

    def append_live_log(line: str) -> None:
        live_log.configure(state="normal")
        live_log.insert("end", line + "\n")
        live_log.see("end")
        live_log.configure(state="disabled")

    def parse_cells(raw: str):
        raw = raw.strip()
        if not raw:
            return None
        return [int(part.strip()) for part in raw.split(",") if part.strip()]

    def poll_live_queue() -> None:
        import queue as _queue

        while True:
            try:
                msg = controller.messages.get_nowait()
            except _queue.Empty:
                break
            mtype = msg.get("type")
            if mtype == "worker_started":
                state_var.set("Running")
                completed_episodes["n"] = 0
                output_status_var.set(f"Output: {msg.get('output')}")
                append_live_log(f"[worker_started] output={msg.get('output')}")
            elif mtype == "compat_check_started":
                append_live_log(
                    f"Checking model compatibility: {msg.get('model')}"
                )
            elif mtype == "compat_check_passed":
                append_live_log("Model compatibility: PASS")
            elif mtype == "plan_ready":
                expected = int(msg.get("expected_episodes") or 0)
                completed_episodes["expected"] = expected
                progress_var.set(f"0 / {expected} (0%)")
                append_live_log(
                    f"[plan_ready] expected_episodes={expected} "
                    f"pairs={msg.get('selected_pairs')}"
                )
            elif mtype == "app_event":
                display = msg.get("display") or {}
                etype = display.get("type")
                if etype == "episode_start":
                    current_var.set(
                        "pair={pair_id} condition={condition} cell={cell_index} "
                        "repeat={repeat} seed={seed} protected={protected}".format(
                            pair_id=display.get("pair_id"),
                            condition=display.get("condition"),
                            cell_index=display.get("cell_index"),
                            repeat=display.get("repeat"),
                            seed=display.get("seed"),
                            protected=display.get("protected"),
                        )
                    )
                    append_live_log(
                        f"[episode_start] #{display.get('episode_number')} "
                        f"{current_var.get()}"
                    )
                elif etype == "episode_complete":
                    completed_episodes["n"] += 1
                    expected = (
                        completed_episodes["expected"]
                        or display.get("expected_episodes")
                        or 0
                    )
                    done = completed_episodes["n"]
                    pct = int(100 * done / expected) if expected else 0
                    progress_var.set(f"{done} / {expected} ({pct}%)")
                    append_live_log(
                        f"[episode_complete] #{display.get('episode_number')} "
                        f"inference_success={display.get('inference_success')} "
                        f"UTA={display.get('unauthorized_tool_attempt')} "
                        f"UE={display.get('unauthorized_execution')} "
                        f"task_success={display.get('task_success')} "
                        f"done_reasons={display.get('done_reasons')}"
                    )
                else:
                    append_live_log(f"[app_event] {etype}")
            elif mtype == "worker_complete":
                state_var.set("Complete")
                output_status_var.set(f"Output: {msg.get('output_path')}")
                append_live_log(
                    f"[worker_complete] results={msg.get('result_count')} "
                    f"expected={msg.get('expected_episodes')} "
                    f"path={msg.get('output_path')}"
                )
                set_live_controls(True)
            elif mtype == "worker_error":
                state_var.set("Failed")
                append_live_log(
                    f"[worker_error] {msg.get('error_type')}: {msg.get('error')}"
                )
                messagebox.showerror(
                    "Live Run failed",
                    f"{msg.get('error_type')}: {msg.get('error')}",
                )
                set_live_controls(True)
        root.after(100, poll_live_queue)

    def on_close() -> None:
        if may_close_window(is_running=controller.is_running):
            root.destroy()
            return
        messagebox.showwarning("Live Run active", CLOSE_WHILE_RUNNING_MESSAGE)

    root.protocol("WM_DELETE_WINDOW", on_close)


    def start_live_run() -> None:
        if controller.is_running:
            messagebox.showwarning("Live Run", "A Live Run is already in progress.")
            return
        try:
            cells = parse_cells(live_cells.get())
            config = make_live_config(
                pairs=[live_pair.get()] if live_pair.get() else None,
                condition=live_condition.get(),
                protected=live_protected.get(),
                cells=cells,
                repeats=int(live_repeats.get()),
                temperature=float(live_temperature.get()),
                seed_base=int(live_seed.get()),
                num_predict=int(live_num_predict.get()),
                request_timeout=float(live_timeout.get()),
                output=live_output.get().strip() or DEFAULT_LIVE_OUTPUT,
                model=live_model.get().strip(),
            )
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Live Run config", str(exc))
            return

        out_path = Path(config.output)
        if out_path.exists():
            if not messagebox.askyesno(
                "Overwrite output?",
                f"Output file already exists:\n{out_path}\n\nOverwrite?",
            ):
                return

        if not messagebox.askokcancel("Start Live Run", LIVE_RUN_WARNING):
            return

        live_log.configure(state="normal")
        live_log.delete("1.0", "end")
        live_log.configure(state="disabled")
        state_var.set("Running")
        set_live_controls(False)
        try:
            controller.start(config)
        except Exception as exc:  # noqa: BLE001
            set_live_controls(True)
            state_var.set("Failed")
            messagebox.showerror("Live Run", str(exc))

    start_btn = ttk.Button(live_form, text="Start Live Run", command=start_live_run)
    start_btn.pack(anchor="w", pady=6)
    ttk.Label(
        live_form,
        text="HARD CANCEL: not available — application layer has no safe cancellation API.",
    ).pack(anchor="w", pady=(0, 4))

    root.after(100, poll_live_queue)

    # ----- Inspect JSON -----
    inspect_tab = ttk.Frame(notebook)
    notebook.add(inspect_tab, text="Inspect JSON")
    inspect_bar = ttk.Frame(inspect_tab)
    inspect_bar.pack(fill="x", padx=4, pady=4)
    result_path_var = tk.StringVar()
    ttk.Entry(inspect_bar, textvariable=result_path_var).pack(
        side="left", fill="x", expand=True
    )

    inspect_out = tk.Text(inspect_tab, wrap="word")
    inspect_out.pack(fill="both", expand=True, padx=4, pady=4)

    def choose_result() -> None:
        path = filedialog.askopenfilename(
            title="Select LangTrust result JSON",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")],
        )
        if path:
            result_path_var.set(path)

    def load_result() -> None:
        inspect_out.configure(state="normal")
        inspect_out.delete("1.0", "end")
        try:
            summary = inspect_result_json(result_path_var.get())
            inspect_out.insert("1.0", json.dumps(summary, indent=2, ensure_ascii=False))
        except Exception as exc:  # noqa: BLE001
            inspect_out.insert("1.0", f"Could not inspect file:\n{exc}")
            messagebox.showerror("Inspect JSON", str(exc))
        inspect_out.configure(state="disabled")

    ttk.Button(inspect_bar, text="Browse…", command=choose_result).pack(
        side="left", padx=4
    )
    ttk.Button(inspect_bar, text="Inspect", command=load_result).pack(side="left")

    # ----- Docs -----
    docs_tab = ttk.Frame(notebook)
    notebook.add(docs_tab, text="Docs")
    docs_bar = ttk.Frame(docs_tab)
    docs_bar.pack(fill="x", padx=4, pady=4)
    docs_found = find_documentation()
    doc_names = [name for name, path in docs_found.items() if path]
    doc_var = tk.StringVar(value=doc_names[0] if doc_names else "")
    ttk.Combobox(
        docs_bar, textvariable=doc_var, values=doc_names, state="readonly"
    ).pack(side="left")
    docs_out = tk.Text(docs_tab, wrap="word")
    docs_out.pack(fill="both", expand=True, padx=4, pady=4)

    def open_doc() -> None:
        docs_out.configure(state="normal")
        docs_out.delete("1.0", "end")
        name = doc_var.get()
        path = docs_found.get(name)
        if not path:
            docs_out.insert(
                "1.0",
                "Documentation file not found locally.\n"
                "These files are available from a source checkout; "
                "they are not guaranteed after a wheel install.",
            )
        else:
            try:
                docs_out.insert(
                    "1.0", f"# {name}\nPath: {path}\n\n" + read_text_file(path)
                )
            except Exception as exc:  # noqa: BLE001
                docs_out.insert("1.0", str(exc))
                messagebox.showerror("Docs", str(exc))
        docs_out.configure(state="disabled")

    ttk.Button(docs_bar, text="Open", command=open_doc).pack(side="left", padx=4)
    if not doc_names:
        docs_out.insert(
            "1.0",
            "No local documentation files were found.\n"
            "Open a repository checkout to browse README / ARTIFACTS / PROVENANCE / "
            "REPRODUCIBILITY / CITATION.cff / SHA256SUMS.",
        )
        docs_out.configure(state="disabled")

    root.mainloop()
    return 0


def main(argv: list[str] | None = None) -> int:
    return launch()


if __name__ == "__main__":
    raise SystemExit(main())
