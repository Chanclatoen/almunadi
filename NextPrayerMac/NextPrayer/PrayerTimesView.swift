import SwiftUI

struct PrayerTimesView: View {
    @ObservedObject var service: PrayerService

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            if !service.mosqueName.isEmpty {
                Text(service.mosqueName)
                    .font(.headline)
                    .padding(.horizontal, 16)
                    .padding(.top, 12)
                    .padding(.bottom, 8)
            }

            Divider()

            ForEach(service.prayers) { prayer in
                PrayerRow(
                    prayer: prayer,
                    isNext: service.nextPrayer?.name == prayer.name && prayer.date > Date()
                )
            }

            if let shuruq = service.shuruq {
                Divider().padding(.vertical, 2)
                HStack {
                    Image(systemName: "sunrise")
                        .foregroundStyle(.secondary)
                        .frame(width: 20)
                    Text("Shuruq")
                        .foregroundStyle(.secondary)
                    Spacer()
                    Text(shuruq)
                        .foregroundStyle(.secondary)
                        .monospacedDigit()
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 6)
            }

            Divider().padding(.vertical, 2)

            if let error = service.lastError {
                Label(error, systemImage: "exclamationmark.triangle")
                    .font(.caption)
                    .foregroundStyle(.red)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 4)
            }

            HStack {
                Button {
                    service.fetchTimes()
                } label: {
                    Label("Refresh", systemImage: "arrow.clockwise")
                }

                Spacer()

                SettingsLink {
                    Label("Settings", systemImage: "gear")
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 8)

            Divider()

            Button("Quit") {
                NSApplication.shared.terminate(nil)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
        }
        .frame(width: 260)
    }
}

struct PrayerRow: View {
    let prayer: PrayerTime
    let isNext: Bool

    var body: some View {
        HStack {
            Image(systemName: prayer.icon)
                .foregroundStyle(isNext ? AnyShapeStyle(.blue) : isPast ? AnyShapeStyle(.tertiary) : AnyShapeStyle(.secondary))
                .frame(width: 20)

            Text(prayer.name.rawValue)
                .fontWeight(isNext ? .semibold : .regular)
                .foregroundStyle(isPast ? .tertiary : .primary)

            Spacer()

            if isNext {
                Text(countdown)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .monospacedDigit()
            }

            Text(prayer.time)
                .monospacedDigit()
                .fontWeight(isNext ? .semibold : .regular)
                .foregroundStyle(isNext ? AnyShapeStyle(.blue) : isPast ? AnyShapeStyle(.tertiary) : AnyShapeStyle(.primary))
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 6)
        .background(isNext ? Color.blue.opacity(0.08) : .clear)
        .cornerRadius(6)
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
            return "-\(h)h \(String(format: "%02d", m))m"
        }
        return "-\(m)m"
    }
}
