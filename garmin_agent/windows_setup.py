"""Helpers used by the Windows setup window."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from garmin_agent.paths import project_root

PYTHON_DOWNLOAD = "https://www.python.org/downloads/"
APP_PASSWORD_URL = "https://myaccount.google.com/apppasswords"
TASK_NAME = "Garmin Agent Daily Report"


def find_python() -> list[str] | None:
    commands: list[list[str]] = [
        ["py", "-3.13"],
        ["py", "-3"],
        ["python"],
        ["python3"],
    ]
    local = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Python"
    if local.is_dir():
        for folder in sorted(local.glob("Python3*"), reverse=True):
            exe = folder / "python.exe"
            if exe.is_file():
                commands.append([str(exe)])
    for command in commands:
        try:
            result = subprocess.run(
                [*command, "--version"],
                check=False,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            continue
        if result.returncode == 0:
            return command
    return None


def venv_python(root: Path | None = None) -> Path:
    return (root or project_root()) / ".venv" / "Scripts" / "python.exe"


def ensure_venv() -> Path:
    root = project_root()
    python_exe = venv_python(root)
    if python_exe.is_file():
        return python_exe
    launcher = find_python()
    if launcher is None:
        raise RuntimeError(
            "Python was not found. Install Python from python.org and check "
            "'Add python.exe to PATH', then try again."
        )
    result = subprocess.run([*launcher, "-m", "venv", str(root / ".venv")], cwd=root)
    if result.returncode != 0 or not python_exe.is_file():
        raise RuntimeError("Could not create the program's private Python folder.")
    return python_exe


def install_requirements() -> None:
    root = project_root()
    python_exe = ensure_venv()
    pip = subprocess.run(
        [str(python_exe), "-m", "pip", "install", "--upgrade", "pip"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if pip.returncode != 0:
        raise RuntimeError(pip.stderr or pip.stdout or "pip upgrade failed")
    deps = subprocess.run(
        [str(python_exe), "-m", "pip", "install", "-r", "requirements.txt"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if deps.returncode != 0:
        raise RuntimeError(deps.stderr or deps.stdout or "Could not install libraries.")


def write_secrets(email: str, garmin_password: str, app_password: str) -> Path:
    path = project_root() / "secrets" / ".env.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"{email.strip()}\n{garmin_password.strip()}\n{app_password.strip().replace(' ', '')}\n",
        encoding="utf-8",
    )
    return path


def read_secret_lines() -> list[str]:
    path = project_root() / "secrets" / ".env.txt"
    if not path.is_file():
        return []
    lines: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            lines.append(line)
    return lines


def register_daily_task(time_24h: str) -> None:
    root = project_root()
    installer = root / "scripts" / "install_scheduled_task.ps1"
    result = subprocess.run(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(installer),
            "-Time",
            time_24h,
            "-SkipDeps",
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(detail or "Could not create the Windows daily task.")


def run_garmin_login() -> None:
    root = project_root()
    python_exe = ensure_venv()
    flags = 0
    if os.name == "nt":
        flags = subprocess.CREATE_NEW_CONSOLE
    result = subprocess.run(
        [str(python_exe), str(root / "scripts" / "setup_garmin_login.py")],
        cwd=root,
        creationflags=flags,
    )
    if result.returncode != 0:
        raise RuntimeError("Garmin sign-in did not finish. Check the small black window for the error.")


def run_daily_job() -> str:
    root = project_root()
    python_exe = ensure_venv()
    result = subprocess.run(
        [str(python_exe), str(root / "run_daily.py")],
        cwd=root,
        capture_output=True,
        text=True,
    )
    output = (result.stdout or "") + (result.stderr or "")
    if result.returncode != 0:
        raise RuntimeError(output.strip() or "The daily email job failed.")
    return output
