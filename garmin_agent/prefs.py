"""User preferences for schedule and Garmin data window."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from garmin_agent.paths import project_root

PREFS_FILE = project_root() / "settings.json"


@dataclass
class Prefs:
    schedule_time: str = "07:00"
    lookback_days: int = 7


def load_prefs() -> Prefs:
    if not PREFS_FILE.is_file():
        return Prefs()
    try:
        raw = json.loads(PREFS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return Prefs()
    time_text = str(raw.get("schedule_time") or "07:00")
    try:
        days = int(raw.get("lookback_days") or 7)
    except (TypeError, ValueError):
        days = 7
    return Prefs(schedule_time=_clean_time(time_text), lookback_days=_clean_days(days))


def save_prefs(prefs: Prefs) -> Path:
    PREFS_FILE.write_text(json.dumps(asdict(prefs), indent=2) + "\n", encoding="utf-8")
    return PREFS_FILE


def _clean_days(days: int) -> int:
    return max(1, min(30, days))


def _clean_time(text: str) -> str:
    parts = text.strip().split(":")
    if len(parts) != 2:
        return "07:00"
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError:
        return "07:00"
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return "07:00"
    return f"{hour:02d}:{minute:02d}"
