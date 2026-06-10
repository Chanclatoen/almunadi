import XCTest

/// Asserts the shared cross-platform fixtures, exactly like the Python suite
/// (AlMunadiWindows/test_al_munadi.py), the GNOME JS suite (tests/test_utils.js),
/// and the Rust suite (AlMunadiLinuxNative/tests/fixtures.rs). If this passes,
/// the macOS behavior core matches the shipping clients.
final class BehaviorFixtureTests: XCTestCase {
    private static var fixtures: [String: Any] = [:]

    override class func setUp() {
        super.setUp()
        Translations.activeLanguage = "en"
        guard let url = Bundle(for: BehaviorFixtureTests.self)
            .url(forResource: "behavior-fixtures", withExtension: "json"),
            let data = try? Data(contentsOf: url),
            let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any]
        else {
            fatalError("behavior-fixtures.json missing from test bundle")
        }
        fixtures = json
    }

    private func cases(_ keyPath: String...) -> [[String: Any]] {
        var node: Any? = Self.fixtures
        for key in keyPath {
            node = (node as? [String: Any])?[key]
        }
        guard let result = node as? [[String: Any]] else {
            XCTFail("fixture group \(keyPath.joined(separator: ".")) missing")
            return []
        }
        return result
    }

    func testCountdownMatchesFixtures() {
        for format in ["compact", "full"] {
            for fixture in cases("countdown", format) {
                let remaining = fixture["remaining_minutes"] as! Int
                XCTAssertEqual(
                    BehaviorFormatting.formatCountdown(remainingMinutes: remaining, format: format),
                    fixture["expected"] as! String,
                    "countdown \(format) \(remaining)"
                )
            }
        }
    }

    func testElapsedMatchesFixtures() {
        for format in ["compact", "full"] {
            for fixture in cases("elapsed_since", format) {
                let elapsed = fixture["elapsed_minutes"] as! Int
                XCTAssertEqual(
                    BehaviorFormatting.formatElapsed(elapsedMinutes: elapsed, format: format),
                    fixture["expected"] as! String,
                    "elapsed \(format) \(elapsed)"
                )
            }
        }
    }

    func testTrayTitleMatchesFixtures() {
        for fixture in cases("tray_title") {
            XCTAssertEqual(
                BehaviorFormatting.formatTrayTitle(
                    mode: fixture["mode"] as! String,
                    name: fixture["name"] as! String,
                    time: fixture["time"] as! String,
                    countdown: fixture["countdown"] as! String
                ),
                fixture["expected"] as! String,
                "tray mode \(fixture["mode"]!)"
            )
        }
    }

    func testIqamaMatchesFixtures() {
        let calendar = Calendar.current
        let baseDate = calendar.date(from: DateComponents(year: 2026, month: 6, day: 10, hour: 9))!
        for fixture in cases("iqama") {
            let resolved = PrayerListBuilder.resolveIqama(
                prayerTime: fixture["prayer_time"] as! String,
                iqamaValue: fixture["iqama"] as? String,
                baseDate: baseDate,
                calendar: calendar
            )
            XCTAssertEqual(
                resolved,
                fixture["expected"] as? String,
                "iqama \(fixture["iqama"] ?? "nil")"
            )
        }
    }

    func testOffsetApplicationMatchesFixtures() {
        guard let apply = (Self.fixtures["prayer_offsets"] as? [String: Any])?["apply"] as? [String: Any] else {
            return XCTFail("prayer_offsets.apply missing")
        }
        let times = apply["times"] as! [String]
        let offsets = apply["offsets"] as! [String: Int]
        let expected = apply["expected"] as! [String]
        let names = PrayerSettingsDefaults.offsetKeys
        let adjusted = times.enumerated().map { i, time in
            PrayerListBuilder.applyOffset(to: time, minutes: offsets[names[i]] ?? 0)
        }
        XCTAssertEqual(adjusted, expected)
    }

    func testOffsetClampMatchesFixtures() {
        guard let clamp = (Self.fixtures["prayer_offsets"] as? [String: Any])?["clamp"] as? [[String: Any]] else {
            return XCTFail("prayer_offsets.clamp missing")
        }
        for fixture in clamp {
            let expected = fixture["expected"] as! Int
            if let input = fixture["input"] as? Int {
                let merged = PrayerSettingsDefaults.mergeOffsets(["Fajr": input])
                XCTAssertEqual(merged["Fajr"], expected, "clamp \(input)")
            } else {
                // Non-integer stored values ("junk", null) fail the [String: Int]
                // decode in PrayerService, which falls back to defaultOffsets() —
                // assert that path yields the fixture's 0.
                XCTAssertEqual(PrayerSettingsDefaults.defaultOffsets()["Fajr"], expected)
            }
        }
    }

    func testJumuahNotificationKeyMatchesFixtures() {
        for fixture in cases("jumuah_notification_key") {
            XCTAssertEqual(
                PrayerSettingsDefaults.notificationKey(
                    for: fixture["index"] as! Int,
                    isFriday: fixture["is_friday"] as! Bool,
                    hasJumua: fixture["has_jumua"] as! Bool
                ),
                fixture["expected"] as! String
            )
        }
    }

    func testVersionCompareMatchesFixtures() {
        for fixture in cases("version_compare") {
            let current = fixture["current"] as! String
            let latest = fixture["latest"] as! String
            XCTAssertEqual(
                VersionCompare.isNewer(current: current, latest: latest),
                fixture["is_newer"] as! Bool,
                "version \(current) vs \(latest)"
            )
        }
    }

    func testSlugExtractionMatchesFixtures() {
        for fixture in cases("slug_extraction") {
            let input = fixture["input"] as! String
            XCTAssertEqual(
                MawaqitURL.extractSlug(from: input),
                fixture["expected"] as? String,
                "slug \(input)"
            )
        }
    }
}
