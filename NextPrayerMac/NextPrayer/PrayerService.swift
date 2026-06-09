import Foundation
import Combine
import UserNotifications
import AVFoundation

class PrayerService: ObservableObject {
    static let appVersion = "1.0.1"
    static let tagPrefix = "v"
    private static let releasesURL = "https://api.github.com/repos/Chanclatoen/next-prayer-mawaqit/releases"
    private static let repoReleasesPage = "https://github.com/Chanclatoen/next-prayer-mawaqit/releases"

    @Published var prayers: [PrayerTime] = []
    @Published var shuruq: String?
    @Published var mosqueName: String = ""
    @Published var nextPrayer: PrayerTime?
    @Published var lastError: String?
    @Published var isCached: Bool = false
    @Published var jumua2: String?
    @Published var searchResults: [MosqueSearchResult] = []
    @Published var isSearching: Bool = false
    @Published var savedMosques: [SavedMosque] = []
    @Published var language: String = UserDefaults.standard.string(forKey: "language") ?? "en"
    @Published var updateInfo: (version: String, url: String)?

    private var updateTimer: AnyCancellable?
    private var notificationTimers: [Timer] = []
    private var updateCheckTimer: Timer?
    private let calendar = Calendar.current
    private static let apiBase = "https://mawaqit.net/api/2.0/mosque"
    private var audioPlayer: AVAudioPlayer?
    private var cachedMawaqitData: MawaqitData?

    var notificationsEnabled: Bool {
        get { UserDefaults.standard.object(forKey: "notificationsEnabled") as? Bool ?? true }
        set {
            UserDefaults.standard.set(newValue, forKey: "notificationsEnabled")
            if newValue { scheduleNotifications() } else { cancelNotifications() }
        }
    }

    var adhanEnabled: Bool {
        get { UserDefaults.standard.bool(forKey: "adhanEnabled") }
        set { UserDefaults.standard.set(newValue, forKey: "adhanEnabled") }
    }

    var adhanPath: String {
        get { UserDefaults.standard.string(forKey: "adhanPath") ?? "" }
        set { UserDefaults.standard.set(newValue, forKey: "adhanPath") }
    }

    var countdownFormat: String {
        get { UserDefaults.standard.string(forKey: "countdownFormat") ?? "compact" }
        set {
            UserDefaults.standard.set(newValue, forKey: "countdownFormat")
            objectWillChange.send()
        }
    }

    var displayMode: String {
        get { UserDefaults.standard.string(forKey: "displayMode") ?? "countdown" }
        set {
            UserDefaults.standard.set(newValue, forKey: "displayMode")
            objectWillChange.send()
        }
    }

    var prayerNotificationSettings: [String: PrayerNotificationSetting] {
        get {
            guard let data = UserDefaults.standard.data(forKey: "prayerNotificationSettings"),
                  let stored = try? JSONDecoder().decode([String: PrayerNotificationSetting].self, from: data)
            else { return PrayerSettingsDefaults.defaultNotificationSettings() }
            return PrayerSettingsDefaults.mergeNotificationSettings(stored)
        }
        set {
            if let data = try? JSONEncoder().encode(newValue) {
                UserDefaults.standard.set(data, forKey: "prayerNotificationSettings")
            }
            scheduleNotifications()
        }
    }

    var prayerOffsets: [String: Int] {
        get {
            guard let data = UserDefaults.standard.data(forKey: "prayerOffsets"),
                  let stored = try? JSONDecoder().decode([String: Int].self, from: data)
            else { return PrayerSettingsDefaults.defaultOffsets() }
            return PrayerSettingsDefaults.mergeOffsets(stored)
        }
        set {
            if let data = try? JSONEncoder().encode(newValue) {
                UserDefaults.standard.set(data, forKey: "prayerOffsets")
            }
            applyOffsetsToPrayers()
            scheduleNotifications()
            objectWillChange.send()
        }
    }

    init() {
        loadSavedMosques()
        migrateSettingsIfNeeded()
        requestNotificationPermission()
        startUpdateTimer()
        loadCache()
        fetchIfConfigured()
        checkForUpdate()
        updateCheckTimer = Timer.scheduledTimer(withTimeInterval: 86400, repeats: true) { [weak self] _ in
            self?.checkForUpdate()
        }
    }

