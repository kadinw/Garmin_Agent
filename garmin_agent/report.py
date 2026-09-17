"""Turn Garmin API payloads into Gemini-friendly files and email text."""

from __future__ import annotations

import csv
import io
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

HEALTH_HEADERS = [
    "date",
    "steps",
    "step_goal",
    "distance_meters",
    "floors_ascended",
    "calories_total",
    "calories_active",
    "resting_hr",
    "min_hr",
    "max_hr",
    "avg_stress",
    "body_battery_high",
    "body_battery_low",
    "sleep_hours",
    "sleep_deep_hours",
    "sleep_rem_hours",
    "sleep_light_hours",
    "sleep_score",
    "hrv_last_night_avg",
    "hrv_status",
    "spo2_avg",
    "respiration_avg",
    "vo2_max",
    "training_readiness",
    "training_status",
    "intensity_minutes",
    "weight_kg",
    "body_fat_pct",
    "hydration_ml",
    "bp_systolic",
    "bp_diastolic",
    "activities",
]

ACTIVITY_HEADERS = [
    "date",
    "time",
    "activity_name",
    "sport",
    "duration_sec",
    "distance_m",
    "calories",
    "avg_hr",
    "max_hr",
    "avg_speed_mps",
    "elevation_gain_m",
    "training_effect",
    "aerobic_effect",
    "anaerobic_effect",
    "training_load",
    "avg_power",
    "avg_cadence",
    "activity_id",
]


def json_ready(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_ready(item) for item in value]
    return str(value)


def nested(data: Any, *keys: str, default: Any = None) -> Any:
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
        if current is None:
            return default
    return current


def _hours(seconds: Any) -> Any:
    if not isinstance(seconds, (int, float)) or seconds <= 0:
        return None
    return round(seconds / 3600, 2)


def _first_present(data: Any, *paths: tuple[str, ...]) -> Any:
    for path in paths:
        value = nested(data, *path)
        if value is not None:
            return value
    return None


def _body_battery_range(payload: Any) -> tuple[Any, Any]:
    day_payload = payload
    if isinstance(payload, list) and payload:
        day_payload = payload[0]

    readings: list[int] = []
    if isinstance(day_payload, dict):
        items = day_payload.get("bodyBatteryValuesArray") or day_payload.get("bodyBatteryValues") or []
        charged = day_payload.get("charged")
        drained = day_payload.get("drained")
    elif isinstance(payload, list):
        items = payload
        charged = drained = None
    else:
        items = []
        charged = drained = None

    for item in items:
        if isinstance(item, dict):
            value = item.get("bodyBatteryLevel") or item.get("value")
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            value = item[1]
        else:
            value = item
        if isinstance(value, (int, float)):
            readings.append(int(value))
    if readings:
        return max(readings), min(readings)
    if charged is not None or drained is not None:
        return charged, drained
    return None, None


def _training_readiness_score(payload: Any) -> Any:
    if isinstance(payload, list) and payload:
        payload = payload[0]
    if isinstance(payload, dict):
        return payload.get("score") or payload.get("trainingReadiness") or nested(payload, "level")
    return None


def _training_status(payload: Any) -> Any:
    return _first_present(
        payload,
        ("mostRecentTrainingStatus", "latestTrainingStatusData", "trainingStatus"),
        ("mostRecentTerminatedTrainingStatus", "status"),
        ("trainingStatusData", "status"),
        ("status",),
    )


def _vo2(day: dict[str, Any]) -> Any:
    summary = day.get("user_summary") or {}
    value = nested(summary, "vo2Max") or nested(summary, "vo2MaxPreciseValue")
    if value is not None:
        return value
    max_metrics = day.get("max_metrics")
    items = max_metrics if isinstance(max_metrics, list) else [max_metrics]
    for item in items:
        value = nested(item, "generic", "vo2MaxPreciseValue") or nested(item, "vo2MaxPreciseValue")
        if value is not None:
            return value
    return nested(day.get("training_status") or {}, "vo2MaxValue")


