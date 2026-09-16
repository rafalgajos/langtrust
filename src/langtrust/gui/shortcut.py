"""Cross-platform LangTrust desktop-launcher planning and creation.

Filesystem mutations are isolated so tests can exercise plans with tmp_path.
"""

from __future__ import annotations

import os
import plistlib
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from langtrust.gui.branding import (
    ICON_ICNS,
    ICON_ICO,
    ICON_PNG,
    read_branding_bytes,
)

APP_NAME = "LangTrust"
BUNDLE_ID = "org.langtrust.gui"
LINUX_DESKTOP_BASENAME = "LangTrust.desktop"
WINDOWS_LNK_BASENAME = "LangTrust.lnk"
MACOS_APP_BASENAME = "LangTrust.app"
MARKER_FILENAME = ".langtrust-shortcut-owner"
OWNER_MARKER_CONTENTS = "owned-by-langtrust-gui-shortcut\n"
LINUX_OWNER_KEY = "X-LangTrust-Owner=langtrust-gui-shortcut"
WINDOWS_DESCRIPTION_MARKER = "Created by langtrust-gui-shortcut"


@dataclass(frozen=True)
class ShortcutPlan:
    platform: str
    desktop_dir: Path
    launcher_path: Path
    python_executable: Path
    module: str = "langtrust.gui"
    icon_basename: str | None = None
    support_dir: Path | None = None
    persistent_icon_path: Path | None = None


class ShortcutError(RuntimeError):
    """User-facing shortcut failure."""


def detect_platform(platform: str | None = None) -> str:
    p = platform if platform is not None else sys.platform
    if p == "darwin":
        return "darwin"
    if p.startswith("win"):
        return "win32"
    if p.startswith("linux"):
        return "linux"
    raise ShortcutError(f"Unsupported platform for LangTrust desktop shortcuts: {p}")


def prefer_pythonw(executable: Path) -> Path:
    """Prefer pythonw.exe when a matching sibling exists."""
    if executable.name.lower() == "python.exe":
        candidate = executable.with_name("pythonw.exe")
        if candidate.is_file():
            return candidate
    return executable


def resolve_desktop_dir(
    *,
    platform: str,
    home: Path | None = None,
    environ: dict[str, str] | None = None,
) -> Path:
    home = home or Path.home()
    env = environ if environ is not None else dict(os.environ)

    if platform == "darwin":
        return home / "Desktop"
    if platform == "win32":
        userprofile = env.get("USERPROFILE")
        if userprofile:
            return Path(userprofile) / "Desktop"
        return home / "Desktop"
    # linux / XDG
    xdg = env.get("XDG_DESKTOP_DIR")
    if xdg:
        return Path(xdg).expanduser()
    # Try user-dirs.dirs
    config = env.get("XDG_CONFIG_HOME", str(home / ".config"))
    user_dirs = Path(config) / "user-dirs.dirs"
    if user_dirs.is_file():
        try:
            for line in user_dirs.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("XDG_DESKTOP_DIR="):
                    raw = line.split("=", 1)[1].strip().strip('"')
                    raw = raw.replace("$HOME", str(home))
                    return Path(raw)
        except OSError:
            pass
    return home / "Desktop"


def resolve_support_dir(
    *,
    platform: str,
    home: Path | None = None,
    environ: dict[str, str] | None = None,
) -> Path:
    home = home or Path.home()
    env = environ if environ is not None else dict(os.environ)
    if platform == "darwin":
        return home / "Library" / "Application Support" / "LangTrust"
    if platform == "win32":
        local = env.get("LOCALAPPDATA")
        if local:
            return Path(local) / "LangTrust"
        return home / "AppData" / "Local" / "LangTrust"
    # linux
    xdg_data = env.get("XDG_DATA_HOME", str(home / ".local" / "share"))
    return Path(xdg_data) / "langtrust"


