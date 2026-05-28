# Next Prayer (Mawaqit) - GNOME Shell Extension

A GNOME Shell extension that displays the next Islamic prayer time in your top bar, powered by [Mawaqit](https://mawaqit.net).

![GNOME 50](https://img.shields.io/badge/GNOME-50-blue)
![License](https://img.shields.io/badge/license-GPL--3.0-green)

## Features

- Shows the next prayer name, time, and countdown in the GNOME top bar
- Click to see all 5 daily prayer times + Shuruq
- Desktop notifications when each prayer time arrives
- Fetches times directly from your mosque's Mawaqit page
- Configurable via GNOME Extensions preferences
- Refreshes automatically every day

## Screenshot

Top bar display: `Maghrib  21:47  (-2h15)`

Dropdown menu shows all prayer times for the day.

## Installation

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

1. Open GNOME Extensions app (or run `gnome-extensions prefs next-prayer@mawaqit`)
2. Paste your mosque's Mawaqit URL (e.g. `https://mawaqit.net/en/w/your-mosque-slug`)
3. The extension will immediately fetch and display prayer times

To find your mosque's URL, go to [mawaqit.net](https://mawaqit.net), search for your mosque, and copy the URL from your browser.

## Requirements

- GNOME Shell 50
- libsoup3 (included with GNOME)

## How it works

The extension fetches the public Mawaqit page for your configured mosque and extracts the embedded prayer time data (`confData`). No Mawaqit account or API key is needed.

Times are refreshed once per day (around midnight) and the top bar label updates every 30 seconds.

## License

GPL-3.0
