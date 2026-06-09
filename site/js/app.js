import {
    buildSearchUrl,
    canonicalMosqueUrl,
    escapeHtml,
    mapPrayerTimes,
    normalizeQuery,
    resultMessageForError,
    sanitizeMosque,
    serviceBadges,
    sortMosques,
} from './mosque-utils.js';

const config = window.NEXT_PRAYER_CONFIG || {};
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
    releasesLinks: document.querySelectorAll('[data-releases-link]'),
    repoLinks: document.querySelectorAll('[data-repo-link]'),
};

for (const link of els.releasesLinks) link.href = config.releasesUrl || '#';
for (const link of els.repoLinks) link.href = config.repoUrl || '#';

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
    setStatus('Searching Mawaqit mosques...');
    showEmpty(false);

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
        setStatus(message);
        els.retry.hidden = false;
        showEmpty(false);
    }
}

function renderResults(results, query) {
    els.results.innerHTML = '';
    if (!results.length) {
        setStatus(`No Mawaqit mosques found for "${query}".`);
        showEmpty(false);
        return;
    }

    setStatus(`${results.length} result${results.length === 1 ? '' : 's'} for "${query}"`);
    const fragment = document.createDocumentFragment();
    for (const mosque of results) fragment.appendChild(renderCard(mosque));
    els.results.appendChild(fragment);
}

function renderCard(mosque) {
    const article = document.createElement('article');
    article.className = 'result-card';

    const url = canonicalMosqueUrl(mosque.slug);
    const prayerTimes = mapPrayerTimes(mosque);
    const badges = serviceBadges(mosque);

    article.innerHTML = `
        <div class="result-main">
            <div>
                <h3>${escapeHtml(mosque.name)}</h3>
                <p>${escapeHtml(mosque.localisation || 'Location not listed')}</p>
            </div>
            <div class="actions">
                <button type="button" class="secondary" data-copy="${escapeHtml(url)}">Copy URL</button>
                <a class="primary" href="${escapeHtml(url)}" target="_blank" rel="noreferrer">Open</a>
            </div>
        </div>
        <div class="times-grid">
            ${prayerTimes.map(item => `
                <div class="time-cell">
                    <span>${escapeHtml(item.label)}</span>
                    <strong>${escapeHtml(item.time)}</strong>
                    ${item.iqama ? `<small>Iqama ${escapeHtml(item.iqama)}</small>` : ''}
                </div>
            `).join('')}
        </div>
        ${mosque.jumua || mosque.jumua2 ? `
            <div class="jumua-row">
                ${mosque.jumua ? `<span>Jumuah <strong>${escapeHtml(mosque.jumua)}</strong></span>` : ''}
                ${mosque.jumua2 ? `<span>Jumuah 2 <strong>${escapeHtml(mosque.jumua2)}</strong></span>` : ''}
            </div>
        ` : ''}
        ${badges.length ? `<div class="badges">${badges.map(label => `<span>${escapeHtml(label)}</span>`).join('')}</div>` : ''}
        <div class="setup-row">
            <code>${escapeHtml(url)}</code>
            <a href="#setup">Use in app</a>
        </div>
    `;

    const copyButton = article.querySelector('[data-copy]');
    copyButton.addEventListener('click', async () => {
        const copied = await copyText(url);
        copyButton.textContent = copied ? 'Copied' : 'Copy failed';
        window.setTimeout(() => { copyButton.textContent = 'Copy URL'; }, 1500);
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
