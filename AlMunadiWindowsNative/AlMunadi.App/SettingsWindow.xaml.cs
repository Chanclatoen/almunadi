using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Windows;
using System.Windows.Controls;
using AlMunadi.Core;
using Microsoft.Win32;
using WpfCheckBox = System.Windows.Controls.CheckBox;
using WpfTextBox = System.Windows.Controls.TextBox;

namespace AlMunadi.App;

public partial class SettingsWindow : Window
{
    private readonly AppDataStore store = new();
    private readonly MawaqitClient mawaqit = new();
    private readonly AdhanPlayer adhanPlayer = new();
    private readonly Dictionary<string, NotificationControls> notificationControls = [];
    private readonly Dictionary<string, WpfTextBox> offsetControls = [];
    private AppSettings settings;

    public SettingsWindow()
    {
        InitializeComponent();
        settings = store.LoadSettings();
        DisplayMode.ItemsSource = new[] { "countdown", "since", "time", "name", "compact", "icon" };
        CountdownFormat.ItemsSource = new[] { "compact", "full" };
        LanguageSelector.ItemsSource = new[] { "en", "nl", "ar", "fr", "tr" };
        MosqueUrl.Text = settings.MosqueUrl;
        DisplayMode.SelectedItem = settings.DisplayMode;
        CountdownFormat.SelectedItem = settings.CountdownFormat;
        LanguageSelector.SelectedItem = settings.Language;
        NotificationsEnabled.IsChecked = settings.NotificationsEnabled;
        DndBypass.IsChecked = settings.DndBypass;
        AdhanEnabled.IsChecked = settings.AdhanEnabled;
        AdhanPath.Text = settings.AdhanPath;
        LaunchAtLogin.IsChecked = StartupManager.IsEnabled();
        RefreshSavedMosques();
        BuildPrayerControls();
        ApplyTranslations();
    }

    private TranslationCatalog Translations => new(LanguageSelector.SelectedItem as string ?? settings.Language);

