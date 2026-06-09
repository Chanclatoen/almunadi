import {
    allowedOrigins,
    checkRateLimit,
    corsForOrigin,
    filterMosque,
    handleRequest,
    rateLimitSize,
    sanitizeQuery,
    sweepRateLimits,
} from './src/index.js';

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

assertEqual(sanitizeQuery('  dordrecht   mosque  '), 'dordrecht mosque', 'sanitizeQuery');
assert(sanitizeQuery('x'.repeat(200)).length === 120, 'sanitizeQuery length limit');

const cors = corsForOrigin('https://example.github.io', {
    ALLOWED_ORIGINS: 'https://example.github.io',
});
assertEqual(cors['Access-Control-Allow-Origin'], 'https://example.github.io', 'allowed CORS origin');
assertEqual(Object.keys(corsForOrigin('https://bad.example', {
    ALLOWED_ORIGINS: 'https://example.github.io',
})).length, 0, 'blocked CORS origin');

const filtered = filterMosque({
    uuid: '1',
    name: 'Test Mosque',
    slug: 'test-mosque',
    localisation: 'Test City',
    times: ['1', '2', '3', '4', '5', '6', '7'],
    iqama: ['+10'],
    iqamaEnabled: true,
    email: 'private@example.com',
    parking: true,
});
assertEqual(filtered.times.length, 6, 'filterMosque trims times');
assert(!('email' in filtered), 'filterMosque strips email');
assertEqual(filtered.parking, true, 'filterMosque keeps service flags');

const env = { ALLOWED_ORIGINS: 'https://example.github.io' };
const ctx = { waitUntil() {} };
const fakeFetch = async url => {
    assert(url.includes('word=irvine'), 'upstream query encoded');
    return new Response(JSON.stringify([{ name: 'Irvine Mosque', slug: 'irvine', times: ['05:00'] }]), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
    });
};

const badQuery = await handleRequest(new Request('https://worker.example/api/search?q=i'), env, ctx, fakeFetch);
assertEqual(badQuery.status, 400, 'short query rejected');

const missing = await handleRequest(new Request('https://worker.example/nope?q=irvine'), env, ctx, fakeFetch);
assertEqual(missing.status, 404, 'unknown path rejected');

const response = await handleRequest(new Request('https://worker.example/api/search?q=irvine', {
    headers: { Origin: 'https://example.github.io', 'CF-Connecting-IP': '203.0.113.10' },
}), env, ctx, fakeFetch);
const payload = await response.json();
assertEqual(response.status, 200, 'search response ok');
assertEqual(response.headers.get('Access-Control-Allow-Origin'), 'https://example.github.io', 'search CORS header');
assertEqual(response.headers.get('Cache-Control'), 'public, max-age=600, s-maxage=600', 'cache header');
assertEqual(payload.results[0].slug, 'irvine', 'search returns filtered result');

const options = await handleRequest(new Request('https://worker.example/api/search', {
    method: 'OPTIONS',
    headers: { Origin: 'https://example.github.io' },
}), env, ctx, fakeFetch);
assertEqual(options.status, 204, 'OPTIONS preflight');
assertEqual(options.headers.get('Access-Control-Allow-Methods'), 'GET, OPTIONS', 'OPTIONS methods header');
assertEqual(options.headers.get('Access-Control-Max-Age'), '86400', 'OPTIONS max-age header');
assert(options.headers.get('Access-Control-Allow-Headers').includes('Content-Type'), 'OPTIONS allow-headers');
assertEqual(options.headers.get('Access-Control-Allow-Origin'), 'https://example.github.io', 'OPTIONS CORS origin');

// allowedOrigins parsing
assertEqual(
    allowedOrigins({ ALLOWED_ORIGINS: 'https://a.com, https://b.com ,' }).join('|'),
    'https://a.com|https://b.com',
    'allowedOrigins trims and drops empties',
);
assert(allowedOrigins({}).includes('https://chanclatoen.github.io'), 'allowedOrigins falls back to defaults');

// Upstream failure -> 502
const failFetch = async () => new Response('upstream down', { status: 503 });
const upstreamFail = await handleRequest(new Request('https://worker.example/api/search?q=irvine', {
    headers: { 'CF-Connecting-IP': '203.0.113.99' },
}), env, ctx, failFetch);
assertEqual(upstreamFail.status, 502, 'upstream failure returns 502');

// Rate limiting
const t0 = 1_000_000;
let allowedCount = 0;
let blocked = null;
for (let i = 0; i < 61; i++) {
    const result = checkRateLimit('rate-test-ip', t0);
    if (result.allowed) allowedCount++;
    else blocked = result;
}
assertEqual(allowedCount, 60, 'rate limit allows 60 requests per window');
assert(blocked && blocked.allowed === false, '61st request blocked');
assert(blocked.retryAfterMs > 0, 'blocked result reports retryAfterMs');
assert(checkRateLimit('rate-test-ip', t0 + 60_000).allowed, 'rate limit resets after window');

// Stale-entry eviction keeps the map bounded. Sweep well past every entry's
// window (including the real-clock entries created by handleRequest above).
sweepRateLimits(Date.now() + 10 * 60_000);
assertEqual(rateLimitSize(), 0, 'sweepRateLimits evicts all stale entries');

// Response caching: a cache hit avoids a second upstream fetch
const store = new Map();
globalThis.caches = {
    default: {
        async match(request) { return store.get(request.url); },
        async put(request, response) { store.set(request.url, response); },
    },
};
let upstreamCalls = 0;
const cachingFetch = async () => {
    upstreamCalls++;
    return new Response(JSON.stringify([{ name: 'Cached Mosque', slug: 'cached', times: ['05:00'] }]), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
    });
};
const pending = [];
const cachingCtx = { waitUntil(promise) { pending.push(promise); } };
const cacheReq = () => new Request('https://worker.example/api/search?q=cachetest', {
    headers: { 'CF-Connecting-IP': '198.51.100.7' },
});
const firstHit = await handleRequest(cacheReq(), env, cachingCtx, cachingFetch);
await firstHit.json();
await Promise.all(pending);
const secondHit = await handleRequest(cacheReq(), env, cachingCtx, cachingFetch);
const secondBody = await secondHit.json();
assertEqual(upstreamCalls, 1, 'cache hit avoids second upstream fetch');
assertEqual(secondHit.status, 200, 'cached response served with 200');
assertEqual(secondBody.results[0].slug, 'cached', 'cached body preserved');
delete globalThis.caches;

console.log(`\nworker: ${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
