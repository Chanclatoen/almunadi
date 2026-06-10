import {
    buildSearchUrl,
    canonicalMosqueUrl,
    detectPlatform,
    escapeHtml,
    mapPrayerTimes,
    normalizeQuery,
    resultMessageForError,
    resultsStatusMessage,
    sanitizeMosque,
    serviceBadges,
    sortMosques,
} from './mosque-utils.js?v=2';

const config = window.AL_MUNADI_CONFIG || {};
const state = {
    controller: null,
    debounceTimer: null,
    lastQuery: '',
    results: [],
};

const els = {
    form: document.querySelector('[data-search-form]'),
    input: document.querySelector('[data-search-input]'),
    status: document.querySelector('[data-status]'),
    results: document.querySelector('[data-results]'),
    empty: document.querySelector('[data-empty]'),
    retry: document.querySelector('[data-retry]'),
    chips: document.querySelectorAll('[data-chip]'),
    navToggle: document.querySelector('[data-nav-toggle]'),
    nav: document.querySelector('[data-nav]'),
    releasesLinks: document.querySelectorAll('[data-releases-link]'),
    repoLinks: document.querySelectorAll('[data-repo-link]'),
    repoPathLinks: document.querySelectorAll('[data-repo-path]'),
};

initExternalLinks();
initNav();
initChips();
initReveal();
initPlatformHint();
initSearch();

/* ---------- external links (config-driven) ---------- */

function initExternalLinks() {
    for (const link of els.releasesLinks) link.href = config.releasesUrl || '#';
    for (const link of els.repoLinks) link.href = config.repoUrl || '#';
    for (const link of els.repoPathLinks) {
        const path = link.getAttribute('data-repo-path') || '';
        const repo = (config.repoUrl || '').replace(/\/$/, '');
        // Paths starting with "#" are anchors into the repo README.
        link.href = repo ? (path.startsWith('#') ? repo + path : `${repo}/${path}`) : '#';
    }
}

/* ---------- header nav (mobile) ---------- */

function initNav() {
    if (!els.navToggle || !els.nav) return;

    const setOpen = open => {
        els.navToggle.setAttribute('aria-expanded', String(open));
        els.nav.classList.toggle('is-open', open);
    };

    els.navToggle.addEventListener('click', () => {
        setOpen(els.navToggle.getAttribute('aria-expanded') !== 'true');
    });

    // Close when a nav link is chosen, on Escape, or on a click outside.
    els.nav.addEventListener('click', event => {
        if (event.target.closest('a')) setOpen(false);
    });
    document.addEventListener('keydown', event => {
        if (event.key !== 'Escape') return;
        if (els.navToggle.getAttribute('aria-expanded') !== 'true') return;
        setOpen(false);
        els.navToggle.focus();
    });
    document.addEventListener('click', event => {
        if (els.navToggle.getAttribute('aria-expanded') !== 'true') return;
        if (event.target.closest('[data-nav], [data-nav-toggle]')) return;
        setOpen(false);
    });
}

/* ---------- example search chips ---------- */

function initChips() {
    for (const chip of els.chips) {
        chip.addEventListener('click', () => {
            els.input.value = chip.textContent.trim();
            els.input.focus();
            runSearch(els.input.value);
        });
    }
}

/* ---------- scroll reveal (progressive enhancement) ---------- */

// If JS or IntersectionObserver is unavailable, or the user prefers reduced
// motion, elements are never given the `reveal` class and render fully visible.
function initReveal() {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!('IntersectionObserver' in window) || prefersReducedMotion) return;

    const observer = new IntersectionObserver(entries => {
        for (const entry of entries) {
            if (!entry.isIntersecting) continue;
            entry.target.classList.add('in');
            observer.unobserve(entry.target);
        }
    }, { threshold: 0.12 });

    for (const element of document.querySelectorAll('[data-reveal]')) {
        element.classList.add('reveal');
        observer.observe(element);
    }
}

/* ---------- platform hint (local-only, reads the UA string) ---------- */

function initPlatformHint() {
    const platform = detectPlatform(navigator.userAgent);
    if (!platform) return;
    // On Linux both the tray app and the GNOME extension are relevant.
    const targets = platform === 'linux' ? ['linux', 'gnome'] : [platform];
    for (const name of targets) {
        const card = document.querySelector(`.download-card[data-platform="${name}"]`);
        if (!card) continue;
        card.classList.add('is-suggested');
        const flag = card.querySelector('.platform-flag');
        if (flag) flag.hidden = false;
    }
}

/* ---------- mosque search ---------- */

function initSearch() {
    if (!els.form) return;

    const initialQuery = normalizeQuery(new URLSearchParams(window.location.search).get('q'));
    if (initialQuery) {
        els.input.value = initialQuery;
        runSearch(initialQuery);
    }

    els.form.addEventListener('submit', event => {
        event.preventDefault();
        runSearch(els.input.value);
    });

    els.input.addEventListener('input', () => {
        window.clearTimeout(state.debounceTimer);
        state.debounceTimer = window.setTimeout(() => runSearch(els.input.value), 300);
    });

    els.retry.addEventListener('click', () => runSearch(state.lastQuery));
}

