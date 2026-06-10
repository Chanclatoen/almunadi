import {
    slugFromUrl,
    toMinutes,
    findNextPrayerIndex,
    formatCountdown,
    resolveIqama,
    parseConfDataJson,
    applyOffset,
    applyPrayerOffsets,
    mergePrayerNotificationSettings,
    mergePrayerOffsets,
    formatTrayText,
    notificationKeyForIndex,
    shouldPlayAdhan,
    defaultPrayerNotificationSettings,
} from './utils.js';

import { readFileSync } from 'fs';

const fixtures = JSON.parse(readFileSync(new URL('./test-fixtures.json', import.meta.url), 'utf-8'));

let passed = 0;
let failed = 0;

function assert(condition, message) {
    if (condition) {
        passed++;
    } else {
        failed++;
        console.error(`FAIL: ${message}`);
    }
}

function assertEqual(actual, expected, message) {
    assert(
        actual === expected,
        `${message}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`
    );
}

// --- slugFromUrl (from fixtures) ---
for (const tc of fixtures.slug_extraction) {
    assertEqual(slugFromUrl(tc.input), tc.expected, `slug: "${tc.input}"`);
}
assertEqual(slugFromUrl(null), null, 'slug: null');

// --- toMinutes (from fixtures) ---
for (const tc of fixtures.to_minutes) {
    assertEqual(toMinutes(tc.input), tc.expected, `toMinutes: ${tc.input}`);
}

// --- findNextPrayerIndex (from fixtures) ---
const npf = fixtures.next_prayer_index;
for (const tc of npf.cases) {
    assertEqual(
        findNextPrayerIndex(npf.times, tc.now_minutes),
        tc.expected,
        `nextPrayer: ${tc.description}`
    );
}

// --- formatCountdown compact (from fixtures) ---
for (const tc of fixtures.format_countdown.compact) {
    assertEqual(formatCountdown(tc.remaining_minutes, 'compact'), tc.expected, `countdown compact: ${tc.remaining_minutes}m`);
}

// --- formatCountdown full (from fixtures) ---
for (const tc of fixtures.format_countdown.full) {
    assertEqual(formatCountdown(tc.remaining_minutes, 'full'), tc.expected, `countdown full: ${tc.remaining_minutes}m`);
}

// --- applyOffset ---
for (const tc of fixtures.apply_offset) {
    assertEqual(applyOffset(tc.time, tc.offset), tc.expected, `applyOffset: ${tc.time} + ${tc.offset}`);
}

// --- applyPrayerOffsets ---
const apo = fixtures.apply_prayer_offsets;
assertEqual(
    JSON.stringify(applyPrayerOffsets(apo.times, apo.offsets)),
    JSON.stringify(apo.expected),
    'applyPrayerOffsets'
);

// --- next prayer with offsets ---
const npo = fixtures.next_prayer_with_offsets;
for (const tc of npo.cases) {
    assertEqual(
        findNextPrayerIndex(npo.times, tc.now_minutes),
        tc.expected,
        `nextPrayerWithOffsets: ${tc.description}`
    );
}
for (const tc of fixtures.next_prayer_with_wrapped_offsets) {
    assertEqual(
        findNextPrayerIndex(tc.times, tc.now_minutes),
        tc.expected,
        `nextPrayerWithWrappedOffsets: ${tc.description}`
    );
}

// --- formatDisplay ---
for (const tc of fixtures.format_display) {
    assertEqual(
        formatTrayText({
            displayMode: tc.mode,
            countdownFormat: tc.format,
            name: tc.name,
            time: tc.time,
            remainingMinutes: tc.remaining,
        }),
        tc.expected_tray,
        `formatTrayText: ${tc.mode}`
    );
}

// --- notification settings migration ---
const defaults = defaultPrayerNotificationSettings();
assert(defaults.Fajr.enabled === true, 'default Fajr enabled');
assert(defaults.Jumuah.enabled === true, 'default Jumuah enabled');
const merged = mergePrayerNotificationSettings({ Asr: { enabled: false, reminder_minutes: 10 } });
assert(merged.Asr.enabled === false, 'merged Asr disabled');
assert(merged.Asr.reminder_minutes === 10, 'merged Asr reminder');
assert(merged.Fajr.enabled === true, 'merged Fajr still enabled');

// --- prayer offsets migration ---
const offsets = mergePrayerOffsets({ Maghrib: 90, Isha: -5 });
assert(offsets.Maghrib === 60, 'offset clamped to +60');
assert(offsets.Isha === -5, 'offset -5 preserved');

