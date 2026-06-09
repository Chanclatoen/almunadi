import SwiftUI

@main
struct NextPrayerApp: App {
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
        let next = service.nextPrayer
        HStack(spacing: 4) {
            Image(systemName: next?.icon ?? "clock")
            Text(next?.menuBarText ?? t("next_prayer"))
        }
    }
}
