# YouTube Subscriptions Manager

![App Screenshot](images/screenshot.png)

A GUI tool to **backup, clear, and restore** your YouTube subscriptions — safely and automatically.
Built with Playwright (browser automation) and Flet (desktop GUI).

---

## Features

- **Export (Backup)** — saves all subscribed channels to `subscriptions.csv`
- **Clear (Unsubscribe)** — mass unsubscribe with a confirmation prompt
- **Import (Restore)** — re-subscribes from a CSV backup file
- **Safe Mode** — human-like random delays to avoid YouTube account flags
- **Background Mode** — runs the browser hidden while you do other things
- **Session Persistence** — stays logged in after the first sign-in

---

## Installation

> No Python or Git required. The installer handles everything.

**Windows** — open PowerShell and run:

```powershell
irm https://github.com/savvy773/app-yt-subs-manager/releases/latest/download/install.ps1 | iex
```

**Linux / macOS** — open a terminal and run:

```bash
curl -fsSL https://github.com/savvy773/app-yt-subs-manager/releases/latest/download/install.sh | bash
```

What the installer does, step by step:

1. Installs **uv** (a fast Python package manager) if not already present
2. Installs the latest **Python** via uv — no system Python needed
3. Downloads the app package (`.whl`) from GitHub Releases
4. Verifies the download with a **Blake3** checksum to ensure integrity
5. Installs the app with `uv tool install`
6. Installs the **Chromium** browser required for automation

---

## Usage

After installation, launch the app from any terminal:

```
yt-subs
```

**First run:**

1. Click **Login / Check Session** — a browser window opens
2. Sign in to your Google account manually
3. Close the browser — your session is saved for future runs

**Main operations:**

| Button | What it does |
|--------|--------------|
| Export (Backup) | Scrolls your subscriptions page and saves all channels to `subscriptions.csv` |
| Clear (Delete) | Unsubscribes from every channel — shows a confirmation dialog first |
| Import (Restore) | Opens each channel URL from `subscriptions.csv` and subscribes |

**Tips:**

- Enable **Background Mode** after your first login to run without a visible browser window
- Safe Mode delays are intentional — do not close the app mid-operation
- For 200+ channels, export and import each take roughly 20–30 minutes

---

## Files created locally

| File / Folder | Description |
|---------------|-------------|
| `subscriptions.csv` | Your channel backup — keep this safe |
| `config.json` | Window position/size (auto-generated) |
| `user_data/` | Google session data — **never share or upload this** |

---

## Uninstall

```
uv tool uninstall yt-subs
```

---

## Disclaimer

This tool automates actions on YouTube, which may conflict with YouTube's Terms of Service.
Use it at your own risk. The author is not responsible for any account restrictions or bans.
The `user_data` folder contains your active Google session — treat it like a password.

---

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.