// --- Jumuah notification key ---
assertEqual(notificationKeyForIndex(1, true, true), 'Jumuah', 'Jumuah key on Friday');
assertEqual(notificationKeyForIndex(1, false, true), 'Dhuhr', 'Dhuhr key on weekday');

// --- shouldPlayAdhan ---
assert(shouldPlayAdhan({ adhan_enabled: null }, true) === true, 'adhan falls back to global');
assert(shouldPlayAdhan({ adhan_enabled: false }, true) === false, 'adhan per-prayer override off');
assert(shouldPlayAdhan({ adhan_enabled: true }, false) === true, 'adhan per-prayer override on');

// --- resolveIqama (from fixtures) ---
for (const tc of fixtures.resolve_iqama) {
    assertEqual(
        resolveIqama(tc.prayer_time, tc.iqama_value),
        tc.expected,
        `iqama: ${tc.prayer_time} + ${JSON.stringify(tc.iqama_value)}`
    );
}

// --- parseConfDataJson (from fixtures) ---
const cdf = fixtures.confdata_html;
const parsed = parseConfDataJson(cdf.valid);
assert(parsed !== null, 'parseConfData: not null');
assertEqual(parsed?.times?.length, cdf.expected_times.length, 'parseConfData: times count');
assertEqual(parsed?.shuruq, cdf.expected_shuruq, 'parseConfData: shuruq');
assertEqual(parsed?.name, cdf.expected_name, 'parseConfData: name');
assertEqual(parseConfDataJson(cdf.invalid), null, 'parseConfData: invalid html returns null');

// --- Translations fixture validation ---
const tf = fixtures.translations;
assert(tf.supported_languages.length >= 4, 'translations: at least 4 languages');
for (const lang of tf.supported_languages) {
    assertEqual(tf.prayer_names[lang]?.length, 5, `translations: ${lang} has 5 prayer names`);
}

// Validate translation JSON files exist and have all required keys
for (const lang of tf.supported_languages) {
    try {
        const trans = JSON.parse(readFileSync(new URL(`../translations/${lang}.json`, import.meta.url), 'utf-8'));
        for (const key of tf.required_keys) {
            assert(key in trans, `translations/${lang}.json has key "${key}"`);
        }
    } catch (e) {
        assert(false, `translations/${lang}.json readable: ${e.message}`);
    }
}

// --- Shared cross-platform fixtures (shared/fixtures/behavior-fixtures.json) ---
// The Python suite asserts the same cases, so platform behavior cannot drift.
const shared = JSON.parse(readFileSync(new URL('../shared/fixtures/behavior-fixtures.json', import.meta.url), 'utf-8'));

for (const fmt of ['compact', 'full']) {
    for (const tc of shared.countdown[fmt]) {
        assertEqual(formatCountdown(tc.remaining_minutes, fmt), tc.expected, `shared countdown ${fmt}: ${tc.remaining_minutes}m`);
    }
}

for (const tc of shared.tray_title) {
    assertEqual(
        formatTrayText({ displayMode: tc.mode, countdownFormat: 'compact', name: tc.name, time: tc.time, remainingMinutes: tc.remaining_minutes }),
        tc.expected,
        `shared tray title: ${tc.mode}`
    );
}

for (const tc of shared.iqama) {
    assertEqual(resolveIqama(tc.prayer_time, tc.iqama), tc.expected, `shared iqama: ${JSON.stringify(tc.iqama)}`);
}

const sharedApply = shared.prayer_offsets.apply;
assertEqual(
    JSON.stringify(applyPrayerOffsets(sharedApply.times, sharedApply.offsets)),
    JSON.stringify(sharedApply.expected),
    'shared applyPrayerOffsets'
);
for (const tc of shared.prayer_offsets.clamp) {
    assertEqual(mergePrayerOffsets({ Fajr: tc.input }).Fajr, tc.expected, `shared offset clamp: ${JSON.stringify(tc.input)}`);
}

for (const tc of shared.jumuah_notification_key) {
    assertEqual(notificationKeyForIndex(tc.index, tc.is_friday, tc.has_jumua), tc.expected, `shared jumuah key: index ${tc.index}`);
}

for (const tc of shared.slug_extraction) {
    assertEqual(slugFromUrl(tc.input), tc.expected, `shared slug: "${tc.input}"`);
}

// --- Summary ---
console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