def flatten_day(day: dict[str, Any], activities: list[dict[str, Any]]) -> dict[str, Any]:
    summary = day.get("user_summary") or {}
    sleep = nested(day.get("sleep"), "dailySleepDTO") or {}
    hrv = nested(day.get("hrv"), "hrvSummary") or {}
    body = nested(day.get("body_composition"), "totalAverage") or {}
    spo2 = day.get("spo2") or {}
    respiration = day.get("respiration") or {}
    bp = day.get("blood_pressure") or {}
    hydration = day.get("hydration") or {}
    intensity = day.get("intensity_minutes") or {}
    high_bb, low_bb = _body_battery_range(day.get("body_battery"))
    day_iso = day.get("date")
    names = [
        f"{act.get('activityName', 'Activity')} ({nested(act, 'activityType', 'typeKey', default='unknown')})"
        for act in activities
        if str(act.get("startTimeLocal", ""))[:10] == day_iso
    ]
    systolic = nested(bp, "measurementSummaries", default=[])
    first_bp = systolic[0] if isinstance(systolic, list) and systolic else {}
    measurements = nested(first_bp, "measurements", default=[])
    first_measurement = measurements[0] if isinstance(measurements, list) and measurements else {}

    return {
        "date": day_iso,
        "steps": nested(summary, "totalSteps"),
        "step_goal": nested(summary, "dailyStepGoal"),
        "distance_meters": nested(summary, "totalDistanceMeters"),
        "floors_ascended": nested(summary, "floorsAscended") or nested(day.get("floors") or {}, "floorsAscended"),
        "calories_total": nested(summary, "totalKilocalories"),
        "calories_active": nested(summary, "activeKilocalories"),
        "resting_hr": nested(summary, "restingHeartRate"),
        "min_hr": nested(summary, "minHeartRate"),
        "max_hr": nested(summary, "maxHeartRate"),
        "avg_stress": nested(summary, "averageStressLevel"),
        "body_battery_high": high_bb,
        "body_battery_low": low_bb,
        "sleep_hours": _hours(nested(sleep, "sleepTimeSeconds")),
        "sleep_deep_hours": _hours(nested(sleep, "deepSleepSeconds")),
        "sleep_rem_hours": _hours(nested(sleep, "remSleepSeconds")),
        "sleep_light_hours": _hours(nested(sleep, "lightSleepSeconds")),
        "sleep_score": nested(sleep, "sleepScores", "overall", "value"),
        "hrv_last_night_avg": nested(hrv, "lastNightAvg") or nested(hrv, "weeklyAverage"),
        "hrv_status": nested(hrv, "status"),
        "spo2_avg": nested(spo2, "averageSpO2") or nested(spo2, "latestSpO2") or nested(summary, "averageSpO2"),
        "respiration_avg": nested(respiration, "avgSleepRespirationValue")
        or nested(respiration, "avgWakingRespirationValue")
        or nested(summary, "averageRespirationValue"),
        "vo2_max": _vo2(day),
        "training_readiness": _training_readiness_score(day.get("training_readiness")),
        "training_status": _training_status(day.get("training_status")),
        "intensity_minutes": nested(intensity, "weeklyAverage")
        or nested(intensity, "moderateValue")
        or nested(summary, "moderateIntensityMinutes"),
        "weight_kg": _kg(nested(body, "weight")),
        "body_fat_pct": nested(body, "bodyFat"),
        "hydration_ml": nested(hydration, "valueInML") or nested(hydration, "goalInML"),
        "bp_systolic": nested(first_measurement, "systolic") or nested(first_bp, "highSystolic"),
        "bp_diastolic": nested(first_measurement, "diastolic") or nested(first_bp, "highDiastolic"),
        "activities": "; ".join(names),
    }


def _kg(grams: Any) -> Any:
    if not isinstance(grams, (int, float)) or grams <= 0:
        return None
    return round(grams / 1000, 2)


