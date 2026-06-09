import SwiftUI
import WidgetKit

struct LargeWidgetView: View {
    let entry: AlMunadiEntry

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text(entry.mosqueName)
                        .font(.system(size: 11))
                        .foregroundStyle(.tertiary)
                        .lineLimit(1)
                    Text(entry.nextPrayer?.displayName ?? t("next_prayer"))
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.secondary)
                }
                Spacer()
                VStack(alignment: .trailing, spacing: 2) {
                    Text(entry.nextPrayer?.time ?? "--:--")
                        .font(.system(size: 26, weight: .bold, design: .rounded))
                    if let next = entry.nextPrayer {
                        Text(next.date, style: .timer)
                            .font(.caption.weight(.medium))
                            .foregroundStyle(.tint)
                            .monospacedDigit()
                    }
                }
            }

            Divider()

            VStack(spacing: 5) {
                ForEach(entry.prayers, id: \.id) { prayer in
                    LargePrayerRow(prayer: prayer, isNext: prayer.id == entry.nextPrayer?.id)
                }
            }

            Divider()

            HStack(alignment: .top, spacing: 14) {
                if let shuruq = entry.shuruq, !shuruq.isEmpty {
                    LabelValue(label: t("shuruq"), value: shuruq)
                }
                if let qibla = entry.qiblaDirection, !qibla.isEmpty {
                    LabelValue(label: t("qibla"), value: qiblaArrow(qibla))
                }
                Spacer()
            }

            if let hijri = entry.hijriDate, !hijri.isEmpty {
                Text(hijri)
                    .font(.caption2)
                    .foregroundStyle(.tertiary)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
    }

    private func qiblaArrow(_ qibla: String) -> String {
        let digits = qibla.compactMap { $0.isNumber || $0 == "-" ? $0 : nil }
        guard let degrees = Int(String(digits)) else { return qibla }
        let arrows = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]
        let octant = ((degrees + 22) % 360) / 45
        return "\(arrows[octant]) \(degrees)°"
    }
}

private struct LabelValue: View {
    let label: String
    let value: String

    var body: some View {
        VStack(alignment: .leading, spacing: 1) {
            Text(label)
                .font(.system(size: 9))
                .foregroundStyle(.tertiary)
            Text(value)
                .font(.caption.weight(.medium))
        }
    }
}

private struct LargePrayerRow: View {
    let prayer: PrayerTime
    let isNext: Bool

    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: prayer.icon)
                .font(.caption)
                .frame(width: 18)
                .foregroundStyle(isNext ? AnyShapeStyle(.tint) : AnyShapeStyle(.secondary))
            Text(prayer.displayName)
                .font(.callout.weight(isNext ? .semibold : .regular))
                .lineLimit(1)
            Spacer()
            if let iqama = prayer.iqamaTime {
                Text(iqama)
                    .font(.caption2)
                    .foregroundStyle(.tertiary)
                    .monospacedDigit()
            }
            Text(prayer.time)
                .font(.callout.weight(isNext ? .bold : .medium))
                .monospacedDigit()
        }
        .foregroundStyle(isNext ? Color.primary : .secondary)
    }
}
