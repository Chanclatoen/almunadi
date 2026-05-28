import Foundation
import Combine
import UserNotifications

class PrayerService: ObservableObject {
    @Published var prayers: [PrayerTime] = []
    @Published var shuruq: String?
    @Published var mosqueName: String = ""
    @Published var nextPrayer: PrayerTime?
    @Published var lastError: String?

    private var updateTimer: AnyCancellable?
    private var notificationTimers: [Timer] = []
    private let calendar = Calendar.current

    init() {
        requestNotificationPermission()
        startUpdateTimer()
        fetchIfConfigured()
    }

    var mosqueUrl: String {
        get { UserDefaults.standard.string(forKey: "mosqueUrl") ?? "" }
        set {
            UserDefaults.standard.set(newValue, forKey: "mosqueUrl")
            fetchTimes()
        }
    }

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

        var fetchUrl = urlString
        if !fetchUrl.contains("/w/") {
            if let slug = extractSlug(from: fetchUrl) {
                fetchUrl = "https://mawaqit.net/en/w/\(slug)"
            }
        }

        guard let url = URL(string: fetchUrl) else {
            lastError = "Invalid URL"
            return
        }

        lastError = nil

        URLSession.shared.dataTask(with: url) { [weak self] data, response, error in
            DispatchQueue.main.async {
                guard let self else { return }

                if let error {
                    self.lastError = error.localizedDescription
                    self.retryFetchLater()
                    return
                }

                guard let data, let html = String(data: data, encoding: .utf8) else {
                    self.lastError = "Could not read response"
                    self.retryFetchLater()
                    return
                }

                if let mawaqitData = self.parseConfData(html) {
                    self.applyData(mawaqitData)
                    self.scheduleDailyRefresh()
                } else {
                    self.lastError = "Could not parse prayer times"
                    self.retryFetchLater()
                }
            }
        }.resume()
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

    private func applyData(_ data: MawaqitData) {
        let names = PrayerName.allCases
        let today = Date()

        var prayerTimes: [PrayerTime] = []
        for (i, name) in names.enumerated() where i < data.times.count {
            if let date = dateFromTimeString(data.times[i], relativeTo: today) {
                prayerTimes.append(PrayerTime(id: name, name: name, time: data.times[i], date: date))
            }
        }

        prayers = prayerTimes
        shuruq = data.shuruq
        mosqueName = data.mosqueName
        updateNextPrayer()
        scheduleNotifications()
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
                nextPrayer = PrayerTime(id: first.name, name: first.name, time: first.time, date: tomorrow)
            }
        }
        objectWillChange.send()
    }

    private func scheduleNotifications() {
        notificationTimers.forEach { $0.invalidate() }
        notificationTimers.removeAll()

        let now = Date()
        for prayer in prayers {
            let delay = prayer.date.timeIntervalSince(now)
            guard delay > 0 else { continue }

            let timer = Timer.scheduledTimer(withTimeInterval: delay, repeats: false) { [weak self] _ in
                self?.sendNotification(prayer: prayer)
                self?.updateNextPrayer()
            }
            notificationTimers.append(timer)
        }
    }

    private func requestNotificationPermission() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound]) { _, _ in }
    }

    private func sendNotification(prayer: PrayerTime) {
        let content = UNMutableNotificationContent()
        content.title = "\(prayer.name.rawValue) - \(prayer.time)"
        content.body = "It's time for \(prayer.name.rawValue) prayer"
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
