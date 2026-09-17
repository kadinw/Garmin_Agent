"""Find the Garmin Agent project folder."""

from __future__ import annotations

import sys
from pathlib import Path


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        here = Path(sys.executable).resolve().parent
    else:
        here = Path(__file__).resolve().parent.parent
    for candidate in (here, here.parent):
        if (candidate / "run_daily.py").is_file():
            return candidate
    return here