    var mosqueUrl: String {
        get { UserDefaults.standard.string(forKey: "mosqueUrl") ?? "" }
        set {
            UserDefaults.standard.set(newValue, forKey: "mosqueUrl")
            fetchTimes()
        }
    }

    // MARK: - Settings migration

    private func migrateSettingsIfNeeded() {
        if UserDefaults.standard.data(forKey: "prayerNotificationSettings") == nil {
            prayerNotificationSettings = PrayerSettingsDefaults.defaultNotificationSettings()
        }
        if UserDefaults.standard.data(forKey: "prayerOffsets") == nil {
            prayerOffsets = PrayerSettingsDefaults.defaultOffsets()
        }
        if UserDefaults.standard.string(forKey: "displayMode") == nil {
            displayMode = "countdown"
        }
    }

    private func applyOffset(to timeStr: String, minutes: Int) -> String {
        guard minutes != 0 else { return timeStr }
        let parts = timeStr.split(separator: ":").compactMap { Int($0) }
        guard parts.count == 2 else { return timeStr }
        var total = parts[0] * 60 + parts[1] + minutes
        total = ((total % 1440) + 1440) % 1440
        return String(format: "%02d:%02d", total / 60, total % 60)
    }

    private func minutes(from timeStr: String) -> Int? {
        let parts = timeStr.split(separator: ":").compactMap { Int($0) }
        guard parts.count == 2 else { return nil }
        return parts[0] * 60 + parts[1]
    }

    private func datesForAdjustedTimes(_ times: [String], relativeTo date: Date) -> [Date?] {
        let minuteValues = times.map { minutes(from: $0) }
        guard !minuteValues.isEmpty else { return [] }

        var dates = Array<Date?>(repeating: nil, count: times.count)
        var dayOffset = 0
        var previousAbsolute: Int?

        for (index, minuteValue) in minuteValues.enumerated() {
            guard let minuteValue else { continue }
            if index == 0,
               minuteValues.count > 1,
               let nextMinute = minuteValues[1],
               minuteValue > nextMinute {
                dayOffset = -1
            } else if index > 0 {
                if dayOffset < 0 { dayOffset = 0 }
                while let previousAbsolute, minuteValue + dayOffset * 1440 <= previousAbsolute {
                    dayOffset += 1
                }
            }

            let absoluteMinutes = minuteValue + dayOffset * 1440
            previousAbsolute = absoluteMinutes
            guard let baseDate = dateFromTimeString(times[index], relativeTo: date) else { continue }
            dates[index] = calendar.date(byAdding: .day, value: dayOffset, to: baseDate)
        }

        return dates
    }

    private func applyOffsetsToPrayers() {
        guard let data = cachedMawaqitData else { return }
        applyData(data, fromCache: isCached)
    }

    // MARK: - Language

    func setLanguage(_ lang: String) {
        UserDefaults.standard.set(lang, forKey: "language")
        language = lang
        // Re-apply display names for current prayers
        updateDisplayNames()
    }

    private func updateDisplayNames() {
        let showJumuah = isFriday()
        for i in prayers.indices {
            let prayer = prayers[i]
            if prayer.name == .dhuhr && showJumuah {
                prayers[i].displayName = t("jumuah")
            } else {
                prayers[i].displayName = Translations.shared.translatedPrayerName(prayer.name)
            }
        }
        updateNextPrayer()
    }

    // MARK: - Multi-Mosque

    private func loadSavedMosques() {
        guard let data = UserDefaults.standard.data(forKey: "savedMosques"),
              let mosques = try? JSONDecoder().decode([SavedMosque].self, from: data)
        else { return }
        savedMosques = mosques
    }

    private func persistSavedMosques() {
        if let data = try? JSONEncoder().encode(savedMosques) {
            UserDefaults.standard.set(data, forKey: "savedMosques")
        }
    }

