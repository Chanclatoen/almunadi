# Next Prayer (Mawaqit) - macOS Menu Bar App

A native macOS menu bar app that displays the next Islamic prayer time, powered by [Mawaqit](https://mawaqit.net).

## Features

- Shows next prayer name, time, and countdown in the macOS menu bar
- Contextual icons: sunrise, sun, clouds, sunset, moon
- Click to see all prayer times in a dropdown
- Next prayer highlighted in blue, past prayers dimmed
- Native macOS notifications at each prayer time
- Launch at login support
- Configure any Mawaqit mosque URL

## Requirements

- macOS 14+ (Sonoma)
- Xcode 15+

## Install (download)

1. Grab the latest `NextPrayer-macOS-*.zip` from the [Releases](https://github.com/Chanclatoen/next-prayer-mawaqit/releases) page.
2. Unzip and drag `NextPrayer.app` into `/Applications`.
3. The app is ad-hoc signed (not notarized), so the first launch is blocked by Gatekeeper.
   Right-click the app → **Open** → **Open**, or run:
   ```bash
   xattr -dr com.apple.quarantine /Applications/NextPrayer.app
   ```
4. The icon appears in the menu bar (there is no Dock icon).

## Building from source

The Xcode project is generated from [`project.yml`](project.yml) with [XcodeGen](https://github.com/yonaskolb/XcodeGen).

### Open in Xcode

The committed `NextPrayer.xcodeproj` is ready to use:

```bash
open NextPrayer.xcodeproj
```

Select the `NextPrayer` scheme and Build & Run (⌘R).

### Build a distributable zip from the command line

```bash
brew install xcodegen        # only needed if you change project.yml
./scripts/build-release.sh   # outputs dist/NextPrayer-macOS-v<version>.zip
```

If you edit `project.yml`, regenerate the project with `xcodegen generate`.

## Releasing

Pushing a tag that starts with `mac-v` triggers the
[`macOS Release`](../.github/workflows/macos-release.yml) GitHub Actions workflow,
which builds the app and attaches the zip to a GitHub Release:

```bash
git tag mac-v1.0.0
git push origin mac-v1.0.0
```

You can also run the workflow manually from the Actions tab (it uploads the zip as a build artifact).

## Configuration

1. Click the menu bar icon
2. Open **Settings**
3. Paste your mosque's Mawaqit URL (e.g. `https://mawaqit.net/en/w/arrahmaan-dordrecht`)
4. Click Save

## License

GPL-3.0