def flatten_activity(activity: dict[str, Any]) -> dict[str, Any]:
    start_local = str(activity.get("startTimeLocal") or "")
    return {
        "date": start_local[:10],
        "time": start_local[11:],
        "activity_name": activity.get("activityName"),
        "sport": nested(activity, "activityType", "typeKey"),
        "duration_sec": activity.get("duration"),
        "distance_m": activity.get("distance"),
        "calories": activity.get("calories"),
        "avg_hr": activity.get("averageHR"),
        "max_hr": activity.get("maxHR"),
        "avg_speed_mps": activity.get("averageSpeed"),
        "elevation_gain_m": activity.get("elevationGain") or activity.get("totalAscent"),
        "training_effect": activity.get("trainingEffectLabel"),
        "aerobic_effect": activity.get("aerobicTrainingEffect"),
        "anaerobic_effect": activity.get("anaerobicTrainingEffect"),
        "training_load": activity.get("activityTrainingLoad"),
        "avg_power": activity.get("avgPower") or activity.get("averagePower"),
        "avg_cadence": activity.get("averageCadence") or activity.get("avgCadence"),
        "activity_id": activity.get("activityId"),
    }


def rows_to_csv(headers: list[str], rows: list[dict[str, Any]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: "" if row.get(key) is None else row.get(key) for key in headers})
    return buffer.getvalue()


def build_files(report: dict[str, Any]) -> dict[str, str]:
    activities = report.get("activities") or []
    health_rows = [flatten_day(day, activities) for day in report.get("days") or []]
    activity_rows = [flatten_activity(act) for act in activities if isinstance(act, dict)]
    return {
        "garmin_full.json": json.dumps(json_ready(report), indent=2, ensure_ascii=False),
        "garmin_health.csv": rows_to_csv(HEALTH_HEADERS, health_rows),
        "garmin_activities.csv": rows_to_csv(ACTIVITY_HEADERS, activity_rows),
    }


def write_files(files: dict[str, str], output_dir: Path, stamp: str) -> list[Path]:
    written: list[Path] = []
    for name, content in files.items():
        path = output_dir / f"{stamp}_{name}"
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def format_metric(value: Any, suffix: str = "") -> str:
    if value in (None, ""):
        return "n/a"
    return f"{value}{suffix}"


def email_body(report: dict[str, Any], health_rows: list[dict[str, Any]]) -> str:
    end = report.get("lookback_end")
    start = report.get("lookback_start")
    latest = health_rows[-1] if health_rows else {}
    error_count = len(report.get("errors") or [])
    activity_count = len(report.get("activities") or [])
    name = nested(report, "profile", "full_name") or "Garmin user"

    return f"""Garmin daily export for Gemini

Subject person: {name}
Complete day: {end}
Trend window: {start} through {end}
Activities in window: {activity_count}
Endpoints that returned no data or an error: {error_count}

Snapshot for {end}:
- Steps: {format_metric(latest.get("steps"))}
- Active calories: {format_metric(latest.get("calories_active"), " kcal")}
- Resting HR: {format_metric(latest.get("resting_hr"), " bpm")}
- Sleep: {format_metric(latest.get("sleep_hours"), " hr")} (score {format_metric(latest.get("sleep_score"))})
- HRV last night: {format_metric(latest.get("hrv_last_night_avg"))} ({format_metric(latest.get("hrv_status"))})
- Body battery high/low: {format_metric(latest.get("body_battery_high"))} / {format_metric(latest.get("body_battery_low"))}
- Avg stress: {format_metric(latest.get("avg_stress"))}
- Training readiness: {format_metric(latest.get("training_readiness"))}
- Training status: {format_metric(latest.get("training_status"))}
- Activities: {format_metric(latest.get("activities"))}

Analyze this export as a personal fitness coach. Use the CSV attachments for trends and the JSON attachment for full Garmin detail. Cover recovery, sleep, HRV, training load, and what to do today. Flag anything that looks like accumulating fatigue or incomplete data.

Attachments:
- garmin_health.csv: one row per day
- garmin_activities.csv: workouts in the lookback window
- garmin_full.json: raw Garmin payloads for the same window
"""
