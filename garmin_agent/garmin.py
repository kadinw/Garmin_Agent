"""Garmin Connect login and data collection."""

from __future__ import annotations

import logging
import sys
import time
from datetime import date, timedelta
from typing import Any, Callable

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

from garmin_agent.config import Settings

LOGGER = logging.getLogger(__name__)

DAILY_ENDPOINTS: tuple[tuple[str, str], ...] = (
    ("user_summary", "get_user_summary"),
    ("stats", "get_stats"),
    ("sleep", "get_sleep_data"),
    ("hrv", "get_hrv_data"),
    ("heart_rates", "get_heart_rates"),
    ("stress", "get_all_day_stress"),
    ("body_battery", "get_body_battery"),
    ("spo2", "get_spo2_data"),
    ("respiration", "get_respiration_data"),
    ("training_readiness", "get_training_readiness"),
    ("training_status", "get_training_status"),
    ("max_metrics", "get_max_metrics"),
    ("body_composition", "get_body_composition"),
    ("intensity_minutes", "get_intensity_minutes_data"),
    ("steps", "get_steps_data"),
    ("floors", "get_floors"),
    ("hydration", "get_hydration_data"),
    ("blood_pressure", "get_blood_pressure"),
)


def _prompt_mfa() -> str:
    if not sys.stdin.isatty():
        raise GarminConnectAuthenticationError(
            "Garmin requested MFA, but this run is unattended. "
            "Run `python scripts/setup_garmin_login.py` once in a terminal to save login tokens."
        )
    return input("Garmin MFA code: ").strip()


def _attach_login_options(client: Garmin) -> None:
    """Prefer the widget SSO flow; mobile login is often IP-rate-limited."""
    inner = getattr(client, "client", None)
    if inner is None:
        return
    inner.skip_strategies = {"mobile+cffi", "mobile+requests"}


def login(settings: Settings) -> Garmin:
    """Reuse saved tokens when possible; otherwise log in with secrets."""
    token_path = str(settings.token_dir)
    try:
        client = Garmin()
        _attach_login_options(client)
        client.login(token_path)
        LOGGER.info("Logged in with saved Garmin tokens.")
        return client
    except (GarminConnectAuthenticationError, GarminConnectConnectionError, FileNotFoundError, OSError) as exc:
        LOGGER.info("Saved Garmin tokens unavailable (%s). Logging in with password.", exc)

    try:
        client = Garmin(
            email=settings.email,
            password=settings.garmin_password,
            prompt_mfa=_prompt_mfa,
        )
        _attach_login_options(client)
        client.login(token_path)
        LOGGER.info("Garmin login succeeded. Tokens saved to %s", token_path)
        return client
    except GarminConnectTooManyRequestsError:
        LOGGER.exception("Garmin rate-limited the login. Wait 15-30 minutes and retry.")
        raise
    except GarminConnectAuthenticationError as exc:
        LOGGER.exception("Garmin login failed.")
        raise GarminConnectAuthenticationError(
            "Garmin rejected the login. Confirm line 1/2 of secrets/.env.txt are the "
            "Garmin Connect email and password (not a Google-only password). "
            "If this account uses Garmin MFA, run "
            "`python scripts/setup_garmin_login.py` once in a terminal. "
            "If Garmin recently returned HTTP 429, wait 15-30 minutes and try again. "
            f"Original error: {exc}"
        ) from exc


def _safe_call(errors: list[dict[str, str]], name: str, func: Callable[..., Any], *args: Any) -> Any:
    try:
        result = func(*args)
        time.sleep(0.25)
        return result
    except GarminConnectTooManyRequestsError:
        errors.append({"endpoint": name, "error": "Garmin rate limit (429)"})
        LOGGER.warning("Rate limited on %s", name)
        time.sleep(5)
        return None
    except Exception as exc:  # garminconnect raises several transport errors
        message = str(exc) or exc.__class__.__name__
        errors.append({"endpoint": name, "error": message})
        LOGGER.debug("Endpoint %s failed: %s", name, message)
        return None


def _call_named(client: Garmin, method_name: str, *args: Any) -> Any:
    method = getattr(client, method_name, None)
    if method is None:
        raise AttributeError(f"{method_name} is not available in this garminconnect version")
    return method(*args)


def collect_day(client: Garmin, day: date, errors: list[dict[str, str]]) -> dict[str, Any]:
    payload: dict[str, Any] = {"date": day.isoformat()}
    iso = day.isoformat()
    for key, method_name in DAILY_ENDPOINTS:
        payload[key] = _safe_call(errors, f"{method_name}:{iso}", _call_named, client, method_name, iso)
    return payload


def collect_report(client: Garmin, end_day: date, lookback_days: int) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    start_day = end_day - timedelta(days=lookback_days - 1)

    profile = {
        "full_name": _safe_call(errors, "get_full_name", getattr(client, "get_full_name", lambda: None)),
        "unit_system": _safe_call(errors, "get_unit_system", getattr(client, "get_unit_system", lambda: None)),
        "user_profile": _safe_call(errors, "get_user_profile", getattr(client, "get_user_profile", lambda: None)),
        "devices": _safe_call(errors, "get_devices", getattr(client, "get_devices", lambda: None)),
    }

    days = []
    current = start_day
    while current <= end_day:
        LOGGER.info("Fetching Garmin data for %s", current.isoformat())
        days.append(collect_day(client, current, errors))
        current += timedelta(days=1)

    activities = _safe_call(
        errors,
        "get_activities_by_date",
        _call_named,
        client,
        "get_activities_by_date",
        start_day.isoformat(),
        end_day.isoformat(),
    ) or []

    calories = _safe_call(
        errors,
        "get_calories_daily",
        _call_named,
        client,
        "get_calories_daily",
        start_day.isoformat(),
        end_day.isoformat(),
    )

    return {
        "generated_at": date.today().isoformat(),
        "lookback_start": start_day.isoformat(),
        "lookback_end": end_day.isoformat(),
        "profile": profile,
        "days": days,
        "activities": activities,
        "calories_daily": calories,
        "errors": errors,
    }
