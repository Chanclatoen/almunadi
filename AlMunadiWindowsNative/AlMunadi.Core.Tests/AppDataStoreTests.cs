using System.Text.Json;
using AlMunadi.Core;

namespace AlMunadi.Core.Tests;

public sealed class AppDataStoreTests : IDisposable
{
    private readonly string directory = Path.Combine(Path.GetTempPath(), "almunadi-tests", Guid.NewGuid().ToString("N"));

    [Fact]
    public void MissingSettingsReturnCanonicalDefaults()
    {
        var settings = new AppDataStore(directory).LoadSettings();

        Assert.Equal("countdown", settings.DisplayMode);
        Assert.Equal("compact", settings.CountdownFormat);
        Assert.Equal("en", settings.Language);
        Assert.Equal(6, settings.PrayerNotificationSettings.Count);
        Assert.Equal(5, settings.PrayerOffsets.Count);
    }

    [Fact]
    public void SettingsNormalizeAndRoundTripInPythonShape()
    {
        var store = new AppDataStore(directory);
        var settings = new AppSettings
        {
            Language = "unknown",
            DisplayMode = "bad",
            CountdownFormat = "bad",
            SavedMosques =
            [
                new() { Url = " https://mawaqit.net/en/w/example ", Name = "Example" },
                new() { Url = "https://mawaqit.net/en/w/example", Name = "Duplicate" },
                new() { Url = " " },
            ],
            PrayerOffsets = new() { ["Fajr"] = 90, ["Dhuhr"] = -90 },
            PrayerNotificationSettings = new()
            {
                ["Fajr"] = new() { ReminderMinutes = 200, AdhanEnabled = true },
            },
        };

        store.SaveSettings(settings);
        var loaded = store.LoadSettings();
        using var json = JsonDocument.Parse(File.ReadAllText(store.SettingsPath));

        Assert.Equal("en", loaded.Language);
        Assert.Single(loaded.SavedMosques);
        Assert.Equal(60, loaded.PrayerOffsets["Fajr"]);
        Assert.Equal(-60, loaded.PrayerOffsets["Dhuhr"]);
        Assert.Equal(120, loaded.PrayerNotificationSettings["Fajr"].ReminderMinutes);
        Assert.True(loaded.PrayerNotificationSettings["Fajr"].AdhanEnabled);
        Assert.True(json.RootElement.TryGetProperty("mosque_url", out _));
        Assert.True(json.RootElement.TryGetProperty("prayer_notification_settings", out _));
    }

    [Fact]
    public void MalformedOrIncompleteCacheIsIgnored()
    {
        var store = new AppDataStore(directory);
        Directory.CreateDirectory(directory);
        File.WriteAllText(store.CachePath, "{\"times\":[\"05:00\"]}");
        Assert.Null(store.LoadCache());

        File.WriteAllText(store.CachePath, "not json");
        Assert.Null(store.LoadCache());
    }

    [Fact]
    public void ValidCacheRoundTrips()
    {
        var store = new AppDataStore(directory);
        store.SaveCache(new PrayerCache
        {
            Times = ["05:00", "13:30", "17:00", "21:00", "22:30"],
            Name = "Example Mosque",
            Date = "2026-06-10",
        });

        Assert.Equal("Example Mosque", store.LoadCache()?.Name);
    }

    public void Dispose()
    {
        if (Directory.Exists(directory))
        {
            Directory.Delete(directory, true);
        }
    }
}
