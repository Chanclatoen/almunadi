import Foundation

#if canImport(WidgetKit)
import WidgetKit
#endif

/// Shared App Group store consumed by the WidgetKit extension.
///
/// The main app calls `saveSnapshot(...)` after every successful Mawaqit refresh;
/// the widget extension calls `loadSnapshot()` from its `TimelineProvider`.
/// macOS Developer ID (non-App-Store) builds require the App Group to be
/// Team-ID-prefixed (`<TeamID>.<group>`); this must match both targets'
/// entitlements and be registered on the developer portal.
enum WidgetSharedStore {
    static let appGroupID = "PM49C5H4XK.net.almunadi.AlMunadi"

    struct Snapshot {
        let data: MawaqitData
        let offsets: [String: Int]
        let language: String
        let countdownFormat: String
        let iqamaEnabled: Bool
    }

    private enum Key {
        static let snapshot = "widgetSnapshot"
        static let offsets = "widgetOffsets"
        static let language = "widgetLanguage"
        static let countdownFormat = "widgetCountdownFormat"
        static let iqamaEnabled = "widgetIqamaEnabled"
    }

    static var defaults: UserDefaults? {
        UserDefaults(suiteName: appGroupID)
    }

    static func saveSnapshot(
        _ data: MawaqitData,
        offsets: [String: Int],
        language: String,
        countdownFormat: String
    ) {
        guard let defaults else { return }
        if let encoded = try? JSONEncoder().encode(data) {
            defaults.set(encoded, forKey: Key.snapshot)
        }
        if let encoded = try? JSONEncoder().encode(offsets) {
            defaults.set(encoded, forKey: Key.offsets)
        }
        defaults.set(language, forKey: Key.language)
        defaults.set(countdownFormat, forKey: Key.countdownFormat)
        defaults.set(data.iqamaEnabled ?? false, forKey: Key.iqamaEnabled)

        #if canImport(WidgetKit)
        WidgetCenter.shared.reloadAllTimelines()
        #endif
    }

    /// Persist just the language so the widget's setup state is localized
    /// even before any mosque is configured (no snapshot exists yet).
    static func saveLanguage(_ language: String) {
        guard let defaults else { return }
        defaults.set(language, forKey: Key.language)

        #if canImport(WidgetKit)
        WidgetCenter.shared.reloadAllTimelines()
        #endif
    }

    static var storedLanguage: String {
        defaults?.string(forKey: Key.language) ?? "en"
    }

    static func loadSnapshot() -> Snapshot? {
        guard let defaults,
              let blob = defaults.data(forKey: Key.snapshot),
              let data = try? JSONDecoder().decode(MawaqitData.self, from: blob),
              !data.times.isEmpty
        else { return nil }

        let offsets: [String: Int] = {
            guard let blob = defaults.data(forKey: Key.offsets),
                  let decoded = try? JSONDecoder().decode([String: Int].self, from: blob)
            else { return PrayerSettingsDefaults.defaultOffsets() }
            return PrayerSettingsDefaults.mergeOffsets(decoded)
        }()

        return Snapshot(
            data: data,
            offsets: offsets,
            language: defaults.string(forKey: Key.language) ?? "en",
            countdownFormat: defaults.string(forKey: Key.countdownFormat) ?? "compact",
            iqamaEnabled: defaults.bool(forKey: Key.iqamaEnabled)
        )
    }
}