    func saveMosque(url: String, name: String) {
        guard !url.isEmpty else { return }
        // Avoid duplicates
        if savedMosques.contains(where: { $0.url == url }) { return }
        savedMosques.append(SavedMosque(url: url, name: name))
        persistSavedMosques()
    }

    func removeMosque(at index: Int) {
        guard savedMosques.indices.contains(index) else { return }
        savedMosques.remove(at: index)
        persistSavedMosques()
    }

    func switchToMosque(_ mosque: SavedMosque) {
        mosqueUrl = mosque.url
    }

    // MARK: - Adhan

    private func playAdhan(force: Bool = false) {
        guard force || adhanEnabled else { return }
        let path = adhanPath
        guard !path.isEmpty else { return }
        let fileURL = URL(fileURLWithPath: path)
        guard FileManager.default.fileExists(atPath: path) else { return }

        do {
            audioPlayer = try AVAudioPlayer(contentsOf: fileURL)
            audioPlayer?.play()
        } catch {
            print("Adhan playback error: \(error)")
        }
    }

    // MARK: - Update Check

    func checkForUpdate() {
        guard let url = URL(string: Self.releasesURL) else { return }
        var request = URLRequest(url: url)
        request.timeoutInterval = 10

        URLSession.shared.dataTask(with: request) { [weak self] data, _, error in
            guard let self, error == nil, let data,
                  let releases = try? JSONSerialization.jsonObject(with: data) as? [[String: Any]]
            else { return }

            for release in releases {
                guard let tag = release["tag_name"] as? String,
                      tag.hasPrefix(Self.tagPrefix)
                else { continue }

                let latest = String(tag.dropFirst(Self.tagPrefix.count))
                let currentParts = Self.appVersion.split(separator: ".").compactMap { Int($0) }
                let latestParts = latest.split(separator: ".").compactMap { Int($0) }

                var newer = false
                for i in 0..<max(currentParts.count, latestParts.count) {
                    let c = i < currentParts.count ? currentParts[i] : 0
                    let l = i < latestParts.count ? latestParts[i] : 0
                    if l > c { newer = true; break }
                    if l < c { break }
                }

                if newer {
                    let htmlUrl = (release["html_url"] as? String) ?? Self.repoReleasesPage
                    DispatchQueue.main.async {
                        self.updateInfo = (version: latest, url: htmlUrl)
                    }
                }
                return // Only check the first matching release
            }
        }.resume()
    }

    // MARK: - Fetch

    func fetchIfConfigured() {
        guard !mosqueUrl.isEmpty else { return }
        fetchTimes()
    }

    func fetchTimes() {
        let urlString = mosqueUrl
        guard !urlString.isEmpty else {
            lastError = "No mosque URL configured"
            return
        }

        if let slug = extractSlug(from: urlString) {
            fetchTimesApi(slug: slug) { [weak self] success in
                if !success {
                    self?.fetchTimesHtml(urlString: urlString)
                }
            }
        } else {
            fetchTimesHtml(urlString: urlString)
        }
    }