def plan_shortcut(
    *,
    platform: str | None = None,
    python_executable: Path | None = None,
    home: Path | None = None,
    environ: dict[str, str] | None = None,
) -> ShortcutPlan:
    plat = detect_platform(platform)
    exe = Path(python_executable or sys.executable)
    if plat == "win32":
        exe = prefer_pythonw(exe)
    desktop = resolve_desktop_dir(platform=plat, home=home, environ=environ)
    support = resolve_support_dir(platform=plat, home=home, environ=environ)

    if plat == "darwin":
        launcher = desktop / MACOS_APP_BASENAME
        icon_name = ICON_ICNS
        persistent = support / ICON_ICNS
    elif plat == "win32":
        launcher = desktop / WINDOWS_LNK_BASENAME
        icon_name = ICON_ICO
        persistent = support / ICON_ICO
    else:
        launcher = desktop / LINUX_DESKTOP_BASENAME
        icon_name = ICON_PNG
        persistent = support / ICON_PNG

    return ShortcutPlan(
        platform=plat,
        desktop_dir=desktop,
        launcher_path=launcher,
        python_executable=exe,
        icon_basename=icon_name,
        support_dir=support,
        persistent_icon_path=persistent,
    )


def ensure_persistent_icon(plan: ShortcutPlan) -> Path:
    if plan.persistent_icon_path is None or plan.icon_basename is None:
        raise ShortcutError("No persistent icon configured for this platform")
    support = plan.support_dir
    assert support is not None
    support.mkdir(parents=True, exist_ok=True)
    target = plan.persistent_icon_path
    target.write_bytes(read_branding_bytes(plan.icon_basename))
    marker = support / MARKER_FILENAME
    if not marker.exists():
        marker.write_text(OWNER_MARKER_CONTENTS, encoding="utf-8")
    return target


def _quote_for_desktop_exec(path: Path) -> str:
    # Freedesktop: escape \, ", and wrap if needed.
    text = str(path)
    if any(ch.isspace() for ch in text) or any(ch in text for ch in '\\"$`'):
        escaped = text.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return text


def render_linux_desktop(plan: ShortcutPlan, icon_path: Path) -> str:
    py = _quote_for_desktop_exec(plan.python_executable)
    icon = _quote_for_desktop_exec(icon_path)
    # Exec: python -m langtrust.gui
    exec_line = f"{py} -m {plan.module}"
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={APP_NAME}\n"
        "Comment=LangTrust research GUI\n"
        f"Exec={exec_line}\n"
        f"Icon={icon}\n"
        "Terminal=false\n"
        "Categories=Development;Science;\n"
        "StartupNotify=true\n"
        "X-LangTrust-Owner=langtrust-gui-shortcut\n"
    )


def render_macos_wrapper(plan: ShortcutPlan) -> str:
    py = str(plan.python_executable)
    # POSIX shell quoting via single quotes + escape embedded singles
    def sh_single(s: str) -> str:
        return "'" + s.replace("'", "'\"'\"'") + "'"

    return (
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        f"exec {sh_single(py)} -m {plan.module}\n"
    )


def render_macos_plist() -> bytes:
    data = {
        "CFBundleName": APP_NAME,
        "CFBundleDisplayName": APP_NAME,
        "CFBundleIdentifier": BUNDLE_ID,
        "CFBundleExecutable": "langtrust",
        "CFBundleIconFile": "langtrust.icns",
        "CFBundlePackageType": "APPL",
        "CFBundleVersion": "1.0",
        "CFBundleShortVersionString": "1.0",
        "LSMinimumSystemVersion": "11.0",
    }
    return plistlib.dumps(data)


