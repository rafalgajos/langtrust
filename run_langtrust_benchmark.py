"""Compatibility wrapper for the LangTrust benchmark CLI."""

from pathlib import Path

from langtrust.cli.benchmark import main


ROOT = Path(__file__).resolve().parent


if __name__ == "__main__":
    # Preserve repository execution semantics while making both scenario
    # discovery and Git provenance independent of the caller's CWD.
    main(
        ROOT / "scenarios",
        git_repo=ROOT,
    )
