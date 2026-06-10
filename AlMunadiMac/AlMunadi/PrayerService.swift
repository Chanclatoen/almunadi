import Foundation
import Combine
import UserNotifications
import AVFoundation

class PrayerService: ObservableObject {
    static let appVersion = "1.0.8"
    static let tagPrefix = "v"
    private static let releasesURL = "https://api.github.com/repos/Chanclatoen/almunadi/releases"
    private static let repoReleasesPage = "https://github.com/Chanclatoen/almunadi/releases"

    @Published var prayers: [PrayerTime] = []
    @Published var shuruq: String?
    @Published var mosqueName: String = ""
    @Published var nextPrayer: PrayerTime?
    @Published var lastPrayer: PrayerTime?
    @Published var fetchFailed: Bool = false
    @Published var isCached: Bool = false
    @Published var jumua2: String?
    @Published var hijriDate: String?
    @Published var qiblaDirection: String?
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
    private static let kaabaLatitude = 21.422487
    private static let kaabaLongitude = 39.826206
    private static let hijriMonths = [
        "Muharram", "Safar", "Rabi al-awwal", "Rabi al-thani",
        "Jumada al-awwal", "Jumada al-thani", "Rajab", "Shaban",
        "Ramadan", "Shawwal", "Dhu al-Qadah", "Dhu al-Hijjah",
    ]
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

