export const PRAYER_KEYS = ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'];
export const NOTIFICATION_PRAYER_KEYS = [...PRAYER_KEYS, 'Jumuah'];

export function slugFromUrl(url) {
    if (!url) return null;
    const match = url.match(/mawaqit\.net\/\w+\/(?:w\/)?(.+?)\/?$/);
    return match ? match[1] : null;
}

export function toMinutes(timeStr) {
    const parts = timeStr.split(':');
    return parseInt(parts[0]) * 60 + parseInt(parts[1]);
}

export function fromMinutes(total) {
    const normalized = ((total % 1440) + 1440) % 1440;
    const h = Math.floor(normalized / 60);
    const m = normalized % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
}

export function applyOffset(timeStr, offsetMinutes) {
    if (!offsetMinutes) return timeStr;
    return fromMinutes(toMinutes(timeStr) + offsetMinutes);
}

export function applyPrayerOffsets(times, offsets = {}) {
    return times.map((time, i) => applyOffset(time, offsets[PRAYER_KEYS[i]] || 0));
}

export function defaultPrayerNotificationSettings() {
    const settings = {};
    for (const key of NOTIFICATION_PRAYER_KEYS) {
        settings[key] = { enabled: true, reminder_minutes: 0, adhan_enabled: null };
    }
    return settings;
}

export function defaultPrayerOffsets() {
    const offsets = {};
    for (const key of PRAYER_KEYS) {
        offsets[key] = 0;
    }
    return offsets;
}

export function mergePrayerNotificationSettings(stored) {
    const merged = defaultPrayerNotificationSettings();
    if (!stored || typeof stored !== 'object') return merged;
    for (const key of NOTIFICATION_PRAYER_KEYS) {
        if (stored[key]) {
            merged[key] = {
                enabled: stored[key].enabled !== false,
                reminder_minutes: Math.max(0, parseInt(stored[key].reminder_minutes) || 0),
                adhan_enabled: stored[key].adhan_enabled ?? null,
            };
        }
    }
    return merged;
}

export function mergePrayerOffsets(stored) {
    const merged = defaultPrayerOffsets();
    if (!stored || typeof stored !== 'object') return merged;
    for (const key of PRAYER_KEYS) {
        if (stored[key] !== undefined) {
            const val = parseInt(stored[key]) || 0;
            merged[key] = Math.max(-60, Math.min(60, val));
        }
    }
    return merged;
}

export function notificationKeyForIndex(index, isFriday, hasJumua) {
    if (index === 1 && isFriday && hasJumua) return 'Jumuah';
    return PRAYER_KEYS[index];
}

export function prayerEvents(times) {
    const minuteValues = times.map(toMinutes);
    const events = [];
    let dayOffset = minuteValues.length > 1 && minuteValues[0] > minuteValues[1] ? -1 : 0;
    let previousAbsolute = null;

    for (let i = 0; i < minuteValues.length; i++) {
        if (i > 0) {
            if (dayOffset < 0) dayOffset = 0;
            while (previousAbsolute !== null && minuteValues[i] + dayOffset * 1440 <= previousAbsolute)
                dayOffset++;
        }

        const absoluteMinutes = minuteValues[i] + dayOffset * 1440;
        previousAbsolute = absoluteMinutes;
        events.push({ index: i, absoluteMinutes });
    }

    return events;
}

export function findNextPrayerIndex(times, nowMinutes) {
    for (const event of prayerEvents(times)) {
        if (event.absoluteMinutes > nowMinutes)
            return event.index;
    }
    const first = prayerEvents(times)[0];
    if (first && first.absoluteMinutes + 1440 > nowMinutes && first.absoluteMinutes < 0)
        return first.index;
    return -1;
}

export function formatCountdown(remaining, format = 'compact') {
    if (remaining <= 0) return 'now';
    const h = Math.floor(remaining / 60);
    const min = remaining % 60;
    if (format === 'full') {
        if (h > 0)
            return `-${h}h ${min.toString().padStart(2, '0')}m`;
        return `-${min}m`;
    }
    if (h > 0)
        return `-${h}h${min.toString().padStart(2, '0')}m`;
    return `-${min}m`;
}

export function formatDisplayParts({ displayMode = 'countdown', countdownFormat = 'compact', name, time, remainingMinutes }) {
    const countdown = formatCountdown(remainingMinutes, countdownFormat);
    switch (displayMode) {
    case 'time':
        return { name, time, countdown: '', showIcon: true };
    case 'name':
        return { name, time: '', countdown: '', showIcon: true };
    case 'compact':
        return { name, time: '', countdown, showIcon: true };
    case 'icon':
        return { name: '', time: '', countdown: '', showIcon: true };
    case 'countdown':
    default:
        return { name, time, countdown, showIcon: true };
    }
}

export function formatTrayText({ displayMode = 'countdown', countdownFormat = 'compact', name, time, remainingMinutes }) {
    const parts = formatDisplayParts({ displayMode, countdownFormat, name, time, remainingMinutes });
    const tokens = [];
    if (parts.name) tokens.push(parts.name);
    if (parts.time) tokens.push(parts.time);
    if (parts.countdown && parts.countdown !== 'now') tokens.push(parts.countdown);
    else if (parts.countdown === 'now') tokens.push('now');
    if (displayMode === 'icon') return name || 'Next Prayer';
    return tokens.join('  ') || name || 'Next Prayer';
}

export function shouldPlayAdhan(prayerSetting, globalAdhanEnabled) {
    if (prayerSetting?.adhan_enabled === true) return true;
    if (prayerSetting?.adhan_enabled === false) return false;
    return !!globalAdhanEnabled;
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
