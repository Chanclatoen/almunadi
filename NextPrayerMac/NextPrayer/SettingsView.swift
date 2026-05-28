import SwiftUI

struct SettingsView: View {
    @ObservedObject var service: PrayerService
    @State private var urlText: String = ""

    var body: some View {
        Form {
            Section {
                TextField("Mawaqit URL", text: $urlText, prompt: Text("https://mawaqit.net/en/w/your-mosque"))
                    .onAppear {
                        urlText = service.mosqueUrl
                    }

                Button("Save") {
                    service.mosqueUrl = urlText
                }
                .disabled(urlText == service.mosqueUrl)
            } header: {
                Text("Mosque Configuration")
            } footer: {
                Text("Go to mawaqit.net, find your mosque, and paste the full URL here.")
                    .foregroundStyle(.secondary)
            }

            if !service.mosqueName.isEmpty {
                Section("Connected Mosque") {
                    LabeledContent("Name", value: service.mosqueName)
                }
            }

            Section {
                Toggle("Launch at login", isOn: launchAtLoginBinding)
            }
        }
        .formStyle(.grouped)
        .frame(width: 420, height: 280)
    }

    private var launchAtLoginBinding: Binding<Bool> {
        Binding(
            get: { UserDefaults.standard.bool(forKey: "launchAtLogin") },
            set: { newValue in
                UserDefaults.standard.set(newValue, forKey: "launchAtLogin")
                SMAppService.setLaunchAtLogin(newValue)
            }
        )
    }
}

import ServiceManagement

extension SMAppService {
    static func setLaunchAtLogin(_ enabled: Bool) {
        let service = SMAppService.mainApp
        do {
            if enabled {
                try service.register()
            } else {
                try service.unregister()
            }
        } catch {
            print("Launch at login error: \(error)")
        }
    }
}
