# Garmin Agent

This program looks at your Garmin watch data once a day and emails it to you. You can then give that email to Gemini and ask questions about sleep, recovery, steps, and workouts.

**For setup, start with [SETUP.md](SETUP.md).** That page lists exactly which files to open.

You do **not** need to be a programmer to use it. Follow the steps in order. If a step asks you to copy a command, copy the whole line, paste it, then press Enter.

---

## What you need

- A Windows computer that is usually on in the morning
- Python 3.13 (or close to it) installed from [python.org](https://www.python.org/downloads/). During install, check the box that says **Add python.exe to PATH**.
- A Garmin Connect account that can sign in with **email and password** (not only “Sign in with Google”)
- A Gmail account. The program emails **that same Gmail address**.

This folder should stay on this computer after you download it. Do not upload the `secrets` folder to GitHub.

---

## Easiest way: run the setup program

1. Keep **GarminAgentSetup.exe** in the same folder as `run_daily.py` (the folder you downloaded or extracted).
2. Double-click **GarminAgentSetup.exe**.
3. If Windows says it protected your PC, click **More info**, then **Run anyway**.
4. A settings window will open. Fill in:
   - your Gmail address
   - your Garmin password
   - your Gmail App Password (click **Open the Gmail App Password page** if you do not have one yet)
   - **When to send the email** (hour, minute, AM or PM)
   - **How much Garmin data to include** (1 is yesterday only, 7 is about a week)
5. Click **Save and turn on the daily email**.
6. Click **Sign in to Garmin**. If Garmin emails a one-time code, type it in the small black window and press Enter.
7. Click **Send a test email now** and wait. Then check Gmail (and spam).

You can open this same window later any time you want to change the time or the number of days.

The sections below are only if you want to do those steps yourself instead of using the setup program.

---

## Step 1. Create your secrets file

Your passwords live in one small text file:

`secrets\.env.txt`

There is an example file named `secrets\.env.example.txt`. You can copy it and rename the copy to `.env.txt`, or create a new Notepad file with that exact name.

### How to open it

1. Open the `secrets` folder in this project.
2. If you already have `.env.txt`, right-click it and choose **Open with → Notepad**.
3. If you do not have `.env.txt`, open Notepad, then use **File → Save As**.
   - Save in the `secrets` folder
   - File name: `.env.txt`
   - Save as type: **All files (*.*)**  
     (If you skip this, Windows may save it as `.env.txt.txt`, and the program will not find it.)

### How to format the file

The file must have **exactly three lines**. No labels, no extra words, no quotation marks.

```
your-gmail-address@gmail.com
your-garmin-password
your-gmail-app-password
```

| Line | What to put here | Example (fake) |
| --- | --- | --- |
| 1 | The Gmail address for Garmin **and** for sending the email | `sam@gmail.com` |
| 2 | Your Garmin Connect password | `MyWatchPassword1` |
| 3 | A Gmail App Password (not your normal Gmail password) | `abcdabcdabcdabcd` |

It should look like this when you are done (with **your** values, not these):

```
sam@gmail.com
MyWatchPassword1
abcdabcdabcdabcd
```

### Rules that matter

- Line 1 is only the email. Do not write `email:` in front of it.
- Line 2 is your **Garmin** password, the one that works on [Garmin Sign In](https://sso.garmin.com/portal/sso/en-US/sign-in) with email and password.
- Line 3 is a special 16-character **Gmail App Password**. Gmail will not send mail using your normal Gmail password.
- Put each item on its own line. Press Enter after line 1, after line 2, and after line 3.
- Do not add blank lines in between.
- Do not put spaces before the text.
- You can leave spaces out of the App Password. If Google shows `abcd efgh ijkl mnop`, you may paste it with or without spaces.

### How to get the Gmail App Password (line 3)

1. Sign in to Google as the **same address** you put on line 1.
2. Turn on 2-Step Verification if Google asks you to: [myaccount.google.com/signinoptions/two-step-verification](https://myaccount.google.com/signinoptions/two-step-verification)
3. Open [App Passwords](https://myaccount.google.com/apppasswords)
4. Create a new app password. A name like `Garmin Agent` is fine.
5. Google will show 16 letters. Copy them.
6. Paste them onto **line 3** of `.env.txt`.
7. Save the file.

If Garmin only lets you sign in with Google, open Garmin account settings and create a Garmin password first. That Garmin password goes on **line 2**.

---

## Step 2. Install the program on this computer (first time only)

1. In File Explorer, open the folder you downloaded (the one that contains `run_daily.py`).
2. Click the address bar at the top of File Explorer, type `powershell`, and press Enter. A black or blue window should open in this folder.
3. Copy and paste these three commands, one at a time. Press Enter after each:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\setup_garmin_login.py
```

If `py -3.13` does not work, try:

```powershell
python -m venv .venv
```

Then run the other two commands as written.

The last command signs in to Garmin. If Garmin emails or texts a one-time code, type that code in the window and press Enter. You only need to do this once on this computer.

Then send a test email:

```powershell
.\.venv\Scripts\python.exe run_daily.py --days 1
```

If it worked, you will get an email with yesterday’s Garmin data. Also check your spam folder.

---

## Step 3. Set up the Windows scheduled task

The setup window is the easiest way to choose the time and how many days of data to include: double-click **GarminAgentSetup.exe** and click **Save and turn on the daily email**.

This tells Windows: “Every morning, run the Garmin email program for me.”

The computer should be **on**, and you should be **logged in**, at the time you choose. If the PC is asleep or shut down, Windows will try again after it wakes (when possible).

### Easy way (recommended)

In the same PowerShell window from Step 2, run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_scheduled_task.ps1
```

That creates a task named **Garmin Agent Daily Report** that runs every day at **7:00 AM**.

To pick a different time, use 24-hour clock time. Example for 8:30 AM:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_scheduled_task.ps1 -Time 08:30
```

Windows may ask if a script is allowed to run. That is expected. The command above already includes the permission to run this installer.

### Check that the task is there

1. Press the Windows key.
2. Type `Task Scheduler` and open it.
3. In the right-hand list, or under **Task Scheduler Library**, look for **Garmin Agent Daily Report**.
4. You should see it set to **Ready**, daily, at 7:00 AM (or the time you chose).

To test it without waiting until morning:

1. Right-click **Garmin Agent Daily Report**
2. Click **Run**
3. Check your Gmail a minute later

### Manual way (if you prefer clicking)

Only use this if the easy way did not work.

1. Open **Task Scheduler**.
2. Click **Create Task…** (not “Create Basic Task”).
3. **General** tab:
   - Name: `Garmin Agent Daily Report`
   - Choose **Run only when user is logged on**
4. **Triggers** tab:
   - New → Daily → set the time (for example 7:00:00 AM) → OK
5. **Actions** tab:
   - New → Start a program
   - Program/script: browse to `scripts\run_daily.bat` inside the folder you downloaded
   - Start in: that same downloaded folder (the one that contains `run_daily.py`)
6. **Conditions** tab:
   - Uncheck **Start the task only if the computer is on AC power** if this is a laptop
7. Click **OK**.

---

## What the email contains

Each run emails you:

- A short summary of yesterday
- `garmin_health.csv` — sleep, heart rate, steps, HRV, and similar daily numbers
- `garmin_activities.csv` — workouts
- `garmin_full.json` — the full Garmin details

It uses **yesterday**, not today, because Garmin often has incomplete steps and sleep until the day is over.

You can open the email in Gmail and ask Gemini to analyze the attachments.

---

## If something goes wrong

| What you see | What to try |
| --- | --- |
| “Missing secrets/.env.txt” | The file is in the wrong folder, or it was saved as `.env.txt.txt`. Put it in `secrets` and name it `.env.txt`. |
| Garmin says invalid username or password | Line 1 and line 2 must be the Garmin email/password, not a Google-only login. |
| Garmin asks for MFA on the scheduled run | Run `.\.venv\Scripts\python.exe scripts\setup_garmin_login.py` once in PowerShell. |
| Gmail says username and password not accepted | Line 3 must be an App Password created while signed into the **same** Gmail as line 1. |
| No email at 7:00 AM | Make sure the PC was on and you were logged in. In Task Scheduler, confirm the task is Ready. Check `logs\daily.log`. |
| You want to send without waiting for the schedule | In PowerShell, run `.\.venv\Scripts\python.exe run_daily.py` |

Copies of each report are also saved in the `output` folder.

---

## Keep this private

Do not share or upload:

- `secrets\.env.txt`
- `secrets\.garminconnect` (Garmin login tokens)
- The `output` folder (your health data)

The rest of this project is safe to keep in a private GitHub repository.
