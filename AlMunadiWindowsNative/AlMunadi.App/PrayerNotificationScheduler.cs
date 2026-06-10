using System.IO;
using AlMunadi.Core;

namespace AlMunadi.App;

public sealed class PrayerNotificationScheduler : IDisposable
{
    private readonly AppDataStore store;
    private readonly AdhanPlayer adhanPlayer = new();
    private readonly List<System.Threading.Timer> timers = [];

    public PrayerNotificationScheduler(AppDataStore store)
    {
        this.store = store;
    }

    public void Reschedule()
    {
        Cancel();
        var settings = store.LoadSettings();
        var cache = store.LoadCache();
        if (cache is null)
        {
            return;
        }

        var now = DateTime.Now;
        var events = PrayerSchedule.BuildEvents(
            cache.Times,
            now,
            settings.PrayerOffsets,
            now.DayOfWeek == DayOfWeek.Friday,
            cache.Jumua);
        foreach (var plan in NotificationPlanner.Build(events, settings, now))
        {
            var delay = plan.OccursAt - now;
            if (delay <= TimeSpan.Zero)
            {
                continue;
            }

            System.Threading.Timer? timer = null;
            timer = new System.Threading.Timer(_ =>
            {
                Deliver(plan, settings);
                timer?.Dispose();
            }, null, delay, Timeout.InfiniteTimeSpan);
            timers.Add(timer);
        }
    }

    public void Dispose()
    {
        Cancel();
        adhanPlayer.Stop();
    }

    private void Deliver(NotificationPlan plan, AppSettings settings)
    {
        if (!plan.IsReminder && plan.PlayAdhan && File.Exists(settings.AdhanPath))
        {
            System.Windows.Application.Current.Dispatcher.Invoke(() => adhanPlayer.Play(settings.AdhanPath));
            return;
        }

        var translations = new TranslationCatalog(settings.Language);
        var prayerName = translations.PrayerName(plan.PrayerName);
        var title = plan.IsReminder
            ? prayerName
            : translations.Get("notification_title", new Dictionary<string, object?>
            {
                ["name"] = prayerName,
                ["time"] = plan.PrayerTime,
            });
        var body = plan.IsReminder
            ? translations.Get("reminder_body", new Dictionary<string, object?>
            {
                ["name"] = prayerName,
                ["minutes"] = plan.ReminderMinutes,
            })
            : translations.Get("notification_body", new Dictionary<string, object?> { ["name"] = prayerName });
        WindowsNotificationService.Send(title, body, plan.BypassDnd);
    }

    private void Cancel()
    {
        foreach (var timer in timers)
        {
            timer.Dispose();
        }

        timers.Clear();
    }
}
