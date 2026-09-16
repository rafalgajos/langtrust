#!/usr/bin/env python3
"""Compatibility wrapper for the LangTrust analysis CLI."""

import sys
from pathlib import Path

from langtrust.cli.analyze import (
    DEFAULT_FOLLOW_PATH,
    DEFAULT_MAIN_PATH,
    DEFAULT_OUTDIR,
    DEFAULT_T0_PATH,
    main,
    run_analysis,
)


ROOT = Path(__file__).resolve().parent


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Preserve the historical repository workflow.
        run_analysis(
            t0_path=ROOT / DEFAULT_T0_PATH,
            main_path=ROOT / DEFAULT_MAIN_PATH,
            follow_path=ROOT / DEFAULT_FOLLOW_PATH,
            outdir=ROOT / DEFAULT_OUTDIR,
        )
    else:
        # Explicit CLI arguments use the caller's paths/CWD.
        main()
