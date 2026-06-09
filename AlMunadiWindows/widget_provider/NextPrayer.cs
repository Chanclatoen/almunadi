// Pure helpers: prayer-time selection, offsets, iqama, Jumuah swap on Fridays,
// countdown formatting and Qibla arrow. Mirrors core/al_munadi_core.py so the
// widget shows the same values as the tray app.

using System;
using System.Collections.Generic;
using System.Globalization;

namespace AlMunadi.Widget;

public static class NextPrayer
{
    public static readonly string[] PrayerKeys = { "Fajr", "Dhuhr", "Asr", "Maghrib", "Isha" };

    public static int? ToMinutes(string time)
    {
        if (string.IsNullOrEmpty(time)) return null;
        var parts = time.Split(':');
        if (parts.Length < 2) return null;
        if (!int.TryParse(parts[0], NumberStyles.Integer, CultureInfo.InvariantCulture, out var h)) return null;
        if (!int.TryParse(parts[1], NumberStyles.Integer, CultureInfo.InvariantCulture, out var m)) return null;
        return h * 60 + m;
    }

    public static string FromMinutes(int total)
    {
        total = ((total % 1440) + 1440) % 1440;
        return $"{total / 60:D2}:{total % 60:D2}";
    }

    public static string ApplyOffset(string time, int minutes)
    {
        if (minutes == 0) return time;
        var m = ToMinutes(time);
        return m == null ? time : FromMinutes(m.Value + minutes);
    }

    public static List<string> AdjustedTimes(CacheData cache, AppSettings settings, DateTime now)
    {
        var offsets = settings.PrayerOffsets ?? new Dictionary<string, int>();
        var isFriday = now.DayOfWeek == DayOfWeek.Friday;
        var showJumuah = isFriday && !string.IsNullOrEmpty(cache.Jumua);
        var result = new List<string>(cache.Times.Count);
        for (var i = 0; i < cache.Times.Count; i++)
        {
            var time = cache.Times[i];
            if (i == 1 && showJumuah) time = cache.Jumua!;
            offsets.TryGetValue(PrayerKeys[Math.Min(i, PrayerKeys.Length - 1)], out var off);
            result.Add(ApplyOffset(time, off));
        }
        return result;
    }

    public static (int Index, DateTime When)? PrayerNext(CacheData cache, AppSettings settings, DateTime now)
    {
        var events = PrayerEvents(cache, settings, now);
        foreach (var ev in events)
        {
            if (ev.When > now) return ev;
        }
        if (events.Count > 0)
        {
            return (events[0].Index, events[0].When.AddDays(1));
        }
        return null;
    }

    public static List<(int Index, DateTime When)> PrayerEvents(CacheData cache, AppSettings settings, DateTime now)
    {
        var times = AdjustedTimes(cache, settings, now);
        var minuteValues = new List<int?>(times.Count);
        foreach (var t in times) minuteValues.Add(ToMinutes(t));

        var events = new List<(int, DateTime)>();
        if (minuteValues.Count == 0) return events;

        var dayOffset = 0;
        if (minuteValues.Count >= 2 && minuteValues[0] is int first && minuteValues[1] is int second && first > second)
        {
            dayOffset = -1;
        }
        int? previousAbsolute = null;
        for (var i = 0; i < minuteValues.Count; i++)
        {
            if (minuteValues[i] is not int mv) continue;
            if (i > 0)
            {
                if (dayOffset < 0) dayOffset = 0;
                while (previousAbsolute is int prev && mv + dayOffset * 1440 <= prev)
                {
                    dayOffset++;
                }
            }
            previousAbsolute = mv + dayOffset * 1440;
            var baseDay = now.Date.AddDays(dayOffset);
            events.Add((i, baseDay.AddMinutes(mv)));
        }
        return events;
    }

    public static string FormatCountdown(TimeSpan remaining, AppSettings settings)
    {
        if (remaining.TotalSeconds <= 0) return Translations.T("now", settings.Language);
        var mins = (int)Math.Floor(remaining.TotalMinutes);
        var h = mins / 60;
        var m = mins % 60;
        if (h > 0)
        {
            return settings.CountdownFormat == "full"
                ? $"-{h}h {m:D2}m"
                : $"-{h}h{m:D2}m";
        }
        return $"-{m}m";
    }

    public static string? Iqama(CacheData cache, AppSettings settings, int index, DateTime now)
    {
        if (!cache.IqamaEnabled || cache.Iqama == null || index >= cache.Iqama.Count) return null;
        var raw = cache.Iqama[index]?.Trim();
        if (string.IsNullOrEmpty(raw) || raw == "0" || raw == "+0") return null;
        if (raw.Contains(':')) return raw;
        var stripped = raw.StartsWith("+") ? raw[1..] : raw;
        if (!int.TryParse(stripped, NumberStyles.Integer, CultureInfo.InvariantCulture, out var offset) || offset <= 0)
        {
            return null;
        }
        if (index >= cache.Times.Count) return null;
        var baseMinutes = ToMinutes(cache.Times[index]);
        return baseMinutes == null ? null : FromMinutes(baseMinutes.Value + offset);
    }

    public static string QiblaArrow(string? qibla)
    {
        if (string.IsNullOrEmpty(qibla)) return string.Empty;
        var digits = new string(qibla.Where(c => char.IsDigit(c) || c == '-').ToArray());
        if (!int.TryParse(digits, NumberStyles.Integer, CultureInfo.InvariantCulture, out var deg))
        {
            return qibla;
        }
        var arrows = new[] { "↑", "↗", "→", "↘", "↓", "↙", "←", "↖" };
        var octant = ((deg + 22) % 360) / 45;
        return $"{arrows[octant]} {deg}°";
    }
}
