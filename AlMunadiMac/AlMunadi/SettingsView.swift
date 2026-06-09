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

            // MARK: - Display Mode

            Section(t("display_mode")) {
                Picker(t("display_mode"), selection: displayModeBinding) {
                    Text(t("display_countdown")).tag("countdown")
                    Text(t("display_since")).tag("since")
                    Text(t("display_time")).tag("time")
                    Text(t("display_name")).tag("name")
                    Text(t("display_compact")).tag("compact")
                    Text(t("display_icon")).tag("icon")
                }
                .pickerStyle(.radioGroup)
            }

            // MARK: - Countdown Format

            Section(t("countdown_format")) {
                Picker(t("countdown_format"), selection: countdownBinding) {
                    Text(t("compact")).tag("compact")
                    Text(t("full")).tag("full")
                }
                .pickerStyle(.radioGroup)
            }

            // MARK: - Per-Prayer Notifications

            Section(t("per_prayer_notifications")) {
                ForEach(PrayerSettingsDefaults.notificationKeys, id: \.self) { key in
                    DisclosureGroup(key) {
                        Toggle(t("prayer_notifications"), isOn: prayerNotifEnabledBinding(for: key))
                        Stepper(
                            "\(t("prayer_reminder")): \(prayerNotifReminder(for: key))",
                            value: prayerNotifReminderBinding(for: key),
                            in: 0...120
                        )
                        Picker(t("adhan"), selection: prayerAdhanBinding(for: key)) {
                            Text(t("adhan_global")).tag(Optional<Bool>.none)
                            Text(t("adhan_on")).tag(Optional(true))
                            Text(t("adhan_off")).tag(Optional(false))
                        }
                        Picker(t("dnd_bypass"), selection: prayerDndBypassBinding(for: key)) {
                            Text(t("adhan_global")).tag(Optional<Bool>.none)
                            Text(t("adhan_on")).tag(Optional(true))
                            Text(t("adhan_off")).tag(Optional(false))
                        }
                    }
                }
            }

            // MARK: - Manual Offsets

            Section(t("manual_offsets")) {
                ForEach(PrayerSettingsDefaults.offsetKeys, id: \.self) { key in
                    Stepper(
                        "\(key) \(t("prayer_offset")): \(service.prayerOffsets[key] ?? 0)",
                        value: prayerOffsetBinding(for: key),
                        in: -60...60
                    )
                }
            }

            // MARK: - Notifications

            Section(t("notifications")) {
                Toggle(t("prayer_notifications"), isOn: notificationsBinding)
                Toggle(t("dnd_bypass"), isOn: dndBypassBinding)
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
        .frame(width: 480, height: 780)
    }

    // MARK: - Bindings

    private var displayModeBinding: Binding<String> {
        Binding(
            get: { service.displayMode },
            set: { service.displayMode = $0 }
        )
    }

    private func prayerNotifEnabledBinding(for key: String) -> Binding<Bool> {
        Binding(
            get: { service.prayerNotificationSettings[key]?.enabled ?? true },
            set: { newValue in
                var settings = service.prayerNotificationSettings
                var entry = settings[key] ?? PrayerNotificationSetting()
                entry.enabled = newValue
                settings[key] = entry
                service.prayerNotificationSettings = settings
            }
        )
    }

    private func prayerNotifReminder(for key: String) -> Int {
        service.prayerNotificationSettings[key]?.reminderMinutes ?? 0
    }

    private func prayerNotifReminderBinding(for key: String) -> Binding<Int> {
        Binding(
            get: { service.prayerNotificationSettings[key]?.reminderMinutes ?? 0 },
            set: { newValue in
                var settings = service.prayerNotificationSettings
                var entry = settings[key] ?? PrayerNotificationSetting()
                entry.reminderMinutes = newValue
                settings[key] = entry
                service.prayerNotificationSettings = settings
            }
        )
    }

    private func prayerAdhanBinding(for key: String) -> Binding<Bool?> {
        Binding(
            get: { service.prayerNotificationSettings[key]?.adhanEnabled },
            set: { newValue in
                var settings = service.prayerNotificationSettings
                var entry = settings[key] ?? PrayerNotificationSetting()
                entry.adhanEnabled = newValue
                settings[key] = entry
                service.prayerNotificationSettings = settings
            }
        )
    }

    private func prayerDndBypassBinding(for key: String) -> Binding<Bool?> {
        Binding(
            get: { service.prayerNotificationSettings[key]?.dndBypass },
            set: { newValue in
                var settings = service.prayerNotificationSettings
                var entry = settings[key] ?? PrayerNotificationSetting()
                entry.dndBypass = newValue
                settings[key] = entry
                service.prayerNotificationSettings = settings
            }
        )
    }

    private func prayerOffsetBinding(for key: String) -> Binding<Int> {
        Binding(
            get: { service.prayerOffsets[key] ?? 0 },
            set: { newValue in
                var offsets = service.prayerOffsets
                offsets[key] = newValue
                service.prayerOffsets = offsets
            }
        )
    }

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

    private var dndBypassBinding: Binding<Bool> {
        Binding(
            get: { service.dndBypass },
            set: { service.dndBypass = $0 }
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
