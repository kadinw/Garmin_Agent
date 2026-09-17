"""Load local secrets and project paths."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SECRETS_FILE = ROOT / "secrets" / ".env.txt"


@dataclass(frozen=True)
class Settings:
    email: str
    garmin_password: str
    smtp_password: str
    recipient: str
    smtp_host: str
    smtp_port: int
    token_dir: Path
    output_dir: Path
    logs_dir: Path


def _nonempty_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines


def load_settings() -> Settings:
    if not SECRETS_FILE.is_file():
        raise FileNotFoundError(
            f"Missing {SECRETS_FILE}. Create it with the Garmin email on line 1 "
            "and the Garmin password on line 2. See secrets/.env.example.txt."
        )

    lines = _nonempty_lines(SECRETS_FILE.read_text(encoding="utf-8"))
    if len(lines) < 2:
        raise ValueError(
            "secrets/.env.txt must contain the Garmin email on line 1 "
            "and the Garmin Connect password on line 2."
        )

    email = lines[0]
    garmin_password = lines[1]
    smtp_password = lines[2] if len(lines) >= 3 else garmin_password
    smtp_password = smtp_password.replace(" ", "")

    token_dir = ROOT / "secrets" / ".garminconnect"
    output_dir = ROOT / "output"
    logs_dir = ROOT / "logs"
    output_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    token_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        email=email,
        garmin_password=garmin_password,
        smtp_password=smtp_password,
        recipient=email,
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        token_dir=token_dir,
        output_dir=output_dir,
        logs_dir=logs_dir,
    )
