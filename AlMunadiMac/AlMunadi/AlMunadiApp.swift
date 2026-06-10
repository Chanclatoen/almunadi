import SwiftUI

@main
struct AlMunadiApp: App {
    @StateObject private var prayerService = PrayerService()

    var body: some Scene {
        MenuBarExtra {
            PrayerTimesView(service: prayerService)
        } label: {
            MenuBarLabel(service: prayerService)
        }
        .menuBarExtraStyle(.window)

        Settings {
            SettingsView(service: prayerService)
        }
    }
}

struct MenuBarLabel: View {
    @ObservedObject var service: PrayerService

    var body: some View {
        let displayMode = service.displayMode
        let prayer = displayMode == "since" ? service.lastPrayer : service.nextPrayer
        let fallback = service.mosqueUrl.isEmpty ? t("set_mosque") : t("next_prayer")
        let text = prayer?.menuBarText(displayMode: displayMode, countdownFormat: service.countdownFormat) ?? fallback

        HStack(spacing: 4) {
            Image(systemName: prayer?.icon ?? "clock")
            if displayMode != "icon" && !text.isEmpty {
                Text(text)
            }
        }
        .help(text)
    }
}
