# Al Munadi — Windows

A Windows system tray app that displays the next Islamic prayer time, powered by [Mawaqit](https://mawaqit.net).

## Install

### Option 1: Download (recommended)

1. Download `AlMunadi.exe` from the [latest release](https://github.com/Chanclatoen/almunadi/releases)
2. Double-click to run — the crescent icon appears in your system tray (bottom-right, near the clock)
3. Click the tray icon to open the prayer times window
4. Go to **Settings** and search for your mosque by name or city

That's it. No Python, no install, no dependencies.

### Option 2: Run from source

Requires Python 3.8+ and Windows 10/11.

```bash
pip install -r requirements.txt
python al_munadi.py
```

### Option 3: Build your own .exe

```bash
pip install -r requirements.txt pyinstaller
pyinstaller --onefile --noconsole --paths .. --name AlMunadi al_munadi.py
```

The executable will be in `dist/AlMunadi.exe`.

## Features

- **System tray icon** with the prayer initial letter on a color-coded circle
- **Prayer times popup** — click the tray icon to see all prayers in a dark-themed card layout
- **Iqama times** displayed when your mosque provides them
- **Jumuah support** — automatically shows Friday prayer time instead of Dhuhr
- **Windows toast notifications** at each prayer time (toggle on/off in settings or tray menu)
- **Mosque search** — find your mosque by name or city from the settings window
- **Offline cache** — works when your network is down using the last fetched data
- **Mawaqit API** with HTML scraping fallback
- **DPI-aware** — crisp on high-resolution displays

## Usage

| Action | What happens |
|--------|-------------|
| **Click tray icon** | Opens the prayer times window |
| **Right-click tray icon** | Quick menu with prayers, settings, refresh |
| **Hover over tray icon** | Shows next prayer, time, and countdown |

### First-time setup

1. Click the tray icon → **Settings**
2. Type your mosque name or city in the search box and press Enter
3. Double-click a result to select it
4. Prayer times load immediately

Or paste a Mawaqit URL directly (e.g. `https://mawaqit.net/en/w/your-mosque`).

## Start at Login

To run AlMunadi automatically when Windows starts:

1. Press `Win + R`, type `shell:startup`, press Enter
2. Copy `AlMunadi.exe` (or a shortcut to it) into the folder that opens

If running from source, create a shortcut to `pythonw al_munadi.py` in that folder instead.

## Settings Location

Settings and cached data are stored in:

```
%APPDATA%\AlMunadi\
├── settings.json    # mosque URL, notification preferences
└── cache.json       # cached prayer times for offline use
```

If upgrading from an older version that stored `next_prayer_settings.json` in the app directory, the settings are migrated automatically on first run.

## Releasing

Pushing a repository `v*` release tag triggers the [Windows Release](../.github/workflows/windows-release.yml) GitHub Actions workflow, which builds the `.exe` with PyInstaller and attaches it to the GitHub Release:

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

## License

GPL-3.0
