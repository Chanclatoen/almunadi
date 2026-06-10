namespace AlMunadi.Core;

public sealed record NotificationPlan(
    DateTime OccursAt,
    string PrayerName,
    string PrayerTime,
    bool IsReminder,
    int ReminderMinutes,
    bool PlayAdhan,
    bool BypassDnd);

public static class NotificationPlanner
{
    public static IReadOnlyList<NotificationPlan> Build(
        IReadOnlyList<PrayerEvent> events,
        AppSettings settings,
        DateTime now)
    {
        if (!settings.NotificationsEnabled)
        {
            return [];
        }

        var plans = new List<NotificationPlan>();
        foreach (var prayerEvent in events)
        {
            var key = prayerEvent.Name == "Jumuah" ? "Jumuah" : BehaviorCore.PrayerNames[prayerEvent.Index];
            var prayerSettings = settings.PrayerNotificationSettings.GetValueOrDefault(key)
                ?? new PrayerNotificationSettings();
            if (!prayerSettings.Enabled)
            {
                continue;
            }

            var bypassDnd = prayerSettings.DndBypass ?? settings.DndBypass;
            if (prayerSettings.ReminderMinutes > 0)
            {
                var reminderAt = prayerEvent.OccursAt.AddMinutes(-prayerSettings.ReminderMinutes);
                if (reminderAt > now)
                {
                    plans.Add(new NotificationPlan(
                        reminderAt,
                        prayerEvent.Name,
                        prayerEvent.Time,
                        true,
                        prayerSettings.ReminderMinutes,
                        false,
                        bypassDnd));
                }
            }

            if (prayerEvent.OccursAt > now)
            {
                plans.Add(new NotificationPlan(
                    prayerEvent.OccursAt,
                    prayerEvent.Name,
                    prayerEvent.Time,
                    false,
                    0,
                    prayerSettings.AdhanEnabled ?? settings.AdhanEnabled,
                    bypassDnd));
            }
        }

        return plans.OrderBy(plan => plan.OccursAt).ToList();
    }
}
