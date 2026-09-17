"""CLI for the once-a-day Garmin export."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, timedelta

from garmin_agent.config import load_settings
from garmin_agent.garmin import collect_report, login
from garmin_agent.mailer import send_report
from garmin_agent.report import build_files, email_body, flatten_day, write_files


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download Garmin watch data and email it for Gemini analysis."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of complete days to include, ending yesterday (default: 7).",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="End date YYYY-MM-DD. Defaults to yesterday so the day is complete.",
    )
    parser.add_argument(
        "--no-email",
        action="store_true",
        help="Write local files only; do not send email.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Log Garmin endpoint failures at debug level.",
    )
    return parser.parse_args(argv)


def configure_logging(settings, verbose: bool) -> None:
    log_path = settings.logs_dir / "garmin_agent.log"
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.days < 1:
        print("--days must be at least 1", file=sys.stderr)
        return 2

    settings = load_settings()
    configure_logging(settings, args.verbose)
    logger = logging.getLogger("garmin_agent")

    end_day = date.fromisoformat(args.date) if args.date else date.today() - timedelta(days=1)
    logger.info("Collecting Garmin data through %s (%s day window)", end_day.isoformat(), args.days)

    client = login(settings)
    report = collect_report(client, end_day, args.days)
    files = build_files(report)
    stamp = f"garmin_{end_day.isoformat()}"
    attachments = write_files(files, settings.output_dir, stamp)
    health_rows = [flatten_day(day, report.get("activities") or []) for day in report.get("days") or []]
    body = email_body(report, health_rows)
    subject = f"Garmin daily report {end_day.isoformat()}"

    logger.info("Wrote %s", ", ".join(path.name for path in attachments))
    if args.no_email:
        logger.info("Skipping email because --no-email was set.")
        return 0

    send_report(settings, subject, body, attachments)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        logging.getLogger("garmin_agent").exception("Daily Garmin job failed")
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
