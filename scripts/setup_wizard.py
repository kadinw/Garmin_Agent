#!/usr/bin/env python3
"""Open the Garmin Agent setup and settings window."""

from __future__ import annotations

import sys
from pathlib import Path


def _add_project_to_path() -> None:
    if getattr(sys, "frozen", False):
        here = Path(sys.executable).resolve().parent
    else:
        here = Path(__file__).resolve().parent.parent
    for candidate in (here, here.parent):
        if (candidate / "run_daily.py").is_file() and str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))
            return
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))


_add_project_to_path()

from garmin_agent.gui import run_app

if __name__ == "__main__":
    run_app()