    private func fetchTimesApi(slug: String, completion: @escaping (Bool) -> Void) {
        guard let url = URL(string: "\(Self.apiBase)/search?word=\(slug)") else {
            completion(false)
            return
        }

        var request = URLRequest(url: url)
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.timeoutInterval = 15

        URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            DispatchQueue.main.async {
                guard let self else { return }

                guard error == nil,
                      let data,
                      let results = try? JSONSerialization.jsonObject(with: data) as? [[String: Any]],
                      let mosque = results.first,
                      let apiTimes = mosque["times"] as? [String],
                      apiTimes.count >= 6
                else {
                    completion(false)
                    return
                }

                let times = [apiTimes[0], apiTimes[2], apiTimes[3], apiTimes[4], apiTimes[5]]
                let shuruq = apiTimes[1]
                let name = (mosque["name"] as? String) ?? (mosque["label"] as? String) ?? ""
                let iqama = mosque["iqama"] as? [String]
                let iqamaEnabled = mosque["iqamaEnabled"] as? Bool ?? false
                let jumua = mosque["jumua"] as? String
                let jumua2 = mosque["jumua2"] as? String

                let mawaqitData = MawaqitData(
                    times: times,
                    shuruq: shuruq,
                    mosqueName: name,
                    iqama: iqama,
                    iqamaEnabled: iqamaEnabled,
                    jumua: jumua,
                    jumua2: jumua2
                )
                self.applyData(mawaqitData)
                self.scheduleDailyRefresh()
                completion(true)
            }
        }.resume()
    }

    private func fetchTimesHtml(urlString: String) {
        var fetchUrl = urlString
        if !fetchUrl.contains("/w/") {
            if let slug = extractSlug(from: fetchUrl) {
                fetchUrl = "https://mawaqit.net/en/w/\(slug)"
            }
        }

        guard let url = URL(string: fetchUrl) else {
            handleFetchError("Invalid URL")
            return
        }

        lastError = nil

        URLSession.shared.dataTask(with: url) { [weak self] data, response, error in
            DispatchQueue.main.async {
                guard let self else { return }

                if let error {
                    self.handleFetchError("Could not reach mawaqit.net: \(error.localizedDescription)")
                    return
                }

                guard let data, let html = String(data: data, encoding: .utf8) else {
                    self.handleFetchError("Could not read response")
                    return
                }

                if let mawaqitData = self.parseConfData(html) {
                    self.applyData(mawaqitData)
                    self.scheduleDailyRefresh()
                } else {
                    self.handleFetchError("Could not parse prayer times")
                }
            }
        }.resume()
    }

    func searchMosques(query: String) {
        guard !query.trimmingCharacters(in: .whitespaces).isEmpty else {
            searchResults = []
            return
        }

        isSearching = true
        let encoded = query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? query
        guard let url = URL(string: "\(Self.apiBase)/search?word=\(encoded)") else {
            isSearching = false
            return
        }

        var request = URLRequest(url: url)
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.timeoutInterval = 15

        URLSession.shared.dataTask(with: request) { [weak self] data, _, _ in
            DispatchQueue.main.async {
                guard let self else { return }
                self.isSearching = false

                guard let data,
                      let results = try? JSONSerialization.jsonObject(with: data) as? [[String: Any]]
                else {
                    self.searchResults = []
                    return
                }

                self.searchResults = results.prefix(10).compactMap { m in
                    guard let slug = m["slug"] as? String else { return nil }
                    return MosqueSearchResult(
                        id: m["uuid"] as? String ?? slug,
                        name: (m["name"] as? String) ?? "",
                        slug: slug,
                        localisation: (m["localisation"] as? String) ?? ""
                    )
                }
            }
        }.resume()
    }

    func selectMosque(_ mosque: MosqueSearchResult) {
        mosqueUrl = "https://mawaqit.net/en/w/\(mosque.slug)"
        searchResults = []
    }

    private func extractSlug(from url: String) -> String? {
        let pattern = #"mawaqit\.net/\w+/(?:w/)?(.+?)/?$"#
        guard let regex = try? NSRegularExpression(pattern: pattern),
              let match = regex.firstMatch(in: url, range: NSRange(url.startIndex..., in: url)),
              let range = Range(match.range(at: 1), in: url)
        else { return nil }
        return String(url[range])
    }

    private func parseConfData(_ html: String) -> MawaqitData? {
        let pattern = #"confData\s*=\s*(\{.*?\});"#
        guard let regex = try? NSRegularExpression(pattern: pattern, options: .dotMatchesLineSeparators),
              let match = regex.firstMatch(in: html, range: NSRange(html.startIndex..., in: html)),
              let range = Range(match.range(at: 1), in: html)
        else { return nil }

        let jsonString = String(html[range])
        guard let jsonData = jsonString.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: jsonData) as? [String: Any],
              let times = json["times"] as? [String]
        else { return nil }

        let shuruq = json["shuruq"] as? String
        let name = (json["name"] as? String) ?? (json["label"] as? String) ?? ""

        return MawaqitData(times: times, shuruq: shuruq, mosqueName: name)
    }

    private func resolveIqama(prayerTime: String, iqamaValue: String?) -> String? {
        guard let val = iqamaValue?.trimmingCharacters(in: .whitespaces),
              !val.isEmpty, val != "0", val != "+0"
        else { return nil }
        if val.contains(":") { return val }
        let cleanVal = val.hasPrefix("+") ? String(val.dropFirst()) : val
        guard let offset = Int(cleanVal), offset > 0,
              let prayerDate = dateFromTimeString(prayerTime, relativeTo: Date())
        else { return nil }
        let iqamaDate = prayerDate.addingTimeInterval(Double(offset * 60))
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        return formatter.string(from: iqamaDate)
    }

    private func isFriday() -> Bool {
        calendar.component(.weekday, from: Date()) == 6
    }

    private func saveCache(_ data: MawaqitData) {
        var cacheData = data
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        cacheData.cacheDate = formatter.string(from: Date())
        if let encoded = try? JSONEncoder().encode(cacheData) {
            UserDefaults.standard.set(encoded, forKey: "cachedPrayerData")
        }
    }

    private func loadCache() {
        guard let data = UserDefaults.standard.data(forKey: "cachedPrayerData"),
              let cached = try? JSONDecoder().decode(MawaqitData.self, from: data),
              !cached.times.isEmpty
        else { return }
        isCached = true
        applyData(cached, fromCache: true)
    }

    private func applyData(_ data: MawaqitData, fromCache: Bool = false) {
        cachedMawaqitData = data
        let names = PrayerName.allCases
        let today = Date()
        let showJumuah = isFriday() && data.jumua != nil
        let offsets = prayerOffsets

        let adjustedTimes = names.enumerated().compactMap { i, name -> String? in
            guard i < data.times.count else { return nil }
            var timeStr = data.times[i]
            if i == 1 && showJumuah, let jumuaTime = data.jumua {
                timeStr = jumuaTime
            }
            return applyOffset(to: timeStr, minutes: offsets[name.rawValue] ?? 0)
        }
        let adjustedDates = datesForAdjustedTimes(adjustedTimes, relativeTo: today)

        var prayerTimes: [PrayerTime] = []
        for (i, name) in names.enumerated() where i < data.times.count {
            var timeStr = data.times[i]
            var displayName = Translations.shared.translatedPrayerName(name)
            let notifKey = PrayerSettingsDefaults.notificationKey(for: i, isFriday: showJumuah, hasJumua: data.jumua != nil)

            if i == 1 && showJumuah, let jumuaTime = data.jumua {
                timeStr = jumuaTime
                displayName = t("jumuah")
            }

            let adjustedTime = i < adjustedTimes.count ? adjustedTimes[i] : applyOffset(to: timeStr, minutes: offsets[name.rawValue] ?? 0)

            if i < adjustedDates.count, let date = adjustedDates[i] {
                var iqamaTime: String? = nil
                if data.iqamaEnabled == true, let iqama = data.iqama, i < iqama.count {
                    iqamaTime = resolveIqama(prayerTime: data.times[i], iqamaValue: iqama[i])
                }
                prayerTimes.append(PrayerTime(
                    id: name,
                    name: name,
                    time: adjustedTime,
                    date: date,
                    displayName: displayName,
                    iqamaTime: iqamaTime,
                    notificationKey: notifKey
                ))
            }
        }

        prayers = prayerTimes
        shuruq = data.shuruq
        mosqueName = data.mosqueName
        jumua2 = (showJumuah ? data.jumua2 : nil)

        if !fromCache {
            isCached = false
            lastError = nil
            saveCache(data)
        }
        updateNextPrayer()
        scheduleNotifications()
    }

    private func handleFetchError(_ message: String) {
        lastError = message
        if prayers.isEmpty { loadCache() }
        retryFetchLater()
    }

    private func dateFromTimeString(_ timeStr: String, relativeTo date: Date) -> Date? {
        let parts = timeStr.split(separator: ":").compactMap { Int($0) }
        guard parts.count == 2 else { return nil }
        return calendar.date(bySettingHour: parts[0], minute: parts[1], second: 0, of: date)
    }

    private func startUpdateTimer() {
        updateTimer = Timer.publish(every: 60, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in
                self?.updateNextPrayer()
            }
    }

    private func updateNextPrayer() {
        let now = Date()
        if let next = prayers.first(where: { $0.date > now }) {
            nextPrayer = next
        } else if let first = prayers.first {
            if let tomorrow = calendar.date(byAdding: .day, value: 1, to: first.date) {
                nextPrayer = PrayerTime(
                    id: first.name,
                    name: first.name,
                    time: first.time,
                    date: tomorrow,
                    displayName: first.displayName,
                    iqamaTime: first.iqamaTime,
                    notificationKey: first.notificationKey
                )
            }
        }
        objectWillChange.send()
    }

    private func cancelNotifications() {
        notificationTimers.forEach { $0.invalidate() }
        notificationTimers.removeAll()
    }

    private func scheduleNotifications() {
        cancelNotifications()
        guard notificationsEnabled else { return }

        let now = Date()
        let settings = prayerNotificationSettings
        var prayersToSchedule = prayers
        if let first = prayers.first,
           first.date <= now,
           let tomorrow = calendar.date(byAdding: .day, value: 1, to: first.date) {
            prayersToSchedule.append(PrayerTime(
                id: first.name,
                name: first.name,
                time: first.time,
                date: tomorrow,
                displayName: first.displayName,
                iqamaTime: first.iqamaTime,
                notificationKey: first.notificationKey
            ))
        }

        for prayer in prayersToSchedule {
            let setting = settings[prayer.notificationKey] ?? PrayerNotificationSetting()
            guard setting.enabled else { continue }

            if setting.reminderMinutes > 0 {
                let reminderDate = prayer.date.addingTimeInterval(-Double(setting.reminderMinutes * 60))
                let reminderDelay = reminderDate.timeIntervalSince(now)
                if reminderDelay > 0 {
                    let timer = Timer.scheduledTimer(withTimeInterval: reminderDelay, repeats: false) { [weak self] _ in
                        self?.sendReminderNotification(prayer: prayer, minutes: setting.reminderMinutes)
                    }
                    notificationTimers.append(timer)
                }
            }

            let delay = prayer.date.timeIntervalSince(now)
            guard delay > 0 else { continue }

            let playAdhan = PrayerSettingsDefaults.shouldPlayAdhan(setting, globalEnabled: adhanEnabled)
            let timer = Timer.scheduledTimer(withTimeInterval: delay, repeats: false) { [weak self] _ in
                self?.sendNotification(prayer: prayer)
                if playAdhan { self?.playAdhan(force: true) }
                self?.updateNextPrayer()
            }
            notificationTimers.append(timer)
        }
    }

    private func sendReminderNotification(prayer: PrayerTime, minutes: Int) {
        let content = UNMutableNotificationContent()
        content.title = String(format: t("prayer_time_title"), prayer.displayName, "\(minutes)m")
        content.body = String(format: t("reminder_body"), prayer.displayName, minutes)
        content.sound = .default

        let request = UNNotificationRequest(
            identifier: "prayer-reminder-\(prayer.name.rawValue)",
            content: content,
            trigger: nil
        )
        UNUserNotificationCenter.current().add(request)
    }

    private func requestNotificationPermission() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound]) { _, _ in }
    }

    private func sendNotification(prayer: PrayerTime) {
        let content = UNMutableNotificationContent()
        content.title = String(format: t("prayer_time_title"), prayer.displayName, prayer.time)
        content.body = String(format: t("prayer_time_body"), prayer.displayName)
        content.sound = .default

        let request = UNNotificationRequest(
            identifier: "prayer-\(prayer.name.rawValue)",
            content: content,
            trigger: nil
        )
        UNUserNotificationCenter.current().add(request)
    }

    private func scheduleDailyRefresh() {
        let tomorrow = calendar.startOfDay(for: calendar.date(byAdding: .day, value: 1, to: Date())!)
        let delay = tomorrow.timeIntervalSinceNow + 60

        let timer = Timer.scheduledTimer(withTimeInterval: delay, repeats: false) { [weak self] _ in
            self?.fetchTimes()
        }
        notificationTimers.append(timer)
    }

    private func retryFetchLater() {
        Timer.scheduledTimer(withTimeInterval: 300, repeats: false) { [weak self] _ in
            self?.fetchTimes()
        }
    }
}
