using System.Text.Json;

namespace AlMunadi.Core;

public sealed class AppDataStore
{
    private static readonly string[] Languages = ["en", "nl", "ar", "fr", "tr"];
    private static readonly string[] DisplayModes = ["countdown", "since", "time", "name", "compact", "icon"];
    private static readonly string[] CountdownFormats = ["compact", "full"];
    private static readonly string[] NotificationPrayerNames = [.. BehaviorCore.PrayerNames, "Jumuah"];

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        WriteIndented = true,
    };

    public AppDataStore(string? dataDirectory = null)
    {
        DataDirectory = dataDirectory ?? Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "AlMunadi");
    }

    public string DataDirectory { get; }
    public string SettingsPath => Path.Combine(DataDirectory, "settings.json");
    public string CachePath => Path.Combine(DataDirectory, "cache.json");

    public AppSettings LoadSettings()
    {
        AppSettings settings;
        try
        {
            settings = File.Exists(SettingsPath)
                ? JsonSerializer.Deserialize<AppSettings>(File.ReadAllText(SettingsPath), JsonOptions) ?? new AppSettings()
                : new AppSettings();
        }
        catch (JsonException)
        {
            settings = new AppSettings();
        }
        catch (IOException)
        {
            settings = new AppSettings();
        }

        return Normalize(settings);
    }

    public void SaveSettings(AppSettings settings) => WriteAtomic(SettingsPath, Normalize(settings));

    public PrayerCache? LoadCache()
    {
        try
        {
            if (!File.Exists(CachePath))
            {
                return null;
            }

            var cache = JsonSerializer.Deserialize<PrayerCache>(File.ReadAllText(CachePath), JsonOptions);
            return cache is { Times.Count: 5 } && cache.Times.All(IsTime) ? cache : null;
        }
        catch (JsonException)
        {
            return null;
        }
        catch (IOException)
        {
            return null;
        }
    }

    public void SaveCache(PrayerCache cache)
    {
        if (cache.Times.Count != 5 || !cache.Times.All(IsTime))
        {
            throw new ArgumentException("Cache must contain five valid prayer times.", nameof(cache));
        }

        WriteAtomic(CachePath, cache);
    }

    public static AppSettings Normalize(AppSettings? settings)
    {
        settings ??= new AppSettings();
        settings.MosqueUrl = settings.MosqueUrl?.Trim() ?? string.Empty;
        settings.AdhanPath ??= string.Empty;
        settings.Language = Languages.Contains(settings.Language) ? settings.Language : "en";
        settings.DisplayMode = DisplayModes.Contains(settings.DisplayMode) ? settings.DisplayMode : "countdown";
        settings.CountdownFormat = CountdownFormats.Contains(settings.CountdownFormat) ? settings.CountdownFormat : "compact";

        var seen = new HashSet<string>(StringComparer.Ordinal);
        settings.SavedMosques = (settings.SavedMosques ?? [])
            .Where(mosque => mosque is not null)
            .Select(mosque => new SavedMosque
            {
                Url = mosque.Url?.Trim() ?? string.Empty,
                Name = mosque.Name ?? string.Empty,
            })
            .Where(mosque => mosque.Url.Length > 0 && seen.Add(mosque.Url))
            .ToList();

        settings.PrayerNotificationSettings ??= [];
        settings.PrayerNotificationSettings = NotificationPrayerNames.ToDictionary(
            name => name,
            name => NormalizeNotificationSettings(
                settings.PrayerNotificationSettings.TryGetValue(name, out var value) ? value : null));

        settings.PrayerOffsets ??= [];
        settings.PrayerOffsets = BehaviorCore.PrayerNames.ToDictionary(
            name => name,
            name => BehaviorCore.ClampOffset(
                settings.PrayerOffsets.TryGetValue(name, out var value) ? value : null));

        return settings;
    }

    private static PrayerNotificationSettings NormalizeNotificationSettings(PrayerNotificationSettings? settings)
    {
        settings ??= new PrayerNotificationSettings();
        settings.ReminderMinutes = Math.Clamp(settings.ReminderMinutes, 0, 120);
        return settings;
    }

    private static bool IsTime(string? value)
    {
        return value is not null
            && TimeOnly.TryParseExact(value, ["H:mm", "HH:mm"], null, System.Globalization.DateTimeStyles.None, out _);
    }

    private static void WriteAtomic<T>(string path, T value)
    {
        var directory = Path.GetDirectoryName(path)!;
        Directory.CreateDirectory(directory);
        var temporaryPath = path + ".tmp";
        File.WriteAllText(temporaryPath, JsonSerializer.Serialize(value, JsonOptions));
        File.Move(temporaryPath, path, true);
    }
}
