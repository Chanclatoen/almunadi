import Foundation

enum PrayerName: String, CaseIterable {
    case fajr = "Fajr"
    case dhuhr = "Dhuhr"
    case asr = "Asr"
    case maghrib = "Maghrib"
    case isha = "Isha"

    var icon: String {
        switch self {
        case .fajr: return "sunrise"
        case .dhuhr: return "sun.max"
        case .asr: return "cloud.sun"
        case .maghrib: return "sunset"
        case .isha: return "moon.stars"
        }
    }
}

struct PrayerNotificationSetting: Codable {
    var enabled: Bool = true
    var reminderMinutes: Int = 0
    var adhanEnabled: Bool? = nil

    enum CodingKeys: String, CodingKey {
        case enabled
        case reminderMinutes = "reminder_minutes"
        case adhanEnabled = "adhan_enabled"
    }
}

struct PrayerTime: Identifiable {
    let id: PrayerName
    let name: PrayerName
    let time: String
    let date: Date
    var displayName: String
    var iqamaTime: String?
    var notificationKey: String

    var icon: String { name.icon }

    func menuBarText(displayMode: String, countdownFormat: String) -> String {
        let remaining = Int(date.timeIntervalSinceNow / 60)
        if remaining <= 0 {
            if displayMode == "icon" { return "" }
            if displayMode == "name" { return displayName }
            return "\(displayName) \(t("now"))"
        }

        let h = remaining / 60
        let m = remaining % 60
        let countdown: String
        if h > 0 {
            if countdownFormat == "full" {
                countdown = "-\(h)h \(String(format: "%02d", m))m"
            } else {
                countdown = "-\(h)h\(String(format: "%02d", m))m"
            }
        } else {
            countdown = "-\(m)m"
        }

        switch displayMode {
        case "time":
            return "\(displayName) \(time)"
        case "name":
            return displayName
        case "compact":
            return "\(displayName) \(countdown)"
        case "icon":
            return ""
        default:
            return "\(displayName) \(time) \(countdown)"
        }
    }
}

struct MawaqitData: Codable {
    let times: [String]
    let shuruq: String?
    let mosqueName: String
    var iqama: [String]?
    var iqamaEnabled: Bool?
    var jumua: String?
    var jumua2: String?
    var cacheDate: String?
}

struct MosqueSearchResult: Identifiable {
    let id: String
    let name: String
    let slug: String
    let localisation: String
}

struct SavedMosque: Codable, Identifiable {
    var id: String { url }
    let url: String
    let name: String
}

enum PrayerSettingsDefaults {
    static let notificationKeys = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha", "Jumuah"]
    static let offsetKeys = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]

    static func defaultNotificationSettings() -> [String: PrayerNotificationSetting] {
        var settings: [String: PrayerNotificationSetting] = [:]
        for key in notificationKeys {
            settings[key] = PrayerNotificationSetting()
        }
        return settings
    }

    static func defaultOffsets() -> [String: Int] {
        var offsets: [String: Int] = [:]
        for key in offsetKeys {
            offsets[key] = 0
        }
        return offsets
    }

    static func mergeNotificationSettings(_ stored: [String: PrayerNotificationSetting]?) -> [String: PrayerNotificationSetting] {
        var merged = defaultNotificationSettings()
        guard let stored else { return merged }
        for key in notificationKeys {
            if let entry = stored[key] {
                merged[key] = PrayerNotificationSetting(
                    enabled: entry.enabled,
                    reminderMinutes: max(0, entry.reminderMinutes),
                    adhanEnabled: entry.adhanEnabled
                )
            }
        }
        return merged
    }

    static func mergeOffsets(_ stored: [String: Int]?) -> [String: Int] {
        var merged = defaultOffsets()
        guard let stored else { return merged }
        for key in offsetKeys {
            if let val = stored[key] {
                merged[key] = max(-60, min(60, val))
            }
        }
        return merged
    }

    static func notificationKey(for index: Int, isFriday: Bool, hasJumua: Bool) -> String {
        if index == 1 && isFriday && hasJumua { return "Jumuah" }
        return PrayerName.allCases[index].rawValue
    }

    static func shouldPlayAdhan(_ setting: PrayerNotificationSetting, globalEnabled: Bool) -> Bool {
        if let perPrayer = setting.adhanEnabled {
            return perPrayer
        }
        return globalEnabled
    }
}
