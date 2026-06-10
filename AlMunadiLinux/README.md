# Al Munadi -- Linux

A standalone Linux system tray app that displays Islamic prayer times from [Mawaqit](https://mawaqit.net). Designed for **KDE Plasma, XFCE, Cinnamon, MATE**, and any other desktop environment with system tray support (not needed for GNOME -- use the GNOME Shell extension instead).

## Requirements

- Python 3.8+
- Any Linux desktop environment with system tray / AppIndicator support
- `libappindicator3` or `libayatana-appindicator` (for the tray icon)
- `notify-send` (from `libnotify-bin`) for desktop notifications
- `tkinter` (usually included with Python; install `python3-tk` if missing)

### Install system dependencies

**Debian / Ubuntu / Mint:**

```bash
sudo apt install python3-tk libayatana-appindicator3-1 gir1.2-ayatanaappindicator3-0.1 libnotify-bin
```

**Fedora:**

```bash
sudo dnf install python3-tkinter libappindicator-gtk3 libnotify
```

**Arch Linux:**

```bash
sudo pacman -S python-gobject libappindicator-gtk3 libnotify tk
```

**openSUSE:**

```bash
sudo zypper install python3-tk libappindicator3-1 libnotify-tools
```

## Install

### Option 1: Run from source (recommended)

```bash
cd AlMunadiLinux
pip install -r requirements.txt
python3 al_munadi_linux.py
```

The crescent/prayer icon appears in your system tray. Click it to see prayer times, right-click for the menu.

### Option 2: Build a standalone binary with PyInstaller

```bash
pip install -r requirements.txt pyinstaller
pyinstaller --onefile --paths .. --name AlMunadiLinux al_munadi_linux.py
```

The binary will be in `dist/AlMunadiLinux`. Copy it anywhere and run it directly -- no Python needed at runtime.

## Features

- **System tray icon** with the next prayer's initial letter on a color-coded circle
- **Prayer times popup** -- click the tray icon to see all five prayers in a dark-themed card layout
- **Iqama times** displayed when your mosque provides them
- **Jumuah support** -- automatically shows Friday prayer time instead of Dhuhr on Fridays
- **Desktop notifications** at each prayer time via `notify-send` (toggle on/off)
- **Adhan audio playback** -- plays an audio file at prayer time using `paplay`, `mpv`, or `aplay`
- **Mosque search** -- find your mosque by name or city from the settings window (runs in the background, so the window never freezes)
- **First-run welcome** -- before a mosque is configured, the tray label shows "Set mosque" and the popup guides you to setup
- **Adhan controls** -- Test adhan and Stop adhan buttons in settings; missing files show a friendly message
- **Manual offsets** -- per-prayer corrections (±60 min) with a one-click Reset offsets button
- **Multi-mosque support** -- save multiple mosques and switch between them
- **Offline cache** -- works when your network is down using the last fetched data
- **Mawaqit API** with HTML scraping fallback
- **Localization** -- English, Dutch, Arabic, French, and Turkish
- **Countdown format** -- choose between compact (`-2h15m`) and full (`-2h 15m`)
- **Precise notifications** -- uses `threading.Timer` for exact prayer-time alerts
- **Error recovery** with automatic retry from cache

## First-time setup

1. Click the tray icon or right-click and choose **Show Prayer Times**
2. Click **Settings** in the popup window
3. Type your mosque name or city in the search box and press Enter
4. Double-click a result to select it
5. Prayer times load immediately

Alternatively, paste a Mawaqit URL directly (e.g. `https://mawaqit.net/en/w/your-mosque`) and click **Save**.

## Auto-start at login

Create a `.desktop` file in `~/.config/autostart/`:

```bash
mkdir -p ~/.config/autostart

cat > ~/.config/autostart/al-munadi.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Al Munadi
Comment=Islamic prayer times in your system tray
Exec=python3 /full/path/to/al_munadi_linux.py
Icon=clock
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
EOF
```

Replace `/full/path/to/al_munadi_linux.py` with the actual path to the script.

If you built a standalone binary with PyInstaller, use that path for `Exec=` instead:

```
Exec=/full/path/to/AlMunadiLinux
```

## Settings location

Settings and cached data are stored following the XDG Base Directory Specification:

```
~/.config/AlMunadi/
  settings.json    # mosque URL, notification preferences, language, etc.
  cache.json       # cached prayer times for offline use
```

## Adhan audio

The app can play an audio file (WAV, MP3, OGG, FLAC, etc.) at each prayer time instead of showing a notification. It tries these players in order:

1. `paplay` (PulseAudio / PipeWire)
2. `mpv` (universal media player)
3. `aplay` (ALSA, WAV only)

Configure the audio file path in **Settings > Adhan > Browse**.

## Desktop widget (Conky)

For an ambient at-a-glance display on the desktop (next prayer, countdown, all 5 prayers, optional iqama + Hijri + Qibla), there is a Conky template in [`conky/`](conky/). It works on any desktop environment with a compositor (KDE, XFCE, Cinnamon, MATE, LXQt, Budgie) and reads the same `~/.config/AlMunadi/cache.json` that this tray app already writes -- no extra config needed.

```bash
sudo apt install conky-all
mkdir -p ~/.config/AlMunadi/conky
cp AlMunadiLinux/conky/almunadi.lua AlMunadiLinux/conky/almunadi-*.conkyrc ~/.config/AlMunadi/conky/
conky -c ~/.config/AlMunadi/conky/almunadi-medium.conkyrc &
```

See [`conky/README.md`](conky/README.md) for the small / medium / large variants and customization options.

> **GNOME users**: use the GNOME Shell extension at the repo root -- it already provides the same data as a panel widget.

## Desktop environment notes

| Desktop | Tray support | Notes |
|---------|-------------|-------|
| **KDE Plasma** | Built-in | Works out of the box |
| **XFCE** | Built-in | Works out of the box |
| **Cinnamon** | Built-in | Works out of the box |
| **MATE** | Built-in | Works out of the box |
| **LXQt** | Built-in | Works out of the box |
| **Budgie** | Built-in | Works out of the box |
| **GNOME** | Requires extension | Install the [AppIndicator](https://extensions.gnome.org/extension/615/appindicator-support/) extension, or use the GNOME Shell extension from this repo instead |

## License

GPL-3.0
