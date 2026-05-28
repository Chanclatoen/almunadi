# Next Prayer (Mawaqit)

Display the next Islamic prayer time in your desktop's top bar/menu bar, powered by [Mawaqit](https://mawaqit.net).

![GNOME 50](https://img.shields.io/badge/GNOME-50-blue)
![macOS 14+](https://img.shields.io/badge/macOS-14+-black)
![Windows 10+](https://img.shields.io/badge/Windows-10+-0078D6)
![License](https://img.shields.io/badge/license-GPL--3.0-green)

## Features

- Next prayer name, time, and countdown in the top bar
- Contextual icons per prayer (sunrise, sun, sunset, moon)
- Click to see all 5 daily prayer times + Shuruq
- Desktop notifications when each prayer time arrives
- Fetches times directly from your mosque's Mawaqit page — no account needed
- Configurable mosque URL
- Refreshes automatically every day

## Platforms

### Linux (GNOME Shell Extension)

See [GNOME installation instructions](#gnome-installation) below.

### macOS (Native Menu Bar App)

See [NextPrayerMac/README.md](NextPrayerMac/README.md) for build instructions. Requires macOS 14+ and Xcode 15+.

### Windows (System Tray App)

See [NextPrayerWindows/README.md](NextPrayerWindows/README.md). Python-based, runs in the system tray with toast notifications. Can be packaged as a standalone `.exe` with PyInstaller.

## GNOME Installation

### From source

```bash
git clone https://github.com/Chanclatoen/next-prayer-mawaqit.git
cd next-prayer-mawaqit
make install
```

Then log out and back in, and enable the extension:

```bash
gnome-extensions enable next-prayer@mawaqit
```

### Manual

1. Copy the files to `~/.local/share/gnome-shell/extensions/next-prayer@mawaqit/`
2. Compile the schema: `glib-compile-schemas schemas/`
3. Log out and back in
4. Enable: `gnome-extensions enable next-prayer@mawaqit`

## Configuration

1. Open extension preferences (GNOME) or Settings (macOS)
2. Paste your mosque's Mawaqit URL (e.g. `https://mawaqit.net/en/w/your-mosque-slug`)
3. Prayer times load immediately

To find your mosque's URL, go to [mawaqit.net](https://mawaqit.net), search for your mosque, and copy the URL from your browser.

## How it works

The app fetches the public Mawaqit page for your configured mosque and extracts the embedded prayer time data (`confData`). No Mawaqit account or API key is needed.

Times are refreshed once per day (around midnight). Notifications are scheduled to fire at the exact second each prayer time arrives.

## License

GPL-3.0