    private void BuildPrayerControls()
    {
        foreach (var prayer in settings.PrayerNotificationSettings.Keys)
        {
            var row = new Grid { Margin = new Thickness(0, 5, 0, 5) };
            row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(110) });
            row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(90) });
            row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(90) });
            row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(90) });
            row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(90) });
            var value = settings.PrayerNotificationSettings[prayer];
            var name = new TextBlock { Text = Translations.PrayerName(prayer), VerticalAlignment = VerticalAlignment.Center };
            var enabled = new WpfCheckBox { IsChecked = value.Enabled, VerticalAlignment = VerticalAlignment.Center };
            var reminder = new WpfTextBox { Text = value.ReminderMinutes.ToString(), Width = 60, Padding = new Thickness(4) };
            var adhan = TriState(value.AdhanEnabled, Translations["adhan_per_prayer"]);
            var dnd = TriState(value.DndBypass, Translations["dnd_bypass_per_prayer"]);
            Grid.SetColumn(enabled, 1); Grid.SetColumn(reminder, 2); Grid.SetColumn(adhan, 3); Grid.SetColumn(dnd, 4);
            row.Children.Add(name); row.Children.Add(enabled); row.Children.Add(reminder); row.Children.Add(adhan); row.Children.Add(dnd);
            PrayerNotificationsPanel.Children.Add(row);
            notificationControls[prayer] = new NotificationControls(name, enabled, reminder, adhan, dnd);
        }

        foreach (var prayer in BehaviorCore.PrayerNames)
        {
            var row = new DockPanel { Margin = new Thickness(0, 5, 0, 5) };
            var input = new WpfTextBox { Text = settings.PrayerOffsets[prayer].ToString(), Width = 70, Padding = new Thickness(4) };
            DockPanel.SetDock(input, Dock.Right);
            row.Children.Add(input);
            row.Children.Add(new TextBlock { Text = Translations.PrayerName(prayer), VerticalAlignment = VerticalAlignment.Center });
            OffsetsPanel.Children.Add(row);
            offsetControls[prayer] = input;
        }
    }

    private static WpfCheckBox TriState(bool? value, string tooltip)
    {
        return new WpfCheckBox
        {
            IsThreeState = true,
            IsChecked = value,
            ToolTip = tooltip,
            HorizontalAlignment = System.Windows.HorizontalAlignment.Center,
            VerticalAlignment = System.Windows.VerticalAlignment.Center,
        };
    }

    private void ApplyTranslations()
    {
        var t = Translations;
        FlowDirection = (LanguageSelector.SelectedItem as string) == "ar"
            ? System.Windows.FlowDirection.RightToLeft
            : System.Windows.FlowDirection.LeftToRight;
        Title = $"Al Munadi - {t["settings"]}";
        MosqueTab.Header = t["mosques"];
        DisplayTab.Header = t["display"];
        NotificationsTab.Header = t["notifications"];
        AdhanTab.Header = t["adhan"];
        OffsetsTab.Header = t["manual_offsets"];
        AppTab.Header = t["app"];
        SearchHintLabel.Text = t["search_hint"];
        SearchButton.Content = t["search"];
        MosqueUrlLabel.Text = t["mosque_url"];
        SavedMosquesLabel.Text = t["saved_mosques"];
        AddMosqueButton.Content = t["add_mosque"];
        RemoveMosqueButton.Content = t["remove_mosque"];
        DisplayModeLabel.Text = t["display_mode"];
        CountdownFormatLabel.Text = t["countdown_format"];
        LanguageLabel.Text = t["language"];
        NotificationsEnabled.Content = t["notifications"];
        DndBypass.Content = t["dnd_bypass"];
        DndNote.Text = t["dnd_platform_note"];
        PerPrayerLabel.Text = t["per_prayer_notifications"];
        AdhanEnabled.Content = t["adhan_enabled"];
        AdhanPathLabel.Text = t["adhan_path"];
        BrowseButton.Content = t["adhan_browse"];
        TestAdhanButton.Content = t["test_adhan"];
        StopAdhanButton.Content = t["stop_adhan"];
        OffsetsHint.Text = t["offsets_hint"];
        ResetOffsetsButton.Content = t["reset_offsets"];
        LaunchAtLogin.Content = t["launch_at_login"];
        VersionText.Text = $"{t["app_version"]}: {Assembly.GetExecutingAssembly().GetName().Version?.ToString(3) ?? "1.0.9"}";
        OpenReleasesButton.Content = t["open_releases"];
        TestNotificationButton.Content = t["test_notification"];
        SaveButton.Content = t["save"];
        foreach (var (prayer, controls) in notificationControls)
        {
            controls.Name.Text = t.PrayerName(prayer);
        }
    }

    private async void SearchMosques(object sender, RoutedEventArgs e)
    {
        SearchButton.IsEnabled = false;
        SearchStatus.Text = Translations["searching"];
        try
        {
            SearchResults.ItemsSource = await mawaqit.SearchAsync(SearchQuery.Text.Trim());
            SearchStatus.Text = SearchResults.Items.Count == 0 ? Translations["no_results"] : string.Empty;
        }
        catch
        {
            SearchStatus.Text = Translations["search_failed"];
        }
        finally
        {
            SearchButton.IsEnabled = true;
        }
    }

    private void SelectSearchResult(object sender, System.Windows.Input.MouseButtonEventArgs e)
    {
        if (SearchResults.SelectedItem is MosqueSearchResult result && result.Slug.Length > 0)
        {
            MosqueUrl.Text = $"https://mawaqit.net/en/w/{result.Slug}";
            UrlStatus.Text = string.Empty;
        }
    }

    private void AddCurrentMosque(object sender, RoutedEventArgs e)
    {
        var url = MosqueUrl.Text.Trim();
        if (BehaviorCore.ExtractSlug(url) is null)
        {
            UrlStatus.Text = Translations["invalid_mawaqit_url"];
            return;
        }

        settings.SavedMosques.Add(new SavedMosque { Url = url, Name = BehaviorCore.ExtractSlug(url)! });
        settings = AppDataStore.Normalize(settings);
        RefreshSavedMosques();
    }

    private void RemoveSavedMosque(object sender, RoutedEventArgs e)
    {
        if (SavedMosques.SelectedItem is SavedMosque selected)
        {
            settings.SavedMosques.RemoveAll(item => item.Url == selected.Url);
            RefreshSavedMosques();
        }
    }

    private void SelectSavedMosque(object sender, System.Windows.Input.MouseButtonEventArgs e)
    {
        if (SavedMosques.SelectedItem is SavedMosque selected)
        {
            MosqueUrl.Text = selected.Url;
        }
    }

    private void RefreshSavedMosques() => SavedMosques.ItemsSource = settings.SavedMosques.ToList();

    private void LanguageChanged(object sender, SelectionChangedEventArgs e)
    {
        if (IsLoaded)
        {
            ApplyTranslations();
        }
    }

    private void BrowseAdhan(object sender, RoutedEventArgs e)
    {
        var dialog = new Microsoft.Win32.OpenFileDialog { CheckFileExists = true };
        if (dialog.ShowDialog(this) == true)
        {
            AdhanPath.Text = dialog.FileName;
        }
    }

    private void TestAdhan(object sender, RoutedEventArgs e)
    {
        try
        {
            adhanPlayer.Play(AdhanPath.Text);
            AdhanStatus.Text = string.Empty;
        }
        catch (FileNotFoundException)
        {
            AdhanStatus.Text = Translations["adhan_file_missing"];
        }
    }

    private void StopAdhan(object sender, RoutedEventArgs e) => adhanPlayer.Stop();

    private void ResetOffsets(object sender, RoutedEventArgs e)
    {
        foreach (var input in offsetControls.Values)
        {
            input.Text = "0";
        }
    }

    private void OpenReleases(object sender, RoutedEventArgs e) => Process.Start(new ProcessStartInfo
    {
        FileName = "https://github.com/Chanclatoen/almunadi/releases",
        UseShellExecute = true,
    });

    private void TestNotification(object sender, RoutedEventArgs e)
    {
        WindowsNotificationService.Send(
            "Al Munadi",
            Translations.Get("notification_body", new Dictionary<string, object?> { ["name"] = Translations.PrayerName("Dhuhr") }),
            DndBypass.IsChecked == true);
    }

    private void Save(object sender, RoutedEventArgs e)
    {
        var url = MosqueUrl.Text.Trim();
        if (url.Length > 0 && BehaviorCore.ExtractSlug(url) is null)
        {
            UrlStatus.Text = Translations["invalid_mawaqit_url"];
            return;
        }

        settings.MosqueUrl = url;
        settings.DisplayMode = DisplayMode.SelectedItem as string ?? "countdown";
        settings.CountdownFormat = CountdownFormat.SelectedItem as string ?? "compact";
        settings.Language = LanguageSelector.SelectedItem as string ?? "en";
        settings.NotificationsEnabled = NotificationsEnabled.IsChecked == true;
        settings.DndBypass = DndBypass.IsChecked == true;
        settings.AdhanEnabled = AdhanEnabled.IsChecked == true;
        settings.AdhanPath = AdhanPath.Text.Trim();
        foreach (var (prayer, controls) in notificationControls)
        {
            var value = settings.PrayerNotificationSettings[prayer];
            value.Enabled = controls.Enabled.IsChecked == true;
            value.ReminderMinutes = int.TryParse(controls.Reminder.Text, out var reminder) ? reminder : 0;
            value.AdhanEnabled = controls.Adhan.IsChecked;
            value.DndBypass = controls.Dnd.IsChecked;
        }
        foreach (var (prayer, input) in offsetControls)
        {
            settings.PrayerOffsets[prayer] = int.TryParse(input.Text, out var offset) ? offset : 0;
        }

        store.SaveSettings(settings);
        StartupManager.SetEnabled(LaunchAtLogin.IsChecked == true);
        AppEvents.NotifyStateChanged();
        Close();
    }

    protected override void OnClosed(EventArgs e)
    {
        adhanPlayer.Stop();
        base.OnClosed(e);
    }

    private sealed record NotificationControls(TextBlock Name, WpfCheckBox Enabled, WpfTextBox Reminder, WpfCheckBox Adhan, WpfCheckBox Dnd);
}
