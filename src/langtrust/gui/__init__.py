"""LangTrust offline GUI package.

Tkinter is imported only when the GUI is launched, not at package import time.
"""

from __future__ import annotations

__all__ = ["GUI_REQUIRES_TKINTER_MESSAGE", "ensure_tkinter_available"]

GUI_REQUIRES_TKINTER_MESSAGE = (
    "LangTrust GUI requires Python with Tkinter support "
    "(the standard library Tk bindings). "
    "Install a Python build that includes Tk, then re-run langtrust-gui. "
    "Core CLI tools (langtrust-benchmark, langtrust-analyze) do not need Tkinter."
)


def ensure_tkinter_available() -> None:
    """Raise ImportError with a user-facing message if Tkinter is missing."""
    try:
        import tkinter  # noqa: F401
    except ImportError as exc:  # pragma: no cover - exercised in tests via stub
        raise ImportError(GUI_REQUIRES_TKINTER_MESSAGE) from exc
