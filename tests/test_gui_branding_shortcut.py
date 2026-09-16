"""Branding resources and desktop-shortcut planning/creation tests."""

from __future__ import annotations

import os
import plistlib
import stat
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from langtrust.gui.branding import (
    BRANDING_FILENAMES,
    ICON_ICNS,
    ICON_ICO,
    ICON_PNG,
    ICON_SVG,
    apply_window_icon,
    read_branding_bytes,
)
from langtrust.gui.shortcut import (
    APP_NAME,
    BUNDLE_ID,
    LINUX_DESKTOP_BASENAME,
    LINUX_OWNER_KEY,
    MACOS_APP_BASENAME,
    MARKER_FILENAME,
    OWNER_MARKER_CONTENTS,
    ShortcutError,
    WINDOWS_DESCRIPTION_MARKER,
    WINDOWS_LNK_BASENAME,
    create_shortcut,
    find_powershell,
    plan_shortcut,
    prefer_pythonw,
    remove_shortcut,
    render_linux_desktop,
    render_macos_plist,
    render_macos_wrapper,
    validate_owned_launcher,
)


def test_branding_files_resolvable_and_named():
    assert BRANDING_FILENAMES == (ICON_SVG, ICON_PNG, ICON_ICO, ICON_ICNS)
    for name in BRANDING_FILENAMES:
        data = read_branding_bytes(name)
        assert isinstance(data, bytes)
        assert len(data) > 0


def test_apply_window_icon_tolerates_failure():
    class BoomRoot:
        def iconphoto(self, *args, **kwargs):
            raise RuntimeError("no display")

        def iconbitmap(self, *args, **kwargs):
            raise RuntimeError("no ico")

    # Must not raise
    apply_window_icon(BoomRoot())