def _ps_quote(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def find_powershell(
    *,
    runner: Callable[..., subprocess.CompletedProcess] | None = None,
) -> str:
    """Return an available PowerShell executable name."""
    run = runner or subprocess.run
    for name in ("powershell", "pwsh"):
        try:
            result = run(
                [name, "-NoProfile", "-NonInteractive", "-Command", "exit 0"],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            continue
        except OSError as exc:
            raise ShortcutError(
                f"Unable to start PowerShell ({name}): {exc}"
            ) from exc
        if result.returncode == 0:
            return name
    raise ShortcutError(
        "PowerShell is not available (tried 'powershell' and 'pwsh'); "
        "cannot create or inspect Windows .lnk shortcuts"
    )


def read_windows_shortcut_description(
    link_path: Path,
    *,
    runner: Callable[..., subprocess.CompletedProcess] | None = None,
) -> str:
    run = runner or subprocess.run
    try:
        ps = find_powershell(runner=run)
    except ShortcutError:
        raise
    script = (
        "$ErrorActionPreference = 'Stop';\n"
        f"$w = New-Object -ComObject WScript.Shell;\n"
        f"$s = $w.CreateShortcut({_ps_quote(str(link_path))});\n"
        "Write-Output $s.Description;\n"
    )
    try:
        result = run(
            [ps, "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ShortcutError(
            "PowerShell is not available; cannot inspect Windows .lnk shortcuts"
        ) from exc
    except OSError as exc:
        raise ShortcutError(
            f"Unable to start PowerShell to inspect shortcut: {exc}"
        ) from exc
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip()
        raise ShortcutError(
            "Failed to inspect Windows shortcut ownership"
            + (f": {err}" if err else "")
        )
    return (result.stdout or "").strip()


def validate_owned_launcher(
    plan: ShortcutPlan,
    *,
    windows_runner: Callable[..., subprocess.CompletedProcess] | None = None,
) -> None:
    """Refuse foreign launchers. No-op when the path does not exist."""
    path = plan.launcher_path
    name = path.name

    if plan.platform == "darwin":
        if name != MACOS_APP_BASENAME:
            raise ShortcutError(f"Refusing to touch unexpected path: {path}")
        if path.is_symlink():
            raise ShortcutError(
                f"Refusing to touch LangTrust.app symlink (not owned): {path}"
            )
        if not path.exists():
            return
        if not path.is_dir():
            raise ShortcutError(f"Expected an application bundle at {path}")
        marker = path / "Contents" / "Resources" / MARKER_FILENAME
        if not marker.is_file():
            raise ShortcutError(
                f"Existing .app is not owned by langtrust-gui-shortcut "
                f"(missing {MARKER_FILENAME}): {path}"
            )
        contents = marker.read_text(encoding="utf-8")
        if contents != OWNER_MARKER_CONTENTS:
            raise ShortcutError(
                f"Existing .app ownership marker mismatch: {path}"
            )
        return

    if plan.platform == "win32":
        if name != WINDOWS_LNK_BASENAME:
            raise ShortcutError(f"Refusing to touch unexpected path: {path}")
        if path.is_symlink():
            raise ShortcutError(
                f"Refusing to touch LangTrust.lnk symlink (not owned): {path}"
            )
        if not path.exists():
            return
        description = read_windows_shortcut_description(
            path, runner=windows_runner
        )
        if description != WINDOWS_DESCRIPTION_MARKER:
            raise ShortcutError(
                f"Existing .lnk is not owned by langtrust-gui-shortcut: {path}"
            )
        return

    if name != LINUX_DESKTOP_BASENAME:
        raise ShortcutError(f"Refusing to touch unexpected path: {path}")
    if path.is_symlink():
        raise ShortcutError(
            f"Refusing to touch LangTrust.desktop symlink (not owned): {path}"
        )
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = [line.strip() for line in text.splitlines()]
    if LINUX_OWNER_KEY not in lines:
        raise ShortcutError(
            f"Existing desktop file is not owned by langtrust-gui-shortcut: {path}"
        )


def create_linux_shortcut(plan: ShortcutPlan, *, force: bool = False) -> Path:
    validate_owned_launcher(plan)
    if plan.launcher_path.exists() and not force:
        raise ShortcutError(
            f"Launcher already exists: {plan.launcher_path} (use --force to replace)"
        )
    icon = ensure_persistent_icon(plan)
    plan.desktop_dir.mkdir(parents=True, exist_ok=True)
    content = render_linux_desktop(plan, icon)
    plan.launcher_path.write_text(content, encoding="utf-8")
    mode = plan.launcher_path.stat().st_mode
    plan.launcher_path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return plan.launcher_path


def create_macos_shortcut(plan: ShortcutPlan, *, force: bool = False) -> Path:
    validate_owned_launcher(plan)
    if plan.launcher_path.exists() and not force:
        raise ShortcutError(
            f"Launcher already exists: {plan.launcher_path} (use --force to replace)"
        )
    if plan.launcher_path.exists() and force:
        shutil.rmtree(plan.launcher_path)

    app = plan.launcher_path
    contents = app / "Contents"
    macos = contents / "MacOS"
    resources = contents / "Resources"
    macos.mkdir(parents=True, exist_ok=True)
    resources.mkdir(parents=True, exist_ok=True)

    wrapper = macos / "langtrust"
    wrapper.write_text(render_macos_wrapper(plan), encoding="utf-8")
    wrapper.chmod(wrapper.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    (contents / "Info.plist").write_bytes(render_macos_plist())
    (resources / ICON_ICNS).write_bytes(read_branding_bytes(ICON_ICNS))
    (resources / MARKER_FILENAME).write_text(
        OWNER_MARKER_CONTENTS, encoding="utf-8"
    )
    ensure_persistent_icon(plan)
    return app


def create_windows_shortcut(
    plan: ShortcutPlan,
    *,
    force: bool = False,
    runner: Callable[..., subprocess.CompletedProcess] | None = None,
) -> Path:
    validate_owned_launcher(plan, windows_runner=runner)
    if plan.launcher_path.exists() and not force:
        raise ShortcutError(
            f"Launcher already exists: {plan.launcher_path} (use --force to replace)"
        )
    icon = ensure_persistent_icon(plan)
    plan.desktop_dir.mkdir(parents=True, exist_ok=True)

    target = str(plan.python_executable)
    arguments = f"-m {plan.module}"
    link = str(plan.launcher_path)
    icon_loc = str(icon)

    script = (
        "$ErrorActionPreference = 'Stop';\n"
        f"$w = New-Object -ComObject WScript.Shell;\n"
        f"$s = $w.CreateShortcut({_ps_quote(link)});\n"
        f"$s.TargetPath = {_ps_quote(target)};\n"
        f"$s.Arguments = {_ps_quote(arguments)};\n"
        f"$s.Description = {_ps_quote(WINDOWS_DESCRIPTION_MARKER)};\n"
        f"$s.IconLocation = {_ps_quote(icon_loc + ',0')};\n"
        f"$s.WorkingDirectory = {_ps_quote(str(plan.python_executable.parent))};\n"
        "$s.Save();\n"
    )
    run = runner or subprocess.run
    try:
        ps = find_powershell(runner=run)
    except ShortcutError:
        raise
    try:
        result = run(
            [ps, "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ShortcutError(
            "PowerShell is not available; cannot create Windows .lnk shortcuts"
        ) from exc
    except OSError as exc:
        raise ShortcutError(
            f"Unable to start PowerShell to create shortcut: {exc}"
        ) from exc
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip()
        raise ShortcutError(
            "Failed to create Windows shortcut via PowerShell"
            + (f": {err}" if err else "")
        )
    if not plan.launcher_path.is_file():
        raise ShortcutError(
            f"PowerShell reported success but shortcut was not created: "
            f"{plan.launcher_path}"
        )
    return plan.launcher_path



def create_shortcut(
    plan: ShortcutPlan,
    *,
    force: bool = False,
    windows_runner: Callable[..., subprocess.CompletedProcess] | None = None,
) -> Path:
    if plan.platform == "darwin":
        return create_macos_shortcut(plan, force=force)
    if plan.platform == "win32":
        return create_windows_shortcut(plan, force=force, runner=windows_runner)
    if plan.platform == "linux":
        return create_linux_shortcut(plan, force=force)
    raise ShortcutError(f"Unsupported platform: {plan.platform}")


def remove_shortcut(
    plan: ShortcutPlan,
    *,
    windows_runner: Callable[..., subprocess.CompletedProcess] | None = None,
) -> Path:
    validate_owned_launcher(plan, windows_runner=windows_runner)
    path = plan.launcher_path
    if not path.exists() and not path.is_symlink():
        raise ShortcutError(f"No LangTrust launcher found at {path}")
    if plan.platform == "darwin":
        if path.resolve() == plan.desktop_dir.resolve():
            raise ShortcutError("Refusing to delete the Desktop directory")
        if path.name != MACOS_APP_BASENAME:
            raise ShortcutError(f"Refusing to delete unexpected path: {path}")
        if path.is_symlink():
            raise ShortcutError(
                f"Refusing to delete LangTrust.app symlink: {path}"
            )
        shutil.rmtree(path)
        return path
    if path.name not in {LINUX_DESKTOP_BASENAME, WINDOWS_LNK_BASENAME}:
        raise ShortcutError(f"Refusing to delete unexpected path: {path}")
    path.unlink()
    return path
