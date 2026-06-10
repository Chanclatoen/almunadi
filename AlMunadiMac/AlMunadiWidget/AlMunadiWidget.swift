import SwiftUI
import WidgetKit

struct AlMunadiEntry: TimelineEntry {
    let date: Date
    let prayers: [PrayerTime]
    let nextPrayer: PrayerTime?
    let lastPrayer: PrayerTime?
    let mosqueName: String
    let shuruq: String?
    let hijriDate: String?
    let qiblaDirection: String?
    let language: String
    let countdownFormat: String
    let isPlaceholder: Bool
    var needsSetup: Bool = false
    var isStale: Bool = false
}

struct AlMunadiProvider: TimelineProvider {
    func placeholder(in context: Context) -> AlMunadiEntry {
        AlMunadiEntry.placeholder
    }

    func getSnapshot(in context: Context, completion: @escaping (AlMunadiEntry) -> Void) {
        completion(makeEntry(for: Date()) ?? (context.isPreview ? .placeholder : .setup(at: Date())))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<AlMunadiEntry>) -> Void) {
        let now = Date()
        guard let snapshot = WidgetSharedStore.loadSnapshot() else {
            // No mosque configured yet: show the localized setup state for
            // real widgets (sample data only in the gallery preview).
            let entry: AlMunadiEntry = context.isPreview ? .placeholder : .setup(at: now)
            completion(Timeline(entries: [entry], policy: .after(now.addingTimeInterval(15 * 60))))
            return
        }

        Translations.activeLanguage = snapshot.language
        let prayers = PrayerListBuilder.buildPrayerList(
            from: snapshot.data,
            offsets: snapshot.offsets,
            language: snapshot.language,
            now: now
        )
        let transitions = NextPrayerComputation.upcomingTransitions(in: prayers, from: now)

        var entries: [AlMunadiEntry] = [makeEntry(at: now, snapshot: snapshot, prayers: prayers)]
        for date in transitions {
            entries.append(makeEntry(at: date, snapshot: snapshot, prayers: prayers))
        }

        completion(Timeline(entries: entries, policy: .atEnd))
    }

    private func makeEntry(for date: Date) -> AlMunadiEntry? {
        guard let snapshot = WidgetSharedStore.loadSnapshot() else { return nil }
        Translations.activeLanguage = snapshot.language
        let prayers = PrayerListBuilder.buildPrayerList(
            from: snapshot.data,
            offsets: snapshot.offsets,
            language: snapshot.language,
            now: date
        )
        return makeEntry(at: date, snapshot: snapshot, prayers: prayers)
    }

    private func makeEntry(
        at date: Date,
        snapshot: WidgetSharedStore.Snapshot,
        prayers: [PrayerTime]
    ) -> AlMunadiEntry {
        AlMunadiEntry(
            date: date,
            prayers: prayers,
            nextPrayer: NextPrayerComputation.nextPrayer(in: prayers, at: date),
            lastPrayer: NextPrayerComputation.lastPrayer(in: prayers, at: date),
            mosqueName: snapshot.data.mosqueName,
            shuruq: snapshot.data.shuruq,
            hijriDate: snapshot.data.hijriDate,
            qiblaDirection: snapshot.data.qiblaDirection,
            language: snapshot.language,
            countdownFormat: snapshot.countdownFormat,
            isPlaceholder: false,
            isStale: Self.isStale(snapshot.data.cacheDate, at: date)
        )
    }

    /// Cached times from a previous day are shown with the cached hint.
    private static func isStale(_ cacheDate: String?, at date: Date) -> Bool {
        guard let cacheDate else { return false }
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        return cacheDate != formatter.string(from: date)
    }
}

extension AlMunadiEntry {
    static var placeholder: AlMunadiEntry {
        let now = Date()
        let calendar = Calendar.current
        let next = calendar.date(byAdding: .hour, value: 1, to: now) ?? now
        return AlMunadiEntry(
            date: now,
            prayers: [],
            nextPrayer: PrayerTime(
                id: .dhuhr,
                name: .dhuhr,
                time: "13:15",
                date: next,
                displayName: "Dhuhr",
                iqamaTime: nil,
                notificationKey: "Dhuhr"
            ),
            lastPrayer: nil,
            mosqueName: "Al Munadi",
            shuruq: "06:30",
            hijriDate: nil,
            qiblaDirection: nil,
            language: "en",
            countdownFormat: "compact",
            isPlaceholder: true
        )
    }

    /// Shown when no mosque has been configured in the app yet.
    static func setup(at date: Date) -> AlMunadiEntry {
        AlMunadiEntry(
            date: date,
            prayers: [],
            nextPrayer: nil,
            lastPrayer: nil,
            mosqueName: "",
            shuruq: nil,
            hijriDate: nil,
            qiblaDirection: nil,
            language: WidgetSharedStore.storedLanguage,
            countdownFormat: "compact",
            isPlaceholder: false,
            needsSetup: true
        )
    }
}

struct AlMunadiWidget: Widget {
    let kind: String = "AlMunadiWidget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: AlMunadiProvider()) { entry in
            AlMunadiWidgetEntryView(entry: entry)
                .tint(Brand.accent)
                .containerBackground(.fill.tertiary, for: .widget)
        }
        .configurationDisplayName("Al Munadi")
        .description("Next prayer time, countdown and daily schedule.")
        .supportedFamilies([.systemSmall, .systemMedium, .systemLarge])
    }
}

struct AlMunadiWidgetEntryView: View {
    @Environment(\.widgetFamily) private var family
    let entry: AlMunadiEntry

    init(entry: AlMunadiEntry) {
        self.entry = entry
        Translations.activeLanguage = entry.language
    }

    var body: some View {
        if entry.needsSetup {
            WidgetSetupView(showsBody: family != .systemSmall)
        } else {
            switch family {
            case .systemSmall: SmallWidgetView(entry: entry)
            case .systemMedium: MediumWidgetView(entry: entry)
            case .systemLarge: LargeWidgetView(entry: entry)
            default: SmallWidgetView(entry: entry)
            }
        }
    }
}

/// Localized no-mosque state — never a blank widget.
struct WidgetSetupView: View {
    let showsBody: Bool

    var body: some View {
        VStack(spacing: 6) {
            Image(systemName: "moon.stars.fill")
                .font(.system(size: 22))
                .foregroundStyle(Brand.accent)

            Text(t("set_mosque"))
                .font(.caption.weight(.semibold))
                .multilineTextAlignment(.center)

            if showsBody {
                Text(t("first_run_body"))
                    .font(.system(size: 10))
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 8)
            }

            Text("Al Munadi")
                .font(.system(size: 10))
                .foregroundStyle(.tertiary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
