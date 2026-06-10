import SwiftUI
import WidgetKit

struct SmallWidgetView: View {
    let entry: AlMunadiEntry

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(spacing: 4) {
                if let next = entry.nextPrayer {
                    Image(systemName: next.icon)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
                Text(entry.nextPrayer?.displayName ?? t("next_prayer"))
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.secondary)
                Spacer()
            }

            Text(entry.nextPrayer?.time ?? "--:--")
                .font(.system(size: 34, weight: .bold, design: .rounded))
                .minimumScaleFactor(0.6)
                .lineLimit(1)

            if let next = entry.nextPrayer {
                Text(next.date, style: .timer)
                    .font(.caption.weight(.medium))
                    .foregroundStyle(.tint)
                    .monospacedDigit()
            }

            Spacer(minLength: 0)
            if entry.isStale {
                HStack(spacing: 3) {
                    Image(systemName: "clock.arrow.circlepath")
                        .font(.system(size: 8))
                    Text(t("cached_data"))
                        .font(.system(size: 9))
                }
                .foregroundStyle(Brand.saffron)
                .lineLimit(1)
            } else {
                Text(entry.mosqueName)
                    .font(.system(size: 10))
                    .foregroundStyle(.tertiary)
                    .lineLimit(1)
                    .truncationMode(.tail)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .leading)
    }
}
