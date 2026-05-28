# Next Prayer (Mawaqit) - Windows System Tray App

A Windows system tray app that displays the next Islamic prayer time, powered by [Mawaqit](https://mawaqit.net).

## Features

- Shows next prayer, time, and countdown in the system tray tooltip
- Color-coded tray icon per prayer
- Right-click menu with all prayer times (next prayer marked with arrow)
- Windows toast notifications at each prayer time
- Configurable mosque URL via dialog

## Requirements

- Python 3.8+
- Windows 10/11

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python next_prayer.py
```

On first run, right-click the tray icon and select **Set Mosque URL** to configure your mosque.

## Auto-start

To run at login, create a shortcut to `next_prayer.py` in:
```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
```

Or use `pythonw next_prayer.py` to run without a console window.

## Building an executable

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name NextPrayer next_prayer.py
```

The executable will be in `dist/NextPrayer.exe`.

## License

GPL-3.0
