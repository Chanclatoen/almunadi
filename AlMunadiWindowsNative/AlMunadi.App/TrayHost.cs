using System.Drawing;
using System.Diagnostics;
using System.IO;
using System.Windows;
using System.Windows.Forms;
using AlMunadi.Core;

namespace AlMunadi.App;

public sealed class TrayHost : IDisposable
{
    private readonly NotifyIcon notifyIcon;
    private readonly AppDataStore store = new();
    private readonly MainWindow popup;
    private readonly PrayerNotificationScheduler notificationScheduler;
    private readonly MawaqitClient mawaqitClient = new();
    private readonly UpdateChecker updateChecker;
    private readonly System.Windows.Threading.DispatcherTimer timer;
    private DateOnly refreshDate = DateOnly.FromDateTime(DateTime.Now);
    private UpdateInfo? updateInfo;

    public TrayHost()
    {
        popup = new MainWindow();
        notificationScheduler = new PrayerNotificationScheduler(store);
        updateChecker = new UpdateChecker(statePath: Path.Combine(store.DataDirectory, "update-check.json"));
        notifyIcon = new NotifyIcon
        {
            Icon = SystemIcons.Information,
            Visible = true,
            ContextMenuStrip = BuildMenu(),
        };
        notifyIcon.MouseClick += (_, args) =>
        {
            if (args.Button == MouseButtons.Left)
            {
                TogglePopup();
            }
        };

        timer = new System.Windows.Threading.DispatcherTimer { Interval = TimeSpan.FromMinutes(1) };
        timer.Tick += async (_, _) =>
        {
            UpdateTray();
            var today = DateOnly.FromDateTime(DateTime.Now);
            if (today != refreshDate)
            {
                refreshDate = today;
                await RefreshDataAsync();
            }
        };
        timer.Start();
        AppEvents.StateChanged += HandleStateChanged;
        notificationScheduler.Reschedule();
        UpdateTray();
        _ = RefreshDataAsync();
        _ = CheckForUpdateAsync();
    }

    public void Dispose()
    {
        timer.Stop();
        AppEvents.StateChanged -= HandleStateChanged;
        notificationScheduler.Dispose();
        notifyIcon.Visible = false;
        notifyIcon.Dispose();
    }

    private void HandleStateChanged()
    {
        popup.RefreshView();
        notificationScheduler.Reschedule();
        UpdateTray();
        var oldMenu = notifyIcon.ContextMenuStrip;
        notifyIcon.ContextMenuStrip = BuildMenu();
        oldMenu?.Dispose();
    }

    private async Task RefreshDataAsync()
    {
        var settings = store.LoadSettings();
        if (string.IsNullOrWhiteSpace(settings.MosqueUrl))
        {
            return;
        }

        try
        {
            await mawaqitClient.FetchAndCacheAsync(settings.MosqueUrl, store);
            popup.RefreshView(string.Empty);
            notificationScheduler.Reschedule();
            UpdateTray();
        }
        catch
        {
            var translations = new TranslationCatalog(settings.Language);
            popup.RefreshView($"{translations["fetch_error"]}. {translations["cached_data"]}");
        }
    }

    private async Task CheckForUpdateAsync()
    {
        updateInfo = await updateChecker.CheckAsync("1.0.9");
        if (updateInfo is not null)
        {
            var oldMenu = notifyIcon.ContextMenuStrip;
            notifyIcon.ContextMenuStrip = BuildMenu();
            oldMenu?.Dispose();
        }
    }

    private ContextMenuStrip BuildMenu()
    {
        var translations = new TranslationCatalog(store.LoadSettings().Language);
        var menu = new ContextMenuStrip();
        menu.Items.Add(translations["show_prayer_times"], null, (_, _) => TogglePopup());
        if (updateInfo is not null)
        {
            menu.Items.Add($"{translations["update_available"]} (v{updateInfo.Version})", null, (_, _) =>
                Process.Start(new ProcessStartInfo(updateInfo.Url) { UseShellExecute = true }));
        }
        menu.Items.Add(translations["settings"], null, (_, _) => new SettingsWindow().Show());
        menu.Items.Add(translations["refresh"], null, async (_, _) => await RefreshDataAsync());
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add(translations["quit"], null, (_, _) => System.Windows.Application.Current.Shutdown());
        return menu;
    }

    private void TogglePopup()
    {
        if (popup.IsVisible)
        {
            popup.Hide();
            return;
        }

        popup.RefreshView();
        var workArea = SystemParameters.WorkArea;
        popup.Left = workArea.Right - popup.Width - 12;
        popup.Top = workArea.Bottom - popup.Height - 12;
        popup.Show();
        popup.Activate();
    }

    private void UpdateTray()
    {
        var settings = store.LoadSettings();
        var cache = store.LoadCache();
        var title = BuildTitle(settings, cache, DateTime.Now);
        notifyIcon.Text = title[..Math.Min(title.Length, 63)];
    }

    private static string BuildTitle(AppSettings settings, PrayerCache? cache, DateTime now)
    {
        if (string.IsNullOrEmpty(settings.MosqueUrl))
        {
            return new TranslationCatalog(settings.Language)["set_mosque"];
        }

        if (cache is null)
        {
            return "Al Munadi";
        }

        var events = PrayerSchedule.BuildEvents(
            cache.Times,
            now,
            settings.PrayerOffsets,
            now.DayOfWeek == DayOfWeek.Friday,
            cache.Jumua);
        var translations = new TranslationCatalog(settings.Language);
        if (settings.DisplayMode == "since")
        {
            var previous = PrayerSchedule.PreviousPrayer(events, now);
            if (previous is null)
            {
                return "Al Munadi";
            }

            var elapsed = BehaviorCore.FormatElapsed(
                PrayerSchedule.WholeMinutesSince(previous.OccursAt, now),
                settings.CountdownFormat);
            var since = translations.Get("since_last_prayer", new Dictionary<string, object?>
            {
                ["name"] = translations.PrayerName(previous.Name),
            });
            return BehaviorCore.FormatTrayTitle("since", since, previous.Time, elapsed);
        }

        var next = PrayerSchedule.NextPrayer(events, now);
        if (next is null)
        {
            return "Al Munadi";
        }

        var countdown = BehaviorCore.FormatCountdown(
            PrayerSchedule.WholeMinutesUntil(next.OccursAt, now),
            settings.CountdownFormat);
        return BehaviorCore.FormatTrayTitle(settings.DisplayMode, translations.PrayerName(next.Name), next.Time, countdown);
    }
}
