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

## Building

1. Open Xcode
2. **File > New > Project > macOS > App**
3. Set:
   - Product Name: `NextPrayer`
   - Interface: **SwiftUI**
   - Language: **Swift**
4. Delete the generated `ContentView.swift`
5. Copy all `.swift` files from `NextPrayer/` into the Xcode project
6. Add the `.entitlements` file to the project
7. In project settings:
   - Set **Application is agent (UIElement)** to `YES` in Info.plist (this hides the dock icon)
   - Or add `LSUIElement: true` to Info.plist
8. Build and run

## Configuration

1. Click the menu bar icon
2. Open **Settings**
3. Paste your mosque's Mawaqit URL (e.g. `https://mawaqit.net/en/w/arrahmaan-dordrecht`)
4. Click Save

## License

GPL-3.0
