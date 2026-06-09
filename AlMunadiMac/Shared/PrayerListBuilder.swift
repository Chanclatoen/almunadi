import Foundation

/// Pure logic that turns a `MawaqitData` snapshot + user offsets + language
/// into the final `[PrayerTime]` displayed by both the main app and the widget.
/// Extracted from `PrayerService.applyData` so the WidgetKit extension can
/// reconstruct the exact same list from the App Group snapshot without
/// instantiating `PrayerService`. Behaviour must stay identical to the
/// original implementation — both call sites depend on it.
enum PrayerListBuilder {

    static func buildPrayerList(
        from data: MawaqitData,
        offsets: [String: Int],
        language: String,
        now: Date = Date(),
        calendar: Calendar = .current
    ) -> [PrayerTime] {
        let names = PrayerName.allCases
        let isFriday = calendar.component(.weekday, from: now) == 6
        let showJumuah = isFriday && data.jumua != nil

        let adjustedTimes: [String] = names.enumerated().compactMap { i, name in
            guard i < data.times.count else { return nil }
            var timeStr = data.times[i]
            if i == 1, showJumuah, let jumuaTime = data.jumua {
                timeStr = jumuaTime
            }
            return applyOffset(to: timeStr, minutes: offsets[name.rawValue] ?? 0)
        }

        let adjustedDates = datesForAdjustedTimes(adjustedTimes, relativeTo: now, calendar: calendar)

        var prayers: [PrayerTime] = []
        for (i, name) in names.enumerated() where i < data.times.count {
            var timeStr = data.times[i]
            var displayName = Translations.shared.translatedPrayerName(name, language: language)
            let notifKey = PrayerSettingsDefaults.notificationKey(for: i, isFriday: showJumuah, hasJumua: data.jumua != nil)

            if i == 1, showJumuah, let jumuaTime = data.jumua {
                timeStr = jumuaTime
                displayName = Translations.shared.t("jumuah", language: language)
            }

            let adjustedTime = i < adjustedTimes.count
                ? adjustedTimes[i]
                : applyOffset(to: timeStr, minutes: offsets[name.rawValue] ?? 0)

            if i < adjustedDates.count, let date = adjustedDates[i] {
                var iqamaTime: String? = nil
                if data.iqamaEnabled == true, let iqama = data.iqama, i < iqama.count {
                    iqamaTime = resolveIqama(
                        prayerTime: data.times[i],
                        iqamaValue: iqama[i],
                        baseDate: now,
                        calendar: calendar
                    )
                }
                prayers.append(PrayerTime(
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
        return prayers
    }

    // MARK: - Pure helpers (reused by PrayerService too)

    static func applyOffset(to timeStr: String, minutes: Int) -> String {
        guard minutes != 0 else { return timeStr }
        let parts = timeStr.split(separator: ":").compactMap { Int($0) }
        guard parts.count == 2 else { return timeStr }
        var total = parts[0] * 60 + parts[1] + minutes
        total = ((total % 1440) + 1440) % 1440
        return String(format: "%02d:%02d", total / 60, total % 60)
    }

    static func minutes(from timeStr: String) -> Int? {
        let parts = timeStr.split(separator: ":").compactMap { Int($0) }
        guard parts.count == 2 else { return nil }
        return parts[0] * 60 + parts[1]
    }

    static func dateFromTimeString(_ timeStr: String, relativeTo date: Date, calendar: Calendar) -> Date? {
        let parts = timeStr.split(separator: ":").compactMap { Int($0) }
        guard parts.count == 2 else { return nil }
        return calendar.date(bySettingHour: parts[0], minute: parts[1], second: 0, of: date)
    }

    static func datesForAdjustedTimes(_ times: [String], relativeTo date: Date, calendar: Calendar) -> [Date?] {
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
            guard let baseDate = dateFromTimeString(times[index], relativeTo: date, calendar: calendar) else { continue }
            dates[index] = calendar.date(byAdding: .day, value: dayOffset, to: baseDate)
        }
        return dates
    }

    static func resolveIqama(
        prayerTime: String,
        iqamaValue: String?,
        baseDate: Date,
        calendar: Calendar
    ) -> String? {
        guard let raw = iqamaValue?.trimmingCharacters(in: .whitespaces),
              !raw.isEmpty, raw != "0", raw != "+0"
        else { return nil }
        if raw.contains(":") { return raw }
        let cleanVal = raw.hasPrefix("+") ? String(raw.dropFirst()) : raw
        guard let offset = Int(cleanVal), offset > 0,
              let prayerDate = dateFromTimeString(prayerTime, relativeTo: baseDate, calendar: calendar)
        else { return nil }
        let iqamaDate = prayerDate.addingTimeInterval(Double(offset * 60))
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        return formatter.string(from: iqamaDate)
    }
}
