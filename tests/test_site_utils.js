import {
    buildSearchUrl,
    canonicalMosqueUrl,
    detectPlatform,
    escapeHtml,
    mapPrayerTimes,
    normalizeQuery,
    resolveIqama,
    resultMessageForError,
    resultsStatusMessage,
    sanitizeMosque,
    scoreMosque,
    serviceBadges,
    sortMosques,
} from '../site/js/mosque-utils.js';

let passed = 0;
let failed = 0;

function assert(condition, message) {
    if (condition) passed++;
    else {
        failed++;
        console.error(`FAIL: ${message}`);
    }
}

function assertEqual(actual, expected, message) {
    assert(actual === expected, `${message}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
}

const raw = {
    uuid: 'abc',
    name: 'Islamic Center Irvine',
    slug: 'islamic-center-irvine',
    localisation: 'Irvine CA USA',
    latitude: '33.6',
    longitude: '-117.8',
    times: ['05:00', '06:20', '13:00', '17:10', '20:05', '21:30', 'extra'],
    iqama: ['+10', '+0', '13:20', '+5'],
    iqamaEnabled: true,
    jumua: '13:15',
    parking: true,
    womenSpace: true,
    email: 'not-returned-to-site-helper',
};

assertEqual(normalizeQuery('  irvine   ca  '), 'irvine ca', 'normalizeQuery collapses whitespace');
assertEqual(canonicalMosqueUrl('islamic-center-irvine'), 'https://mawaqit.net/en/w/islamic-center-irvine', 'canonical URL');
assertEqual(buildSearchUrl('https://worker.example/', 'irvine ca'), 'https://worker.example/api/search?q=irvine%20ca', 'buildSearchUrl');

const mosque = sanitizeMosque(raw);
assertEqual(mosque.times.length, 6, 'sanitizeMosque limits times');
assertEqual(mosque.latitude, 33.6, 'sanitizeMosque latitude number');
assert(!('email' in mosque), 'sanitizeMosque strips unused fields');

const prayers = mapPrayerTimes(mosque);
assertEqual(prayers[0].iqama, '05:10', 'mapPrayerTimes resolves offset iqama');
assertEqual(prayers[2].iqama, '13:20', 'mapPrayerTimes preserves explicit iqama');
assertEqual(serviceBadges(mosque).join(','), 'Women space,Parking', 'service badges');

const sorted = sortMosques([
    { name: 'Remote Mosque', localisation: 'Irvine', slug: 'remote' },
    { name: 'Irvine Mosque', localisation: 'California', slug: 'irvine-mosque' },
], 'irvine');
assertEqual(sorted[0].name, 'Irvine Mosque', 'sortMosques prioritizes name matches');

assertEqual(resultMessageForError({ name: 'AbortError' }), '', 'AbortError is silent');
assert(resultMessageForError(new Error('x')).includes('Search is unavailable'), 'generic error message');

// resolveIqama edge cases
assertEqual(resolveIqama('05:00', '+10'), '05:10', 'resolveIqama applies positive offset');
assertEqual(resolveIqama('13:00', '13:20'), '13:20', 'resolveIqama preserves explicit time');
assertEqual(resolveIqama('05:00', '+0'), null, 'resolveIqama ignores +0 offset');
assertEqual(resolveIqama('05:00', '0'), null, 'resolveIqama ignores 0 offset');
assertEqual(resolveIqama('05:00', '-5'), null, 'resolveIqama ignores negative offset');
assertEqual(resolveIqama(null, '+10'), null, 'resolveIqama needs a prayer time');
assertEqual(resolveIqama('23:55', '+10'), '00:05', 'resolveIqama wraps past midnight');

// scoreMosque scoring tiers
assertEqual(scoreMosque({ name: 'Irvine' }, 'irvine'), 175, 'scoreMosque exact name match');
assertEqual(scoreMosque({ name: 'Other', localisation: 'Irvine' }, 'irvine'), 18, 'scoreMosque location-only match');
assertEqual(scoreMosque({ name: 'Irvine' }, ''), 0, 'scoreMosque returns 0 for empty query');

// canonicalMosqueUrl + buildSearchUrl base handling
assertEqual(canonicalMosqueUrl(''), '', 'canonicalMosqueUrl empty slug');
assertEqual(buildSearchUrl('', 'irvine'), '/api/search?q=irvine', 'buildSearchUrl uses relative path for same-host mount');
assertEqual(buildSearchUrl('https://w.example/', 'a b'), 'https://w.example/api/search?q=a%20b', 'buildSearchUrl strips trailing slash and encodes');

// mapPrayerTimes filters out missing times
const partial = mapPrayerTimes({ times: ['05:00', '', '13:00'] });
assertEqual(partial.length, 2, 'mapPrayerTimes drops empty times');
assertEqual(partial[1].label, 'Dhuhr', 'mapPrayerTimes keeps label alignment');

// resultsStatusMessage wording
assertEqual(resultsStatusMessage(1, 'irvine'), '1 mosque found for "irvine"', 'resultsStatusMessage singular');
assertEqual(resultsStatusMessage(12, 'Dordrecht'), '12 mosques found for "Dordrecht"', 'resultsStatusMessage plural');
assert(resultsStatusMessage(0, 'xyz').includes('Try a city name'), 'resultsStatusMessage no results gives a hint');

// detectPlatform (local-only download hint)
assertEqual(detectPlatform('Mozilla/5.0 (Windows NT 10.0; Win64; x64)'), 'windows', 'detectPlatform windows');
assertEqual(detectPlatform('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'), 'macos', 'detectPlatform macos');
assertEqual(detectPlatform('Mozilla/5.0 (X11; Linux x86_64)'), 'linux', 'detectPlatform linux');
assertEqual(detectPlatform('Mozilla/5.0 (Linux; Android 14; Pixel)'), null, 'detectPlatform ignores android');
assertEqual(detectPlatform(''), null, 'detectPlatform empty UA');

// escapeHtml neutralizes markup
assertEqual(
    escapeHtml('<b>"x"&\'</b>'),
    '&lt;b&gt;&quot;x&quot;&amp;&#039;&lt;/b&gt;',
    'escapeHtml escapes all unsafe characters',
);

console.log(`\nsite utils: ${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
