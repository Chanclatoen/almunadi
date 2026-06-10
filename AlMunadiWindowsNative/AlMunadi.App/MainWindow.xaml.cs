using System.Windows;
using System.Windows.Media;
using AlMunadi.Core;

namespace AlMunadi.App;

public partial class MainWindow : Window
{
    private readonly AppDataStore store = new();

    public MainWindow()
    {
        InitializeComponent();
        Deactivated += (_, _) => Hide();
        RefreshView();
    }

    public void RefreshView(string? status = null)
    {
        var settings = store.LoadSettings();
        var cache = store.LoadCache();
        var translations = new TranslationCatalog(settings.Language);
        FlowDirection = settings.Language == "ar"
            ? System.Windows.FlowDirection.RightToLeft
            : System.Windows.FlowDirection.LeftToRight;
        WelcomeTitle.Text = translations["first_run_title"];
        WelcomeBody.Text = translations["first_run_body"];
        FindMosqueButton.Content = translations["find_mosque"];
        NextPrayerLabel.Text = translations["next_prayer"].ToUpperInvariant();
        RefreshButton.Content = translations["refresh"];
        SettingsButton.Content = translations["settings"];
        var firstRun = string.IsNullOrEmpty(settings.MosqueUrl);
        WelcomePanel.Visibility = firstRun ? Visibility.Visible : Visibility.Collapsed;
        SchedulePanel.Visibility = !firstRun && cache is not null ? Visibility.Visible : Visibility.Collapsed;
        MosqueName.Text = cache?.Name ?? "Al Munadi";
        MetaText.Text = string.Join("  |  ", new[] { cache?.HijriDate, cache?.QiblaDirection }.Where(value => !string.IsNullOrWhiteSpace(value)));
        StatusText.Text = status ?? (cache is null ? string.Empty : translations["cached_data"]);
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
        var rows = events.Select(item => new PrayerRow(
            translations.PrayerName(item.Name),
            item.Time,
            System.Windows.Media.Brushes.White,
            item.OccursAt <= now ? 0.45 : 1.0)).ToList();
        if (!string.IsNullOrWhiteSpace(cache.Shuruq))
        {
            rows.Insert(1, new PrayerRow(translations.PrayerName("Shuruq"), cache.Shuruq, (System.Windows.Media.Brush)FindResource("SaffronBrush"), 1.0));
        }
        if (now.DayOfWeek == DayOfWeek.Friday && !string.IsNullOrWhiteSpace(cache.Jumua2))
        {
            var insertIndex = rows.Count >= 3 ? 3 : rows.Count;
            rows.Insert(insertIndex, new PrayerRow(translations.PrayerName("Jumuah 2"), cache.Jumua2, (System.Windows.Media.Brush)FindResource("SaffronBrush"), 1.0));
        }
        PrayerRows.ItemsSource = rows;
        var next = PrayerSchedule.NextPrayer(events, now);
        NextPrayerText.Text = next is null
            ? string.Empty
            : $"{translations.PrayerName(next.Name)}  {next.Time}  {BehaviorCore.FormatCountdown(PrayerSchedule.WholeMinutesUntil(next.OccursAt, now), settings.CountdownFormat)}";
        NextIqamaText.Text = string.Empty;
        if (next is not null && cache.IqamaEnabled && cache.Iqama is not null && next.Index < cache.Iqama.Count)
        {
            var iqama = BehaviorCore.ResolveIqama(cache.Times[next.Index], cache.Iqama[next.Index]);
            if (iqama is not null)
            {
                NextIqamaText.Text = $"{translations["iqama"]}: {iqama}";
            }
        }
    }

    private void OpenSettings(object sender, RoutedEventArgs e)
    {
        new SettingsWindow().Show();
        Hide();
    }

    private async void Refresh(object sender, RoutedEventArgs e)
    {
        var settings = store.LoadSettings();
        if (string.IsNullOrEmpty(settings.MosqueUrl))
        {
            OpenSettings(sender, e);
            return;
        }

        StatusText.Text = new TranslationCatalog(settings.Language)["loading"];
        try
        {
            await new MawaqitClient().FetchAndCacheAsync(settings.MosqueUrl, store);
            AppEvents.NotifyStateChanged();
            RefreshView();
        }
        catch
        {
            var translations = new TranslationCatalog(settings.Language);
            RefreshView($"{translations["fetch_error"]}. {translations["cached_data"]}");
        }
    }

    private sealed record PrayerRow(string Name, string Time, System.Windows.Media.Brush Foreground, double Opacity);
}
