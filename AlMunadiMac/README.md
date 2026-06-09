# Al Munadi — macOS

A native macOS menu bar app that displays the next Islamic prayer time, powered by [Mawaqit](https://mawaqit.net).

## Install

### Option 1: Download (recommended)

1. Download `AlMunadi-macOS-*.zip` from the [latest release](https://github.com/Chanclatoen/almunadi/releases)
2. Unzip and drag `AlMunadi.app` into `/Applications`
3. The app is ad-hoc signed (not notarized), so the first launch is blocked by Gatekeeper. Either:
   - Right-click the app → **Open** → **Open**, or
   - Run: `xattr -dr com.apple.quarantine /Applications/AlMunadi.app`
4. The icon appears in your menu bar (there is no Dock icon)
5. Click the menu bar icon → **Settings** → search for your mosque

### Option 2: Build from source

Requires macOS 14+ (Sonoma) and Xcode 15+.

The committed `AlMunadi.xcodeproj` is ready to use:

```bash
open AlMunadi.xcodeproj
```

Select the **AlMunadi** scheme and press ⌘R to build and run.

To build a distributable zip from the command line:

```bash
brew install xcodegen        # only needed if you change project.yml
./scripts/build-release.sh   # outputs dist/AlMunadi-macOS-v<version>.zip
```

If you edit `project.yml`, regenerate the project with `xcodegen generate`.

## Features

- **Menu bar display** — next prayer name, time, and live countdown with contextual icons (sunrise, sun, clouds, sunset, moon)
- **Desktop widget** (small / medium / large, macOS 14+) — next prayer + countdown, all 5 prayers, or full layout with iqama, Hijri date and Qibla direction; reloads at each prayer-time transition. Add via right-click on the desktop → **Edit Widgets** → Al Munadi.
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
| Launch at login | Start AlMunadi when you log in |

## Widget data sharing (App Group)

The widget extension reads from the App Group `group.net.almunadi.AlMunadi`. The main app writes the prayer snapshot to this group after every successful Mawaqit fetch via `WidgetSharedStore.saveSnapshot(...)` and calls `WidgetCenter.shared.reloadAllTimelines()` so the widget refreshes immediately.

**Team ID prefix for distribution**: the current App Group identifier works locally with ad-hoc signing. For a notarized release through an Apple Developer team, App Groups must be prefixed with the team ID — e.g. `group.<TEAMID>.almunadi`. When a team ID is wired in:

1. Update `com.apple.security.application-groups` in both `AlMunadi/AlMunadi.entitlements` and `AlMunadiWidget/AlMunadiWidget.entitlements`.
2. Update the `appGroupID` constant in `Shared/WidgetSharedStore.swift`.
3. Register the new App Group on developer.apple.com under the team's identifiers.

## Releasing

Pushing a repository `v*` release tag triggers the [macOS Release](../.github/workflows/macos-release.yml) GitHub Actions workflow, which builds the app and attaches the zip to the GitHub Release:

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

You can also run the workflow manually from the Actions tab.

## License

GPL-3.0
