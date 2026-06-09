import SwiftUI
import UniformTypeIdentifiers

struct SettingsView: View {
    @ObservedObject var service: PrayerService
    @State private var urlText: String = ""
    @State private var searchQuery: String = ""
    @State private var adhanPathText: String = ""

    var body: some View {
        Form {
            Section(t("find_mosque")) {
                HStack {
                    TextField(t("search_placeholder"), text: $searchQuery)
                        .onSubmit { service.searchMosques(query: searchQuery) }
                    Button(t("search")) {
                        service.searchMosques(query: searchQuery)
                    }
                    .disabled(searchQuery.trimmingCharacters(in: .whitespaces).isEmpty)
                }

                if service.isSearching {
                    ProgressView()
                        .controlSize(.small)
                }

                if !service.searchResults.isEmpty {
                    List(service.searchResults) { mosque in
                        VStack(alignment: .leading) {
                            Text(mosque.name)
                                .fontWeight(.medium)
                            if !mosque.localisation.isEmpty {
                                Text(mosque.localisation)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                    .lineLimit(1)
                            }
                        }
                        .contentShape(Rectangle())
                        .onTapGesture {
                            service.selectMosque(mosque)
                            urlText = service.mosqueUrl
                            searchQuery = ""
                        }
                    }
                    .frame(height: min(CGFloat(service.searchResults.count) * 44, 200))
                }
            }

            Section {
                TextField(t("mawaqit_url"), text: $urlText, prompt: Text("https://mawaqit.net/en/w/your-mosque"))
                    .onAppear {
                        urlText = service.mosqueUrl
                        adhanPathText = service.adhanPath
                    }

                Button(t("save")) {
                    service.mosqueUrl = urlText
                }
                .disabled(urlText == service.mosqueUrl)
            } header: {
                Text(t("paste_url"))
            } footer: {
                Text(t("paste_url_footer"))
                    .foregroundStyle(.secondary)
            }

            if !service.mosqueName.isEmpty {
                Section(t("connected_mosque")) {
                    LabeledContent(t("name"), value: service.mosqueName)
                }
            }

            // MARK: - Saved Mosques

            Section(t("saved_mosques")) {
                if service.savedMosques.isEmpty {
                    Text(t("no_saved_mosques"))
                        .foregroundStyle(.secondary)
                } else {
                    ForEach(Array(service.savedMosques.enumerated()), id: \.element.id) { index, mosque in
                        HStack {
                            VStack(alignment: .leading) {
                                Text(mosque.name.isEmpty ? mosque.url : mosque.name)
                                    .fontWeight(.medium)
                                if !mosque.name.isEmpty {
                                    Text(mosque.url)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                        .lineLimit(1)
                                }
                            }

                            Spacer()

                            Button(t("switch_mosque")) {
                                service.switchToMosque(mosque)
                                urlText = service.mosqueUrl
                            }
                            .controlSize(.small)

                            Button(role: .destructive) {
                                service.removeMosque(at: index)
                            } label: {
                                Image(systemName: "trash")
                            }
                            .controlSize(.small)
                        }
                    }
                }

                if !service.mosqueUrl.isEmpty {
                    Button(t("save_current")) {
                        service.saveMosque(url: service.mosqueUrl, name: service.mosqueName)
                    }
                }
            }

            // MARK: - Language

            Section(t("language")) {
                Picker(t("language"), selection: languageBinding) {
                    ForEach(Translations.supportedLanguages, id: \.code) { lang in
                        Text(lang.label).tag(lang.code)
                    }
                }
            }

            // MARK: - Countdown Format

            Section(t("countdown_format")) {
                Picker(t("countdown_format"), selection: countdownBinding) {
                    Text(t("compact")).tag("compact")
                    Text(t("full")).tag("full")
                }
                .pickerStyle(.radioGroup)
            }

            // MARK: - Notifications

            Section(t("notifications")) {
                Toggle(t("prayer_notifications"), isOn: notificationsBinding)
            }

            // MARK: - Adhan

            Section(t("adhan")) {
                Toggle(t("enable_adhan"), isOn: adhanEnabledBinding)

                HStack {
                    TextField(t("adhan_path_placeholder"), text: $adhanPathText)
                        .onChange(of: adhanPathText) { _, newValue in
                            service.adhanPath = newValue
                        }
                    Button(t("choose_file")) {
                        chooseAdhanFile()
                    }
                }
                .disabled(!service.adhanEnabled)
            }

            // MARK: - Launch at Login

            Section {
                Toggle(t("launch_at_login"), isOn: launchAtLoginBinding)
            }
        }
        .formStyle(.grouped)
        .frame(width: 480, height: 680)
    }

    // MARK: - Bindings

    private var languageBinding: Binding<String> {
        Binding(
            get: { service.language },
            set: { service.setLanguage($0) }
        )
    }

    private var countdownBinding: Binding<String> {
        Binding(
            get: { service.countdownFormat },
            set: { service.countdownFormat = $0 }
        )
    }

    private var notificationsBinding: Binding<Bool> {
        Binding(
            get: { service.notificationsEnabled },
            set: { service.notificationsEnabled = $0 }
        )
    }

    private var adhanEnabledBinding: Binding<Bool> {
        Binding(
            get: { service.adhanEnabled },
            set: { service.adhanEnabled = $0 }
        )
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

    // MARK: - File Picker

    private func chooseAdhanFile() {
        let panel = NSOpenPanel()
        panel.allowedContentTypes = [.audio]
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = false
        panel.message = "Select an adhan audio file (MP3, WAV, etc.)"

        if panel.runModal() == .OK, let url = panel.url {
            adhanPathText = url.path
            service.adhanPath = url.path
        }
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
