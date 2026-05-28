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

    var icon: String { name.icon }

    var menuBarText: String {
        let remaining = Int(date.timeIntervalSinceNow / 60)
        if remaining <= 0 {
            return "\(name.rawValue) now"
        }
        let h = remaining / 60
        let m = remaining % 60
        if h > 0 {
            return "\(name.rawValue) \(time) -\(h)h\(String(format: "%02d", m))m"
        }
        return "\(name.rawValue) \(time) -\(m)m"
    }
}

struct MawaqitData {
    let times: [String]
    let shuruq: String?
    let mosqueName: String
}
