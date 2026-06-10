using AlMunadi.Core;

namespace AlMunadi.Core.Tests;

public sealed class PrayerScheduleTests
{
    private static readonly string[] Times = ["05:30", "13:30", "17:00", "21:30", "00:15"];

    [Fact]
    public void BuildsMidnightWrappedEventsAndAppliesOffsets()
    {
        var now = new DateTime(2026, 6, 10, 20, 0, 0);
        var events = PrayerSchedule.BuildEvents(Times, now, new Dictionary<string, int> { ["Isha"] = -5 });

        Assert.Equal(new DateTime(2026, 6, 11, 0, 10, 0), events[^1].OccursAt);
        Assert.Equal("00:10", events[^1].Time);
    }

    [Fact]
    public void SelectsNextAndPreviousAcrossMidnight()
    {
        var now = new DateTime(2026, 6, 10, 23, 0, 0);
        var events = PrayerSchedule.BuildEvents(Times, now);

        Assert.Equal("Isha", PrayerSchedule.NextPrayer(events, now)?.Name);
        Assert.Equal("Maghrib", PrayerSchedule.PreviousPrayer(events, now)?.Name);
    }

    [Fact]
    public void FridayJumuahReplacesDhuhr()
    {
        var now = new DateTime(2026, 6, 12, 10, 0, 0);
        var events = PrayerSchedule.BuildEvents(Times, now, isFriday: true, jumua: "13:45");

        Assert.Equal("Jumuah", events[1].Name);
        Assert.Equal("13:45", events[1].Time);
    }
}
