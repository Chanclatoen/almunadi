export function slugFromUrl(url) {
    if (!url) return null;
    const match = url.match(/mawaqit\.net\/\w+\/(?:w\/)?(.+?)\/?$/);
    return match ? match[1] : null;
}

export function toMinutes(timeStr) {
    const parts = timeStr.split(':');
    return parseInt(parts[0]) * 60 + parseInt(parts[1]);
}

export function findNextPrayerIndex(times, nowMinutes) {
    for (let i = 0; i < times.length; i++) {
        if (toMinutes(times[i]) > nowMinutes)
            return i;
    }
    return -1;
}

export function formatCountdown(remaining) {
    const h = Math.floor(remaining / 60);
    const min = remaining % 60;
    if (h > 0)
        return `-${h}h ${min.toString().padStart(2, '0')}m`;
    return `-${min}m`;
}

export function resolveIqama(prayerTime, iqamaValue) {
    if (!iqamaValue) return null;
    const val = String(iqamaValue).trim();
    if (val === '0' || val === '+0' || val === '') return null;
    if (val.includes(':')) return val;
    const offset = parseInt(val.replace('+', ''));
    if (isNaN(offset) || offset <= 0) return null;
    const total = toMinutes(prayerTime) + offset;
    const h = Math.floor(total / 60) % 24;
    const m = total % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
}

export function parseConfDataJson(html) {
    const match = html.match(/confData\s*=\s*(\{.*?\});/s);
    if (!match) return null;
    try {
        const data = JSON.parse(match[1]);
        return {
            times: data.times,
            shuruq: data.shuruq || null,
            name: data.name || data.label || '',
        };
    } catch {
        return null;
    }
}
