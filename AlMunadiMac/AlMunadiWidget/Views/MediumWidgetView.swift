import SwiftUI
import WidgetKit

struct MediumWidgetView: View {
    let entry: AlMunadiEntry

    var body: some View {
        HStack(alignment: .top, spacing: 14) {
            VStack(alignment: .leading, spacing: 4) {
                Text(entry.mosqueName)
                    .font(.system(size: 10))
                    .foregroundStyle(.tertiary)
                    .lineLimit(1)

                if entry.isStale {
                    HStack(spacing: 3) {
                        Image(systemName: "clock.arrow.circlepath")
                            .font(.system(size: 8))
                        Text(t("cached_data"))
                            .font(.system(size: 9))
                    }
                    .foregroundStyle(Brand.saffron)
                    .lineLimit(1)
                }

                Text(entry.nextPrayer?.displayName ?? t("next_prayer"))
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.secondary)

                Text(entry.nextPrayer?.time ?? "--:--")
                    .font(.system(size: 30, weight: .bold, design: .rounded))
                    .minimumScaleFactor(0.7)
                    .lineLimit(1)

                if let next = entry.nextPrayer {
                    Text(next.date, style: .timer)
                        .font(.caption.weight(.medium))
                        .foregroundStyle(.tint)
                        .monospacedDigit()
                }

                Spacer(minLength: 0)
            }
            .frame(maxWidth: .infinity, alignment: .leading)

            VStack(spacing: 3) {
                ForEach(entry.prayers, id: \.id) { prayer in
                    PrayerRow(prayer: prayer, isNext: prayer.id == entry.nextPrayer?.id)
                }
            }
            .frame(maxWidth: .infinity)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

struct PrayerRow: View {
    let prayer: PrayerTime
    let isNext: Bool

    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: prayer.icon)
                .font(.caption2)
                .frame(width: 14)
                .foregroundStyle(isNext ? AnyShapeStyle(.tint) : AnyShapeStyle(.secondary))
            Text(prayer.displayName)
                .font(.caption.weight(isNext ? .semibold : .regular))
                .lineLimit(1)
            Spacer()
            Text(prayer.time)
                .font(.caption.weight(isNext ? .bold : .medium))
                .monospacedDigit()
        }
        .foregroundStyle(isNext ? Color.primary : .secondary)
    }
}
