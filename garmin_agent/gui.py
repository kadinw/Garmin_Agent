"""Simple setup and settings window for Garmin Agent."""

from __future__ import annotations

import threading
import tkinter as tk
import webbrowser
from datetime import date, timedelta
from tkinter import messagebox, ttk

from garmin_agent.prefs import Prefs, load_prefs, save_prefs
from garmin_agent.windows_setup import (
    APP_PASSWORD_URL,
    PYTHON_DOWNLOAD,
    TASK_NAME,
    find_python,
    install_requirements,
    read_secret_lines,
    register_daily_task,
    run_daily_job,
    run_garmin_login,
    write_secrets,
)


def split_time(time_24h: str) -> tuple[int, int, str]:
    hour, minute = (int(part) for part in time_24h.split(":"))
    if hour == 0:
        return 12, minute, "AM"
    if hour == 12:
        return 12, minute, "PM"
    if hour > 12:
        return hour - 12, minute, "PM"
    return hour, minute, "AM"


def to_24h(hour_12: int, minute: int, ampm: str) -> str:
    hour = hour_12
    if ampm == "AM":
        if hour == 12:
            hour = 0
    elif hour != 12:
        hour += 12
    return f"{hour:02d}:{minute:02d}"


class GarminAgentApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Garmin Agent")
        self.minsize(560, 640)
        self.geometry("620x720")
        self.busy = False

        prefs = load_prefs()
        secrets = read_secret_lines()
        hour, minute, ampm = split_time(prefs.schedule_time)

        pad = {"padx": 16, "pady": 6}
        main = ttk.Frame(self, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Garmin Agent", font=("Segoe UI", 18, "bold")).pack(anchor="w", **pad)
        ttk.Label(
            main,
            text="This window saves your passwords, chooses when the email goes out, and chooses how many days of watch data to include.",
            wraplength=560,
        ).pack(anchor="w", **pad)

        account = ttk.LabelFrame(main, text="Your accounts", padding=12)
        account.pack(fill=tk.X, **pad)

        self.email_var = tk.StringVar(value=secrets[0] if secrets else "")
        self.garmin_var = tk.StringVar(value=secrets[1] if len(secrets) > 1 else "")
        self.app_var = tk.StringVar(value=secrets[2] if len(secrets) > 2 else "")

        self._labeled_entry(account, "Gmail address (also used for Garmin)", self.email_var)
        self._labeled_entry(account, "Garmin password", self.garmin_var, secret=True)
        self._labeled_entry(account, "Gmail App Password (16 letters from Google)", self.app_var, secret=True)
        ttk.Button(account, text="Open the Gmail App Password page", command=self._open_app_passwords).pack(
            anchor="w", pady=(8, 0)
        )

        schedule = ttk.LabelFrame(main, text="When to send the email", padding=12)
        schedule.pack(fill=tk.X, **pad)
        ttk.Label(
            schedule,
            text="Windows will send the Garmin email at this time every day. Your computer should be on, and you should be signed in.",
            wraplength=540,
        ).pack(anchor="w")

        time_row = ttk.Frame(schedule)
        time_row.pack(anchor="w", pady=8)
        ttk.Label(time_row, text="Hour").pack(side=tk.LEFT)
        self.hour_var = tk.IntVar(value=hour)
        ttk.Spinbox(time_row, from_=1, to=12, width=4, textvariable=self.hour_var).pack(side=tk.LEFT, padx=(6, 12))
        ttk.Label(time_row, text="Minute").pack(side=tk.LEFT)
        self.minute_var = tk.IntVar(value=minute)
        ttk.Spinbox(time_row, from_=0, to=59, width=4, textvariable=self.minute_var, format="%02.0f").pack(
            side=tk.LEFT, padx=(6, 12)
        )
        self.ampm_var = tk.StringVar(value=ampm)
        ttk.Radiobutton(time_row, text="AM", variable=self.ampm_var, value="AM").pack(side=tk.LEFT)
        ttk.Radiobutton(time_row, text="PM", variable=self.ampm_var, value="PM").pack(side=tk.LEFT)

        window = ttk.LabelFrame(main, text="How much Garmin data to include", padding=12)
        window.pack(fill=tk.X, **pad)
        ttk.Label(
            window,
            text="Each email always ends with yesterday (today is still incomplete). Choose how many past days to attach.",
            wraplength=540,
        ).pack(anchor="w")
        days_row = ttk.Frame(window)
        days_row.pack(anchor="w", pady=8)
        ttk.Label(days_row, text="Days of data").pack(side=tk.LEFT)
        self.days_var = tk.IntVar(value=prefs.lookback_days)
        days_box = ttk.Spinbox(
            days_row,
            from_=1,
            to=30,
            width=5,
            textvariable=self.days_var,
            command=self._update_range_label,
        )
        days_box.pack(side=tk.LEFT, padx=8)
        days_box.bind("<KeyRelease>", lambda _event: self._update_range_label())
        ttk.Label(days_row, text="(1 is yesterday only, 7 is about a week)").pack(side=tk.LEFT)
        self.range_label = ttk.Label(window, text="")
        self.range_label.pack(anchor="w")
        self._update_range_label()

        buttons = ttk.Frame(main)
        buttons.pack(fill=tk.X, **pad)
        ttk.Button(buttons, text="Save and turn on the daily email", command=self._save_and_schedule).pack(
            fill=tk.X, pady=3
        )
        ttk.Button(buttons, text="Sign in to Garmin (needed once)", command=self._garmin_login).pack(
            fill=tk.X, pady=3
        )
        ttk.Button(buttons, text="Send a test email now", command=self._test_email).pack(fill=tk.X, pady=3)

        self.status = tk.StringVar(value="Fill in the boxes, then click Save.")
        ttk.Label(main, textvariable=self.status, wraplength=560, foreground="#333333").pack(
            anchor="w", **pad
        )

        if find_python() is None:
            self.status.set("Python was not found. Install it from python.org and check Add python.exe to PATH.")

    def _labeled_entry(self, parent: ttk.LabelFrame, label: str, variable: tk.StringVar, secret: bool = False) -> None:
        ttk.Label(parent, text=label).pack(anchor="w", pady=(8, 0))
        entry = ttk.Entry(parent, textvariable=variable, show="*" if secret else "")
        entry.pack(fill=tk.X)

    def _open_app_passwords(self) -> None:
        webbrowser.open(APP_PASSWORD_URL)

    def _current_prefs(self) -> Prefs:
        hour = int(self.hour_var.get())
        minute = int(self.minute_var.get())
        days = int(self.days_var.get())
        if hour < 1 or hour > 12 or minute < 0 or minute > 59:
            raise ValueError("Choose an hour from 1 to 12 and minutes from 0 to 59.")
        if days < 1 or days > 30:
            raise ValueError("Days of data must be between 1 and 30.")
        return Prefs(schedule_time=to_24h(hour, minute, self.ampm_var.get()), lookback_days=days)

    def _update_range_label(self) -> None:
        try:
            days = int(self.days_var.get())
        except (tk.TclError, ValueError):
            return
        days = max(1, min(30, days))
        end = date.today() - timedelta(days=1)
        start = end - timedelta(days=days - 1)
        if days == 1:
            text = f"The next email will include {end.isoformat()} only."
        else:
            text = f"The next email will include {start.isoformat()} through {end.isoformat()}."
        self.range_label.configure(text=text)

    def _save_secrets(self) -> None:
        email = self.email_var.get().strip()
        garmin = self.garmin_var.get().strip()
        app = self.app_var.get().strip()
        if "@" not in email:
            raise ValueError("Enter a Gmail address, such as you@gmail.com.")
        if not garmin:
            raise ValueError("Enter your Garmin password.")
        if not app:
            raise ValueError("Enter the Gmail App Password from Google.")
        write_secrets(email, garmin, app)

    def _set_busy(self, message: str) -> None:
        self.busy = True
        self.status.set(message)
        self.configure(cursor="watch")
        self.update_idletasks()

    def _clear_busy(self) -> None:
        self.busy = False
        self.configure(cursor="")

    def _background(self, work, success: str) -> None:
        if self.busy:
            return

        def runner() -> None:
            try:
                work()
            except Exception as exc:
                self.after(0, lambda: self._done(False, str(exc)))
            else:
                self.after(0, lambda: self._done(True, success))

        threading.Thread(target=runner, daemon=True).start()

    def _done(self, ok: bool, message: str) -> None:
        self._clear_busy()
        self.status.set(message)
        if ok:
            messagebox.showinfo("Garmin Agent", message)
        else:
            messagebox.showerror("Garmin Agent", message)

    def _save_and_schedule(self) -> None:
        try:
            self._save_secrets()
            prefs = self._current_prefs()
            save_prefs(prefs)
        except Exception as exc:
            messagebox.showerror("Garmin Agent", str(exc))
            return
        if find_python() is None:
            if messagebox.askyesno("Python needed", "Python was not found. Open the download page?"):
                webbrowser.open(PYTHON_DOWNLOAD)
            return
        self._set_busy("Saving settings and creating the daily Windows task. Please wait...")

        def work() -> None:
            install_requirements()
            register_daily_task(prefs.schedule_time)

        readable = split_time(prefs.schedule_time)
        success = (
            f"Saved. Windows will email you every day at {readable[0]}:{readable[1]:02d} {readable[2]}. "
            f"Each email will include {prefs.lookback_days} day(s) of Garmin data. "
            f"The task name is '{TASK_NAME}'."
        )
        self._background(work, success)

    def _garmin_login(self) -> None:
        try:
            self._save_secrets()
        except Exception as exc:
            messagebox.showerror("Garmin Agent", str(exc))
            return
        messagebox.showinfo(
            "Garmin sign-in",
            "A small black window will open. If Garmin emails a one-time code, type it there and press Enter.",
        )
        self._set_busy("Waiting for Garmin sign-in...")
        self._background(run_garmin_login, "Garmin sign-in finished. You can send a test email now.")

    def _test_email(self) -> None:
        try:
            self._save_secrets()
            prefs = self._current_prefs()
            save_prefs(prefs)
        except Exception as exc:
            messagebox.showerror("Garmin Agent", str(exc))
            return
        self._set_busy("Collecting Garmin data and sending a test email. This can take a minute...")
        self._background(run_daily_job, "Test email sent. Check your Gmail inbox and spam folder.")


def run_app() -> None:
    app = GarminAgentApp()
    app.mainloop()
