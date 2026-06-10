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
- **Mosque search** — find your mosque by name or city from the settings window (runs in the background, so the window never freezes)
- **First-run welcome** — before a mosque is configured, the tray label shows "Set mosque" and the popup guides you to setup
- **Adhan controls** — choose your own WAV file, with Test adhan and Stop adhan buttons in settings
- **Manual offsets** — per-prayer corrections (±60 min) with a one-click Reset offsets button
- **Offline cache** — works when your network is down using the last fetched data
- **Mawaqit API** with HTML scraping fallback
- **DPI-aware** — crisp on high-resolution displays
- **Al Munadi look** — calm charcoal/emerald theme shared with the other platforms

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

## Desktop widget (Windows 11 Widget Board)

A separate MSIX package adds a native Widget Board widget (Win+W → "+") in three sizes — small (next prayer + countdown), medium (all 5 prayers), large (all 5 + iqama + Hijri + Qibla). It reads the same `%APPDATA%\AlMunadi\cache.json` that the tray app already writes, so **the tray app must be running and configured first**.

### Install

1. Download `AlMunadiWidget.msix` and `AlMunadiWidget.cer` from the [latest release](https://github.com/Chanclatoen/almunadi/releases).
2. Trust the self-signed certificate (the MSIX is signed with a CI-generated cert; once distribution is set up with a real code-signing cert this step disappears):

   ```powershell
   Import-Certificate -FilePath AlMunadiWidget.cer `
                      -CertStoreLocation Cert:\LocalMachine\TrustedPeople
   ```

   Requires an elevated PowerShell.

3. Install the MSIX:

   ```powershell
   Add-AppxPackage AlMunadiWidget.msix
   ```

4. Open the Widget Board (`Win+W`) → click **+ Add widgets** → find **Al Munadi** → pick a size.

The widget refreshes itself at every prayer-time transition and whenever `cache.json` changes (e.g. when you switch mosques in the tray app), so no polling.

### Build from source

Requires .NET 8 SDK and the Windows App SDK.

```powershell
cd AlMunadiWindows\widget_provider
dotnet publish -c Release -r win-x64 --self-contained `
  /p:Platform=x64 /p:GenerateAppxPackageOnBuild=true
```

See `widget_provider/Assets/README.md` for the icon assets required by `Package.appxmanifest`.

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

Pushing a repository `v*` release tag triggers the [Windows Release](../.github/workflows/windows-release.yml) GitHub Actions workflow, which builds the `.exe` with PyInstaller, packages the C# Widget Provider into a signed MSIX, and attaches both (plus the self-signed `.cer`) to the GitHub Release:

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

## License

GPL-3.0
