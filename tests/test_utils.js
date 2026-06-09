import {
    slugFromUrl,
    toMinutes,
    findNextPrayerIndex,
    formatCountdown,
    resolveIqama,
    parseConfDataJson,
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
    assertEqual(formatCountdown(tc.remaining_minutes), tc.expected, `countdown compact: ${tc.remaining_minutes}m`);
}

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

// --- Summary ---
console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
