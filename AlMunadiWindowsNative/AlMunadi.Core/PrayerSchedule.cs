namespace AlMunadi.Core;

public sealed record PrayerEvent(int Index, string Name, string Time, DateTime OccursAt);

public static class PrayerSchedule
{
    public static IReadOnlyList<PrayerEvent> BuildEvents(
        IReadOnlyList<string> times,
        DateTime now,
        IReadOnlyDictionary<string, int>? offsets = null,
        bool isFriday = false,
        string? jumua = null)
    {
        if (times.Count != BehaviorCore.PrayerNames.Length)
        {
            return [];
        }

        var effectiveTimes = times.ToArray();
        var names = BehaviorCore.PrayerNames.ToArray();
        if (isFriday && !string.IsNullOrWhiteSpace(jumua))
        {
            effectiveTimes[1] = jumua;
            names[1] = "Jumuah";
        }

        var events = new List<PrayerEvent>(effectiveTimes.Length);
        DateTime? previous = null;
        for (var index = 0; index < effectiveTimes.Length; index++)
        {
            var offset = offsets is not null && offsets.TryGetValue(BehaviorCore.PrayerNames[index], out var value)
                ? BehaviorCore.ClampOffset(value)
                : 0;
            var adjusted = BehaviorCore.ApplyOffset(effectiveTimes[index], offset);
            if (!TimeOnly.TryParseExact(adjusted, ["H:mm", "HH:mm"], out var time))
            {
                return [];
            }

            var occursAt = now.Date.Add(time.ToTimeSpan());
            if (previous is not null && occursAt <= previous)
            {
                occursAt = occursAt.AddDays(1);
            }

            events.Add(new PrayerEvent(index, names[index], adjusted, occursAt));
            previous = occursAt;
        }

        return events;
    }

    public static PrayerEvent? NextPrayer(IReadOnlyList<PrayerEvent> events, DateTime now)
    {
        var next = events.FirstOrDefault(item => item.OccursAt > now);
        if (next is not null)
        {
            return next;
        }

        return events.Count == 0 ? null : events[0] with { OccursAt = events[0].OccursAt.AddDays(1) };
    }

    public static PrayerEvent? PreviousPrayer(IReadOnlyList<PrayerEvent> events, DateTime now)
    {
        var previous = events.LastOrDefault(item => item.OccursAt <= now);
        if (previous is not null)
        {
            return previous;
        }

        return events.Count == 0 ? null : events[^1] with { OccursAt = events[^1].OccursAt.AddDays(-1) };
    }

    public static int WholeMinutesUntil(DateTime target, DateTime now) =>
        Math.Max(0, (int)Math.Ceiling((target - now).TotalMinutes));

    public static int WholeMinutesSince(DateTime target, DateTime now) =>
        Math.Max(0, (int)Math.Floor((now - target).TotalMinutes));
}
