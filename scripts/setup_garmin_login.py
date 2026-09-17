#!/usr/bin/env python3
"""Interactive first-time Garmin login so later scheduled runs can stay unattended."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from garmin_agent.config import load_settings
from garmin_agent.garmin import login


def main() -> int:
    settings = load_settings()
    print(f"Logging in as {settings.email}...")
    print("If Garmin emails a one-time code, enter it here.")
    login(settings)
    print(f"Success. Tokens saved to {settings.token_dir}")
    print("You can now run:  python run_daily.py")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)
