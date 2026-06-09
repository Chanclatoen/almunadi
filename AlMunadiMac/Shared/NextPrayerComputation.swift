import Foundation

/// Pure next/last-prayer selection and timeline-transition computation,
/// extracted from `PrayerService.updateNextPrayer` so both menu-bar and
/// WidgetKit extension produce identical results.
enum NextPrayerComputation {

    static func nextPrayer(
        in prayers: [PrayerTime],
        at date: Date,
        calendar: Calendar = .current
    ) -> PrayerTime? {
        if let next = prayers.first(where: { $0.date > date }) { return next }
        guard let first = prayers.first,
              let tomorrow = calendar.date(byAdding: .day, value: 1, to: first.date)
        else { return nil }
        return PrayerTime(
            id: first.name,
            name: first.name,
            time: first.time,
            date: tomorrow,
            displayName: first.displayName,
            iqamaTime: first.iqamaTime,
            notificationKey: first.notificationKey
        )
    }

    static func lastPrayer(
        in prayers: [PrayerTime],
        at date: Date,
        calendar: Calendar = .current
    ) -> PrayerTime? {
        if let last = prayers.last(where: { $0.date <= date }) { return last }
        guard let last = prayers.last,
              let yesterday = calendar.date(byAdding: .day, value: -1, to: last.date)
        else { return nil }
        return PrayerTime(
            id: last.name,
            name: last.name,
            time: last.time,
            date: yesterday,
            displayName: last.displayName,
            iqamaTime: last.iqamaTime,
            notificationKey: last.notificationKey
        )
    }

    /// Timestamps at which the "next prayer" indicator changes today + a
    /// midnight rollover so the widget timeline reloads at the start of
    /// each new day.
    static func upcomingTransitions(
        in prayers: [PrayerTime],
        from date: Date,
        calendar: Calendar = .current
    ) -> [Date] {
        var transitions: Set<Date> = []
        for prayer in prayers where prayer.date > date {
            transitions.insert(prayer.date)
        }
        if let first = prayers.first,
           let tomorrowFirst = calendar.date(byAdding: .day, value: 1, to: first.date),
           tomorrowFirst > date {
            transitions.insert(tomorrowFirst)
        }
        if let tomorrow = calendar.date(byAdding: .day, value: 1, to: date) {
            transitions.insert(calendar.startOfDay(for: tomorrow))
        }
        return transitions.sorted()
    }
}
