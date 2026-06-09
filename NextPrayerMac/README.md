# Next Prayer (Mawaqit) — macOS

A native macOS menu bar app that displays the next Islamic prayer time, powered by [Mawaqit](https://mawaqit.net).

## Install

### Option 1: Download (recommended)

1. Download `NextPrayer-macOS-*.zip` from the [latest release](https://github.com/Chanclatoen/next-prayer-mawaqit/releases)
2. Unzip and drag `NextPrayer.app` into `/Applications`
3. The app is ad-hoc signed (not notarized), so the first launch is blocked by Gatekeeper. Either:
   - Right-click the app → **Open** → **Open**, or
   - Run: `xattr -dr com.apple.quarantine /Applications/NextPrayer.app`
4. The icon appears in your menu bar (there is no Dock icon)
5. Click the menu bar icon → **Settings** → search for your mosque

### Option 2: Build from source

Requires macOS 14+ (Sonoma) and Xcode 15+.

The committed `NextPrayer.xcodeproj` is ready to use:

```bash
open NextPrayer.xcodeproj
```

Select the **NextPrayer** scheme and press ⌘R to build and run.

To build a distributable zip from the command line:

```bash
brew install xcodegen        # only needed if you change project.yml
./scripts/build-release.sh   # outputs dist/NextPrayer-macOS-v<version>.zip
```

If you edit `project.yml`, regenerate the project with `xcodegen generate`.

## Features

- **Menu bar display** — next prayer name, time, and live countdown with contextual icons (sunrise, sun, clouds, sunset, moon)
- **Prayer times dropdown** — click to see all 5 prayers + Shuruq, with the next prayer highlighted in blue
- **Iqama times** — shown under each prayer when your mosque provides them
- **Jumuah support** — automatically shows Friday prayer time instead of Dhuhr, plus Jumuah 2 if available
- **Native notifications** — macOS alerts at each prayer time (toggle on/off in Settings)
- **Mosque search** — find your mosque by name or city directly from Settings
- **Offline cache** — keeps showing prayer times when your network is down
- **Mawaqit API** with HTML scraping fallback
- **Launch at login** — toggle in Settings

## Usage

| Action | What happens |
|--------|-------------|
| **Click menu bar icon** | Opens the prayer times dropdown |
| **Hover over menu bar icon** | See the next prayer at a glance |

### First-time setup

1. Click the menu bar icon → **Settings**
2. Search for your mosque by name or city, or paste a Mawaqit URL
3. Prayer times appear immediately

## Settings

Settings are stored in macOS `UserDefaults` (standard for native apps). Cached prayer data persists across restarts for offline support.

| Setting | Description |
|---------|-------------|
| Mosque URL | Your mosque's Mawaqit URL |
| Prayer notifications | Toggle desktop notifications on/off |
| Launch at login | Start NextPrayer when you log in |

## Releasing

Pushing a repository `v*` release tag triggers the [macOS Release](../.github/workflows/macos-release.yml) GitHub Actions workflow, which builds the app and attaches the zip to the GitHub Release:

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

You can also run the workflow manually from the Actions tab.

## License

GPL-3.0