    var dndBypass: Bool {
        get { UserDefaults.standard.object(forKey: "dndBypass") as? Bool ?? true }
        set { UserDefaults.standard.set(newValue, forKey: "dndBypass") }
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
            objectWillChange.send()
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

    private func applyOffsetsToPrayers() {
        guard let data = cachedMawaqitData else { return }
        applyData(data, fromCache: isCached)
        // applyData skips saveCache when fromCache=true, so the widget store
        // would miss settings changes that don't trigger a fresh fetch.
        if isCached { pushWidgetSnapshot(data) }
    }

    // MARK: - Language

    func setLanguage(_ lang: String) {
        UserDefaults.standard.set(lang, forKey: "language")
        language = lang
        // Re-apply display names for current prayers
        updateDisplayNames()
        if let data = cachedMawaqitData { pushWidgetSnapshot(data) }
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
                if VersionCompare.isNewer(current: Self.appVersion, latest: latest) {
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
        // First run: nothing configured yet — the UI shows the welcome state.
        guard !urlString.isEmpty else { return }

        if let slug = MawaqitURL.extractSlug(from: urlString) {
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
                let latitude = mosque["latitude"] as? Double
                let longitude = mosque["longitude"] as? Double
                let hijriAdjustment = mosque["hijriAdjustment"] as? Int ?? 0

                let mawaqitData = MawaqitData(
                    times: times,
                    shuruq: shuruq,
                    mosqueName: name,
                    iqama: iqama,
                    iqamaEnabled: iqamaEnabled,
                    jumua: jumua,
                    jumua2: jumua2,
                    hijriDate: Self.formatHijriDate(adjustment: hijriAdjustment),
                    qiblaDirection: Self.formatQiblaDirection(latitude: latitude, longitude: longitude)
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
            if let slug = MawaqitURL.extractSlug(from: fetchUrl) {
                fetchUrl = "https://mawaqit.net/en/w/\(slug)"
            }
        }

        guard let url = URL(string: fetchUrl) else {
            handleFetchError("Invalid URL")
            return
        }

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
        let latitude = json["latitude"] as? Double
        let longitude = json["longitude"] as? Double
        let hijriAdjustment = json["hijriAdjustment"] as? Int ?? 0

        return MawaqitData(
            times: times,
            shuruq: shuruq,
            mosqueName: name,
            iqama: json["iqama"] as? [String],
            iqamaEnabled: json["iqamaEnabled"] as? Bool,
            jumua: json["jumua"] as? String,
            jumua2: json["jumua2"] as? String,
            hijriDate: Self.formatHijriDate(adjustment: hijriAdjustment),
            qiblaDirection: Self.formatQiblaDirection(latitude: latitude, longitude: longitude)
        )
    }

    private static func formatQiblaDirection(latitude: Double?, longitude: Double?) -> String? {
        guard let latitude, let longitude else { return nil }
        let lat1 = latitude * .pi / 180
        let lat2 = kaabaLatitude * .pi / 180
        let deltaLon = (kaabaLongitude - longitude) * .pi / 180
        let y = sin(deltaLon)
        let x = cos(lat1) * tan(lat2) - sin(lat1) * cos(deltaLon)
        let bearing = Int(round((atan2(y, x) * 180 / .pi + 360).truncatingRemainder(dividingBy: 360)))
        return "\(bearing)°"
    }

    private static func gregorianToJdn(year: Int, month: Int, day: Int) -> Int {
        let a = (14 - month) / 12
        let y = year + 4800 - a
        let m = month + 12 * a - 3
        return day + (153 * m + 2) / 5 + 365 * y + y / 4 - y / 100 + y / 400 - 32045
    }

    private static func islamicToJdn(year: Int, month: Int, day: Int) -> Int {
        day + Int(ceil(29.5 * Double(month - 1))) + (year - 1) * 354
            + Int(floor(Double(3 + 11 * year) / 30.0)) + 1948439 - 1
    }

    private static func formatHijriDate(adjustment: Int = 0) -> String {
        let components = Calendar.current.dateComponents([.year, .month, .day], from: Date())
        let jdn = gregorianToJdn(
            year: components.year ?? 2026,
            month: components.month ?? 1,
            day: components.day ?? 1
        ) + adjustment
        let year = Int(floor(Double(30 * (jdn - 1948439) + 10646) / 10631.0))
        let month = min(12, Int(ceil(Double(jdn - (29 + islamicToJdn(year: year, month: 1, day: 1))) / 29.5)) + 1)
        let day = jdn - islamicToJdn(year: year, month: month, day: 1) + 1
        return "\(day) \(hijriMonths[month - 1]) \(year) AH"
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
        pushWidgetSnapshot(cacheData)
    }

    /// Push the current snapshot + settings to the App Group so the WidgetKit
    /// extension can read them. Called from `saveCache` after a fresh fetch and
    /// also when settings (offsets / language) change so the widget reflects
    /// them without waiting for the next fetch.
    private func pushWidgetSnapshot(_ data: MawaqitData) {
        WidgetSharedStore.saveSnapshot(
            data,
            offsets: prayerOffsets,
            language: language,
            countdownFormat: countdownFormat
        )
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
        let today = Date()
        let showJumuah = isFriday() && data.jumua != nil

        prayers = PrayerListBuilder.buildPrayerList(
            from: data,
            offsets: prayerOffsets,
            language: language,
            now: today,
            calendar: calendar
        )
        shuruq = data.shuruq
        mosqueName = data.mosqueName
        jumua2 = (showJumuah ? data.jumua2 : nil)
        hijriDate = data.hijriDate
        qiblaDirection = data.qiblaDirection

        if !fromCache {
            isCached = false
            fetchFailed = false
            saveCache(data)
        }
        updateNextPrayer()
        scheduleNotifications()
    }

    /// Errors are calm and localized: the UI only learns that the fetch
    /// failed (it shows t("fetch_error")); the detail goes to the console.
    private func handleFetchError(_ message: String) {
        print("Al Munadi fetch error: \(message)")
        fetchFailed = true
        if prayers.isEmpty { loadCache() }
        retryFetchLater()
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
        lastPrayer = NextPrayerComputation.lastPrayer(in: prayers, at: now, calendar: calendar)
        nextPrayer = NextPrayerComputation.nextPrayer(in: prayers, at: now, calendar: calendar)
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

        let setting = prayerNotificationSettings[prayer.notificationKey] ?? PrayerNotificationSetting()
        if PrayerSettingsDefaults.shouldBypassDnd(setting, globalEnabled: dndBypass) {
            content.interruptionLevel = .timeSensitive
        }

        let request = UNNotificationRequest(
            identifier: "prayer-reminder-\(prayer.name.rawValue)",
            content: content,
            trigger: nil
        )
        UNUserNotificationCenter.current().add(request)
    }

    private func requestNotificationPermission() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .timeSensitive]) { _, _ in }
    }

    private func sendNotification(prayer: PrayerTime) {
        let content = UNMutableNotificationContent()
        content.title = String(format: t("prayer_time_title"), prayer.displayName, prayer.time)
        content.body = String(format: t("prayer_time_body"), prayer.displayName)
        content.sound = .default

        let setting = prayerNotificationSettings[prayer.notificationKey] ?? PrayerNotificationSetting()
        if PrayerSettingsDefaults.shouldBypassDnd(setting, globalEnabled: dndBypass) {
            content.interruptionLevel = .timeSensitive
        }

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
