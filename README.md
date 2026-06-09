# Next Prayer (Mawaqit)

Display the next Islamic prayer time in your desktop's top bar / menu bar / system tray, powered by [Mawaqit](https://mawaqit.net).

![GNOME 50](https://img.shields.io/badge/GNOME-50-blue)
![KDE / Linux](https://img.shields.io/badge/KDE%20%2F%20Linux-tray-1d99f3)
![macOS 14+](https://img.shields.io/badge/macOS-14+-black)
![Windows 10+](https://img.shields.io/badge/Windows-10+-0078D6)
![License](https://img.shields.io/badge/license-GPL--3.0-green)
![Languages](https://img.shields.io/badge/i18n-EN%20%7C%20AR%20%7C%20FR%20%7C%20TR-orange)

## Quick Install

### Windows

1. Download `NextPrayer.exe` from the [latest release](https://github.com/Chanclatoen/next-prayer-mawaqit/releases)
2. Double-click to run — the icon appears in your system tray
3. Click the tray icon and search for your mosque

No Python or install required. See [Windows README](NextPrayerWindows/README.md) for more options.

### macOS

1. Download `NextPrayer-macOS-*.zip` from the [latest release](https://github.com/Chanclatoen/next-prayer-mawaqit/releases)
2. Unzip, drag `NextPrayer.app` to `/Applications`
3. First launch: right-click the app, click **Open**, then **Open** again
4. The icon appears in your menu bar — click it and open Settings to search for your mosque

See [macOS README](NextPrayerMac/README.md) for build instructions.

### Linux — KDE, XFCE, Cinnamon, MATE, and others

```bash
cd NextPrayerLinux
pip install -r requirements.txt
python next_prayer_linux.py
```

The tray icon appears in your panel. Click it to view prayer times, right-click for the menu. Works on any Linux desktop with system tray support.

See [Linux README](NextPrayerLinux/README.md) for auto-start, PyInstaller packaging, and troubleshooting.

### Linux — GNOME Shell

```bash
git clone https://github.com/Chanclatoen/next-prayer-mawaqit.git
cd next-prayer-mawaqit
make install
```

Log out and back in, then enable:

```bash
gnome-extensions enable next-prayer@mawaqit
```

Right-click the top bar indicator and choose **Configure mosque** to search for your mosque. You can also download the `.zip` from [releases](https://github.com/Chanclatoen/next-prayer-mawaqit/releases) and install it manually (see below).

## Features

- **Works everywhere** — native GNOME extension, macOS menu bar app, Windows tray app, and standalone Linux tray app for KDE/XFCE/Cinnamon/MATE
- **Prayer times in your desktop** — next prayer name, time, and live countdown always visible
- **All 5 daily prayers + Shuruq** — click to see the full schedule
- **Iqama times** — shown when your mosque provides them via Mawaqit
- **Jumuah (Friday prayer)** — automatically replaces Dhuhr on Fridays with your mosque's Jumuah time
- **Desktop notifications** — fires at the exact second each prayer arrives (toggle on/off)
- **Adhan audio** — optionally play your own adhan audio file at each prayer time
- **Mosque search** — find your mosque by name or city, no need to hunt for URLs
- **Multi-mosque** — save multiple mosques and switch between them instantly
- **Offline cache** — keeps working when your network is down, using the last fetched data
- **4 languages** — English, Arabic (عربي), French (Français), Turkish (Türkçe)
- **Mawaqit API** — uses the structured API for reliable data, with HTML scraping as fallback
- **No account needed** — works with any public mosque on mawaqit.net
- **Daily auto-refresh** — fetches new times around midnight

## Configuration

### Find your mosque (recommended)

All platforms have a built-in **Search** feature. Type your mosque's name or city and pick from the results. The app handles the rest.

### Paste a URL (advanced)

1. Go to [mawaqit.net](https://mawaqit.net) and find your mosque
2. Copy the URL from your browser (e.g. `https://mawaqit.net/en/w/arrahmaan-dordrecht`)
3. Paste it in the app's settings

## GNOME Manual Installation

If you prefer not to use `make install`:

1. Download the `next-prayer@mawaqit.zip` from [releases](https://github.com/Chanclatoen/next-prayer-mawaqit/releases)
2. Extract to `~/.local/share/gnome-shell/extensions/next-prayer@mawaqit/`
3. Log out and back in
4. Enable: `gnome-extensions enable next-prayer@mawaqit`

Or install from source manually:

```bash
cp -r extension.js prefs.js metadata.json stylesheet.css schemas/ \
  ~/.local/share/gnome-shell/extensions/next-prayer@mawaqit/
glib-compile-schemas ~/.local/share/gnome-shell/extensions/next-prayer@mawaqit/schemas/
```

## How It Works

The app fetches prayer data from the Mawaqit API, which returns structured JSON including prayer times, iqama offsets, and Jumuah schedules. If the API is unavailable, it falls back to parsing the public HTML page. No Mawaqit account or API key is needed.

Times refresh once per day (around midnight). Notifications are scheduled with precise timers so they fire at the exact second. When the network is down, the app serves cached data from the last successful fetch and retries every 5 minutes.

## Releasing

Pushing application code to `main` automatically bumps the patch version, commits the version files, creates a `vX.Y.Z` tag, and dispatches all 4 platform release builds. Documentation, workflow, and script-only changes are ignored by the automatic release workflow.

A single version tag still triggers all 4 platform builds, so manual releases can also be created with:

```bash
git tag vX.Y.Z && git push origin vX.Y.Z
```

This creates a release with:
- `NextPrayer-macOS-*.zip` — macOS app
- `NextPrayer.exe` — Windows executable
- `NextPrayer-Linux` — Linux binary
- `next-prayer@mawaqit.zip` — GNOME extension

## Testing

```bash
# Python (Windows / Linux apps)
cd NextPrayerWindows && pip install pytest && pytest
cd NextPrayerLinux && pip install pytest && pytest

# JavaScript (shared utilities)
node tests/test_utils.js
```

## License

GPL-3.0
