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

struct PrayerTime: Identifiable {
    let id: PrayerName
    let name: PrayerName
    let time: String
    let date: Date
    var displayName: String
    var iqamaTime: String?

    var icon: String { name.icon }

    var menuBarText: String {
        let remaining = Int(date.timeIntervalSinceNow / 60)
        let format = UserDefaults.standard.string(forKey: "countdownFormat") ?? "compact"
        if remaining <= 0 {
            return "\(displayName) \(t("now"))"
        }
        let h = remaining / 60
        let m = remaining % 60
        if h > 0 {
            if format == "full" {
                return "\(displayName) \(time) -\(h)h \(String(format: "%02d", m))m"
            }
            return "\(displayName) \(time) -\(h)h\(String(format: "%02d", m))m"
        }
        return "\(displayName) \(time) -\(m)m"
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
