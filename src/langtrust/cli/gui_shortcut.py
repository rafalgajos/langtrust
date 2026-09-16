"""Create or remove a LangTrust desktop launcher for the current environment."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from langtrust.gui.shortcut import (
    ShortcutError,
    create_shortcut,
    plan_shortcut,
    remove_shortcut,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="langtrust-gui-shortcut",
        description=(
            "Create or remove a native desktop launcher for the LangTrust GUI "
            "bound to this Python environment."
        ),
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--remove",
        action="store_true",
        help="Remove the LangTrust launcher previously created by this command",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing LangTrust-owned launcher",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        plan = plan_shortcut(python_executable=Path(sys.executable))
        if args.remove:
            if args.force:
                print(
                    "Note: --force is ignored with --remove",
                    file=sys.stderr,
                )
            removed = remove_shortcut(plan)
            print(f"Removed LangTrust launcher: {removed}")
            return 0

        path = create_shortcut(plan, force=args.force)
        print(f"Created LangTrust launcher: {path}")
        if plan.platform == "linux":
            print(
                "Note: some Linux desktops require you to mark new .desktop "
                "files as trusted/allowed before they launch."
            )
        elif plan.platform == "darwin":
            print(
                "Note: this is an unsigned minimal .app bound to the current "
                "Python environment (not a system installer)."
            )
        return 0
    except ShortcutError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
