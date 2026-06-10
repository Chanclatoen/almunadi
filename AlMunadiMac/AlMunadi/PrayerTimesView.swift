import SwiftUI

struct PrayerTimesView: View {
    @ObservedObject var service: PrayerService

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            if service.mosqueUrl.isEmpty {
                FirstRunView()
            } else {
                configuredContent
            }

            Divider()

            Button {
                NSApplication.shared.terminate(nil)
            } label: {
                HStack {
                    Spacer()
                    Text(t("quit"))
                        .font(.system(size: 11))
                        .foregroundStyle(.secondary)
                    Spacer()
                }
            }
            .buttonStyle(.plain)
            .padding(.vertical, 6)
        }
        .frame(width: 300)
    }

    @ViewBuilder
    private var configuredContent: some View {
        // Update available banner
        if let update = service.updateInfo {
            Button {
                if let url = URL(string: update.url) {
                    NSWorkspace.shared.open(url)
                }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.system(size: 11))
                    Text("\(t("update_available")) — v\(update.version)")
                        .font(.system(size: 11, weight: .semibold))
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 6)
                .foregroundStyle(Brand.onAccent)
                .background(Brand.accent)
            }
            .buttonStyle(.plain)
        }

        // Mosque name header
        if !service.mosqueName.isEmpty {
            VStack(alignment: .leading, spacing: 6) {
                Text(service.mosqueName)
                    .font(.system(size: 14, weight: .semibold))
                    .padding(.horizontal, 16)
                    .padding(.top, 12)

                // Cached indicator (inline with header)
                if service.isCached {
                    HStack(spacing: 4) {
                        Image(systemName: "clock.arrow.circlepath")
                            .font(.system(size: 9))
                        Text(t("cached_data"))
                            .font(.system(size: 10))
                    }
                    .foregroundStyle(Brand.saffron)
                    .padding(.horizontal, 16)
                }

                if service.hijriDate != nil || service.qiblaDirection != nil {
                    HStack(spacing: 8) {
                        if let hijri = service.hijriDate {
                            Label(hijri, systemImage: "calendar")
                        }
                        if let qibla = service.qiblaDirection {
                            Label("\(t("qibla")) \(qibla)", systemImage: "location.north.line")
                        }
                    }
                    .font(.system(size: 10))
                    .foregroundStyle(.secondary)
                    .padding(.horizontal, 16)
                }

                Divider()
                    .padding(.top, 6)
            }
        }

        // Next prayer card
        if let next = service.nextPrayer {
            NextPrayerCard(prayer: next, countdownFormat: service.countdownFormat)
        }

        // Mosque switcher
        if !service.savedMosques.isEmpty {
            Menu {
                ForEach(service.savedMosques) { mosque in
                    Button(mosque.name.isEmpty ? mosque.url : mosque.name) {
                        service.switchToMosque(mosque)
                    }
                }
            } label: {
                HStack(spacing: 4) {
                    Image(systemName: "building.2")
                        .font(.system(size: 10))
                    Text(t("switch_to"))
                        .font(.system(size: 11, weight: .medium))
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 3)
                .background(.quaternary.opacity(0.5))
                .clipShape(Capsule())
            }
            .menuStyle(.borderlessButton)
            .padding(.horizontal, 16)
            .padding(.vertical, 6)

            Divider()
        }

        // Prayer rows
        ForEach(service.prayers) { prayer in
            PrayerRow(
                prayer: prayer,
                isNext: service.nextPrayer?.name == prayer.name && prayer.date > Date(),
                countdownFormat: service.countdownFormat
            )
        }

        // Jumua 2
        if let jumua2 = service.jumua2 {
            HStack {
                Image(systemName: "sun.max")
                    .foregroundStyle(Brand.saffron.opacity(0.75))
                    .frame(width: 20)
                Text(t("jumuah2"))
                    .foregroundStyle(Brand.saffron.opacity(0.75))
                Spacer()
                Text(jumua2)
                    .foregroundStyle(Brand.saffron.opacity(0.65))
                    .monospacedDigit()
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
        }

        // Shuruq row
        if let shuruq = service.shuruq {
            Divider().padding(.vertical, 2)
            HStack {
                Image(systemName: "sunrise")
                    .foregroundStyle(Brand.saffron.opacity(0.75))
                    .frame(width: 20)
                Text(t("shuruq"))
                    .foregroundStyle(Brand.saffron.opacity(0.75))
                    .fontWeight(.medium)
                Spacer()
                Text(shuruq)
                    .foregroundStyle(Brand.saffron.opacity(0.65))
                    .monospacedDigit()
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
        }

        Divider().padding(.vertical, 2)

        // Calm error banner — localized, never raw error text
        if service.fetchFailed {
            HStack(spacing: 6) {
                Image(systemName: "exclamationmark.triangle.fill")
                    .font(.system(size: 10))
                Text(t("fetch_error"))
                    .font(.system(size: 11))
                    .lineLimit(2)
                Spacer()
                Button {
                    service.fetchTimes()
                } label: {
                    Text(t("retry"))
                        .font(.system(size: 10, weight: .medium))
                        .padding(.horizontal, 8)
                        .padding(.vertical, 2)
                        .background(Brand.saffron.opacity(0.15))
                        .clipShape(Capsule())
                }
                .buttonStyle(.plain)
            }
            .foregroundStyle(Brand.errorText)
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(Brand.saffron.opacity(0.06))
        }

        // Bottom action bar
        HStack(spacing: 12) {
            Button {
                service.fetchTimes()
            } label: {
                HStack(spacing: 4) {
                    Image(systemName: "arrow.clockwise")
                        .font(.system(size: 10))
                    Text(t("refresh"))
                        .font(.system(size: 11, weight: .medium))
                }
                .padding(.horizontal, 10)
                .padding(.vertical, 4)
                .background(.quaternary.opacity(0.4))
                .clipShape(Capsule())
            }
            .buttonStyle(.plain)

            Spacer()

            SettingsLink {
                HStack(spacing: 4) {
                    Image(systemName: "gear")
                        .font(.system(size: 10))
                    Text(t("settings"))
                        .font(.system(size: 11, weight: .medium))
                }
                .padding(.horizontal, 10)
                .padding(.vertical, 4)
                .background(.quaternary.opacity(0.4))
                .clipShape(Capsule())
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
    }
}

/// Welcome state shown before any mosque is configured (spec §7).
struct FirstRunView: View {
    var body: some View {
        VStack(spacing: 10) {
            Image(systemName: "moon.stars.fill")
                .font(.system(size: 28))
                .foregroundStyle(Brand.accent)
                .padding(.top, 8)

            Text(t("first_run_title"))
                .font(.system(size: 15, weight: .semibold))

            Text(t("first_run_body"))
                .font(.system(size: 11))
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .fixedSize(horizontal: false, vertical: true)

            SettingsLink {
                Text(t("find_mosque"))
                    .font(.system(size: 12, weight: .semibold))
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .tint(Brand.accent)
            .padding(.top, 4)
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 16)
    }
}

/// Emphasized next-prayer card at the top of the dropdown, with a live
/// countdown that ticks on minute boundaries.
struct NextPrayerCard: View {
    let prayer: PrayerTime
    let countdownFormat: String

    var body: some View {
        TimelineView(.everyMinute) { context in
            HStack(spacing: 10) {
                RoundedRectangle(cornerRadius: 1.5)
                    .fill(Brand.accent)
                    .frame(width: 3)

                VStack(alignment: .leading, spacing: 4) {
                    Text(t("next_prayer").uppercased())
                        .font(.system(size: 9, weight: .bold))
                        .kerning(0.8)
                        .foregroundStyle(Brand.accent)

                    HStack(alignment: .firstTextBaseline) {
                        Text(prayer.displayName)
                            .font(.system(size: 20, weight: .bold))
                        Spacer()
                        Text(prayer.time)
                            .font(.system(size: 20, weight: .bold))
                            .monospacedDigit()
                    }

                    HStack {
                        Text(countdownText(at: context.date))
                            .font(.system(size: 11, weight: .medium))
                            .monospacedDigit()
                            .foregroundStyle(Brand.accent)
                        Spacer()
                        if let iqama = prayer.iqamaTime {
                            Text("\(t("iqama")) \(iqama)")
                                .font(.system(size: 10))
                                .monospacedDigit()
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            }
            .padding(10)
            .background(Brand.accent.opacity(0.10))
            .clipShape(RoundedRectangle(cornerRadius: 8))
            .padding(.horizontal, 10)
            .padding(.vertical, 8)
        }
    }

    private func countdownText(at date: Date) -> String {
        let remaining = Int(prayer.date.timeIntervalSince(date) / 60)
        return BehaviorFormatting.formatCountdown(remainingMinutes: remaining, format: countdownFormat)
    }
}

struct PrayerRow: View {
    let prayer: PrayerTime
    let isNext: Bool
    var countdownFormat: String = "compact"

    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: prayer.icon)
                .font(.system(size: 13))
                .foregroundStyle(iconStyle)
                .frame(width: 20)

            VStack(alignment: .leading, spacing: 2) {
                Text(prayer.displayName)
                    .font(.system(size: 13, weight: isNext ? .semibold : .regular))
                    .foregroundStyle(nameStyle)

                if let iqama = prayer.iqamaTime {
                    HStack(spacing: 3) {
                        Text("Iq")
                            .font(.system(size: 8, weight: .bold))
                            .foregroundStyle(isNext ? Brand.accent.opacity(0.8) : .secondary.opacity(0.6))
                            .padding(.horizontal, 4)
                            .padding(.vertical, 1)
                            .background(
                                isNext
                                    ? AnyShapeStyle(Brand.accent.opacity(0.08))
                                    : AnyShapeStyle(Color.secondary.opacity(0.08))
                            )
                            .clipShape(RoundedRectangle(cornerRadius: 3))
                        Text(iqama)
                            .font(.system(size: 10))
                            .italic()
                            .foregroundStyle(isNext ? Brand.accent.opacity(0.8) : .secondary.opacity(0.6))
                    }
                }
            }

            Spacer()

            if isNext {
                Text(countdown)
                    .font(.system(size: 12, weight: .medium))
                    .monospacedDigit()
                    .foregroundStyle(Brand.accent)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Brand.accent.opacity(0.08))
                    .clipShape(Capsule())
            }

            Text(prayer.time)
                .font(.system(size: 13))
                .monospacedDigit()
                .fontWeight(isNext ? .semibold : .regular)
                .foregroundStyle(timeStyle)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
        .background(isNext ? Brand.accent.opacity(0.10) : Color.clear)
        .clipShape(RoundedRectangle(cornerRadius: 8))
        .overlay(alignment: .leading) {
            if isNext {
                RoundedRectangle(cornerRadius: 1.5)
                    .fill(Brand.accent)
                    .frame(width: 3)
                    .padding(.vertical, 4)
            }
        }
    }

    private var isPast: Bool {
        prayer.date <= Date()
    }

    /// Jumuah (Dhuhr replaced on Fridays) carries the saffron accent.
    private var isJumuah: Bool {
        prayer.notificationKey == "Jumuah"
    }

    private var iconStyle: AnyShapeStyle {
        if isNext { return AnyShapeStyle(Brand.accent) }
        if isPast { return AnyShapeStyle(.secondary.opacity(0.5)) }
        if isJumuah { return AnyShapeStyle(Brand.saffron) }
        return AnyShapeStyle(Brand.prayerColor(prayer.name).opacity(0.85))
    }

    private var nameStyle: AnyShapeStyle {
        if isNext { return AnyShapeStyle(Brand.accent) }
        if isPast { return AnyShapeStyle(.secondary.opacity(0.6)) }
        if isJumuah { return AnyShapeStyle(Brand.saffron) }
        return AnyShapeStyle(.primary)
    }

    private var timeStyle: AnyShapeStyle {
        if isNext { return AnyShapeStyle(Brand.accent) }
        if isPast { return AnyShapeStyle(.secondary.opacity(0.5)) }
        if isJumuah { return AnyShapeStyle(Brand.saffron.opacity(0.85)) }
        return AnyShapeStyle(.primary)
    }

    private var countdown: String {
        let remaining = Int(prayer.date.timeIntervalSinceNow / 60)
        guard remaining > 0 else { return "" }
        return BehaviorFormatting.formatCountdown(remainingMinutes: remaining, format: countdownFormat)
    }
}
