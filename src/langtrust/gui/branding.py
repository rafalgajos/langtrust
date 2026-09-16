"""Packaged LangTrust branding helpers for the Tk GUI.

Icon application must never prevent GUI launch.
"""

from __future__ import annotations

import sys
from importlib.resources import as_file, files
from typing import Any

RESOURCES_PACKAGE = "langtrust.resources"
BRANDING_DIR = "branding"
ICON_PNG = "langtrust.png"
ICON_ICO = "langtrust.ico"
ICON_ICNS = "langtrust.icns"
ICON_SVG = "langtrust.svg"
BRANDING_FILENAMES = (ICON_SVG, ICON_PNG, ICON_ICO, ICON_ICNS)
WINDOWS_APP_USER_MODEL_ID = "org.langtrust.gui"

# Keep PhotoImage references alive for the Tk process lifetime.
_PHOTO_REFS: list[Any] = []


def _branding_traversable(filename: str):
    if filename not in BRANDING_FILENAMES:
        raise FileNotFoundError(f"Unknown branding asset: {filename}")
    return files(RESOURCES_PACKAGE).joinpath(BRANDING_DIR, filename)


def read_branding_bytes(filename: str) -> bytes:
    return _branding_traversable(filename).read_bytes()


def set_windows_app_user_model_id() -> None:
    """Set a stable Windows taskbar identity. Failures are non-fatal."""
    if not sys.platform.startswith("win"):
        return

    try:
        _set_windows_app_user_model_id_impl()
    except Exception:
        return


def _set_windows_app_user_model_id_impl(shell32=None) -> None:
    if shell32 is None:
        import ctypes

        shell32 = ctypes.windll.shell32

    shell32.SetCurrentProcessExplicitAppUserModelID(
        WINDOWS_APP_USER_MODEL_ID
    )


def apply_window_icon(root) -> None:
    """Apply LangTrust icon to a Tk root. Failures are swallowed."""
    try:
        _apply_window_icon_impl(root)
    except Exception:
        return


def _apply_window_icon_impl(root) -> None:
    platform = sys.platform

    # Cross-platform Tk icon.
    png_res = _branding_traversable(ICON_PNG)
    with as_file(png_res) as png_path:
        try:
            from tkinter import PhotoImage

            photo = PhotoImage(file=str(png_path))
            _PHOTO_REFS.append(photo)
            root.iconphoto(True, photo)
        except Exception:
            pass

    # On Windows, apply the native ICO to the current root window last.
    # Passing the ICO as the positional bitmap sets the current window;
    # using only default= does not reliably replace the root-window icon.
    if platform.startswith("win"):
        ico_res = _branding_traversable(ICON_ICO)
        with as_file(ico_res) as ico_path:
            try:
                root.iconbitmap(str(ico_path))
            except Exception:
                try:
                    root.wm_iconbitmap(str(ico_path))
                except Exception:
                    pass
