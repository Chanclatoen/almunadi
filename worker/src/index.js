const MAWAQIT_SEARCH_URL = 'https://mawaqit.net/api/2.0/mosque/search?word=';
const DEFAULT_ALLOWED_ORIGINS = [
    'https://almunadi.net',
    'https://www.almunadi.net',
    'https://chanclatoen.github.io',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
];
const RATE_LIMIT_WINDOW_MS = 60_000;
const RATE_LIMIT_MAX = 60;
// Sweep stale entries once the map grows past this many keys so a long-lived
// Worker instance handling many distinct IPs cannot leak memory unboundedly.
const RATE_LIMIT_SWEEP_THRESHOLD = 5_000;
const rateLimits = new Map();

export default {
    async fetch(request, env, ctx) {
        return handleRequest(request, env, ctx, fetch);
    },
};

export async function handleRequest(request, env = {}, ctx = {}, fetchImpl = fetch) {
    const origin = request.headers.get('Origin') || '';
    const corsHeaders = corsForOrigin(origin, env);

    if (request.method === 'OPTIONS') {
        return new Response(null, {
            status: 204,
            headers: {
                ...corsHeaders,
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Accept',
                'Access-Control-Max-Age': '86400',
            },
        });
    }

    const url = new URL(request.url);
    if (request.method !== 'GET' || url.pathname !== '/api/search') {
        return jsonResponse({ error: 'Not found' }, 404, corsHeaders);
    }

    const rate = checkRateLimit(clientKey(request));
    if (!rate.allowed) {
        return jsonResponse({ error: 'Too many requests' }, 429, {
            ...corsHeaders,
            'Retry-After': String(Math.ceil(rate.retryAfterMs / 1000)),
        });
    }

    const query = sanitizeQuery(url.searchParams.get('q'));
    if (query.length < 2) {
        return jsonResponse({ error: 'Query must be at least 2 characters' }, 400, corsHeaders);
    }

    const cacheKey = new Request(`https://next-prayer-worker.local/api/search?q=${encodeURIComponent(query)}`);
    const cache = typeof caches !== 'undefined' ? caches.default : null;
    if (cache) {
        const cached = await cache.match(cacheKey);
        if (cached) return withCors(cached, corsHeaders);
    }

    const upstream = await fetchImpl(`${MAWAQIT_SEARCH_URL}${encodeURIComponent(query)}`, {
        headers: { Accept: 'application/json' },
    });

    if (!upstream.ok) {
        return jsonResponse({ error: 'Mawaqit search unavailable' }, 502, corsHeaders);
    }

    const raw = await upstream.json();
    const results = Array.isArray(raw) ? raw.map(filterMosque).filter(m => m.slug) : [];
    const response = jsonResponse(
        { query, count: results.length, results },
        200,
        {
            ...corsHeaders,
            'Cache-Control': 'public, max-age=600, s-maxage=600',
        },
    );

    if (cache) ctx.waitUntil?.(cache.put(cacheKey, response.clone()));
    return response;
}

export function sanitizeQuery(value) {
    return String(value || '').trim().replace(/\s+/g, ' ').slice(0, 120);
}

export function allowedOrigins(env = {}) {
    const configured = String(env.ALLOWED_ORIGINS || '')
        .split(',')
        .map(item => item.trim())
        .filter(Boolean);
    return configured.length ? configured : DEFAULT_ALLOWED_ORIGINS;
}

export function corsForOrigin(origin, env = {}) {
    if (!origin) return {};
    const allowed = allowedOrigins(env);
    if (!allowed.includes(origin)) return {};
    return {
        'Access-Control-Allow-Origin': origin,
        Vary: 'Origin',
    };
}

export function filterMosque(raw = {}) {
    return {
        uuid: stringValue(raw.uuid),
        name: stringValue(raw.name || raw.label || 'Unknown mosque'),
        label: stringValue(raw.label || raw.name || 'Unknown mosque'),
        slug: stringValue(raw.slug),
        localisation: stringValue(raw.localisation),
        latitude: numberOrNull(raw.latitude),
        longitude: numberOrNull(raw.longitude),
        times: arrayOfStrings(raw.times, 6),
        iqama: arrayOfStrings(raw.iqama, 6),
        iqamaEnabled: raw.iqamaEnabled === true,
        jumua: raw.jumua ? stringValue(raw.jumua) : null,
        jumua2: raw.jumua2 ? stringValue(raw.jumua2) : null,
        womenSpace: raw.womenSpace === true,
        janazaPrayer: raw.janazaPrayer === true,
        aidPrayer: raw.aidPrayer === true,
        childrenCourses: raw.childrenCourses === true,
        adultCourses: raw.adultCourses === true,
        ramadanMeal: raw.ramadanMeal === true,
        handicapAccessibility: raw.handicapAccessibility === true,
        ablutions: raw.ablutions === true,
        parking: raw.parking === true,
    };
}

export function checkRateLimit(key, now = Date.now()) {
    if (rateLimits.size >= RATE_LIMIT_SWEEP_THRESHOLD) sweepRateLimits(now);
    const current = rateLimits.get(key);
    if (!current || now - current.startedAt >= RATE_LIMIT_WINDOW_MS) {
        rateLimits.set(key, { count: 1, startedAt: now });
        return { allowed: true, retryAfterMs: 0 };
    }
    current.count += 1;
    if (current.count > RATE_LIMIT_MAX) {
        return {
            allowed: false,
            retryAfterMs: RATE_LIMIT_WINDOW_MS - (now - current.startedAt),
        };
    }
    return { allowed: true, retryAfterMs: 0 };
}

export function sweepRateLimits(now = Date.now()) {
    for (const [key, entry] of rateLimits) {
        if (now - entry.startedAt >= RATE_LIMIT_WINDOW_MS) rateLimits.delete(key);
    }
}

// Exposed for tests to assert the rate-limit map stays bounded.
export function rateLimitSize() {
    return rateLimits.size;
}

function clientKey(request) {
    return request.headers.get('CF-Connecting-IP')
        || request.headers.get('X-Forwarded-For')
        || 'anonymous';
}

function jsonResponse(body, status, headers = {}) {
    return new Response(JSON.stringify(body), {
        status,
        headers: {
            'Content-Type': 'application/json; charset=utf-8',
            ...headers,
        },
    });
}

function withCors(response, corsHeaders) {
    const headers = new Headers(response.headers);
    for (const [key, value] of Object.entries(corsHeaders)) headers.set(key, value);
    return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers,
    });
}

function stringValue(value) {
    return String(value || '');
}

function numberOrNull(value) {
    const num = Number(value);
    return Number.isFinite(num) ? num : null;
}

function arrayOfStrings(value, limit) {
    return Array.isArray(value) ? value.slice(0, limit).map(stringValue) : [];
}