def test_plan_uses_sys_executable(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    (home / "Desktop").mkdir()
    py = tmp_path / "venv" / "bin" / "python"
    py.parent.mkdir(parents=True)
    py.write_text("#!/bin/sh\n", encoding="utf-8")
    plan = plan_shortcut(
        platform="linux",
        python_executable=py,
        home=home,
        environ={"HOME": str(home)},
    )
    assert plan.python_executable == py
    assert plan.module == "langtrust.gui"
    assert plan.launcher_path == home / "Desktop" / LINUX_DESKTOP_BASENAME


def test_plan_handles_spaces_in_paths(tmp_path):
    home = tmp_path / "user name"
    desktop = home / "My Desktop"
    desktop.mkdir(parents=True)
    py = tmp_path / "env with spaces" / "bin" / "python"
    py.parent.mkdir(parents=True)
    py.write_text("x", encoding="utf-8")
    plan = plan_shortcut(
        platform="linux",
        python_executable=py,
        home=home,
        environ={"HOME": str(home), "XDG_DESKTOP_DIR": str(desktop)},
    )
    assert " " in str(plan.python_executable)
    assert plan.desktop_dir == desktop
    icon = plan.persistent_icon_path
    assert icon is not None
    content = render_linux_desktop(plan, icon)
    assert str(py) in content or '"' in content
    assert "-m langtrust.gui" in content


def test_linux_desktop_create_executable_and_force(tmp_path):
    home = tmp_path / "home"
    desktop = home / "Desktop"
    desktop.mkdir(parents=True)
    py = tmp_path / "python"
    py.write_text("x", encoding="utf-8")
    plan = plan_shortcut(
        platform="linux",
        python_executable=py,
        home=home,
        environ={"HOME": str(home)},
    )
    path = create_shortcut(plan, force=False)
    assert path.exists()
    assert path.stat().st_mode & stat.S_IXUSR
    text = path.read_text(encoding="utf-8")
    assert text.startswith("[Desktop Entry]")
    assert f"Name={APP_NAME}" in text
    assert "X-LangTrust-Owner=langtrust-gui-shortcut" in text
    assert plan.persistent_icon_path is not None
    assert plan.persistent_icon_path.is_file()

    with pytest.raises(ShortcutError, match="already exists"):
        create_shortcut(plan, force=False)

    path.write_text(text + "# stale\n", encoding="utf-8")
    create_shortcut(plan, force=True)
    assert "# stale" not in path.read_text(encoding="utf-8")

    removed = remove_shortcut(plan)
    assert removed == path
    assert not path.exists()


def test_macos_app_bundle_plan_and_create(tmp_path):
    home = tmp_path / "home"
    (home / "Desktop").mkdir(parents=True)
    py = tmp_path / "Python with spaces" / "bin" / "python3"
    py.parent.mkdir(parents=True)
    py.write_text("x", encoding="utf-8")
    plan = plan_shortcut(
        platform="darwin",
        python_executable=py,
        home=home,
        environ={"HOME": str(home)},
    )
    assert plan.launcher_path.name == MACOS_APP_BASENAME
    app = create_shortcut(plan)
    assert (app / "Contents" / "Info.plist").is_file()
    assert (app / "Contents" / "MacOS" / "langtrust").is_file()
    assert (app / "Contents" / "Resources" / "langtrust.icns").is_file()
    assert (app / "Contents" / "Resources" / MARKER_FILENAME).is_file()
    wrapper = (app / "Contents" / "MacOS" / "langtrust").read_text(encoding="utf-8")
    assert "-m langtrust.gui" in wrapper
    assert str(py) in wrapper
    info = plistlib.loads((app / "Contents" / "Info.plist").read_bytes())
    assert info["CFBundleIdentifier"] == BUNDLE_ID
    assert info["CFBundleName"] == APP_NAME
    assert info["CFBundleExecutable"] == "langtrust"
    assert info["CFBundleIconFile"] == "langtrust.icns"
    assert info["CFBundlePackageType"] == "APPL"
    # wrapper executable
    assert (app / "Contents" / "MacOS" / "langtrust").stat().st_mode & stat.S_IXUSR

    with pytest.raises(ShortcutError, match="already exists"):
        create_shortcut(plan, force=False)
    create_shortcut(plan, force=True)
    remove_shortcut(plan)
    assert not app.exists()


def test_windows_shortcut_planning_and_pythonw(tmp_path):
    home = tmp_path / "home"
    (home / "Desktop").mkdir(parents=True)
    py = tmp_path / "Python 3.14" / "python.exe"
    py.parent.mkdir(parents=True)
    py.write_text("x", encoding="utf-8")
    plan = plan_shortcut(
        platform="win32",
        python_executable=py,
        home=home,
        environ={"USERPROFILE": str(home)},
    )
    assert plan.launcher_path.name == WINDOWS_LNK_BASENAME
    assert plan.python_executable == py  # no pythonw yet
    assert plan.icon_basename == ICON_ICO

    pyw = py.with_name("pythonw.exe")
    pyw.write_text("x", encoding="utf-8")
    plan2 = plan_shortcut(
        platform="win32",
        python_executable=py,
        home=home,
        environ={"USERPROFILE": str(home)},
    )
    assert plan2.python_executable == pyw


def test_windows_create_uses_runner(tmp_path):
    home = tmp_path / "home"
    (home / "Desktop").mkdir(parents=True)
    py = tmp_path / "python.exe"
    py.write_text("x", encoding="utf-8")
    plan = plan_shortcut(
        platform="win32",
        python_executable=py,
        home=home,
        environ={"USERPROFILE": str(home), "LOCALAPPDATA": str(tmp_path / "lad")},
    )
    calls = {}

    def fake_run(cmd, capture_output=True, text=True, check=False):
        calls["cmd"] = cmd
        # Simulate successful .lnk creation
        plan.launcher_path.write_text("lnk", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    path = create_shortcut(plan, force=False, windows_runner=fake_run)
    assert path.exists()
    assert calls["cmd"][0] == "powershell"
    script = calls["cmd"][-1]
    assert "-m langtrust.gui" in script
    assert str(py) in script or "python.exe" in script
    assert "langtrust.ico" in script.lower() or "IconLocation" in script


def test_prefer_pythonw_only_when_exists(tmp_path):
    py = tmp_path / "python.exe"
    py.write_text("x", encoding="utf-8")
    assert prefer_pythonw(py) == py
    pyw = tmp_path / "pythonw.exe"
    pyw.write_text("x", encoding="utf-8")
    assert prefer_pythonw(py) == pyw


def test_unsupported_platform():
    with pytest.raises(ShortcutError, match="Unsupported platform"):
        plan_shortcut(platform="solaris", python_executable=Path("/bin/python"))


def test_remove_only_expected_linux(tmp_path):
    home = tmp_path / "home"
    desktop = home / "Desktop"
    desktop.mkdir(parents=True)
    py = tmp_path / "python"
    py.write_text("x", encoding="utf-8")
    plan = plan_shortcut(
        platform="linux",
        python_executable=py,
        home=home,
        environ={"HOME": str(home)},
    )
    create_shortcut(plan)
    # foreign file with wrong name must not be removable via plan
    foreign = desktop / "Other.desktop"
    foreign.write_text("[Desktop Entry]\nName=Other\n", encoding="utf-8")
    # plan still points at LangTrust.desktop
    remove_shortcut(plan)
    assert not plan.launcher_path.exists()
    assert foreign.exists()


def test_shortcut_modules_do_not_import_scientific_core():
    import ast

    for rel in (
        "src/langtrust/gui/branding.py",
        "src/langtrust/gui/shortcut.py",
        "src/langtrust/cli/gui_shortcut.py",
    ):
        tree = ast.parse(Path(rel).read_text(encoding="utf-8"))
        names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.extend(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.append(node.module or "")
        banned = (
            "langtrust.agent",
            "langtrust.backend",
            "langtrust.environment",
            "langtrust.evaluation",
            "langtrust.benchmark",
        )
        for name in names:
            assert not any(name == b or name.startswith(b + ".") for b in banned), (
                rel,
                name,
            )


def test_macos_wrapper_quotes_spaces():
    plan = plan_shortcut(
        platform="darwin",
        python_executable=Path("/Applications/My Python/bin/python3"),
        home=Path("/Users/test"),
        environ={"HOME": "/Users/test"},
    )
    script = render_macos_wrapper(plan)
    assert "/Applications/My Python/bin/python3" in script
    assert "-m langtrust.gui" in script


def test_render_macos_plist_bytes():
    info = plistlib.loads(render_macos_plist())
    assert info["CFBundleIdentifier"] == BUNDLE_ID


def _linux_home(tmp_path):
    home = tmp_path / "home"
    (home / "Desktop").mkdir(parents=True)
    py = tmp_path / "python"
    py.write_text("x", encoding="utf-8")
    return plan_shortcut(
        platform="linux",
        python_executable=py,
        home=home,
        environ={"HOME": str(home)},
    )


def test_foreign_linux_desktop_name_only_refused_force_and_remove(tmp_path):
    plan = _linux_home(tmp_path)
    foreign = plan.launcher_path
    foreign.write_text(
        "[Desktop Entry]\nType=Application\nName=LangTrust\nExec=true\n",
        encoding="utf-8",
    )
    with pytest.raises(ShortcutError, match="not owned"):
        create_shortcut(plan, force=True)
    with pytest.raises(ShortcutError, match="not owned"):
        remove_shortcut(plan)
    assert foreign.exists()




def test_foreign_linux_desktop_commented_owner_marker_refused(tmp_path):
    plan = _linux_home(tmp_path)
    foreign = plan.launcher_path
    foreign.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=LangTrust\n"
        "# X-LangTrust-Owner=langtrust-gui-shortcut\n"
        "Exec=true\n",
        encoding="utf-8",
    )
    with pytest.raises(ShortcutError, match="not owned"):
        create_shortcut(plan, force=True)
    with pytest.raises(ShortcutError, match="not owned"):
        remove_shortcut(plan)
    assert foreign.exists()
    assert foreign.read_text(encoding="utf-8").startswith("[Desktop Entry]")


def test_owned_linux_desktop_force_and_remove(tmp_path):
    plan = _linux_home(tmp_path)
    create_shortcut(plan)
    assert LINUX_OWNER_KEY in plan.launcher_path.read_text(encoding="utf-8")
    create_shortcut(plan, force=True)
    remove_shortcut(plan)
    assert not plan.launcher_path.exists()


def _macos_home(tmp_path):
    home = tmp_path / "home"
    (home / "Desktop").mkdir(parents=True)
    py = tmp_path / "python3"
    py.write_text("x", encoding="utf-8")
    return plan_shortcut(
        platform="darwin",
        python_executable=py,
        home=home,
        environ={"HOME": str(home)},
    )


def test_foreign_macos_app_bundle_id_without_marker_refused(tmp_path):
    import plistlib

    plan = _macos_home(tmp_path)
    app = plan.launcher_path
    (app / "Contents" / "Resources").mkdir(parents=True)
    (app / "Contents" / "MacOS").mkdir(parents=True)
    (app / "Contents" / "Info.plist").write_bytes(
        plistlib.dumps({"CFBundleIdentifier": BUNDLE_ID, "CFBundleName": APP_NAME})
    )
    with pytest.raises(ShortcutError, match="not owned|missing"):
        create_shortcut(plan, force=True)
    with pytest.raises(ShortcutError, match="not owned|missing"):
        remove_shortcut(plan)
    assert app.exists()


def test_owned_macos_app_force_and_remove(tmp_path):
    plan = _macos_home(tmp_path)
    create_shortcut(plan)
    marker = plan.launcher_path / "Contents" / "Resources" / MARKER_FILENAME
    assert marker.read_text(encoding="utf-8") == OWNER_MARKER_CONTENTS
    create_shortcut(plan, force=True)
    remove_shortcut(plan)
    assert not plan.launcher_path.exists()


def test_macos_symlink_refused(tmp_path):
    plan = _macos_home(tmp_path)
    target = tmp_path / "other.app"
    target.mkdir()
    plan.launcher_path.symlink_to(target)
    with pytest.raises(ShortcutError, match="symlink"):
        create_shortcut(plan, force=True)
    with pytest.raises(ShortcutError, match="symlink"):
        remove_shortcut(plan)


def _windows_home(tmp_path):
    home = tmp_path / "home"
    (home / "Desktop").mkdir(parents=True)
    py = tmp_path / "python.exe"
    py.write_text("x", encoding="utf-8")
    return plan_shortcut(
        platform="win32",
        python_executable=py,
        home=home,
        environ={"USERPROFILE": str(home), "LOCALAPPDATA": str(tmp_path / "lad")},
    )


def test_foreign_windows_lnk_without_description_refused(tmp_path):
    plan = _windows_home(tmp_path)
    plan.launcher_path.write_text("fake-lnk", encoding="utf-8")

    def runner(cmd, capture_output=True, text=True, check=False):
        if cmd[-1] == "exit 0":
            return subprocess.CompletedProcess(cmd, 0, "", "")
        return subprocess.CompletedProcess(cmd, 0, "Some other shortcut\n", "")

    with pytest.raises(ShortcutError, match="not owned"):
        create_shortcut(plan, force=True, windows_runner=runner)
    with pytest.raises(ShortcutError, match="not owned"):
        remove_shortcut(plan, windows_runner=runner)


def test_owned_windows_lnk_force_and_remove(tmp_path):
    plan = _windows_home(tmp_path)
    state = {"desc": ""}

    def runner(cmd, capture_output=True, text=True, check=False):
        script = cmd[-1]
        if script == "exit 0":
            return subprocess.CompletedProcess(cmd, 0, "", "")
        if "Write-Output $s.Description" in script:
            return subprocess.CompletedProcess(cmd, 0, state["desc"] + "\n", "")
        if "CreateShortcut" in script and "Save" in script:
            assert WINDOWS_DESCRIPTION_MARKER in script
            plan.launcher_path.write_text("lnk", encoding="utf-8")
            state["desc"] = WINDOWS_DESCRIPTION_MARKER
            return subprocess.CompletedProcess(cmd, 0, "", "")
        return subprocess.CompletedProcess(cmd, 1, "", "unexpected")

    create_shortcut(plan, force=False, windows_runner=runner)
    create_shortcut(plan, force=True, windows_runner=runner)
    remove_shortcut(plan, windows_runner=runner)
    assert not plan.launcher_path.exists()


def test_powershell_unavailable_is_shortcut_error(tmp_path):
    plan = _windows_home(tmp_path)

    def runner(cmd, capture_output=True, text=True, check=False):
        raise FileNotFoundError("powershell")

    with pytest.raises(ShortcutError, match="PowerShell"):
        create_shortcut(plan, force=False, windows_runner=runner)


def test_powershell_success_without_lnk_is_failure(tmp_path):
    plan = _windows_home(tmp_path)

    def runner(cmd, capture_output=True, text=True, check=False):
        if cmd[-1] == "exit 0":
            return subprocess.CompletedProcess(cmd, 0, "", "")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    with pytest.raises(ShortcutError, match="was not created"):
        create_shortcut(plan, force=False, windows_runner=runner)


def test_find_powershell_prefers_available():
    calls = []

    def runner(cmd, capture_output=True, text=True, check=False):
        calls.append(cmd[0])
        if cmd[0] == "powershell":
            raise FileNotFoundError("nope")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    assert find_powershell(runner=runner) == "pwsh"
    assert calls == ["powershell", "pwsh"]


def test_windows_branding_sets_ico_on_current_root(tmp_path, monkeypatch):
    import langtrust.gui.branding as branding

    ico = tmp_path / branding.ICON_ICO
    png = tmp_path / branding.ICON_PNG
    ico.write_bytes(b"fake-ico")
    png.write_bytes(b"fake-png")

    resources = {
        branding.ICON_ICO: ico,
        branding.ICON_PNG: png,
    }

    monkeypatch.setattr(branding.sys, "platform", "win32")
    monkeypatch.setattr(
        branding,
        "_branding_traversable",
        lambda filename: resources[filename],
    )

    calls = []

    class FakeRoot:
        def iconphoto(self, *args, **kwargs):
            calls.append(("iconphoto", args, kwargs))

        def iconbitmap(self, *args, **kwargs):
            calls.append(("iconbitmap", args, kwargs))

        def wm_iconbitmap(self, *args, **kwargs):
            calls.append(("wm_iconbitmap", args, kwargs))

    branding._apply_window_icon_impl(FakeRoot())

    bitmap_calls = [
        call for call in calls if call[0] == "iconbitmap"
    ]

    assert bitmap_calls == [
        ("iconbitmap", (str(ico),), {})
    ]


def test_windows_app_user_model_id_is_applied():
    import langtrust.gui.branding as branding

    calls = []

    class FakeShell32:
        def SetCurrentProcessExplicitAppUserModelID(self, value):
            calls.append(value)

    branding._set_windows_app_user_model_id_impl(FakeShell32())

    assert calls == [branding.WINDOWS_APP_USER_MODEL_ID]
    assert branding.WINDOWS_APP_USER_MODEL_ID == "org.langtrust.gui"


def test_windows_app_user_model_id_failure_is_nonfatal(monkeypatch):
    import langtrust.gui.branding as branding

    monkeypatch.setattr(branding.sys, "platform", "win32")

    def boom():
        raise OSError("Windows shell unavailable")

    monkeypatch.setattr(
        branding,
        "_set_windows_app_user_model_id_impl",
        boom,
    )

    branding.set_windows_app_user_model_id()


def test_windows_app_user_model_id_is_set_before_tk_root():
    from pathlib import Path

    source = Path("src/langtrust/gui/app.py").read_text(encoding="utf-8")

    app_id_call = source.index("    set_windows_app_user_model_id()\n")
    tk_root = source.index("    root = tk.Tk()\n")

    assert app_id_call < tk_root
