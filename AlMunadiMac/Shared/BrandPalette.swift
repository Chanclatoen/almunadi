import SwiftUI
import AppKit

extension NSColor {
    convenience init(hex: UInt32) {
        self.init(
            srgbRed: CGFloat((hex >> 16) & 0xFF) / 255,
            green: CGFloat((hex >> 8) & 0xFF) / 255,
            blue: CGFloat(hex & 0xFF) / 255,
            alpha: 1
        )
    }
}

/// Al Munadi brand palette (shared/product-behavior.md §2). Accent colors
/// only — windows and menus keep their native materials. Dark values come
/// from the canonical dark-surface palette; light values are darker
/// equivalents chosen for contrast on light backgrounds.
enum Brand {
    /// Emerald — next prayer, primary actions.
    static let accent = dynamic(dark: 0x46C79E, light: 0x0F5D47)
    /// Saffron — Shuruq, Jumuah, cached/warning hints.
    static let saffron = dynamic(dark: 0xE3B15A, light: 0xB07F2F)
    /// Calm error text (never red walls).
    static let errorText = dynamic(dark: 0xE0B36A, light: 0x9C6F1E)
    /// Text placed on an accent-filled surface.
    static let onAccent = Color(nsColor: NSColor(hex: 0x0C1A14))

    static func prayerColor(_ name: PrayerName) -> Color {
        switch name {
        case .fajr: return dynamic(dark: 0xD9A05B, light: 0xA8742F)
        case .dhuhr: return dynamic(dark: 0xE3B15A, light: 0xB07F2F)
        case .asr: return dynamic(dark: 0xBC8A52, light: 0x8E6231)
        case .maghrib: return dynamic(dark: 0xC96B4A, light: 0xA04D30)
        case .isha: return dynamic(dark: 0x7D93C4, light: 0x4A608E)
        }
    }

    private static func dynamic(dark: UInt32, light: UInt32) -> Color {
        Color(nsColor: NSColor(name: nil) { appearance in
            appearance.bestMatch(from: [.aqua, .darkAqua]) == .darkAqua
                ? NSColor(hex: dark)
                : NSColor(hex: light)
        })
    }
}
