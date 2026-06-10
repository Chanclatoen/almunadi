import Foundation

/// Cross-platform behavior primitives shared by the app, the widget, and the
/// fixture test suite. These mirror core/al_munadi_core.py and are asserted
/// against shared/fixtures/behavior-fixtures.json — change the fixtures first,
/// then keep every platform suite green.
enum BehaviorFormatting {
    /// Zero or negative remaining/elapsed minutes render as the localized "now".
    static func formatDuration(minutes: Int, prefix: String, format: String) -> String {
        guard minutes > 0 else { return t("now") }
        let h = minutes / 60
        let m = minutes % 60
        if h > 0 {
            if format == "full" {
                return "\(prefix)\(h)h \(String(format: "%02d", m))m"
            }
            return "\(prefix)\(h)h\(String(format: "%02d", m))m"
        }
        return "\(prefix)\(m)m"
    }

    static func formatCountdown(remainingMinutes: Int, format: String) -> String {
        formatDuration(minutes: remainingMinutes, prefix: "-", format: format)
    }

    static func formatElapsed(elapsedMinutes: Int, format: String) -> String {
        formatDuration(minutes: elapsedMinutes, prefix: "+", format: format)
    }

    /// Bar-label composition per product-behavior.md §3: double-space joins;
    /// "icon" returns the bare name so it can serve as the tooltip.
    static func formatTrayTitle(mode: String, name: String, time: String, countdown: String) -> String {
        switch mode {
        case "time":
            return "\(name)  \(time)"
        case "name", "icon":
            return name
        case "compact":
            return "\(name)  \(countdown)"
        default:
            return "\(name)  \(time)  \(countdown)"
        }
    }
}

enum VersionCompare {
    /// Numeric per-segment comparison tolerating suffixes ("1.0.9-beta" → 1.0.9).
    static func isNewer(current: String, latest: String) -> Bool {
        guard !latest.isEmpty else { return false }
        let currentParts = segments(current)
        let latestParts = segments(latest)
        for i in 0..<max(currentParts.count, latestParts.count) {
            let c = i < currentParts.count ? currentParts[i] : 0
            let l = i < latestParts.count ? latestParts[i] : 0
            if l > c { return true }
            if l < c { return false }
        }
        return false
    }

    private static func segments(_ version: String) -> [Int] {
        version.split(separator: ".").map { Int($0.prefix(while: { $0.isNumber })) ?? 0 }
    }
}

enum MawaqitURL {
    /// Resolves the mosque slug from a mawaqit.net URL, with or without the
    /// /w/ segment; nil for anything that is not a Mawaqit mosque page.
    static func extractSlug(from url: String) -> String? {
        let pattern = #"mawaqit\.net/\w+/(?:w/)?(.+?)/?$"#
        guard let regex = try? NSRegularExpression(pattern: pattern),
              let match = regex.firstMatch(in: url, range: NSRange(url.startIndex..., in: url)),
              let range = Range(match.range(at: 1), in: url)
        else { return nil }
        return String(url[range])
    }
}
