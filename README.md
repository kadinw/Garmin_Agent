# Garmin Agent

Daily Windows job that pulls Garmin Connect watch data and emails it to `aleccwilkins@gmail.com` so Gemini can analyze recovery, sleep, training load, and activities.

Inspired by [johnson4601/AI_Fitness](https://github.com/johnson4601/AI_Fitness), but this project is email-based instead of Google Drive / dashboard based.

## What it sends

Each morning the job fetches **yesterday's complete day** plus a **7-day trend window**, then emails:

- `garmin_health.csv` — sleep, HRV, steps, stress, body battery, training readiness, and related daily metrics
- `garmin_activities.csv` — runs, rides, walks, and other recorded workouts
- `garmin_full.json` — the raw Garmin payloads Gemini can inspect in detail

The email body includes a short snapshot plus a coach-style prompt for Gemini.

## Secrets

Keep credentials in `secrets/.env.txt` (this folder is gitignored):

```
your.email@gmail.com
your-garmin-password
your-gmail-app-password
```

- Line 1: Garmin Connect email (also the Gmail SMTP username)
- Line 2: Garmin Connect password
- Line 3 (recommended): [Gmail App Password](https://myaccount.google.com/apppasswords)

Gmail will reject a normal account password when 2-Step Verification is on. Create an App Password and put it on line 3. Leave line 3 off only if SMTP login with line 2 already works.

Copy `secrets/.env.example.txt` if you need a blank template.

## One-time setup

In PowerShell, from this folder:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run_daily.py
```

The first run may ask for a Garmin MFA code. Tokens are saved under `secrets/.garminconnect/` so later scheduled runs can stay unattended.

If Garmin asks for MFA, or the daily job reports a login error, run this once in a terminal:

```powershell
.\.venv\Scripts\python.exe scripts\setup_garmin_login.py
```

Then register the 7:00 AM Windows task:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_scheduled_task.ps1
```

Optional: `scripts\install_scheduled_task.ps1 -Time 06:30`

## Manual commands

```powershell
# Normal daily run (fetch + email)
.\.venv\Scripts\python.exe run_daily.py

# Save files locally without sending email
.\.venv\Scripts\python.exe run_daily.py --no-email

# Wider history window
.\.venv\Scripts\python.exe run_daily.py --days 30

# Specific end date
.\.venv\Scripts\python.exe run_daily.py --date 2026-09-14
```

Reports are also written to `output\`. Logs go to `logs\garmin_agent.log` and, for the scheduled task, `logs\daily.log`.

## Using this with Gemini

After the email arrives:

1. Open it in Gmail
2. Ask Gemini to analyze the attachments, or add this mailbox/label as a Gem data source
3. Use the prompt already included in the email body, or ask a narrower question such as "Am I recovered enough for a hard workout today?"

## Notes

- Garmin Connect has no official public API. This uses the unofficial `garminconnect` / `garth` libraries, the same family of tools AI_Fitness uses. Garmin can change login or endpoints at any time.
- The job uses **yesterday**, not today, because step counts and sleep are often incomplete until the day is over.
- Line 2 must be the **Garmin Connect** password. If the watch account was created with "Sign in with Google", set a Garmin password in Garmin account settings first.
- Garmin often emails a one-time MFA code, especially on newer watches. Complete `scripts\setup_garmin_login.py` once, then leave the scheduled task unattended.
- Do not commit `secrets/`, Garmin tokens, or `output/` to GitHub.
