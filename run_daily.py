#!/usr/bin/env python3
"""Entry point for the daily Garmin export job."""

from garmin_agent.main import main

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)
