# Al Munadi — macOS

A native macOS menu bar app that displays the next Islamic prayer time, powered by [Mawaqit](https://mawaqit.net).

## Install

### Option 1: Download (recommended)

1. Download `AlMunadi-macOS-*.zip` from the [latest release](https://github.com/Chanclatoen/almunadi/releases)
2. Unzip and drag `AlMunadi.app` into `/Applications`
3. Double-click to open. Releases are signed with a Developer ID and notarized by Apple, so Gatekeeper allows them with no extra steps.
   - If you build an unsigned/ad-hoc copy yourself and Gatekeeper blocks it, run: `xattr -dr com.apple.quarantine /Applications/AlMunadi.app`
4. The icon appears in your menu bar (there is no Dock icon)
5. Click the menu bar icon → **Settings** → search for your mosque

### Option 2: Build from source

Requires macOS 14+ (Sonoma) and Xcode 15+.

The Xcode project is generated from `project.yml` by [XcodeGen](https://github.com/yonaskolb/XcodeGen) (it is not committed):

```bash
brew install xcodegen
xcodegen generate
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

The widget extension reads from the App Group `PM49C5H4XK.net.almunadi.AlMunadi`. The main app writes the prayer snapshot to this group after every successful Mawaqit fetch via `WidgetSharedStore.saveSnapshot(...)` and calls `WidgetCenter.shared.reloadAllTimelines()` so the widget refreshes immediately.

**Team ID prefix**: macOS Developer ID (non-App-Store) builds require the App Group to be prefixed with the team ID (`<TeamID>.<group>`), so it is set to `PM49C5H4XK.net.almunadi.AlMunadi`. This identifier appears in three places that must stay in sync, and must be registered under the team's identifiers on developer.apple.com:

1. `com.apple.security.application-groups` in both `AlMunadi/AlMunadi.entitlements` and `AlMunadiWidget/AlMunadiWidget.entitlements`.
2. The `appGroupID` constant in `Shared/WidgetSharedStore.swift`.

If you build under a different team, replace `PM49C5H4XK` with your own Team ID in all three.

## Time-sensitive notifications (DND bypass) — disabled pending a provisioning profile

The DND-bypass option sets notifications to `.timeSensitive` so they pierce Focus.
That requires the `com.apple.developer.usernotifications.time-sensitive` entitlement,
which under Developer ID signing must be backed by an **embedded provisioning profile**
— something the CI release does not currently manage. The entitlement is therefore
omitted, and such notifications are delivered at the normal (`.active`) level instead.
The code path is unchanged, so re-enabling is just configuration.

To restore the feature:

1. On developer.apple.com, enable **Time Sensitive Notifications** for the App ID
   `net.almunadi.AlMunadi`.
2. Create a **Developer ID** provisioning profile for that App ID and download it.
3. Add the profile to CI (e.g. a base64 secret), install it into
   `~/Library/MobileDevice/Provisioning Profiles/` during the build, and embed it
   (`PROVISIONING_PROFILE_SPECIFIER` / copy as `embedded.provisionprofile`).
4. Re-add the `com.apple.developer.usernotifications.time-sensitive` key to
   `AlMunadi/AlMunadi.entitlements`.

## Releasing

Pushing a repository `v*` release tag triggers the [macOS Release](../.github/workflows/macos-release.yml) GitHub Actions workflow, which builds the app and attaches the zip to the GitHub Release:

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

You can also run the workflow manually from the Actions tab.

## License

GPL-3.0
