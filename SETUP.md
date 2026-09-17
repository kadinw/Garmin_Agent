# Setup: which files to open

Start here. You only need to open a few things. Leave the other files alone.

## 1. Open this folder

In File Explorer, open:

`Documents\GitHub\Garmin_Agent`

You should see a file named **GarminAgentSetup.exe** in that same folder, next to `run_daily.py` and this `SETUP.md` file.

If Python is not installed yet, first install it from [python.org/downloads](https://www.python.org/downloads/). On the installer, check **Add python.exe to PATH**.

---

## 2. Open the setup program (this is the main file)

**File to open:** `GarminAgentSetup.exe`

1. Double-click **GarminAgentSetup.exe**.
2. If Windows says “Windows protected your PC”, click **More info**, then **Run anyway**.
3. A settings window will open. That window is the whole setup.

Fill in these boxes:

| Box in the window | What to type |
| --- | --- |
| Gmail address | The Gmail you use for Garmin, such as `you@gmail.com` |
| Garmin password | The password that works on the Garmin website with email sign-in |
| Gmail App Password | A special 16-letter send key from Google, not your normal Gmail password |

If you do not have an App Password yet, click **Open the Gmail App Password page** in that same window. Sign in as the same Gmail address, create an app password, copy the 16 letters, and paste them into the App Password box.

Then set:

| Control in the window | What it means |
| --- | --- |
| Hour / Minute / AM or PM | What time the email should go out each day |
| Days of data | How many past days to include. **1** = yesterday only. **7** = about a week |

Then click the buttons in this order:

1. **Save and turn on the daily email**
2. **Sign in to Garmin (needed once)** — a small black window may open. If Garmin emails a code, type it there and press Enter.
3. **Send a test email now** — wait until it finishes.

Check that Gmail inbox (and the spam folder). You should see an email named like **Garmin daily report** with CSV and JSON files attached.

You can close the setup window after that. Open **GarminAgentSetup.exe** again any time you want to change the time or the number of days.

---

## 3. Files you usually do not need to open

These are used automatically. You do not have to edit them for a normal setup.

| File or folder | What it is |
| --- | --- |
| `secrets\.env.txt` | Where the setup window saves your three secret lines. The setup program writes this for you. |
| `secrets\.env.example.txt` | A blank example. Only open this if you are typing secrets by hand. |
| `settings.json` | Where the setup window saves the send time and number of days. Created after you click Save. |
| `scripts\run_daily.bat` | What Windows runs every morning. Do not edit this. |
| `run_daily.py` | The daily email program. Windows runs it for you. |
| `output\` | Copies of the reports that were emailed. Open a file here only if you want to look at the data. |
| `logs\daily.log` | A text diary of the morning job. Open this if no email arrived. |
| `logs\garmin_agent.log` | More detailed program notes. Open this if something failed. |

---

## 4. If you want to type the secrets file yourself

Only do this if you are not using the setup window.

**Folder to open:** `secrets`  
**File to open:** `.env.txt`  
Open it with Notepad.

If the file does not exist, copy `secrets\.env.example.txt`, rename the copy to `.env.txt`, then open that.

Put exactly three lines, with no extra words:

```
you@gmail.com
your-garmin-password
your-gmail-app-password
```

Save the file. Make sure it is named `.env.txt` and not `.env.txt.txt`.

---

## 5. Check that Windows will run it every day

1. Press the Windows key.
2. Type `Task Scheduler` and open it.
3. Look for **Garmin Agent Daily Report**.
4. It should say **Ready**.

To try it without waiting until morning: right-click **Garmin Agent Daily Report** → **Run**. Then check Gmail.

---

## 6. What you should get when setup worked

- An email in the Gmail inbox from line 1
- Attachments named like `garmin_health.csv`, `garmin_activities.csv`, and `garmin_full.json`
- A matching copy of those files inside the `output` folder

After that, leave this computer on and stay signed in at the time you chose.

---

## 7. Do not share these

Do not email, copy to a public place, or upload to GitHub:

- `secrets\.env.txt` (passwords)
- `secrets\.garminconnect` (Garmin login tokens)
- `output\` (your health data)

`GarminAgentSetup.exe`, `SETUP.md`, and `README.md` are safe to keep in the project.
