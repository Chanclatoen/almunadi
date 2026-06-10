export const PRAYER_LABELS = ['Fajr', 'Shuruq', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'];

export const SERVICE_BADGES = [
    ['womenSpace', 'Women space'],
    ['janazaPrayer', 'Janaza'],
    ['aidPrayer', 'Eid prayer'],
    ['childrenCourses', 'Children classes'],
    ['adultCourses', 'Adult classes'],
    ['ramadanMeal', 'Ramadan meal'],
    ['handicapAccessibility', 'Accessible'],
    ['ablutions', 'Ablutions'],
    ['parking', 'Parking'],
];

export function normalizeQuery(value) {
    return String(value || '').trim().replace(/\s+/g, ' ');
}

export function canonicalMosqueUrl(slug) {
    if (!slug) return '';
    return `https://mawaqit.net/en/w/${encodeURIComponent(slug)}`;
}

export function mapPrayerTimes(mosque) {
    const times = Array.isArray(mosque?.times) ? mosque.times : [];
    return PRAYER_LABELS.map((label, index) => ({
        label,
        time: times[index] || null,
        iqama: resolveIqama(times[index], mosque?.iqama?.[index]),
    })).filter(item => item.time);
}

export function resolveIqama(prayerTime, iqamaValue) {
    if (!prayerTime || !iqamaValue) return null;
    const val = String(iqamaValue).trim();
    if (!val || val === '0' || val === '+0') return null;
    if (val.includes(':')) return val;

    const offset = parseInt(val.replace('+', ''), 10);
    if (!Number.isFinite(offset) || offset <= 0) return null;

    const [h, m] = prayerTime.split(':').map(Number);
    if (!Number.isFinite(h) || !Number.isFinite(m)) return null;
    const total = h * 60 + m + offset;
    const nextH = Math.floor(((total % 1440) + 1440) % 1440 / 60);
    const nextM = ((total % 60) + 60) % 60;
    return `${String(nextH).padStart(2, '0')}:${String(nextM).padStart(2, '0')}`;
}

export function serviceBadges(mosque) {
    return SERVICE_BADGES
        .filter(([key]) => mosque?.[key] === true)
        .map(([, label]) => label);
}

export function sanitizeMosque(raw) {
    const slug = String(raw?.slug || '');
    return {
        uuid: String(raw?.uuid || slug),
        name: String(raw?.name || raw?.label || 'Unknown mosque'),
        label: String(raw?.label || raw?.name || 'Unknown mosque'),
        slug,
        localisation: String(raw?.localisation || ''),
        latitude: numberOrNull(raw?.latitude),
        longitude: numberOrNull(raw?.longitude),
        times: Array.isArray(raw?.times) ? raw.times.slice(0, 6).map(String) : [],
        iqama: Array.isArray(raw?.iqama) ? raw.iqama.slice(0, 6).map(String) : [],
        iqamaEnabled: raw?.iqamaEnabled === true,
        jumua: raw?.jumua ? String(raw.jumua) : null,
        jumua2: raw?.jumua2 ? String(raw.jumua2) : null,
        womenSpace: raw?.womenSpace === true,
        janazaPrayer: raw?.janazaPrayer === true,
        aidPrayer: raw?.aidPrayer === true,
        childrenCourses: raw?.childrenCourses === true,
        adultCourses: raw?.adultCourses === true,
        ramadanMeal: raw?.ramadanMeal === true,
        handicapAccessibility: raw?.handicapAccessibility === true,
        ablutions: raw?.ablutions === true,
        parking: raw?.parking === true,
    };
}

export function sortMosques(results, query) {
    const normalized = normalizeQuery(query).toLocaleLowerCase();
    return [...results].sort((a, b) => scoreMosque(b, normalized) - scoreMosque(a, normalized));
}

export function scoreMosque(mosque, normalizedQuery) {
    if (!normalizedQuery) return 0;
    const name = String(mosque?.name || mosque?.label || '').toLocaleLowerCase();
    const location = String(mosque?.localisation || '').toLocaleLowerCase();
    const slug = String(mosque?.slug || '').toLocaleLowerCase();

    let score = 0;
    if (name === normalizedQuery) score += 100;
    if (name.startsWith(normalizedQuery)) score += 45;
    if (name.includes(normalizedQuery)) score += 30;
    if (location.includes(normalizedQuery)) score += 18;
    if (slug.includes(normalizedQuery.replace(/\s+/g, '-'))) score += 10;
    return score;
}

export function buildSearchUrl(apiBase, query) {
    // An empty base is a supported deployment: the Worker is mounted on the same
    // host as the site, so the request goes to a relative `/api/search` path.
    const base = String(apiBase || '').replace(/\/$/, '');
    return `${base}/api/search?q=${encodeURIComponent(normalizeQuery(query))}`;
}

export function resultMessageForError(error) {
    if (error?.name === 'AbortError') return '';
    return 'Search is unavailable. Check the Worker URL in site/config.js or try again later.';
}

export function resultsStatusMessage(count, query) {
    if (!count) return `No mosques found for "${query}". Try a city name instead of the mosque name, and check the spelling.`;
    return `${count} mosque${count === 1 ? '' : 's'} found for "${query}"`;
}

// Local-only platform hint used to highlight the matching download card.
// Nothing is sent anywhere; this only reads the user agent string.
export function detectPlatform(userAgent) {
    const ua = String(userAgent || '').toLowerCase();
    if (ua.includes('windows')) return 'windows';
    if (ua.includes('mac os') || ua.includes('macintosh')) return 'macos';
    if (ua.includes('android')) return null;
    if (ua.includes('linux') || ua.includes('x11')) return 'linux';
    return null;
}

export function escapeHtml(value) {
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function numberOrNull(value) {
    const num = Number(value);
    return Number.isFinite(num) ? num : null;
}
