import SwiftUI

struct PrayerTimesView: View {
    @ObservedObject var service: PrayerService

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
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
                    .foregroundStyle(.white)
                    .background(Color.blue)
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
                        .foregroundStyle(.orange.opacity(0.8))
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
                        .foregroundStyle(.secondary)
                        .frame(width: 20)
                    Text(t("jumuah2"))
                        .foregroundStyle(.secondary)
                    Spacer()
                    Text(jumua2)
                        .foregroundStyle(.secondary)
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
                        .foregroundStyle(.orange.opacity(0.75))
                        .frame(width: 20)
                    Text(t("shuruq"))
                        .foregroundStyle(.orange.opacity(0.75))
                        .fontWeight(.medium)
                    Spacer()
                    Text(shuruq)
                        .foregroundStyle(.orange.opacity(0.65))
                        .monospacedDigit()
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
            }

            Divider().padding(.vertical, 2)

            // Error banner
            if let error = service.lastError {
                HStack(spacing: 6) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .font(.system(size: 10))
                    Text(error)
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
                            .background(.orange.opacity(0.15))
                            .clipShape(Capsule())
                    }
                    .buttonStyle(.plain)
                }
                .foregroundStyle(.orange)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(.orange.opacity(0.06))
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
}

struct PrayerRow: View {
    let prayer: PrayerTime
    let isNext: Bool
    var countdownFormat: String = "compact"

    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: prayer.icon)
                .font(.system(size: 13))
                .foregroundStyle(isNext ? AnyShapeStyle(.blue) : isPast ? AnyShapeStyle(.secondary.opacity(0.5)) : AnyShapeStyle(.secondary))
                .frame(width: 20)

            VStack(alignment: .leading, spacing: 2) {
                Text(prayer.displayName)
                    .font(.system(size: 13, weight: isNext ? .semibold : .regular))
                    .foregroundStyle(isPast ? AnyShapeStyle(.secondary.opacity(0.6)) : AnyShapeStyle(.primary))

                if let iqama = prayer.iqamaTime {
                    HStack(spacing: 3) {
                        Text("Iq")
                            .font(.system(size: 8, weight: .bold))
                            .foregroundStyle(isNext ? .blue.opacity(0.6) : .secondary.opacity(0.6))
                            .padding(.horizontal, 4)
                            .padding(.vertical, 1)
                            .background(
                                isNext
                                    ? AnyShapeStyle(Color.blue.opacity(0.08))
                                    : AnyShapeStyle(Color.secondary.opacity(0.08))
                            )
                            .clipShape(RoundedRectangle(cornerRadius: 3))
                        Text(iqama)
                            .font(.system(size: 10))
                            .italic()
                            .foregroundStyle(isNext ? .blue.opacity(0.6) : .secondary.opacity(0.6))
                    }
                }
            }

            Spacer()

            if isNext {
                Text(countdown)
                    .font(.system(size: 12, weight: .medium, design: .monospaced))
                    .foregroundStyle(.blue.opacity(0.7))
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Color.blue.opacity(0.06))
                    .clipShape(Capsule())
            }

            Text(prayer.time)
                .font(.system(size: 13, design: .monospaced))
                .fontWeight(isNext ? .semibold : .regular)
                .foregroundStyle(isNext ? AnyShapeStyle(.blue) : isPast ? AnyShapeStyle(.secondary.opacity(0.5)) : AnyShapeStyle(.primary))
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
        .background(
            isNext
                ? Color.blue.opacity(0.1)
                : .clear
        )
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }

    private var isPast: Bool {
        prayer.date <= Date()
    }

    private var countdown: String {
        let remaining = Int(prayer.date.timeIntervalSinceNow / 60)
        guard remaining > 0 else { return "" }
        let h = remaining / 60
        let m = remaining % 60
        if h > 0 {
            if countdownFormat == "full" {
                return "-\(h)h \(String(format: "%02d", m))m"
            }
            return "-\(h)h\(String(format: "%02d", m))m"
        }
        return "-\(m)m"
    }
}
