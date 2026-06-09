# Al Munadi

Display the next Islamic prayer time in your desktop's top bar / menu bar / system tray, powered by [Mawaqit](https://mawaqit.net).

![GNOME 50](https://img.shields.io/badge/GNOME-50-blue)
![KDE / Linux](https://img.shields.io/badge/KDE%20%2F%20Linux-tray-1d99f3)
![macOS 14+](https://img.shields.io/badge/macOS-14+-black)
![Windows 10+](https://img.shields.io/badge/Windows-10+-0078D6)
![License](https://img.shields.io/badge/license-GPL--3.0-green)
![Languages](https://img.shields.io/badge/i18n-EN%20%7C%20NL%20%7C%20AR%20%7C%20FR%20%7C%20TR-orange)

## Screenshots

Screenshots are not committed yet. Once captured from a real build, they will live under `docs/screenshots/` (see `docs/screenshots/README.md` for capture guidelines):

- GNOME Shell extension: `docs/screenshots/gnome.png`
- Linux tray app: `docs/screenshots/linux.png`
- Windows tray app: `docs/screenshots/windows.png`
- macOS menu bar app: `docs/screenshots/macos.png`
- Mosque finder website: `docs/screenshots/site.png`

## Quick Install

Need the exact Mawaqit URL for your mosque? Use the hosted mosque finder:

**Find your mosque:** https://almunadi.net/

Search for your mosque, copy the Mawaqit URL, then paste it into the app settings.

### Windows

1. Download `AlMunadi.exe` from the [latest release](https://github.com/Chanclatoen/almunadi/releases)
2. Double-click to run — the icon appears in your system tray
3. Click the tray icon and search for your mosque

No Python or install required. See [Windows README](AlMunadiWindows/README.md) for more options.

### macOS

1. Download `AlMunadi-macOS-*.zip` from the [latest release](https://github.com/Chanclatoen/almunadi/releases)
2. Unzip, drag `AlMunadi.app` to `/Applications`, and double-click to open — releases are signed with a Developer ID and notarized by Apple, so no Gatekeeper bypass is needed
3. The icon appears in your menu bar — click it and open Settings to search for your mosque

> Older or unsigned builds (no Developer ID) may be blocked by Gatekeeper. If you hit "damaged / can't be opened", run `xattr -dr com.apple.quarantine /Applications/AlMunadi.app`.

See [macOS README](AlMunadiMac/README.md) for build instructions.

### Linux — KDE, XFCE, Cinnamon, MATE, and others

```bash
cd AlMunadiLinux
pip install -r requirements.txt
python al_munadi_linux.py
```

The tray icon appears in your panel. Click it to view prayer times, right-click for the menu. Works on any Linux desktop with system tray support.

See [Linux README](AlMunadiLinux/README.md) for auto-start, PyInstaller packaging, and troubleshooting.

### Linux — GNOME Shell

```bash
git clone https://github.com/Chanclatoen/almunadi.git
cd almunadi
make install
```

Log out and back in, then enable:

```bash
gnome-extensions enable almunadi@almunadi.net
```

Right-click the top bar indicator and choose **Configure mosque** to search for your mosque. You can also download the `.zip` from [releases](https://github.com/Chanclatoen/almunadi/releases) and install it manually (see below).

## Features

- **Works everywhere** — native GNOME extension, macOS menu bar app, Windows tray app, and standalone Linux tray app for KDE/XFCE/Cinnamon/MATE
- **Prayer times in your desktop** — next prayer name, time, and live countdown always visible
- **All 5 daily prayers + Shuruq** — click to see the full schedule
- **Hijri date + Qibla direction** — shown in the popup/menu when mosque metadata is available
- **Iqama times** — shown when your mosque provides them via Mawaqit
- **Jumuah (Friday prayer)** — automatically replaces Dhuhr on Fridays with your mosque's Jumuah time
- **Since last prayer mode** — switch the tray/menu bar text from countdown to elapsed time since the previous prayer
- **Desktop notifications** — fires at the exact second each prayer arrives (toggle on/off)
- **Jumuah reminder control** — Jumuah has its own per-prayer reminder setting, separate from daily Dhuhr
- **Adhan audio** — optionally play your own adhan audio file at each prayer time
- **Mosque search** — find your mosque by name or city, no need to hunt for URLs
- **Multi-mosque** — save multiple mosques and switch between them instantly
- **Offline cache** — keeps working when your network is down, using the last fetched data
- **5 languages** — English, Dutch (Nederlands), Arabic (عربي), French (Français), Turkish (Türkçe)
- **Mawaqit API** — uses the structured API for reliable data, with HTML scraping as fallback
- **No account needed** — works with any public mosque on mawaqit.net
- **Daily auto-refresh** — fetches new times around midnight

## Configuration

### Find your mosque (recommended)

All platforms have a built-in **Search** feature. Type your mosque's name or city and pick from the results. The app handles the rest.

You can also use the hosted mosque finder at https://almunadi.net/ to copy a URL before opening the app.

### Paste a URL (advanced)

1. Go to [mawaqit.net](https://mawaqit.net) and find your mosque
2. Copy the URL from your browser (e.g. `https://mawaqit.net/en/w/arrahmaan-dordrecht`)
3. Paste it in the app's settings

## GNOME Manual Installation

If you prefer not to use `make install`:

1. Download the `almunadi@almunadi.net.zip` from [releases](https://github.com/Chanclatoen/almunadi/releases)
2. Extract to `~/.local/share/gnome-shell/extensions/almunadi@almunadi.net/`
3. Log out and back in
4. Enable: `gnome-extensions enable almunadi@almunadi.net`

Or install from source manually:

```bash
mkdir -p ~/.local/share/gnome-shell/extensions/almunadi@almunadi.net/
cp -r extension.js prefs.js metadata.json stylesheet.css schemas/ \
  ~/.local/share/gnome-shell/extensions/almunadi@almunadi.net/
glib-compile-schemas ~/.local/share/gnome-shell/extensions/almunadi@almunadi.net/schemas/
```

The GNOME `metadata.json` uses two version fields: `app-version` follows the app semver, while `version` is the monotonically increasing GNOME Extensions package version required by ego.gnome.org.

## Source Layout

- Shared Python logic: `core/al_munadi_core.py`
- Windows tray entrypoint: `AlMunadiWindows/al_munadi.py`
- Linux tray entrypoint: `AlMunadiLinux/al_munadi_linux.py`
- GNOME Shell extension: `extension.js`, `prefs.js`, `metadata.json`, `schemas/`
- macOS menu bar app: `AlMunadiMac/`

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
- `AlMunadi-macOS-*.zip` — macOS app
- `AlMunadi.exe` — Windows executable
- `AlMunadi-Linux` — Linux binary
- `almunadi@almunadi.net.zip` — GNOME extension

## Website

The static website lives in `site/` and deploys to GitHub Pages on pushes to `main`.

The hosted mosque finder uses a Cloudflare Worker in `worker/` for live Mawaqit search because the Mawaqit endpoint does not expose browser CORS headers. After deploying the Worker, set the Worker origin (`apiBase`) in `site/config.js` — the committed config used by this project's deployment. `site/config.example.js` is a template for forks. Leave `apiBase` empty only when the Worker is mounted under the same site domain.

## Testing

```bash
# Python (Windows / Linux apps)
cd AlMunadiWindows && pip install pytest && pytest
cd AlMunadiLinux && pip install pytest && pytest

# JavaScript (shared utilities)
node tests/test_utils.js
node tests/test_site_utils.js
node worker/test_worker.js
```

## License

GPL-3.0
