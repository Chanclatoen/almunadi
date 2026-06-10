using AlMunadi.Core;

namespace AlMunadi.Core.Tests;

public sealed class NotificationPlannerTests
{
    [Fact]
    public void BuildsReminderAndPrayerWithOverrides()
    {
        var now = new DateTime(2026, 6, 12, 12, 0, 0);
        var settings = AppDataStore.Normalize(new AppSettings
        {
            AdhanEnabled = false,
            DndBypass = false,
            PrayerNotificationSettings = new()
            {
                ["Jumuah"] = new()
                {
                    ReminderMinutes = 10,
                    AdhanEnabled = true,
                    DndBypass = true,
                },
            },
        });
        var events = PrayerSchedule.BuildEvents(
            ["05:00", "13:30", "17:00", "21:00", "22:30"],
            now,
            isFriday: true,
            jumua: "13:45");

        var plans = NotificationPlanner.Build(events, settings, now);
        var jumuah = plans.Where(plan => plan.PrayerName == "Jumuah").ToList();

        Assert.Equal(2, jumuah.Count);
        Assert.True(jumuah[0].IsReminder);
        Assert.False(jumuah[0].PlayAdhan);
        Assert.True(jumuah[1].PlayAdhan);
        Assert.All(jumuah, plan => Assert.True(plan.BypassDnd));
    }

    [Fact]
    public void DisabledGlobalNotificationsProduceNoPlans()
    {
        var settings = AppDataStore.Normalize(new AppSettings { NotificationsEnabled = false });
        var now = new DateTime(2026, 6, 10, 12, 0, 0);
        var events = PrayerSchedule.BuildEvents(["05:00", "13:30", "17:00", "21:00", "22:30"], now);

        Assert.Empty(NotificationPlanner.Build(events, settings, now));
    }
}