async function runSearch(rawQuery) {
    const query = normalizeQuery(rawQuery);
    state.lastQuery = query;
    syncQueryParam(query);

    if (state.controller) state.controller.abort();
    els.retry.hidden = true;
    els.results.innerHTML = '';

    if (query.length < 2) {
        setStatus('');
        showEmpty(true);
        return;
    }

    state.controller = new AbortController();
    setStatus('Searching public Mawaqit mosques…');
    showEmpty(false);
    renderSkeletons();

    try {
        const response = await fetch(buildSearchUrl(config.apiBase, query), {
            signal: state.controller.signal,
            headers: { Accept: 'application/json' },
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(payload.error || `Search failed (${response.status})`);

        const rawResults = Array.isArray(payload.results) ? payload.results : [];
        state.results = sortMosques(rawResults.map(sanitizeMosque), query);
        renderResults(state.results, query);
    } catch (error) {
        const message = resultMessageForError(error);
        if (!message) return;
        els.results.innerHTML = '';
        setStatus(message);
        els.retry.hidden = false;
        showEmpty(false);
    }
}

function renderSkeletons(count = 3) {
    const fragment = document.createDocumentFragment();
    for (let i = 0; i < count; i++) {
        const card = document.createElement('div');
        card.className = 'skeleton-card';
        card.setAttribute('aria-hidden', 'true');
        card.innerHTML = `
            <div class="skeleton-line is-title"></div>
            <div class="skeleton-line is-sub"></div>
            <div class="skeleton-line is-block"></div>
        `;
        fragment.appendChild(card);
    }
    els.results.replaceChildren(fragment);
}

function renderResults(results, query) {
    els.results.innerHTML = '';
    setStatus(resultsStatusMessage(results.length, query));
    if (!results.length) {
        showEmpty(false);
        return;
    }

    const fragment = document.createDocumentFragment();
    for (const mosque of results) fragment.appendChild(renderCard(mosque));
    els.results.appendChild(fragment);
}

function renderCard(mosque) {
    const article = document.createElement('article');
    article.className = 'card';

    const url = canonicalMosqueUrl(mosque.slug);
    const prayerTimes = mapPrayerTimes(mosque);
    const badges = serviceBadges(mosque);

    article.innerHTML = `
        <div class="card-head">
            <div>
                <h3>${escapeHtml(mosque.name)}</h3>
                <p class="card-loc">${escapeHtml(mosque.localisation || 'Location not listed')}</p>
            </div>
            <div class="card-actions">
                <button type="button" class="ghost" data-copy="${escapeHtml(url)}">Copy link</button>
                <a class="solid" href="${escapeHtml(url)}" target="_blank" rel="noreferrer">Open on Mawaqit</a>
            </div>
        </div>
        <div class="times">
            ${prayerTimes.map(item => `
                <div class="time">
                    <span class="time-label">${escapeHtml(item.label)}</span>
                    <strong class="time-val">${escapeHtml(item.time)}</strong>
                    ${item.iqama ? `<span class="time-iqama">Iqama ${escapeHtml(item.iqama)}</span>` : ''}
                </div>
            `).join('')}
        </div>
        ${mosque.jumua || mosque.jumua2 ? `
            <div class="jumua">
                ${mosque.jumua ? `<span>Jumuah <strong>${escapeHtml(mosque.jumua)}</strong></span>` : ''}
                ${mosque.jumua2 ? `<span>Jumuah 2 <strong>${escapeHtml(mosque.jumua2)}</strong></span>` : ''}
            </div>
        ` : ''}
        ${badges.length ? `<div class="badges">${badges.map(label => `<span>${escapeHtml(label)}</span>`).join('')}</div>` : ''}
        <div class="card-foot">
            <code>${escapeHtml(url)}</code>
            <a href="#how">Use in app</a>
        </div>
    `;

    const copyButton = article.querySelector('[data-copy]');
    copyButton.addEventListener('click', async () => {
        const copied = await copyText(url);
        copyButton.textContent = copied ? 'Copied ✓' : 'Copy failed';
        copyButton.classList.toggle('is-copied', copied);
        window.setTimeout(() => {
            copyButton.textContent = 'Copy link';
            copyButton.classList.remove('is-copied');
        }, 1500);
    });

    return article;
}

function setStatus(message) {
    els.status.textContent = message;
}

function showEmpty(visible) {
    els.empty.hidden = !visible;
}

function syncQueryParam(query) {
    const url = new URL(window.location.href);
    if (query) url.searchParams.set('q', query);
    else url.searchParams.delete('q');
    window.history.replaceState({}, '', url);
}

async function copyText(value) {
    try {
        if (navigator.clipboard?.writeText) {
            await navigator.clipboard.writeText(value);
            return true;
        }
    } catch {
        // Fall through to the textarea fallback.
    }

    const textarea = document.createElement('textarea');
    textarea.value = value;
    textarea.setAttribute('readonly', '');
    textarea.style.position = 'fixed';
    textarea.style.left = '-9999px';
    document.body.appendChild(textarea);
    textarea.select();
    try {
        return document.execCommand('copy');
    } finally {
        textarea.remove();
    }
}
